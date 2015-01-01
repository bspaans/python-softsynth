from synth.midi.MidiFileParser import MidiFileParser
from synth.instruments.OvertoneInstrument import OvertoneInstrument
from synth.instruments.PercussionInstrument import PercussionInstrument
from synth.instruments.SynthInstrument import SynthInstrument
from synth.interfaces import SampleGenerator
from synth.note_envelopes import MidiTrackNoteEnvelope
from synth.pcm import PCMWithFrequency
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
        instrument = OvertoneInstrument(self.options, envelope, overtones = 2, 
                attack = att, decay = dec, release = rel, sustain = sus)
        return instrument

    def get_percussion(self, envelope):
        return PercussionInstrument(self.options, envelope)

class Channel(SampleGenerator):

    def __init__(self, options, channel_nr, synth):
        super(Channel, self).__init__(options)
        self.channel_nr = channel_nr
        self.instrument_bank = synth.instrument_bank
        self.percussion = None
        self.instrument_cache = None

    def set_events(self, events, ticks_per_beat):
        self.events = events
        if self.options.output_midi_events:
            print "Channel", self.channel_nr
            for e in events:
                print e
        self.note_envelope = MidiTrackNoteEnvelope(self.options, events, ticks_per_beat)

    def get_instruments(self, nr_of_samples, phase):
        if self.channel_nr == 9:
            if self.percussion is None:
                self.percussion = self.instrument_bank.get_percussion(self.note_envelope)
            return [(0, nr_of_samples, self.percussion)]
        if self.instrument_cache is None:
            self.instrument_cache = self.instrument_bank.get_instrument(4, self.note_envelope)
        return [(0, nr_of_samples, self.instrument_cache)]
            

    def get_pitch_bend_envelope(self, nr_of_samples, phase):
        pass

    def get_samples(self, nr_of_samples, phase, release = None):
        result = numpy.zeros(nr_of_samples)
        sources = numpy.zeros(nr_of_samples)
        for start, stop, instrument in self.get_instruments(nr_of_samples, phase):
            result[start:stop] += instrument.get_samples(stop - start, phase + start, release)
            sources[start:stop] += 1
        return result, sources


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
        for channel, events in channels.iteritems():
            self.channels[channel].set_events(events, ticks_per_beat)
        song_length = 0
        for channel, c in self.channels.iteritems():
            if c.note_envelope.track_length > song_length:
                song_length = c.note_envelope.track_length

        for channel, c in self.channels.iteritems():
            c.note_envelope.track_length = song_length
	
        return self

    def add_instrument(self, instrument):
        self.instruments.append(instrument)

    def old_get_samples(self, nr_of_samples, phase, release = None):
        result = None
        for i in self.instruments:
            samples = i.get_samples(nr_of_samples, phase, release)
            result = samples if result is None else numpy.add(result, samples)
        sources = len(self.instruments)
        return result if sources <= 1 else result / float(sources)

    def get_samples(self, nr_of_samples, phase, release = None):
        result = numpy.zeros(nr_of_samples)
        sources = numpy.zeros(nr_of_samples)
        for nr, channel in self.channels.iteritems():
            samples, instruments = channel.get_samples(nr_of_samples, phase, release)
            sources += instruments
            result  += samples
        return result / sources

