"""
Assembly-level geometry and refueling pattern management.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

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
    Represents a fuel assembly with burnup tracking.

    Attributes:
        id: Unique identifier
        position: Center position of assembly
        batch: Current fuel batch (0 = fresh, 1,2,3 = batches)
        burnup: Current burnup [MWd/kgU]
        enrichment: Initial enrichment [fraction]
        heavy_metal_mass: Heavy metal mass [kg]
        insertion_cycle: Cycle when assembly was inserted
        refueling_history: List of refueling events for this assembly
    """

    id: int
    position: Point3D
    batch: int = 0  # 0 = fresh, 1,2,3 = batches
    burnup: float = 0.0  # MWd/kgU
    enrichment: float = 0.0  # Initial enrichment
    heavy_metal_mass: float = 0.0  # kg
    insertion_cycle: int = 0
    refueling_history: List[RefuelingEvent] = field(default_factory=list)

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


class AssemblyManager:
    """
    Manages assemblies and refueling operations.

    Attributes:
        assemblies: List of all assemblies
        current_cycle: Current operating cycle
        refueling_pattern: Current refueling pattern
    """

    def __init__(self, name: str = "AssemblyManager"):
        self.name = name
        self.assemblies: List[Assembly] = []
        self.current_cycle: int = 0
        self.refueling_pattern: Optional[RefuelingPattern] = None

    def add_assembly(self, assembly: Assembly):
        """Add an assembly to the manager."""
        self.assemblies.append(assembly)

    def get_assemblies_by_batch(self, batch: int) -> List[Assembly]:
        """Get all assemblies in specified batch."""
        return [a for a in self.assemblies if a.batch == batch]

    def get_depleted_assemblies(self, target_burnup: float = 120.0) -> List[Assembly]:
        """Get assemblies that have reached target burnup."""
        return [a for a in self.assemblies if a.is_depleted(target_burnup)]

    def shuffle_assemblies(self, pattern: RefuelingPattern):
        """
        Shuffle assemblies according to refueling pattern.

        Args:
            pattern: Refueling pattern to apply
        """
        if not pattern.validate(len(self.assemblies)):
            raise ValueError("Invalid refueling pattern for number of assemblies")

        # Sort assemblies by position (for deterministic shuffling)
        # This is simplified - real shuffling would consider actual positions
        sorted_assemblies = sorted(self.assemblies, key=lambda a: (a.position.x, a.position.y))

        # Increment batch numbers (batch 3 → remove, batch 2 → batch 3, batch 1 → batch 2, fresh → batch 1)
        for assembly in sorted_assemblies:
            if assembly.batch >= pattern.n_batches:
                # Remove from core (mark as discharged)
                assembly.batch = -1  # Special marker for discharged
            elif assembly.batch > 0:
                assembly.batch += 1
            else:
                # Fresh fuel becomes batch 1
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

