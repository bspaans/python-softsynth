import math

class Source(object):
    def __init__(self, options):
        self.sink = None
	self.options = options
    def connect_sink(self, sink):
        self.sink = sink
    def open(self):
        pass
    def read(self):
        yield True
    def stream(self):
        self.open()
        self.sink.open()
        try:
            for e in self.read():
                self.sink.write(e)
        except KeyboardInterrupt:
            print "Stopped."
        finally:
            self.sink.close()

class WaveFormSource(Source):
    def __init__(self, options, nr_of_samples = -1):
        super(WaveFormSource, self).__init__(options)
        self.sample_rate   = options.sample_rate
        self.byte_rate     = options.byte_rate
        self.max_value     = 2 ** (self.byte_rate * 8 - 1) - 1
        self.nr_of_samples = nr_of_samples # < 0 for unlimited or until cut off by the implementing class

        self.max_amplitude = 1.0
        self.attack_time   = options.sample_rate / 8.0
        self.decay_time    = options.sample_rate / 8.0
        self.sustain_level = 0.0

    def amplitude(self, t):
        if t < self.attack_time:
            return t / self.attack_time * self.max_amplitude
        elif t < self.attack_time + self.decay_time:
            r = (t - self.attack_time) / self.decay_time
            return self.max_amplitude - self.sustain_level * r
        else:
            return self.sustain_level
        return self.max_amplitude

class SineWaveForm(WaveFormSource):
    def __init__(self, options, frequency = None, nr_of_samples = None):
        super(SineWaveForm, self).__init__(options, nr_of_samples)
        self.frequency = frequency if frequency is not None else options.pitch_standard


    def read(self):
        cycles_per_period = 2 * math.pi * (self.frequency / self.sample_rate)
        t = 0
        while self.nr_of_samples < 0 or t < self.nr_of_samples:
            sine = self.amplitude(t) * math.sin( t * cycles_per_period) * self.max_value
            t += 1
            yield sine

    def __repr__(self):
        return "< sine wave %fHz >" % self.frequency
