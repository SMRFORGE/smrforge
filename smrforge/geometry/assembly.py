"""
Assembly-level geometry and refueling pattern management.

Enhanced features include:
- Advanced burnup-dependent geometry (fuel shuffling)
- Multiple batch fuel management (support for more than 3 batches)
- Advanced assembly positioning/orientation
- Enhanced fuel cycle geometry tracking with snapshots
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

from smrforge.geometry.core_geometry import Point3D


class FuelBatch(Enum):
    """Fuel batch designations."""

    BATCH_1 = 1
    BATCH_2 = 2
    BATCH_3 = 3
    FRESH = 0  # Fresh fuel


@dataclass
class RefuelingEvent:
    """Record of a refueling event."""

    cycle: int
    date: Optional[str] = None  # ISO format date string
    assemblies_refueled: List[int] = field(default_factory=list)  # Assembly IDs
    batch_out: Optional[int] = None  # Batch being removed
    batch_in: Optional[int] = None  # Batch being inserted


@dataclass
class Assembly:
    """
    Represents a fuel assembly with burnup tracking and enhanced positioning.

    Attributes:
        id: Unique identifier
        position: Center position of assembly
        batch: Current fuel batch (0 = fresh, 1,2,3,... = batches)
        burnup: Current burnup [MWd/kgU]
        enrichment: Initial enrichment [fraction]
        heavy_metal_mass: Heavy metal mass [kg]
        insertion_cycle: Cycle when assembly was inserted
        refueling_history: List of refueling events for this assembly
        orientation: Assembly orientation angle [degrees] (0 = default, 60 = rotated)
        original_position: Original position before shuffling (for tracking)
        position_history: History of positions over cycles
    """

    id: int
    position: Point3D
    batch: int = 0  # 0 = fresh, 1,2,3,... = batches
    burnup: float = 0.0  # MWd/kgU
    enrichment: float = 0.0  # Initial enrichment
    heavy_metal_mass: float = 0.0  # kg
    insertion_cycle: int = 0
    refueling_history: List[RefuelingEvent] = field(default_factory=list)
    orientation: float = 0.0  # Degrees (0, 60, 120, 180, 240, 300 for hexagonal)
    original_position: Optional[Point3D] = None  # Original position
    position_history: List[Tuple[int, Point3D]] = field(default_factory=list)  # [(cycle, position), ...]

    def burnup_fraction(self, target_burnup: float = 120.0) -> float:
        """
        Calculate burnup as fraction of target.

        Args:
            target_burnup: Target discharge burnup [MWd/kgU]

        Returns:
            Burnup fraction (0.0-1.0+)
        """
        if target_burnup <= 0:
            return 0.0
        return self.burnup / target_burnup

    def is_depleted(self, target_burnup: float = 120.0) -> bool:
        """Check if assembly has reached target burnup."""
        return self.burnup >= target_burnup

    def age_cycles(self, current_cycle: int) -> int:
        """Calculate number of cycles assembly has been in core."""
        return current_cycle - self.insertion_cycle

    def rotate(self, angle: float):
        """
        Rotate assembly orientation.

        Args:
            angle: Rotation angle [degrees] (will be normalized to 0-360)
        """
        self.orientation = (self.orientation + angle) % 360.0

    def set_orientation(self, angle: float):
        """
        Set assembly orientation.

        Args:
            angle: Orientation angle [degrees] (0-360)
        """
        self.orientation = angle % 360.0

    def record_position(self, cycle: int):
        """Record current position for this cycle."""
        self.position_history.append((cycle, Point3D(self.position.x, self.position.y, self.position.z)))

    def move_to(self, new_position: Point3D, cycle: Optional[int] = None):
        """
        Move assembly to new position and record history.

        Args:
            new_position: New position
            cycle: Optional cycle number for history tracking
        """
        if self.original_position is None:
            self.original_position = Point3D(self.position.x, self.position.y, self.position.z)
        self.position = new_position
        if cycle is not None:
            self.record_position(cycle)


@dataclass
class RefuelingPattern:
    """
    Defines a refueling pattern for the core.

    Attributes:
        name: Pattern name
        n_batches: Number of fuel batches
        batch_fractions: Fraction of core in each batch
        shuffle_sequence: Shuffle sequence defining how assemblies move between batches
    """

    name: str
    n_batches: int = 3
    batch_fractions: List[float] = field(default_factory=lambda: [1 / 3, 1 / 3, 1 / 3])
    shuffle_sequence: Optional[Dict[int, int]] = None  # {old_position: new_position}

    def validate(self, n_assemblies: int) -> bool:
        """
        Validate pattern is consistent with number of assemblies.

        Args:
            n_assemblies: Total number of assemblies

        Returns:
            True if valid
        """
        if len(self.batch_fractions) != self.n_batches:
            return False
        if abs(sum(self.batch_fractions) - 1.0) > 1e-6:
            return False

        # Check batch sizes are integers
        batch_sizes = [int(f * n_assemblies) for f in self.batch_fractions]
        if sum(batch_sizes) != n_assemblies:
            return False

        return True

    def get_batch_size(self, n_assemblies: int, batch: int) -> int:
        """Get number of assemblies in specified batch."""
        if batch < 0 or batch >= len(self.batch_fractions):
            return 0
        return int(self.batch_fractions[batch] * n_assemblies)

    def generate_position_based_shuffle(
        self, assemblies: List["Assembly"], shuffle_type: str = "radial_rotation"
    ) -> Dict[int, int]:
        """
        Generate shuffle sequence based on assembly positions.

        Args:
            assemblies: List of assemblies
            shuffle_type: Type of shuffle pattern:
                - "radial_rotation": Rotate positions radially (inner->outer->inner)
                - "radial_outward": Move assemblies outward (higher burnup -> periphery)
                - "radial_inward": Move assemblies inward (lower burnup -> center)
                - "pattern_based": Use existing shuffle_sequence if provided

        Returns:
            Dictionary mapping old position index to new position index
        """
        if shuffle_type == "pattern_based" and self.shuffle_sequence is not None:
            return self.shuffle_sequence

        # Create position mapping
        sorted_assemblies = sorted(assemblies, key=lambda a: (a.position.x, a.position.y))
        n = len(assemblies)
        shuffle_map = {}

        if shuffle_type == "radial_rotation":
            # Rotate positions: move each assembly to next position in sequence
            for i, assembly in enumerate(sorted_assemblies):
                new_idx = (i + n // self.n_batches) % n
                shuffle_map[assembly.id] = sorted_assemblies[new_idx].id

        elif shuffle_type == "radial_outward":
            # Sort by burnup, move high burnup to outer positions
            sorted_by_burnup = sorted(assemblies, key=lambda a: a.burnup, reverse=True)
            # Assign to positions sorted by distance from center
            positions_by_dist = sorted(
                assemblies,
                key=lambda a: np.sqrt(a.position.x**2 + a.position.y**2),
                reverse=True,
            )
            for i, assembly in enumerate(sorted_by_burnup):
                shuffle_map[assembly.id] = positions_by_dist[i].id

        elif shuffle_type == "radial_inward":
            # Sort by burnup, move low burnup (fresh) to center positions
            sorted_by_burnup = sorted(assemblies, key=lambda a: a.burnup)
            positions_by_dist = sorted(
                assemblies,
                key=lambda a: np.sqrt(a.position.x**2 + a.position.y**2),
            )
            for i, assembly in enumerate(sorted_by_burnup):
                shuffle_map[assembly.id] = positions_by_dist[i].id

        else:
            # Default: no shuffle
            for assembly in assemblies:
                shuffle_map[assembly.id] = assembly.id

        return shuffle_map


@dataclass
class GeometrySnapshot:
    """Snapshot of geometry state at a specific cycle."""

    cycle: int
    assemblies_positions: Dict[int, Point3D]  # {assembly_id: position}
    assemblies_batches: Dict[int, int]  # {assembly_id: batch}
    assemblies_burnup: Dict[int, float]  # {assembly_id: burnup}
    assemblies_orientation: Dict[int, float]  # {assembly_id: orientation}


class AssemblyManager:
    """
    Manages assemblies and refueling operations with enhanced features.

    Attributes:
        assemblies: List of all assemblies
        current_cycle: Current operating cycle
        refueling_pattern: Current refueling pattern
        geometry_snapshots: History of geometry snapshots
        max_batches: Maximum number of batches supported (default: unlimited)
    """

    def __init__(self, name: str = "AssemblyManager", max_batches: int = 10):
        self.name = name
        self.assemblies: List[Assembly] = []
        self.current_cycle: int = 0
        self.refueling_pattern: Optional[RefuelingPattern] = None
        self.geometry_snapshots: List[GeometrySnapshot] = []
        self.max_batches: int = max_batches

    def add_assembly(self, assembly: Assembly):
        """Add an assembly to the manager."""
        self.assemblies.append(assembly)

    def get_assemblies_by_batch(self, batch: int) -> List[Assembly]:
        """Get all assemblies in specified batch."""
        return [a for a in self.assemblies if a.batch == batch]

    def get_depleted_assemblies(self, target_burnup: float = 120.0) -> List[Assembly]:
        """Get assemblies that have reached target burnup."""
        return [a for a in self.assemblies if a.is_depleted(target_burnup)]

    def shuffle_assemblies(
        self, pattern: RefuelingPattern, shuffle_type: str = "position_based", apply_positions: bool = True
    ):
        """
        Shuffle assemblies according to refueling pattern with position tracking.

        Args:
            pattern: Refueling pattern to apply
            shuffle_type: Type of shuffle ("position_based", "batch_only", "radial_rotation", etc.)
            apply_positions: Whether to actually move assembly positions (True) or just update batches (False)
        """
        if not pattern.validate(len(self.assemblies)):
            raise ValueError("Invalid refueling pattern for number of assemblies")

        # Record current geometry snapshot
        self._record_geometry_snapshot()

        if shuffle_type == "position_based" or shuffle_type.startswith("radial"):
            # Advanced position-based shuffling
            shuffle_map = pattern.generate_position_based_shuffle(self.assemblies, shuffle_type)

            # Create position map
            id_to_assembly = {a.id: a for a in self.assemblies}
            id_to_position = {a.id: a.position for a in self.assemblies}

            # Apply shuffle
            for assembly in self.assemblies:
                # Update batch numbers
                if assembly.batch >= pattern.n_batches:
                    assembly.batch = -1  # Discharged
                elif assembly.batch > 0:
                    assembly.batch += 1
                else:
                    assembly.batch = 1

                # Update positions if requested
                if apply_positions and assembly.id in shuffle_map:
                    new_id = shuffle_map[assembly.id]
                    if new_id in id_to_position and new_id != assembly.id:
                        new_position = id_to_position[new_id]
                        assembly.move_to(new_position, cycle=self.current_cycle + 1)

        else:
            # Simple batch-only shuffle (original behavior)
            sorted_assemblies = sorted(self.assemblies, key=lambda a: (a.position.x, a.position.y))
            for assembly in sorted_assemblies:
                if assembly.batch >= pattern.n_batches:
                    assembly.batch = -1  # Discharged
                elif assembly.batch > 0:
                    assembly.batch += 1
                else:
                    assembly.batch = 1

        self.current_cycle += 1

    def refuel(
        self,
        pattern: RefuelingPattern,
        target_burnup: float = 120.0,
        fresh_enrichment: float = 0.195,
    ):
        """
        Perform refueling operation.

        Args:
            pattern: Refueling pattern
            target_burnup: Target discharge burnup [MWd/kgU]
            fresh_enrichment: Enrichment of fresh fuel
        """
        # Get assemblies to remove (oldest batch)
        depleted = self.get_assemblies_by_batch(pattern.n_batches)

        # Create refueling event
        event = RefuelingEvent(
            cycle=self.current_cycle,
            assemblies_refueled=[a.id for a in depleted],
            batch_out=pattern.n_batches,
            batch_in=0,  # Fresh fuel
        )

        # Shuffle existing assemblies
        self.shuffle_assemblies(pattern)

        # Replace depleted assemblies with fresh
        for assembly in depleted:
            assembly.batch = 0  # Fresh
            assembly.burnup = 0.0
            assembly.enrichment = fresh_enrichment
            assembly.insertion_cycle = self.current_cycle
            assembly.refueling_history.append(event)

        self.refueling_pattern = pattern

    def average_burnup(self, batch: Optional[int] = None) -> float:
        """
        Calculate average burnup.

        Args:
            batch: Optional batch number (None = all assemblies)

        Returns:
            Average burnup [MWd/kgU]
        """
        assemblies = (
            self.get_assemblies_by_batch(batch) if batch is not None else self.assemblies
        )
        if not assemblies:
            return 0.0
        return np.mean([a.burnup for a in assemblies])

    def cycle_length_estimate(self, power_thermal: float, target_burnup: float = 120.0) -> float:
        """
        Estimate cycle length.

        Args:
            power_thermal: Thermal power [W]
            target_burnup: Target burnup [MWd/kgU]

        Returns:
            Estimated cycle length [days]
        """
        # Simplified calculation
        total_hm = sum(a.heavy_metal_mass for a in self.assemblies if a.batch >= 0)
        if total_hm <= 0:
            return 0.0

        # Energy content
        energy_per_kg = target_burnup * 24.0 * 3600.0 * 1e6  # J/kg
        total_energy = total_hm * energy_per_kg

        # Cycle length
        cycle_length = total_energy / power_thermal / (24.0 * 3600.0)  # days

        return cycle_length

    def _record_geometry_snapshot(self):
        """Record current geometry state."""
        snapshot = GeometrySnapshot(
            cycle=self.current_cycle,
            assemblies_positions={a.id: Point3D(a.position.x, a.position.y, a.position.z) for a in self.assemblies},
            assemblies_batches={a.id: a.batch for a in self.assemblies},
            assemblies_burnup={a.id: a.burnup for a in self.assemblies},
            assemblies_orientation={a.id: a.orientation for a in self.assemblies},
        )
        self.geometry_snapshots.append(snapshot)

    def get_geometry_at_cycle(self, cycle: int) -> Optional[GeometrySnapshot]:
        """Get geometry snapshot for a specific cycle."""
        for snapshot in self.geometry_snapshots:
            if snapshot.cycle == cycle:
                return snapshot
        return None

    def get_position_history(self, assembly_id: int) -> List[Tuple[int, Point3D]]:
        """Get position history for a specific assembly."""
        assembly = next((a for a in self.assemblies if a.id == assembly_id), None)
        if assembly is None:
            return []
        return assembly.position_history.copy()

    def apply_burnup_dependent_shuffle(
        self, pattern: RefuelingPattern, burnup_thresholds: Optional[Dict[int, float]] = None
    ):
        """
        Apply burnup-dependent shuffle (move high burnup assemblies outward).

        Args:
            pattern: Refueling pattern
            burnup_thresholds: Optional burnup thresholds per batch for shuffle decisions
        """
        # Sort assemblies by burnup
        sorted_by_burnup = sorted(self.assemblies, key=lambda a: a.burnup, reverse=True)

        # Create position mapping based on distance from center
        positions_by_distance = sorted(
            self.assemblies, key=lambda a: np.sqrt(a.position.x**2 + a.position.y**2), reverse=True
        )

        # Apply shuffle: high burnup -> outer positions, low burnup -> inner positions
        for i, assembly in enumerate(sorted_by_burnup):
            if i < len(positions_by_distance):
                new_position = positions_by_distance[i].position
                assembly.move_to(new_position, cycle=self.current_cycle + 1)

        # Now apply normal batch shuffle
        self.shuffle_assemblies(pattern, shuffle_type="batch_only", apply_positions=False)

    def get_assemblies_by_orientation(self, orientation_range: Tuple[float, float]) -> List[Assembly]:
        """
        Get assemblies within specified orientation range.

        Args:
            orientation_range: (min_angle, max_angle) in degrees

        Returns:
            List of assemblies within orientation range
        """
        min_angle, max_angle = orientation_range
        return [
            a for a in self.assemblies if min_angle <= a.orientation <= max_angle or a.orientation % 360 in range(int(min_angle), int(max_angle) + 1)
        ]

    def rotate_assembly(self, assembly_id: int, angle: float):
        """Rotate a specific assembly."""
        assembly = next((a for a in self.assemblies if a.id == assembly_id), None)
        if assembly:
            assembly.rotate(angle)

    def rotate_batch(self, batch: int, angle: float):
        """Rotate all assemblies in a specific batch."""
        for assembly in self.get_assemblies_by_batch(batch):
            assembly.rotate(angle)

    def get_batch_statistics(self, batch: Optional[int] = None) -> Dict[str, float]:
        """
        Get comprehensive statistics for a batch or all assemblies.

        Args:
            batch: Optional batch number (None = all assemblies)

        Returns:
            Dictionary with statistics
        """
        assemblies = self.get_assemblies_by_batch(batch) if batch is not None else self.assemblies
        if not assemblies:
            return {}

        burnups = [a.burnup for a in assemblies]
        enrichments = [a.enrichment for a in assemblies]
        ages = [a.age_cycles(self.current_cycle) for a in assemblies]

        return {
            "count": len(assemblies),
            "avg_burnup": np.mean(burnups),
            "max_burnup": np.max(burnups),
            "min_burnup": np.min(burnups),
            "std_burnup": np.std(burnups),
            "avg_enrichment": np.mean(enrichments),
            "avg_age": np.mean(ages),
            "total_hm_mass": sum(a.heavy_metal_mass for a in assemblies),
        }

    def support_multiple_batches(self, n_batches: int) -> bool:
        """
        Check if manager supports specified number of batches.

        Args:
            n_batches: Number of batches

        Returns:
            True if supported
        """
        return n_batches <= self.max_batches

    def create_multi_batch_pattern(
        self, name: str, n_batches: int, batch_fractions: Optional[List[float]] = None
    ) -> RefuelingPattern:
        """
        Create a refueling pattern with specified number of batches.

        Args:
            name: Pattern name
            n_batches: Number of batches
            batch_fractions: Optional list of fractions (defaults to equal fractions)

        Returns:
            RefuelingPattern instance

        Raises:
            ValueError: If n_batches exceeds max_batches
        """
        if n_batches > self.max_batches:
            raise ValueError(
                f"Number of batches ({n_batches}) exceeds maximum ({self.max_batches}). "
                f"Increase max_batches in AssemblyManager constructor."
            )

        if batch_fractions is None:
            batch_fractions = [1.0 / n_batches] * n_batches

        return RefuelingPattern(name=name, n_batches=n_batches, batch_fractions=batch_fractions)

