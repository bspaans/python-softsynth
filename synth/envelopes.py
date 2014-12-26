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

    def add_segment(self, level, duration):
        segment_range = level - self.last_level
        step_size = segment_range / (duration - 1)
        arr = numpy.full([duration], step_size)
        arr[0] = self.last_level 
        arr = arr.cumsum()
        arr = numpy.add(arr, self.last_level)
        self.segments.append((self.last_position, self.last_position + duration, level, arr))
        self.last_position += duration
        self.last_level = level

    def get_amplitudes(self, phase, nr_of_samples):
        result = numpy.empty([nr_of_samples])
        result_length = 0
        last_level = 0.0
        for (start, stop, level, arr) in self.segments:
            if phase >= start and phase < stop:
                index = phase - start
                max_length = stop - phase
                if max_length > nr_of_samples - result_length:
                    result_max_bound = nr_of_samples
                    arr_max_bound = index + nr_of_samples - result_length
                else:
                    result_max_bound = result_length + max_length
                    arr_max_bound = len(arr)
                result[result_length:result_max_bound] = arr[index:arr_max_bound]
                result[result_length] += last_level
                result[result_length] /= 2
                result_length = result_max_bound
            if result_length >= nr_of_samples:
                return result
            last_level = level

        if result_length < nr_of_samples:
            result[result_length:] = last_level
        return result

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

