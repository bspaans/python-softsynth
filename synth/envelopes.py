
class ConstantFrequencyEnvelope(object):
    def __init__(self, freq):
        self.freq = freq
    def get_frequency(self, options, t):
        return self.freq

class BendFrequencyEnvelope(object):
    def __init__(self, start_freq, end_freq, bend_time = 44100):
        self.start_freq = start_freq
        self.end_freq = end_freq
        self.bend_time = bend_time

    def get_frequency(self, options, t):
        if t < self.bend_time:
            return self.start_freq + (self.end_freq - self.start_freq) * (float(t) / self.bend_time)
        return self.end_freq

class ConstantAmplitudeEnvelope(object):
    def __init__(self, max_amplitude):
        self.max_amplitude = max_amplitude
    def get_amplitude(self, options, t):
        return self.max_amplitude

class ADSRAmplitudeEnvelope(object):
    def __init__(self, max_amplitude = 1.0):
        self.max_amplitude = max_amplitude
        self.set_attack(0.01)
        self.set_decay(0.1)
        self.set_sustain(0.0)
        self.set_release(1.0)
    def set_attack(self, v):
        self.attack = v
    def set_decay(self, v):
        self.decay = v
    def set_sustain(self, v):
        self.sustain_level = v
    def set_release(self, v):
        self.release = v
    def get_amplitude(self, options, t, stopped_since = None):
        attack_time = options.sample_rate * float(self.attack)
        if t < attack_time:
            return (t / attack_time) * self.max_amplitude
        decay_time = options.sample_rate * float(self.decay)
        if t < attack_time + decay_time:
            return self.max_amplitude - ((t - attack_time) / decay_time) * (self.max_amplitude - self.sustain_level)
        if stopped_since is None:
            return self.sustain_level
        release_time = options.sample_rate * float(self.release)
        return self.sustain_level - ((t - stopped_since) / release_time) * self.sustain_level

