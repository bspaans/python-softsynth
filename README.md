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

```
python synth/synth.py test/midi/test1.mid
```

or for the new, more performant, approach:

```
python synth/oscillator.py | aplay -f S16_LE -r 44100 -c 1
```

This one doesn't have midi support though. But it's so fast.
