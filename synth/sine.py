#!/usr/bin/env python
import pyaudio
import struct
import math
import time
from mingus.midi.sequencer import Sequencer
from mingus.midi import midi_file_in
import multiprocessing
import sys

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
    def get_amplitude(self, output_options, t):
        freq = self.frequency_envelope.get_frequency(t)
        cycles_per_period = 2 * math.pi * (float(freq) / output_options.sample_rate)
        return math.sin(t * cycles_per_period) * output_options.max_value

class Adder(object):
    def __init__(self):
        self.sources = []
        self.stopped = {}
    def add_source(self, source):
        self.sources.append(source)
    def stop_source(self, source):
        self.stopped[source] = True
    def get_amplitude(self, output_options, t):
        values = []
        for s in self.sources:
            v = s.get_amplitude(output_options, t)
            if v is not None:
                values.append(v)
        return sum(values) / len(values)

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
    def get_note(self, options, t):
        return [(69, t)]

class ArpeggioNoteEnvelope(object):
    def __init__(self):
        self.pattern1 = {1: 69, 2: 72, 3: 76, 4: 81}
        self.pattern2 = {}
        for x in xrange(1, 13):
            self.pattern2[x] = 56 + x

    def get_note(self, options, t):
        rate = options.sample_rate
        change_every = rate / 12
        if (t / options.sample_rate) % 2 == 0:
            notes = self.pattern1
        else:
            notes = self.pattern2
        phase = math.floor(t / change_every) % len(notes)
        return [(notes[phase + 1], t % change_every)]

class TrackNoteEnvelope(object):
    def __init__(self, track):
        self.prepare_track(track):

    def prepare_track(self, track):
        pass

    def get_note(self, options, t):
        pass

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
            adder.add_source(SineWave(BendFrequencyEnveleope(0, freq, 500)))
            adder.add_source(SineWave(BendFrequencyEnveleope(freq * 2, freq * 2, 500)))
            adder.add_source(SineWave(BendFrequencyEnveleope(freq * 4, freq * 3, 500)))
            self.notes[note] = adder

    def get_amplitude(self, options, t):
        notes = self.note_envelope.get_note(options, t)
        values = []
        for (note, relative_t) in notes:
            v = self.notes[note].get_amplitude(options, relative_t)
            if v is not None:
                values.append(v)
        return sum(values) / len(values)


t = 0
options = Options()
(composition, bpm) = midi_file_in.MIDI_to_Composition(sys.argv[1])
track = filter(lambda t: len(t.bars) != 1, composition.tracks)[0]

track_envelope = TrackNoteEnvelope(track)
instrument = Instrument(FrequencyTable(options), ArpeggioNoteEnvelope())

def callback(in_data, frame_count, time_info, status):
    global t, sine, options
    data = []
    for t_frame in xrange(frame_count):
        sample = struct.pack(options.struct_pack_format, int(instrument.get_amplitude(options, t + t_frame)))
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
