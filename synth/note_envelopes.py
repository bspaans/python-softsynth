import math

class ConstantNoteEnvelope(object):
    def get_notes(self, options, t):
        return [(69, t)]

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

