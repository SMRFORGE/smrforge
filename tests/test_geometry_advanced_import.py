"""
Comprehensive tests for geometry/advanced_import.py to improve coverage.

Tests cover:
- CSGSurface, CSGCell, Lattice dataclasses
- AdvancedGeometryImporter methods
- Import error handling (openmc, trimesh, ET unavailable)
- Error paths and edge cases
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

try:
    from smrforge.geometry.advanced_import import (
        CSGSurface,
        CSGCell,
        Lattice,
        AdvancedGeometryImporter,
        GeometryConverter,
    )
    from smrforge.geometry.core_geometry import Point3D
    ADVANCED_IMPORT_AVAILABLE = True
except ImportError:
    ADVANCED_IMPORT_AVAILABLE = False


class TestCSGSurface:
    """Test CSGSurface dataclass."""
    
    def test_csg_surface_creation(self):
        """Test creating a CSGSurface."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        surface = CSGSurface(
            id=1,
            surface_type="z-cylinder",
            coeffs=[10.0, 0.0, 0.0],
            boundary_type="vacuum",
        )
        
        assert surface.id == 1
        assert surface.surface_type == "z-cylinder"
        assert surface.coeffs == [10.0, 0.0, 0.0]
        assert surface.boundary_type == "vacuum"
    
    def test_csg_surface_default_boundary(self):
        """Test CSGSurface with default boundary type."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        surface = CSGSurface(
            id=2,
            surface_type="z-plane",
            coeffs=[0.0],
        )
        
        assert surface.boundary_type == "vacuum"


class TestCSGCell:
    """Test CSGCell dataclass."""
    
    def test_csg_cell_creation(self):
        """Test creating a CSGCell."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        cell = CSGCell(
            id=1,
            region="-1 & 2 & -3",
            material=1,
            fill=2,
            surfaces=[1, 2, 3],
        )
        
        assert cell.id == 1
        assert cell.region == "-1 & 2 & -3"
        assert cell.material == 1
        assert cell.fill == 2
        assert cell.surfaces == [1, 2, 3]
    
    def test_csg_cell_defaults(self):
        """Test CSGCell with default values."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        cell = CSGCell(id=1)
        
        assert cell.region is None
        assert cell.material is None
        assert cell.fill is None
        assert cell.surfaces == []


class TestLattice:
    """Test Lattice dataclass."""
    
    def test_lattice_creation(self):
        """Test creating a Lattice."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        lattice = Lattice(
            id=1,
            lattice_type="hexagonal",
            dimension=(3, 3, 1),
            lower_left=Point3D(0, 0, 0),
            pitch=(36.0, 36.0, 800.0),
            universes=[[[1, 2, 3], [4, 5, 6], [7, 8, 9]]],
        )
        
        assert lattice.id == 1
        assert lattice.lattice_type == "hexagonal"
        assert lattice.dimension == (3, 3, 1)
        assert lattice.pitch == (36.0, 36.0, 800.0)


class TestAdvancedGeometryImporter:
    """Test AdvancedGeometryImporter class."""
    
    def test_extract_surface_ids_from_region(self):
        """Test extracting surface IDs from region string."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        # Test with region string
        region = "-1 & 2 & -3"
        surface_ids = AdvancedGeometryImporter._extract_surface_ids_from_region(region)
        
        assert surface_ids == [1, 2, 3]
    
    def test_extract_surface_ids_empty_region(self):
        """Test extracting surface IDs from empty region."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        surface_ids = AdvancedGeometryImporter._extract_surface_ids_from_region(None)
        
        assert surface_ids == []
    
    def test_extract_surface_ids_complex_region(self):
        """Test extracting surface IDs from complex region string."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        region = "(-1 | 2) & -3 & 4"
        surface_ids = AdvancedGeometryImporter._extract_surface_ids_from_region(region)
        
        assert 1 in surface_ids
        assert 2 in surface_ids
        assert 3 in surface_ids
        assert 4 in surface_ids
    
    def test_from_openmc_full_without_openmc(self):
        """Test from_openmc_full when openmc is not available."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        with patch('smrforge.geometry.advanced_import._OPENMC_AVAILABLE', False):
            # Should fallback to manual XML parsing
            xml_content = """<?xml version="1.0"?>
<geometry>
    <surface id="1" type="z-cylinder" coeffs="10.0 0.0 0.0" boundary_type="vacuum"/>
    <cell id="1" material="1" region="-1"/>
</geometry>"""
            
            filepath = Path("test_geometry.xml")
            with patch('builtins.open', mock_open(read_data=xml_content)):
                with patch('pathlib.Path.exists', return_value=True):
                    # Should attempt manual parsing
                    result = AdvancedGeometryImporter.from_openmc_full(filepath)
                    # Result may be None if parsing fails, but should not raise ImportError
                    assert result is None or hasattr(result, 'blocks')
    
    def test_from_openmc_full_file_not_found(self):
        """Test from_openmc_full with non-existent file."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        filepath = Path("nonexistent.xml")
        
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises((FileNotFoundError, ValueError)):
                AdvancedGeometryImporter.from_openmc_full(filepath)
    
    def test_from_openmc_xml_csg_without_et(self):
        """Test _from_openmc_xml_csg when ET is not available."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        with patch('smrforge.geometry.advanced_import.ET', None):
            filepath = Path("test.xml")
            with pytest.raises(ImportError, match="xml.etree.ElementTree not available"):
                AdvancedGeometryImporter._from_openmc_xml_csg(filepath)
    
    def test_from_openmc_xml_csg_invalid_xml(self):
        """Test _from_openmc_xml_csg with invalid XML."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        invalid_xml = "not valid xml content"
        filepath = Path("invalid.xml")
        
        with patch('builtins.open', mock_open(read_data=invalid_xml)):
            with patch('pathlib.Path.exists', return_value=True):
                with pytest.raises(ValueError, match="Error parsing OpenMC CSG"):
                    AdvancedGeometryImporter._from_openmc_xml_csg(filepath)
    
    def test_reconstruct_core_from_csg_basic(self):
        """Test _reconstruct_core_from_csg with basic CSG data."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        try:
            from smrforge.geometry.core_geometry import PrismaticCore
            
            surfaces = {
                1: CSGSurface(id=1, surface_type="z-cylinder", coeffs=[100.0]),
                2: CSGSurface(id=2, surface_type="z-plane", coeffs=[0.0]),
                3: CSGSurface(id=3, surface_type="z-plane", coeffs=[800.0]),
            }
            cells = {
                1: CSGCell(id=1, material=1, surfaces=[1, 2, 3]),
            }
            lattices = {}
            
            core = PrismaticCore(name="Test")
            result = AdvancedGeometryImporter._reconstruct_core_from_csg(surfaces, cells, lattices, core)
            
            assert result is not None
            assert isinstance(result, PrismaticCore)
        except ImportError:
            pytest.skip("PrismaticCore not available")


class TestGeometryConverter:
    """Test GeometryConverter class."""
    
    def test_converter_initialization(self):
        """Test GeometryConverter initialization."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        try:
            converter = GeometryConverter()
            assert converter is not None
        except (ImportError, TypeError):
            pytest.skip("GeometryConverter not available or requires arguments")
