"""Tests for Lattice and Universe geometry classes."""

import numpy as np
import pytest

from smrforge.geometry.lattice import (
    Lattice,
    LatticeType,
    Universe,
)


class TestUniverse:
    """Tests for Universe class."""

    def test_universe_init(self):
        """Test Universe initialization."""
        u = Universe(id=1, name="fuel")
        assert u.id == 1
        assert u.name == "fuel"

    def test_universe_add_cell(self):
        """Test adding cell to universe."""
        u = Universe(id=1)
        u.add_cell(1, material_id=10, region="-1")
        assert 1 in u.cells


class TestLattice:
    """Tests for Lattice class."""

    def test_rectangular_create(self):
        """Test create_rectangular factory."""
        lat = Lattice.create_rectangular(
            id=1, nx=3, ny=3, pitch_x=1.0, pitch_y=1.0, universe_id=10
        )
        assert lat.lattice_type == LatticeType.RECTANGULAR
        assert lat.universes.shape == (3, 3)
        assert lat.get_universe_id(1, 1) == 10

    def test_get_position_rectangular(self):
        """Test get_position for rectangular lattice."""
        lat = Lattice.create_rectangular(
            id=1, nx=2, ny=2, pitch_x=10.0, pitch_y=10.0, universe_id=1
        )
        x, y = lat.get_position(0, 0)
        assert x == 5.0
        assert y == 5.0
