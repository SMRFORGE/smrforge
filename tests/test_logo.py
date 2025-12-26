"""
Tests for logo utility module.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from smrforge.utils.logo import get_logo_data, get_logo_path


class TestGetLogoPath:
    """Test get_logo_path function."""

    def test_get_logo_path_returns_path(self):
        """Test that get_logo_path returns a Path object when logo exists."""
        try:
            logo_path = get_logo_path()
            assert isinstance(logo_path, Path)
            assert logo_path.exists()
        except FileNotFoundError:
            # Logo may not exist in test environment - that's acceptable
            pytest.skip("Logo file not found in test environment")

    def test_get_logo_path_file_not_found(self):
        """Test that get_logo_path raises FileNotFoundError when logo doesn't exist."""
        with patch("smrforge.utils.logo.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError, match="Logo not found"):
                get_logo_path()


class TestGetLogoData:
    """Test get_logo_data function."""

    def test_get_logo_data_returns_bytes(self):
        """Test that get_logo_data returns bytes when logo exists."""
        try:
            logo_data = get_logo_data()
            if logo_data is not None:
                assert isinstance(logo_data, bytes)
                assert len(logo_data) > 0
        except FileNotFoundError:
            # Logo may not exist in test environment - that's acceptable
            pytest.skip("Logo file not found in test environment")

    def test_get_logo_data_returns_none_when_not_found(self):
        """Test that get_logo_data returns None when logo doesn't exist."""
        with patch("smrforge.utils.logo.get_logo_path", side_effect=FileNotFoundError("Logo not found")):
            logo_data = get_logo_data()
            assert logo_data is None

    def test_get_logo_data_reads_file(self):
        """Test that get_logo_data reads the file correctly."""
        try:
            logo_path = get_logo_path()
            if logo_path.exists():
                logo_data = get_logo_data()
                assert logo_data is not None
                # Verify it matches direct file read
                expected_data = logo_path.read_bytes()
                assert logo_data == expected_data
        except FileNotFoundError:
            pytest.skip("Logo file not found in test environment")

