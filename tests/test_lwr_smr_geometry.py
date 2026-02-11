"""
Tests for LWR SMR geometry classes.

Tests square lattice fuel assemblies, fuel rods, and PWR SMR core geometry.
"""

import numpy as np
import pytest

try:
    from smrforge.geometry.core_geometry import MaterialRegion, Point3D
    from smrforge.geometry.lwr_smr import (
        AssemblyType,
        BWRSMRCore,
        ControlBlade,
        ControlRodCluster,
        FuelAssembly,
        FuelRod,
        PWRSMRCore,
        SpacerGrid,
        WaterChannel,
    )

    _LWR_SMR_AVAILABLE = True
except ImportError:
    _LWR_SMR_AVAILABLE = False


@pytest.mark.skipif(not _LWR_SMR_AVAILABLE, reason="LWR SMR geometry not available")
class TestFuelRod:
    """Tests for FuelRod class."""

    def test_fuel_rod_creation(self):
        """Test creating a fuel rod."""
        position = Point3D(0.0, 0.0, 0.0)
        rod = FuelRod(
            id=1,
            position=position,
            fuel_radius=0.4,
            cladding_radius=0.48,
            height=365.76,
            enrichment=0.045,
        )

        assert rod.id == 1
        assert rod.fuel_radius == 0.4
        assert rod.cladding_radius == 0.48
        assert rod.enrichment == 0.045
        assert rod.height == 365.76

    def test_fuel_rod_volume(self):
        """Test fuel rod volume calculations."""
        rod = FuelRod(
            id=1,
            position=Point3D(0, 0, 0),
            fuel_radius=0.4,
            cladding_radius=0.48,
            height=100.0,
        )

        fuel_vol = rod.fuel_volume()
        expected_fuel_vol = np.pi * 0.4**2 * 100.0
        assert abs(fuel_vol - expected_fuel_vol) < 1e-6

        cladding_vol = rod.cladding_volume()
        inner_radius = 0.4 + 0.0082  # fuel_radius + gap
        expected_cladding_vol = np.pi * (0.48**2 - inner_radius**2) * 100.0
        assert abs(cladding_vol - expected_cladding_vol) < 1e-6

        total_vol = rod.total_volume()
        expected_total = np.pi * 0.48**2 * 100.0
        assert abs(total_vol - expected_total) < 1e-6

    def test_fuel_rod_power(self):
        """Test fuel rod power calculation."""
        rod = FuelRod(
            id=1,
            position=Point3D(0, 0, 0),
            fuel_radius=0.4,
            cladding_radius=0.48,
            height=100.0,
            power_density=100.0,  # W/cm³
        )

        power = rod.power()
        fuel_vol = rod.fuel_volume()
        expected_power = 100.0 * fuel_vol
        assert abs(power - expected_power) < 1e-6


@pytest.mark.skipif(not _LWR_SMR_AVAILABLE, reason="LWR SMR geometry not available")
class TestFuelAssembly:
    """Tests for FuelAssembly class."""

    def test_fuel_assembly_creation(self):
        """Test creating a fuel assembly."""
        assembly = FuelAssembly(
            id=1,
            position=Point3D(0, 0, 0),
            lattice_size=17,
            pitch=1.26,
            height=365.76,
        )

        assert assembly.id == 1
        assert assembly.lattice_size == 17
        assert assembly.pitch == 1.26
        assert assembly.height == 365.76
        assert assembly.assembly_type == AssemblyType.FUEL

    def test_fuel_assembly_build_square_lattice(self):
        """Test building square lattice of fuel rods."""
        assembly = FuelAssembly(
            id=1,
            position=Point3D(0, 0, 0),
            lattice_size=5,  # Small for testing
            pitch=1.26,
            height=100.0,
        )

        assembly.build_square_lattice()

        # Should have 5x5 = 25 rod positions
        # But guide tubes might reduce this
        assert len(assembly.fuel_rods) > 0
        assert len(assembly.fuel_rods) <= 25

    def test_fuel_assembly_with_guide_tubes(self):
        """Test assembly with guide tube positions."""
        assembly = FuelAssembly(
            id=1,
            position=Point3D(0, 0, 0),
            lattice_size=5,
            pitch=1.26,
            height=100.0,
        )

        # Define guide tube positions (corners)
        guide_tubes = [(0, 0), (0, 4), (4, 0), (4, 4)]
        assembly.build_square_lattice(guide_tube_positions=guide_tubes)

        # Should have guide tubes at specified positions
        assert len(assembly.guide_tubes) == 4
        # Should have fewer fuel rods (25 - 4 = 21)
        assert len(assembly.fuel_rods) == 21

    def test_fuel_assembly_volume(self):
        """Test fuel assembly volume calculations."""
        assembly = FuelAssembly(
            id=1,
            position=Point3D(0, 0, 0),
            lattice_size=3,
            pitch=1.26,
            height=100.0,
        )

        assembly.build_square_lattice()

        total_vol = assembly.total_fuel_volume()
        assert total_vol > 0

        # Check that volume is sum of rod volumes
        rod_vol_sum = sum(rod.fuel_volume() for rod in assembly.fuel_rods)
        assert abs(total_vol - rod_vol_sum) < 1e-6

    def test_fuel_assembly_power(self):
        """Test fuel assembly power calculation."""
        assembly = FuelAssembly(
            id=1,
            position=Point3D(0, 0, 0),
            lattice_size=3,
            pitch=1.26,
            height=100.0,
        )

        assembly.build_square_lattice()

        # Set power density on rods
        for rod in assembly.fuel_rods:
            rod.power_density = 50.0  # W/cm³

        total_power = assembly.total_power()
        assert total_power > 0

        # Check that power is sum of rod powers
        rod_power_sum = sum(rod.power() for rod in assembly.fuel_rods)
        assert abs(total_power - rod_power_sum) < 1e-6

    def test_fuel_assembly_pitch(self):
        """Test assembly pitch calculation."""
        assembly = FuelAssembly(
            id=1,
            position=Point3D(0, 0, 0),
            lattice_size=17,
            pitch=1.26,
        )

        pitch = assembly.assembly_pitch()
        # Should be approximately lattice_size * pitch * 1.1
        expected = 17 * 1.26 * 1.1
        assert abs(pitch - expected) < 1e-6


@pytest.mark.skipif(not _LWR_SMR_AVAILABLE, reason="LWR SMR geometry not available")
class TestPWRSMRCore:
    """Tests for PWRSMRCore class."""

    def test_pwr_smr_core_creation(self):
        """Test creating a PWR SMR core."""
        core = PWRSMRCore(name="Test-PWR-SMR")

        assert core.name == "Test-PWR-SMR"
        assert len(core.assemblies) == 0
        assert len(core.control_rod_clusters) == 0

    def test_build_square_lattice_core(self):
        """Test building square lattice core."""
        core = PWRSMRCore(name="Test-Core")
        core.build_square_lattice_core(
            n_assemblies_x=3,
            n_assemblies_y=3,
            assembly_pitch=21.5,
            assembly_height=365.76,
            lattice_size=17,
            rod_pitch=1.26,
        )

        assert len(core.assemblies) == 9  # 3x3 = 9 assemblies
        assert core.n_assemblies == 9
        assert core.core_height == 365.76
        assert core.assembly_pitch == 21.5

    def test_core_dimensions(self):
        """Test core dimension calculations."""
        core = PWRSMRCore(name="Test-Core")
        core.build_square_lattice_core(
            n_assemblies_x=4,
            n_assemblies_y=4,
            assembly_pitch=21.5,
        )

        # Core diameter should be approximately n_assemblies * pitch
        expected_diameter = 4 * 21.5
        assert abs(core.core_diameter - expected_diameter) < 1.0  # Allow some tolerance

    def test_core_fuel_volume(self):
        """Test core fuel volume calculation."""
        core = PWRSMRCore(name="Test-Core")
        core.build_square_lattice_core(
            n_assemblies_x=2,
            n_assemblies_y=2,
            lattice_size=5,  # Small for testing
        )

        total_vol = core.total_fuel_volume()
        assert total_vol > 0

        # Should be sum of assembly volumes
        assembly_vol_sum = sum(a.total_fuel_volume() for a in core.assemblies)
        assert abs(total_vol - assembly_vol_sum) < 1e-6

    def test_core_power(self):
        """Test core power calculation."""
        core = PWRSMRCore(name="Test-Core")
        core.build_square_lattice_core(
            n_assemblies_x=2,
            n_assemblies_y=2,
            lattice_size=5,
        )

        # Set power density on rods
        for assembly in core.assemblies:
            for rod in assembly.fuel_rods:
                rod.power_density = 30.0  # W/cm³

        total_power = core.total_power()
        assert total_power > 0

        # Should be sum of assembly powers
        assembly_power_sum = sum(a.total_power() for a in core.assemblies)
        assert abs(total_power - assembly_power_sum) < 1e-6

    def test_generate_mesh(self):
        """Test mesh generation."""
        core = PWRSMRCore(name="Test-Core")
        core.build_square_lattice_core(
            n_assemblies_x=3,
            n_assemblies_y=3,
        )

        core.generate_mesh(n_radial=10, n_axial=20)

        assert core.radial_mesh is not None
        assert core.axial_mesh is not None
        assert len(core.radial_mesh) == 11  # n_radial + 1
        assert len(core.axial_mesh) == 21  # n_axial + 1

    def test_to_dataframe(self):
        """Test DataFrame export."""
        core = PWRSMRCore(name="Test-Core")
        core.build_square_lattice_core(
            n_assemblies_x=2,
            n_assemblies_y=2,
            lattice_size=5,
        )

        df = core.to_dataframe()

        assert len(df) == 4  # 2x2 = 4 assemblies
        assert "assembly_id" in df.columns
        assert "x" in df.columns
        assert "y" in df.columns
        assert "n_rods" in df.columns


@pytest.mark.skipif(not _LWR_SMR_AVAILABLE, reason="LWR SMR geometry not available")
class TestWaterChannel:
    """Tests for WaterChannel class."""

    def test_water_channel_creation(self):
        """Test creating a water channel."""
        channel = WaterChannel(
            id=1,
            position=Point3D(0, 0, 0),
            flow_area=10.0,
            height=365.76,
        )

        assert channel.id == 1
        assert channel.flow_area == 10.0
        assert channel.height == 365.76
        assert channel.temperature == 573.15  # Default
        assert channel.pressure == 15.5e6  # Default PWR pressure


@pytest.mark.skipif(not _LWR_SMR_AVAILABLE, reason="LWR SMR geometry not available")
class TestControlRodCluster:
    """Tests for ControlRodCluster class."""

    def test_control_rod_cluster_creation(self):
        """Test creating a control rod cluster."""
        cluster = ControlRodCluster(
            id=1,
            position=Point3D(0, 0, 0),
            n_rods=20,
        )

        assert cluster.id == 1
        assert cluster.n_rods == 20
        assert cluster.insertion == 0.0  # Fully withdrawn
        assert cluster.worth == 0.0


@pytest.mark.skipif(not _LWR_SMR_AVAILABLE, reason="LWR SMR geometry not available")
class TestControlBlade:
    """Tests for ControlBlade class."""

    def test_control_blade_creation(self):
        """Test creating a control blade."""
        blade = ControlBlade(
            id=1,
            position=Point3D(0, 0, 0),
        )

        assert blade.id == 1
        assert blade.width == 5.0  # Default
        assert blade.insertion == 0.0
        assert blade.worth == 0.0
