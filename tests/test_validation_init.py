"""
Tests for smrforge.validation.__init__.py import error paths.
"""

import importlib
from unittest.mock import Mock, patch

import pytest


class TestValidationInitImports:
    """Test validation.__init__.py import error handling."""

    def test_validation_init_imports_success(self):
        """Test validation.__init__.py imports successfully."""
        validation = importlib.import_module("smrforge.validation")
        assert hasattr(validation, "ReactorSpecification")
        assert hasattr(validation, "ValidationResult")

    def test_validation_init_integration_import_error(self):
        """Test validation.__init__.py handles integration import error."""
        with patch("smrforge.validation.integration", side_effect=ImportError("Test")):
            validation = importlib.import_module("smrforge.validation")
            importlib.reload(validation)
            # Should still have basic imports
            assert hasattr(validation, "ReactorSpecification")
            # Integration features may not be available
            assert hasattr(validation, "_INTEGRATION_AVAILABLE")
