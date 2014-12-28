from envelopes import ADSRAmplitudeEnvelope, BendFrequencyEnvelope, \
                      ConstantFrequencyEnvelope, ConstantAmplitudeEnvelope
from waves import SineWave, SquareWave, RandomWave, Adder
from filters import Delay, Filter, Flanger, GlitchFlanger

class PercussionInstrument(BaseInstrument):
    def __init__(self, frequency_table, note_envelope):
        super(PercussionInstrument, self).__init__(frequency_table, note_envelope)

    def init(self):
        amp_env = ADSRAmplitudeEnvelope(1.0)
        amp_env.set_attack(0.0000001)
        amp_env.set_decay(0.15)
        amp_env.set_sustain(0.0)
        freq_env1 = BendFrequencyEnvelope(60, 50, 10000)
        adder = Adder()
        adder.add_source(SquareWave(freq_env1, amp_env))
        self.notes[47] = adder # kick1
        self.notes[48] = adder # kick2
        amp_env = ADSRAmplitudeEnvelope(1.0)
        self.notes[52] = RandomWave(amp_env) # snare
        amp_env = ADSRAmplitudeEnvelope(0.1)
        amp_env.set_attack(0.00001)
        amp_env.set_decay(0.05)
        amp_env.set_sustain(0.0)
        self.notes[54] = RandomWave(amp_env) # closed hihat
        amp_env = ADSRAmplitudeEnvelope(0.3)
        amp_env.set_attack(0.0)
        amp_env.set_decay(2.0)
        amp_env.set_sustain(1.0)
        self.notes[61] = RandomWave(amp_env) # crash
        self.notes[69] = RandomWave(amp_env) # crash

