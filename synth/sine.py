#!/usr/bin/env python
import pyaudio
import struct
import math
import time
from mingus.midi.sequencer import Sequencer
from mingus.midi import midi_file_in
import multiprocessing
import sys
import cProfile

STRUCT_PACK_FORMAT = {1: 'b', 2: 'h', 4: 'i', 8: 'q'} # key is byte rate

class Options(object):
    def __init__(self):
        self.sample_rate    = 44100
        self.pitch_standard = 440  # pitch of A4
        self.byte_rate      = 2    # gives 2 ^ (8 * DEFAULT_BYTE_RATE) levels
        self.max_value     = 2 ** (self.byte_rate * 8 - 1) - 1
        self.struct_pack_format = STRUCT_PACK_FORMAT[self.byte_rate]

class ConstantFrequencyEnvelope(object):
    def __init__(self, freq):
        self.freq = freq
    def get_frequency(self, t):
        return self.freq

class BendFrequencyEnveleope(object):
    def __init__(self, start_freq, end_freq, bend_time):
        self.start_freq = start_freq
        self.end_freq = end_freq
        self.bend_time = 44100
    def get_frequency(self, t):
        if t < self.bend_time + 1000:
            return self.start_freq + (self.end_freq - self.start_freq) * (float(t) / self.bend_time)
        return self.end_freq

class SineWave(object):
    def __init__(self, frequency_envelope):
        self.frequency_envelope = frequency_envelope
        self.sample_rate_adjustment = { 44100: 2.0 * math.pi / 44100.0 }
    def get_amplitude(self, output_options, t):
        freq = self.frequency_envelope.get_frequency(t)
        v = math.sin(self.sample_rate_adjustment[output_options.sample_rate] * freq * t)
        return v * output_options.max_value

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

class FrequencyTable(object):
    def __init__(self, options):
        self.midi_frequencies = {} # 69 corresponds with a4
        self.initialize_midi_frequencies(options.pitch_standard)
    def initialize_midi_frequencies(self, pitch_standard):
        for i in range(70):
            freq = pitch_standard * 2 ** -(i / 12.0)
            self.midi_frequencies[69 - i] = freq
        for i in range(70):
            freq = pitch_standard * 2 ** (i / 12.0)
            self.midi_frequencies[69 + i] = freq

class ConstantNoteEnvelope(object):
    def get_notes(self, options, t):
        return {69:t}

class ArpeggioNoteEnvelope(object):
    def __init__(self):
        self.pattern1 = {1: 69, 2: 72, 3: 76, 4: 81}
        self.pattern2 = {}
        for x in xrange(1, 13):
            self.pattern2[x] = 56 + x

    def get_notes(self, options, t):
        rate = options.sample_rate
        change_every = rate / 48
        if (t / options.sample_rate) % 2 == 0:
            notes = self.pattern1
        else:
            notes = self.pattern2
        phase = math.floor(t / change_every) % len(notes)
        return {notes[phase + 1]: t % change_every}

class RangeBucket(object):
    def __init__(self, start, stop, slots = 12):
        self.buckets = []
        for x in range(slots):
            self.buckets.append([])
        self.start = start
        self.stop = stop
        self.slots = slots
        self.slot_size = (stop - start) / self.slots
        print self.start, self.stop, self.slots, self.slot_size

    def add_item(self, start, stop, item):
        start_bucket = int(math.floor(start / self.slot_size))
        stop_bucket = int(math.ceil(stop / self.slot_size))
        for x in xrange(start_bucket, stop_bucket):
            self.buckets[x].append((start, stop, item))

    def get_notes_from_bucket(self, t):
        t = t % self.stop
        bucket = int(math.floor(t / self.slot_size))
        for (start, stop, items) in self.buckets[bucket]:
            if t < start or t > stop:
                continue
            for n in items:
                yield((n, t - start))

class TrackNoteEnvelope(object):

    def __init__(self, options, track):
        self.prepare_track(options, track)

    def prepare_track(self, options, track):
        self.mega_bar = []
        minimum = None
        maximum = None
        for i, bar in enumerate(track.bars):
            for b in bar.bar:
                start = (b[0] + i) * options.sample_rate
                stop = (1 / b[1]) * options.sample_rate + start

                if minimum is None or start < minimum:
                    minimum = start
                if maximum is None or stop > maximum:
                    maximum = stop

                notes = map(lambda n: int(n) + 24, b[2])
                self.mega_bar.append((start, stop, notes))
        self.bucket = RangeBucket(minimum, maximum)
        for b in self.mega_bar:
            self.bucket.add_item(*b)

    def get_notes(self, options, t):
        return self.bucket.get_notes_from_bucket(t)

class Instrument(object):
    def __init__(self, frequency_table, note_envelope):
        self.options = options
        self.frequency_table = frequency_table
        self.notes = {}
        self.note_envelope = note_envelope
        self.init()

    def init(self):
        for note, freq in self.frequency_table.midi_frequencies.iteritems():
            adder = Adder()
            adder.add_source(SineWave(ConstantFrequencyEnvelope(freq)))
            adder.add_source(SineWave(ConstantFrequencyEnvelope(freq)))
            adder.add_source(SineWave(ConstantFrequencyEnvelope(freq)))
            self.notes[note] = SineWave(ConstantFrequencyEnvelope(freq))

    def get_amplitude(self, options, t):
        value = 0
        playing = 0
        for note, relative_t in self.note_envelope.get_notes(options, t):
            v = self.notes[note].get_amplitude(options, relative_t)
            if v is not None:
                value += v
                playing += 1
        if playing == 0:
            return 0
        return value / playing

class Synth(object):
    def __init__(self):
        self.instruments = []

    def add_instrument(self, instrument):
        self.instruments.append(instrument)

    def get_amplitude(self, options, t):
        value = 0
        playing = 0
        for i in self.instruments:
            v = i.get_amplitude(options, t)
            if v != 0.0:
                value += v
                playing += 1
        if playing == 0:
            return 0
        return value / playing


options = Options()
(composition, bpm) = midi_file_in.MIDI_to_Composition(sys.argv[1])
tracks = filter(lambda t: len(t.bars) != 1, composition.tracks)

synth = Synth()
for t in tracks:
    instrument = Instrument(FrequencyTable(options), TrackNoteEnvelope(options, t))
    synth.add_instrument(instrument)

GLOBAL_TIME = 0
if len(sys.argv) > 2 and sys.argv[2] == "--profile":
    do_it=lambda: map(lambda i: synth.get_amplitude(options, i), xrange(44100))
    cProfile.run('do_it()')
    sys.exit(0)

def callback(in_data, frame_count, time_info, status):
    global GLOBAL_TIME, sine, options
    data = []
    for t_frame in xrange(frame_count):
        sample = struct.pack(options.struct_pack_format, int(synth.get_amplitude(options, int(GLOBAL_TIME + t_frame))))
        data.append(sample)
    GLOBAL_TIME += frame_count
    return ''.join(data), pyaudio.paContinue

output = pyaudio.PyAudio()
stream = output.open(format=pyaudio.paInt16, channels=1, rate= 44100, output=True, stream_callback=callback)
stream.start_stream()
while stream.is_active():
    time.sleep(0.1)
stream.stop_stream()
stream.close()
