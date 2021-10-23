import numpy as np


def triangular_wave(f, times):
    moduled_time = (times - 0.25 / f) % (1/f) - 0.5/f
    saw = np.abs(moduled_time)
    norm_saw = (4 * f * saw - 1)
    return norm_saw


def generate_adsr(a, d, s, r, times):
    if a > 0:
        env = times/a
    else:
        env = s * np.ones(times.shape)
    sample_rate = int(1/(times[1] - times[0]))
    if d > 0:
        env[int(a * sample_rate):int((a+d) * sample_rate)] = 1 + (a-times[int(a * sample_rate):int((a+d) * sample_rate)])*(1-s)/d
    if r > 0:
        env[int((a+d) * sample_rate):int((a+d+r) * sample_rate)] = s + (a+d-times[int((a+d)*sample_rate):int((a+d+r) * sample_rate)])*s/r
    env[int((a+d+r) * sample_rate):] = 0
    return env
