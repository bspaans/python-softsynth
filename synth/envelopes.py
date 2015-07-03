import numpy
import sys
import random

class ConstantFrequencyEnvelope(object):
    def __init__(self, freq):
        self.freq = float(freq)
    def get_frequencies(self, nr_of_samples, phase, release = None, pitch_bend = None):
        result = numpy.full([nr_of_samples], self.freq)
        if pitch_bend is not None:
            result *= (2 ** ((pitch_bend * 19) / 1200.0))
        phases = numpy.arange(phase, phase + nr_of_samples)
        return result, phases

class SemiToneBendFrequencyEnvelope(object):
    def __init__(self, freq):
        self.base_freq = float(freq)
        self.semitones = 0
    def get_frequencies(self, nr_of_samples, phase, release = None):
        result = numpy.full([nr_of_samples], self.base_freq)
        phases = numpy.arange(phase, phase + nr_of_samples)
        return result, phases

class ConstantAmplitudeEnvelope(object):
    def __init__(self, max_amplitude):
        self.max_amplitude = max_amplitude
    def get_amplitudes(self, phase, nr_of_samples):
        return numpy.full([nr_of_samples], self.max_amplitude)
    
class SegmentAmplitudeEnvelope(object):
    def __init__(self):
        self.segments = []
        self.last_level = 0.0
        self.last_position = 0
        self.release_time = 50
        self.segment_array = None
        self.segment_arrays = []

    def add_segment(self, level, duration):
        if duration <= 1:
            step_size = level
            duration = 1
        else:
            segment_range = level - self.last_level
            step_size = segment_range / (duration - 1)
        
        arr = numpy.full([duration], step_size)
        arr[0] = self.last_level 
        arr = arr.cumsum()
        self.segment_arrays.append(arr)
        self.last_position += duration
        self.last_level = level

    def get_segment_array(self):
        if self.segment_array is not None:
            return self.segment_array
        self.segment_array = numpy.concatenate(self.segment_arrays)
        return self.segment_array

    def get_amplitudes(self, phase, nr_of_samples, release = None):
        index_start = phase
        index_stop = phase + nr_of_samples 
        if release is not None:
            last_level = self.last_level
            if release <= self.last_position:
                segments = self.get_segment_array()
                last_level = segments[release - 1]
            return self.get_release_amplitudes(nr_of_samples, last_level, phase - release)
        if index_start >= self.last_position:
            return numpy.full([nr_of_samples], self.last_level)
        segments = self.get_segment_array()
        if index_stop > self.last_position:
            arr = segments[index_start:]
            rest = numpy.full([nr_of_samples - len(arr)], self.last_level)
            return numpy.concatenate((arr, rest))
        else:
            return segments[index_start:index_stop]

    def get_release_amplitudes(self, nr_of_samples, last_level, phase):
        if phase >= self.release_time or self.last_level == 0.0:
            return numpy.zeros(nr_of_samples)
        step_size = last_level / float(self.release_time)
        result = numpy.full([nr_of_samples], -step_size)
        result[0] = last_level - (phase * step_size)
        result = result.cumsum()
        if phase + nr_of_samples > self.release_time:
            result[self.release_time - phase:] = 0.0
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
    def get_segment_envelope(self, options):
        if self.segment_envelope is not None:
            return self.segment_envelope
        s = SegmentAmplitudeEnvelope()
        s.add_segment(self.max_amplitude, float(self.attack) * options.sample_rate)
        s.add_segment(self.sustain_level, float(self.delay) * options.sample_rate)
        self.segment_envelope = s
        return s
    def get_amplitudes(self, phase, nr_of_samples, release = None):
        return self.get_segment_envelope().get_amplitudes(phase, nr_of_samples, release)

