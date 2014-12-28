import math
import numpy

class NoteEvent(object):
    def __init__(self, start_time, stop_time, note):
        self.start_time = start_time 
        self.stop_time = stop_time 
        self.note = int(note)

    def get_start_index_for_phase(self, phase):
        s = self.start_time - phase
        return 0 if s <= 0 else s

    def get_note_phase_for_phase(self, phase):
        s = self.start_time - phase
        return -s if s <= 0 else 0

    def get_stop_index_for_phase(self, phase, nr_of_samples):
        s = nr_of_samples if self.stop_time is None else self.stop_time - phase
        return min(s, nr_of_samples)

    def does_this_note_play(self, phase, nr_of_samples):
        if self.stop_time is not None and phase >= self.stop_time:
            return False
        return phase + nr_of_samples > self.start_time

class ConstantNoteEnvelope(object):
    def __init__(self, options, note):
        self.options = options
        self.note = note

    def get_notes(self, options, t):
        return [(self.note, t)]

    def get_notes_for_range(self, options, phase, nr_of_samples):
        return [NoteEvent(0, None, self.note)]

class ArpeggioNoteEnvelope(object):
    def __init__(self):
        self.pattern1 = {1: 69, 2: 72, 3: 76, 4: 81}
        self.pattern2 = {}
        for x in xrange(1, 13):
            self.pattern2[x] = 56 + x
        self.pattern3 = {1: 64, 2: 69, 3: 72, 4: 57}

    def get_notes_for_range(self, options, phase, nr_of_samples):
        result = []
        change_every = options.sample_rate / 12
        for t in xrange(phase, phase + nr_of_samples + change_every - 1, change_every):
            if (t / options.sample_rate) % 2 == 0:
                pattern = self.pattern1
            else:
                pattern = self.pattern3
            notes_played = int(math.floor( t / change_every))
            note_phase = notes_played % len(pattern)
            current_note_started_at = notes_played * change_every
            current_note_stops_at = current_note_started_at + change_every
            result.append(NoteEvent(current_note_started_at, 
                current_note_stops_at, parrent[note_phase + 1]))
        return result

class MidiTrackNoteEnvelope(object):
    def __init__(self, options, track, ticks_per_beat, bpm = 120.0):
        self.options = options
        self.ticks_per_beat = float(ticks_per_beat)
        self.bpm = bpm
        self.seconds_per_beat = 60.0 / self.bpm
        self.samples_per_beat = self.options.sample_rate * self.seconds_per_beat
        self.samples_per_tick = self.samples_per_beat / self.ticks_per_beat
        self.prepare_track(track)

    def prepare_track(self, track):
        result = []
        track.replace_note_off_with_stop_time_on_note_on()
        for event in track.events:
            if event.event_type in [8, 9]:
                event.start_time = int(event.start_time * self.samples_per_tick)
                if event.stop_time is not None:
                    event.stop_time = int(event.stop_time * self.samples_per_tick)
                result.append(event)
        self.events = result
        self.event_pointer = 0

    def get_notes_for_range(self, options, phase, nr_of_samples):
        result = []
        while self.event_pointer < len(self.events) and \
                self.events[self.event_pointer].start_time <= phase + nr_of_samples:
            event  = self.events[self.event_pointer]
            if event.start_time >= phase:
                result.append(NoteEvent(event.start_time, event.stop_time, \
                        event.param1))
            self.event_pointer += 1
        return result
