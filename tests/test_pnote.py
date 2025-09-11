import pytest
import base64
from pnote import PNote, NoteEvent, ControlEvent, Event


def test_pnote_init():
    """Test that the PNote class initializes correctly."""
    # Empty PNote
    pnote = PNote()
    assert pnote.events == []

    # PNote with events
    events = [
        NoteEvent("C4", 100, 101, 102),
        NoteEvent("D4", 102, 103, 104),
        ControlEvent("Sustain", "on", 104),
    ]
    pnote = PNote(events)
    assert len(pnote.events) == 3

    # Events are sorted, first by start time, then controls before notes
    events_not_sorted = [
        NoteEvent("D4", 102, 103, 104),
        NoteEvent("C4", 100, 101, 102),
        ControlEvent("Sustain", "on", 104),
    ]
    pnote = PNote(events_not_sorted)
    assert len(pnote.events) == 3
    assert isinstance(pnote.events[0], NoteEvent) and pnote.events[0].pitch == "C4"
    assert isinstance(pnote.events[1], NoteEvent) and pnote.events[1].pitch == "D4"
    assert (
        isinstance(pnote.events[2], ControlEvent) and pnote.events[2].name == "Sustain"
    )


def test_pnote_add_event():
    """Test that the PNote class adds events correctly."""
    pnote = PNote()
    pnote.add_event(NoteEvent("C4", 100, 101, 102))
    assert len(pnote.events) == 1
    assert isinstance(pnote.events[0], NoteEvent) and pnote.events[0].pitch == "C4"

    # adding a note event with the same start time should insert it at the correct position  # noqa: E501
    pnote.add_event(NoteEvent("D4", 100, 101, 102))
    assert len(pnote.events) == 2
    assert isinstance(pnote.events[0], NoteEvent) and pnote.events[0].pitch == "D4"
    assert isinstance(pnote.events[1], NoteEvent) and pnote.events[1].pitch == "C4"

    # adding a control event with the same start time should appear before notes at that start  # noqa: E501
    pnote.add_event(ControlEvent("Sustain", "on", 100))
    assert len(pnote.events) == 3
    assert (
        isinstance(pnote.events[0], ControlEvent) and pnote.events[0].name == "Sustain"
    )
    assert isinstance(pnote.events[1], NoteEvent) and pnote.events[1].pitch == "D4"
    assert isinstance(pnote.events[2], NoteEvent) and pnote.events[2].pitch == "C4"

    # adding a note event with an earlier start time should insert it at the correct position  # noqa: E501
    pnote.add_event(NoteEvent("B3", 99, 100, 101))
    assert len(pnote.events) == 4
    assert isinstance(pnote.events[0], NoteEvent) and pnote.events[0].pitch == "B3"
    assert (
        isinstance(pnote.events[1], ControlEvent) and pnote.events[1].name == "Sustain"
    )
    assert isinstance(pnote.events[2], NoteEvent) and pnote.events[2].pitch == "D4"
    assert isinstance(pnote.events[3], NoteEvent) and pnote.events[3].pitch == "C4"

    # adding an unknown Event subclass at same start should sort after controls and notes  # noqa: E501
    class CustomEvent(Event):
        def __init__(self, start: int):
            super().__init__(start)

        def to_pnote(self) -> str:
            return f"Custom:start={self.start}"

    pnote.add_event(CustomEvent(100))
    assert len(pnote.events) == 5
    assert isinstance(pnote.events[4], CustomEvent)


def test_pnote_to_string():
    """Test that the PNote class converts to string correctly."""
    pnote = PNote(
        [
            NoteEvent("C4", 100, 101, 102),
            NoteEvent("D4", 102, 103, 104),
            ControlEvent("Sustain", "on", 100),
        ]
    )
    assert (
        pnote.to_string()
        == "Sustain:on:start=100\nC4:start=100:dur=101:vel=102\nD4:start=102:dur=103:vel=104"  # noqa: E501
    )


def test_pnote_from_midi():
    """Test that the PNote class converts from MIDI correctly."""
    # Create a simple MIDI in MuseScore with EXACTLY these events:
    # - Tempo: 120 BPM at song start (explicit tempo marking at time 0)
    # - Note: C4 starting at 0, duration = one quarter note, velocity = 80
    # - Note: D4 starting at one quarter note, duration = one quarter note, velocity = 90  # noqa: E501
    # Notes:
    # - Quarter note corresponds to 16 sixty-fourths in this notation.
    # - Ensure velocities are set precisely (80 and 90) in MuseScore's note properties.
    # - Keep the score minimal (no extra notes/controllers) so the test remains deterministic.  # noqa: E501
    b64_midi = "TVRoZAAAAAYAAQABAeBNVHJrAAAAWQD/AwVQaWFubwD/WAQCAhgIAP9ZAgAAAP9RAwehIACweQAAZAAAZQAABgwAZH8AZX8AwAAAsAdkAApAAFsAAF0AAP8hAQAAkDxQg0c8ABk+WoNHPgAB/y8A"  # noqa: E501

    midi_bytes = base64.b64decode(b64_midi)
    pnote = PNote.from_midi(midi_bytes)

    # Expected order per spec: events sorted by start asc; at same start, controls before notes.  # noqa: E501
    # So with tempo and C4 at start=0, Tempo appears before C4; D4 at start=16 is last.
    expected = (
        "Tempo:120.0:start=0\nC4:start=0:dur=16:vel=80\nD4:start=16:dur=16:vel=90"
    )

    assert pnote.to_string() == expected


def test_pnote_from_midi_file_like():
    """Cover from_midi with a file-like object (BytesIO)."""
    import io

    b64_midi = "TVRoZAAAAAYAAQABAeBNVHJrAAAAWQD/AwVQaWFubwD/WAQCAhgIAP9ZAgAAAP9RAwehIACweQAAZAAAZQAABgwAZH8AZX8AwAAAsAdkAApAAFsAAF0AAP8hAQAAkDxQg0c8ABk+WoNHPgAB/y8A"  # noqa: E501
    midi_bytes = base64.b64decode(b64_midi)
    f = io.BytesIO(midi_bytes)
    pnote = PNote.from_midi(f)

    expected = (
        "Tempo:120.0:start=0\nC4:start=0:dur=16:vel=80\nD4:start=16:dur=16:vel=90"
    )
    assert pnote.to_string() == expected


def test_pnote_from_midi_pathlike(tmp_path):
    """Cover from_midi with a path-like source (Path object)."""
    b64_midi = "TVRoZAAAAAYAAQABAeBNVHJrAAAAWQD/AwVQaWFubwD/WAQCAhgIAP9ZAgAAAP9RAwehIACweQAAZAAAZQAABgwAZH8AZX8AwAAAsAdkAApAAFsAAF0AAP8hAQAAkDxQg0c8ABk+WoNHPgAB/y8A"  # noqa: E501
    midi_bytes = base64.b64decode(b64_midi)
    midi_path = tmp_path / "example.mid"
    midi_path.write_bytes(midi_bytes)

    pnote = PNote.from_midi(midi_path)

    expected = (
        "Tempo:120.0:start=0\nC4:start=0:dur=16:vel=80\nD4:start=16:dur=16:vel=90"
    )
    assert pnote.to_string() == expected


def test_pnote_from_midi_invalid_type():
    """Passing an unsupported source type should raise TypeError."""
    with pytest.raises(TypeError):
        PNote.from_midi(123)  # type: ignore[arg-type]  # not bytes, not file-like, not path-like


def test_pnote_from_string_empty():
    pnote = PNote.from_string("")
    assert len(pnote.events) == 0


def test_pnote_from_string_whitespace_only():
    pnote = PNote.from_string("  \n\t  ")
    assert len(pnote.events) == 0


def test_pnote_from_string_single_note_event():
    s = "C4:start=0:dur=16:vel=80"
    pnote = PNote.from_string(s)
    assert len(pnote.events) == 1
    event = pnote.events[0]
    assert isinstance(event, NoteEvent)
    assert event.pitch == "C4"
    assert event.start == 0


def test_pnote_from_string_single_control_event():
    s = "Tempo:120:start=0"
    pnote = PNote.from_string(s)
    assert len(pnote.events) == 1
    event = pnote.events[0]
    assert isinstance(event, ControlEvent)
    assert event.name == "Tempo"
    assert event.value == "120"


def test_pnote_from_string_multiple_events_sorted():
    s = "Tempo:120:start=0\n" "C4:start=0:dur=16:vel=80\n" "D4:start=16:dur=16:vel=90"
    pnote = PNote.from_string(s)
    assert len(pnote.events) == 3
    assert isinstance(pnote.events[0], ControlEvent)
    assert isinstance(pnote.events[1], NoteEvent)
    assert pnote.events[1].pitch == "C4"
    assert isinstance(pnote.events[2], NoteEvent)
    assert pnote.events[2].pitch == "D4"


def test_pnote_from_string_multiple_events_unsorted():
    s = "D4:start=16:dur=16:vel=90\n" "C4:start=0:dur=16:vel=80\n" "Tempo:120:start=0"
    pnote = PNote.from_string(s)
    assert len(pnote.events) == 3
    assert isinstance(pnote.events[0], ControlEvent)
    assert isinstance(pnote.events[1], NoteEvent)
    assert pnote.events[1].pitch == "C4"
    assert isinstance(pnote.events[2], NoteEvent)
    assert pnote.events[2].pitch == "D4"


def test_pnote_from_string_invalid_line():
    s = "C4:start=0:dur=16:vel=80\n" "Invalid:line:format\n" "D4:start=16:dur=16:vel=90"
    with pytest.raises(ValueError, match="Error parsing line 2: 'Invalid:line:format'"):
        PNote.from_string(s)


def test_pnote_from_string_invalid_pitch_format_error():
    s = "C:start=0:dur=16:vel=80"  # Invalid pitch
    with pytest.raises(
        ValueError,
        match="Error parsing line 1: 'C:start=0:dur=16:vel=80' - Could not parse event: C:start=0:dur=16:vel=80. NoteEvent error: Invalid pitch format: C",
    ):
        PNote.from_string(s)


def test_pnote_from_string_with_empty_lines():
    s = "Tempo:120:start=0\n" "\n" "   \n" "C4:start=0:dur=16:vel=80"
    pnote = PNote.from_string(s)
    assert len(pnote.events) == 2
    assert isinstance(pnote.events[0], ControlEvent)
    assert pnote.events[0].name == "Tempo"
    assert isinstance(pnote.events[1], NoteEvent)
    assert pnote.events[1].pitch == "C4"


def test_ticks_to_sixtyfourth_uses_ceiling_for_duration():
    """A note slightly shorter than an exact 1/64 should round up to that 1/64.

    With ticks_per_beat=480, one sixty-fourth is 30 ticks. We create a note of
    480 - 27 = 453 ticks (i.e., 15.1 sixty-fourths). Ceiling should round to 16.
    """
    import io
    import mido

    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    track.append(mido.Message("note_on", note=60, velocity=80, time=0))
    track.append(mido.Message("note_off", note=60, velocity=0, time=453))

    buf = io.BytesIO()
    mid.save(file=buf)
    midi_bytes = buf.getvalue()

    p = PNote.from_midi(midi_bytes)
    assert p.to_string() == "C4:start=0:dur=16:vel=80"


def test_ticks_to_sixtyfourth_guard_zero_tpb():
    """Guard: when ticks_per_beat // 16 == 0, function returns 0."""
    from pnote.models import _ticks_to_sixtyfourth

    assert _ticks_to_sixtyfourth(100, 0, 500000) == 0
    assert _ticks_to_sixtyfourth(0, 0, 500000) == 0
