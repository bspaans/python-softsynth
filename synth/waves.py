import math
import random

class SineWave(object):
    def __init__(self, frequency_envelope, amplitude_envelope):
        self.frequency_envelope = frequency_envelope
        self.sample_rate_adjustment = { 44100: 2.0 * math.pi / 44100.0 }
        self.amplitude_envelope = amplitude_envelope

    def get_amplitude(self, output_options, t):
        freq = self.frequency_envelope.get_frequency(output_options, t)
        amp  = self.amplitude_envelope.get_amplitude(output_options, t)
        v = math.sin(self.sample_rate_adjustment[output_options.sample_rate] * freq * t)
        return amp * v * output_options.max_value

class SquareWave(object):
    def __init__(self, frequency_envelope, amplitude_envelope):
        self.frequency_envelope = frequency_envelope
        self.sample_rate_adjustment = { 44100: 2.0 * math.pi / 44100.0 }
        self.amplitude_envelope = amplitude_envelope

    def get_amplitude(self, output_options, t):
        freq = self.frequency_envelope.get_frequency(output_options, t)
        amp  = self.amplitude_envelope.get_amplitude(output_options, t)
        v = math.sin(self.sample_rate_adjustment[output_options.sample_rate] * freq * t)
        if v >= 0:
            v = 1.0
        else:
            v = -1.0
        return amp * v * output_options.max_value

class RandomWave(object):
    def __init__(self, amplitude_envelope):
        self.amplitude_envelope = amplitude_envelope

    def get_amplitude(self, output_options, t):
        amp  = self.amplitude_envelope.get_amplitude(output_options, t)
        v = (random.random() - 0.5) * 2
        return amp * v * output_options.max_value

class Adder(object):
    def __init__(self):
        self.sources = []
        self.stopped = {}
    def add_source(self, source):
        self.sources.append(source)
    def stop_source(self, source):
        self.stopped[source] = True
    def get_amplitude(self, output_options, t):
        num = 0
        value = 0
        for s in self.sources:
            v = s.get_amplitude(output_options, t)
            if v is not None:
                value += v
                num += 1
        return value / num

