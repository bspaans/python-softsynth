import binascii
from header import MidiHeader


class MidiFileParser:

    def __init__(self):
        pass

    def parse_midi_file(self, file):
        """Parse a MIDI file.

        Return the header -as a tuple containing respectively the MIDI
        format, the number of tracks and the time division-, the parsed
        track data and the number of bytes read.
        """
        f = open(file, 'r')
        self.bytes_read = 0
        header = MidiHeader().parse_header_from_file(f)
        result = []
        for t in range(header['number_of_tracks']):
            events = self.parse_track(f)
            result.append(events)
        f.close()
        return (header, result)

    def bytes_to_int(self, bytes):
        return int(binascii.b2a_hex(bytes), 16)

    def parse_track(self, fp):
        """Parse a MIDI track from its header to its events.

        Return a list of events and the number of bytes that were read.
        """
        events = []
        chunk_size = self.parse_track_header(fp)
        while chunk_size > 0:
            (delta_time, chunk_delta) = self.parse_varbyte_as_int(fp)
            chunk_size -= chunk_delta
            (event, chunk_delta) = self.parse_midi_event(fp)
            chunk_size -= chunk_delta
            events.append((delta_time, event))
        if chunk_size < 0:
            print 'yikes.', self.bytes_read, chunk_size
        return events

    def parse_midi_event(self, fp):
        """Parse a MIDI event.

        Return a dictionary and the number of bytes read.
        """
        chunk_size = 0
        try:
            ec = self.bytes_to_int(fp.read(1))
            chunk_size += 1
        except:
            raise IOError("Couldn't read event type "
                    "and channel data from file.")

        # Get the nibbles
        event_type = (ec & 0xf0) >> 4
        channel = ec & 0x0f

        # I don't know what these events are supposed to do, but I keep finding
        # them. The parser ignores them.
        if event_type < 8:
            raise FormatError('Unknown event type %d. Byte %d.' % (event_type,
                self.bytes_read))

        # Meta events can have strings of variable length
        if event_type == 0x0f:
            try:
                meta_event = self.bytes_to_int(fp.read(1))
                (length, chunk_delta) = self.parse_varbyte_as_int(fp)
                data = fp.read(length)
                chunk_size += 1 + chunk_delta + length
            except:
                raise IOError("Couldn't read meta event from file.")
            return ({'event': event_type, 'meta_event': meta_event,
                'data': data}, chunk_size)
        elif event_type in [12, 13]:
            # Program change and Channel aftertouch events only have one
            # parameter
            try:
                param1 = fp.read(1)
                chunk_size += 1
            except:
                raise IOError("Couldn't read MIDI event parameters from file.")
            param1 = self.bytes_to_int(param1)
            return ({'event': event_type, 'channel': channel,
                'param1': param1}, chunk_size)
        else:
            try:
                param1 = fp.read(1)
                param2 = fp.read(1)
                chunk_size += 2
            except:
                raise IOError("Couldn't read MIDI event parameters from file.")
            param1 = self.bytes_to_int(param1)
            param2 = self.bytes_to_int(param2)
            return ({'event': event_type, 'channel': channel, 'param1': param1,
                'param2': param2}, chunk_size)

    def parse_track_header(self, fp):
        """Return the size of the track chunk."""
        # Check the header
        h = fp.read(8)
        if h[0:4] != 'MTrk':
            raise HeaderError('Not a valid Track header.')
        chunk_size = self.bytes_to_int(h[4:8])
        return chunk_size

    def parse_varbyte_as_int(self, fp, return_bytes_read=True):
        """Read a variable length byte from the file and return the
        corresponding integer."""
        result = 0
        bytes_read = 0
        r = 0x80
        while r & 0x80:
            r = self.bytes_to_int(fp.read(1))
            if r & 0x80:
                result = (result << 7) + (r & 0x7F)
            else:
                result = (result << 7) + r
            bytes_read += 1
        return (result, bytes_read)
