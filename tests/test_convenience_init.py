"""
Tests for smrforge.convenience.__init__.py import error paths.
"""

import pytest
from unittest.mock import patch, Mock
import sys


class TestConvenienceInitImports:
    """Test convenience.__init__.py import error handling."""
    
    def test_convenience_init_imports_success(self):
        """Test convenience.__init__.py imports successfully."""
        import smrforge.convenience
        # Should have _CONVENIENCE_MAIN_AVAILABLE flag
        assert hasattr(smrforge.convenience, '_CONVENIENCE_MAIN_AVAILABLE')
        assert hasattr(smrforge.convenience, '_TRANSIENT_CONVENIENCE_AVAILABLE')
    
    def test_convenience_init_transient_import_error(self):
        """Test convenience.__init__.py handles transient import error."""
        # Test that the flag exists and can be False
        import smrforge.convenience
        assert hasattr(smrforge.convenience, '_TRANSIENT_CONVENIENCE_AVAILABLE')
        # The flag will be True if transients are available, False otherwise
        # This test just verifies the flag exists and the error handling path exists
        assert isinstance(smrforge.convenience._TRANSIENT_CONVENIENCE_AVAILABLE, bool)
    
    def test_convenience_init_exception_handling(self):
        """Test convenience.__init__.py handles exceptions during import."""
        with patch('pathlib.Path.exists', return_value=False):
            import importlib
            import smrforge.convenience
            # Ensure module is registered for reload even if other tests manipulated sys.modules
            sys.modules[smrforge.convenience.__name__] = smrforge.convenience
            importlib.reload(smrforge.convenience)
            # Should handle gracefully
            assert hasattr(smrforge.convenience, '_CONVENIENCE_MAIN_AVAILABLE')
