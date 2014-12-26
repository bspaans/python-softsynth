import numpy
import sys

class ConstantFrequencyEnvelope(object):
    def __init__(self, freq):
        self.freq = freq
    def get_frequency(self, options, t):
        return self.freq
    def get_frequencies(self, phase, nr_of_samples):
        result = numpy.empty([nr_of_samples])
        result.fill(self.freq)
        return result
        

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
    def get_amplitudes(self, phase, nr_of_samples):
        return numpy.full([nr_of_samples], self.max_amplitude)
    
class SegmentAmplitudeEnvelope(object):
    def __init__(self):
        self.segments = []
        self.last_level = 0.0
        self.last_position = 0
        self.segment_array = numpy.array([])

    def add_segment(self, level, duration):
        segment_range = level - self.last_level
        step_size = segment_range / (duration - 1)
        arr = numpy.full([duration], step_size)
        arr[0] = self.last_level 
        arr = arr.cumsum()
        self.segment_array = numpy.concatenate([self.segment_array, arr])
        self.last_position += duration
        self.last_level = level

    def get_amplitudes(self, phase, nr_of_samples):
        index_start = phase
        index_stop = phase + nr_of_samples 
        if index_start >= self.last_position:
            return numpy.full([nr_of_samples], self.last_level)
        if index_stop > self.last_position:
            arr = self.segment_array[index_start:]
            rest = numpy.full([nr_of_samples - len(arr)], self.last_level)
            return numpy.concatenate([arr, rest])
        else:
            return self.segment_array[index_start:index_stop]


class ADSRAmplitudeEnvelope(object):
    def __init__(self, max_amplitude = 1.0):
        self.max_amplitude = max_amplitude
        self.segment_envelope = None
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

    def get_segment_envelope(self, options):
        if self.segment_envelope is not None:
            return self.segment_envelope
        s = SegmentAmplitudeEnvelope()
        s.add_segment(self.max_amplitude, float(self.attack) * options.sample_rate)
        s.add_segment(self.sustain_level, float(self.delay) * options.sample_rate)
        self.segment_envelope = s
        return s

    def get_amplitudes(self, phase, nr_of_samples):
        return self.get_segment_envelope().get_amplitudes(phase, nr_of_samples)

