"""
Tests for core module
"""

import pytest

def test_constants():
    """Test that constants are accessible"""
    from smrforge.core import constants
    assert hasattr(constants, '__file__')

def test_materials_database():
    """Test materials database"""
    from smrforge.core import materials_database
    assert materials_database is not None
