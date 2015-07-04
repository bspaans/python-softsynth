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

If pyaudio is installed you can stream midi by running:

```
synth test_files/midi/bwv772.mid
```

Streaming midi without pyaudio is also possible by piping into `aplay`:

```
synth test_files/midi/bwv772.mid --wave --stdout | aplay -f S16_LE -r 44100 -c 1
```

You can also write wav files directly with `--wave` or `-w`:

```
synth -w test_files/midi/bwv772.mid
```

Test 
====

In the root directory of the project run:

```
nosetests
```
