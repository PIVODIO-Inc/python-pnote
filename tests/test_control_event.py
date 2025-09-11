from pnote import ControlEvent
import pytest


def test_control_event_init():
    """Test that the ControlEvent class initializes correctly."""
    event = ControlEvent("Sustain", "on", 100)
    assert event.name == "Sustain"
    assert event.value == "on"
    assert event.start == 100


def test_control_event_to_pnote():
    """Test that the ControlEvent class converts to PNote string correctly."""
    event = ControlEvent("Sustain", "off", 100)
    assert event.to_pnote() == "Sustain:off:start=100"


def test_control_event_from_string_valid():
    event_string = "Sustain:on:start=100"
    event = ControlEvent.from_string(event_string)
    assert event.name == "Sustain"
    assert event.value == "on"
    assert event.start == 100


def test_control_event_from_string_invalid_parts_count():
    with pytest.raises(
        ValueError, match="ControlEvent requires exactly 3 colon-separated parts"
    ):
        ControlEvent.from_string("Sustain:on")
    with pytest.raises(
        ValueError, match="ControlEvent requires exactly 3 colon-separated parts"
    ):
        ControlEvent.from_string("Sustain:on:start=100:extra")


def test_control_event_from_string_empty_name():
    with pytest.raises(ValueError, match="Control name cannot be empty"):
        ControlEvent.from_string(":on:start=100")


def test_control_event_from_string_empty_value():
    with pytest.raises(ValueError, match="Control value cannot be empty"):
        ControlEvent.from_string("Sustain::start=100")


def test_control_event_from_string_invalid_start_part_format():
    with pytest.raises(
        ValueError, match="Third part must be 'start=VALUE', got 'start-100'"
    ):
        ControlEvent.from_string("Sustain:on:start-100")


def test_control_event_from_string_empty_start_value():
    with pytest.raises(ValueError, match="Empty start value"):
        ControlEvent.from_string("Sustain:on:start=")


def test_control_event_from_string_invalid_start_value():
    with pytest.raises(
        ValueError,
        match="Invalid start value 'abc': invalid literal for int\(\) with base 10: 'abc'",
    ):
        ControlEvent.from_string("Sustain:on:start=abc")


def test_control_event_from_string_negative_start_value():
    with pytest.raises(ValueError, match="start must be non-negative, got -1"):
        ControlEvent.from_string("Sustain:on:start=-1")
