"""
Tests for smrforge.validation.__init__.py import error paths.
"""

from unittest.mock import Mock, patch

import pytest


class TestValidationInitImports:
    """Test validation.__init__.py import error handling."""

    def test_validation_init_imports_success(self):
        """Test validation.__init__.py imports successfully."""
        import smrforge.validation

        assert hasattr(smrforge.validation, "ReactorSpecification")
        assert hasattr(smrforge.validation, "ValidationResult")

    def test_validation_init_integration_import_error(self):
        """Test validation.__init__.py handles integration import error."""
        with patch("smrforge.validation.integration", side_effect=ImportError("Test")):
            import importlib

            import smrforge.validation

            importlib.reload(smrforge.validation)
            # Should still have basic imports
            assert hasattr(smrforge.validation, "ReactorSpecification")
            # Integration features may not be available
            assert hasattr(smrforge.validation, "_INTEGRATION_AVAILABLE")
