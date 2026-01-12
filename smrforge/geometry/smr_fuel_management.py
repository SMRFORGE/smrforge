"""
SMR-specific fuel management for long-cycle operations.

Provides enhanced fuel management capabilities for SMRs with:
- Long-cycle fuel management (3-5 year cycles)
- SMR-specific batch refueling patterns
- Compact core fuel shuffling
- Extended cycle length tracking
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..utils.logging import get_logger
from .assembly import Assembly, AssemblyManager, RefuelingPattern
from .core_geometry import Point3D

logger = get_logger("smrforge.geometry.smr_fuel_management")


@dataclass
class SMRRefuelingPattern:
    """
    SMR-specific refueling pattern for long-cycle operations.
    
    SMRs typically have:
    - Longer cycles (3-5 years vs 18-24 months for large reactors)
    - Fewer assemblies (compact cores)
    - Different shuffling patterns (optimized for small cores)
    
    Attributes:
        name: Pattern name
        cycle_length_years: Cycle length in years (3-5 for SMRs)
        n_batches: Number of fuel batches
        batch_fractions: Fraction of core in each batch
        shuffle_pattern: Shuffling pattern type ("out-in", "in-out", "scatter", "custom")
        compact_core: True if this is for a compact SMR core
    """
    
    name: str
    cycle_length_years: float = 3.0  # Years (typical SMR: 3-5 years)
    n_batches: int = 3
    batch_fractions: List[float] = field(default_factory=lambda: [1/3, 1/3, 1/3])
    shuffle_pattern: str = "out-in"  # "out-in", "in-out", "scatter", "custom"
    compact_core: bool = True
    
    def __post_init__(self):
        """Validate batch fractions."""
        if abs(sum(self.batch_fractions) - 1.0) > 0.01:
            raise ValueError(f"Batch fractions must sum to 1.0, got {sum(self.batch_fractions)}")
        if len(self.batch_fractions) != self.n_batches:
            raise ValueError(
                f"Number of batch fractions ({len(self.batch_fractions)}) "
                f"must match n_batches ({self.n_batches})"
            )


class SMRFuelManager(AssemblyManager):
    """
    Enhanced fuel manager for SMR-specific operations.
    
    Extends AssemblyManager with SMR-specific features:
    - Long-cycle tracking (3-5 year cycles)
    - Compact core shuffling patterns
    - Extended burnup tracking for long cycles
    - SMR-optimized refueling strategies
    
    Usage:
        >>> from smrforge.geometry.smr_fuel_management import SMRFuelManager, SMRRefuelingPattern
        >>> 
        >>> manager = SMRFuelManager(name="NuScale-Fuel-Manager")
        >>> pattern = SMRRefuelingPattern(
        ...     name="3-batch-long-cycle",
        ...     cycle_length_years=4.0,
        ...     n_batches=3,
        ... )
        >>> 
        >>> # Perform long-cycle refueling
        >>> manager.refuel_smr(pattern, target_burnup=60.0)  # MWd/kgU for 4-year cycle
    """
    
    def __init__(self, name: str = "SMRFuelManager", max_batches: int = 5):
        """
        Initialize SMR fuel manager.
        
        Args:
            name: Manager name
            max_batches: Maximum number of batches (typically 3-5 for SMRs)
        """
        super().__init__(name=name, max_batches=max_batches)
        self.cycle_length_years: float = 3.0  # Default 3-year cycle
        self.total_operating_years: float = 0.0
        self.smr_pattern: Optional[SMRRefuelingPattern] = None
    
    def refuel_smr(
        self,
        pattern: SMRRefuelingPattern,
        target_burnup: float = 60.0,  # MWd/kgU (lower for long cycles)
        fresh_enrichment: float = 0.045,
    ):
        """
        Perform SMR-specific refueling with long-cycle support.
        
        Args:
            pattern: SMR refueling pattern
            target_burnup: Target discharge burnup [MWd/kgU]
            fresh_enrichment: Enrichment of fresh fuel
        """
        self.smr_pattern = pattern
        self.cycle_length_years = pattern.cycle_length_years
        
        # Use SMR-specific shuffling
        self.shuffle_smr_compact(pattern)
        
        # Replace depleted assemblies
        depleted = self.get_assemblies_by_batch(pattern.n_batches)
        for assembly in depleted:
            if assembly.burnup >= target_burnup:
                assembly.batch = 0  # Fresh
                assembly.burnup = 0.0
                assembly.enrichment = fresh_enrichment
                assembly.insertion_cycle = self.current_cycle
        
        # Update cycle tracking
        self.current_cycle += 1
        self.total_operating_years += pattern.cycle_length_years
        
        logger.info(
            f"SMR refueling complete: Cycle {self.current_cycle}, "
            f"Total operating years: {self.total_operating_years:.1f}"
        )
    
    def shuffle_smr_compact(self, pattern: SMRRefuelingPattern):
        """
        Shuffle assemblies for compact SMR core.
        
        Uses SMR-optimized shuffling patterns:
        - "out-in": Move outer assemblies inward
        - "in-out": Move inner assemblies outward
        - "scatter": Scatter pattern for compact cores
        - "custom": Custom pattern
        
        Args:
            pattern: SMR refueling pattern
        """
        if pattern.shuffle_pattern == "out-in":
            self._shuffle_out_in(pattern)
        elif pattern.shuffle_pattern == "in-out":
            self._shuffle_in_out(pattern)
        elif pattern.shuffle_pattern == "scatter":
            self._shuffle_scatter(pattern)
        else:
            # Fall back to standard shuffle
            refueling_pattern = RefuelingPattern(
                name=pattern.name,
                n_batches=pattern.n_batches,
                batch_fractions=pattern.batch_fractions,
            )
            self.shuffle_assemblies(refueling_pattern)
    
    def _shuffle_out_in(self, pattern: SMRRefuelingPattern):
        """Out-in shuffling: outer assemblies move inward."""
        # Calculate distances from core center
        center_x = np.mean([a.position.x for a in self.assemblies])
        center_y = np.mean([a.position.y for a in self.assemblies])
        
        # Sort by distance from center (outer first)
        assemblies_with_dist = [
            (a, np.sqrt((a.position.x - center_x)**2 + (a.position.y - center_y)**2))
            for a in self.assemblies
        ]
        assemblies_with_dist.sort(key=lambda x: x[1], reverse=True)
        
        # Shuffle: outer assemblies become inner batches
        n_per_batch = len(self.assemblies) // pattern.n_batches
        for i, (assembly, _) in enumerate(assemblies_with_dist):
            if assembly.batch >= pattern.n_batches:
                assembly.batch = -1  # Discharged
            elif assembly.batch > 0:
                # Move to next batch (inward)
                assembly.batch = min(assembly.batch + 1, pattern.n_batches)
            else:
                # Fresh fuel becomes batch 1 (outermost)
                assembly.batch = 1
    
    def _shuffle_in_out(self, pattern: SMRRefuelingPattern):
        """In-out shuffling: inner assemblies move outward."""
        # Calculate distances from core center
        center_x = np.mean([a.position.x for a in self.assemblies])
        center_y = np.mean([a.position.y for a in self.assemblies])
        
        # Sort by distance from center (inner first)
        assemblies_with_dist = [
            (a, np.sqrt((a.position.x - center_x)**2 + (a.position.y - center_y)**2))
            for a in self.assemblies
        ]
        assemblies_with_dist.sort(key=lambda x: x[1])
        
        # Shuffle: inner assemblies become outer batches
        for i, (assembly, _) in enumerate(assemblies_with_dist):
            if assembly.batch >= pattern.n_batches:
                assembly.batch = -1  # Discharged
            elif assembly.batch > 0:
                # Move to next batch (outward)
                assembly.batch = min(assembly.batch + 1, pattern.n_batches)
            else:
                # Fresh fuel becomes batch 1 (innermost)
                assembly.batch = 1
    
    def _shuffle_scatter(self, pattern: SMRRefuelingPattern):
        """Scatter pattern: randomize batch assignments for compact cores."""
        # For compact cores, use scatter pattern
        for assembly in self.assemblies:
            if assembly.batch >= pattern.n_batches:
                assembly.batch = -1  # Discharged
            elif assembly.batch > 0:
                # Randomly assign to next batch
                assembly.batch = min(assembly.batch + 1, pattern.n_batches)
            else:
                # Fresh fuel randomly assigned to batch 1 or 2
                assembly.batch = np.random.choice([1, 2])
    
    def get_long_cycle_burnup(
        self, cycle_years: float, power_density: float = 40.0
    ) -> float:
        """
        Calculate burnup for a long cycle.
        
        Args:
            cycle_years: Cycle length in years
            power_density: Average power density [W/cm³]
        
        Returns:
            Burnup increment [MWd/kgU]
        """
        # Simplified burnup calculation
        # Burnup = (power * time) / (fuel mass)
        # For typical SMR: ~40 W/cm³, 4-year cycle
        
        cycle_days = cycle_years * 365.25
        # Assume typical fuel density and volume
        # This is simplified - actual calculation would use actual fuel mass
        burnup_increment = (power_density * cycle_days * 24 * 3600) / (1e6 * 1000)  # MWd/kgU
        
        return burnup_increment
    
    def simulate_long_cycle(
        self,
        pattern: SMRRefuelingPattern,
        n_cycles: int = 5,
        target_burnup: float = 60.0,
    ) -> Dict[str, List[float]]:
        """
        Simulate multiple long cycles for SMR.
        
        Args:
            pattern: SMR refueling pattern
            n_cycles: Number of cycles to simulate
            target_burnup: Target discharge burnup [MWd/kgU]
        
        Returns:
            Dictionary with cycle history:
            - 'cycles': Cycle numbers
            - 'burnup_avg': Average burnup per cycle
            - 'burnup_max': Maximum burnup per cycle
            - 'operating_years': Cumulative operating years
        """
        history = {
            "cycles": [],
            "burnup_avg": [],
            "burnup_max": [],
            "operating_years": [],
        }
        
        for cycle in range(n_cycles):
            # Calculate burnup increment for this cycle
            burnup_inc = self.get_long_cycle_burnup(pattern.cycle_length_years)
            
            # Update burnup for all assemblies
            for assembly in self.assemblies:
                if assembly.batch > 0:  # Active fuel
                    assembly.burnup += burnup_inc
            
            # Perform refueling
            self.refuel_smr(pattern, target_burnup=target_burnup)
            
            # Record history
            history["cycles"].append(self.current_cycle)
            history["burnup_avg"].append(self.average_burnup())
            history["burnup_max"].append(max(a.burnup for a in self.assemblies))
            history["operating_years"].append(self.total_operating_years)
        
        return history
