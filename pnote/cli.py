from __future__ import annotations

import argparse
import logging
import sys
from typing import List, Optional

from pnote import __version__


def build_arg_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for the PNote CLI."""
    parser = argparse.ArgumentParser(
        prog="pnote",
        description="Convert MIDI files to PNote format.",
        epilog="Examples:\n"
               "  pnote input.mid\n"
               "  pnote -i input.mid -o output.pnote\n"
               "  pnote --input song.mid --verbose\n"
               "  pnote --version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "input",
        nargs="?",
        help="MIDI file path (alternative to -i/--input)",
    )
    parser.add_argument(
        "-i", "--input",
        dest="input_flag",
        help="MIDI file path",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"pnote {__version__}",
        help="Show version information",
    )

    return parser


def parse_args(argv: Optional[List[str]]) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # Validate input: must provide either positional or -i/--input
    if not args.input and not args.input_flag:
        parser.error("MIDI file path is required. Use positional argument or -i/--input. Run 'pnote -h' for help.")

    # If both positional and -i are provided, they must match
    if args.input and args.input_flag and args.input != args.input_flag:
        parser.error("Positional input and -i/--input must be the same.")

    # Set the input path
    args.input_path = args.input_flag or args.input

    return args


def validate_input_path(path: str) -> None:
    """Validate the input MIDI path."""
    import os

    # Check if file exists
    if not os.path.exists(path):
        raise FileNotFoundError(f"MIDI file not found: {path}")

    # Check if it's a file (not a directory)
    if not os.path.isfile(path):
        raise ValueError(f"Path is not a file: {path}")

    # Check file extension
    _, ext = os.path.splitext(path)
    if ext.lower() not in ('.mid', '.midi'):
        raise ValueError(f"Invalid file extension '{ext}'. Expected .mid or .midi")

    return None


def convert_midi_to_pnote(source: str) -> str:
    """Convert the given MIDI source to PNote string."""
    from pnote import PNote

    try:
        pnote = PNote.from_midi(source)
        return pnote.to_string()
    except Exception as e:
        raise RuntimeError(f"Failed to convert MIDI file: {e}") from e


def write_output(pnote_text: str, output_path: Optional[str]) -> None:
    """Write PNote text to a file or stdout."""
    if output_path is None:
        # Write to stdout
        print(pnote_text)
    else:
        # Write to file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(pnote_text)
        except Exception as e:
            raise RuntimeError(f"Failed to write output file '{output_path}': {e}") from e


def configure_logging(verbose: bool) -> None:
    """Configure logging based on verbosity."""
    import sys

    # Configure logging
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        stream=sys.stderr
    )

    # Suppress mido warnings unless verbose
    if not verbose:
        logging.getLogger('mido').setLevel(logging.ERROR)


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for the PNote CLI."""
    try:
        args = parse_args(argv)
        configure_logging(args.verbose)

        logging.info(f"Converting MIDI file: {args.input_path}")

        # Validate input
        validate_input_path(args.input_path)
        logging.info("Input file validated successfully")

        # Convert MIDI to PNote
        logging.info("Starting MIDI to PNote conversion...")
        pnote_text = convert_midi_to_pnote(args.input_path)
        logging.info("Conversion completed successfully")

        # Write output
        if args.output:
            logging.info(f"Writing output to file: {args.output}")
        else:
            logging.info("Writing output to stdout")

        write_output(pnote_text, args.output)
        logging.info("Output written successfully")

        return 0

    except SystemExit as e:
        # argparse exits with SystemExit on --help, --version, or errors
        return int(e.code) if isinstance(e.code, int) else 1
    except FileNotFoundError as e:
        logging.error(str(e))
        return 1
    except ValueError as e:
        logging.error(str(e))
        return 1
    except RuntimeError as e:
        logging.error(str(e))
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


