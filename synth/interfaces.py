import numpy

class SampleGenerator(object):

    def __init__(self, options):
        self.options = options
        self.last_level = 0.0

    def get_samples(self, nr_of_samples, phase, release = None):
    	# Should return an array of length nr_of_samples
	# with values between -1.0 and 1.0
        pass

    def get_samples_in_byte_rate(self, nr_of_samples, phase, release = None):
        result = self.get_samples(nr_of_samples, phase, release)
        return numpy.multiply(result, self.options.max_value).astype(int)


