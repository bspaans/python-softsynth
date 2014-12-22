from envelopes import ADSRAmplitudeEnvelope, BendFrequencyEnvelope, \
                      ConstantFrequencyEnvelope, ConstantAmplitudeEnvelope
from waves import SineWave, SquareWave, RandomWave, Adder

class BaseInstrument(object):
    def __init__(self, frequency_table, note_envelope):
        self.frequency_table = frequency_table
        self.notes = {}
        self.note_envelope = note_envelope
        self.init()

    def init(self):
        pass

    def get_amplitude(self, options, t):
        value = 0
        playing = 0
        for note, relative_t in self.note_envelope.get_notes(options, t):
            v = self.notes[note].get_amplitude(options, relative_t)
            if v is not None:
                value += v
                playing += 1
        if playing == 0:
            return 0
        return value / playing

class OvertoneInstrument(BaseInstrument):
    def __init__(self, frequency_table, note_envelope):
        super(OvertoneInstrument, self).__init__(frequency_table, note_envelope)

    def init(self):
        for note, freq in self.frequency_table.midi_frequencies.iteritems():
            amp_env = ADSRAmplitudeEnvelope(1.0)
            amp_env.set_attack(0.01)
            amp_env.set_decay(0.1)
            amp_env.set_sustain(0.0)
            freq_env = ConstantFrequencyEnvelope(freq)
            adder = Adder()
            adder.add_source(SineWave(ConstantFrequencyEnvelope(freq), amp_env))
            adder.add_source(SineWave(ConstantFrequencyEnvelope(freq * 2), amp_env))
            adder.add_source(SineWave(ConstantFrequencyEnvelope(freq * 3), amp_env))
            self.notes[note] = SineWave(ConstantFrequencyEnvelope(freq), amp_env)

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

