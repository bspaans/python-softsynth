import sys
import cProfile
import pstats
from synth.wave_writer import WaveWriter
from synth.midi.MidiFileParser import MidiFileParser
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

def create_synth_from_midi_tracks(header, tracks):
    options = Options()
    ticks_per_beat = header["time_division"]['ticks_per_beat']
    for t in tracks:
        instr = OvertoneInstrument
        instrument = instr(options, MidiTrackNoteEnvelope(options, t, ticks_per_beat))
        return instrument

def process_midi_files():
    global amplitude_generator
    for f in sys.argv:
        if ".mid" in f:
            (header, tracks) = MidiFileParser().parse_midi_file(sys.argv[1])
            tracks = filter(lambda t: len(filter(lambda x: x.event_type in [8,9], t.events)) != 0, tracks)
            synth = create_synth_from_midi_tracks(header, tracks)
            return synth

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
