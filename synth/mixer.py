from synth.source import Source

class Mixer(Source):
    def __init__(self, options):
        super(Mixer, self).__init__(options)
        self.sources = {}

    def add_source(self, source, token_id):
        self.sources[token_id] = source.read()

    def remove_source(self, source, token_id):
        if token_id not in self.sources:
            return 
        del(self.sources[token_id])

    def _read_from_generators(self):
        values = []
        empty_generators = []
        for (token_id, generator) in self.sources.iteritems():
            try:
                values.append(generator.next())
            except StopIteration:
                empty_generators.append(token_id)
        map(self.remove_source, empty_generators)
        return values

    def read(self):
        id(self.sources)
        while True:
            values = self._read_from_generators()
            number_of_sources = len(values)
            if number_of_sources == 0:
                yield 0.0
            else:
                yield (sum(values) / number_of_sources)

    def __repr__(self):
        return "<mixer [%s]>" % (", ".join(map(str, self.sources)))

