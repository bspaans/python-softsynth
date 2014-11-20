#!/usr/bin/env python

import math
import wave
import struct
import uuid

DEFAULT_SAMPLE_RATE       = 44100
PITCH_STANDARD            = 440  # pitch of A4
DEFAULT_BYTE_RATE         = 2    # gives 2 ^ (8 * DEFAULT_BYTE_RATE) levels

STRUCT_PACK_FORMAT = { 1: 'b', 2: 'h', 4: 'i', 8: 'q' }


class Source(object):
    def __init__(self):
        self.sink = None
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

class Sink(object):
    def open(self):
        pass # setup processing
    def write(self, elem):
        pass # do some processing
    def close(self):
        pass # finish of processing


class WaveFormSource(Source):
    def __init__(self, nr_of_samples = -1):
        super(WaveFormSource, self).__init__()
        self.sample_rate   = DEFAULT_SAMPLE_RATE
        self.byte_rate     = DEFAULT_BYTE_RATE
        self.max_value     = 2 ** (self.byte_rate * 8 - 1) - 1
        self.nr_of_samples = nr_of_samples # < 0 for unlimited or until cut off by the implementing class


class SineWaveForm(WaveFormSource):
    def __init__(self, frequency = PITCH_STANDARD, nr_of_samples = None):
        super(SineWaveForm, self).__init__(nr_of_samples)
        self.frequency = frequency

    def read(self):
        cycles_per_period = 2 * math.pi * self.frequency / self.sample_rate
        t = 0
        while self.nr_of_samples < 0 or t < self.nr_of_samples:
            sine = math.sin( t * cycles_per_period) * self.max_value
            t += 1
            yield sine

    def __repr__(self):
        return "< sine wave %fHz >" % self.frequency


class Mixer(Source):
    def __init__(self):
        super(Mixer, self).__init__()
        self.sources = {}

    def add_source(self, source, token_id):
        self.sources[token_id] = source.read()

    def remove_source(self, source, token_id):
        if token_id not in self.sources:
            return 
        del(self.sources[token_id])

    def _read_from_generators(self):
        values = []
        empty_generators = []
        for (token_id, generator) in self.sources.iteritems():
            try:
                values.append(generator.next())
            except StopIteration:
                empty_generators.append(token_id)
        map(self.remove_source, empty_generators)
        return values

    def read(self):
        while True:
            values = self._read_from_generators()
            number_of_sources = len(values)
            if number_of_sources == 0:
                yield 0.0
            else:
                yield (sum(values) / number_of_sources)

class ScheduledSources(Source):
    def __init__(self):
        super(ScheduledSources, self).__init__()
        self.sample_rate = DEFAULT_SAMPLE_RATE
        self.events = {}
        self.mixer = Mixer()

    def add_event(self, time, event):
        events = self.events.get(time, [])
        events.append(event)
        self.events[time] = events

    def play_at(self, source, start_at_sample, stop_at_sample = None):
        token_id = uuid.uuid4()
        self.add_event(start_at_sample, ("START", source, token_id))
        if stop_at_sample is not None:
            self.add_event(stop_at_sample, ("STOP", source, token_id))

    def read(self):
        t = 0
        for p in self.mixer.read():
            if t in self.events:
                for typ, source, id_ in self.events[t]:
                    print typ, t, "-", id_, ":", source
                    if typ == "START":
                        self.mixer.add_source(source, id_)
                    elif typ == "STOP":
                        self.mixer.remove_source(source, id_)
            yield p
            t += 1

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
        print "Written", self.filename


if __name__ == '__main__':
    sine_wave_1 = SineWaveForm(frequency=440)
    sine_wave_2 = SineWaveForm(frequency=220)
    sine_wave_3 = SineWaveForm(frequency=261.63)
    sine_wave_4 = SineWaveForm(frequency=329.63)

    scheduler = ScheduledSources()
    scheduler.play_at(sine_wave_1, DEFAULT_SAMPLE_RATE * 4)
    scheduler.play_at(sine_wave_2, 0.0, DEFAULT_SAMPLE_RATE)
    scheduler.play_at(sine_wave_3, 0.0, DEFAULT_SAMPLE_RATE / 2)
    scheduler.play_at(sine_wave_4, 0.0, DEFAULT_SAMPLE_RATE / 2 * 3)

    wave_writer = WaveWriter("sample.wav")
    scheduler.connect_sink(wave_writer)
    scheduler.stream()
