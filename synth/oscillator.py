import math
import options
import wave_writer
import sys
import cProfile
import pstats
import numpy

class SynthObject(object):
    def __init__(self, options):
        self.options = options
        self.freq = options.pitch_standard
        self.phase = 0

    def get_samples(self, nr_of_samples):
        phase_incr = self.options.two_pi_divided_by_sample_rate * self.freq
        result = numpy.arange(nr_of_samples)
        result = numpy.multiply(result, phase_incr)
        result = numpy.add(result, self.phase * phase_incr)
        result = numpy.sin(result)
        self.phase += nr_of_samples
        return numpy.multiply(result, self.options.max_value).astype(int)

class Oscillator(SynthObject):
    def __init__(self, options):
        super(Oscillator, self).__init__(options)

    def phase_to_int(self, phase):
        return math.sin(phase)



def profile_call():
    Oscillator(options.Options()).get_samples(44100)

def profile():
    if "--profile" in sys.argv:
        cProfile.run('profile_call()', 'restats')
        p = pstats.Stats('restats')
        p.strip_dirs().sort_stats('time').print_stats()
        sys.exit(0)

def main():
    profile()
    t= 0
    opts = options.Options()
    osc = Oscillator(opts)
    wave = wave_writer.WaveWriter(opts, "output.wav", also_output_to_stdout = True)
    try:
        while True:
            wave.write_samples(osc.get_samples(1000))
            t += 1000
    except KeyboardInterrupt:
        print "Written", t, "samples" 
        wave.close() 

if __name__ == '__main__':
    main()
