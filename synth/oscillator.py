import math
import options
import wave_writer
import sys
import cProfile
import pstats
import numpy
import envelopes

class Oscillator(object):
    def __init__(self, options, amplitude_envelope = None):
        self.options = options
        self.freq = options.pitch_standard
        self.phase = 0
        self.phase_incr = self.options.two_pi_divided_by_sample_rate * self.freq
        self.amp_env = amplitude_envelope

    def get_samples(self, nr_of_samples):
        result = numpy.full([nr_of_samples], self.phase_incr).cumsum()
        result = numpy.add(result, self.phase * self.phase_incr)
        result = numpy.sin(result)
        if self.amp_env is not None:
            amplitudes = self.amp_env.get_amplitudes(self.phase, nr_of_samples)
            result = numpy.multiply(result, amplitudes)
        self.phase += nr_of_samples
        return result

    def get_samples_in_byte_rate(self, nr_of_samples):
        result = self.get_samples(nr_of_samples)
        return numpy.multiply(result, self.options.max_value).astype(int)


def profile_call():
    opts = options.Options()
    amp_env = envelopes.SegmentAmplitudeEnvelope()
    amp_env.add_segment(1.0, 20000)
    amp_env.add_segment(0.0, 20000)
    osc = Oscillator(opts, amp_env)
    osc.get_samples_in_byte_rate(44100)

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
    amp_env = envelopes.SegmentAmplitudeEnvelope()
    amp_env.add_segment(1.0, 20000)
    amp_env.add_segment(0.2, 20000)
    amp_env.add_segment(0.0, 10000)
    osc = Oscillator(opts, amp_env)
    wave = wave_writer.WaveWriter(opts, "output.wav", also_output_to_stdout = True)
    try:
        while True:
            wave.write_samples(osc.get_samples_in_byte_rate(1000))
            t += 1000
    except KeyboardInterrupt:
        print "Written", t, "samples" 
        wave.close() 

if __name__ == '__main__':
    main()
