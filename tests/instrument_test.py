from nose.tools import *
from synth.instruments import BaseInstrument 
from synth.options import Options
from synth.note_envelopes import NoteEvent


class Test_BaseInstrument(object):

    class DummyNoteEnvelope(object):
        def __init__(self, cb):
            self.callback = cb
        def get_notes_for_range(self, options, phase, nr_of_samples):
            return self.callback(phase, nr_of_samples)

    class DummySampleGenerator(object):
        def __init__(self, note):
            self.note = note
        def get_samples(self, nr_of_samples, phase, release = None):
            if release is not None:
                return [0.0] * nr_of_samples
            result = []
            for t in xrange(nr_of_samples):
                result.append(self.note + phase)
            return result

    def init_note(self, options, note, freq):
        return [Test_BaseInstrument.DummySampleGenerator(note)]

    def test_get_samples_one_note_one_phase(self):
        options = Options()
        notes = Test_BaseInstrument.DummyNoteEnvelope(
                lambda phase, nr_of_samples: [NoteEvent(0, 1, 69)])
        BaseInstrument.init_note = self.init_note
        self.unit = BaseInstrument(options, notes)
        samples = self.unit.get_samples(10, 0)
        assert_equal(samples[0], 69)
        assert_equal(samples[5], 74)
        assert_equal(samples[9], 78)

    def test_get_samples_one_note_multiple_phases(self):
        options = Options()
        notes = Test_BaseInstrument.DummyNoteEnvelope(
                lambda phase, nr_of_samples: [NoteEvent(phase, 1, phase + 69)])
        BaseInstrument.init_note = self.init_note
        self.unit = BaseInstrument(options, notes)
        samples = self.unit.get_samples(10, 0)
        assert_equal(samples[0], 69)
        assert_equal(samples[9], 78)
        samples = self.unit.get_samples(10, 10)
        assert_equal(samples[0], 79)
        assert_equal(samples[9], 88)

    def test_get_samples_one_half_note_one_phase(self):
        options = Options()
        notes = Test_BaseInstrument.DummyNoteEnvelope(
                lambda phase, nr_of_samples: [NoteEvent(0, nr_of_samples / 2, 69)])
        BaseInstrument.init_note = self.init_note
        self.unit = BaseInstrument(options, notes)
        samples = self.unit.get_samples(10, 0)
        assert_equal(samples[0], 69)
        assert_equal(samples[1], 70)
        assert_equal(samples[2], 71)
        assert_equal(samples[3], 72)
        assert_equal(samples[4], 73)
        assert_equal(samples[5], 0)
        assert_equal(samples[6], 0)

    def test_get_samples_two_half_notes_one_phase(self):
        options = Options()
        notes = Test_BaseInstrument.DummyNoteEnvelope(
                lambda phase, nr_of_samples: [(0, 0, nr_of_samples / 2, 69), 
                    (nr_of_samples / 2, 0, nr_of_samples / 2, 10)])
        notes = Test_BaseInstrument.DummyNoteEnvelope(
                lambda phase, nr_of_samples: [NoteEvent(0, nr_of_samples / 2, 69),
                    NoteEvent(nr_of_samples / 2, nr_of_samples /2, 10)])
        BaseInstrument.init_note = self.init_note
        self.unit = BaseInstrument(options, notes)
        samples = self.unit.get_samples(10, 0)
        assert_equal(len(samples), 10)
        assert_equal(samples[0], 69 / 2.0)
        assert_equal(samples[1], 70 / 2.0)
        assert_equal(samples[2], 71 / 2.0)
        assert_equal(samples[3], 72 / 2.0)
        assert_equal(samples[4], 73 / 2.0)
        assert_equal(samples[5], 10 / 2.0)
        assert_equal(samples[6], 11 / 2.0)
        assert_equal(samples[7], 12 / 2.0)
        assert_equal(samples[8], 13 / 2.0)
        assert_equal(samples[9], 14 / 2.0)
