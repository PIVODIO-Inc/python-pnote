import pytest
from pnote import Event


def test_event_init():
    """Test that the Event class initializes correctly."""
    event = Event(100)
    assert event.start == 100


def test_event_to_pnote():
    """Test that the base Event class would raise an error if to_pnote is called."""
    event = Event(100)
    with pytest.raises(NotImplementedError):
        event.to_pnote()
