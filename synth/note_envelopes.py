import math
import numpy
import sys

class NoteEvent(object):
    def __init__(self, start_time, stop_time, note, velocity = 127.0):
        self.start_time = start_time 
        self.stop_time = stop_time 
        self.note = int(note)
        self.velocity = velocity / 127.0

    def get_start_index_for_phase(self, time, phase):
        s = time - phase
        return 0 if s <= 0 else s

    def get_stop_index_for_phase(self, time, phase, nr_of_samples):
        s = nr_of_samples if time is None else time - phase
        return min(s, nr_of_samples)

    def get_note_phase_for_phase(self, phase):
        s = self.start_time - phase
        return -s if s <= 0 else 0

    def does_this_note_play(self, phase, nr_of_samples):
        if self.stop_time is not None and phase >= self.stop_time:
            return False
        return phase + nr_of_samples > self.start_time

class MidiTrackNoteEnvelope(object):
    def __init__(self, options, track, ticks_per_beat):
        self.options = options
        self.ticks_per_beat = float(ticks_per_beat)
        self.loop = options.loop
        self.prepare_track(track)

    def prepare_track(self, track):
        result = [ e for e in track if e.event_type == 9 ]
        self.events = result
        self.event_pointer = 0
        self.nr_of_events = len(self.events)
        if self.nr_of_events == 0:
            self.track_length = 0
        else:
            self.track_length = max(map(lambda s: 0.0 if s.stop_time is None else s.stop_time, self.events))
        self.nr_of_loops = 0

    def get_notes_for_range(self, options, phase, nr_of_samples):
        result = []
        while self.event_pointer < self.nr_of_events and \
                self.events[self.event_pointer].start_time + self.nr_of_loops * self.track_length <= phase + nr_of_samples:

            event = self.events[self.event_pointer]
            offset = self.nr_of_loops * self.track_length
            if event.start_time + offset >= phase:
                if event.stop_time is None:
                    event.stop_time = nr_of_samples
                result.append(NoteEvent(event.start_time + offset, event.stop_time + offset, \
                        event.param1, event.param2))
            self.event_pointer += 1
            if self.loop and self.event_pointer >= self.nr_of_events:
                self.event_pointer = self.event_pointer % self.nr_of_events
                self.nr_of_loops += 1
                sys.stderr.write("Looping round, right round.\n")
        return result
