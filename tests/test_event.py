import pytest
from pnote import Event
from pnote import NoteEvent, ControlEvent


def test_event_init():
    """Test that the Event class initializes correctly."""
    event = Event(100)
    assert event.start == 100


def test_event_to_pnote():
    """Test that the base Event class would raise an error if to_pnote is called."""
    event = Event(100)
    with pytest.raises(NotImplementedError):
        event.to_pnote()


def test_event_from_string_note_event():
    event_string = "C4:start=0:dur=16:vel=80"
    event = Event.from_string(event_string)
    assert isinstance(event, NoteEvent)
    assert event.pitch == "C4"
    assert event.start == 0
    assert event.dur == 16
    assert event.vel == 80


def test_event_from_string_control_event():
    event_string = "Sustain:on:start=64"
    event = Event.from_string(event_string)
    assert isinstance(event, ControlEvent)
    assert event.name == "Sustain"
    assert event.value == "on"
    assert event.start == 64


def test_event_from_string_invalid_event():
    with pytest.raises(ValueError, match="Could not parse event"):
        Event.from_string("Invalid:event:string")
    with pytest.raises(ValueError, match="Could not parse event"):
        Event.from_string("C4:start=invalid:dur=16:vel=80")
    with pytest.raises(ValueError, match="Could not parse event"):
        Event.from_string("Sustain:on:start=invalid")
