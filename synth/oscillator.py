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
from midi.MidiFileParser import MidiFileParser

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
        sys.stderr.write("Loaded %s\n" % file)

    def get_samples(self, nr_of_samples, release = None):
        if self.phase > self.length:
            result = numpy.zeros(nr_of_samples)
        elif self.phase + nr_of_samples < self.length:
            result = self.wavefile[self.phase:self.phase + nr_of_samples]
        else:
            result = numpy.zeros(nr_of_samples)
            samples = self.length - self.phase
            result[:samples] = self.wavefile[self.phase:]
        self.phase += nr_of_samples
        return result

class BaseInstrument(SampleGenerator):
    def __init__(self, options, note_envelope):
        super(BaseInstrument, self).__init__(options)
        self.notes = {}
        self.note_envelope = note_envelope
        self.init(options)
        self.phase = 0

        self.notes_playing = set()
        self.notes_stopped = set()

    def init(self, options):
        for note, freq in options.frequency_table.midi_frequencies.iteritems():
            self.notes[note] = self.init_note(options, note, freq)
    def init_note(self, options, note, freq):
        return None
    def get_samples(self, nr_of_samples):
        result = numpy.zeros(nr_of_samples)
        sources = 0
        self.get_and_set_new_playing_notes(nr_of_samples)
        (sources_p, result) = self.render_playing_notes(result, nr_of_samples)
        (sources_s, result) = self.render_stopped_notes(result, nr_of_samples)
        self.phase += nr_of_samples
        sources += sources_p + sources_s
        if sources <= 1:
            return result
        return result / float(sources)

    def get_and_set_new_playing_notes(self, nr_of_samples):
        notes = self.note_envelope.get_notes_for_range(self.options, 
                self.phase, nr_of_samples)
        self.notes_playing = self.notes_playing.union(notes)

    def render_playing_notes(self, result, nr_of_samples):
        sources = 0
        for p in self.notes_playing:
            if not p.does_this_note_play(self.phase, nr_of_samples):
                continue

            start_index = p.get_start_index_for_phase(self.phase)
            stop_index = p.get_stop_index_for_phase(self.phase, nr_of_samples)
            note_phase =  p.get_note_phase_for_phase(self.phase)
            length = stop_index - start_index

            for sample_generator in self.notes[p.note]:
                sample_generator.phase = note_phase
                result[start_index:stop_index] += sample_generator.get_samples(length)
                sources += 1
        return (sources, result)

    def remove_stopped_playing_notes(self, nr_of_samples):
        remove = set()
        for p in self.notes_playing:
            if p.stop_time is not None and self.phase + nr_of_samples > p.stop_time:
                remove.add(p)
        for r in remove:
            self.notes_playing.remove(r)
            self.notes_stopped.add(r)

    def render_stopped_notes(self, result, nr_of_samples):
        self.remove_stopped_playing_notes(nr_of_samples)
        sources = 0
        stopped = set()
        for p in self.notes_stopped:
            if self.phase > p.stop_time:
                start_index = 0
                note_phase = self.phase
            else:
                start_index = p.stop_time - self.phase
                note_phase = p.stop_time
            length = nr_of_samples - start_index
            for sample_generator in self.notes[p.note]:
                sample_generator.phase = note_phase
                samples = sample_generator.get_samples(length, release = p.stop_time)
                result[start_index:] += samples
                sources += 1
                if (samples[-4:] == [0,0,0,0]).all():
                    stopped.add(p)
        for s in stopped:
            self.notes_stopped.remove(s)
        return (sources, result)

class OvertoneInstrument(BaseInstrument):
    def __init__(self, options, note_envelope):
        super(OvertoneInstrument, self).__init__(options, note_envelope)
    def init_note(self, options, note, freq):
        amp_env = envelopes.SegmentAmplitudeEnvelope()
        amp_env.release_time = 100
        amp_env.add_segment(1.0, 4000)
        amp_env.add_segment(0.4, 4000)
        osc1 = Oscillator(options, freq, amp_env)
        #osc1 = PCM(options, "demo/rap_102_c1.wav", amp_env) 
        return [osc1]

class SynthInstrument(BaseInstrument):
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

def create_synth_from_midi_tracks(header, tracks):
    options = Options()
    ticks_per_beat = header["time_division"]['ticks_per_beat']
    for t in tracks:
        instr = OvertoneInstrument
        instrument = instr(options, note_envelopes.MidiTrackNoteEnvelope(options, t, ticks_per_beat))
        return instrument

def process_midi_files():
    global amplitude_generator
    for f in sys.argv:
        if ".mid" in f:
            (header, tracks) = MidiFileParser().parse_midi_file(sys.argv[1])
            tracks = filter(lambda t: len(filter(lambda x: x.event_type in [8,9], t.events)) != 0, tracks)
            synth = create_synth_from_midi_tracks(header, tracks)
            return synth

def main():
    input = process_midi_files()
    profile()
    plot()
    t= 0
    opts = Options()
    if input is None:
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
