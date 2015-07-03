import sys
import argparse

from synth.synthesizer import Synthesizer
from synth.wave_writer import WaveWriter
from synth.options import Options
from synth import stream
from synth.instruments.OvertoneInstrument import OvertoneInstrument
from synth.note_envelopes import MidiTrackNoteEnvelope

def profile_call():
    opts = Options()
    instr = OvertoneInstrument(opts, ArpeggioNoteEnvelope())
    input = instr
    input.get_samples_in_byte_rate(44100)

def profile(opts):
    if opts.profile_application:
        import cProfile
        import pstats
        cProfile.run('profile_call()', 'restats')
        p = pstats.Stats('restats')
        p.strip_dirs().sort_stats('time').print_stats()
        sys.exit(0)


def get_args():
    parser = argparse.ArgumentParser(prog='synth',
            description='Programmable synth')
    parser.add_argument('input', metavar='INPUT', nargs=1, 
            help='the input file path')
    parser.add_argument('output', metavar='OUTPUT', nargs='?', 
            help='the optional output file path. Default is INPUT.wav')
    parser.add_argument('-w', '--wave', action='store_true',
            help='Output wave file.')
    parser.add_argument('--profile', action='store_true',
            help='Profile the application to find hot spots.')
    parser.add_argument('--stdout', action='store_true',
            help='Also write PCM data to stdout. Only valid in conjunction with the --wave flag.')
    args = parser.parse_args()
    opts = Options(args.input[0], args.output)
    opts.write_wave = args.wave
    opts.write_wave_to_stdout = args.stdout
    opts.profile_application = args.profile
    return opts

def main():
    opts = get_args()
    synth = Synthesizer(opts).load_from_midi(opts.input)
    profile(opts)

    wave = None
    if stream.PYAUDIO and not opts.write_wave:
        stream.stream_to_pyaudio(opts, synth)
    else: 
        WaveWriter(opts).output(synth)

if __name__ == '__main__':
    main()
