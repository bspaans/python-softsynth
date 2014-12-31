from synth.interfaces import SampleGenerator
import wave
import struct
import numpy
import sys
import math

wavefile_cache = {}

class PCM(SampleGenerator):
    def __init__(self, options, file, amplitude_envelope = None):
        super(PCM, self).__init__(options)
        self.amp_env = amplitude_envelope
        self.file = file
        self.load_file(file)

    def load_file(self, file):
        global wavefile_cache
        if file in wavefile_cache:
            self.length = len(wavefile_cache[file])
            self.wavefile = wavefile_cache[file]
            return
        w = wave.open(file)
        if w.getframerate() != self.options.sample_rate:
            raise "sample rate mismatch"
        if w.getsampwidth() != self.options.byte_rate:
            raise "byte rate mismatch"
        if w.getnchannels() != 1:
            raise "channel mismatch"
        frames = w.readframes(w.getnframes())
        samples = struct.unpack(str(w.getnframes()) + self.options.struct_pack_format, frames)
        self.wavefile = numpy.array([s / float(self.options.max_value) for s in samples])
        self.length = w.getnframes()
        w.close()
        wavefile_cache[file] = self.wavefile
        sys.stderr.write("Loaded %s\n" % file)

    def get_samples(self, nr_of_samples, phase, release = None):
        if phase > self.length:
            result = numpy.zeros(nr_of_samples)
        elif phase + nr_of_samples < self.length:
            result = self.wavefile[phase:phase + nr_of_samples]
        else:
            result = numpy.zeros(nr_of_samples)
            samples = self.length - phase
            result[:samples] = self.wavefile[phase:]
        return result

class PCMWithFrequency(PCM):

    def __init__(self, options, file, freq = None, amplitude_envelope = None):
        super(PCMWithFrequency, self).__init__(options, file)
        self.freq = options.pitch_standard if freq is None else freq
        self.freq_ratio = self.freq / self.options.pitch_standard

    def get_samples(self, nr_of_samples, phase, release = None):
        if self.freq == self.options.pitch_standard:
            return PCM.get_samples(self, nr_of_samples, phase, release)

        result = numpy.zeros(nr_of_samples)
        for t in xrange(phase, phase + nr_of_samples):
            index = t * self.freq_ratio
            mod = index % 1
            if mod == 0:
                result[t-phase] = self.wavefile[math.floor(index)]
            else:
                s1 = self.wavefile[math.floor(index)] * (mod)
                s2 = self.wavefile[math.floor(index + 1)] * (1 - mod)
                result[t - phase] = (s1 + s2)
        return result
