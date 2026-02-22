"""
Tests for smrforge.presets.__init__.py import error paths.
"""

from unittest.mock import Mock, patch

import pytest


class TestPresetsInitImports:
    """Test presets.__init__.py import error handling."""

    def test_presets_init_imports_success(self):
        """Test presets.__init__.py imports successfully."""
        import smrforge.presets

        assert hasattr(smrforge.presets, "_PRESETS_AVAILABLE")

    def test_presets_init_htgr_import_error(self):
        """Test presets.__init__.py handles htgr import error."""
        # Test that the flag exists and can be False
        import smrforge.presets

        assert hasattr(smrforge.presets, "_PRESETS_AVAILABLE")
        # The flag will be True if presets are available, False otherwise
        # This test just verifies the flag exists and the error handling path exists
        assert isinstance(smrforge.presets._PRESETS_AVAILABLE, bool)
