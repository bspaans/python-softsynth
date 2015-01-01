from MidiHeader import MidiHeader
from MidiTrack import MidiTrack

class MidiFileParser(object):

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
            result.append(MidiTrack().parse_track(f))
        f.close()
        result = self.split_tracks_into_channels(result)
        return (header, result)

    def split_tracks_into_channels(self, tracks):
        channels = {}
        for t in tracks:
            for e in t.events:
                channel = channels.get(e.channel, [])
                channel.append(e)
                channels[e.channel] = channel 
        return channels
