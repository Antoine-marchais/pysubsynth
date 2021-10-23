from unittest import TestCase
from unittest.mock import MagicMock
from src.inputs import SynthController
from src.signal_processing import triangular_wave, generate_adsr
from pynput import keyboard
import numpy as np
from dataclasses import dataclass
from src.utils import plot_waves

@dataclass
class TimeStruct:
    outputBufferDacTime: float
    currentTime: float


class TestSynthController(TestCase):

    def test_fill_buffer_no_sound(self):
        stream = MagicMock()
        stream.time = 0
        synth_ctrl = SynthController(44100, 256, 2)
        synth_ctrl.connect_stream(stream)
        test_buffer = np.ones((256, 2))
        synth_ctrl.fill_buffer(test_buffer, 256, TimeStruct(2.5, 2.5), None)
        np.testing.assert_array_equal(test_buffer, np.zeros((256, 2)))

    def test_note_on(self):
        stream = MagicMock()
        stream.time = 0
        synth_ctrl = SynthController(44100, 256, 2)
        synth_ctrl.connect_stream(stream)
        stream.time = 2.5 + 128/44100
        synth_ctrl.note_on(keyboard.KeyCode(vk=4))
        test_time_range = np.linspace(0, 127/44100, 128)
        test_buffer = np.zeros((256, 2))
        wave_gen = lambda t: triangular_wave(220, t)
        test_buffer[128:, 0] = 0.2 * wave_gen(test_time_range)
        test_buffer[128:, 1] = 0.2 * wave_gen(test_time_range)
        synth_buffer = np.zeros((256, 2))
        synth_ctrl.fill_buffer(synth_buffer, 256, TimeStruct(2.5, 2.5), None)
        np.testing.assert_allclose(test_buffer, synth_buffer, rtol=0, atol=0.01)

    def test_fill_buffer_with_notes(self):
        stream = MagicMock()
        stream.time = 0
        synth_ctrl = SynthController(44100, 256, 2)
        synth_ctrl.connect_stream(stream)
        test_buffer = np.ones((256, 2))
        stream.time = 2.5 + 128/44100
        synth_ctrl.note_on(keyboard.KeyCode(vk=4))
        stream.time = 2.5 + 192/44100
        synth_ctrl.note_off(keyboard.KeyCode(vk=4))
        test_time_range = np.linspace(0, 63/44100, 64)
        ctrl_buffer = np.zeros((256, 2))
        wave_gen = lambda t: triangular_wave(220, t)
        ctrl_buffer[128:192, 0] = 0.2 * wave_gen(test_time_range)
        ctrl_buffer[128:192, 1] = 0.2 * wave_gen(test_time_range)
        synth_ctrl.fill_buffer(test_buffer, 256, TimeStruct(2.5, 2.5), None)
        np.testing.assert_allclose(test_buffer, ctrl_buffer, atol=0.01, rtol=0)

    def test_continuity(self):
        stream = MagicMock()
        stream.time = 0
        synth_ctrl = SynthController(44100, 256, 2)
        synth_ctrl.connect_stream(stream)
        test_buffer = np.ones((768, 2))
        stream.time = 2.5 + 128/44100
        synth_ctrl.note_on(keyboard.KeyCode(vk=4))
        synth_ctrl.fill_buffer(test_buffer[:256], 256, TimeStruct(2.5, 2.5), None)
        synth_ctrl.fill_buffer(test_buffer[256:512], 256, TimeStruct(2.5 + 256/44100, 2.5 + 256/44100), None)
        synth_ctrl.fill_buffer(test_buffer[512:], 256, TimeStruct(2.5 + 512/44100, 2.5 + 512/44100), None)
        self.assertAlmostEqual(test_buffer[511, 0], test_buffer[512, 0], delta=0.01)

    def test_phase_shift(self):
        synth_ctrl = SynthController(44100, 256, 2)
        test_buffer = np.zeros((256, 2))
        synth_ctrl.phase_shift_wave(synth_ctrl.note_dict.from_name("A3"), 0.20/220, test_buffer)
        self.assertAlmostEqual(test_buffer[int(0.30/220*synth_ctrl.samplerate), 0], 0, delta=0.01)

    def test_apply_ad(self):
        synth_ctrl = SynthController(44100, 512, 2, attack=384/44100, decay=512/44100, sustain=0.2)
        test_buffer = np.zeros((512, 2))
        synth_ctrl.phase_shift_wave(synth_ctrl.note_dict.from_name("A3"), 256/44100, test_buffer)
        synth_ctrl.apply_ad(256/44100, test_buffer)
        test_time_range = np.linspace(0, (256+511)/44100, 256+512)
        wave = 0.2 * triangular_wave(220, test_time_range)
        adsr = generate_adsr(384/44100, 512/44100, 0.2, 1000, test_time_range)
        true_wave = wave * adsr
        np.testing.assert_allclose(test_buffer[:, 0], true_wave[256:], atol=0.01, rtol=0)

    def test_apply_release(self):
        synth_ctrl = SynthController(44100, 512, 2, release=512/44100)
        test_buffer = np.zeros((512, 2))
        synth_ctrl.phase_shift_wave(synth_ctrl.note_dict.from_name("A3"), 256/44100, test_buffer)
        synth_ctrl.apply_release(256/44100, test_buffer)
        test_time_range = np.linspace(0, 767/44100, 768)
        wave = 0.2 * triangular_wave(220, test_time_range)
        adsr = generate_adsr(0, 0, 1, 512/44100, test_time_range)
        true_wave = wave * adsr
        np.testing.assert_allclose(test_buffer[:, 0], true_wave[256:], atol=0.01, rtol=0)

    def test_triangular_and_adsr(self):
        stream = MagicMock()
        stream.time = 0
        synth_ctrl = SynthController(44100, 512, 2, attack=256/44100, decay=256/44100, sustain=0.3, release=512/44100)
        synth_ctrl.connect_stream(stream)
        test_buffer = np.zeros((2048, 2))
        stream.time = 2.5 + 256 / 44100
        synth_ctrl.note_on(keyboard.KeyCode(vk=4))
        synth_ctrl.fill_buffer(test_buffer[:512, :], 512, TimeStruct(2.5, 2.5), None)
        synth_ctrl.fill_buffer(test_buffer[512: 1024], 512, TimeStruct(2.5+512/44100, 2.5+512/44100), None)
        stream.time = 2.5 + 1280 / 44100
        synth_ctrl.note_off(keyboard.KeyCode(vk=4))
        synth_ctrl.fill_buffer(test_buffer[1024: 1536], 512, TimeStruct(2.5+1024/44100, 2.5+1024/44100), None)
        synth_ctrl.fill_buffer(test_buffer[1536: 2048], 512, TimeStruct(2.5+1536/44100, 2.5+1536/44100), None)
        test_time_range = np.linspace(0, 2047/44100, 2048)
        true_wave = np.zeros(test_time_range.shape)
        wave = 0.2*triangular_wave(220, test_time_range[:-256])
        adsr = generate_adsr(256/44100, 256/44100, 0.3, 512/44100, test_time_range)
        padded_adsr = np.zeros(test_time_range.shape)
        padded_adsr[256:768] = adsr[:512]
        padded_adsr[768:1280] = 0.3
        padded_adsr[1280:1792] = adsr[512: 1024]
        true_wave[256:] = wave * padded_adsr[256:]
        np.testing.assert_allclose(test_buffer[:, 0], true_wave, atol=0.01, rtol=0)

