from dataclasses import dataclass


@dataclass
class Note:
    name: str
    midi: int
    frequency: float


class NoteDict:
    def __init__(self):
        self.midi_dict = {}
        self.name_dict = {}
        with open("src/resources/note_list.csv", "r") as f:
            all_notes = f.read().split("\n")
            all_notes.pop(0)
            all_notes.pop(-1)
            for note_line in all_notes:
                name, midi, freq = note_line.split(",")
                self.midi_dict[int(midi)] = Note(str(name), int(midi), float(freq))
                self.name_dict[name] = Note(str(name), int(midi), float(freq))

    def from_name(self, name: str):
        return self.name_dict.get(name, None)

    def from_midi(self, midi: int):
        return self.midi_dict.get(midi, None)


class KeyBoardMapping:
    def __init__(self):
        self.note_dict = NoteDict()
        self.key_dict = {}
        with open("src/resources/keyboard_mapping.csv", "r") as f:
            all_keys = f.read().split("\n")
            all_keys.pop(0)
            all_keys.pop(-1)
            for key_line in all_keys:
                name, keycode = key_line.split(",")
                self.key_dict[int(keycode)] = self.note_dict.from_name(name)

    def from_key(self, key_code: int):
        return self.key_dict.get(key_code, None)

    def shift_up(self):
        for key in self.key_dict:
            current_note = self.key_dict[key]
            self.key_dict[key] = self.note_dict.from_midi(current_note.midi + 12)

    def shift_down(self):
        for key in self.key_dict:
            current_note = self.key_dict[key]
            self.key_dict[key] = self.note_dict.from_midi(current_note.midi - 12)


def generate_notes():
    note_list = open("src/resources/note_list.csv", "w")
    note_list.write("name,midi,freq\n")
    for octave in range(-1, 10):
        for idx, note in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]):
            name = note + str(octave)
            midi = (octave + 1) * 12 + idx
            freq = 27.5 * 2 ** ((midi - 21) / 12)
            if octave < 9 or idx < 8:
                note_list.write(f"{name},{midi},{freq}\n")
    note_list.close()


if __name__ == "__main__":
    generate_notes()
