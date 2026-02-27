"""
Lattice and Universe classes for full reactor core representation.

Provides MCNP/Serpent/OpenMC-style lattice and universe hierarchy
for assembly-level and pin-level geometry description.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.geometry.lattice")


class LatticeType(Enum):
    """Type of lattice arrangement."""

    RECTANGULAR = "rectangular"
    HEXAGONAL = "hexagonal"
    CYLINDRICAL = "cylindrical"


@dataclass
class Universe:
    """
    Universe: container for cells or other universes (MCNP/Serpent style).

    A universe can contain:
    - Direct cell definitions (material IDs, surfaces)
    - Fills referencing other universes (for nested structures)
    """

    id: int
    name: Optional[str] = None
    cells: Dict[int, Any] = field(default_factory=dict)  # cell_id -> cell data
    fills: Dict[Tuple[int, int], int] = field(
        default_factory=dict
    )  # (cell_id, instance) -> universe_id

    def add_cell(self, cell_id: int, material_id: int, region: Optional[str] = None) -> None:
        """Add a cell to this universe."""
        self.cells[cell_id] = {"material_id": material_id, "region": region}
        logger.debug(f"Universe {self.id}: added cell {cell_id}")

    def add_fill(self, cell_id: int, instance: int, universe_id: int) -> None:
        """Add fill (lattice/universe) to cell."""
        self.fills[(cell_id, instance)] = universe_id

    def __repr__(self) -> str:
        return f"Universe(id={self.id}, name={self.name}, cells={len(self.cells)})"


@dataclass
class Lattice:
    """
    Lattice: regular array of universes (assembly or core level).

    Supports rectangular, hexagonal, and cylindrical arrangements.
    Used for fuel assembly lattices and full core maps.
    """

    id: int
    lattice_type: LatticeType
    dimension: Tuple[int, ...]  # (nx, ny) or (nx, ny, nz) or (n_rings, nz)
    pitch: Tuple[float, ...]  # (pitch_x, pitch_y) or (pitch_r, pitch_z)
    lower_left: Tuple[float, ...]  # (x, y) or (x, y, z)
    universes: np.ndarray  # [..., universe_id] - maps lattice position to universe
    outer_universe_id: Optional[int] = None  # Universe outside lattice bounds
    name: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate dimension vs universes shape."""
        self.universes = np.asarray(self.universes)
        expected = np.prod(self.dimension)
        actual = self.universes.size
        if actual != expected:
            raise ValueError(
                f"Lattice {self.id}: universes size {actual} != "
                f"dimension product {expected}"
            )
        self.universes = self.universes.reshape(self.dimension)
        logger.debug(
            f"Lattice {self.id}: type={self.lattice_type.value}, "
            f"dim={self.dimension}, pitch={self.pitch}"
        )

    def get_universe_id(self, i: int, j: int = 0, k: int = 0) -> int:
        """
        Get universe ID at lattice indices.

        Args:
            i, j, k: Lattice indices (j,k optional for 1D)

        Returns:
            Universe ID, or outer_universe_id if out of bounds
        """
        d = self.dimension
        if len(d) == 1:
            if i < 0 or i >= d[0]:
                if self.outer_universe_id is not None:
                    return self.outer_universe_id
                raise IndexError(f"Lattice index {i} out of bounds")
            return int(self.universes.flat[i])
        if len(d) == 2:
            if i < 0 or i >= d[0] or j < 0 or j >= d[1]:
                if self.outer_universe_id is not None:
                    return self.outer_universe_id
                raise IndexError(f"Lattice index ({i},{j}) out of bounds")
            return int(self.universes[i, j])
        if i < 0 or i >= d[0] or j < 0 or j >= d[1] or k < 0 or k >= d[2]:
            if self.outer_universe_id is not None:
                return self.outer_universe_id
            raise IndexError(f"Lattice index ({i},{j},{k}) out of bounds")
        return int(self.universes[i, j, k])

    def get_position(self, i: int, j: int, k: int = 0) -> Tuple[float, ...]:
        """Get physical position (x, y) or (x, y, z) of lattice cell."""
        ll = self.lower_left
        p = self.pitch
        if self.lattice_type == LatticeType.HEXAGONAL:
            # Hexagonal offset
            x = ll[0] + p[0] * (i + 0.5 * (j % 2))
            y = ll[1] + p[1] * j * np.sqrt(3) / 2
            return (x, y) if len(ll) == 2 else (x, y, ll[2] + p[-1] * k)
        elif self.lattice_type == LatticeType.RECTANGULAR:
            x = ll[0] + p[0] * (i + 0.5)
            y = ll[1] + p[1] * (j + 0.5)
            return (x, y) if len(ll) == 2 else (x, y, ll[2] + p[2] * (k + 0.5))
        else:
            # Cylindrical: (r, theta, z)
            return (ll[0] + p[0] * i, 2 * np.pi * j / max(1, self.dimension[1]), ll[-1] + p[-1] * k)

    @classmethod
    def create_rectangular(
        cls,
        id: int,
        nx: int,
        ny: int,
        pitch_x: float,
        pitch_y: float,
        universe_id: int,
        lower_left: Tuple[float, float] = (0.0, 0.0),
    ) -> "Lattice":
        """Create rectangular lattice filled with single universe."""
        universes = np.full((nx, ny), universe_id, dtype=int)
        return cls(
            id=id,
            lattice_type=LatticeType.RECTANGULAR,
            dimension=(nx, ny),
            pitch=(pitch_x, pitch_y),
            lower_left=lower_left,
            universes=universes,
        )
