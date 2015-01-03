from synth.interfaces import SampleGenerator
import numpy

class Oscillator(SampleGenerator):
    def __init__(self, options, freq = None):
        super(Oscillator, self).__init__(options)
        self.freq = options.pitch_standard if freq is None else freq
        self.phase_incr = self.options.two_pi_divided_by_sample_rate * self.freq

    def get_samples(self, nr_of_samples, phase, release = None, pitch_bend = None):
        result = numpy.full([nr_of_samples], self.phase_incr)
        result[0] = 0.0
        result = result.cumsum()
        result = numpy.add(result, phase * self.phase_incr)
        result = numpy.sin(result)
        return result

class OscillatorWithFrequencyControl(SampleGenerator):
    def __init__(self, options, frequency_envelope):
        super(OscillatorWithFrequencyControl, self).__init__(options)
        self.frequency_envelope = frequency_envelope

    def get_samples(self, nr_of_samples, phase, release = None, pitch_bend = None):
        frequencies, phases = self.frequency_envelope.get_frequencies(nr_of_samples, phase, release, pitch_bend)
        result = numpy.multiply(frequencies, self.options.two_pi_divided_by_sample_rate)
        result = numpy.multiply(result, phases)
        result = numpy.sin(result)
        return result

class OscillatorWithFrequencyAndAmplitudeControl(OscillatorWithFrequencyControl):
    def __init__(self, options, frequency_envelope, amplitude_envelope):
        super(OscillatorWithFrequencyAndAmplitudeControl, self).__init__(options, frequency_envelope)
        self.amp_env = amplitude_envelope

    def get_samples(self, nr_of_samples, phase, release = None, pitch_bend = None):
        result = OscillatorWithFrequencyControl.get_samples(self, nr_of_samples, phase, release, pitch_bend)
        amplitudes = self.amp_env.get_amplitudes(phase, nr_of_samples, release)
        return numpy.multiply(result, amplitudes)

class OscillatorWithAmplitudeEnvelope(Oscillator):
    def __init__(self, options, amplitude_envelope, freq = None):
        super(OscillatorWithAmplitudeEnvelope, self).__init__(options, freq)
        self.amp_env = amplitude_envelope

    def get_samples(self, nr_of_samples, phase, release = None, pitch_bend = None):
        result = Oscillator.get_samples(self, nr_of_samples, phase, release, pitch_bend)
        amplitudes = self.amp_env.get_amplitudes(phase, nr_of_samples, release)
        return numpy.multiply(result, amplitudes)

class RandomOscillatorWithAmplitudeEnvelope(Oscillator):
    def __init__(self, options, amplitude_envelope, freq = None):
        super(RandomOscillatorWithAmplitudeEnvelope, self).__init__(options, freq)
        self.amp_env = amplitude_envelope

    def get_samples(self, nr_of_samples, phase, release = None, pitch_bend = None):
        result = numpy.random.random_sample(nr_of_samples) * 2 - 1
        amplitudes = self.amp_env.get_amplitudes(phase, nr_of_samples, release)
        return numpy.multiply(result, amplitudes)

