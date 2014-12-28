from synth.oscillator import Oscillator
from synth.options import Options
from nose.tools import *

class Test_Oscillator(object):

    def setup(self):
        self.options = Options()
        self.freq = 441.0
        self.unit = Oscillator(self.options, self.freq)

    def test_get_samples_one_period_at_zero_phase(self):
        period = int(self.options.sample_rate / self.freq) # 100
        samples = self.unit.get_samples(period + 1, 0)
        assert_equals(len(samples), period + 1)
        assert_equals(samples[0], 0.0)
        assert_almost_equals(samples[period / 4], 1.0)
        assert_almost_equals(samples[period / 2], 0.0)
        assert_almost_equals(samples[period / 4 * 3], -1.0)
        assert_almost_equals(samples[period], 0.0)

