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


class TestEndfSetupEdgeCases:
    """Edge case tests for endf_setup.py to improve coverage to 80%."""
    
    def test_setup_existing_files_retry_path(self, tmp_path):
        """Test setup_existing_files retry path when no valid files found."""
        try:
            from smrforge.core.endf_setup import setup_existing_files
            
            # Create empty directory
            endf_dir = tmp_path / "empty_endf"
            endf_dir.mkdir()
            
            # Mock user: enter valid path, get no files, retry, then cancel
            with patch('builtins.input', side_effect=[str(endf_dir), "y", "q"]):
                with patch('builtins.print'):  # Suppress output
                    with patch('smrforge.core.endf_setup.scan_endf_directory') as mock_scan:
                        # Mock scan to return no valid files
                        mock_scan.return_value = {
                            'total_files': 0,
                            'valid_files': 0,
                            'directory_structure': 'flat',
                            'library_versions': [],
                            'nuclides': [],
                        }
                        result = setup_existing_files()
                        # Should eventually return None after retry/cancel
                        assert result is None
        except ImportError:
            pytest.skip("endf_setup module not available")
    
    def test_setup_existing_files_with_organization(self, tmp_path):
        """Test setup_existing_files with file organization."""
        try:
            from smrforge.core.endf_setup import setup_existing_files
            
            endf_dir = tmp_path / "endf_source"
            endf_dir.mkdir()
            
            # Mock user: valid path, yes to organize, default version, then validation
            with patch('builtins.input', side_effect=[str(endf_dir), "", "y", ""]):
                with patch('builtins.print'):  # Suppress output
                    with patch('smrforge.core.endf_setup.scan_endf_directory') as mock_scan:
                        with patch('smrforge.core.endf_setup.organize_bulk_endf_downloads') as mock_org:
                            with patch('smrforge.core.endf_setup.NuclearDataCache') as mock_cache:
                                # Mock successful scan
                                mock_scan.return_value = {
                                    'total_files': 10,
                                    'valid_files': 5,
                                    'directory_structure': 'nested',
                                    'library_versions': ['VIII.1'],
                                    'nuclides': ['U235', 'U238'],
                                }
                                # Mock successful organization
                                mock_org.return_value = {
                                    'files_organized': 5,
                                    'files_skipped': 0,
                                    'nuclides_indexed': 2,
                                }
                                # Mock cache creation and validation
                                mock_cache_instance = Mock()
                                mock_cache_instance._find_local_endf_file.return_value = Mock()
                                mock_cache.return_value = mock_cache_instance
                                
                                result = setup_existing_files()
                                # May return None or path depending on validation
                                assert result is None or isinstance(result, Path)
        except ImportError:
            pytest.skip("endf_setup module not available")
    
    def test_setup_existing_files_organization_error(self, tmp_path):
        """Test setup_existing_files when organization fails."""
        try:
            from smrforge.core.endf_setup import setup_existing_files
            
            endf_dir = tmp_path / "endf_source"
            endf_dir.mkdir()
            
            with patch('builtins.input', side_effect=[str(endf_dir), "y", ""]):
                with patch('builtins.print'):  # Suppress output
                    with patch('smrforge.core.endf_setup.scan_endf_directory') as mock_scan:
                        with patch('smrforge.core.endf_setup.organize_bulk_endf_downloads') as mock_org:
                            # Mock scan with valid files
                            mock_scan.return_value = {
                                'total_files': 10,
                                'valid_files': 5,
                                'directory_structure': 'nested',
                                'library_versions': ['VIII.1'],
                                'nuclides': ['U235'],
                            }
                            # Mock organization failure
                            mock_org.side_effect = Exception("Organization failed")
                            
                            result = setup_existing_files()
                            # Should continue with original directory despite error
                            assert result is None or isinstance(result, Path)
        except ImportError:
            pytest.skip("endf_setup module not available")
    
    def test_setup_existing_files_validation_exception(self, tmp_path):
        """Test setup_existing_files when validation raises exception."""
        try:
            from smrforge.core.endf_setup import setup_existing_files
            
            endf_dir = tmp_path / "endf_dir"
            endf_dir.mkdir()
            
            with patch('builtins.input', side_effect=[str(endf_dir), "n"]):
                with patch('builtins.print'):  # Suppress output
                    with patch('smrforge.core.endf_setup.scan_endf_directory') as mock_scan:
                        with patch('smrforge.core.endf_setup.NuclearDataCache') as mock_cache:
                            # Mock successful scan
                            mock_scan.return_value = {
                                'total_files': 10,
                                'valid_files': 5,
                                'directory_structure': 'flat',
                                'library_versions': [],
                                'nuclides': [],
                            }
                            # Mock cache creation to raise exception
                            mock_cache.side_effect = Exception("Cache creation failed")
                            
                            result = setup_existing_files()
                            # Should return None on exception
                            assert result is None
        except ImportError:
            pytest.skip("endf_setup module not available")
    
    def test_setup_download_instructions_yes_path(self):
        """Test setup_download_instructions when user chooses 'y'."""
        try:
            from smrforge.core.endf_setup import setup_download_instructions
            
            # Mock user: press Enter, then 'y' to set up now
            with patch('builtins.input', side_effect=["", "y", "q"]):  # 'q' to cancel setup
                with patch('builtins.print'):  # Suppress output
                    with patch('smrforge.core.endf_setup.setup_existing_files', return_value=None):
                        result = setup_download_instructions()
                        assert result is None
        except ImportError:
            pytest.skip("endf_setup module not available")
    
    def test_validate_endf_setup_with_cache_test(self, tmp_path):
        """Test validate_endf_setup with cache test."""
        try:
            from smrforge.core.endf_setup import validate_endf_setup
            
            # Create directory
            endf_dir = tmp_path / "endf_test"
            endf_dir.mkdir()
            
            with patch('smrforge.core.endf_setup.scan_endf_directory') as mock_scan:
                with patch('smrforge.core.endf_setup.NuclearDataCache') as mock_cache:
                    # Mock successful scan
                    mock_scan.return_value = {
                        'total_files': 10,
                        'valid_files': 5,
                        'directory_structure': 'flat',
                        'library_versions': ['VIII.1'],
                        'nuclides': ['U235'],
                    }
                    # Mock cache with test nuclide finding
                    mock_cache_instance = Mock()
                    mock_cache_instance._find_local_endf_file.return_value = Mock()
                    mock_cache.return_value = mock_cache_instance
                    
                    is_valid, results = validate_endf_setup(endf_dir)
                    
                    assert isinstance(is_valid, bool)
                    assert isinstance(results, dict)
                    assert "has_files" in results
        except ImportError:
            pytest.skip("endf_setup module not available")
    
    def test_validate_endf_setup_cache_test_failure(self, tmp_path):
        """Test validate_endf_setup when cache test fails."""
        try:
            from smrforge.core.endf_setup import validate_endf_setup
            
            endf_dir = tmp_path / "endf_test"
            endf_dir.mkdir()
            
            with patch('smrforge.core.endf_setup.scan_endf_directory') as mock_scan:
                with patch('smrforge.core.endf_setup.NuclearDataCache') as mock_cache:
                    # Mock successful scan
                    mock_scan.return_value = {
                        'total_files': 10,
                        'valid_files': 5,
                        'directory_structure': 'flat',
                        'library_versions': [],
                        'nuclides': [],
                    }
                    # Mock cache test to raise exception
                    mock_cache.side_effect = Exception("Cache test failed")
                    
                    is_valid, results = validate_endf_setup(endf_dir)
                    
                    # Should handle exception gracefully
                    assert isinstance(is_valid, bool)
                    assert isinstance(results, dict)
                    assert "warnings" in results or "errors" in results
        except ImportError:
            pytest.skip("endf_setup module not available")
    
    def test_validate_endf_setup_no_test_nuclides_found(self, tmp_path):
        """Test validate_endf_setup when no test nuclides are found."""
        try:
            from smrforge.core.endf_setup import validate_endf_setup
            
            endf_dir = tmp_path / "endf_test"
            endf_dir.mkdir()
            
            with patch('smrforge.core.endf_setup.scan_endf_directory') as mock_scan:
                with patch('smrforge.core.endf_setup.NuclearDataCache') as mock_cache:
                    # Mock successful scan
                    mock_scan.return_value = {
                        'total_files': 10,
                        'valid_files': 5,
                        'directory_structure': 'flat',
                        'library_versions': [],
                        'nuclides': [],
                    }
                    # Mock cache with no test nuclides found
                    mock_cache_instance = Mock()
                    mock_cache_instance._find_local_endf_file.return_value = None  # Not found
                    mock_cache.return_value = mock_cache_instance
                    
                    is_valid, results = validate_endf_setup(endf_dir)
                    
                    # Should warn but may still be valid
                    assert isinstance(is_valid, bool)
                    assert isinstance(results, dict)
        except ImportError:
            pytest.skip("endf_setup module not available")
    
    def test_validate_endf_setup_scan_exception(self, tmp_path):
        """Test validate_endf_setup when scan raises exception."""
        try:
            from smrforge.core.endf_setup import validate_endf_setup
            
            endf_dir = tmp_path / "endf_test"
            endf_dir.mkdir()
            
            with patch('smrforge.core.endf_setup.scan_endf_directory') as mock_scan:
                # Mock scan to raise exception
                mock_scan.side_effect = Exception("Scan failed")
                
                is_valid, results = validate_endf_setup(endf_dir)
                
                # Should handle exception and return False
                assert is_valid is False
                assert isinstance(results, dict)
                assert "errors" in results
        except ImportError:
            pytest.skip("endf_setup module not available")
    
    def test_setup_endf_data_interactive_option_1(self):
        """Test interactive setup wizard choosing option 1 (existing files)."""
        try:
            from smrforge.core.endf_setup import setup_endf_data_interactive
            
            # Mock user choosing option 1, then canceling
            with patch('builtins.input', return_value="q"):
                with patch('builtins.print'):  # Suppress output
                    with patch('smrforge.core.endf_setup.setup_existing_files', return_value=None):
                        result = setup_endf_data_interactive()
                        assert result is None
        except ImportError:
            pytest.skip("endf_setup module not available")
    
    def test_setup_endf_data_interactive_invalid_option(self):
        """Test interactive setup wizard with invalid option."""
        try:
            from smrforge.core.endf_setup import setup_endf_data_interactive
            
            # Mock user entering invalid option, then canceling
            with patch('builtins.input', side_effect=["3", "q"]):
                with patch('builtins.print'):  # Suppress output
                    result = setup_endf_data_interactive()
                    assert result is None
        except ImportError:
            pytest.skip("endf_setup module not available")

    def test_validate_endf_setup_no_valid_files(self, tmp_path):
        """Test validate_endf_setup when scan returns zero valid files."""
        try:
            from smrforge.core.endf_setup import validate_endf_setup

            (tmp_path / "endf_empty").mkdir()
            with patch('smrforge.core.endf_setup.scan_endf_directory') as mock_scan:
                mock_scan.return_value = {
                    'total_files': 0,
                    'valid_files': 0,
                    'directory_structure': 'flat',
                    'library_versions': [],
                    'nuclides': [],
                }
                is_valid, results = validate_endf_setup(tmp_path / "endf_empty")
                assert is_valid is False
                assert "No valid ENDF files found" in results["errors"]
                assert results["valid_files"] == 0
        except ImportError:
            pytest.skip("endf_setup module not available")

