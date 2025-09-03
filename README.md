# PNote: LLM MIDI Notation System

A Python library and CLI tool for converting MIDI files to PNote format, a textual representation of MIDI data optimized for Large Language Model (LLM) consumption.

## 🎵 What is PNote?

PNote is a custom textual representation of MIDI data designed to be:
- **Deterministic**: Same input always produces same output
- **Compact**: Efficient text representation
- **Faithful**: Preserves all MIDI semantics
- **LLM-friendly**: Easy for language models to understand and generate

## 📋 Features

- ✅ Convert MIDI files to PNote text format
- ✅ Command-line interface with rich options
- ✅ Python API for programmatic use
- ✅ Comprehensive test suite (95% coverage)
- ✅ Type-safe with mypy
- ✅ Modern Python (3.12+) with full type hints

## 🚀 Quick Start

### Installation

```bash
# Using uv (recommended)
uv pip install pnote

# Or using pip
pip install pnote

# For development with all dependencies
uv sync --group dev
```

### Basic Usage

```bash
# Convert a MIDI file to PNote format
pnote input.mid

# Save output to a file
pnote input.mid -o output.pnote

# Use verbose mode to see progress
pnote input.mid -v

# Get help
pnote --help
```

### Python API

```python
from pnote import PNote

# Load from MIDI file
pnote = PNote.from_midi("song.mid")

# Convert to PNote string
pnote_text = pnote.to_string()

# Load from bytes
with open("song.mid", "rb") as f:
    midi_bytes = f.read()
pnote = PNote.from_midi(midi_bytes)
```

## 📖 PNote Format Example

```
Tempo:120:start=0
E4:start=0:dur=16:vel=85
C4:start=0:dur=16:vel=80
G3:start=0:dur=16:vel=78
F#3:start=32:dur=8:vel=60
Sustain:on:start=64
Sustain:off:start=80
```

Each line represents one event:
- **Notes**: `Pitch:start=START:dur=DUR:vel=VEL`
- **Controls**: `ControlName:VALUE:start=START`

Events are sorted chronologically, with controls before notes at the same time, and notes ordered by pitch (high to low).

## 🛠️ Development

### Setup

```bash
# Clone the repository
git clone https://github.com/PIVODIO-Inc/python-pnote.git
cd python-pnote

# Install development dependencies
uv sync --group dev
```

### Code Quality

```bash
# Format code
make format

# Lint and type check
make quality

# Run tests
make test

# Run tests with coverage
make test-cov

# Full development workflow
make dev
```

### Available Make Targets

- `make format` - Format code with ruff
- `make lint` - Check code formatting and linting
- `make type-check` - Run type checking with mypy
- `make quality` - Run all code quality checks
- `make test` - Run tests with pytest
- `make test-cov` - Run tests with coverage report
- `make clean` - Clean up generated files
- `make dev` - Full development workflow

## 📚 Documentation

### Command Line Options

```
Usage: pnote [OPTIONS] [INPUT]

Convert MIDI files to PNote format.

Options:
  -i, --input PATH   MIDI file path
  -o, --output PATH  Output file path (default: stdout)
  -v, --verbose      Enable verbose output
  --version          Show version information
  --help             Show this message and exit

Arguments:
  INPUT  MIDI file path (alternative to -i/--input)
```

### Python API

#### PNote Class

```python
class PNote:
    def __init__(self, events: List[Event] | None = None)
    def add_event(self, event: Event) -> None
    def to_string(self) -> str

    @classmethod
    def from_midi(cls, source: Union[str, os.PathLike, bytes, bytearray, BinaryIO]) -> "PNote"
```

#### Event Classes

```python
class NoteEvent(Event):
    def __init__(self, pitch: str, start: int, dur: int, vel: int)

class ControlEvent(Event):
    def __init__(self, name: str, value: str, start: int)
```

## 🔬 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pnote --cov-report=html

# Run specific test file
pytest tests/test_cli.py

# Run tests matching pattern
pytest -k "midi"
```

## 📄 Specification

For detailed information about the PNote format, see [specification.md](specification.md).