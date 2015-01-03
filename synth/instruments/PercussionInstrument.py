from synth.envelopes import SegmentAmplitudeEnvelope
from synth.oscillator import OscillatorWithAmplitudeEnvelope, \
    RandomOscillatorWithAmplitudeEnvelope
from synth.new_filters import DistortionFilter
from synth.instruments.BaseInstrument import BaseInstrument
import sys

class PercussionInstrument(BaseInstrument):
    def __init__(self, options, note_envelope):
        super(PercussionInstrument, self).__init__(options, note_envelope)

    def init_note(self, options, note, freq):
        if note in [35, 36]: # kick
            amp_env = SegmentAmplitudeEnvelope()
            amp_env.add_segment(1.0, 100)
            amp_env.add_segment(0.0, 2500)
            osc = OscillatorWithAmplitudeEnvelope(options, amp_env, freq = 100)
            osc2 = OscillatorWithAmplitudeEnvelope(options, amp_env, freq = 60)
            return [osc, osc2]
        if note in [40, 38]: # snare
            amp_env = SegmentAmplitudeEnvelope()
            amp_env.release_time = 100
            amp_env.add_segment(0.55, 100)
            amp_env.add_segment(0.0, 6000)
	    dist = DistortionFilter(options, 0.05)
            osc = RandomOscillatorWithAmplitudeEnvelope(options, amp_env, freq = 100)
	    dist.set_source(osc)
            return [dist]
        if note in [42, 46, 51]: # closed hihat
            amp_env = SegmentAmplitudeEnvelope()
            amp_env.add_segment(0.1, 200)
            amp_env.add_segment(0.0, 5000)
            osc = RandomOscillatorWithAmplitudeEnvelope(options, amp_env, freq = 100)
            return [osc]
        if note in [51]: # ride
            amp_env = SegmentAmplitudeEnvelope()
            amp_env.add_segment(0.1, 100)
            amp_env.add_segment(0.0, 5000)
            osc = RandomOscillatorWithAmplitudeEnvelope(options, amp_env, freq = 100)
            amp_env = SegmentAmplitudeEnvelope()
            amp_env.add_segment(0.8, 100)
            amp_env.add_segment(0.0, 1000)
            osc2 = OscillatorWithAmplitudeEnvelope(options, amp_env, freq = 300)
            amp_env = SegmentAmplitudeEnvelope()
            amp_env.add_segment(0.8, 100)
            amp_env.add_segment(0.0, 1000)
            osc3 = OscillatorWithAmplitudeEnvelope(options, amp_env, freq = 600)
            return [osc, osc2, osc3]
        if note in [49, 55, 57]: # crash
            amp_env = SegmentAmplitudeEnvelope()
            amp_env.release_time = 100
            amp_env.add_segment(0.3, 300)
            amp_env.add_segment(0.5, 4000)
            amp_env.add_segment(0.5, 6000)
            amp_env.add_segment(0.1, 10000)
            osc = RandomOscillatorWithAmplitudeEnvelope(options, amp_env, freq = 100)
            return [osc]
        return []

    def get_sample_generators_for_note(self, note):
        if self.sample_generators[note] == []:
            #sys.stderr.write("No generators for note %d\n" % note)
            pass
        return self.sample_generators[note]
