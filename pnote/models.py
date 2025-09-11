from __future__ import annotations

from typing import List, Union
import io
import os
from typing import BinaryIO
import mido
import re


# Map MIDI note number to pitch name + octave (C4 = MIDI 60)
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


class Event:
    __slots__ = ("start",)

    def __init__(self, start: int):
        self.start = start

    def to_pnote(self) -> str:
        raise NotImplementedError

    @classmethod
    def from_string(cls, s: str) -> "Event":
        """Parse an event from string representation"""
        try:
            return NoteEvent.from_string(s)
        except ValueError as e1:
            try:
                return ControlEvent.from_string(s)
            except ValueError as e2:
                raise ValueError(
                    f"Could not parse event: {s}. "
                    f"NoteEvent error: {e1}, ControlEvent error: {e2}"
                ) from e2


class NoteEvent(Event):
    __slots__ = ("pitch", "dur", "vel")

    def __init__(self, pitch: str, start: int, dur: int, vel: int):
        super().__init__(start)
        self.pitch = pitch
        self.dur = dur
        self.vel = vel

    def to_pnote(self) -> str:
        return f"{self.pitch}:start={self.start}:dur={self.dur}:vel={self.vel}"

    @classmethod
    def from_string(cls, s: str) -> "NoteEvent":
        parts = s.split(":")
        if len(parts) != 4:
            raise ValueError(
                f"NoteEvent requires exactly 4 colon-separated parts, got {len(parts)}"
            )
        return cls._parse_parts(parts)

    @classmethod
    def _parse_parts(cls, parts: List[str]) -> "NoteEvent":
        pitch = parts[0]
        if not pitch:
            raise ValueError("Pitch cannot be empty")

        # Add pitch format validation
        if not re.match(r"^[A-G][#b]?\d+$", pitch):
            raise ValueError(f"Invalid pitch format: {pitch}")

        # Optimize parameter parsing
        params = {}
        for part in parts[1:]:
            if "=" not in part:
                raise ValueError(
                    f"Invalid parameter format '{part}': expected 'key=value'"
                )
            k, v = part.split("=", 1)
            params[k] = v

        # Validate required parameters (efficient set comparison)
        param_keys = set(params.keys())
        # If param_keys is not the expected set, it means some keys are missing and/or extra.
        # Given the fixed number of parts, any "missing" implies "extra" (e.g., misspelled key).
        # We simplify to only report "Unexpected parameters" for clarity.
        if param_keys != {"start", "dur", "vel"}:
            extra = param_keys - {"start", "dur", "vel"}
            raise ValueError(f"Unexpected parameters: {extra}")

        # Convert to integers with validation
        try:
            start = int(params["start"])
            dur = int(params["dur"])
            vel = int(params["vel"])
        except ValueError as e:
            raise ValueError(f"Invalid integer parameter: {e}")

        # Validate ranges
        if start < 0:
            raise ValueError(f"start must be non-negative, got {start}")
        if dur <= 0:
            raise ValueError(f"dur must be positive, got {dur}")
        if not (0 <= vel <= 127):
            raise ValueError(f"vel must be between 0 and 127, got {vel}")

        return NoteEvent(pitch, start, dur, vel)


class ControlEvent(Event):
    __slots__ = ("name", "value")

    def __init__(self, name: str, value: str, start: int):
        super().__init__(start)
        self.name = name
        self.value = value

    def to_pnote(self) -> str:
        return f"{self.name}:{self.value}:start={self.start}"

    @classmethod
    def from_string(cls, s: str) -> "ControlEvent":
        parts = s.split(":")
        if len(parts) != 3:
            raise ValueError(
                f"ControlEvent requires exactly 3 colon-separated parts, got {len(parts)}"
            )
        return cls._parse_parts(parts)

    @classmethod
    def _parse_parts(cls, parts: List[str]) -> "ControlEvent":
        name = parts[0]
        value = parts[1]
        start_part = parts[2]

        if not name:
            raise ValueError("Control name cannot be empty")
        if not value:
            raise ValueError("Control value cannot be empty")

        # Parse start parameter efficiently
        if not start_part.startswith("start="):
            raise ValueError(f"Third part must be 'start=VALUE', got '{start_part}'")

        start_str = start_part[6:]  # Skip 'start='
        if not start_str:
            raise ValueError("Empty start value")

        try:
            start = int(start_str)
        except ValueError as e:
            raise ValueError(f"Invalid start value '{start_str}': {e}")

        if start < 0:
            raise ValueError(f"start must be non-negative, got {start}")

        return ControlEvent(name, value, start)


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
    def from_string(cls, pnote_string: str) -> "PNote":
        """Construct a PNote from a PNote format string.

        Parses a string containing PNote events, one per line:
        - NoteEvent: Pitch:start=START:dur=DUR:vel=VEL
        - ControlEvent: ControlName:VALUE:start=START

        Args:
            pnote_string: The PNote format string to parse

        Returns:
            A new PNote instance with the parsed events

        Raises:
            ValueError: If the string contains invalid event formats
        """
        pnote = cls()

        # Handle empty input efficiently
        if not pnote_string or not pnote_string.strip():
            return pnote

        # Process each line
        for line_num, line in enumerate(pnote_string.strip().splitlines(), 1):
            line = line.strip()
            if not line:  # Skip empty lines
                continue

            try:
                # Parse the line into an event
                # Determine event type by part count and validate
                event: Event = Event.from_string(line)

                pnote.add_event(event)

            except Exception as e:
                raise ValueError(f"Error parsing line {line_num}: '{line}' - {str(e)}")

        return pnote

    @classmethod
    def from_midi(
        cls, source: Union[str, os.PathLike, bytes, bytearray, BinaryIO]
    ) -> "PNote":
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
            raise TypeError(
                "Unsupported source type for from_midi; expected path, bytes, "
                "or file-like object"
            )

        return cls._from_midi_mid(mid)

    @classmethod
    def _from_midi_mid(cls, mid: "mido.MidiFile") -> "PNote":
        """Internal: construct a PNote from an already-created mido.MidiFile."""
        pnote = cls()
        current_tempo = 500000  # default microseconds per beat
        for track in mid.tracks:
            absolute_ticks = 0
            note_on_times: dict[int, list[tuple[int, int]]] = {}
            for msg in track:
                absolute_ticks += msg.time
                if msg.type == "set_tempo":
                    current_tempo = msg.tempo
                    start = _ticks_to_sixtyfourth(
                        absolute_ticks, mid.ticks_per_beat, current_tempo
                    )
                    pnote.add_event(
                        ControlEvent("Tempo", str(mido.tempo2bpm(current_tempo)), start)
                    )
                elif msg.type == "note_on" and msg.velocity > 0:
                    start = _ticks_to_sixtyfourth(
                        absolute_ticks, mid.ticks_per_beat, current_tempo
                    )
                    note_on_times.setdefault(msg.note, []).append(
                        (absolute_ticks, msg.velocity)
                    )
                elif (msg.type == "note_off") or (
                    msg.type == "note_on" and msg.velocity == 0
                ):
                    if msg.note in note_on_times and note_on_times[msg.note]:
                        on_tick, vel = note_on_times[msg.note].pop(0)
                        start = _ticks_to_sixtyfourth(
                            on_tick, mid.ticks_per_beat, current_tempo
                        )
                        end = _ticks_to_sixtyfourth(
                            absolute_ticks, mid.ticks_per_beat, current_tempo
                        )
                        dur = max(1, end - start)
                        pitch = _midi_note_to_pitch(msg.note)
                        pnote.add_event(NoteEvent(pitch, start, dur, vel))
        return pnote


def _ticks_to_sixtyfourth(
    ticks: int, ticks_per_beat: int, tempo_us_per_beat: int
) -> int:
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


def _event_sort_key(e: Event):  # type: ignore[no-untyped-def]
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
