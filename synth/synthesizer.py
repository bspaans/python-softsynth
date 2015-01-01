from synth.midi.MidiFileParser import MidiFileParser
from synth.instruments.OvertoneInstrument import OvertoneInstrument
from synth.instruments.PercussionInstrument import PercussionInstrument
from synth.instruments.SynthInstrument import SynthInstrument
from synth.interfaces import SampleGenerator
from synth.note_envelopes import MidiTrackNoteEnvelope
from synth.pcm import PCMWithFrequency
import numpy
import random

class Synthesizer(SampleGenerator):

    def __init__(self, options):
        super(Synthesizer, self).__init__(options)
        self.instruments = []

    def load_from_midi(self, file):
        (header, tracks) = MidiFileParser().parse_midi_file(file)
        tracks = filter(lambda t: len(filter(lambda x: x.event_type in [8,9], 
            t.events)) != 0, tracks)
        if self.options.output_midi_events:
            for t in tracks:
                print "NEW TRACK"
                for e in t.events:
                    print e
        ticks_per_beat = header["time_division"]['ticks_per_beat']
        song_length = 0
        for t in tracks:
            envelope = MidiTrackNoteEnvelope(self.options, t, ticks_per_beat)
            channels = t.get_channels()
            if 9 in channels:
                instrument = PercussionInstrument(self.options, envelope)
            else:
                att = 1000 # random.randrange(1000, 10000)
                dec = 2000 # random.randrange(1000, 10000)
                rel = 100 # random.randrange(1000, 10000)
                sus = 0.5 # random.random()
                instrument = OvertoneInstrument(self.options, envelope, overtones = 2, 
                        attack = att, decay = dec, release = rel, sustain = sus)
                #instrument = SynthInstrument(self.options, envelope)
            self.instruments.append(instrument)
            if envelope.track_length > song_length:
                song_length = envelope.track_length

        for i in self.instruments:
            i.note_envelope.track_length = song_length
	
        #self.instruments.append(PCMWithFrequency(self.options, "demo/rap_102_c1.wav", 440.0))
        return self

    def add_instrument(self, instrument):
        self.instruments.append(instrument)

    def get_samples(self, nr_of_samples, phase, release = None):
        result = None
        for i in self.instruments:
            samples = i.get_samples(nr_of_samples, phase, release)
            result = samples if result is None else numpy.add(result, samples)
        sources = len(self.instruments)
        return result if sources <= 1 else result / float(sources)

