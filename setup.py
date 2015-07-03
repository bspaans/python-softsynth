#!/usr/bin/env python

try:
    from setuptools import setup, find_packages
except ImportError:
    print("setuptools is missing. Install it using your package "
        + "manager (usually python-setuptools) or via pip (pip"
        + " install setuptools).")

setup(name= "softsynth",
    version = "0.3.3",
    description = "Proof of concept software synthesizer",
    long_description = """you too""",
    author = "Bart Spaans",
    author_email = "bart.spaans@gmail.com",
    url = "https://github.com/bspaans/python-softsynth",
    packages = ['synth', 'synth.midi', 'synth.instruments'],
    license="GPLv3",
    classifiers = [
        'Intended Audience :: Developers',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Artistic Software',
        'Topic :: Education',
        'Topic :: Multimedia',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Sound/Audio :: MIDI',
        ],
    entry_points = { 
        'console_scripts': [
            'synth = synth.main:main'
        ]
    }
)
