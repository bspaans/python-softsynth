import pyaudio
import struct
import wave

class Sink(object):
    def __init__(self, options):
        self.sample_rate   = options.sample_rate
        self.byte_rate     = options.byte_rate
        self.struct_format = options.struct_pack_format
        self.options = options
    def open(self):
        pass # setup processing
    def write(self, elem):
        pass # do some processing
    def close(self):
        pass # finish of processing

class WaveWriter(Sink):

    def __init__(self, options, filename):
        super(WaveWriter, self).__init__(options)
        self.filename      = filename

    def open(self):
        self.data = []

    def write(self, elem):
        sample = struct.pack(self.struct_format, int(elem))
        self.data.append(sample)

    def close(self):
        w = wave.open(self.filename, "w")
        w.setnchannels(1)
        w.setsampwidth(self.byte_rate)
        w.setframerate(self.sample_rate)
        w.writeframes(''.join(self.data))
        w.close()
        print "Written", self.filename

class PyAudioWriter(Sink):

    def __init__(self, options):
        super(PyAudioWriter, self).__init__(options)
        self.pyaudio = pyaudio.PyAudio()
        self.BUFFER_SIZE   = 2

    def open(self):
        self.stream = self.pyaudio.open(format=pyaudio.paInt16 , channels=1, rate=self.sample_rate, output=True)
        self.data = []

    def write(self, elem):
        sample = struct.pack(self.struct_format, int(elem))
        self.data.append(sample)
        if len(self.data) == self.BUFFER_SIZE:
            self.stream.write(''.join(self.data))
            self.data = []

    def close(self):
        self.stream.close()

