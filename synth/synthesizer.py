from synth.midi.MidiFileParser import MidiFileParser
from synth.instruments.OvertoneInstrument import OvertoneInstrument
from synth.instruments.PercussionInstrument import PercussionInstrument
from synth.instruments.SynthInstrument import SynthInstrument
from synth.interfaces import SampleGenerator
from synth.pcm import PCMWithFrequency
from synth.channel import Channel
import numpy
import random

class InstrumentBank(object):

    def __init__(self, options):
        self.options = options

    def get_instrument(self, midi_nr, envelope):
        att = 1000 # random.randrange(1000, 10000)
        dec = 2000 # random.randrange(1000, 10000)
        rel = 100 # random.randrange(1000, 10000)
        sus = 0.5 # random.random()
        instrument = OvertoneInstrument(self.options, envelope, overtones = 1, 
                attack = att, decay = dec, release = rel, sustain = sus)
        return instrument

    def get_percussion(self, envelope):
        return PercussionInstrument(self.options, envelope)

class Synthesizer(SampleGenerator):

    def __init__(self, options):
        super(Synthesizer, self).__init__(options)
        self.instruments = []
        self.instrument_bank = InstrumentBank(options)
        self.channels = {}
        for c in xrange(16):
            self.channels[c] = Channel(options, c, self)


    def load_from_midi(self, file):
        (header, channels) = MidiFileParser().parse_midi_file(file)
        ticks_per_beat = header["time_division"]['ticks_per_beat']

        song_length = 0
        for channel, events in channels.iteritems():
            if channel is None:
                continue
            c = self.channels[channel]
            c.set_events(events, ticks_per_beat)
            if c.note_envelope.track_length > song_length:
                song_length = c.note_envelope.track_length

        for channel, c in self.channels.iteritems():
            c.set_song_length(song_length)

        self.song_length = song_length
        return self

    def add_instrument(self, instrument):
        self.instruments.append(instrument)

    def get_samples(self, nr_of_samples, phase, release = None, pitch_bend = None):
        if not self.options.loop and phase > self.song_length:
            return None
        result = numpy.zeros(nr_of_samples)
        sources = numpy.zeros(nr_of_samples)
        for nr, channel in self.channels.iteritems():
            channel_result = channel.get_samples(nr_of_samples, phase, release)
            if channel_result is None:
                continue
            samples, instruments = channel_result
            sources += instruments
            result  += samples
        return result / sources

