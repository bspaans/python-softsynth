from synth.synthesizer import SampleGenerator

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
