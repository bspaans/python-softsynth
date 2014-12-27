import random
class Filter(object):

    def __init__(self, sample_generators):
        self.sample_generators = sample_generators
        self.amp_in = 0.5
        self.amp_in_delay1 = 0.5
        self.amp_in_delay2 = 0.30
        self.amp_out_feedback1 = 0.1
        self.amp_out_feedback2 = 0.2
        self.delay1 = 0.0
        self.delay2 = 0.0
        self.feedback1 = 0.0
        self.feedback2 = 0.0

    def get_amplitude(self, output_options, t):
        value_in = self.amplitude_generator.get_amplitude(output_options, t)

        value_out = (self.amp_in * value_in) \
                  + (self.amp_in_delay1 * self.delay1) \
                  + (self.amp_in_delay2 * self.delay2) \
                  - (self.amp_out_feedback1 * self.feedback1) \
                  - (self.amp_out_feedback2 * self.feedback2)

        self.delay2 = self.delay1
        self.delay1 = value_in
        self.feedback2 = self.feedback1
        self.feedback1 = value_out
        return value_out

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


class Flanger(object):

    def __init__(self, amplitude_generator, wet_dry = 0.1, max_delay = 10, min_delay = 5):
        self.amplitude_generator = amplitude_generator
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.original_max_delay = max_delay
        self.delay_steps = self.max_delay - self.min_delay
        self.wet_dry = wet_dry
        self.values = [0.0] * self.max_delay
        self.value_index = 0

    def get_amplitude(self, output_options, t):
        current = self.amplitude_generator.get_amplitude(output_options, t)
        self.values[self.value_index] = current 
        self.value_index += 1
        if self.value_index >= self.max_delay:
            self.value_index = 0
        if t < self.min_delay:
            return current

        delay_step = int(t % self.delay_steps)
        delay_index = self.value_index - (self.min_delay + delay_step)
        if delay_index < 0:
            delay_index += self.max_delay
        delay = self.values[delay_index]
        v = self.wet_dry * current + (1.0 - self.wet_dry) * delay
        return v

class GlitchFlanger(Flanger):
    def __init__(self, amplitude_generator, wet_dry = 0.1, max_delay = 20, min_delay =5, change_range_every = 1000):
        super(GlitchFlanger, self).__init__(amplitude_generator, wet_dry, max_delay, min_delay)
        self.change_range_every = change_range_every

    def get_amplitude(self, output_options, t):
        v = Flanger.get_amplitude(self, output_options, t)
        if t % self.change_range_every == 0:
            self.max_delay = random.randrange(self.min_delay, self.original_max_delay)
        return v

