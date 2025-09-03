"""Tests for the PNote CLI functionality."""

import base64
import io
import logging
import os
import sys
import tempfile
from unittest.mock import patch

import pytest

from pnote.cli import (
    build_arg_parser,
    configure_logging,
    convert_midi_to_pnote,
    main,
    parse_args,
    validate_input_path,
    write_output,
)


class TestValidateInputPath:
    """Test input path validation."""

    def test_valid_midi_file(self):
        """Test validation of a valid MIDI file."""
        # Create a temporary .mid file
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp:
            tmp.write(b'dummy midi content')
            tmp_path = tmp.name

        try:
            # Should not raise an exception
            validate_input_path(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_valid_midi_file_uppercase_ext(self):
        """Test validation with uppercase .MIDI extension."""
        with tempfile.NamedTemporaryFile(suffix='.MIDI', delete=False) as tmp:
            tmp.write(b'dummy midi content')
            tmp_path = tmp.name

        try:
            validate_input_path(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_file_not_found(self):
        """Test validation of non-existent file."""
        with pytest.raises(FileNotFoundError, match="MIDI file not found"):
            validate_input_path("/nonexistent/file.mid")

    def test_directory_as_input(self):
        """Test validation when path is a directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            with pytest.raises(ValueError, match="Path is not a file"):
                validate_input_path(tmp_dir)

    def test_invalid_extension(self):
        """Test validation with invalid file extension."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b'text content')
            tmp_path = tmp.name

        try:
            with pytest.raises(ValueError, match="Invalid file extension '.txt'"):
                validate_input_path(tmp_path)
        finally:
            os.unlink(tmp_path)


class TestConvertMidiToPnote:
    """Test MIDI to PNote conversion."""

    @pytest.fixture
    def sample_midi_bytes(self):
        """Return sample MIDI bytes from existing test."""
        b64_midi = "TVRoZAAAAAYAAQABAeBNVHJrAAAAWQD/AwVQaWFubwD/WAQCAhgIAP9ZAgAAAP9RAwehIACweQAAZAAAZQAABgwAZH8AZX8AwAAAsAdkAApAAFsAAF0AAP8hAQAAkDxQg0c8ABk+WoNHPgAB/y8A"
        return base64.b64decode(b64_midi)

    def test_successful_conversion(self, sample_midi_bytes):
        """Test successful conversion of MIDI bytes to PNote string."""
        # Create a temporary MIDI file
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp:
            tmp.write(sample_midi_bytes)
            tmp_path = tmp.name

        try:
            result = convert_midi_to_pnote(tmp_path)

            # Should return a non-empty string
            assert isinstance(result, str)
            assert len(result) > 0

            # Should contain expected PNote format
            assert "Tempo:120.0:start=0" in result
            assert "C4:start=0:dur=16:vel=80" in result
            assert "D4:start=16:dur=16:vel=90" in result
        finally:
            os.unlink(tmp_path)

    def test_conversion_with_file_like_object(self, sample_midi_bytes):
        """Test conversion with file-like object."""
        file_obj = io.BytesIO(sample_midi_bytes)
        result = convert_midi_to_pnote(file_obj)

        assert isinstance(result, str)
        assert len(result) > 0
        assert "Tempo:120.0:start=0" in result

    def test_invalid_midi_file(self):
        """Test conversion with invalid MIDI file."""
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp:
            tmp.write(b'invalid midi content')
            tmp_path = tmp.name

        try:
            with pytest.raises(RuntimeError, match="Failed to convert MIDI file"):
                convert_midi_to_pnote(tmp_path)
        finally:
            os.unlink(tmp_path)


class TestWriteOutput:
    """Test output writing functionality."""

    def test_write_to_stdout(self, capsys):
        """Test writing to stdout."""
        test_content = "Test PNote content\nLine 2"

        write_output(test_content, None)

        captured = capsys.readouterr()
        assert captured.out == test_content + "\n"  # print() adds newline

    def test_write_to_file(self):
        """Test writing to file."""
        test_content = "Test PNote content\nLine 2"

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            write_output(test_content, tmp_path)

            # Read back and verify
            with open(tmp_path, 'r', encoding='utf-8') as f:
                written_content = f.read()

            assert written_content == test_content
        finally:
            os.unlink(tmp_path)

    def test_write_to_file_error(self):
        """Test writing to file with permission error."""
        test_content = "Test content"

        # Try to write to a directory that doesn't allow writing
        with pytest.raises(RuntimeError, match="Failed to write output file"):
            write_output(test_content, "/root/forbidden/file.pnote")


class TestConfigureLogging:
    """Test logging configuration."""

    def test_verbose_logging(self):
        """Test verbose logging configuration."""
        configure_logging(True)

        logger = logging.getLogger('pnote.cli')
        assert logger.level <= logging.INFO

        # Clean up
        logging.getLogger().handlers.clear()

    def test_quiet_logging(self):
        """Test quiet logging configuration."""
        configure_logging(False)

        logger = logging.getLogger('pnote.cli')
        assert logger.level <= logging.WARNING

        # Check that mido logger is suppressed
        mido_logger = logging.getLogger('mido')
        assert mido_logger.level == logging.ERROR

        # Clean up
        logging.getLogger().handlers.clear()


class TestArgumentParsing:
    """Test argument parsing and validation."""

    def test_parse_args_with_positional_input(self):
        """Test parsing with positional input argument."""
        args = parse_args(['test.mid'])
        assert args.input_path == 'test.mid'

    def test_parse_args_with_flag_input(self):
        """Test parsing with -i/--input flag."""
        args = parse_args(['-i', 'test.mid'])
        assert args.input_path == 'test.mid'

    def test_parse_args_with_both_positional_and_flag(self):
        """Test parsing with both positional and flag (should match)."""
        args = parse_args(['test.mid', '-i', 'test.mid'])
        assert args.input_path == 'test.mid'

    def test_parse_args_conflicting_inputs(self):
        """Test parsing with conflicting positional and flag inputs."""
        with pytest.raises(SystemExit):
            parse_args(['file1.mid', '-i', 'file2.mid'])

    def test_parse_args_missing_input(self):
        """Test parsing without any input."""
        with pytest.raises(SystemExit):
            parse_args([])

    def test_parse_args_with_output(self):
        """Test parsing with output file."""
        args = parse_args(['-i', 'input.mid', '-o', 'output.pnote'])
        assert args.input_path == 'input.mid'
        assert args.output == 'output.pnote'

    def test_parse_args_with_verbose(self):
        """Test parsing with verbose flag."""
        args = parse_args(['-i', 'input.mid', '-v'])
        assert args.input_path == 'input.mid'
        assert args.verbose is True


class TestMainFunction:
    """Test the main CLI function."""

    @pytest.fixture
    def sample_midi_bytes(self):
        """Return sample MIDI bytes from existing test."""
        b64_midi = "TVRoZAAAAAYAAQABAeBNVHJrAAAAWQD/AwVQaWFubwD/WAQCAhgIAP9ZAgAAAP9RAwehIACweQAAZAAAZQAABgwAZH8AZX8AwAAAsAdkAApAAFsAAF0AAP8hAQAAkDxQg0c8ABk+WoNHPgAB/y8A"
        return base64.b64decode(b64_midi)

    def test_main_success_with_stdout(self, sample_midi_bytes, capsys):
        """Test successful main execution with stdout output."""
        # Create temporary MIDI file
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp:
            tmp.write(sample_midi_bytes)
            tmp_path = tmp.name

        try:
            # Mock sys.argv for testing
            with patch('sys.argv', ['pnote', tmp_path]):
                exit_code = main()

            assert exit_code == 0

            # Check that output was written to stdout
            captured = capsys.readouterr()
            assert "Tempo:120.0:start=0" in captured.out
            assert "C4:start=0:dur=16:vel=80" in captured.out
        finally:
            os.unlink(tmp_path)

    def test_main_success_with_file_output(self, sample_midi_bytes):
        """Test successful main execution with file output."""
        # Create temporary MIDI file
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp:
            tmp.write(sample_midi_bytes)
            tmp_path = tmp.name

        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix='.pnote', delete=False) as out_tmp:
            out_path = out_tmp.name

        try:
            # Mock sys.argv for testing
            with patch('sys.argv', ['pnote', '-i', tmp_path, '-o', out_path]):
                exit_code = main()

            assert exit_code == 0

            # Check that output file was created and contains expected content
            assert os.path.exists(out_path)
            with open(out_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "Tempo:120.0:start=0" in content
            assert "C4:start=0:dur=16:vel=80" in content
        finally:
            os.unlink(tmp_path)
            if os.path.exists(out_path):
                os.unlink(out_path)

    def test_main_file_not_found(self, capsys, caplog):
        """Test main with non-existent input file."""
        with caplog.at_level(logging.ERROR):
            with patch('sys.argv', ['pnote', '/nonexistent/file.mid']):
                exit_code = main()

        assert exit_code == 1

        # Check that error was logged
        assert any("MIDI file not found" in record.message for record in caplog.records)

    def test_main_invalid_extension(self, capsys, caplog):
        """Test main with invalid file extension."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b'not midi')
            tmp_path = tmp.name

        try:
            with caplog.at_level(logging.ERROR):
                with patch('sys.argv', ['pnote', tmp_path]):
                    exit_code = main()

            assert exit_code == 1

            # Check that error was logged
            assert any("Invalid file extension" in record.message for record in caplog.records)
        finally:
            os.unlink(tmp_path)

    def test_main_verbose_mode(self, sample_midi_bytes, capsys, caplog):
        """Test main with verbose mode enabled."""
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp:
            tmp.write(sample_midi_bytes)
            tmp_path = tmp.name

        try:
            with caplog.at_level(logging.INFO):
                with patch('sys.argv', ['pnote', tmp_path, '-v']):
                    exit_code = main()

            assert exit_code == 0

            # Check that verbose messages were logged
            messages = [record.message for record in caplog.records]
            assert any("Converting MIDI file:" in msg for msg in messages)
            assert any("Input file validated successfully" in msg for msg in messages)
            assert any("Starting MIDI to PNote conversion" in msg for msg in messages)
            assert any("Conversion completed successfully" in msg for msg in messages)
        finally:
            os.unlink(tmp_path)


class TestBuildArgParser:
    """Test argument parser building."""

    def test_help_output(self, capsys):
        """Test that help output is properly formatted."""
        parser = build_arg_parser()

        # This should exit with code 0
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(['--help'])

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "Convert MIDI files to PNote format" in captured.out
        assert "positional arguments:" in captured.out
        assert "options:" in captured.out
        assert "Examples:" in captured.out

    def test_version_output(self, capsys):
        """Test version output."""
        parser = build_arg_parser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(['--version'])

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "pnote" in captured.out
        assert "0.1.0" in captured.out
