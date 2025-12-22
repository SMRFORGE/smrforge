"""
Tests for safety analysis module
"""

import pytest
import numpy as np

def test_import():
    """Test that safety module can be imported"""
    from smrforge import safety
    assert safety is not None

def test_transients():
    """Test transient simulations"""
    try:
        from smrforge.safety.transients import *
        # Add actual tests here
    except ImportError:
        pytest.skip("Transients not yet fully implemented")
