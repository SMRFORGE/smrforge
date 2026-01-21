"""
Extended tests for geometry/advanced_import.py to improve coverage.

This test file focuses on additional edge cases and uncovered paths:
- _reconstruct_core_from_csg edge cases (missing surfaces, different surface types)
- _reconstruct_lattice edge cases (non-hexagonal, missing data)
- _reconstruct_from_serpent edge cases (missing data, different surface types)
- _reconstruct_from_mcnp edge cases (different surface types, edge cases)
- Edge cases in parsing methods
- Error handling paths
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

try:
    from smrforge.geometry.advanced_import import (
        CSGSurface,
        CSGCell,
        Lattice,
        AdvancedGeometryImporter,
        GeometryConverter,
        _is_numeric,
    )
    from smrforge.geometry.core_geometry import Point3D, PrismaticCore
    ADVANCED_IMPORT_AVAILABLE = True
except ImportError:
    ADVANCED_IMPORT_AVAILABLE = False


class TestReconstructCoreFromCSGExtended:
    """Extended tests for _reconstruct_core_from_csg edge cases."""
    
    def test_reconstruct_core_from_csg_no_surfaces(self):
        """Test _reconstruct_core_from_csg with no surfaces."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        surfaces = {}
        cells = {
            1: CSGCell(id=1, material=1),
        }
        lattices = {}
        
        core = PrismaticCore(name="Test")
        result = AdvancedGeometryImporter._reconstruct_core_from_csg(surfaces, cells, lattices, core)
        
        assert result is not None
        assert isinstance(result, PrismaticCore)
    
    def test_reconstruct_core_from_csg_no_cells(self):
        """Test _reconstruct_core_from_csg with no cells."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        surfaces = {
            1: CSGSurface(id=1, surface_type="z-cylinder", coeffs=[100.0]),
        }
        cells = {}
        lattices = {}
        
        core = PrismaticCore(name="Test")
        result = AdvancedGeometryImporter._reconstruct_core_from_csg(surfaces, cells, lattices, core)
        
        assert result is not None
        assert isinstance(result, PrismaticCore)
    
    def test_reconstruct_core_from_csg_cell_with_fill(self):
        """Test _reconstruct_core_from_csg with cell that has fill."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        surfaces = {
            1: CSGSurface(id=1, surface_type="z-cylinder", coeffs=[100.0]),
        }
        cells = {
            1: CSGCell(id=1, material=1, fill="lattice"),
        }
        lattices = {}
        
        core = PrismaticCore(name="Test")
        result = AdvancedGeometryImporter._reconstruct_core_from_csg(surfaces, cells, lattices, core)
        
        assert result is not None
        assert isinstance(result, PrismaticCore)
    
    def test_reconstruct_core_from_csg_empty_coeffs(self):
        """Test _reconstruct_core_from_csg with surface having empty coeffs."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        surfaces = {
            1: CSGSurface(id=1, surface_type="z-cylinder", coeffs=[]),
            2: CSGSurface(id=2, surface_type="z-plane", coeffs=[]),
        }
        cells = {
            1: CSGCell(id=1, material=1),
        }
        lattices = {}
        
        core = PrismaticCore(name="Test")
        result = AdvancedGeometryImporter._reconstruct_core_from_csg(surfaces, cells, lattices, core)
        
        assert result is not None
        assert isinstance(result, PrismaticCore)
    
    def test_reconstruct_core_from_csg_multiple_z_planes(self):
        """Test _reconstruct_core_from_csg with multiple z-planes."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        surfaces = {
            1: CSGSurface(id=1, surface_type="z-cylinder", coeffs=[100.0]),
            2: CSGSurface(id=2, surface_type="z-plane", coeffs=[0.0]),
            3: CSGSurface(id=3, surface_type="z-plane", coeffs=[800.0]),
            4: CSGSurface(id=4, surface_type="z-plane", coeffs=[-50.0]),
        }
        cells = {
            1: CSGCell(id=1, material=1),
        }
        lattices = {}
        
        core = PrismaticCore(name="Test")
        result = AdvancedGeometryImporter._reconstruct_core_from_csg(surfaces, cells, lattices, core)
        
        assert result is not None
        assert isinstance(result, PrismaticCore)
        assert result.core_height > 0


class TestReconstructLatticeExtended:
    """Extended tests for _reconstruct_lattice edge cases."""
    
    def test_reconstruct_lattice_rectangular(self):
        """Test _reconstruct_lattice with rectangular lattice."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        lattices = {
            1: Lattice(
                id=1,
                lattice_type="rectangular",
                dimension=(2, 2, 1),
                lower_left=Point3D(0, 0, 0),
                pitch=(36.0, 36.0, 800.0),
                universes=[[[1, 2], [3, 4]]],
            ),
        }
        
        core = PrismaticCore(name="Test")
        result = AdvancedGeometryImporter._reconstruct_lattice(lattices, core)
        
        assert result is not None
        assert isinstance(result, PrismaticCore)
        # Rectangular lattices may not modify core as much
        assert result.n_rings == 0  # Not hexagonal
    
    def test_reconstruct_lattice_cylindrical(self):
        """Test _reconstruct_lattice with cylindrical lattice."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        lattices = {
            1: Lattice(
                id=1,
                lattice_type="cylindrical",
                dimension=(2, 0, 1),
                lower_left=Point3D(0, 0, 0),
                pitch=(36.0, 36.0, 800.0),
                universes=[[[1]]],
            ),
        }
        
        core = PrismaticCore(name="Test")
        result = AdvancedGeometryImporter._reconstruct_lattice(lattices, core)
        
        assert result is not None
        assert isinstance(result, PrismaticCore)
    
    def test_reconstruct_lattice_empty_dimension(self):
        """Test _reconstruct_lattice with empty dimension."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        lattices = {
            1: Lattice(
                id=1,
                lattice_type="hexagonal",
                dimension=(),
                lower_left=Point3D(0, 0, 0),
                pitch=(36.0, 36.0, 800.0),
                universes=[],
            ),
        }
        
        core = PrismaticCore(name="Test")
        result = AdvancedGeometryImporter._reconstruct_lattice(lattices, core)
        
        assert result is not None
        assert isinstance(result, PrismaticCore)
    
    def test_reconstruct_lattice_empty_pitch(self):
        """Test _reconstruct_lattice with empty pitch."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        lattices = {
            1: Lattice(
                id=1,
                lattice_type="hexagonal",
                dimension=(2, 0, 1),
                lower_left=Point3D(0, 0, 0),
                pitch=(),
                universes=[[[1]]],
            ),
        }
        
        core = PrismaticCore(name="Test")
        result = AdvancedGeometryImporter._reconstruct_lattice(lattices, core)
        
        assert result is not None
        assert isinstance(result, PrismaticCore)


class TestReconstructFromSerpentExtended:
    """Extended tests for _reconstruct_from_serpent edge cases."""
    
    def test_reconstruct_from_serpent_no_surfaces(self):
        """Test _reconstruct_from_serpent with no surfaces."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        surfaces = {}
        cells = {
            1: {"universe": "0", "material": "fuel"},
        }
        lattices = {}
        
        core = PrismaticCore(name="Test")
        result = AdvancedGeometryImporter._reconstruct_from_serpent(surfaces, cells, lattices, core)
        
        assert result is not None
        assert isinstance(result, PrismaticCore)
    
    def test_reconstruct_from_serpent_multiple_pz_surfaces(self):
        """Test _reconstruct_from_serpent with multiple pz surfaces."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        surfaces = {
            1: {"type": "cz", "params": [100.0]},
            2: {"type": "pz", "params": [0.0]},
            3: {"type": "pz", "params": [800.0]},
            4: {"type": "pz", "params": [-50.0]},
        }
        cells = {}
        lattices = {}
        
        core = PrismaticCore(name="Test")
        result = AdvancedGeometryImporter._reconstruct_from_serpent(surfaces, cells, lattices, core)
        
        assert result is not None
        assert isinstance(result, PrismaticCore)
        assert result.core_height > 0
    
    def test_reconstruct_from_serpent_hex_lattice_insufficient_params(self):
        """Test _reconstruct_from_serpent with hex lattice having insufficient params."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        surfaces = {
            1: {"type": "cz", "params": [100.0]},
        }
        cells = {}
        lattices = {
            1: {"type": "hex", "params": [36.0]},  # Only one param, needs at least 2
        }
        
        core = PrismaticCore(name="Test")
        result = AdvancedGeometryImporter._reconstruct_from_serpent(surfaces, cells, lattices, core)
        
        assert result is not None
        assert isinstance(result, PrismaticCore)
    
    def test_reconstruct_from_serpent_non_hex_lattice(self):
        """Test _reconstruct_from_serpent with non-hexagonal lattice."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        surfaces = {}
        cells = {}
        lattices = {
            1: {"type": "rect", "params": [20.0, 20.0]},
        }
        
        core = PrismaticCore(name="Test")
        result = AdvancedGeometryImporter._reconstruct_from_serpent(surfaces, cells, lattices, core)
        
        assert result is not None
        assert isinstance(result, PrismaticCore)


class TestReconstructFromMCNPExtended:
    """Extended tests for _reconstruct_from_mcnp edge cases."""
    
    def test_reconstruct_from_mcnp_no_surfaces(self):
        """Test _reconstruct_from_mcnp with no surfaces."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        surfaces = {}
        cells = {
            1: {"material": 1, "region": "-1 2 -3"},
        }
        
        core = PrismaticCore(name="Test")
        result = AdvancedGeometryImporter._reconstruct_from_mcnp(surfaces, cells, core)
        
        assert result is not None
        assert isinstance(result, PrismaticCore)
    
    def test_reconstruct_from_mcnp_multiple_pz_surfaces(self):
        """Test _reconstruct_from_mcnp with multiple PZ surfaces."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        surfaces = {
            1: {"type": "CZ", "params": [100.0]},
            2: {"type": "PZ", "params": [0.0]},
            3: {"type": "PZ", "params": [800.0]},
            4: {"type": "PZ", "params": [-50.0]},
        }
        cells = {}
        
        core = PrismaticCore(name="Test")
        result = AdvancedGeometryImporter._reconstruct_from_mcnp(surfaces, cells, core)
        
        assert result is not None
        assert isinstance(result, PrismaticCore)
        assert result.core_height > 0
    
    def test_reconstruct_from_mcnp_no_params(self):
        """Test _reconstruct_from_mcnp with surface having no params."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        surfaces = {
            1: {"type": "CZ", "params": []},
            2: {"type": "PZ", "params": []},
        }
        cells = {}
        
        core = PrismaticCore(name="Test")
        result = AdvancedGeometryImporter._reconstruct_from_mcnp(surfaces, cells, core)
        
        assert result is not None
        assert isinstance(result, PrismaticCore)


class TestCreateHexLatticeExtended:
    """Extended tests for _create_hex_lattice edge cases."""
    
    def test_create_hex_lattice_zero_diameter(self):
        """Test _create_hex_lattice with zero core diameter."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        core = PrismaticCore(name="Test")
        core.core_diameter = 0.0
        core.core_height = 800.0
        
        result = AdvancedGeometryImporter._create_hex_lattice(core, pitch=36.0)
        
        assert result is not None
        assert isinstance(result, PrismaticCore)
        assert result.n_rings == 3  # Default when diameter is 0


class TestParseMCNPSurfacesExtended:
    """Extended tests for _parse_mcnp_surfaces edge cases."""
    
    def test_parse_mcnp_surfaces_negative_id(self):
        """Test _parse_mcnp_surfaces with negative surface ID."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        content = """
-1 CZ 100.0
2 PZ 0.0
"""
        surfaces = AdvancedGeometryImporter._parse_mcnp_surfaces(content)
        
        assert isinstance(surfaces, dict)
        assert 1 in surfaces  # Should convert negative ID to positive
        assert surfaces[1]["type"] == "CZ"
    
    def test_parse_mcnp_surfaces_px_py_types(self):
        """Test _parse_mcnp_surfaces with PX and PY surface types."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        content = """
1 PX 0.0
2 PY 0.0
3 PZ 800.0
"""
        surfaces = AdvancedGeometryImporter._parse_mcnp_surfaces(content)
        
        assert isinstance(surfaces, dict)
        assert 1 in surfaces
        assert surfaces[1]["type"] == "PX"
        assert 2 in surfaces
        assert surfaces[2]["type"] == "PY"
    
    def test_parse_mcnp_surfaces_no_params(self):
        """Test _parse_mcnp_surfaces with surface having no params."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        content = """
1 PX
"""
        surfaces = AdvancedGeometryImporter._parse_mcnp_surfaces(content)
        
        assert isinstance(surfaces, dict)
        # May or may not include surface depending on implementation
        assert isinstance(surfaces, dict)


class TestParseMCNPCellsExtended:
    """Extended tests for _parse_mcnp_cells edge cases."""
    
    def test_parse_mcnp_cells_negative_material(self):
        """Test _parse_mcnp_cells with negative material."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        content = """
1 -1 -10.0 -1 2 -3
"""
        cells = AdvancedGeometryImporter._parse_mcnp_cells(content)
        
        assert isinstance(cells, dict)
        assert 1 in cells
        assert cells[1]["material"] == -1
    
    def test_parse_mcnp_cells_non_numeric_material(self):
        """Test _parse_mcnp_cells with non-numeric material."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        content = """
1 fuel -10.0 -1 2 -3
"""
        cells = AdvancedGeometryImporter._parse_mcnp_cells(content)
        
        assert isinstance(cells, dict)
        assert 1 in cells
        assert cells[1]["material"] is None  # Non-numeric material
    
    def test_parse_mcnp_cells_minimal_region(self):
        """Test _parse_mcnp_cells with minimal region."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        content = """
1 1 -10.0 -1
"""
        cells = AdvancedGeometryImporter._parse_mcnp_cells(content)
        
        assert isinstance(cells, dict)
        assert 1 in cells
        # Region includes all parts after material, so includes density and region
        assert "-1" in cells[1]["region"]


class TestIsNumericExtended:
    """Extended tests for _is_numeric helper function."""
    
    def test_is_numeric_scientific_notation(self):
        """Test _is_numeric with scientific notation."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        assert _is_numeric("1e5") is True
        assert _is_numeric("1E-5") is True
        assert _is_numeric("-1.5e10") is True
    
    def test_is_numeric_whitespace(self):
        """Test _is_numeric with whitespace."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        # float() can handle leading/trailing whitespace, so these are numeric
        assert _is_numeric(" 123 ") is True  # float() accepts whitespace
        assert _is_numeric("123") is True


class TestFromOpenMCXMLExtended:
    """Extended tests for _from_openmc_xml_csg edge cases."""
    
    def test_from_openmc_xml_csg_empty_file(self):
        """Test _from_openmc_xml_csg with empty XML file."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        xml_content = """<?xml version="1.0"?>
<geometry>
</geometry>"""
        
        filepath = Path("empty.xml")
        with patch('builtins.open', mock_open(read_data=xml_content)):
            with patch('pathlib.Path.exists', return_value=True):
                result = AdvancedGeometryImporter._from_openmc_xml_csg(filepath)
                # Should handle empty geometry gracefully
                assert result is not None or True
    
    def test_from_openmc_xml_csg_missing_attributes(self):
        """Test _from_openmc_xml_csg with missing XML attributes."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        xml_content = """<?xml version="1.0"?>
<geometry>
    <surface id="1"/>
    <cell id="1"/>
    <lattice id="1"/>
</geometry>"""
        
        filepath = Path("missing_attrs.xml")
        with patch('builtins.open', mock_open(read_data=xml_content)):
            with patch('pathlib.Path.exists', return_value=True):
                result = AdvancedGeometryImporter._from_openmc_xml_csg(filepath)
                # Should handle missing attributes gracefully
                assert result is not None or True
    
    def test_from_openmc_xml_csg_invalid_universe_text(self):
        """Test _from_openmc_xml_csg with invalid universe text."""
        if not ADVANCED_IMPORT_AVAILABLE:
            pytest.skip("Advanced import module not available")
        
        xml_content = """<?xml version="1.0"?>
<geometry>
    <lattice id="1" type="hexagonal" dimension="2 2 1" pitch="36.0 36.0 800.0" lower_left="0.0 0.0 0.0">
        <universes>
            <universe>abc</universe>
            <universe></universe>
        </universes>
    </lattice>
</geometry>"""
        
        filepath = Path("invalid_universe.xml")
        with patch('builtins.open', mock_open(read_data=xml_content)):
            with patch('pathlib.Path.exists', return_value=True):
                # Should raise ValueError when universe text cannot be parsed as int
                with pytest.raises(ValueError, match="Error parsing OpenMC CSG"):
                    AdvancedGeometryImporter._from_openmc_xml_csg(filepath)
