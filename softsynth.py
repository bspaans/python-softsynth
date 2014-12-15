#!/usr/bin/env python

import uuid
import sys
import multiprocessing
from synth.source import SineWaveForm
from synth.sink import PyAudioWriter
from synth.mixer import Mixer
from synth.server import SynthTCPServer

STRUCT_PACK_FORMAT = {1: 'b', 2: 'h', 4: 'i', 8: 'q'} # key is byte rate

class Options(object):
    def __init__(self):
        self.sample_rate    = 44100
        self.pitch_standard = 440  # pitch of A4
        self.byte_rate      = 2    # gives 2 ^ (8 * DEFAULT_BYTE_RATE) levels
        self.struct_pack_format = STRUCT_PACK_FORMAT[self.byte_rate]

class FrequencyTable(object):

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

class Instrument(object):
    def __init__(self, options, frequency_table):
        self.options = options
        self.frequency_table = frequency_table

    def get_note(self, note):
        options = self.options
        freq = self.frequency_table.midi_frequencies[note]
        base_freq = SineWaveForm(options, frequency=freq)
        first_overtone = SineWaveForm(options, frequency=freq * 2)
        first_overtone.max_amplitude = 0.75
        second_overtone = SineWaveForm(options, frequency=freq * 3)
        second_overtone.max_amplitude = 0.5
        mixer = Mixer(options)
        mixer.add_source(base_freq, str(base_freq))
        mixer.add_source(first_overtone, str(first_overtone))
        mixer.add_source(second_overtone, str(second_overtone))
        return mixer

class Synth(object):
    def __init__(self, options):
        self.options = options
        self.mixer = Mixer(options)
        self.sink = None

        self.freq_table = FrequencyTable(options)
        self.instrument = Instrument(options, self.freq_table)

        self.playing = {}

    def noteon(self, note):
        token_id = uuid.uuid4()
        instrument_note = self.instrument.get_note(note)
        instrument_note.id = token_id
        self.playing[note] = instrument_note
        self.mixer.add_source(instrument_note, token_id)
        print "Note on"

    def noteoff(self, note):
        instrument_note = self.playing[note]
        self.mixer.remove_source(instrument_note, instrument_note.id)
        print "Note off"

    def process_command(self, command, arg):
        if command == 'noteon':
            self.noteon(arg)
        if command == 'noteoff':
            self.noteoff(arg)
    
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
        

def start_softsynth(options = None):
    if options is None:
        options = Options()
    queue = multiprocessing.Queue()
    synth = Synth(options)
    synth_proc = multiprocessing.Process(target=synth.stream, args=(queue,))
    return (queue, synth_proc)

def main():
    (queue, synth_proc) = start_softsynth()
    port = int(sys.argv[1]) if len(sys.argv) == 2 else 5001
    server = SynthTCPServer('localhost', port, queue) 
    synth_proc.start()
    server.serve_forever()

if __name__ == '__main__':
    main()

