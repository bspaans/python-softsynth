from nose.tools import *
from synth.envelopes import ConstantAmplitudeEnvelope, SegmentAmplitudeEnvelope

class Test_ConstantAmplitudeEnvelope(object):

    def setup(self):
        self.nr_of_samples = 1000
        self.max_amplitude = 0.5
        self.unit = ConstantAmplitudeEnvelope(self.max_amplitude)

    def test_at_phase_zero(self):
        phase = 0
        amps = self.unit.get_amplitudes(phase, self.nr_of_samples)
        assert_equals(len(amps), self.nr_of_samples)
        map(lambda a: assert_equal(a, self.max_amplitude), amps)

    def test_with_different_phase(self):
        phase = 50
        amps = self.unit.get_amplitudes(phase, self.nr_of_samples)
        assert_equals(len(amps), self.nr_of_samples)
        map(lambda a: assert_equal(a, self.max_amplitude), amps)

class Test_SegmentAmplitudeEnvelope(object):

    def setup(self):
        self.unit = SegmentAmplitudeEnvelope()

    def test_single_segment_get_amplitudes_for_whole_range_at_phase_zero(self):
        level = 1.0
        duration = 1000
        phase = 0
        self.unit.add_segment(level, duration)
        amplitudes = self.unit.get_amplitudes(phase, duration)
        assert_equal(len(amplitudes), duration)
        assert_almost_equal(amplitudes[0], 0.0)
        assert_almost_equal(amplitudes[duration - 1], level)

    def test_single_segment_get_amplitudes_for_whole_range_at_different_phase(self):
        level = 1.0
        duration = 10
        phase = 2
        self.unit.add_segment(level, duration)
        amplitudes = self.unit.get_amplitudes(phase, duration)
        assert_equal(len(amplitudes), duration)
        assert_almost_equal(amplitudes[(duration / 2) - phase], 
                level / (duration -1) * (duration / 2))
        assert_almost_equal(amplitudes[duration - phase - 1], 1.0)
        for t in amplitudes[duration - phase:]:
            assert_almost_equal(t, 1.0)

    def test_multiple_segments_get_amplitudes_for_whole_range_at_phase_zero(self):
        level = 1.0
        level2 = 1.0 - level
        duration = 1000
        phase = 0
        nr_of_samples = duration * 2
        self.unit.add_segment(level, duration)
        self.unit.add_segment(level2, duration)
        amplitudes = self.unit.get_amplitudes(phase, nr_of_samples)
        assert_equal(len(amplitudes), nr_of_samples)
        assert_equal(amplitudes[0], 0.0)
        assert_almost_equal(amplitudes[nr_of_samples - 1], 0.0)
        assert_almost_equal(amplitudes[duration], level)

