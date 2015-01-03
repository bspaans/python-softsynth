from synth.interfaces import SampleGenerator
import numpy

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

    def get_samples(self, nr_of_samples, phase, release = None, pitch_bend = None):
        sources_arr = numpy.zeros(nr_of_samples)
        result = numpy.zeros(nr_of_samples)
        notes = self.note_envelope.get_notes_for_range(self.options, phase, nr_of_samples)
        self.notes_playing = self.notes_playing.union(notes)
        (sources_arr, result) = self.render_playing_notes(result, sources_arr, nr_of_samples, phase, pitch_bend)
        (sources_arr, result) = self.render_stopped_notes(result, sources_arr, nr_of_samples, phase)
        sources_arr = numpy.add(sources_arr, numpy.where(sources_arr == 0.0, 1.0, 0.0))
        return result / sources_arr

    def render_playing_notes(self, result, sources_arr, nr_of_samples, phase, pitch_bend):
        for p in self.notes_playing:
            if not p.does_this_note_play(phase, nr_of_samples):
                continue

            start_index = p.get_start_index_for_phase(p.start_time, phase)
            stop_index = p.get_stop_index_for_phase(p.stop_time, phase, nr_of_samples)
            note_phase =  p.get_note_phase_for_phase(phase)
            length = stop_index - start_index

            for sample_generator in self.get_sample_generators_for_note(p.note):
                samples = sample_generator.get_samples(length, note_phase, None, pitch_bend[start_index:stop_index])
                result[start_index:stop_index] += numpy.multiply(samples, p.velocity)
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
                result[start_index:] += numpy.multiply(samples, p.velocity)
                sources_arr[start_index:] += 1
                for i, s in enumerate(reversed(samples)):
                    if s != 0.0:
                        break
                    sources_arr[-(i + 1)] -= 1
                postfix_len = min(len(samples), 4)
                if (samples[-postfix_len:] <= [0] * postfix_len).all():
                    stopped.add(p)
        for s in stopped:
            self.notes_stopped.remove(s)
        return (sources_arr, result)
