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
python synth/sine.py test/midi/test1.mid midi
```

