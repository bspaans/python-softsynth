from synth.new_filters import Delay
from synth.options import Options
from nose.tools import *
import numpy

class Test_Delay(object):

    class DummySampleGenerator(object):
        def __init__(self, note):
            self.note = note
        def get_samples(self, nr_of_samples, phase, release = None):
            if release is not None:
                return numpy.zeros(nr_of_samples)
            result = numpy.arange(phase, phase + nr_of_samples)
            return result + float(self.note)

    def setup(self):
        pass

    def teardown(self):
        pass

    def test_delay_phase_zero(self):
        options = Options()
        delay_by = 1
        self.unit = Delay(options, delay_by)
        self.unit.set_source(Test_Delay.DummySampleGenerator(69))
        nr_of_samples = 10
        phase = 0
        samples = self.unit.get_samples(nr_of_samples, phase)
        assert_equal(len(samples), nr_of_samples)
        assert_equal(samples[0], 69)
        assert_equal(samples[1], 69.5)
        assert_equal(samples[2], 70.5)
        assert_equal(samples[3], 71.5)

    def test_delay_with_different_phase(self):
        options = Options()
        delay_by = 1
        self.unit = Delay(options, delay_by)
        self.unit.set_source(Test_Delay.DummySampleGenerator(69))
        nr_of_samples = 3
        phase = 0
        samples = self.unit.get_samples(nr_of_samples, phase)
        assert_equal(len(samples), nr_of_samples)
        assert_equal(samples[0], 69)
        assert_equal(samples[1], 69.5)
        assert_equal(samples[2], 70.5)

        phase += nr_of_samples
        samples = self.unit.get_samples(nr_of_samples, phase)
        assert_equal(len(samples), nr_of_samples)
        assert_equal(samples[0], 71.5)
        assert_equal(samples[1], 72.5)
        assert_equal(samples[2], 73.5)

    def test_delay_longer_than_nr_of_samples(self):
        options = Options()
        delay_by = 3
        self.unit = Delay(options, delay_by)
        self.unit.set_source(Test_Delay.DummySampleGenerator(69))
        nr_of_samples = 2
        phase = 0
        samples = self.unit.get_samples(nr_of_samples, phase)
        assert_equal(len(samples), nr_of_samples)
        assert_equal(samples[0], 69)
        assert_equal(samples[1], 70)

        phase += nr_of_samples
        samples = self.unit.get_samples(nr_of_samples, phase)
        assert_equal(samples[0], 71.0)
        assert_equal(samples[1], 70.5)

        phase += nr_of_samples
        samples = self.unit.get_samples(nr_of_samples, phase)
        assert_equal(samples[0], 71.5)
        assert_equal(samples[1], 72.5)

        phase += nr_of_samples
        samples = self.unit.get_samples(nr_of_samples, phase)
        assert_equal(samples[0], 73.5)
        assert_equal(samples[1], 74.5)
