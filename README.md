Proof of concept software synthesizer

Install
=======

On linux:
---------

- install pyaudio from http://people.csail.mit.edu/hubert/pyaudio/

and then: 

```
pip install softsynth
```

or after cloning the git repo:

```
sudo python setup.py install
```

On Mac:
-------

```
brew install portaudio
sudo easy_install pyaudio
```

and then: 

```
pip install softsynth
```

or after cloning the git repo:

```
sudo python setup.py install
```

Run
===

Stream midi:

```
blakey test_files/midi/bwv772.mid | aplay -f S16_LE -r 44100 -c 1
```

Write wav file:

```
blakey -w test_files/midi/bwv772.mid
```

Test 
====

In the root directory of the project run:

```
nosetests
```
