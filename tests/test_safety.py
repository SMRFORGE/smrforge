"""
Tests for safety analysis module
"""

import numpy as np
import pytest


def test_import():
    """Test that safety module can be imported"""
    from smrforge import safety

    assert safety is not None


def test_transients():
    """Test transient simulations"""
    try:
        from smrforge.safety import transients

        assert transients is not None
        # Add actual tests here
    except ImportError:
        pytest.skip("Transients not yet fully implemented")
