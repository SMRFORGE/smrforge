"""
Tests for Fast Reactor SMR geometry classes.

Tests sodium-cooled fast reactor geometry, wire-wrap spacers, and hexagonal assemblies.
"""

import numpy as np
import pytest

try:
    from smrforge.geometry.core_geometry import MaterialRegion, Point3D
    from smrforge.geometry.fast_reactor_smr import (
        FastReactorAssembly,
        FastReactorFuelPin,
        FastReactorSMRCore,
        FastReactorType,
        LiquidMetalChannel,
        WireWrapSpacer,
    )

    _FAST_REACTOR_SMR_AVAILABLE = True
except ImportError:
    _FAST_REACTOR_SMR_AVAILABLE = False


@pytest.mark.skipif(
    not _FAST_REACTOR_SMR_AVAILABLE,
    reason="Fast Reactor SMR geometry not available",
)
class TestWireWrapSpacer:
    """Tests for WireWrapSpacer class."""

    def test_wire_wrap_creation(self):
        """Test creating a wire-wrap spacer."""
        wire_wrap = WireWrapSpacer(
            id=1,
            wire_diameter=0.1,
            wire_pitch=30.0,
            height=100.0,
        )

        assert wire_wrap.id == 1
        assert wire_wrap.wire_diameter == 0.1
        assert wire_wrap.wire_pitch == 30.0
        assert wire_wrap.height == 100.0
        assert wire_wrap.wire_material == "StainlessSteel-316"

    def test_wire_length(self):
        """Test wire length calculation."""
        wire_wrap = WireWrapSpacer(
            id=1,
            wire_diameter=0.1,
            wire_pitch=30.0,
        )

        length = wire_wrap.wire_length(pin_height=100.0)
        assert length > 0.0

        # Longer pin should have longer wire
        length2 = wire_wrap.wire_length(pin_height=200.0)
        assert length2 > length


@pytest.mark.skipif(
    not _FAST_REACTOR_SMR_AVAILABLE,
    reason="Fast Reactor SMR geometry not available",
)
class TestFastReactorFuelPin:
    """Tests for FastReactorFuelPin class."""

    def test_fuel_pin_creation(self):
        """Test creating a fast reactor fuel pin."""
        fuel_mat = MaterialRegion(
            material_id="MOX",
            composition={"Pu239": 0.15, "U238": 0.85},
            temperature=900.0,
            density=10.0,
        )
        clad_mat = MaterialRegion(
            material_id="SS316",
            composition={"Fe": 0.70, "Cr": 0.18, "Ni": 0.12},
            temperature=700.0,
            density=8.0,
        )

        pin = FastReactorFuelPin(
            id=1,
            position=Point3D(0, 0, 0),
            fuel_radius=0.3,
            cladding_radius=0.35,
            height=100.0,
            material_fuel=fuel_mat,
            material_clad=clad_mat,
        )

        assert pin.id == 1
        assert pin.fuel_radius == 0.3
        assert pin.cladding_radius == 0.35
        assert pin.enrichment == 0.0

    def test_fuel_pin_volume(self):
        """Test fuel pin volume calculations."""
        fuel_mat = MaterialRegion(
            material_id="MOX", composition={}, temperature=900.0, density=10.0
        )
        clad_mat = MaterialRegion(
            material_id="SS316", composition={}, temperature=700.0, density=8.0
        )

        pin = FastReactorFuelPin(
            id=1,
            position=Point3D(0, 0, 0),
            fuel_radius=0.3,
            cladding_radius=0.35,
            height=100.0,
            material_fuel=fuel_mat,
            material_clad=clad_mat,
        )

        fuel_vol = pin.fuel_volume()
        expected = np.pi * 0.3**2 * 100.0
        assert abs(fuel_vol - expected) < 1e-6


@pytest.mark.skipif(
    not _FAST_REACTOR_SMR_AVAILABLE,
    reason="Fast Reactor SMR geometry not available",
)
class TestFastReactorAssembly:
    """Tests for FastReactorAssembly class."""

    def test_assembly_creation(self):
        """Test creating a fast reactor assembly."""
        assembly = FastReactorAssembly(
            id=1,
            position=Point3D(0, 0, 0),
            flat_to_flat=15.0,
            height=100.0,
            n_pins=127,  # Typical SFR assembly
            pin_pitch=0.8,
        )

        assert assembly.id == 1
        assert assembly.flat_to_flat == 15.0
        assert assembly.n_pins == 127
        assert len(assembly.fuel_pins) == 0

    def test_build_hexagonal_lattice(self):
        """Test building hexagonal lattice of fuel pins."""
        fuel_mat = MaterialRegion(
            material_id="MOX", composition={}, temperature=900.0, density=10.0
        )
        clad_mat = MaterialRegion(
            material_id="SS316", composition={}, temperature=700.0, density=8.0
        )
        coolant_mat = MaterialRegion(
            material_id="sodium",
            composition={"Na": 1.0},
            temperature=773.15,
            density=0.85,
        )

        assembly = FastReactorAssembly(
            id=1,
            position=Point3D(0, 0, 0),
            flat_to_flat=15.0,
            height=100.0,
            n_pins=19,  # Small for testing
            pin_pitch=0.8,
        )

        fuel_pin_params = {
            "fuel_radius": 0.3,
            "cladding_radius": 0.35,
            "material_fuel": fuel_mat,
            "material_clad": clad_mat,
        }

        assembly.build_hexagonal_lattice(fuel_pin_params, coolant_mat)

        assert len(assembly.fuel_pins) > 0
        assert len(assembly.fuel_pins) <= assembly.n_pins

        # Check that pins have wire-wrap
        if assembly.wire_wrap_pitch > 0:
            assert any(pin.wire_wrap is not None for pin in assembly.fuel_pins)

    def test_total_fuel_volume(self):
        """Test total fuel volume calculation."""
        fuel_mat = MaterialRegion(
            material_id="MOX", composition={}, temperature=900.0, density=10.0
        )
        clad_mat = MaterialRegion(
            material_id="SS316", composition={}, temperature=700.0, density=8.0
        )
        coolant_mat = MaterialRegion(
            material_id="sodium", composition={}, temperature=773.15, density=0.85
        )

        assembly = FastReactorAssembly(
            id=1,
            position=Point3D(0, 0, 0),
            flat_to_flat=15.0,
            height=100.0,
            n_pins=19,
            pin_pitch=0.8,
        )

        fuel_pin_params = {
            "fuel_radius": 0.3,
            "cladding_radius": 0.35,
            "material_fuel": fuel_mat,
            "material_clad": clad_mat,
        }

        assembly.build_hexagonal_lattice(fuel_pin_params, coolant_mat)

        total_vol = assembly.total_fuel_volume()
        assert total_vol > 0

        # Should be sum of pin volumes
        pin_vol_sum = sum(pin.fuel_volume() for pin in assembly.fuel_pins)
        assert abs(total_vol - pin_vol_sum) < 1e-6


@pytest.mark.skipif(
    not _FAST_REACTOR_SMR_AVAILABLE,
    reason="Fast Reactor SMR geometry not available",
)
class TestFastReactorSMRCore:
    """Tests for FastReactorSMRCore class."""

    def test_core_creation(self):
        """Test creating a fast reactor SMR core."""
        core = FastReactorSMRCore(name="Natrium-345MWe")

        assert core.name == "Natrium-345MWe"
        assert core.reactor_type == FastReactorType.SODIUM_COOLED
        assert len(core.assemblies) == 0

    def test_build_hexagonal_core_lattice(self):
        """Test building hexagonal core lattice."""
        fuel_mat = MaterialRegion(
            material_id="MOX", composition={}, temperature=900.0, density=10.0
        )
        clad_mat = MaterialRegion(
            material_id="SS316", composition={}, temperature=700.0, density=8.0
        )
        coolant_mat = MaterialRegion(
            material_id="sodium", composition={}, temperature=773.15, density=0.85
        )

        core = FastReactorSMRCore(name="Test-SFR")
        core.build_hexagonal_core_lattice(
            n_rings=2,  # Small for testing
            assembly_pitch=20.0,
            assembly_height=100.0,
            assembly_flat_to_flat=15.0,
            n_pins_per_assembly=19,
            pin_pitch=0.8,
            fuel_pin_params={
                "fuel_radius": 0.3,
                "cladding_radius": 0.35,
                "material_fuel": fuel_mat,
                "material_clad": clad_mat,
            },
            coolant_material=coolant_mat,
        )

        assert len(core.assemblies) > 0
        assert core.core_height == 100.0
        assert core.assembly_pitch == 20.0

    def test_core_fuel_volume(self):
        """Test core fuel volume calculation."""
        fuel_mat = MaterialRegion(
            material_id="MOX", composition={}, temperature=900.0, density=10.0
        )
        clad_mat = MaterialRegion(
            material_id="SS316", composition={}, temperature=700.0, density=8.0
        )
        coolant_mat = MaterialRegion(
            material_id="sodium", composition={}, temperature=773.15, density=0.85
        )

        core = FastReactorSMRCore(name="Test-SFR")
        core.build_hexagonal_core_lattice(
            n_rings=1,
            assembly_pitch=20.0,
            assembly_height=100.0,
            assembly_flat_to_flat=15.0,
            n_pins_per_assembly=7,  # Small for testing
            pin_pitch=0.8,
            fuel_pin_params={
                "fuel_radius": 0.3,
                "cladding_radius": 0.35,
                "material_fuel": fuel_mat,
                "material_clad": clad_mat,
            },
            coolant_material=coolant_mat,
        )

        total_vol = core.total_fuel_volume()
        assert total_vol > 0

        # Should be sum of assembly volumes
        assembly_vol_sum = sum(a.total_fuel_volume() for a in core.assemblies)
        assert abs(total_vol - assembly_vol_sum) < 1e-6


@pytest.mark.skipif(
    not _FAST_REACTOR_SMR_AVAILABLE,
    reason="Fast Reactor SMR geometry not available",
)
class TestLiquidMetalChannel:
    """Tests for LiquidMetalChannel class."""

    def test_channel_creation(self):
        """Test creating a liquid metal channel."""
        channel = LiquidMetalChannel(
            id=1,
            position=Point3D(0, 0, 0),
            flow_area=10.0,
            height=100.0,
        )

        assert channel.id == 1
        assert channel.flow_area == 10.0
        assert channel.temperature == 773.15  # Default SFR temperature
        assert channel.coolant_type == "sodium"
