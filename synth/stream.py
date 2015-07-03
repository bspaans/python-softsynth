#!/usr/bin/env python

import struct
import time
try:
    import pyaudio
    PYAUDIO = True
except:
    sys.stderr.write("portaudio is not available. Falling back to outputting PCM,\n")
    PYAUDIO = False

pyaudio_time = 0

def stream_to_pyaudio(options, synth):

    def callback(data_in, frame_count, time_info, status):
        global pyaudio_time
        data = synth.get_samples_in_byte_rate(frame_count, pyaudio_time)
        if data is None:
            return '', pyaudio.paComplete
        fmt = str(frame_count) + options.struct_pack_format
        data = struct.pack(fmt, *map(int, data))
        pyaudio_time += frame_count
        return ''.join(data), pyaudio.paContinue

    output = pyaudio.PyAudio()
    stream = output.open(format=pyaudio.paInt16, channels=1, 
            rate=options.sample_rate, output=True, stream_callback=callback)
    stream.start_stream()
    while stream.is_active():
        time.sleep(0.1)
    return
    stream.stop_stream()
    stream.close()
