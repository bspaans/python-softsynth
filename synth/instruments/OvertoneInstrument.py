from synth.envelopes import SegmentAmplitudeEnvelope
from synth.oscillator import OscillatorWithFrequencyAndAmplitudeControl
from synth.new_filters import Delay, DistortionFilter
from synth.instruments.BaseInstrument import BaseInstrument
from synth.envelopes import ConstantFrequencyEnvelope


class OvertoneInstrument(BaseInstrument):

    def __init__(self, options, note_envelope, overtones = 1, attack = 4000, decay = 4000, sustain = 0.5, release = 100):
        self.overtones = 1 if overtones <= 1 else overtones
        self.attack = attack
        self.decay = decay
        self.sustain = sustain
        self.release = release
        super(OvertoneInstrument, self).__init__(options, note_envelope)

    def init_note(self, options, note, freq):
        result = []
        for d in xrange(self.overtones, self.overtones + 1):
            amp_env = SegmentAmplitudeEnvelope()
            amp_env.release_time = self.release
            amp_env.add_segment(1.0 / (d + 1), self.attack)
            amp_env.add_segment(self.sustain / (d + 1), self.decay)
            freq_env = ConstantFrequencyEnvelope(d * freq)
            osc = OscillatorWithFrequencyAndAmplitudeControl(options, freq_env, amp_env)
	    delay = Delay(options, 4)
	    delay.set_source(osc)
	    dist = DistortionFilter(options, 0.01)
	    dist.set_source(osc)
        result.append(dist)
        return result

