from pnote import ControlEvent


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
