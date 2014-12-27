import math
from options import Options
import wave_writer
import sys
import cProfile
import pstats
import numpy
import envelopes
import note_envelopes
import wave
import struct

class SampleGenerator(object):
    def __init__(self, options):
        self.options = options
        self.last_level = 0.0

    def get_samples_in_byte_rate(self, nr_of_samples):
        result = self.get_samples(nr_of_samples)
        return numpy.multiply(result, self.options.max_value).astype(int)

class Oscillator(SampleGenerator):
    def __init__(self, options, freq = None, amplitude_envelope = None):
        super(Oscillator, self).__init__(options)
        self.freq = options.pitch_standard if freq is None else freq
        self.phase = 0
        self.phase_incr = self.options.two_pi_divided_by_sample_rate * self.freq
        self.amp_env = amplitude_envelope

    def get_samples(self, nr_of_samples, release = None):
        result = numpy.full([nr_of_samples], self.phase_incr)
        result[0] = 0.0
        result = result.cumsum()
        result = numpy.add(result, self.phase * self.phase_incr)
        result = numpy.sin(result)
        if self.amp_env is not None:
            amplitudes = self.amp_env.get_amplitudes(self.phase, nr_of_samples, release)
            result = numpy.multiply(result, amplitudes)
        self.phase += nr_of_samples
        return result

wavefile_cache = {}

class PCM(SampleGenerator):
    def __init__(self, options, file, amplitude_envelope = None):
        super(PCM, self).__init__(options)
        self.amp_env = amplitude_envelope
        self.file = file
        self.load_file(file)
        self.phase = 0

    def load_file(self, file):
        global wavefile_cache
        if file in wavefile_cache:
            self.length = len(wavefile_cache[file])
            self.wavefile = wavefile_cache[file]
            return
        w = wave.open(file)
        if w.getframerate() != self.options.sample_rate:
            raise "sample rate mismatch"
        if w.getsampwidth() != self.options.byte_rate:
            raise "byte rate mismatch"
        if w.getnchannels() != 1:
            raise "channel mismatch"
        frames = w.readframes(w.getnframes())
        samples = struct.unpack(str(w.getnframes()) + self.options.struct_pack_format, frames)
        self.wavefile = numpy.array([s / float(self.options.max_value) for s in samples])
        self.length = w.getnframes()
        w.close()
        wavefile_cache[file] = self.wavefile

    def get_samples(self, nr_of_samples, release = None):
        if self.phase > self.length:
            result = numpy.zeros(nr_of_samples)
        elif self.phase + nr_of_samples < self.length:
            result = self.wavefile[self.phase:self.phase + nr_of_samples]
        else:
            result = numpy.zeros(nr_of_samples)
            samples = self.length - self.phase
            sys.stderr.write("%d %d %d %d\n" % (self.phase, nr_of_samples, self.length, samples))
            result[:samples] = self.wavefile[self.phase:]
        self.phase += nr_of_samples
        return result


class Instrument(SampleGenerator):
    def __init__(self, options, note_envelope):
        super(Instrument, self).__init__(options)
        self.notes = {}
        self.note_envelope = note_envelope
        self.init(options)
        self.phase = 0
        self.currently_playing = set()
        self.currently_stopped = set()
        self.last_level = 0.0

    def init(self, options):
        for note, freq in options.frequency_table.midi_frequencies.iteritems():
            self.notes[note] = self.init_note(options, note, freq)
    def init_note(self, options, note, freq):
        return None
    def get_samples(self, nr_of_samples):
        result = numpy.zeros(nr_of_samples)
        sources = 0
        notes = self.note_envelope.get_notes_for_range(self.options, 
                self.phase, nr_of_samples)
        arrays = []
        playing = set()
        stopped = self.currently_stopped.copy()
        notes_playing = set()
        already_stopped = set()
        for (start, phase, length, note) in notes:
            arr = numpy.zeros(nr_of_samples)
            for sample_generator in self.notes[note]:
                sample_generator.phase = phase
                result[start:start+length] += sample_generator.get_samples(length)
                sources += 1
            if start + length < nr_of_samples:
                stopped.add((self.phase + start + length, note))
                already_stopped.add((self.phase - (start + phase), note))
            else:
                notes_playing.add((self.phase - (start + phase), note))
        for previously_playing in self.currently_playing:
            if previously_playing not in notes_playing and previously_playing not in already_stopped:
                stopped.add((self.phase, note))
        self.currently_playing = notes_playing

        for (stopped_at, stopped_note) in stopped:
            if stopped_at >= self.phase:
                index = stopped_at - self.phase
                phase = stopped_at
                length = self.phase + nr_of_samples - stopped_at
            else:
                index = 0
                phase = self.phase
                length = nr_of_samples

            for sample_generator in self.notes[stopped_note]:
                sample_generator.phase = phase
                samples = sample_generator.get_samples(length, release = stopped_at)
                result[index:] += samples
                sources += 1
                if not (samples[-4:] == [0,0,0,0]).all():
                    self.currently_stopped.add((stopped_at, stopped_note))
                else: 
                    if (stopped_at, stopped_note) in self.currently_stopped:
                        self.currently_stopped.remove((stopped_at, stopped_note))

        result[0] += self.last_level
        result[0] /= 2.0

        self.phase += nr_of_samples
        if sources <= 1:
            self.last_level = result[-1]
            return result
        result = result / float(sources)
        self.last_level = result[-1]
        return result

class OvertoneInstrument(Instrument):
    def __init__(self, options, note_envelope):
        super(OvertoneInstrument, self).__init__(options, note_envelope)
    def init_note(self, options, note, freq):
        amp_env = envelopes.SegmentAmplitudeEnvelope()
        amp_env.release_time = 10
        amp_env.add_segment(0.65, 400)
        amp_env.add_segment(0.4, 4000)
        osc1 = Oscillator(options, freq, amp_env)
        osc1 = PCM(options, "demo/rap_102_c1.wav", amp_env) 
        return [osc1]

class SynthInstrument(Instrument):
    def __init__(self, options, note_envelope):
        super(SynthInstrument, self).__init__(options, note_envelope)
    def init_note(self, options, note, freq):
        amp_env = envelopes.SegmentAmplitudeEnvelope()
        amp_env.add_segment(1.0, 1000)
        amp_env.add_segment(0.5, 10000)
        osc1= Oscillator(options, freq, amp_env)
        return [osc1]


def profile_call():
    opts = Options()
    instr = OvertoneInstrument(opts, note_envelopes.ArpeggioNoteEnvelope())
    input = instr
    input.get_samples_in_byte_rate(44100)

def profile():
    if "--profile" in sys.argv:
        cProfile.run('profile_call()', 'restats')
        p = pstats.Stats('restats')
        p.strip_dirs().sort_stats('time').print_stats()
        sys.exit(0)

def plot():
    if "--plot" in sys.argv:
        opts = Options()
        instr = OvertoneInstrument(opts, note_envelopes.ArpeggioNoteEnvelope())
        input = instr
        nr_of_samples = int(sys.argv[sys.argv.index("--plot") + 1])
        if len(sys.argv) > sys.argv.index("--plot") + 2 and sys.argv[sys.argv.index("--plot") + 2].isdigit():


            start_at = int(sys.argv[sys.argv.index("--plot") + 2])
            samples = instr.get_samples_in_byte_rate(nr_of_samples + start_at)[start_at:]
        else:
            samples = instr.get_samples_in_byte_rate(nr_of_samples)
        import Gnuplot
        g = Gnuplot.Gnuplot()
        g.title("Yo")
        g("set data style linespoints")
        g.plot(zip(xrange(nr_of_samples), samples))
        raw_input('Please press return to continue...\n')
        sys.exit(0)


def main():
    profile()
    plot()
    t= 0
    opts = Options()
    env = note_envelopes.ArpeggioNoteEnvelope()
    env = note_envelopes.ConstantNoteEnvelope(opts, 68)
    instr = OvertoneInstrument(opts, env)
    input = instr
    wave = wave_writer.WaveWriter(opts, "output.wav", also_output_to_stdout = True)
    try:
        while True:
            wave.write_samples(input.get_samples_in_byte_rate(1000))
            t += 2000
    except KeyboardInterrupt:
        print "Written", t, "samples" 
        wave.close() 

if __name__ == '__main__':
    main()
