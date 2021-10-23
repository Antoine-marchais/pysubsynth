import sounddevice as sd
from pynput import keyboard
import os
from src.inputs import SynthController

SAMPLE_RATE = 44100
ATTACK = 0.7
DECAY = 0.2
SUSTAIN = 0.5
RELEASE = 4


def mainloop():
    os.system("stty -echo")
    synth_ctrl = SynthController(SAMPLE_RATE, 4096, 2, attack=ATTACK, decay=DECAY, sustain=SUSTAIN, release=RELEASE)
    out_stream = sd.OutputStream(samplerate=SAMPLE_RATE, blocksize=4096, callback=synth_ctrl.fill_buffer)
    synth_ctrl.connect_stream(out_stream)
    listener = keyboard.Listener(
        on_press=synth_ctrl.note_on,
        on_release=synth_ctrl.note_off
    )
    listener.start()
    while True:
        pass


if __name__ == "__main__":
    mainloop()