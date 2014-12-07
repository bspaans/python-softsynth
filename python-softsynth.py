#!/usr/bin/env python

import uuid
import sys
import multiprocessing
from synth.source import Source, SineWaveForm
from synth.sink import PyAudioWriter
from synth.mixer import Mixer
from synth.server import SynthTCPServer

STRUCT_PACK_FORMAT = { 1: 'b', 2: 'h', 4: 'i', 8: 'q' } # key is byte rate

class Options:
    def __init__(self):
        self.sample_rate    = 44100
        self.pitch_standard = 440  # pitch of A4
        self.byte_rate      = 2    # gives 2 ^ (8 * DEFAULT_BYTE_RATE) levels
	self.struct_pack_format = STRUCT_PACK_FORMAT[self.byte_rate]

	
class ScheduledSources(Source):
    def __init__(self, options):
        super(ScheduledSources, self).__init__(options)
        self.sample_rate = options.sample_rate
        self.events = {}
        self.mixer = Mixer(options)

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

class FrequencyTable:

    def __init__(self, options):
        self.note_frequencies = {}
        self.midi_frequencies = {} # 69 corresponds with a4
        self.initialize_midi_frequencies(options.pitch_standard)
        self.initialize_note_frequencies()

    def initialize_midi_frequencies(self, pitch_standard):
        for i in range(70):
            freq = pitch_standard * 2 ** -(i / 12.0)
            self.midi_frequencies[69 - i] = freq
        for i in range(70):
            freq = pitch_standard * 2 ** (i / 12.0)
            self.midi_frequencies[69 + i] = freq

    def midi_to_note(self, midi_nr):
        notes = ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b']
        octave = midi_nr / 12 - 1
        note = notes[midi_nr % 12]
        notation = "%s%d" % (note, octave)
        return notation


    def initialize_note_frequencies(self):
        for i in range(128):
            notation = self.midi_to_note(i)
            self.note_frequencies[notation] = self.midi_frequencies[i]
            print notation, self.midi_frequencies[i]

class InstrumentBank:
    def __init__(self, options, frequency_table):
        self.bank = {}
        for n, freq in frequency_table.note_frequencies.iteritems():
            base_freq = SineWaveForm(options, frequency=freq)
            first_overtone = SineWaveForm(options, frequency=freq * 2)
            first_overtone.max_amplitude = 0.75
            second_overtone = SineWaveForm(options, frequency=freq * 3)
            second_overtone.max_amplitude = 0.5
            mixer = Mixer(options)
            mixer.add_source(base_freq, str(base_freq))
            mixer.add_source(first_overtone, str(first_overtone))
            mixer.add_source(second_overtone, str(second_overtone))
            self.bank[n] = mixer

class Synth:
    def __init__(self, options):
        self.options = options
        self.mixer = Mixer(options)

        self.freq_table = FrequencyTable(options)
        self.bank = InstrumentBank(options, self.freq_table)

        self.playing = {}

    def noteon(self, note):
        token_id = uuid.uuid4()
        self.playing[note] = token_id
        self.mixer.add_source(self.bank.bank[self.freq_table.midi_to_note(note)], token_id)
        print "Note on"

    def noteoff(self, note):
        token_id = self.playing[note]
        self.mixer.remove_source(self.bank.bank[self.freq_table.midi_to_note(note)], token_id)
        print "Note off"

    def process_command(self, command, arg):
        if command == 'noteon':
            self.noteon(arg)
        if command == 'noteoff':
            self.noteon(arg)
    
    def stream(self, queue):
        print "Started streaming"
        self.sink = PyAudioWriter(self.options)
        self.mixer.connect_sink(self.sink)
        self.sink.open()
        try:
            for e in self.mixer.read():
                self.sink.write(e)
                while not queue.empty():
                    command, arg = queue.get()
                    self.process_command(command, arg)

        except KeyboardInterrupt:
            print "Stopped streaming."
        finally:
            self.sink.close()
        

def main():
    options = Options()
    q = multiprocessing.Queue()
    synth = Synth(options)
    synth_proc = multiprocessing.Process(target=synth.stream, args=(q,))
    server = SynthTCPServer('localhost', int(sys.argv[1]), q) 
    synth_proc.start()
    server.serve_forever()

    scheduler = ScheduledSources(options)
    scheduler.play_at(bank.bank['a3'], 0.0, options.sample_rate * 40)
    scheduler.play_at(bank.bank['a4'], 0.0, options.sample_rate * 40)
    scheduler.play_at(bank.bank['e4'], options.sample_rate, options.sample_rate * 40)
    scheduler.play_at(bank.bank['c4'], options.sample_rate * 2, options.sample_rate * 40)

    #wave_writer = WaveWriter("sample.wav")
    #scheduler.connect_sink(wave_writer)
    pyaudio_writer = PyAudioWriter(options)
    scheduler.connect_sink(pyaudio_writer)
    scheduler.stream()

if __name__ == '__main__':
    main()

