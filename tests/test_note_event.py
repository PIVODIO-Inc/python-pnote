from pnote import NoteEvent


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
