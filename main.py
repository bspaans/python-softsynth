import sys
import cProfile
import pstats
from synth.synthesizer import Synthesizer
from synth.wave_writer import WaveWriter
from synth.options import Options
from synth.instruments import OvertoneInstrument
from synth.note_envelopes import ArpeggioNoteEnvelope,\
        ConstantNoteEnvelope, MidiTrackNoteEnvelope

def profile_call():
    opts = Options()
    instr = OvertoneInstrument(opts, ArpeggioNoteEnvelope())
    input = instr
    input.get_samples_in_byte_rate(44100)

def profile():
    if "--profile" in sys.argv:
        cProfile.run('profile_call()', 'restats')
        p = pstats.Stats('restats')
        p.strip_dirs().sort_stats('time').print_stats()
        sys.exit(0)

def plot():
    if "--plot" in sys.argv:
        opts = Options()
        instr = OvertoneInstrument(opts, ArpeggioNoteEnvelope())
        input = instr
        nr_of_samples = int(sys.argv[sys.argv.index("--plot") + 1])
        if len(sys.argv) > sys.argv.index("--plot") + 2 and sys.argv[sys.argv.index("--plot") + 2].isdigit():


            start_at = int(sys.argv[sys.argv.index("--plot") + 2])
            samples = instr.get_samples_in_byte_rate(nr_of_samples + start_at)[start_at:]
        else:
            samples = instr.get_samples_in_byte_rate(nr_of_samples)
        import Gnuplot
        g = Gnuplot.Gnuplot()
        g.title("Yo")
        g("set data style linespoints")
        g.plot(zip(xrange(nr_of_samples), samples))
        raw_input('Please press return to continue...\n')
        sys.exit(0)

def process_midi_files():
    for f in sys.argv:
        if ".mid" in f:
            return Synthesizer(Options()).load_from_midi(f)

def main():
    input = process_midi_files()
    profile()
    plot()
    t= 0
    opts = Options()
    if input is None:
        env = ArpeggioNoteEnvelope()
        env = ConstantNoteEnvelope(opts, 68)
        instr = OvertoneInstrument(opts, env)
        input = instr
    wave = WaveWriter(opts, "output.wav", also_output_to_stdout = True)
    try:
        while True:
            wave.write_samples(input.get_samples_in_byte_rate(1000, t))
            t += 1000
    except KeyboardInterrupt:
        print "Written", t, "samples" 
        wave.close() 

if __name__ == '__main__':
    main()
