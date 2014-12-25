import wave
import struct 
import sys 

class WaveWriter(object):

    def __init__(self, options, filename, also_output_to_stdout = False):
        self.options = options
        self.filename = filename
        self.also_output_to_stdout = also_output_to_stdout
        self.open()

    def open(self):
        w = wave.open(self.filename, "w")
        w.setnchannels(1)
        w.setsampwidth(self.options.byte_rate)
        w.setframerate(self.options.sample_rate)
        self.wave = w
        self.data = []

    def write(self, elem):
        sample = struct.pack(self.options.struct_pack_format, int(elem))
        self.data.append(sample)
        if len(self.data) > 1024:
            if self.also_output_to_stdout:
                sys.stdout.write(''.join(self.data))
                sys.stdout.flush()
            self.wave.writeframes(''.join(self.data))
            self.data = []

    def write_samples(self, elems):
        fmt = str(len(elems)) + self.options.struct_pack_format
        sample = struct.pack(fmt, *map(int, elems))
        if self.also_output_to_stdout:
            sys.stdout.write(sample)
            sys.stdout.flush()
        self.wave.writeframes(sample)

    def close(self):
        self.wave.close()
        print "Written", self.filename

