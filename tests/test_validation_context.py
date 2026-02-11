"""
Unit tests for ValidationContext class.
"""

import pytest

from smrforge.validation.integration import ValidationContext


class MockValidatedClass:
    """Mock class for testing ValidationContext."""

    def __init__(self):
        self._validation_enabled = True

    def _disable_validation(self):
        """Disable validation."""
        self._validation_enabled = False

    def _enable_validation(self):
        """Enable validation."""
        self._validation_enabled = True


class TestValidationContext:
    """Tests for ValidationContext class."""

    def test_validation_context_enter_exit(self):
        """Test ValidationContext enter and exit."""
        obj = MockValidatedClass()

        assert obj._validation_enabled is True

        with ValidationContext(obj):
            assert obj._validation_enabled is False

        assert obj._validation_enabled is True

    def test_validation_context_nested(self):
        """Test nested ValidationContext."""
        obj = MockValidatedClass()

        with ValidationContext(obj):
            assert obj._validation_enabled is False
            with ValidationContext(obj):
                assert obj._validation_enabled is False
            assert obj._validation_enabled is False

        assert obj._validation_enabled is True

    def test_validation_context_exception(self):
        """Test ValidationContext restores validation even on exception."""
        obj = MockValidatedClass()

        try:
            with ValidationContext(obj):
                assert obj._validation_enabled is False
                raise ValueError("Test exception")
        except ValueError:
            pass

        assert obj._validation_enabled is True
