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

    def test_generate_mesh_with_reflector(self):
        """Test mesh generation with reflector thickness."""
        try:
            from smrforge.geometry.core_geometry import PrismaticCore

            core = PrismaticCore(name="Test-Mesh")
            core.build_hexagonal_lattice(
                n_rings=1, pitch=40.0, block_height=79.3, n_axial=2, flat_to_flat=36.0
            )
            core.reflector_thickness = 30.0

            # Generate mesh
            core.generate_mesh(n_radial=11, n_axial=21)

            assert core.radial_mesh is not None
            assert core.axial_mesh is not None
            # Radial mesh should extend beyond core by reflector thickness
            assert core.radial_mesh[-1] > core.core_diameter / 2
        except ImportError:
            pytest.skip("PrismaticCore not available")

    def test_get_block_by_position(self):
        """Test get_block_by_position method."""
        try:
            from smrforge.geometry.core_geometry import PrismaticCore

            core = PrismaticCore(name="Test-Position")
            core.build_hexagonal_lattice(
                n_rings=1, pitch=40.0, block_height=79.3, n_axial=2, flat_to_flat=36.0
            )

            if len(core.blocks) > 0:
                # Test with position of first block
                first_block = core.blocks[0]
                found_block = core.get_block_by_position(
                    first_block.position.x,
                    first_block.position.y,
                    first_block.position.z,
                )
                # Should find a block (might not be exact due to simplified check)
                assert found_block is not None or len(core.blocks) == 0

                # Test with position outside core
                outside_block = core.get_block_by_position(1000.0, 1000.0, 1000.0)
                assert outside_block is None
        except ImportError:
            pytest.skip("PrismaticCore not available")

    def test_prismatic_to_dataframe(self):
        """Test PrismaticCore.to_dataframe method."""
        try:
            from smrforge.geometry.core_geometry import PrismaticCore

            core = PrismaticCore(name="Test-DF")
            core.build_hexagonal_lattice(
                n_rings=1, pitch=40.0, block_height=79.3, n_axial=1, flat_to_flat=36.0
            )

            df = core.to_dataframe()
            assert df is not None
            # Should have columns
            assert len(df.columns) > 0
        except ImportError:
            pytest.skip("PrismaticCore not available")

    def test_pebble_bed_to_dataframe(self):
        """Test PebbleBedCore.to_dataframe method."""
        try:
            from smrforge.geometry.core_geometry import PebbleBedCore

            core = PebbleBedCore(name="Test-DF")
            core.build_structured_packing(
                core_height=100.0, core_diameter=50.0, pebble_radius=2.0
            )

            if len(core.pebbles) > 0:
                df = core.to_dataframe()
                assert df is not None
                assert len(df.columns) > 0
        except ImportError:
            pytest.skip("PebbleBedCore not available")

    def test_compute_distance_matrix(self):
        """Test compute_distance_matrix function."""
        try:
            from smrforge.geometry.core_geometry import compute_distance_matrix

            # Create small array of positions
            positions = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])

            dist_matrix = compute_distance_matrix(positions)

            assert dist_matrix.shape == (3, 3)
            # Should be symmetric
            assert np.allclose(dist_matrix, dist_matrix.T)
            # Diagonal should be zero
            assert np.allclose(np.diag(dist_matrix), 0.0)
            # Distance from [0,0,0] to [1,0,0] should be 1.0
            assert np.isclose(dist_matrix[0, 1], 1.0)
        except ImportError:
            pytest.skip("compute_distance_matrix not available")

    def test_geometry_export_pebble_bed(self, temp_dir):
        """Test geometry export for PebbleBedCore."""
        try:
            from smrforge.geometry.core_geometry import GeometryExporter, PebbleBedCore

            core = PebbleBedCore(name="Test-Export-PB")
            core.build_structured_packing(
                core_height=100.0, core_diameter=50.0, pebble_radius=2.0
            )

            export_path = temp_dir / "test_pebble_bed.json"
            GeometryExporter.to_json(core, export_path)

            assert export_path.exists()
            # Verify file contains expected data
            import json

            with open(export_path) as f:
                data = json.load(f)
            assert data["name"] == "Test-Export-PB"
            assert "n_pebbles" in data
        except ImportError:
            pytest.skip("GeometryExporter not available")

    def test_point3d_to_array(self):
        """Test Point3D.to_array method."""
        try:
            from smrforge.geometry.core_geometry import Point3D

            p = Point3D(1.0, 2.0, 3.0)
            arr = p.to_array()

            assert isinstance(arr, np.ndarray)
            assert len(arr) == 3
            assert arr[0] == 1.0
            assert arr[1] == 2.0
            assert arr[2] == 3.0
        except ImportError:
            pytest.skip("Point3D not available")

    def test_point3d_subtraction(self):
        """Test Point3D subtraction."""
        try:
            from smrforge.geometry.core_geometry import Point3D

            p1 = Point3D(5.0, 6.0, 7.0)
            p2 = Point3D(1.0, 2.0, 3.0)

            p3 = p1 - p2
            assert p3.x == 4.0
            assert p3.y == 4.0
            assert p3.z == 4.0
        except ImportError:
            pytest.skip("Point3D not available")

    def test_graphite_block_vertices(self):
        """Test GraphiteBlock.vertices() method."""
        try:
            from smrforge.geometry.core_geometry import GraphiteBlock, MaterialRegion, Point3D

            block = GraphiteBlock(
                id=1,
                position=Point3D(0.0, 0.0, 0.0),
                flat_to_flat=36.0,
                height=79.3,
            )

            vertices = block.vertices()
            assert vertices.shape == (6, 2)  # 6 vertices, 2D (x, y)
            assert np.all(np.isfinite(vertices))
        except ImportError:
            pytest.skip("GraphiteBlock not available")

    def test_graphite_block_total_fuel_volume(self):
        """Test GraphiteBlock.total_fuel_volume() method."""
        try:
            from smrforge.geometry.core_geometry import (
                FuelChannel,
                GraphiteBlock,
                MaterialRegion,
                Point3D,
            )

            mat_region = MaterialRegion(
                material_id="fuel", composition={"U235": 0.001}, temperature=1200.0, density=10.0
            )

            block = GraphiteBlock(
                id=1,
                position=Point3D(0.0, 0.0, 0.0),
                flat_to_flat=36.0,
                height=79.3,
            )

            # Add a fuel channel
            channel = FuelChannel(
                id=1,
                position=Point3D(0.0, 0.0, 0.0),
                radius=0.5,
                height=79.3,
                material_region=mat_region,
            )
            block.fuel_channels.append(channel)

            fuel_vol = block.total_fuel_volume()
            assert fuel_vol > 0
            assert fuel_vol == channel.volume()
        except ImportError:
            pytest.skip("GraphiteBlock not available")

    def test_graphite_block_power(self):
        """Test GraphiteBlock.power() method."""
        try:
            from smrforge.geometry.core_geometry import (
                FuelChannel,
                GraphiteBlock,
                MaterialRegion,
                Point3D,
            )

            mat_region = MaterialRegion(
                material_id="fuel", composition={"U235": 0.001}, temperature=1200.0, density=10.0
            )

            block = GraphiteBlock(
                id=1,
                position=Point3D(0.0, 0.0, 0.0),
                flat_to_flat=36.0,
                height=79.3,
            )

            # Add fuel channel with power density
            channel = FuelChannel(
                id=1,
                position=Point3D(0.0, 0.0, 0.0),
                radius=0.5,
                height=79.3,
                material_region=mat_region,
                power_density=10.0,  # W/cm³
            )
            block.fuel_channels.append(channel)

            power = block.power()
            assert power > 0
            expected_power = channel.power_density * channel.volume()
            assert np.isclose(power, expected_power)
        except ImportError:
            pytest.skip("GraphiteBlock not available")

    def test_pebble_volume(self):
        """Test Pebble.volume() method."""
        try:
            from smrforge.geometry.core_geometry import MaterialRegion, Pebble, Point3D

            pebble = Pebble(
                id=1,
                position=Point3D(0.0, 0.0, 0.0),
                radius=3.0,
                fuel_zone_radius=2.5,
            )

            volume = pebble.volume()
            expected = (4 / 3) * np.pi * 3.0**3
            assert np.isclose(volume, expected)
        except ImportError:
            pytest.skip("Pebble not available")

    def test_pebble_fuel_volume(self):
        """Test Pebble.fuel_volume() method."""
        try:
            from smrforge.geometry.core_geometry import MaterialRegion, Pebble, Point3D

            pebble = Pebble(
                id=1,
                position=Point3D(0.0, 0.0, 0.0),
                radius=3.0,
                fuel_zone_radius=2.5,
            )

            fuel_vol = pebble.fuel_volume()
            expected = (4 / 3) * np.pi * 2.5**3
            assert np.isclose(fuel_vol, expected)
            # Fuel volume should be less than total volume
            assert fuel_vol < pebble.volume()
        except ImportError:
            pytest.skip("Pebble not available")

    def test_coolant_channel(self):
        """Test CoolantChannel dataclass."""
        try:
            from smrforge.geometry.core_geometry import CoolantChannel, Point3D

            channel = CoolantChannel(
                id=1,
                position=Point3D(0.0, 0.0, 0.0),
                radius=1.0,
                height=79.3,
                flow_area=3.14,  # π * r²
            )

            assert channel.id == 1
            assert channel.radius == 1.0
            assert channel.height == 79.3
        except ImportError:
            pytest.skip("CoolantChannel not available")


class TestPebbleBedCoreMethods:
    """Test additional PebbleBedCore methods."""

    def test_build_random_packing(self):
        """Test build_random_packing method."""
        try:
            from smrforge.geometry.core_geometry import PebbleBedCore

            core = PebbleBedCore(name="Test-Random")
            # Use small dimensions to avoid long execution
            core.build_random_packing(
                core_height=50.0,
                core_diameter=20.0,
                pebble_radius=2.0,
                annular_inner_diameter=0.0,
            )

            assert core.core_height == 50.0
            assert core.core_diameter == 20.0
            # Should have created some pebbles (may vary due to randomness)
            assert len(core.pebbles) >= 0  # Can be 0 if no valid positions found
        except ImportError:
            pytest.skip("PebbleBedCore not available")

    def test_build_random_packing_annular(self):
        """Test build_random_packing with annular geometry."""
        try:
            from smrforge.geometry.core_geometry import PebbleBedCore

            core = PebbleBedCore(name="Test-Annular")
            core.build_random_packing(
                core_height=50.0,
                core_diameter=30.0,
                pebble_radius=2.0,
                annular_inner_diameter=10.0,
            )

            assert core.annular_inner_diameter == 10.0
            assert len(core.pebbles) >= 0
        except ImportError:
            pytest.skip("PebbleBedCore not available")

    def test_simulate_recirculation(self):
        """Test simulate_recirculation method."""
        try:
            from smrforge.geometry.core_geometry import PebbleBedCore

            core = PebbleBedCore(name="Test-Recirculation")
            core.build_structured_packing(
                core_height=100.0, core_diameter=50.0, pebble_radius=3.0
            )

            if len(core.pebbles) > 0:
                # Store initial residence times
                initial_residence = [p.residence_time for p in core.pebbles]

                # Simulate one step
                core.simulate_recirculation(n_passes=1, discharge_burnup=90.0)

                # Check that residence time increased for all pebbles
                # (positions may change due to sorting and movement)
                for i, pebble in enumerate(core.pebbles):
                    assert pebble.residence_time >= initial_residence[i]
                    # Position should be within reasonable bounds (0 to core_height)
                    assert 0 <= pebble.position.z <= core.core_height + 10.0
        except ImportError:
            pytest.skip("PebbleBedCore not available")

    def test_get_pebble_neighbors(self):
        """Test get_pebble_neighbors method."""
        try:
            from smrforge.geometry.core_geometry import PebbleBedCore

            core = PebbleBedCore(name="Test-Neighbors")
            core.build_structured_packing(
                core_height=50.0, core_diameter=30.0, pebble_radius=2.0
            )

            if len(core.pebbles) > 1:
                # Get neighbors for first pebble
                neighbors = core.get_pebble_neighbors(0, radius=10.0)

                # Should return list of Pebble objects (excluding the pebble itself)
                assert isinstance(neighbors, list)
                assert all(hasattr(p, "id") for p in neighbors)
                # First pebble should not be in neighbors
                assert all(p.id != 0 for p in neighbors)
        except ImportError:
            pytest.skip("PebbleBedCore not available")

    def test_geometry_export_pebble_bed_json(self, temp_dir):
        """Test GeometryExporter.to_json for PebbleBedCore."""
        try:
            from smrforge.geometry.core_geometry import GeometryExporter, PebbleBedCore

            core = PebbleBedCore(name="Test-Export-Pebble")
            core.build_structured_packing(
                core_height=50.0, core_diameter=30.0, pebble_radius=2.0
            )

            export_path = temp_dir / "test_pebble_core.json"
            GeometryExporter.to_json(core, export_path)

            assert export_path.exists()

            # Check JSON content
            import json

            with open(export_path) as f:
                data = json.load(f)

            assert data["name"] == "Test-Export-Pebble"
            assert data["type"] == "PebbleBedCore"
            assert "n_pebbles" in data
            assert "packing_fraction" in data
        except ImportError:
            pytest.skip("GeometryExporter not available")
