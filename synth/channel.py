from synth.interfaces import SampleGenerator
from synth.note_envelopes import MidiTrackNoteEnvelope
import numpy

class Channel(SampleGenerator):

    def __init__(self, options, channel_nr, synth):
        super(Channel, self).__init__(options)
        self.channel_nr = channel_nr
        self.instrument_bank = synth.instrument_bank
        self.percussion = None
        self.current_instrument = None
        self.note_envelope = None

    def set_timing_units(self, ticks_per_beat):
        self.bpm = self.options.bpm
        self.seconds_per_beat = 60.0 / self.bpm
        self.samples_per_beat = self.options.sample_rate * self.seconds_per_beat
        self.samples_per_tick = self.samples_per_beat / ticks_per_beat

    def set_events(self, events, ticks_per_beat):
        self.events = events
        self.pitch_bend_events = [ e for e in events if e.event_type == 14 ]
        if self.options.output_midi_events:
            print "Channel", self.channel_nr
            for e in events:
                print e
        self.set_timing_units(ticks_per_beat)
        for event in self.events:
            event.start_time = int(event.start_time * self.samples_per_tick)
            if event.stop_time is not None:
                event.stop_time = int(event.stop_time * self.samples_per_tick)
        self.event_pointer = 0
        self.note_envelope = MidiTrackNoteEnvelope(self.options, events, ticks_per_beat)

    def get_instruments(self, nr_of_samples, phase):
        if self.channel_nr == 9:
            if self.percussion is None:
                self.percussion = self.instrument_bank.get_percussion(self.note_envelope)
            return [(0, nr_of_samples, self.percussion)]
        if self.current_instrument is None:
            self.current_instrument = self.instrument_bank.get_instrument(4, self.note_envelope)
        return [(0, nr_of_samples, self.current_instrument)]
            

    def get_pitch_bend(self, nr_of_samples, phase):
        result = numpy.zeros(nr_of_samples)
        while self.event_pointer < len(self.pitch_bend_events):
            e = self.pitch_bend_events[self.event_pointer]
            if e.event_type == 14:
                start_index = max(0, e.start_time - phase)
                stop_index = min(e.stop_time - phase, nr_of_samples)
                result[start_index:stop_index] = e.param2 - 64
            if e.stop_time > phase + nr_of_samples:
                break
            self.event_pointer += 1
        return result

    def get_samples(self, nr_of_samples, phase, release = None, pitch_bend = None):
        if self.note_envelope is None:
            return None
        result = numpy.zeros(nr_of_samples)
        sources = numpy.zeros(nr_of_samples)
        pitch_bend = self.get_pitch_bend(nr_of_samples, phase)
        for start, stop, instrument in self.get_instruments(nr_of_samples, phase):
            result[start:stop] += instrument.get_samples(stop - start, phase + start, release, pitch_bend[start:stop])
            sources[start:stop] += 1
        return result, sources

    def set_song_length(self, song_length):
        if self.note_envelope is not None:
            self.note_envelope.track_length = song_length


