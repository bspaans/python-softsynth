from synth.options import Options, FrequencyTable
from nose.tools import *


class Test_FrequencyTable(object):

    def test_frequency_table(self):
        options = Options()
        options.pitch_standard = 440.0
        self.unit = FrequencyTable(options)

        assert_equal(self.unit.midi_frequencies[69], options.pitch_standard) 
        assert_equal(self.unit.midi_frequencies[81], options.pitch_standard * 2) 
        assert_equal(self.unit.midi_frequencies[93], options.pitch_standard * 4) 
