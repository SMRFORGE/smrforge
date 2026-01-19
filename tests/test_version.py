"""
Tests for smrforge.__version__ module.
"""

import pytest
from smrforge.__version__ import __version__, __version_info__, get_version


class TestVersion:
    """Test version information."""
    
    def test_version_string(self):
        """Test that __version__ is a string."""
        assert isinstance(__version__, str)
        assert len(__version__) > 0
    
    def test_version_info(self):
        """Test that __version_info__ is a tuple."""
        assert isinstance(__version_info__, tuple)
        assert len(__version_info__) >= 2
    
    def test_get_version(self):
        """Test get_version function."""
        version = get_version()
        assert isinstance(version, str)
        assert version == __version__
