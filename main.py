import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt

SAMPLE_RATE = 44100
freq = 220
ampl = 0.5

def triangular_wave(ampl, f, t):
    return ampl * (4 * f * np.abs(t % (1/f) - 0.5/f) - 1)

def generate_adsr(a, d, s, r, note_len, sample_rate):
    time_array = np.arange(0, note_len+r, 1/sample_rate)
    env = time_array/a
    env[int(a * sample_rate):int((a+d) * sample_rate)] = 1 + (a-time_array[int(a * sample_rate):int((a+d) * sample_rate)])*(1-s)/d
    env[int((a+d)*sample_rate):int(note_len*sample_rate)] = s
    env[int(note_len*sample_rate):] = s + (note_len-time_array[int(note_len*sample_rate):])*s/r
    return env

time_array = np.arange(0, 2, 1/SAMPLE_RATE)
wav_gen = lambda t: triangular_wave(ampl, freq, t)
adsr = generate_adsr(0.1, 0.3, 0.5, 0.4, 1.2, SAMPLE_RATE).astype(np.float32)
lpcm = wav_gen(time_array).astype(np.float32)
lpcm[:adsr.size] = lpcm[:adsr.size] * adsr
lpcm[adsr.size:] = 0

sd.play(lpcm, samplerate=SAMPLE_RATE)
sd.wait()