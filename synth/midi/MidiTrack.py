from MidiEvent import MidiEvent
import utils

class MidiTrack(object):

    def reset(self):
        self.events = []

    def parse_track(self, fp):
        """Parse a MIDI track from its header to its events.

        Return a list of events and the number of bytes that were read.
        """
        self.reset()
        chunk_size = self.parse_track_header(fp)
        cum_time = 0
        while chunk_size > 0:
            (delta_time, chunk_delta) = utils.parse_varbyte_as_int(fp)
            chunk_size -= chunk_delta
            midi_event = MidiEvent()
            chunk_delta = midi_event.parse_midi_event(fp)
            chunk_size -= chunk_delta
            cum_time += delta_time
            midi_event.delta_time = delta_time
            midi_event.start_time = cum_time
            self.events.append(midi_event)
        if chunk_size < 0:
            print 'yikes.', chunk_size
        self.set_stop_times()
        return self

    def parse_track_header(self, fp):
        """Return the size of the track chunk."""
        # Check the header
        h = fp.read(8)
        if h[0:4] != 'MTrk':
            raise HeaderError('Not a valid Track header.')
        chunk_size = utils.bytes_to_int(h[4:8])
        return chunk_size

    def __repr__(self):
        result = "[\n "
        result += ",\n ".join(map(str, self.events))
        return result + "]"

    def set_stop_times(self):
        for e in self.events:
            if e.event_type not in [8, 9]:
                e.stop_time = e.start_time
        self.replace_note_off_with_stop_time_on_note_on()
        self.set_pitch_bend_stop_time_to_next_pitch_bend_start_time()

    def replace_note_off_with_stop_time_on_note_on(self):
        result = []
        playing = {}
        last_time = 0
        for e in self.events:
            if e.start_time > last_time:
                last_time = e.start_time
            if e.event_type not in [8, 9]:
                result.append(e)
                continue
            if e.event_type == 8: # note off
                if e.param1 not in playing:
                    continue
                event = playing[e.param1]
                event.stop_time = e.start_time
                del(playing[e.param1])
            else: # note on
                playing[e.param1] = e
                e.param1 = int(e.param1)
                result.append(e)
        for e in playing.itervalues(): 
            e.stop_time = last_time
        self.events = result

    def set_pitch_bend_stop_time_to_next_pitch_bend_start_time(self):
        pitch_bend = None
        for e in self.events:
            if e.event_type == 14:
                if pitch_bend is not None:
                    pitch_bend.stop_time = e.start_time
                pitch_bend = e
