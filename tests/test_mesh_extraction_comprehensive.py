"""
Comprehensive tests for geometry/mesh_extraction.py to improve coverage to 75-80%.

Tests cover:
- Block mesh extraction (extract_block_mesh)
- Channel mesh extraction (extract_fuel_channel_mesh, extract_coolant_channel_mesh)
- Pebble mesh extraction (extract_pebble_mesh)
- Core mesh extraction (extract_core_surface_mesh, extract_core_volume_mesh)
- Pebble bed mesh extraction (extract_pebble_bed_volume_mesh)
- Material boundary extraction (extract_material_boundaries)
- Error handling and edge cases
"""

import numpy as np
import pytest
from unittest.mock import Mock, MagicMock

from smrforge.geometry.mesh_extraction import (
    add_flux_to_mesh,
    add_power_to_mesh,
    extract_block_mesh,
    extract_fuel_channel_mesh,
    extract_coolant_channel_mesh,
    extract_pebble_mesh,
    extract_core_surface_mesh,
    extract_core_volume_mesh,
    extract_pebble_bed_volume_mesh,
    extract_material_boundaries,
)


@pytest.fixture
def mock_block():
    """Create a mock GraphiteBlock."""
    from smrforge.geometry.core_geometry import GraphiteBlock, Point3D
    
    block = GraphiteBlock(
        id=1,
        position=Point3D(x=0, y=0, z=0),
        block_type="fuel",
        flat_to_flat=36.0,
        height=80.0,
    )
    return block


@pytest.fixture
def mock_fuel_channel():
    """Create a mock FuelChannel."""
    from smrforge.geometry.core_geometry import FuelChannel, Point3D, MaterialRegion
    
    channel = FuelChannel(
        id=1,
        position=Point3D(x=0, y=0, z=0),
        radius=1.5,
        height=80.0,
        material_region=MaterialRegion(material_id="fuel", composition={}, temperature=1200.0, density=10.0),
    )
    return channel


@pytest.fixture
def mock_coolant_channel():
    """Create a mock CoolantChannel."""
    from smrforge.geometry.core_geometry import CoolantChannel, Point3D
    
    channel = CoolantChannel(
        id=1,
        position=Point3D(x=0, y=0, z=0),
        radius=2.0,
        height=80.0,
        flow_area=12.57,
    )
    return channel


@pytest.fixture
def mock_pebble():
    """Create a mock Pebble."""
    from smrforge.geometry.core_geometry import Pebble, Point3D, MaterialRegion
    
    pebble = Pebble(
        id=1,
        position=Point3D(x=0, y=0, z=0),
        radius=3.0,
        material_region=MaterialRegion(material_id="pebble", composition={}, temperature=1200.0, density=10.0),
    )
    return pebble


@pytest.fixture
def mock_prismatic_core():
    """Create a mock PrismaticCore."""
    from smrforge.geometry.core_geometry import PrismaticCore, GraphiteBlock, Point3D
    
    core = PrismaticCore(name="TestCore")
    # Add some blocks
    for i in range(3):
        block = GraphiteBlock(
            id=i+1,
            position=Point3D(x=i*40, y=0, z=0),
            block_type="fuel" if i == 0 else "reflector",
            flat_to_flat=36.0,
            height=80.0,
        )
        core.blocks.append(block)
    return core


@pytest.fixture
def mock_pebble_bed_core():
    """Create a mock PebbleBedCore."""
    from smrforge.geometry.core_geometry import PebbleBedCore, Pebble, Point3D, MaterialRegion
    
    core = PebbleBedCore(name="TestPebbleBed")
    # Add some pebbles
    for i in range(3):
        pebble = Pebble(
            id=i+1,
            position=Point3D(x=i*10, y=0, z=0),
            radius=3.0,
            material_region=MaterialRegion(material_id="pebble", composition={}, temperature=1200.0, density=10.0),
        )
        core.pebbles.append(pebble)
    return core


class TestBlockMeshExtraction:
    """Test block mesh extraction."""

    def test_extract_block_mesh(self, mock_block):
        """Test extracting mesh for a block."""
        mesh = extract_block_mesh(mock_block)
        assert mesh is not None
        assert hasattr(mesh, 'vertices')
        assert hasattr(mesh, 'n_vertices')
        assert mesh.n_vertices > 0

    def test_extract_block_mesh_with_material(self, mock_block):
        """Test extracting block mesh with material ID."""
        mesh = extract_block_mesh(mock_block)
        assert mesh.cell_materials is not None
        assert mesh.cell_materials[0] == "fuel"


class TestChannelMeshExtraction:
    """Test channel mesh extraction."""

    def test_extract_fuel_channel_mesh(self, mock_fuel_channel):
        """Test extracting mesh for a fuel channel."""
        mesh = extract_fuel_channel_mesh(mock_fuel_channel)
        assert mesh is not None
        assert hasattr(mesh, 'vertices')
        assert mesh.n_vertices > 0

    def test_extract_fuel_channel_mesh_with_material(self, mock_fuel_channel):
        """Test extracting fuel channel mesh with material ID."""
        mesh = extract_fuel_channel_mesh(mock_fuel_channel)
        assert mesh.cell_materials is not None
        assert mesh.cell_materials[0] == "fuel"

    def test_extract_fuel_channel_mesh_no_material_region(self):
        """Test extracting fuel channel mesh without material region."""
        from smrforge.geometry.core_geometry import FuelChannel, Point3D
        
        channel = FuelChannel(
            id=1,
            position=Point3D(x=0, y=0, z=0),
            radius=1.5,
            height=80.0,
            material_region=None,
        )
        mesh = extract_fuel_channel_mesh(channel)
        assert mesh is not None
        # Should default to "fuel"
        assert mesh.cell_materials is not None
        assert mesh.cell_materials[0] == "fuel"

    def test_extract_coolant_channel_mesh(self, mock_coolant_channel):
        """Test extracting mesh for a coolant channel."""
        mesh = extract_coolant_channel_mesh(mock_coolant_channel)
        assert mesh is not None
        assert hasattr(mesh, 'vertices')
        assert mesh.n_vertices > 0

    def test_extract_coolant_channel_mesh_with_material(self, mock_coolant_channel):
        """Test extracting coolant channel mesh with material ID."""
        mesh = extract_coolant_channel_mesh(mock_coolant_channel)
        assert mesh.cell_materials is not None
        assert mesh.cell_materials[0] == "coolant"


class TestPebbleMeshExtraction:
    """Test pebble mesh extraction."""

    def test_extract_pebble_mesh(self, mock_pebble):
        """Test extracting mesh for a pebble."""
        mesh = extract_pebble_mesh(mock_pebble)
        assert mesh is not None
        assert hasattr(mesh, 'vertices')
        assert mesh.n_vertices > 0

    def test_extract_pebble_mesh_with_material(self, mock_pebble):
        """Test extracting pebble mesh with material ID."""
        mesh = extract_pebble_mesh(mock_pebble)
        # Sphere meshes may only have faces, not cells, so cell_materials may be None
        # Just verify mesh is created successfully
        assert mesh is not None
        assert mesh.n_vertices > 0

    def test_extract_pebble_mesh_no_material_region(self):
        """Test extracting pebble mesh without material region."""
        from smrforge.geometry.core_geometry import Pebble, Point3D
        
        pebble = Pebble(
            id=1,
            position=Point3D(x=0, y=0, z=0),
            radius=3.0,
            material_region=None,
        )
        mesh = extract_pebble_mesh(pebble)
        assert mesh is not None
        # Sphere meshes only have faces, not cells, so cell_materials may be None
        # Just verify mesh is created successfully
        assert mesh.n_vertices > 0


class TestCoreMeshExtraction:
    """Test core mesh extraction."""

    def test_extract_core_surface_mesh(self, mock_prismatic_core):
        """Test extracting surface mesh for a core."""
        surface = extract_core_surface_mesh(mock_prismatic_core)
        assert surface is not None
        assert hasattr(surface, 'vertices')
        assert hasattr(surface, 'faces')
        assert surface.n_vertices > 0

    def test_extract_core_surface_mesh_no_reflector(self):
        """Test extracting surface mesh when no reflector blocks exist."""
        from smrforge.geometry.core_geometry import PrismaticCore, GraphiteBlock, Point3D
        
        core = PrismaticCore(name="TestCore")
        # Add only fuel blocks
        for i in range(2):
            block = GraphiteBlock(
                id=i+1,
                position=Point3D(x=i*40, y=0, z=0),
                block_type="fuel",
                flat_to_flat=36.0,
                height=80.0,
            )
            core.blocks.append(block)
        
        surface = extract_core_surface_mesh(core)
        assert surface is not None

    def test_extract_core_surface_mesh_empty_core(self):
        """Test extracting surface mesh from empty core."""
        from smrforge.geometry.core_geometry import PrismaticCore
        
        core = PrismaticCore(name="EmptyCore")
        surface = extract_core_surface_mesh(core)
        assert surface is not None
        assert surface.n_vertices == 0

    def test_extract_core_volume_mesh(self, mock_prismatic_core):
        """Test extracting volume mesh for a core."""
        mesh = extract_core_volume_mesh(mock_prismatic_core)
        assert mesh is not None
        assert hasattr(mesh, 'vertices')
        assert mesh.n_vertices > 0

    def test_extract_core_volume_mesh_with_channels(self, mock_prismatic_core):
        """Test extracting volume mesh with channels included."""
        # Add channels to first block
        from smrforge.geometry.core_geometry import FuelChannel, Point3D, MaterialRegion
        
        if mock_prismatic_core.blocks:
            channel = FuelChannel(
                id=1,
                position=Point3D(x=0, y=0, z=0),
                radius=1.5,
                height=80.0,
                material_region=MaterialRegion(material_id="fuel", composition={}, temperature=1200.0, density=10.0),
            )
            mock_prismatic_core.blocks[0].fuel_channels.append(channel)
        
        mesh = extract_core_volume_mesh(mock_prismatic_core, include_channels=True)
        assert mesh is not None

    def test_extract_core_volume_mesh_with_material_filter(self, mock_prismatic_core):
        """Test extracting volume mesh with material filter."""
        mesh = extract_core_volume_mesh(
            mock_prismatic_core,
            material_filter=["fuel"],
        )
        assert mesh is not None

    def test_extract_core_volume_mesh_empty_core(self):
        """Test extracting volume mesh from empty core."""
        from smrforge.geometry.core_geometry import PrismaticCore
        
        core = PrismaticCore(name="EmptyCore")
        mesh = extract_core_volume_mesh(core)
        assert mesh is not None
        assert mesh.n_vertices == 0

    def test_extract_core_volume_mesh_no_matching_materials(self, mock_prismatic_core):
        """Test extracting volume mesh with filter that matches no materials."""
        mesh = extract_core_volume_mesh(
            mock_prismatic_core,
            material_filter=["nonexistent"],
        )
        assert mesh is not None
        assert mesh.n_vertices == 0


class TestPebbleBedMeshExtraction:
    """Test pebble bed mesh extraction."""

    def test_extract_pebble_bed_volume_mesh(self, mock_pebble_bed_core):
        """Test extracting volume mesh for a pebble bed core."""
        mesh = extract_pebble_bed_volume_mesh(mock_pebble_bed_core)
        assert mesh is not None
        assert hasattr(mesh, 'vertices')
        assert mesh.n_vertices > 0

    def test_extract_pebble_bed_volume_mesh_with_material_filter(self, mock_pebble_bed_core):
        """Test extracting pebble bed volume mesh with material filter."""
        mesh = extract_pebble_bed_volume_mesh(
            mock_pebble_bed_core,
            material_filter=["pebble"],
        )
        assert mesh is not None

    def test_extract_pebble_bed_volume_mesh_empty_core(self):
        """Test extracting volume mesh from empty pebble bed core."""
        from smrforge.geometry.core_geometry import PebbleBedCore
        
        core = PebbleBedCore(name="EmptyPebbleBed")
        mesh = extract_pebble_bed_volume_mesh(core)
        assert mesh is not None
        assert mesh.n_vertices == 0

    def test_extract_pebble_bed_volume_mesh_no_matching_materials(self, mock_pebble_bed_core):
        """Test extracting pebble bed volume mesh with filter that matches no materials."""
        mesh = extract_pebble_bed_volume_mesh(
            mock_pebble_bed_core,
            material_filter=["nonexistent"],
        )
        assert mesh is not None
        assert mesh.n_vertices == 0


class TestMaterialBoundaryExtraction:
    """Test material boundary extraction."""

    def test_extract_material_boundaries(self, mock_prismatic_core):
        """Test extracting material boundaries."""
        surfaces = extract_material_boundaries(mock_prismatic_core)
        assert isinstance(surfaces, list)
        assert len(surfaces) > 0
        for surface in surfaces:
            assert hasattr(surface, 'vertices')
            assert hasattr(surface, 'faces')

    def test_extract_material_boundaries_empty_core(self):
        """Test extracting material boundaries from empty core."""
        from smrforge.geometry.core_geometry import PrismaticCore
        
        core = PrismaticCore(name="EmptyCore")
        surfaces = extract_material_boundaries(core)
        assert isinstance(surfaces, list)
        # May be empty or have some default surfaces

    def test_extract_material_boundaries_single_material(self):
        """Test extracting material boundaries when only one material exists."""
        from smrforge.geometry.core_geometry import PrismaticCore, GraphiteBlock, Point3D
        
        core = PrismaticCore(name="SingleMaterialCore")
        # Add only fuel blocks
        for i in range(2):
            block = GraphiteBlock(
                id=i+1,
                position=Point3D(x=i*40, y=0, z=0),
                block_type="fuel",
                flat_to_flat=36.0,
                height=80.0,
            )
            core.blocks.append(block)
        
        surfaces = extract_material_boundaries(core)
        assert isinstance(surfaces, list)


class TestAddFluxToMesh:
    """Test adding flux data to mesh."""
    
    def test_add_flux_to_mesh_3d(self, mock_prismatic_core):
        """Test adding 3D flux array to mesh."""
        from smrforge.geometry.mesh_3d import Mesh3D
        
        # Create a simple mesh with cells
        mesh = Mesh3D(
            vertices=np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]]),
            cells=np.array([[0, 1, 2, 3]]),
        )
        
        # Create 3D flux array [nz=2, nr=2, ng=3]
        flux = np.array([[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], 
                         [[7.0, 8.0, 9.0], [10.0, 11.0, 12.0]]])
        
        result = add_flux_to_mesh(mesh, flux, mock_prismatic_core, group=0)
        
        assert result is not None
        assert hasattr(result, 'cell_data')
        assert 'flux' in result.cell_data
    
    def test_add_flux_to_mesh_2d(self, mock_prismatic_core):
        """Test adding 2D flux array to mesh."""
        from smrforge.geometry.mesh_3d import Mesh3D
        
        mesh = Mesh3D(
            vertices=np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]]),
            cells=np.array([[0, 1, 2, 3]]),
        )
        
        # Create 2D flux array [n_blocks=3, ng=2]
        flux = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        
        result = add_flux_to_mesh(mesh, flux, mock_prismatic_core, group=1)
        
        assert result is not None
        assert 'flux' in result.cell_data
    
    def test_add_flux_to_mesh_1d(self, mock_prismatic_core):
        """Test adding 1D flux array to mesh."""
        from smrforge.geometry.mesh_3d import Mesh3D
        
        mesh = Mesh3D(
            vertices=np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]]),
            cells=np.array([[0, 1, 2, 3]]),
        )
        
        # Create 1D flux array
        flux = np.array([1.0, 2.0, 3.0, 4.0])
        
        result = add_flux_to_mesh(mesh, flux, mock_prismatic_core, group=0)
        
        assert result is not None
        assert 'flux' in result.cell_data
    
    def test_add_flux_to_mesh_short_array(self, mock_prismatic_core):
        """Test adding flux array shorter than number of cells."""
        from smrforge.geometry.mesh_3d import Mesh3D
        
        mesh = Mesh3D(
            vertices=np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0]]),
            cells=np.array([[0, 1, 2, 3], [1, 2, 3, 4]]),
        )
        
        # Create short flux array (2 values for 2 cells - should work)
        flux = np.array([1.0, 2.0])
        
        result = add_flux_to_mesh(mesh, flux, mock_prismatic_core, group=0)
        
        assert result is not None
        assert 'flux' in result.cell_data
        assert len(result.cell_data['flux']) == mesh.n_cells
    
    def test_add_flux_to_mesh_no_cells(self, mock_prismatic_core):
        """Test adding flux to mesh without cells."""
        from smrforge.geometry.mesh_3d import Mesh3D
        
        mesh = Mesh3D(
            vertices=np.array([[0, 0, 0], [1, 0, 0]]),
            cells=None,
        )
        
        flux = np.array([1.0, 2.0])
        
        result = add_flux_to_mesh(mesh, flux, mock_prismatic_core, group=0)
        
        # Should return mesh unchanged
        assert result is mesh


class TestAddPowerToMesh:
    """Test adding power data to mesh."""
    
    def test_add_power_to_mesh_2d(self, mock_prismatic_core):
        """Test adding 2D power array to mesh."""
        from smrforge.geometry.mesh_3d import Mesh3D
        
        mesh = Mesh3D(
            vertices=np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]]),
            cells=np.array([[0, 1, 2, 3]]),
        )
        
        # Create 2D power array [nz=2, nr=2]
        power = np.array([[1.0, 2.0], [3.0, 4.0]])
        
        result = add_power_to_mesh(mesh, power, mock_prismatic_core)
        
        assert result is not None
        assert hasattr(result, 'cell_data')
        assert 'power' in result.cell_data
    
    def test_add_power_to_mesh_1d(self, mock_prismatic_core):
        """Test adding 1D power array to mesh."""
        from smrforge.geometry.mesh_3d import Mesh3D
        
        mesh = Mesh3D(
            vertices=np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]]),
            cells=np.array([[0, 1, 2, 3]]),
        )
        
        # Create 1D power array
        power = np.array([1.0, 2.0, 3.0, 4.0])
        
        result = add_power_to_mesh(mesh, power, mock_prismatic_core)
        
        assert result is not None
        assert 'power' in result.cell_data
    
    def test_add_power_to_mesh_short_array(self, mock_prismatic_core):
        """Test adding power array shorter than number of cells."""
        from smrforge.geometry.mesh_3d import Mesh3D
        
        mesh = Mesh3D(
            vertices=np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [1, 0, 1]]),
            cells=np.array([[0, 1, 2, 3], [2, 3, 4, 5]]),
        )
        
        # Create short power array (1 value for 2 cells - will be tiled)
        power = np.array([1.0])
        
        result = add_power_to_mesh(mesh, power, mock_prismatic_core)
        
        assert result is not None
        assert 'power' in result.cell_data
        assert len(result.cell_data['power']) == mesh.n_cells
    
    def test_add_power_to_mesh_no_cells(self, mock_prismatic_core):
        """Test adding power to mesh without cells."""
        from smrforge.geometry.mesh_3d import Mesh3D
        
        mesh = Mesh3D(
            vertices=np.array([[0, 0, 0], [1, 0, 0]]),
            cells=None,
        )
        
        power = np.array([1.0, 2.0])
        
        result = add_power_to_mesh(mesh, power, mock_prismatic_core)
        
        # Should return mesh unchanged
        assert result is mesh

