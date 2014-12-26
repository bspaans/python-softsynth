from nose.tools import *
from synth.envelopes import ConstantFrequencyEnvelope

class Test_ConstantFrequencyEnvelope(object):

    def setup(self):
        self.freq = 100.0
        self.phase = 0
        self.nr_of_samples = 1000
        self.unit = ConstantFrequencyEnvelope(self.freq)

    def test_ConstantFrequencyEnvelope_general_usage(self):
        freqs = self.unit.get_frequencies(self.phase, self.nr_of_samples)
        assert len(freqs) == self.nr_of_samples
        assert all(map(lambda f: f == self.freq, freqs))

    def test_ConstantFrequencyEnvelope_different_phase(self):
        self.phase = 50
        freqs = self.unit.get_frequencies(self.phase, self.nr_of_samples)
        assert len(freqs) == self.nr_of_samples
        assert all(map(lambda f: f == self.freq, freqs))
