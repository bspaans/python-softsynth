#!/usr/bin/env python

import math
import wave
import struct

DEFAULT_SAMPLE_RATE       = 44100
PITCH_STANDARD            = 440  # pitch of A4
DEFAULT_BYTE_RATE         = 2    # gives 2 ^ (8 * DEFAULT_BYTE_RATE) levels

STRUCT_PACK_FORMAT = { 1: 'b', 2: 'h', 4: 'i', 8: 'q' }


class Source(object):
    def __init__(self):
        self.sink = None
    def connect_sink(self, sink):
        self.sink = sink
    def read(self):
        yield True
    def stream(self):
        self.sink.open()
        try:
            for e in self.read():
                self.sink.write(e)
        finally:
            self.sink.close()

class Sink(object):
    def open(self):
        pass # setup processing
    def write(self, elem):
        pass # do some processing
    def close(self):
        pass # finish of processing


class WaveForm(Source):
    def __init__(self, frequency = PITCH_STANDARD):
        super(WaveForm, self).__init__()
        self.frequency   = frequency
        self.sample_rate = DEFAULT_SAMPLE_RATE
        self.byte_rate   = DEFAULT_BYTE_RATE
        self.nr_samples  = self.sample_rate
        self.max_value   = 2 ** (self.byte_rate * 8 - 1) - 1


class SineWaveForm(WaveForm):
    def __init__(self, frequency = PITCH_STANDARD):
        super(SineWaveForm, self).__init__(frequency)

    def read(self):
        cycles_per_period = 2 * math.pi * self.frequency / self.sample_rate
        t = 0
        while True:
            sine = math.sin( t * cycles_per_period) * self.max_value
            t += 1
            yield sine


class WaveWriter(Sink):

    def __init__(self, filename):
        super(WaveWriter, self).__init__()
        self.sample_rate   = DEFAULT_SAMPLE_RATE
        self.byte_rate     = DEFAULT_BYTE_RATE
        self.struct_format = STRUCT_PACK_FORMAT[self.byte_rate]
        self.filename      = filename

    def open(self):
        self.data = []

    def write(self, elem):
        sample = struct.pack(self.struct_format, int(elem))
        self.data.append(sample)

    def close(self):
        w = wave.open(self.filename, "w")
        w.setnchannels(1)
        w.setsampwidth(self.byte_rate)
        w.setframerate(self.sample_rate)
        w.writeframes(''.join(self.data))
        w.close()


if __name__ == '__main__':
    sine_wave = SineWaveForm()
    wave_writer = WaveWriter("sample.wav")
    sine_wave.connect_sink(wave_writer)
    sine_wave.stream()
