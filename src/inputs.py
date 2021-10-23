import numpy as np
from pynput import keyboard
import sounddevice as sd
from src.notes import NoteDict, Note, KeyBoardMapping
from src.signal_processing import triangular_wave, generate_adsr
from dataclasses import dataclass
from threading import Lock


@dataclass
class MidiEvent:
    midi: int
    start_time: float
    end_time: float


class SynthController:
    def __init__(self, samplerate, blocksize, channels=2, attack=0, decay=0, sustain=1, release=0):
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.n_channels = channels
        self.midi_events = {}
        self.released_events = []
        self.out_stream: sd.OutputStream = None
        self.amplitude = 0.2
        self.waves = {}
        self.note_dict = NoteDict()
        self.key_mapping = KeyBoardMapping()
        self.init_waves()
        self.midi_lock = Lock()
        self.attack = attack
        self.sustain = sustain
        self.decay = decay
        self.release = release
        self.ad_env = None
        self.release_env = None
        self.compute_adsr()

    def connect_stream(self, stream: sd.OutputStream) -> None:
        self.out_stream = stream
        self.out_stream.start()

    def note_on(self, key: keyboard.Key) -> None:
        if isinstance(key, keyboard.KeyCode):
            note = self.key_mapping.from_key(key.vk)
            self.midi_lock.acquire()
            if note is not None and note.midi not in self.midi_events:
                self.midi_events[note.midi] = MidiEvent(note.midi, self.out_stream.time, None)
            self.midi_lock.release()
        elif key == keyboard.Key.up:
            self.key_mapping.shift_up()
        elif key == keyboard.Key.down:
            self.key_mapping.shift_down()

    def note_off(self, key: keyboard.KeyCode) -> None:
        if isinstance(key, keyboard.KeyCode):
            note = self.key_mapping.from_key(key.vk)
            if note is not None and note.midi in self.midi_events:
                self.midi_events[note.midi].end_time = self.out_stream.time
                self.released_events.append(self.midi_events.pop(note.midi))

    def fill_buffer(self, indata: np.ndarray, frames: int, stream_time, status: sd.CallbackFlags) -> None:
        buffer_start = stream_time.outputBufferDacTime
        indata.fill(0)
        events_to_clean = []
        self.midi_lock.acquire()
        iter_events = list(self.midi_events.values()) + self.released_events
        self.midi_lock.release()
        for event in iter_events:
            wave_buffer = np.zeros(indata.shape)
            begin_time = max(event.start_time, buffer_start)
            begin_index = round((begin_time-buffer_start) * self.samplerate)
            release_index = self.blocksize if event.end_time is None else max(0, min(round((event.end_time - buffer_start) * self.samplerate), self.blocksize))
            end_index = self.blocksize if event.end_time is None else max(0, min(round((event.end_time+self.release-buffer_start) * self.samplerate), self.blocksize))
            self.phase_shift_wave(self.note_dict.from_midi(event.midi), begin_time - event.start_time, wave_buffer[begin_index: end_index])
            self.apply_ad(begin_time - event.start_time, wave_buffer[begin_index: release_index])
            if release_index != self.blocksize:
                release_time = max(0, buffer_start - event.end_time)
                self.apply_release(release_time, wave_buffer[release_index: end_index])
            if event.end_time is not None and buffer_start + self.blocksize/self.samplerate > event.end_time + self.release:
                events_to_clean.append(event)
            indata += wave_buffer
        for event in events_to_clean:
            self.released_events.remove(event)

    def phase_shift_wave(self, midi_note: Note, elapsed_time: float, buffer: np.ndarray):
        offset = int((elapsed_time % (1 / midi_note.frequency)) * self.samplerate)
        num_frames = buffer.shape[0]
        for i in range(buffer.shape[1]):
            buffer[:, i] = self.waves[midi_note.midi][offset: offset+num_frames]

    def apply_ad(self, elapsed_time, buffer):
        start_index = min(self.ad_env.shape[0], int(elapsed_time * self.samplerate))
        end_index = min(self.ad_env.shape[0], int(elapsed_time * self.samplerate) + buffer.shape[0])
        for i in range(buffer.shape[1]):
            buffer[:end_index-start_index, i] = buffer[:end_index-start_index, i] * self.ad_env[start_index: end_index]
            buffer[end_index-start_index:, i] = self.sustain * buffer[end_index-start_index:, i]

    def apply_release(self, elapsed_time, buffer):
        start_index = int(elapsed_time * self.samplerate)
        for i in range(buffer.shape[1]):
            buffer[:, i] = buffer[:, i] * self.release_env[start_index: start_index + buffer.shape[0]]

    def init_waves(self):
        for midi, note in self.note_dict.midi_dict.items():
            min_len = max(int(2/note.frequency*self.samplerate), 2*self.blocksize)
            timerange = np.linspace(0, min_len/self.samplerate, min_len-1)
            self.waves[midi] = self.amplitude * triangular_wave(note.frequency, timerange)

    def compute_adsr(self):
        min_len = int((self.attack + self.decay + self.release) * self.samplerate + self.blocksize)
        adsr_times = np.linspace(0, min_len/self.samplerate, min_len-1)
        adsr = generate_adsr(self.attack, self.decay, self.sustain, self.release, adsr_times)
        self.ad_env = adsr[:int((self.attack + self.decay) * self.samplerate)]
        self.release_env = adsr[int((self.attack + self.decay) * self.samplerate):]

