"""Tests for parametric geometry builders (Community tier)."""

import pytest


class TestParametricBuilders:
    """Tests for parametric_builders module."""

    def test_create_fuel_pin(self):
        """create_fuel_pin returns FuelChannel with expected dimensions."""
        from smrforge.geometry.parametric_builders import create_fuel_pin

        pin = create_fuel_pin(radius=0.41, height=200.0)
        assert pin.radius == 0.41
        assert pin.height == 200.0
        assert pin.id == 0
        assert pin.position.x == 0.0 and pin.position.y == 0.0

    def test_create_moderator_block(self):
        """create_moderator_block returns GraphiteBlock."""
        from smrforge.geometry.parametric_builders import create_moderator_block

        block = create_moderator_block(flat_to_flat=36.0, height=80.0)
        assert block.flat_to_flat == 36.0
        assert block.height == 80.0
        assert block.block_type == "reflector"

    def test_create_rectangular_fuel_lattice(self):
        """create_rectangular_fuel_lattice returns list of fuel pins."""
        from smrforge.geometry.parametric_builders import create_rectangular_fuel_lattice

        pins = create_rectangular_fuel_lattice(nx=5, ny=5, pitch=1.26)
        assert len(pins) == 25
        assert pins[0].radius == 0.41

    def test_create_simple_prismatic_core(self):
        """create_simple_prismatic_core returns PrismaticCore with blocks."""
        from smrforge.geometry.parametric_builders import create_simple_prismatic_core

        core = create_simple_prismatic_core(n_rings=2)
        assert len(core.blocks) == 7  # 1 center + 6 ring 1
        assert core.core_height == 80.0
        assert core.core_diameter > 0
