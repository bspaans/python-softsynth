Proof of concept software synthesizer

Install
=======

On linux:
---------

- install pyaudio from http://people.csail.mit.edu/hubert/pyaudio/

```
sudo pip install -r requirements.txt
```

On Mac:
-------

```
brew install portaudio
sudo easy_install pyaudio
sudo pip install -r requirements.txt 
```

Run
===

Run the synth as a TCP server:

```
python softsynth.py
```

Or run the MIDI sequencer:

```
python sequencer.py midifile.mid
```
