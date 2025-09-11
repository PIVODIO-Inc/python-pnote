from pnote import NoteEvent
import pytest


def test_note_event_init():
    """Test that the NoteEvent class initializes correctly."""
    event = NoteEvent("C4", 100, 101, 102)
    assert event.pitch == "C4"
    assert event.start == 100
    assert event.dur == 101
    assert event.vel == 102


def test_note_event_to_pnote():
    """Test that the NoteEvent class converts to PNote string correctly."""
    event = NoteEvent("C4", 100, 101, 102)
    assert event.to_pnote() == "C4:start=100:dur=101:vel=102"


def test_note_event_from_string_valid():
    event_string = "C4:start=100:dur=101:vel=102"
    event = NoteEvent.from_string(event_string)
    assert event.pitch == "C4"
    assert event.start == 100
    assert event.dur == 101
    assert event.vel == 102


def test_note_event_from_string_invalid_parts_count():
    with pytest.raises(
        ValueError, match="NoteEvent requires exactly 4 colon-separated parts"
    ):
        NoteEvent.from_string("C4:start=100:dur=101")
    with pytest.raises(
        ValueError, match="NoteEvent requires exactly 4 colon-separated parts"
    ):
        NoteEvent.from_string("C4:start=100:dur=101:vel=102:extra")


def test_note_event_from_string_empty_pitch():
    with pytest.raises(ValueError, match="Pitch cannot be empty"):
        NoteEvent.from_string(":start=100:dur=101:vel=102")


def test_note_event_from_string_invalid_param_format():
    with pytest.raises(
        ValueError, match="Invalid parameter format 'start-100': expected 'key=value'"
    ):
        NoteEvent.from_string("C4:start-100:dur=101:vel=102")


def test_note_event_from_string_missing_params():
    with pytest.raises(
        ValueError, match="NoteEvent requires exactly 4 colon-separated parts, got 3"
    ):
        NoteEvent.from_string("C4:start=100:dur=101")


def test_note_event_from_string_unexpected_params():
    with pytest.raises(
        ValueError, match="NoteEvent requires exactly 4 colon-separated parts, got 5"
    ):
        NoteEvent.from_string("C4:start=100:dur=101:vel=102:foo=bar")


def test_note_event_from_string_invalid_integer_param():
    with pytest.raises(
        ValueError, match="invalid literal for int\(\) with base 10: 'abc'"
    ):
        NoteEvent.from_string("C4:start=abc:dur=101:vel=102")


def test_note_event_from_string_invalid_start_range():
    with pytest.raises(ValueError, match="start must be non-negative, got -1"):
        NoteEvent.from_string("C4:start=-1:dur=101:vel=102")


def test_note_event_from_string_invalid_dur_range():
    with pytest.raises(ValueError, match="dur must be positive, got 0"):
        NoteEvent.from_string("C4:start=100:dur=0:vel=102")


def test_note_event_from_string_invalid_vel_range():
    with pytest.raises(ValueError, match="vel must be between 0 and 127, got 200"):
        NoteEvent.from_string("C4:start=100:dur=101:vel=200")
    with pytest.raises(ValueError, match="vel must be between 0 and 127, got -1"):
        NoteEvent.from_string("C4:start=100:dur=101:vel=-1")


def test_note_event_from_string_invalid_pitch_format():
    with pytest.raises(ValueError, match="Invalid pitch format: C"):  # Missing octave
        NoteEvent.from_string("C:start=100:dur=101:vel=102")
    with pytest.raises(
        ValueError, match="Invalid pitch format: C4#"
    ):  # Invalid sharp position
        NoteEvent.from_string("C4#:start=100:dur=101:vel=102")


def test_note_event_from_string_incorrect_param_names():
    # Test case where 'start' is misspelled as 'strt', resulting in 'strt' being
    # an unexpected parameter.
    with pytest.raises(ValueError, match="Unexpected parameters: {'strt'}"):
        NoteEvent.from_string("C4:strt=100:dur=101:vel=102")
