# PNote LLM MIDI Notation System Specification


This specification defines a custom textual representation of MIDI data optimized for LLM consumption.  
The format is designed to be **deterministic, compact, and faithful** to MIDI semantics.


## Formal Grammar 

```
File           = { Event } ;

Event          = NoteEvent | ControlEvent ;

NoteEvent      = Pitch ":" "start=" Int ":" "dur=" Int ":" "vel=" Int ;

ControlEvent   = ControlName ":" ControlValue ":" "start=" Int ;

Pitch          = NoteName [Accidental] Octave ;

NoteName       = "C" | "D" | "E" | "F" | "G" | "A" | "B" ;

Accidental     = "#" | "b" ;

Octave         = Digit {Digit} ;   (* typically 0–9 *)

Int            = Digit {Digit} ;

ControlName    = "Sustain" | "SoftPedal" | "Sostenuto" | "Tempo" | "Instr" ;

ControlValue   = "on" | "off" | Int ;

Digit          = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;
```

Sorting rule:
- Events are sorted by ascending start.
- If multiple events share the same start, ControlEvents come before NoteEvents.
- ControlEvents at the same start are sorted alphabetically by name, then value.
- NoteEvents at the same start are sorted by pitch, high → low.


## Human-readable description


This is a performance notation format designed to capture how a piece was
actually played (from MIDI), not how it’s traditionally written in sheet music.

- Each line represents one event (note or control).

- Notes are written as:
  Pitch:start=START:dur=DUR:vel=VEL

  where:
  * Pitch = note name + optional sharp (#) or flat (b) + octave number
            Example: C4, F#3, Bb5
  * start = the start time in sixty-fourth notes from the beginning
            Example: start=0 means song start
  * dur   = note duration in sixty-fourth notes
            Example: dur=16 means a quarter note
  * vel   = how strongly the note was played (0–127, MIDI velocity)

- Controls (pedals, tempo, etc.) are written as:
  ControlName:VALUE:start=START

Examples:

Notes:

  - `C4:start=0:dur=16:vel=80`    → Middle C, quarter note, velocity 80
  - `F#3:start=32:dur=8:vel=60`   → F# starting at beat 32, eighth note, softer touch
  - `A5:start=48:dur=4:vel=127`   → High A, thirty-second note, maximum velocity

Controls:

  - `Sustain:on:start=64`    → sustain pedal pressed at beat 64
  - `Sustain:off:start=80`   → sustain pedal released at beat 80
  - `Tempo:120:start=0`      → tempo set to 120 BPM at the beginning

- Events are listed in chronological order (by start time).
  * If multiple notes occur at the same time, they are ordered
    highest pitch first, downwards.
  * This way chords always appear grouped consistently.

Example chord (C major triad at beat 0):
```
  E4:start=0:dur=16:vel=85
  C4:start=0:dur=16:vel=80
  G3:start=0:dur=16:vel=78
```