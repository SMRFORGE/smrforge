"""Tests for validate_preprocessed_library."""

from pathlib import Path

import pytest

from smrforge.data_downloader import validate_preprocessed_library


class TestValidatePreprocessedLibrary:
    """Tests for validate_preprocessed_library."""

    def test_nonexistent_path(self):
        """Test validation of nonexistent path."""
        result = validate_preprocessed_library(Path("/nonexistent/path"))
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_existing_empty_dir(self, tmp_path):
        """Test validation of existing empty directory."""
        result = validate_preprocessed_library(tmp_path)
        assert "valid" in result
        assert "nuclides_found" in result
        assert "missing_nuclides" in result
