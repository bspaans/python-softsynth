Proof of concept sequencer in pure Python

The sequencer is modeled around sources and sinks, and streams data implemented
using Python's generators.

Current state:

* A source can be connected to a sink
* There are two sources: a sine wave transform generator, and a mixer that can mix multiple wave sources into one
* There is one sink: a wave file writer 
