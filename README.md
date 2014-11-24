Proof of concept software synthesizer and sequencer in pure Python

The synthesizer is modeled around sources and sinks, and streams data
using Python's generators.

Current state:

* A source can be connected to a sink
* There are two sources: a sine wave transform generator, and a mixer that can mix multiple wave sources into one
* Wave forms have attack, decay and sustain parameters
* There are two sinks: a wave file writer and a pyaudio output sink
* A primitive sequencer can be used to "schedule" sources

On linux:
=========
- pip install pyaudio
- python python-softsynth.py

On Mac:
=======
- brew install portaudio
- sudo easy_install pyaudio
- python python-softsynth.py


On Windows:
===========
- lol windows
