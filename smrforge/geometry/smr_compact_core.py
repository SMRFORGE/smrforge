"""
SMR-specific compact core layouts.

Provides compact core arrangements optimized for Small Modular Reactors:
- Reduced assembly counts (fewer assemblies than full-scale)
- Compact reflector designs
- SMR-specific core arrangements
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..utils.logging import get_logger
from .core_geometry import Point3D
from .lwr_smr import FuelAssembly, PWRSMRCore

logger = get_logger("smrforge.geometry.smr_compact_core")


@dataclass
class CompactReflector:
    """
    Compact reflector for SMR cores.

    SMRs use thinner, more efficient reflectors than full-scale reactors
    due to their smaller size and different neutron economy.

    Attributes:
        id: Unique identifier
        position: Center position
        inner_radius: Inner radius (core boundary) [cm]
        outer_radius: Outer radius [cm]
        height: Reflector height [cm]
        material: Reflector material name (e.g., "water", "steel", "graphite")
        thickness: Reflector thickness [cm]
    """

    id: int
    position: Point3D
    inner_radius: float  # cm
    outer_radius: float  # cm
    height: float  # cm
    material: str = "water"  # Typical SMR reflector
    thickness: float = 0.0  # cm (outer_radius - inner_radius)

    def __post_init__(self):
        """Calculate thickness if not provided."""
        if self.thickness == 0.0:
            self.thickness = self.outer_radius - self.inner_radius

    def volume(self) -> float:
        """Calculate reflector volume [cm³]."""
        return np.pi * (self.outer_radius**2 - self.inner_radius**2) * self.height


class CompactSMRCore(PWRSMRCore):
    """
    Compact SMR core with reduced assembly counts and optimized layout.

    Extends PWRSMRCore with SMR-specific features:
    - Reduced assembly counts (typically 17-37 assemblies vs 100+ for full-scale)
    - Compact reflector designs
    - Optimized core arrangements for small cores

    Usage:
        >>> from smrforge.geometry.smr_compact_core import CompactSMRCore
        >>>
        >>> core = CompactSMRCore(name="NuScale-Compact")
        >>> core.build_compact_core(
        ...     n_assemblies=37,  # NuScale has 37 assemblies
        ...     assembly_pitch=21.5,
        ...     reflector_thickness=10.0,  # Compact reflector
        ... )
    """

    def __init__(self, name: str = "Compact-SMR"):
        """Initialize compact SMR core."""
        super().__init__(name=name)
        self.reflector: Optional[CompactReflector] = None
        self.reflector_thickness: float = 10.0  # cm (typical SMR: 5-15 cm)
        self.is_compact: bool = True

    def build_compact_core(
        self,
        n_assemblies: int,
        assembly_pitch: float = 21.5,  # cm
        assembly_height: float = 365.76,  # cm
        lattice_size: int = 17,  # 17x17 for NuScale
        rod_pitch: float = 1.26,  # cm
        reflector_thickness: float = 10.0,  # cm
        core_shape: str = "square",  # "square", "circular", "hexagonal"
    ):
        """
        Build compact SMR core with reduced assembly count.

        Args:
            n_assemblies: Total number of assemblies (typically 17-37 for SMRs)
            assembly_pitch: Assembly-to-assembly pitch [cm]
            assembly_height: Assembly height [cm]
            lattice_size: Fuel rod lattice size (e.g., 17 for 17x17)
            rod_pitch: Fuel rod pitch [cm]
            reflector_thickness: Reflector thickness [cm] (5-15 cm typical for SMRs)
            core_shape: Core shape ("square", "circular", "hexagonal")
        """
        self.reflector_thickness = reflector_thickness
        self.core_height = assembly_height

        # Determine arrangement based on number of assemblies
        if core_shape == "square":
            n_x, n_y = self._calculate_square_arrangement(n_assemblies)
        elif core_shape == "circular":
            n_x, n_y = self._calculate_circular_arrangement(n_assemblies)
        elif core_shape == "hexagonal":
            n_x, n_y = self._calculate_hexagonal_arrangement(n_assemblies)
        else:
            raise ValueError(f"Unknown core shape: {core_shape}")

        # Build core using parent method
        self.build_square_lattice_core(
            n_assemblies_x=n_x,
            n_assemblies_y=n_y,
            assembly_pitch=assembly_pitch,
            assembly_height=assembly_height,
            lattice_size=lattice_size,
            rod_pitch=rod_pitch,
        )

        # Trim to exact number of assemblies if needed
        if len(self.assemblies) > n_assemblies:
            # Remove excess assemblies (keep those closest to center)
            center_x = np.mean([a.position.x for a in self.assemblies])
            center_y = np.mean([a.position.y for a in self.assemblies])

            assemblies_with_dist = [
                (
                    a,
                    np.sqrt(
                        (a.position.x - center_x) ** 2 + (a.position.y - center_y) ** 2
                    ),
                )
                for a in self.assemblies
            ]
            assemblies_with_dist.sort(
                key=lambda x: x[1]
            )  # Sort by distance (closest first)

            # Keep only the n_assemblies closest to center
            self.assemblies = [a for a, _ in assemblies_with_dist[:n_assemblies]]
            self.n_assemblies = len(self.assemblies)

        # Add compact reflector
        self._add_compact_reflector()

        logger.info(
            f"Built compact SMR core: {len(self.assemblies)} assemblies, "
            f"{n_x}x{n_y} arrangement, {reflector_thickness} cm reflector"
        )

    def _calculate_square_arrangement(self, n_assemblies: int) -> Tuple[int, int]:
        """Calculate square arrangement for given number of assemblies."""
        # Find closest square number
        n_side = int(np.sqrt(n_assemblies))
        if n_side * n_side < n_assemblies:
            n_side += 1

        return n_side, n_side

    def _calculate_circular_arrangement(self, n_assemblies: int) -> Tuple[int, int]:
        """Calculate circular arrangement (approximated as square)."""
        # For circular, use square approximation
        # Could be enhanced to use actual circular packing
        return self._calculate_square_arrangement(n_assemblies)

    def _calculate_hexagonal_arrangement(self, n_assemblies: int) -> Tuple[int, int]:
        """Calculate hexagonal arrangement."""
        # Hexagonal: 1, 7, 19, 37, 61, ... assemblies
        # For now, approximate as square
        return self._calculate_square_arrangement(n_assemblies)

    def _add_compact_reflector(self):
        """Add compact reflector around core."""
        # Calculate core radius (approximate as circular)
        core_radius = self.core_diameter / 2.0

        # Create compact reflector
        self.reflector = CompactReflector(
            id=1,
            position=Point3D(0, 0, self.core_height / 2),
            inner_radius=core_radius,
            outer_radius=core_radius + self.reflector_thickness,
            height=self.core_height,
            material="water",  # Typical SMR reflector
            thickness=self.reflector_thickness,
        )

    def get_assembly_count_by_batch(self) -> Dict[int, int]:
        """
        Get assembly count by batch for compact core.

        Returns:
            Dictionary mapping batch number to assembly count
        """
        batch_counts = {}
        for assembly in self.assemblies:
            batch = getattr(assembly, "batch", 0)
            batch_counts[batch] = batch_counts.get(batch, 0) + 1
        return batch_counts

    def get_compact_core_metrics(self) -> Dict[str, float]:
        """
        Get metrics specific to compact SMR cores.

        Returns:
            Dictionary with compact core metrics:
            - 'n_assemblies': Number of assemblies
            - 'core_diameter': Core diameter [cm]
            - 'reflector_thickness': Reflector thickness [cm]
            - 'assembly_density': Assemblies per unit area [assemblies/cm²]
            - 'compactness_ratio': Ratio of SMR to full-scale core size
        """
        core_area = np.pi * (self.core_diameter / 2) ** 2
        assembly_density = self.n_assemblies / core_area if core_area > 0 else 0.0

        # Typical full-scale PWR: ~200 assemblies, ~400 cm diameter
        full_scale_assemblies = 200
        full_scale_diameter = 400.0  # cm
        compactness_ratio = (
            (self.n_assemblies / full_scale_assemblies)
            * (full_scale_diameter / self.core_diameter)
            if self.core_diameter > 0
            else 0.0
        )

        return {
            "n_assemblies": self.n_assemblies,
            "core_diameter": self.core_diameter,
            "reflector_thickness": self.reflector_thickness,
            "assembly_density": assembly_density,
            "compactness_ratio": compactness_ratio,
        }


def create_nuscale_compact_core() -> CompactSMRCore:
    """
    Create NuScale-style compact core (37 assemblies).

    Returns:
        CompactSMRCore configured for NuScale design
    """
    core = CompactSMRCore(name="NuScale-Compact")
    core.build_compact_core(
        n_assemblies=37,  # NuScale has 37 assemblies
        assembly_pitch=21.5,  # cm
        assembly_height=365.76,  # cm (12 feet)
        lattice_size=17,  # 17x17 fuel assemblies
        rod_pitch=1.26,  # cm
        reflector_thickness=10.0,  # cm
        core_shape="circular",
    )
    return core


def create_mpower_compact_core() -> CompactSMRCore:
    """
    Create mPower-style compact core (69 assemblies).

    Returns:
        CompactSMRCore configured for mPower design
    """
    core = CompactSMRCore(name="mPower-Compact")
    core.build_compact_core(
        n_assemblies=69,  # mPower has 69 assemblies
        assembly_pitch=21.5,  # cm
        assembly_height=365.76,  # cm
        lattice_size=15,  # 15x15 fuel assemblies
        rod_pitch=1.26,  # cm
        reflector_thickness=12.0,  # cm
        core_shape="square",
    )
    return core
