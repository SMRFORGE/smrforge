"""
Tests for Molten Salt SMR geometry.

Tests molten salt channels, graphite blocks, freeze plugs, and MSR cores.
"""

import pytest
import numpy as np

try:
    from smrforge.geometry.molten_salt_smr import (
        FreezePlug,
        GraphiteModeratorBlock,
        MSRType,
        MSRSMRCore,
        MoltenSaltChannel,
        SaltCirculationLoop,
        create_liquid_fuel_msr_core,
        create_thermal_msr_core,
    )
    from smrforge.geometry.core_geometry import Point3D

    _MOLTEN_SALT_SMR_AVAILABLE = True
except ImportError:
    _MOLTEN_SALT_SMR_AVAILABLE = False


@pytest.mark.skipif(
    not _MOLTEN_SALT_SMR_AVAILABLE,
    reason="Molten salt SMR not available",
)
class TestMoltenSaltChannel:
    """Tests for MoltenSaltChannel class."""

    def test_channel_creation(self):
        """Test creating molten salt channel."""
        channel = MoltenSaltChannel(
            id=1,
            position=Point3D(0, 0, 0),
            inner_radius=5.0,  # cm
            outer_radius=5.5,  # cm
            height=400.0,  # cm
            salt_type="fuel_salt",
            fuel_dissolved=True,
        )

        assert channel.id == 1
        assert channel.inner_radius == 5.0
        assert channel.fuel_dissolved is True

    def test_flow_area(self):
        """Test flow area calculation."""
        channel = MoltenSaltChannel(
            id=1,
            position=Point3D(0, 0, 0),
            inner_radius=5.0,
            outer_radius=5.5,
            height=400.0,
        )

        area = channel.flow_area()
        expected = np.pi * 5.0 ** 2

        assert area == pytest.approx(expected)

    def test_volume(self):
        """Test volume calculation."""
        channel = MoltenSaltChannel(
            id=1,
            position=Point3D(0, 0, 0),
            inner_radius=5.0,
            outer_radius=5.5,
            height=400.0,
        )

        volume = channel.volume()
        expected = np.pi * 5.0 ** 2 * 400.0

        assert volume == pytest.approx(expected)

    def test_fuel_mass(self):
        """Test fuel mass calculation."""
        channel = MoltenSaltChannel(
            id=1,
            position=Point3D(0, 0, 0),
            inner_radius=5.0,
            outer_radius=5.5,
            height=400.0,
            fuel_dissolved=True,
            fuel_concentration=1.0,  # g/L
        )

        fuel_mass = channel.fuel_mass()
        assert fuel_mass > 0

        # Channel without fuel
        channel.fuel_dissolved = False
        assert channel.fuel_mass() == 0.0


@pytest.mark.skipif(
    not _MOLTEN_SALT_SMR_AVAILABLE,
    reason="Molten salt SMR not available",
)
class TestGraphiteModeratorBlock:
    """Tests for GraphiteModeratorBlock class."""

    def test_block_creation(self):
        """Test creating graphite moderator block."""
        block = GraphiteModeratorBlock(
            id=1,
            position=Point3D(0, 0, 0),
            shape="hexagonal",
            size=20.0,  # cm
            height=400.0,  # cm
        )

        assert block.id == 1
        assert block.shape == "hexagonal"
        assert block.size == 20.0

    def test_volume_hexagonal(self):
        """Test hexagonal volume calculation."""
        block = GraphiteModeratorBlock(
            id=1,
            position=Point3D(0, 0, 0),
            shape="hexagonal",
            size=20.0,
            height=400.0,
        )

        volume = block.volume()
        assert volume > 0

    def test_volume_square(self):
        """Test square volume calculation."""
        block = GraphiteModeratorBlock(
            id=1,
            position=Point3D(0, 0, 0),
            shape="square",
            size=20.0,
            height=400.0,
        )

        volume = block.volume()
        expected = 20.0 ** 2 * 400.0

        assert volume == pytest.approx(expected)

    def test_mass(self):
        """Test mass calculation."""
        block = GraphiteModeratorBlock(
            id=1,
            position=Point3D(0, 0, 0),
            shape="square",
            size=20.0,
            height=400.0,
            graphite_density=1.7,  # g/cm³
        )

        mass = block.mass()
        expected = 20.0 ** 2 * 400.0 * 1.7

        assert mass == pytest.approx(expected)


@pytest.mark.skipif(
    not _MOLTEN_SALT_SMR_AVAILABLE,
    reason="Molten salt SMR not available",
)
class TestFreezePlug:
    """Tests for FreezePlug class."""

    def test_plug_creation(self):
        """Test creating freeze plug."""
        plug = FreezePlug(
            id=1,
            position=Point3D(0, 0, 0),
            diameter=10.0,  # cm
            thickness=5.0,  # cm
        )

        assert plug.id == 1
        assert plug.is_frozen is True

    def test_check_melt_condition(self):
        """Test melt condition checking."""
        plug = FreezePlug(
            id=1,
            position=Point3D(0, 0, 0),
            diameter=10.0,
            thickness=5.0,
            melt_temperature=873.15,  # K
            current_temperature=733.15,  # K (frozen)
        )

        assert plug.check_melt_condition() is False  # Should be frozen

        # Increase temperature above melt point
        plug.current_temperature = 900.0  # K
        assert plug.check_melt_condition() is True  # Should melt

    def test_volume(self):
        """Test volume calculation."""
        plug = FreezePlug(
            id=1,
            position=Point3D(0, 0, 0),
            diameter=10.0,
            thickness=5.0,
        )

        volume = plug.volume()
        expected = np.pi * (10.0 / 2) ** 2 * 5.0

        assert volume == pytest.approx(expected)


@pytest.mark.skipif(
    not _MOLTEN_SALT_SMR_AVAILABLE,
    reason="Molten salt SMR not available",
)
class TestSaltCirculationLoop:
    """Tests for SaltCirculationLoop class."""

    def test_loop_creation(self):
        """Test creating salt circulation loop."""
        loop = SaltCirculationLoop(
            id=1,
            name="Primary Loop",
            loop_type="primary",
        )

        assert loop.id == 1
        assert loop.name == "Primary Loop"
        assert loop.loop_type == "primary"

    def test_total_volume(self):
        """Test total volume calculation."""
        loop = SaltCirculationLoop(id=1, name="Test Loop")

        # Add channels
        for i in range(3):
            channel = MoltenSaltChannel(
                id=i,
                position=Point3D(i * 10, 0, 0),
                inner_radius=5.0,
                outer_radius=5.5,
                height=400.0,
            )
            loop.channels.append(channel)

        total_volume = loop.total_volume()
        assert total_volume > 0


@pytest.mark.skipif(
    not _MOLTEN_SALT_SMR_AVAILABLE,
    reason="Molten salt SMR not available",
)
class TestMSRSMRCore:
    """Tests for MSRSMRCore class."""

    def test_core_creation(self):
        """Test creating MSR SMR core."""
        core = MSRSMRCore(name="Test-MSR")

        assert core.name == "Test-MSR"
        assert len(core.salt_channels) == 0

    def test_build_liquid_fuel_core(self):
        """Test building liquid fuel MSR core."""
        core = MSRSMRCore()
        core.build_liquid_fuel_core(
            n_channels=50,
            channel_radius=5.0,
            channel_pitch=15.0,
        )

        assert len(core.salt_channels) > 0
        assert core.msr_type == MSRType.LIQUID_FUEL
        assert all(ch.fuel_dissolved for ch in core.salt_channels)

    def test_build_thermal_msr_core(self):
        """Test building thermal MSR core."""
        core = MSRSMRCore()
        core.build_thermal_msr_core(
            n_blocks=19,
            block_size=20.0,
            n_channels_per_block=7,
        )

        assert len(core.graphite_blocks) > 0
        assert len(core.salt_channels) > 0
        assert core.msr_type == MSRType.THERMAL

    def test_get_total_fuel_mass(self):
        """Test getting total fuel mass."""
        core = MSRSMRCore()
        core.build_liquid_fuel_core(
            n_channels=10,
            fuel_concentration=1.0,  # g/L
        )

        total_mass = core.get_total_fuel_mass()
        assert total_mass > 0

    def test_get_total_salt_volume(self):
        """Test getting total salt volume."""
        core = MSRSMRCore()
        core.build_liquid_fuel_core(n_channels=10)

        total_volume = core.get_total_salt_volume()
        assert total_volume > 0

    def test_check_freeze_plugs(self):
        """Test checking freeze plug status."""
        core = MSRSMRCore()

        # Add freeze plug
        plug = FreezePlug(
            id=1,
            position=Point3D(0, 0, 0),
            diameter=10.0,
            thickness=5.0,
            current_temperature=900.0,  # K (above melt point)
        )
        core.add_freeze_plug(plug)

        status = core.check_freeze_plugs()
        assert 1 in status
        assert status[1] is True  # Should be melted


@pytest.mark.skipif(
    not _MOLTEN_SALT_SMR_AVAILABLE,
    reason="Molten salt SMR not available",
)
class TestPresetCores:
    """Tests for preset MSR core functions."""

    def test_create_liquid_fuel_msr_core(self):
        """Test creating liquid fuel MSR core."""
        core = create_liquid_fuel_msr_core()

        assert core.name == "Liquid-Fuel-MSR"
        assert core.msr_type == MSRType.LIQUID_FUEL
        assert len(core.salt_channels) > 0

    def test_create_thermal_msr_core(self):
        """Test creating thermal MSR core."""
        core = create_thermal_msr_core()

        assert core.name == "Thermal-MSR"
        assert core.msr_type == MSRType.THERMAL
        assert len(core.graphite_blocks) > 0
