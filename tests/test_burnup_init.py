"""
Tests for smrforge.burnup.__init__.py import error paths.
"""

import pytest
from unittest.mock import patch, Mock


class TestBurnupInitImports:
    """Test burnup.__init__.py import error handling."""
    
    def test_burnup_init_imports_success(self):
        """Test burnup.__init__.py imports successfully."""
        import smrforge.burnup
        assert hasattr(smrforge.burnup, 'BurnupSolver')
        assert hasattr(smrforge.burnup, 'BurnupOptions')
        assert hasattr(smrforge.burnup, 'NuclideInventory')
    
    def test_burnup_init_lwr_burnup_import_error(self):
        """Test burnup.__init__.py handles lwr_burnup import error."""
        with patch('smrforge.burnup.lwr_burnup', side_effect=ImportError("Test")):
            import importlib
            import smrforge.burnup
            importlib.reload(smrforge.burnup)
            # Should still have basic imports
            assert hasattr(smrforge.burnup, 'BurnupSolver')
            # LWR features may not be available
            assert hasattr(smrforge.burnup, '_LWR_BURNUP_AVAILABLE')
    
    def test_burnup_init_fuel_management_import_error(self):
        """Test burnup.__init__.py handles fuel_management_integration import error."""
        with patch('smrforge.burnup.fuel_management_integration', side_effect=ImportError("Test")):
            import importlib
            import smrforge.burnup
            importlib.reload(smrforge.burnup)
            # Should still have basic imports
            assert hasattr(smrforge.burnup, 'BurnupSolver')
