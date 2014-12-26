from nose.tools import *
from synth.envelopes import ConstantFrequencyEnvelope, \
        ConstantAmplitudeEnvelope, SegmentAmplitudeEnvelope

class Test_ConstantFrequencyEnvelope(object):

    def setup(self):
        self.freq = 100.0
        self.nr_of_samples = 1000
        self.unit = ConstantFrequencyEnvelope(self.freq)

    def test_at_phase_zero(self):
        phase = 0
        freqs = self.unit.get_frequencies(phase, self.nr_of_samples)
        assert_equal(len(freqs), self.nr_of_samples)
        map(lambda f: assert_equal(f, self.freq), freqs)

    def test_with_different_phase(self):
        phase = 50
        freqs = self.unit.get_frequencies(phase, self.nr_of_samples)
        assert_equal(len(freqs), self.nr_of_samples)
        map(lambda f: assert_equal(f, self.freq), freqs)

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

    def test_add_segment(self):
        level = 1.0
        level2 = 1.0 - level
        duration = 1000
        self.unit.add_segment(level, duration)
        self.unit.add_segment(level2, duration)

        segment = self.unit.segments[0]
        segment_start, segment_stop, segment_level, segment_arr = segment

        assert_equal(segment_start, 0)
        assert_equal(segment_stop, duration)
        assert_equal(segment_level, level)
        assert_equal(len(segment_arr), duration)
        assert_almost_equal(segment_arr[0], 0.0)
        assert_almost_equal(segment_arr[(duration - 1) / 2 + 1], level / 2, places = 2)
        assert_almost_equal(segment_arr[duration - 1], level)

        segment = self.unit.segments[1]
        segment_start, segment_stop, segment_level, segment_arr = segment

        assert_equal(segment_start, duration)
        assert_equal(segment_stop, duration + duration)
        assert_equal(segment_level, level2)
        assert_equal(len(segment_arr), duration)
        assert_almost_equal(segment_arr[0], level)
        assert_almost_equal(segment_arr[1], 
                level + ((level2 - level)/duration), places = 2)
        assert_almost_equal(segment_arr[(duration - 1) / 2], 
                level +((level2 - level)/(duration - 1))*(duration - 1) / 2, places = 2)
        assert_almost_equal(segment_arr[duration - 1], level2)

    def test_single_segment_get_samples_for_whole_range_at_phase_zero(self):
        level = 1.0
        duration = 1000
        phase = 0
        self.unit.add_segment(level, duration)
        samples = self.unit.get_amplitudes(phase, duration)
        assert_equal(len(samples), duration)
        assert_almost_equal(samples[0], 0.0)
        assert_almost_equal(samples[duration - 1], level)

    def test_single_segment_get_samples_for_whole_range_at_different_phase(self):
        level = 1.0
        duration = 10
        phase = 2
        self.unit.add_segment(level, duration)
        samples = self.unit.get_amplitudes(phase, duration)
        assert_equal(len(samples), duration)
        assert_almost_equal(samples[(duration / 2) - phase], 
                level / (duration -1) * (duration / 2))
        assert_almost_equal(samples[duration - phase - 1], 1.0)
        for t in samples[duration - phase:]:
            assert_almost_equal(t, 1.0)
