#!/usr/bin/env python
import pyaudio
import struct
import math
import time
from mingus.midi.sequencer import Sequencer
from mingus.midi import midi_file_in
import multiprocessing
import sys
import random
import cProfile
import wave

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
    def get_frequency(self, options, t):
        return self.freq

class BendFrequencyEnvelope(object):
    def __init__(self, start_freq, end_freq, bend_time = 44100):
        self.start_freq = start_freq
        self.end_freq = end_freq
        self.bend_time = bend_time

    def get_frequency(self, options, t):
        if t < self.bend_time:
            return self.start_freq + (self.end_freq - self.start_freq) * (float(t) / self.bend_time)
        return self.end_freq

class ConstantAmplitudeEnvelope(object):
    def __init__(self, max_amplitude):
        self.max_amplitude = max_amplitude
    def get_amplitude(self, options, t):
        return self.max_amplitude

class ADSRAmplitudeEnvelope(object):
    def __init__(self, max_amplitude = 1.0):
        self.max_amplitude = max_amplitude
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
    def get_amplitude(self, options, t, stopped_since = None):
        attack_time = options.sample_rate * float(self.attack)
        if t < attack_time:
            return (t / attack_time) * self.max_amplitude
        decay_time = options.sample_rate * float(self.decay)
        if t < attack_time + decay_time:
            return self.max_amplitude - ((t - attack_time) / decay_time) * (self.max_amplitude - self.sustain_level)
        if stopped_since is None:
            return self.sustain_level
        release_time = options.sample_rate * float(self.release)
        return self.sustain_level - ((t - stopped_since) / release_time) * self.sustain_level


class SineWave(object):
    def __init__(self, frequency_envelope, amplitude_envelope):
        self.frequency_envelope = frequency_envelope
        self.sample_rate_adjustment = { 44100: 2.0 * math.pi / 44100.0 }
        self.amplitude_envelope = amplitude_envelope

    def get_amplitude(self, output_options, t):
        freq = self.frequency_envelope.get_frequency(options, t)
        amp  = self.amplitude_envelope.get_amplitude(options, t)
        v = math.sin(self.sample_rate_adjustment[output_options.sample_rate] * freq * t)
        return amp * v * output_options.max_value

class SquareWave(object):
    def __init__(self, frequency_envelope, amplitude_envelope):
        self.frequency_envelope = frequency_envelope
        self.sample_rate_adjustment = { 44100: 2.0 * math.pi / 44100.0 }
        self.amplitude_envelope = amplitude_envelope

    def get_amplitude(self, output_options, t):
        freq = self.frequency_envelope.get_frequency(options, t)
        amp  = self.amplitude_envelope.get_amplitude(options, t)
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
        amp  = self.amplitude_envelope.get_amplitude(options, t)
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
        return [(69, t)]

class ArpeggioNoteEnvelope(object):
    def __init__(self):
        self.pattern1 = {1: 69, 2: 72, 3: 76, 4: 81}
        self.pattern2 = {}
        for x in xrange(1, 13):
            self.pattern2[x] = 56 + x
        self.pattern3 = {1: 64, 2: 69, 3: 72, 4: 57}

    def get_notes(self, options, t):
        rate = options.sample_rate
        change_every = rate / 2
        if (t / options.sample_rate) % 2 == 0:
            notes = self.pattern1
        else:
            notes = self.pattern3
        phase = math.floor(t / change_every) % len(notes)
        return [(notes[phase + 1], t % change_every)]

class RangeBucket(object):
    def __init__(self, start, stop, slots = 12):
        self.buckets = []
        for x in range(slots):
            self.buckets.append([])
        self.start = start
        self.stop = stop
        self.slots = slots
        self.slot_size = (stop - start) / self.slots

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
        print track.bars
        for i, bar in enumerate(track.bars):
            for b in bar.bar:
                if b[2] == []:
                    continue
                start = (b[0] + i) * options.sample_rate
                stop = (1.0 / b[1]) * options.sample_rate + start

                if minimum is None or start < minimum:
                    minimum = start
                if maximum is None or stop > maximum:
                    maximum = stop

                notes = map(lambda n: int(n) + 24, b[2])
                self.mega_bar.append((start, stop, notes))
        self.bucket = RangeBucket(minimum, maximum)
        print self.mega_bar
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
        pass

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

class OvertoneInstrument(Instrument):
    def __init__(self, frequency_table, note_envelope):
        super(OvertoneInstrument, self).__init__(frequency_table, note_envelope)

    def init(self):
        for note, freq in self.frequency_table.midi_frequencies.iteritems():
            amp_env = ADSRAmplitudeEnvelope(1.0)
            amp_env.set_attack(0.01)
            amp_env.set_decay(0.1)
            amp_env.set_sustain(0.0)
            freq_env = ConstantFrequencyEnvelope(freq)
            adder = Adder()
            adder.add_source(SineWave(ConstantFrequencyEnvelope(freq), amp_env))
            adder.add_source(SineWave(ConstantFrequencyEnvelope(freq * 2), amp_env))
            adder.add_source(SineWave(ConstantFrequencyEnvelope(freq * 3), amp_env))
            self.notes[note] = SineWave(ConstantFrequencyEnvelope(freq), amp_env)

class PercussionInstrument(Instrument):
    def __init__(self, frequency_table, note_envelope):
        super(PercussionInstrument, self).__init__(frequency_table, note_envelope)

    def init(self):
        amp_env = ADSRAmplitudeEnvelope(1.0)
        amp_env.set_attack(0.0000001)
        amp_env.set_decay(0.15)
        amp_env.set_sustain(0.0)
        freq_env1 = BendFrequencyEnvelope(60, 50, 10000)
        adder = Adder()
        adder.add_source(SquareWave(freq_env1, amp_env))
        self.notes[47] = adder # kick1
        self.notes[48] = adder # kick2
        amp_env = ADSRAmplitudeEnvelope(1.0)
        self.notes[52] = RandomWave(amp_env) # snare
        amp_env = ADSRAmplitudeEnvelope(0.1)
        amp_env.set_attack(0.00001)
        amp_env.set_decay(0.05)
        amp_env.set_sustain(0.0)
        self.notes[54] = RandomWave(amp_env) # closed hihat
        amp_env = ADSRAmplitudeEnvelope(0.3)
        amp_env.set_attack(0.0)
        amp_env.set_decay(2.0)
        amp_env.set_sustain(1.0)
        self.notes[61] = RandomWave(amp_env) # crash
        self.notes[69] = RandomWave(amp_env) # crash

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

class WaveWriter(object):

    def __init__(self, options, filename):
        super(WaveWriter, self).__init__(options)
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

options = Options()
(composition, bpm) = midi_file_in.MIDI_to_Composition(sys.argv[1])
tracks = filter(lambda t: len(t.bars) != 1, composition.tracks)

print tracks
amplitude_generator = None
if "midi" in sys.argv:
    synth = Synth()
    for t in tracks:
        instr = OvertoneInstrument
        for b in t.bars:
            for nc in b.bar:
                for n in nc[2]:
                    if hasattr(n, "channel"):
                        if n.channel == 9:
                            instr = PercussionInstrument
                        break
        instrument = instr(FrequencyTable(options), TrackNoteEnvelope(options, t))
        synth.add_instrument(instrument)
    amplitude_generator = synth
else:
    instrument = OvertoneInstrument(FrequencyTable(options), ArpeggioNoteEnvelope())
    amplitude_generator = instrument

GLOBAL_TIME = 0
if "--profile" in sys.argv:
    do_it=lambda: map(lambda i: amplitude_generator.get_amplitude(options, i), xrange(44100))
    cProfile.run('do_it()')
    sys.exit(0)

def callback(in_data, frame_count, time_info, status):
    global GLOBAL_TIME, sine, options
    data = []
    for t_frame in xrange(frame_count):
        sample = struct.pack(options.struct_pack_format, int(amplitude_generator.get_amplitude(options, int(GLOBAL_TIME + t_frame))))
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
