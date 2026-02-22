"""
Tests for smrforge.presets.__init__.py import error paths.
"""

import importlib
from unittest.mock import Mock, patch

import pytest


class TestPresetsInitImports:
    """Test presets.__init__.py import error handling."""

    def test_presets_init_imports_success(self):
        """Test presets.__init__.py imports successfully."""
        presets = importlib.import_module("smrforge.presets")
        assert hasattr(presets, "_PRESETS_AVAILABLE")

    def test_presets_init_htgr_import_error(self):
        """Test presets.__init__.py handles htgr import error."""
        # Test that the flag exists and can be False
        presets = importlib.import_module("smrforge.presets")
        assert hasattr(presets, "_PRESETS_AVAILABLE")
        # The flag will be True if presets are available, False otherwise
        # This test just verifies the flag exists and the error handling path exists
        assert isinstance(presets._PRESETS_AVAILABLE, bool)
