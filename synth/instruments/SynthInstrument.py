from synth.envelopes import SegmentAmplitudeEnvelope
from synth.oscillator import OscillatorWithAmplitudeEnvelope
from synth.instruments.BaseInstrument import BaseInstrument

class SynthInstrument(BaseInstrument):
    def __init__(self, options, note_envelope):
        super(SynthInstrument, self).__init__(options, note_envelope)
    def init_note(self, options, note, freq):
        amp_env = SegmentAmplitudeEnvelope()
        amp_env.add_segment(1.0, 1000)
        amp_env.add_segment(0.5, 10000)
        osc1= OscillatorWithAmplitudeEnvelope(options, amp_env, freq)
        return [osc1]
