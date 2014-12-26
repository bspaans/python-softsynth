import math
import numpy

class ConstantNoteEnvelope(object):
    def get_notes(self, options, t):
        return [(69, t)]

    def get_notes_for_range(self, options, phase, nr_of_samples):
        values = [(0, 10000, 69), (10000, 20000, 72), (20000, 30000, 75)]
        result = []
        for start, stop, note in values:
            if phase >= start and phase < stop:
                length = min(stop - start, nr_of_samples)
                result.append((0, phase - start, length, note))
            elif phase + nr_of_samples > start and phase + nr_of_samples < stop:
                length = nr_of_samples - start
                result.append((start - phase, 0, nr_of_samples, note))
        return result


class ArpeggioNoteEnvelope(object):
    def __init__(self):
        self.pattern1 = {1: 69, 2: 72, 3: 76, 4: 81}
        self.pattern2 = {}
        for x in xrange(1, 13):
            self.pattern2[x] = 56 + x
        self.pattern3 = {1: 64, 2: 69, 3: 72, 4: 57}

    def get_notes(self, options, t):
        rate = options.sample_rate
        change_every = rate / 8
        if (t / options.sample_rate) % 2 == 0:
            notes = self.pattern1
        else:
            notes = self.pattern3
        phase = math.floor(t / change_every) % len(notes)
        return [(notes[phase + 1], t % change_every)]

    def get_notes_for_range(self, options, phase, nr_of_samples):
        notes = numpy.zeros(nr_of_samples, dtype=numpy.int)
        phases = numpy.zeros(nr_of_samples)

        result = []
        change_every = options.sample_rate / 1
        for t in xrange(phase, phase + nr_of_samples + change_every - 1, change_every):
            if (t / options.sample_rate) % 2 == 0:
                pattern = self.pattern1
            else:
                pattern = self.pattern3
            note_phase = math.floor(t / change_every) % len(pattern)
            start_period = int(math.floor(t / change_every) * change_every)
            if start_period >= nr_of_samples + phase:
                continue
            if start_period < phase:
                start = 0
                length = min(start_period + change_every - phase, nr_of_samples - (t - phase))
            else:
                start = start_period - phase
                length = min(change_every, nr_of_samples - start)
            result.append((start, t % change_every, length, pattern[note_phase + 1]))
        return result



class TrackNoteEnvelope(object):

    def __init__(self, options, track):
        self.prepare_track(options, track)

    def prepare_track(self, options, track):
        self.mega_bar = []
        minimum = None
        maximum = None
        print track.bars
        for i, bar in enumerate(track.bars):
            for b in bar.bar:
                if b[2] == []:
                    continue
                start = (b[0] + i) * options.sample_rate
                stop = (1.0 / b[1]) * options.sample_rate + start

                if minimum is None or start < minimum:
                    minimum = start
                if maximum is None or stop > maximum:
                    maximum = stop

                notes = map(lambda n: int(n) + 24, b[2])
                self.mega_bar.append((start, stop, notes))
        self.bucket = RangeBucket(minimum, maximum)
        print self.mega_bar
        for b in self.mega_bar:
            self.bucket.add_item(*b)

    def get_notes(self, options, t):
        return self.bucket.get_notes_from_bucket(t)

class RangeBucket(object):
    def __init__(self, start, stop, slots = 12):
        self.buckets = []
        for x in range(slots):
            self.buckets.append([])
        self.start = start
        self.stop = stop
        self.slots = slots
        self.slot_size = (stop - start) / self.slots

    def add_item(self, start, stop, item):
        start_bucket = int(math.floor(start / self.slot_size))
        stop_bucket = int(math.ceil(stop / self.slot_size))
        for x in xrange(start_bucket, stop_bucket):
            self.buckets[x].append((start, stop, item))

    def get_notes_from_bucket(self, t):
        t = t % self.stop
        bucket = int(math.floor(t / self.slot_size))
        for (start, stop, items) in self.buckets[bucket]:
            if t < start or t > stop:
                continue
            for n in items:
                yield((n, t - start))

