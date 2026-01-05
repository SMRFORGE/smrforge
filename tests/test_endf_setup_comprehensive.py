"""
Comprehensive tests for core/endf_setup.py to improve coverage to 75-80%.

Tests cover:
- Print utility functions
- Setup wizard functions
- Interactive prompts (mocked)
- Validation functions
- Error handling
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys


class TestEndfSetupPrintFunctions:
    """Test print utility functions."""

    def test_print_step(self, capsys):
        """Test print_step function."""
        try:
            from smrforge.core.endf_setup import print_step
            
            print_step(1, "Test Step")
            captured = capsys.readouterr()
            assert "STEP 1: Test Step" in captured.out
            assert "=" in captured.out
        except ImportError:
            pytest.skip("endf_setup module not available")

    def test_print_success(self, capsys):
        """Test print_success function."""
        try:
            from smrforge.core.endf_setup import print_success
            
            print_success("Test success message")
            captured = capsys.readouterr()
            assert "✓" in captured.out
            assert "Test success message" in captured.out
        except ImportError:
            pytest.skip("endf_setup module not available")

    def test_print_error(self, capsys):
        """Test print_error function."""
        try:
            from smrforge.core.endf_setup import print_error
            
            print_error("Test error message")
            captured = capsys.readouterr()
            assert "✗" in captured.out or "Test error message" in captured.out
        except ImportError:
            pytest.skip("endf_setup module not available")

    def test_print_info(self, capsys):
        """Test print_info function."""
        try:
            from smrforge.core.endf_setup import print_info
            
            print_info("Test info message")
            captured = capsys.readouterr()
            assert "ℹ" in captured.out or "Test info message" in captured.out
        except ImportError:
            pytest.skip("endf_setup module not available")

    def test_print_warning(self, capsys):
        """Test print_warning function."""
        try:
            from smrforge.core.endf_setup import print_warning
            
            print_warning("Test warning message")
            captured = capsys.readouterr()
            assert "⚠" in captured.out or "Test warning message" in captured.out
        except ImportError:
            pytest.skip("endf_setup module not available")


class TestEndfSetupWizard:
    """Test setup wizard functions."""

    def test_setup_endf_data_interactive_cancel(self):
        """Test interactive setup wizard with cancellation."""
        try:
            from smrforge.core.endf_setup import setup_endf_data_interactive
            
            # Mock user cancellation
            with patch('builtins.input', return_value="q"):
                with patch('builtins.print'):  # Suppress output
                    result = setup_endf_data_interactive()
                    assert result is None
        except ImportError:
            pytest.skip("endf_setup module not available")

    def test_setup_endf_data_interactive_option_2(self):
        """Test interactive setup wizard choosing option 2 (download instructions)."""
        try:
            from smrforge.core.endf_setup import setup_endf_data_interactive
            
            # Mock user choosing option 2, then pressing Enter, then 'n' to exit
            with patch('builtins.input', side_effect=["2", "", "n"]):
                with patch('builtins.print'):  # Suppress output
                    result = setup_endf_data_interactive()
                    # Should return None when user exits
                    assert result is None
        except ImportError:
            pytest.skip("endf_setup module not available")

    def test_setup_existing_files_cancel(self):
        """Test setup_existing_files with cancellation."""
        try:
            from smrforge.core.endf_setup import setup_existing_files
            
            # Mock user cancellation
            with patch('builtins.input', return_value="q"):
                with patch('builtins.print'):  # Suppress output
                    result = setup_existing_files()
                    assert result is None
        except ImportError:
            pytest.skip("endf_setup module not available")

    def test_setup_existing_files_invalid_path(self):
        """Test setup_existing_files with invalid path."""
        try:
            from smrforge.core.endf_setup import setup_existing_files
            
            # Mock user entering invalid path, then canceling
            with patch('builtins.input', side_effect=["/nonexistent/path", "q"]):
                with patch('builtins.print'):  # Suppress output
                    with patch('pathlib.Path.exists', return_value=False):
                        result = setup_existing_files()
                        # Should eventually return None after cancellation
                        assert result is None
        except ImportError:
            pytest.skip("endf_setup module not available")

    def test_setup_download_instructions(self):
        """Test setup_download_instructions."""
        try:
            from smrforge.core.endf_setup import setup_download_instructions
            
            # Mock user input - choose 'n' to exit
            with patch('builtins.input', return_value="n"):
                with patch('builtins.print'):  # Suppress output
                    result = setup_download_instructions()
                    assert result is None
        except ImportError:
            pytest.skip("endf_setup module not available")


class TestEndfSetupValidation:
    """Test validation functions."""

    def test_validate_endf_setup_nonexistent_dir(self):
        """Test validate_endf_setup with nonexistent directory."""
        try:
            from smrforge.core.endf_setup import validate_endf_setup
            
            nonexistent_path = Path("/nonexistent/directory/path")
            is_valid, results = validate_endf_setup(nonexistent_path)
            
            assert is_valid is False
            assert isinstance(results, dict)
            assert "directory_exists" in results
            assert results["directory_exists"] is False
        except ImportError:
            pytest.skip("endf_setup module not available")

    def test_validate_endf_setup_empty_dir(self, tmp_path):
        """Test validate_endf_setup with empty directory."""
        try:
            from smrforge.core.endf_setup import validate_endf_setup
            
            is_valid, results = validate_endf_setup(tmp_path)
            
            assert isinstance(is_valid, bool)
            assert isinstance(results, dict)
            assert "directory_exists" in results
            assert "valid_files" in results
        except ImportError:
            pytest.skip("endf_setup module not available")

    def test_validate_endf_setup_default(self):
        """Test validate_endf_setup with default (None) directory."""
        try:
            from smrforge.core.endf_setup import validate_endf_setup
            
            is_valid, results = validate_endf_setup(None)
            
            assert isinstance(is_valid, bool)
            assert isinstance(results, dict)
        except ImportError:
            pytest.skip("endf_setup module not available")

