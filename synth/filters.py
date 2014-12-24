

class Delay(object):

    def __init__(self, amplitude_generator, delay, wet_dry = 0.5):
        self.amplitude_generator = amplitude_generator
        self.delay = delay
        self.wet_dry = wet_dry
        self.values = [0.0] * self.delay
        self.value_index = 0

    def get_amplitude(self, output_options, t):
        current = self.amplitude_generator.get_amplitude(output_options, t)
        self.values[self.value_index] = current 
        self.value_index += 1
        if self.value_index >= self.delay:
            self.value_index = 0
        if t < self.delay:
            return current

        delay_index = self.value_index - self.delay
        if delay_index < 0:
            delay_index += self.delay
        delay = self.values[delay_index]
        v = self.wet_dry * current + (1.0 - self.wet_dry) * delay
        return v


