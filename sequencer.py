#!/usr/bin/env python

from mingus.midi.sequencer import Sequencer
from mingus.midi import midi_file_in
import multiprocessing
import time
import softsynth
import sys

class SoftsynthSequencer(Sequencer):

    def __init__(self):
        super(SoftsynthSequencer, self).__init__()

    def init(self):
        print "Initializing softsynth"
        (self.command_queue, self.synth_proc) = softsynth.start_softsynth()
        self.synth_proc.start()

    def play_event(self, note, channel, velocity):
        self.command_queue.put(('noteon', note))

    def stop_event(self, note, channel):
        self.command_queue.put(('noteoff', note))

    def cc_event(self, channel, control, value):
        pass

    def instr_event(self, channel, instr, bank):
        pass

    def sleep(self, seconds):
        time.sleep(seconds)


def main():
    (composition, bpm) = midi_file_in.MIDI_to_Composition(sys.argv[1])
    track = filter(lambda t: len(t.bars) != 1, composition.tracks)[0]
    track = track.transpose('7', True)
    sequencer = SoftsynthSequencer()
    sequencer.play_Track(track)

if __name__ == '__main__':
    main()
