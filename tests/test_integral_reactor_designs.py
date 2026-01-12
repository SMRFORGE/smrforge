"""
Tests for integral reactor design components (in-vessel steam generators).

Tests in-vessel steam generators and integrated primary systems for SMRs.
"""

import pytest
import numpy as np

try:
    from smrforge.geometry.lwr_smr import (
        InVesselSteamGenerator,
        IntegratedPrimarySystem,
        PWRSMRCore,
        SteamGeneratorTube,
        Point3D,
    )

    _INTEGRAL_DESIGNS_AVAILABLE = True
except ImportError:
    _INTEGRAL_DESIGNS_AVAILABLE = False


@pytest.mark.skipif(
    not _INTEGRAL_DESIGNS_AVAILABLE,
    reason="Integral reactor design components not available",
)
class TestSteamGeneratorTube:
    """Tests for SteamGeneratorTube class."""

    def test_tube_creation(self):
        """Test creating a steam generator tube."""
        tube = SteamGeneratorTube(
            id=1,
            position=Point3D(0, 0, 0),
            outer_diameter=1.9,
            inner_diameter=1.7,
            length=600.0,
        )

        assert tube.id == 1
        assert tube.outer_diameter == 1.9
        assert tube.inner_diameter == 1.7
        assert tube.length == 600.0
        assert tube.tube_type == "U-tube"
        assert tube.material == "Inconel-690"

    def test_flow_areas(self):
        """Test flow area calculations."""
        tube = SteamGeneratorTube(
            id=1,
            position=Point3D(0, 0, 0),
            outer_diameter=1.9,
            inner_diameter=1.7,
            length=600.0,
        )

        primary_area = tube.flow_area_primary()
        secondary_area = tube.flow_area_secondary()

        assert primary_area > 0
        assert secondary_area > 0
        assert secondary_area < primary_area  # Inner < outer

    def test_heat_transfer_area(self):
        """Test heat transfer area calculation."""
        tube = SteamGeneratorTube(
            id=1,
            position=Point3D(0, 0, 0),
            outer_diameter=1.9,
            inner_diameter=1.7,
            length=600.0,
        )

        area = tube.heat_transfer_area()
        expected = np.pi * 1.9 * 600.0

        assert area == pytest.approx(expected)


@pytest.mark.skipif(
    not _INTEGRAL_DESIGNS_AVAILABLE,
    reason="Integral reactor design components not available",
)
class TestInVesselSteamGenerator:
    """Tests for InVesselSteamGenerator class."""

    def test_steam_generator_creation(self):
        """Test creating an in-vessel steam generator."""
        sg = InVesselSteamGenerator(
            id=1,
            position=Point3D(0, 0, 1000),
            n_tubes=1000,
            tube_bundle_diameter=200.0,
            height=600.0,
        )

        assert sg.id == 1
        assert sg.n_tubes == 1000
        assert sg.tube_bundle_diameter == 200.0
        assert sg.height == 600.0
        assert len(sg.tubes) == 0

    def test_build_tube_bundle(self):
        """Test building a tube bundle."""
        sg = InVesselSteamGenerator(
            id=1,
            position=Point3D(0, 0, 1000),
            n_tubes=100,
            tube_bundle_diameter=50.0,
            height=100.0,
        )

        sg.build_tube_bundle(
            tube_outer_diameter=1.9,
            tube_inner_diameter=1.7,
            tube_length=600.0,
            tube_pitch=2.5,
        )

        assert len(sg.tubes) > 0
        assert len(sg.tubes) <= sg.n_tubes

    def test_total_heat_transfer_area(self):
        """Test total heat transfer area calculation."""
        sg = InVesselSteamGenerator(
            id=1,
            position=Point3D(0, 0, 1000),
            n_tubes=10,
            tube_bundle_diameter=20.0,
            height=30.0,
        )

        sg.build_tube_bundle(tube_length=100.0)

        total_area = sg.total_heat_transfer_area()
        assert total_area > 0

        # Should be sum of individual tube areas
        tube_area_sum = sum(tube.heat_transfer_area() for tube in sg.tubes)
        assert total_area == pytest.approx(tube_area_sum)

    def test_temperature_properties(self):
        """Test temperature and pressure properties."""
        sg = InVesselSteamGenerator(
            id=1,
            position=Point3D(0, 0, 1000),
            n_tubes=100,
            tube_bundle_diameter=50.0,
            height=100.0,
            primary_inlet_temp=573.15,
            primary_outlet_temp=523.15,
            secondary_pressure=6.0e6,
        )

        assert sg.primary_inlet_temp > sg.primary_outlet_temp
        assert sg.secondary_pressure > 0


@pytest.mark.skipif(
    not _INTEGRAL_DESIGNS_AVAILABLE,
    reason="Integral reactor design components not available",
)
class TestIntegratedPrimarySystem:
    """Tests for IntegratedPrimarySystem class."""

    def test_system_creation(self):
        """Test creating an integrated primary system."""
        system = IntegratedPrimarySystem(
            name="CAREM-25",
            vessel_diameter=300.0,
            vessel_height=2000.0,
        )

        assert system.name == "CAREM-25"
        assert system.vessel_diameter == 300.0
        assert system.vessel_height == 2000.0
        assert len(system.steam_generators) == 0
        assert system.integrated_pressurizer is True

    def test_vessel_volume(self):
        """Test vessel volume calculation."""
        system = IntegratedPrimarySystem(
            name="Test",
            vessel_diameter=300.0,
            vessel_height=2000.0,
        )

        volume = system.vessel_volume()
        expected = np.pi * (300.0 / 2) ** 2 * 2000.0

        assert volume == pytest.approx(expected)

    def test_add_steam_generator(self):
        """Test adding steam generators."""
        system = IntegratedPrimarySystem(
            name="Test",
            vessel_diameter=300.0,
            vessel_height=2000.0,
        )

        sg1 = InVesselSteamGenerator(
            id=1,
            position=Point3D(0, 0, 1500),
            n_tubes=100,
            tube_bundle_diameter=50.0,
            height=100.0,
        )

        sg2 = InVesselSteamGenerator(
            id=2,
            position=Point3D(0, 0, 1600),
            n_tubes=100,
            tube_bundle_diameter=50.0,
            height=100.0,
        )

        system.add_steam_generator(sg1)
        system.add_steam_generator(sg2)

        assert len(system.steam_generators) == 2

    def test_total_heat_transfer(self):
        """Test total heat transfer calculation."""
        system = IntegratedPrimarySystem(
            name="Test",
            vessel_diameter=300.0,
            vessel_height=2000.0,
        )

        sg1 = InVesselSteamGenerator(
            id=1,
            position=Point3D(0, 0, 1500),
            n_tubes=100,
            tube_bundle_diameter=50.0,
            height=100.0,
            heat_transfer_rate=10e6,  # 10 MW
        )

        sg2 = InVesselSteamGenerator(
            id=2,
            position=Point3D(0, 0, 1600),
            n_tubes=100,
            tube_bundle_diameter=50.0,
            height=100.0,
            heat_transfer_rate=15e6,  # 15 MW
        )

        system.add_steam_generator(sg1)
        system.add_steam_generator(sg2)

        total_heat = system.total_steam_generator_heat_transfer()
        assert total_heat == pytest.approx(25e6)  # 25 MW total

    def test_get_steam_generators_by_position(self):
        """Test getting steam generators by z-position."""
        system = IntegratedPrimarySystem(
            name="Test",
            vessel_diameter=300.0,
            vessel_height=2000.0,
        )

        sg1 = InVesselSteamGenerator(
            id=1,
            position=Point3D(0, 0, 1000),
            n_tubes=100,
            tube_bundle_diameter=50.0,
            height=100.0,
        )

        sg2 = InVesselSteamGenerator(
            id=2,
            position=Point3D(0, 0, 1500),
            n_tubes=100,
            tube_bundle_diameter=50.0,
            height=100.0,
        )

        system.add_steam_generator(sg1)
        system.add_steam_generator(sg2)

        # Get SGs in lower region
        lower_sgs = system.get_steam_generators_by_position(0, 1200)
        assert len(lower_sgs) == 1
        assert lower_sgs[0].id == 1

        # Get SGs in upper region
        upper_sgs = system.get_steam_generators_by_position(1400, 2000)
        assert len(upper_sgs) == 1
        assert upper_sgs[0].id == 2

    def test_integrated_system_with_core(self):
        """Test integrated system with core."""
        # Create core
        core = PWRSMRCore(name="Test-Core")
        core.build_square_lattice_core(
            n_assemblies_x=3,
            n_assemblies_y=3,
            lattice_size=17,
        )

        # Create integrated system
        system = IntegratedPrimarySystem(
            name="CAREM-25",
            vessel_diameter=300.0,
            vessel_height=2000.0,
            core=core,
        )

        assert system.core is not None
        assert system.core.name == "Test-Core"
        assert len(system.core.assemblies) == 9

        # Add steam generator
        sg = InVesselSteamGenerator(
            id=1,
            position=Point3D(0, 0, 1500),
            n_tubes=100,
            tube_bundle_diameter=50.0,
            height=100.0,
        )
        system.add_steam_generator(sg)

        assert len(system.steam_generators) == 1
