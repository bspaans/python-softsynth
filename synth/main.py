import sys
try:
    import pyaudio
except:
    sys.stderr.write("portaudio is not available. Falling back to writing output.wav\n")
import cProfile
import pstats
from synth.synthesizer import Synthesizer
from synth.wave_writer import WaveWriter
from synth.options import Options
from synth.instruments.OvertoneInstrument import OvertoneInstrument
from synth.note_envelopes import MidiTrackNoteEnvelope
import time
import struct

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

def plot(input):
    if "--plot" in sys.argv:
        opts = Options()
        nr_of_samples = int(sys.argv[sys.argv.index("--plot") + 1])
        if len(sys.argv) > sys.argv.index("--plot") + 2 and sys.argv[sys.argv.index("--plot") + 2].isdigit():


            start_at = int(sys.argv[sys.argv.index("--plot") + 2])
            samples = input.get_samples_in_byte_rate(nr_of_samples + start_at, 0)[start_at:]
        else:
            samples = input.get_samples_in_byte_rate(nr_of_samples)
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

def output_to_wave_writer(options, synth):
    wave = WaveWriter(options, "output.wav", also_output_to_stdout = "--stdout" in sys.argv)
    t= 0
    try:
    	w = True
        while w:
            w = wave.write_samples(synth.get_samples_in_byte_rate(options.buffer_size, t))
            t += options.buffer_size
    except KeyboardInterrupt:
        sys.stderr.write("Writted %d samples\n" % t)
    finally:
        wave.close() 

# It's global time
# Haven't found a way to pass this in to the callback. 
#
pyaudio_synth = None
pyaudio_options = None
pyaudio_time = 0

def callback(data_in, frame_count, time_info, status):
    global pyaudio_synth, pyaudio_options, pyaudio_time
    data = pyaudio_synth.get_samples_in_byte_rate(frame_count, pyaudio_time)
    if data is None:
    	return '', pyaudio.paComplete
    fmt = str(frame_count) + pyaudio_options.struct_pack_format
    data = struct.pack(fmt, *map(int, data))
    pyaudio_time += frame_count
    return ''.join(data), pyaudio.paContinue

def stream_to_pyaudio(options, synth):
    global pyaudio_synth, pyaudio_options
    pyaudio_options = options
    pyaudio_synth = synth
    output = pyaudio.PyAudio()
    stream = output.open(format=pyaudio.paInt16, channels=1, 
            rate=options.sample_rate, output=True, stream_callback=callback)
    stream.start_stream()
    while stream.is_active():
        time.sleep(0.1)
    return
    stream.stop_stream()
    stream.close()

def main():
    synth = process_midi_files()
    profile()
    plot(synth)
    opts = Options()

    wave = None
    if 'pyaudio' in globals() and "--wave" not in sys.argv:
        stream_to_pyaudio(opts, synth)
    else: 
        output_to_wave_writer(opts, synth)

if __name__ == '__main__':
    main()
