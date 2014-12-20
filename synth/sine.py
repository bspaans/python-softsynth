#!/usr/bin/env python
import pyaudio
import struct
import math
import time

STRUCT_PACK_FORMAT = {1: 'b', 2: 'h', 4: 'i', 8: 'q'} # key is byte rate

class Options(object):
    def __init__(self):
        self.sample_rate    = 44100
        self.pitch_standard = 440  # pitch of A4
        self.byte_rate      = 2    # gives 2 ^ (8 * DEFAULT_BYTE_RATE) levels
        self.max_value     = 2 ** (self.byte_rate * 8 - 1) - 1
        self.struct_pack_format = STRUCT_PACK_FORMAT[self.byte_rate]

class FrequencyEnvelope:
    def get_frequency(self, t):
        pass

class ConstantFrequencyEnvelope:
    def __init__(self, freq):
        self.freq = freq
    def get_frequency(self, t):
        return self.freq

class BendFrequencyEnveleope:
    def __init__(self, start_freq, end_freq, bend_time):
        self.start_freq = start_freq
        self.end_freq = end_freq
        self.bend_time = 44100
    def get_frequency(self, t):
        if t < self.bend_time + 1000:
            return self.start_freq + (self.end_freq - self.start_freq) * (float(t) / self.bend_time)
        return self.end_freq

class SineWave:
    def __init__(self, frequency_envelope):
        self.frequency_envelope = frequency_envelope
    def get_amplitude(self, output_options, t):
        freq = self.frequency_envelope.get_frequency(t)
        cycles_per_period = 2 * math.pi * (float(freq) / output_options.sample_rate)
        return math.sin(t * cycles_per_period) * output_options.max_value

class Adder:
    def __init__(self):
        self.sources = []

    def add_source(self, source):
        self.sources.append(source)

    def get_amplitude(self, output_options, t):
        values = []
        for s in self.sources:
            v = s.get_amplitude(output_options, t)
            if v is not None:
                values.append(v)
        return sum(values) / len(values)

t = 0
sineA = SineWave(BendFrequencyEnveleope(0,440,500))
sineA2 = SineWave(ConstantFrequencyEnvelope(880))
sineA3 = SineWave(BendFrequencyEnveleope(3520,1760,500))
adder = Adder()
adder.add_source(sineA)
adder.add_source(sineA2)
adder.add_source(sineA3)
options = Options()

def callback(in_data, frame_count, time_info, status):
    global t, sine, options
    data = []
    for t_frame in xrange(frame_count):
        sample = struct.pack(options.struct_pack_format, int(adder.get_amplitude(options, t + t_frame)))
        data.append(sample)
    t += frame_count
    return ''.join(data), pyaudio.paContinue

output = pyaudio.PyAudio()
stream = output.open(format=pyaudio.paInt16, channels=1, rate= 44100, output=True, stream_callback=callback)
stream.start_stream()
while stream.is_active():
    time.sleep(0.1)
stream.stop_stream()
stream.close()
