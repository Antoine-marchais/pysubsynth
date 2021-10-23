# PySubSynth

A substractive synth in python. This programs reads events from the key board using a piano key mapping, creates the expected signal using substractive synthesis, and outputs the result to your soundcard.

## Setup

This software has been tested on mac. There is no guarantee that it will function on other platforms.

I recommend installing the dependencies in a virtual environment:

```bash
virtualenv venv
. venv/bin/activate
pip install requirements.txt
```

## Configuration

The mapping used by the synth functions for the mac keyboard, but it might be different for a different platform, and you might want to change it according to your needs. In any case you can change the mapping used by editing the `src/resources/keyboard_mapping.csv` file. the **key** column corresponds to the virtual key number of the keyboard key you want to be associated with each note.

## Running the synth

The synth can simple be run as a python script. Beware that you might be asked for a confirmation to record keystrokes, as this program reads keyboard events.

```bash
python main.py
```

Once the program is running, the synth can be played using the keys specified in the mapping file.

