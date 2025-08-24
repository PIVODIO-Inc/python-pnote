from __future__ import annotations

from typing import List, Union
import io
import os
from typing import BinaryIO
import mido


# Map MIDI note number to pitch name + octave (C4 = MIDI 60)
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


class Event:
    def __init__(self, start: int):
        self.start = start

    def to_pnote(self) -> str:
        raise NotImplementedError


class NoteEvent(Event):
    def __init__(self, pitch: str, start: int, dur: int, vel: int):
        super().__init__(start)
        self.pitch = pitch
        self.dur = dur
        self.vel = vel

    def to_pnote(self) -> str:
        return f"{self.pitch}:start={self.start}:dur={self.dur}:vel={self.vel}"


class ControlEvent(Event):
    def __init__(self, name: str, value: str, start: int):
        super().__init__(start)
        self.name = name
        self.value = value

    def to_pnote(self) -> str:
        return f"{self.name}:{self.value}:start={self.start}"


class PNote:
    """Container for a sequence of events in PNote format."""

    def __init__(self, events: List[Event] | None = None):
        self.events: List[Event] = []
        if events:
            for event in events:
                self.add_event(event)

    def add_event(self, event: Event) -> None:
        # Insert in the correct position to maintain sorted invariant per spec
        new_key = _event_sort_key(event)
        for idx, existing in enumerate(self.events):
            if new_key < _event_sort_key(existing):
                self.events.insert(idx, event)
                return
        self.events.append(event)

    def to_string(self) -> str:
        """Return the entire notation as a single string.

        Ensures events are sorted per the specification before rendering.
        """
        return "\n".join(e.to_pnote() for e in self.events)

    def __str__(self) -> str:  # pragma: no cover - convenience
        return self.to_string()

    @classmethod
    def from_midi(cls, source: Union[str, os.PathLike, bytes, bytearray, BinaryIO]) -> "PNote":
        """Construct a PNote from a MIDI source.

        Accepted `source` types: filesystem path (`str`/`os.PathLike`), raw
        `bytes`/`bytearray`, or a binary file-like object with a `read()` method.

        This method will create the appropriate `mido.MidiFile` internally and
        delegate to the private `_from_midi_mid` loader.
        """

        # bytes -> BytesIO
        if isinstance(source, (bytes, bytearray)):
            file_obj = io.BytesIO(source)
            mid = mido.MidiFile(file=file_obj)
        # file-like
        elif hasattr(source, "read"):
            # assume binary mode file-like
            mid = mido.MidiFile(file=source)
        # path-like
        elif isinstance(source, (str, os.PathLike)):
            mid = mido.MidiFile(filename=str(source))
        else:
            raise TypeError("Unsupported source type for from_midi; expected path, bytes, or file-like object")

        return cls._from_midi_mid(mid)

    @classmethod
    def _from_midi_mid(cls, mid: "mido.MidiFile") -> "PNote":
        """Internal: construct a PNote from an already-created mido.MidiFile."""
        pnote = cls()
        current_tempo = 500000  # default microseconds per beat
        for track in mid.tracks:
            absolute_ticks = 0
            note_on_times = {}
            for msg in track:
                absolute_ticks += msg.time
                if msg.type == 'set_tempo':
                    current_tempo = msg.tempo
                    start = _ticks_to_sixtyfourth(absolute_ticks, mid.ticks_per_beat, current_tempo)
                    pnote.add_event(ControlEvent('Tempo', str(mido.tempo2bpm(current_tempo)), start))
                elif msg.type == 'note_on' and msg.velocity > 0:
                    start = _ticks_to_sixtyfourth(absolute_ticks, mid.ticks_per_beat, current_tempo)
                    note_on_times.setdefault(msg.note, []).append((absolute_ticks, msg.velocity))
                elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
                    if msg.note in note_on_times and note_on_times[msg.note]:
                        on_tick, vel = note_on_times[msg.note].pop(0)
                        start = _ticks_to_sixtyfourth(on_tick, mid.ticks_per_beat, current_tempo)
                        end = _ticks_to_sixtyfourth(absolute_ticks, mid.ticks_per_beat, current_tempo)
                        dur = max(1, end - start)
                        pitch = _midi_note_to_pitch(msg.note)
                        pnote.add_event(NoteEvent(pitch, start, dur, vel))
        return pnote


def _ticks_to_sixtyfourth(ticks: int, ticks_per_beat: int, tempo_us_per_beat: int) -> int:
    # Convert MIDI ticks to sixty-fourth-note counts.
    # ticks_per_beat is ticks per quarter note; 1 quarter note = 16 sixty-fourths
    # ticks per sixty-fourth = ticks_per_beat / 16
    # Use ceiling division to quantize early note-offs (common in DAWs/MuseScore)
    # up to the nearest sixty-fourth so durations align with musical grid.
    sixtyfourth_ticks = ticks_per_beat // 16
    # Guard against pathological inputs
    if sixtyfourth_ticks <= 0:
        return 0
    return (ticks + (sixtyfourth_ticks - 1)) // sixtyfourth_ticks


def _midi_note_to_pitch(midi_note: int) -> str:
    name = NOTE_NAMES[midi_note % 12]
    octave = (midi_note // 12) - 1
    return f"{name}{octave}"


def _midi_pitch_value(event: NoteEvent) -> int:
    # Convert pitch string back to MIDI number for sorting high->low
    # Handle multi-char octave numbers
    # Split name (letters + optional #) from octave digits at the end
    pitch = event.pitch
    # Find index where digits start from the end
    idx = len(pitch) - 1
    while idx >= 0 and pitch[idx].isdigit():
        idx -= 1
    name = pitch[: idx + 1]
    octave = int(pitch[idx + 1 :])
    base = NOTE_NAMES.index(name)
    return (octave + 1) * 12 + base


def _event_sort_key(e: Event):
    # Sort by ascending start; ControlEvent before NoteEvent at same start;
    # for controls at same start, alphabetical by (name, value);
    # for notes at same start, higher pitch first.
    if isinstance(e, ControlEvent):
        name = getattr(e, "name", "")
        value = getattr(e, "value", "")
        return (e.start, 0, name, value)
    elif isinstance(e, NoteEvent):
        return (e.start, 1, -_midi_pitch_value(e))
    else:
        return (e.start, 2)


__all__ = ["Event", "NoteEvent", "ControlEvent", "PNote"]


