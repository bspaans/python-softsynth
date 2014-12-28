import binascii 

class MidiHeader(object):
    def parse_header_from_file(self, fp):
        data = fp.read(14)

        header           = data[0:4]
        chunk_size       = self.bytes_to_int(data[4:8])
        format_type      = self.bytes_to_int(data[8:10])
        number_of_tracks = self.bytes_to_int(data[10:12])
        time_division    = self.parse_time_division(data[12:14])

        if header != 'MThd':
            raise Exception('Not a valid MIDI file header.')
        if format_type not in [0, 1, 2]:
            raise Exception('%d is not a valid MIDI format.' % format_type)
        if chunk_size < 6:
            return False
        chunk_size -= 6
        if chunk_size % 2 == 1:
            raise Exception("Won't parse this.")
        fp.read(chunk_size / 2)

        return {'format_type': format_type, 
            'number_of_tracks': number_of_tracks, 
            'time_division': time_division}

    def bytes_to_int(self, bytes):
        return int(binascii.b2a_hex(bytes), 16)

    def parse_time_division(self, bytes):
        """Parse the time division found in the header of a MIDI file and
        return a dictionary with the boolean fps set to indicate whether to
        use frames per second or ticks per beat.

        If fps is True, the values SMPTE_frames and clock_ticks will also be
        set. If fps is False, ticks_per_beat will hold the value.
        """
        # If highest bit is set, time division is set in frames per second
        # otherwise in ticks_per_beat
        value = self.bytes_to_int(bytes)
        if not value & 0x8000:
            return {'fps': False, 'ticks_per_beat': value & 0x7FFF}
        else:
            SMPTE_frames = (value & 0x7F00) >> 2
            if SMPTE_frames not in [24, 25, 29, 30]:
                raise TimeDivisionError, \
                    "'%d' is not a valid value for the number of SMPTE frames"\
                     % SMPTE_frames
            clock_ticks = (value & 0x00FF) >> 2
            return {'fps': True, 'SMPTE_frames': SMPTE_frames,
                    'clock_ticks': clock_ticks}

