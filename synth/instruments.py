from synth.interfaces import SampleGenerator
from synth.envelopes import SegmentAmplitudeEnvelope
from synth.oscillator import Oscillator, OscillatorWithAmplitudeEnvelope, \
        RandomOscillatorWithAmplitudeEnvelope
import numpy
import sys

class BaseInstrument(SampleGenerator):

    def __init__(self, options, note_envelope):
        super(BaseInstrument, self).__init__(options)
        self.sample_generators = {}
        self.note_envelope = note_envelope
        self.init(options)
        self.notes_playing = set()
        self.notes_stopped = set()
        self.max_sources = 1

    def init(self, options):
        for note, freq in options.frequency_table.midi_frequencies.iteritems():
            self.sample_generators[note] = self.init_note(options, note, freq)

    def init_note(self, options, note, freq):
        return None

    def get_samples(self, nr_of_samples, phase, release = None):
        sources_arr = numpy.zeros(nr_of_samples)
        result = numpy.zeros(nr_of_samples)
        notes = self.note_envelope.get_notes_for_range(self.options, phase, nr_of_samples)
        self.notes_playing = self.notes_playing.union(notes)
        (sources_p, result) = self.render_playing_notes(result, sources_arr, nr_of_samples, phase)
        (sources_s, result) = self.render_stopped_notes(result, sources_arr, nr_of_samples, phase)
        sources_arr += sources_p + sources_s
        sources_arr = numpy.add(sources_arr, numpy.where(sources_arr == 0.0, 1.0, 0.0))
        return result / sources_arr

    def render_playing_notes(self, result, sources_arr, nr_of_samples, phase):
        for p in self.notes_playing:
            if not p.does_this_note_play(phase, nr_of_samples):
                continue

            start_index = p.get_start_index_for_phase(p.start_time, phase)
            stop_index = p.get_stop_index_for_phase(p.stop_time, phase, nr_of_samples)
            note_phase =  p.get_note_phase_for_phase(phase)
            length = stop_index - start_index

            for sample_generator in self.get_sample_generators_for_note(p.note):
                result[start_index:stop_index] += sample_generator.get_samples(length, note_phase)
                sources_arr[start_index:stop_index] += 1
        return (sources_arr, result)

    def remove_stopped_playing_notes(self, nr_of_samples, phase):
        remove = set()
        for p in self.notes_playing:
            if p.stop_time is not None and phase + nr_of_samples > p.stop_time:
                remove.add(p)
        for r in remove:
            self.notes_playing.remove(r)
            self.notes_stopped.add(r)

    def get_sample_generators_for_note(self, note):
        if self.sample_generators[note] == []:
            sys.stderr.write("No generators for note %d\n" % note)
        return self.sample_generators[note]

    def render_stopped_notes(self, result, sources_arr, nr_of_samples, phase):
        self.remove_stopped_playing_notes(nr_of_samples, phase)
        stopped = set()
        for p in self.notes_stopped:
            start_index = p.get_start_index_for_phase(p.stop_time, phase)
            if phase > p.stop_time:
                note_phase = phase
            else:
                note_phase = p.stop_time
            length = nr_of_samples - start_index
            for sample_generator in self.get_sample_generators_for_note(p.note):
                samples = sample_generator.get_samples(length, note_phase, release = p.stop_time)
                result[start_index:] += samples
                sources_arr[start_index:] += 1
                postfix_len = min(len(samples), 4)
                if (samples[-postfix_len:] <= [0] * postfix_len).all():
                    stopped.add(p)
        for s in stopped:
            self.notes_stopped.remove(s)
        return (sources_arr, result)

class OvertoneInstrument(BaseInstrument):

    def __init__(self, options, note_envelope, overtones = 1, attack = 4000, decay = 4000, sustain = 0.5, release = 100):
        self.overtones = 1 if overtones <= 1 else overtones
        self.attack = attack
        self.decay = decay
        self.sustain = sustain
        self.release = release
        super(OvertoneInstrument, self).__init__(options, note_envelope)

    def init_note(self, options, note, freq):
        result = []
        for d in xrange(self.overtones, self.overtones + 1):
            amp_env = SegmentAmplitudeEnvelope()
            amp_env.release_time = self.release
            amp_env.add_segment(1.0 / d, self.attack)
            amp_env.add_segment(self.sustain / d, self.decay)
            osc = OscillatorWithAmplitudeEnvelope(options, amp_env, freq * d)
            result.append(osc)
        return result

class SynthInstrument(BaseInstrument):
    def __init__(self, options, note_envelope):
        super(SynthInstrument, self).__init__(options, note_envelope)
    def init_note(self, options, note, freq):
        amp_env = SegmentAmplitudeEnvelope()
        amp_env.add_segment(1.0, 1000)
        amp_env.add_segment(0.5, 10000)
        osc1= OscillatorWithAmplitudeEnvelope(options, amp_env, freq)
        return [osc1]

class PercussionInstrument(BaseInstrument):
    def __init__(self, options, note_envelope):
        super(PercussionInstrument, self).__init__(options, note_envelope)

    def init_note(self, options, note, freq):
        if note in [35, 36]: # kick
            amp_env = SegmentAmplitudeEnvelope()
            amp_env.add_segment(1.0, 100)
            amp_env.add_segment(0.0, 5000)
            osc = OscillatorWithAmplitudeEnvelope(options, amp_env, freq = 100)
            return [osc]
        if note in [40]: # snare
            amp_env = SegmentAmplitudeEnvelope()
            amp_env.release_time = 100
            amp_env.add_segment(1.0, 100)
            amp_env.add_segment(0.0, 8000)
            osc = RandomOscillatorWithAmplitudeEnvelope(options, amp_env, freq = 100)
            return [osc]
        if note in [42]: # closed hihat
            amp_env = SegmentAmplitudeEnvelope()
            amp_env.add_segment(0.1, 100)
            amp_env.add_segment(0.0, 5000)
            osc = RandomOscillatorWithAmplitudeEnvelope(options, amp_env, freq = 100)
            return [osc]
        if note in [49, 57]: # crash
            amp_env = SegmentAmplitudeEnvelope()
            amp_env.release_time = 100
            amp_env.add_segment(0.3, 1)
            amp_env.add_segment(1.0, 4000)
            amp_env.add_segment(1.0, 6000)
            amp_env.add_segment(0.5, 10000)
            osc = RandomOscillatorWithAmplitudeEnvelope(options, amp_env, freq = 100)
            return [osc]
        return []

    def get_sample_generators_for_note(self, note):
        if self.sample_generators[note] == []:
            sys.stderr.write("No generators for note %d\n" % note)
        return self.sample_generators[note]
