from synth.interfaces import SampleGenerator
from synth.envelopes import SegmentAmplitudeEnvelope
from synth.oscillator import Oscillator, OscillatorWithAmplitudeEnvelope
import numpy

class BaseInstrument(SampleGenerator):

    def __init__(self, options, note_envelope):
        super(BaseInstrument, self).__init__(options)
        self.notes = {}
        self.note_envelope = note_envelope
        self.init(options)
        self.notes_playing = set()
        self.notes_stopped = set()

    def init(self, options):
        for note, freq in options.frequency_table.midi_frequencies.iteritems():
            self.notes[note] = self.init_note(options, note, freq)

    def init_note(self, options, note, freq):
        return None

    def get_samples(self, nr_of_samples, phase, release = None):
        sources = 0
        result = numpy.zeros(nr_of_samples)
        notes = self.note_envelope.get_notes_for_range(self.options, phase, nr_of_samples)
        self.notes_playing = self.notes_playing.union(notes)
        (sources_p, result) = self.render_playing_notes(result, nr_of_samples, phase)
        (sources_s, result) = self.render_stopped_notes(result, nr_of_samples, phase)
        sources += sources_p + sources_s
        return result if sources <= 1 else result / float(sources)

    def render_playing_notes(self, result, nr_of_samples, phase):
        sources = 0
        for p in self.notes_playing:
            if not p.does_this_note_play(phase, nr_of_samples):
                continue

            start_index = p.get_start_index_for_phase(p.start_time, phase)
            stop_index = p.get_stop_index_for_phase(p.stop_time, phase, nr_of_samples)
            note_phase =  p.get_note_phase_for_phase(phase)
            length = stop_index - start_index

            for sample_generator in self.notes[p.note]:
                result[start_index:stop_index] += sample_generator.get_samples(length, note_phase)
                sources += 1
        return (sources, result)

    def remove_stopped_playing_notes(self, nr_of_samples, phase):
        remove = set()
        for p in self.notes_playing:
            if p.stop_time is not None and phase + nr_of_samples > p.stop_time:
                remove.add(p)
        for r in remove:
            self.notes_playing.remove(r)
            self.notes_stopped.add(r)

    def render_stopped_notes(self, result, nr_of_samples, phase):
        self.remove_stopped_playing_notes(nr_of_samples, phase)
        sources = 0
        stopped = set()
        for p in self.notes_stopped:
            start_index = p.get_start_index_for_phase(p.stop_time, phase)
            if phase > p.stop_time:
                note_phase = phase
            else:
                note_phase = p.stop_time
            length = nr_of_samples - start_index
            for sample_generator in self.notes[p.note]:
                samples = sample_generator.get_samples(length, note_phase, release = p.stop_time)
                result[start_index:] += samples
                sources += 1
                if (samples[-4:] <= [0,0,0,0]).all():
                    stopped.add(p)
        for s in stopped:
            self.notes_stopped.remove(s)
        return (sources, result)

class OvertoneInstrument(BaseInstrument):
    def __init__(self, options, note_envelope):
        super(OvertoneInstrument, self).__init__(options, note_envelope)
    def init_note(self, options, note, freq):
        amp_env = SegmentAmplitudeEnvelope()
        amp_env.release_time = 100
        amp_env.add_segment(1.0, 4000)
        amp_env.add_segment(0.4, 4000)
        osc1 = OscillatorWithAmplitudeEnvelope(options, amp_env, freq)
        #osc1 = PCM(options, "demo/rap_102_c1.wav", amp_env) 
        return [osc1]

class SynthInstrument(BaseInstrument):
    def __init__(self, options, note_envelope):
        super(SynthInstrument, self).__init__(options, note_envelope)
    def init_note(self, options, note, freq):
        amp_env = SegmentAmplitudeEnvelope()
        amp_env.add_segment(1.0, 1000)
        amp_env.add_segment(0.5, 10000)
        osc1= OscillatorWithAmplitudeEnvelope(options, amp_env, freq)
        return [osc1]
