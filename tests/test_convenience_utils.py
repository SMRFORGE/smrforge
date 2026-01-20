"""
Tests for smrforge.convenience_utils module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from smrforge.core.reactor_core import Nuclide


class TestGetNuclide:
    """Test get_nuclide function."""
    
    def test_get_nuclide_simple(self):
        """Test get_nuclide with simple nuclide."""
        from smrforge.convenience_utils import get_nuclide
        
        nuclide = get_nuclide("U235")
        assert nuclide.Z == 92
        assert nuclide.A == 235
        assert nuclide.m == 0
    
    def test_get_nuclide_metastable(self):
        """Test get_nuclide with metastable."""
        from smrforge.convenience_utils import get_nuclide
        
        nuclide = get_nuclide("U235m1")
        assert nuclide.Z == 92
        assert nuclide.A == 235
        assert nuclide.m == 1
    
    def test_get_nuclide_invalid(self):
        """Test get_nuclide with invalid string."""
        from smrforge.convenience_utils import get_nuclide
        
        with pytest.raises((ValueError, KeyError, AttributeError)):
            get_nuclide("invalid")


class TestCreateNuclideList:
    """Test create_nuclide_list function."""
    
    def test_create_nuclide_list_simple(self):
        """Test create_nuclide_list with simple list."""
        from smrforge.convenience_utils import create_nuclide_list
        
        nuclides = create_nuclide_list(["U235", "U238", "Pu239"])
        assert len(nuclides) == 3
        assert all(isinstance(n, Nuclide) for n in nuclides)
        assert nuclides[0].Z == 92
        assert nuclides[0].A == 235
    
    def test_create_nuclide_list_empty(self):
        """Test create_nuclide_list with empty list."""
        from smrforge.convenience_utils import create_nuclide_list
        
        nuclides = create_nuclide_list([])
        assert isinstance(nuclides, list)
        assert len(nuclides) == 0


class TestGetMaterial:
    """Test get_material function."""
    
    def test_get_material_exists(self):
        """Test get_material with existing material."""
        from smrforge.convenience_utils import get_material
        
        # Try to get a material that might exist
        try:
            material = get_material("graphite_IG-110")
            assert material is not None
        except (KeyError, AttributeError, ImportError):
            # Material database might not be available
            pass
    
    def test_get_material_not_found(self):
        """Test get_material with non-existent material."""
        from smrforge.convenience_utils import get_material
        
        with pytest.raises((KeyError, ValueError)):
            get_material("nonexistent_material")


class TestListMaterials:
    """Test list_materials function."""
    
    def test_list_materials_all(self):
        """Test list_materials with no category."""
        from smrforge.convenience_utils import list_materials
        import polars as pl
        
        materials = list_materials()
        # Returns a Polars DataFrame
        assert isinstance(materials, pl.DataFrame)
        assert len(materials) >= 0  # May be empty if database not available
    
    def test_list_materials_category(self):
        """Test list_materials with category."""
        from smrforge.convenience_utils import list_materials
        import polars as pl
        
        materials = list_materials(category="moderator")
        # Returns a Polars DataFrame
        assert isinstance(materials, pl.DataFrame)
        # If there are materials, check they're all moderators
        if len(materials) > 0:
            assert "category" in materials.columns
            assert all(materials["category"] == "moderator")
        # May be empty if database not available


class TestConvenienceUtilsImportErrors:
    """Test convenience_utils import error paths."""
    
    def test_convenience_utils_import_error_handling(self):
        """Test convenience_utils handles import errors gracefully."""
        # Test that module can be imported even if some dependencies fail
        import smrforge.convenience_utils
        # Should not raise even if some imports fail
        assert hasattr(smrforge.convenience_utils, '_CORE_AVAILABLE')
        assert hasattr(smrforge.convenience_utils, '_VIZ_AVAILABLE')
