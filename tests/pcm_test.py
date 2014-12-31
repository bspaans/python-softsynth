from nose.tools import *
from synth.pcm import PCMWithFrequency, wavefile_cache
from synth.options import Options
import numpy

class Test_PCMWithFrequency(object):

    def setup(self):
        self.wavefile = numpy.array([10, 11, 12, 13, 14])
        wavefile_cache["test.wav"] = self.wavefile
        self.options = Options()

    def teardown(self):
        pass

    def test_get_base_frequency(self):
        unit = PCMWithFrequency(self.options, "test.wav")
        nr_of_samples = 5
        phase = 0
        samples = unit.get_samples(nr_of_samples, phase)
        assert_equal(len(samples), 5)
        assert((samples == self.wavefile).all())

    def test_get_half_base_frequency(self):
        unit = PCMWithFrequency(self.options, "test.wav", self.options.pitch_standard / 2)
        nr_of_samples = 5
        phase = 0
        samples = unit.get_samples(nr_of_samples, phase)
        assert_equal(len(samples), 5)
        assert_almost_equal(samples[0], 10)
        assert_almost_equal(samples[1], 10.5)
        assert_almost_equal(samples[2], 11)
        assert_almost_equal(samples[3], 11.5)
        assert_almost_equal(samples[4], 12)
