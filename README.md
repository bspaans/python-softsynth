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
python main.py test_files/midi/bwv772.mid | aplay -f S16_LE -r 44100 -c 1
```

Test 
====

In the root directory of the project run:

```
nosetests
```
