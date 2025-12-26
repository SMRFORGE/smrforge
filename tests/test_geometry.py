"""
Comprehensive tests for geometry module
"""

from pathlib import Path

import numpy as np
import pytest


class TestGeometryImports:
    """Test geometry module imports."""

    def test_geometry_module_import(self):
        """Test that geometry module can be imported."""
        from smrforge import geometry

        assert geometry is not None

    def test_prismatic_core_import(self):
        """Test that PrismaticCore can be imported."""
        try:
            from smrforge.geometry.core_geometry import PrismaticCore

            assert PrismaticCore is not None
        except ImportError:
            pytest.skip("PrismaticCore not available")

    def test_pebble_bed_core_import(self):
        """Test that PebbleBedCore can be imported."""
        try:
            from smrforge.geometry.core_geometry import PebbleBedCore

            assert PebbleBedCore is not None
        except ImportError:
            pytest.skip("PebbleBedCore not available")


class TestPrismaticCore:
    """Test PrismaticCore class."""

    def test_prismatic_core_creation(self):
        """Test creating a PrismaticCore instance."""
        try:
            from smrforge.geometry.core_geometry import PrismaticCore

            core = PrismaticCore(name="Test-Core")
            assert core.name == "Test-Core"
            assert len(core.blocks) == 0
        except ImportError:
            pytest.skip("PrismaticCore not available")

    def test_hexagonal_lattice_build(self):
        """Test building hexagonal lattice."""
        try:
            from smrforge.geometry.core_geometry import PrismaticCore

            core = PrismaticCore(name="Test-Core")
            core.build_hexagonal_lattice(
                n_rings=2, pitch=40.0, block_height=79.3, n_axial=3, flat_to_flat=36.0
            )

            assert len(core.blocks) > 0
            assert core.core_height > 0
            assert core.n_rings == 2
        except ImportError:
            pytest.skip("PrismaticCore not available")

    def test_prismatic_core_mesh_generation(self):
        """Test mesh generation for PrismaticCore."""
        try:
            from smrforge.geometry.core_geometry import PrismaticCore

            core = PrismaticCore(name="Test-Core")
            core.build_hexagonal_lattice(
                n_rings=2, pitch=40.0, block_height=79.3, n_axial=3, flat_to_flat=36.0
            )

            # Generate mesh
            core.generate_mesh(n_radial=11, n_axial=21)

            assert core.radial_mesh is not None
            assert core.axial_mesh is not None
            assert len(core.radial_mesh) > 0
            assert len(core.axial_mesh) > 0
        except ImportError:
            pytest.skip("PrismaticCore not available")

    @pytest.mark.parametrize("n_rings", [1, 2, 3])
    def test_different_lattice_sizes(self, n_rings):
        """Test building lattices with different numbers of rings."""
        try:
            from smrforge.geometry.core_geometry import PrismaticCore

            core = PrismaticCore(name=f"Test-Core-{n_rings}")
            core.build_hexagonal_lattice(
                n_rings=n_rings,
                pitch=40.0,
                block_height=79.3,
                n_axial=2,
                flat_to_flat=36.0,
            )

            assert core.n_rings == n_rings
            assert len(core.blocks) > 0
        except ImportError:
            pytest.skip("PrismaticCore not available")


class TestPebbleBedCore:
    """Test PebbleBedCore class."""

    def test_pebble_bed_core_creation(self):
        """Test creating a PebbleBedCore instance."""
        try:
            from smrforge.geometry.core_geometry import PebbleBedCore

            core = PebbleBedCore(name="Test-PebbleBed")
            assert core.name == "Test-PebbleBed"
            assert len(core.pebbles) == 0
        except ImportError:
            pytest.skip("PebbleBedCore not available")

    def test_pebble_bed_build(self):
        """Test building pebble bed core."""
        try:
            from smrforge.geometry.core_geometry import PebbleBedCore

            core = PebbleBedCore(name="Test-PebbleBed")
            core.build_structured_packing(
                core_height=1100.0, core_diameter=300.0, pebble_radius=3.0
            )

            assert len(core.pebbles) > 0
            assert core.core_height == 1100.0
            assert core.core_diameter == 300.0
            assert 0 < core.packing_fraction < 1.0
        except ImportError:
            pytest.skip("PebbleBedCore not available")


class TestGeometryUtilities:
    """Test geometry utility functions."""

    def test_point3d_operations(self):
        """Test Point3D operations."""
        try:
            from smrforge.geometry.core_geometry import Point3D

            p1 = Point3D(1.0, 2.0, 3.0)
            p2 = Point3D(4.0, 5.0, 6.0)

            distance = p1.distance_to(p2)
            expected = np.sqrt(3**2 + 3**2 + 3**2)
            assert np.isclose(distance, expected)

            p3 = p1 + p2
            assert p3.x == 5.0
            assert p3.y == 7.0
            assert p3.z == 9.0
        except ImportError:
            pytest.skip("Point3D not available")

    def test_geometry_export(self, temp_dir):
        """Test geometry export functionality."""
        try:
            from smrforge.geometry.core_geometry import GeometryExporter, PrismaticCore

            core = PrismaticCore(name="Test-Export")
            core.build_hexagonal_lattice(
                n_rings=2, pitch=40.0, block_height=79.3, n_axial=2, flat_to_flat=36.0
            )

            export_path = temp_dir / "test_core.json"
            GeometryExporter.to_json(core, export_path)

            assert export_path.exists()
        except ImportError:
            pytest.skip("Geometry export not available")

    def test_prismatic_core_methods(self):
        """Test additional PrismaticCore methods."""
        try:
            from smrforge.geometry.core_geometry import PrismaticCore

            core = PrismaticCore(name="Test-Methods")
            core.build_hexagonal_lattice(
                n_rings=1, pitch=40.0, block_height=79.3, n_axial=2, flat_to_flat=36.0
            )

            # Test total_fuel_volume
            fuel_vol = core.total_fuel_volume()
            assert fuel_vol >= 0

            # Test total_power
            power = core.total_power()
            assert power >= 0

            # Test get_block_by_position
            block = core.get_block_by_position(0.0, 0.0, 50.0)
            assert block is not None or len(core.blocks) == 0

            # Test to_dataframe
            try:
                df = core.to_dataframe()
                assert df is not None
            except Exception:
                # May fail if polars not available
                pass
        except ImportError:
            pytest.skip("PrismaticCore not available")

    def test_material_region(self):
        """Test MaterialRegion dataclass."""
        try:
            from smrforge.geometry.core_geometry import MaterialRegion

            region = MaterialRegion(
                material_id="fuel",
                composition={"U235": 0.001, "U238": 0.01},
                temperature=1200.0,
                density=10.0,
            )

            assert region.total_number_density() == 0.011
            assert region.material_id == "fuel"
        except ImportError:
            pytest.skip("MaterialRegion not available")

    def test_fuel_channel(self):
        """Test FuelChannel dataclass."""
        try:
            from smrforge.geometry.core_geometry import FuelChannel, MaterialRegion, Point3D

            mat_region = MaterialRegion(
                material_id="fuel",
                composition={"U235": 0.001},
                temperature=1200.0,
                density=10.0,
            )

            channel = FuelChannel(
                id=1,
                position=Point3D(0.0, 0.0, 0.0),
                radius=0.5,
                height=100.0,
                material_region=mat_region,
            )

            assert channel.volume() > 0
            assert channel.id == 1
        except ImportError:
            pytest.skip("FuelChannel not available")

    def test_pebble_bed_total_volume(self):
        """Test PebbleBedCore methods."""
        try:
            from smrforge.geometry.core_geometry import PebbleBedCore

            core = PebbleBedCore(name="Test-Volume")
            core.build_structured_packing(
                core_height=200.0, core_diameter=100.0, pebble_radius=3.0
            )

            # Test that pebbles were created
            assert len(core.pebbles) > 0
            assert core.core_height == 200.0
            assert core.core_diameter == 100.0

            # Test that packing fraction is set
            assert 0 < core.packing_fraction <= 1.0
        except ImportError:
            pytest.skip("PebbleBedCore not available")
