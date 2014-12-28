from synth.midi.MidiFileParser import MidiFileParser
from synth.instruments import OvertoneInstrument, PercussionInstrument
from synth.interfaces import SampleGenerator
from synth.note_envelopes import MidiTrackNoteEnvelope
import numpy

class Synthesizer(SampleGenerator):

    def __init__(self, options):
        super(Synthesizer, self).__init__(options)
        self.instruments = []

    def load_from_midi(self, file):
        (header, tracks) = MidiFileParser().parse_midi_file(file)
        tracks = filter(lambda t: len(filter(lambda x: x.event_type in [8,9], 
            t.events)) != 0, tracks)
        ticks_per_beat = header["time_division"]['ticks_per_beat']
        for t in tracks:
            envelope = MidiTrackNoteEnvelope(self.options, t, ticks_per_beat)
            channels = t.get_channels()
            if 9 in channels:
                instrument = PercussionInstrument(self.options, envelope)
            else:
                instrument = OvertoneInstrument(self.options, envelope, overtones = 3)
            self.instruments.append(instrument)
        return self

    def add_instrument(self, instrument):
        self.instruments.append(instrument)

    def get_samples(self, nr_of_samples, phase, release = None):
        sources = 0
        result = None
        for i in self.instruments:
            samples = i.get_samples(nr_of_samples, phase, release)
            result = samples if result is None else numpy.add(result, samples)
            sources += 1
        return result if sources <= 1 else result / float(sources)

