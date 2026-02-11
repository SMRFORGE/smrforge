"""
SMR-specific scram system with advanced features.

Provides enhanced scram capabilities for Small Modular Reactors:
- SMR-specific scram sequences
- Scram time calculations (insertion velocity)
- Scram worth calculations for compact cores
- Automatic scram triggers
- Scram effectiveness metrics
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..utils.logging import get_logger
from .control_rods import ControlRodBank, ControlRodSystem, ScramEvent
from .core_geometry import Point3D
from .lwr_smr import ControlBlade, ControlRodCluster

logger = get_logger("smrforge.geometry.smr_scram_system")


class ScramType(Enum):
    """Types of scram sequences for SMRs."""

    FULL = "full"  # Full scram - all rods inserted
    PARTIAL = "partial"  # Partial scram - selected banks only
    STAGED = "staged"  # Staged scram - sequential insertion
    EMERGENCY = "emergency"  # Emergency scram - fastest insertion


@dataclass
class SMRScramSequence:
    """
    SMR-specific scram sequence definition.

    SMRs may use different scram strategies than full-scale reactors:
    - Staged scram: Insert banks in sequence (faster response)
    - Partial scram: Only safety banks (for compact cores)
    - Emergency scram: All banks simultaneously (maximum speed)

    Attributes:
        name: Sequence name
        scram_type: Type of scram sequence
        bank_priorities: List of bank names in insertion order
        insertion_velocity: Rod insertion velocity [cm/s] (typical: 50-100 cm/s)
        delay_between_banks: Delay between bank insertions [s]
        target_insertion: Target insertion fraction (typically 0.0 for full scram)
    """

    name: str
    scram_type: ScramType = ScramType.FULL
    bank_priorities: List[str] = field(default_factory=list)
    insertion_velocity: float = 75.0  # cm/s (typical PWR: 50-100 cm/s)
    delay_between_banks: float = 0.1  # s
    target_insertion: float = 0.0  # 0.0 = fully inserted

    def calculate_scram_time(self, rod_length: float, n_banks: int) -> float:
        """
        Calculate total scram time for this sequence.

        Args:
            rod_length: Control rod length [cm]
            n_banks: Number of banks in sequence

        Returns:
            Total scram time [s]
        """
        if self.scram_type == ScramType.EMERGENCY:
            # Emergency: all banks simultaneously
            return rod_length / self.insertion_velocity
        elif self.scram_type == ScramType.STAGED:
            # Staged: sequential with delays
            insertion_time = rod_length / self.insertion_velocity
            return insertion_time + (n_banks - 1) * self.delay_between_banks
        else:
            # Full or partial: standard insertion
            return rod_length / self.insertion_velocity


class SMRScramSystem(ControlRodSystem):
    """
    Enhanced scram system for SMRs with advanced features.

    Extends ControlRodSystem with SMR-specific capabilities:
    - SMR-specific scram sequences
    - Scram time calculations
    - Compact core scram worth calculations
    - Automatic scram triggers
    - Scram effectiveness metrics

    Usage:
        >>> from smrforge.geometry.smr_scram_system import SMRScramSystem, SMRScramSequence, ScramType
        >>>
        >>> scram_system = SMRScramSystem(name="NuScale-Scram")
        >>> sequence = SMRScramSequence(
        ...     name="emergency-scram",
        ...     scram_type=ScramType.EMERGENCY,
        ...     insertion_velocity=100.0,  # cm/s
        ... )
        >>>
        >>> # Perform emergency scram
        >>> scram_system.scram_smr(sequence, trigger_reason="High power")
    """

    def __init__(self, name: str = "SMRScramSystem"):
        """Initialize SMR scram system."""
        super().__init__(name=name)
        self.scram_sequences: List[SMRScramSequence] = []
        self.scram_velocity: float = 75.0  # cm/s (default)
        self.compact_core: bool = True  # SMRs have compact cores
        self.auto_scram_enabled: bool = False
        self.scram_triggers: Dict[str, float] = {}  # {trigger_name: threshold}

    def add_scram_sequence(self, sequence: SMRScramSequence):
        """Add a scram sequence to the system."""
        self.scram_sequences.append(sequence)

    def scram_smr(
        self,
        sequence: Optional[SMRScramSequence] = None,
        trigger_reason: str = "Manual scram",
        timestamp: Optional[float] = None,
    ) -> ScramEvent:
        """
        Perform SMR-specific scram with sequence support.

        Args:
            sequence: Optional scram sequence (uses default if None)
            trigger_reason: Reason for scram
            timestamp: Optional timestamp

        Returns:
            ScramEvent record
        """
        if sequence is None:
            # Use default full scram
            sequence = SMRScramSequence(
                name="default-full",
                scram_type=ScramType.FULL,
                insertion_velocity=self.scram_velocity,
            )

        if timestamp is None:
            timestamp = 0.0

        # Record insertion before scram
        insertion_before = {bank.name: bank.insertion for bank in self.banks}

        # Perform scram based on sequence type
        banks_involved = []

        if sequence.scram_type == ScramType.EMERGENCY:
            # Emergency: all banks simultaneously
            for bank in self.banks:
                bank.scram()
                banks_involved.append(bank.name)

        elif sequence.scram_type == ScramType.STAGED:
            # Staged: insert banks in priority order
            if sequence.bank_priorities:
                # Use specified order
                for bank_name in sequence.bank_priorities:
                    bank = self.get_bank(bank_name)
                    if bank:
                        bank.scram()
                        banks_involved.append(bank_name)
            else:
                # Use bank priority order
                sorted_banks = sorted(
                    self.banks,
                    key=lambda b: (
                        b.priority.value if hasattr(b.priority, "value") else 0
                    ),
                )
                for bank in sorted_banks:
                    bank.scram()
                    banks_involved.append(bank.name)

        elif sequence.scram_type == ScramType.PARTIAL:
            # Partial: only safety/shutdown banks
            for bank in self.banks:
                if bank.priority.value <= 2:  # SAFETY or SHUTDOWN
                    bank.scram()
                    banks_involved.append(bank.name)

        else:  # FULL
            # Full: all banks
            for bank in self.banks:
                bank.scram()
                banks_involved.append(bank.name)

        # Record insertion after scram
        insertion_after = {bank.name: bank.insertion for bank in self.banks}

        # Record scram event
        scram_event = ScramEvent(
            timestamp=timestamp,
            trigger_reason=trigger_reason,
            banks_involved=banks_involved,
            insertion_before=insertion_before,
            insertion_after=insertion_after,
        )
        self.scram_history.append(scram_event)

        logger.info(
            f"SMR scram executed: {sequence.scram_type.value}, "
            f"{len(banks_involved)} banks, reason: {trigger_reason}"
        )

        return scram_event

    def calculate_scram_time(
        self,
        sequence: Optional[SMRScramSequence] = None,
        rod_length: Optional[float] = None,
    ) -> float:
        """
        Calculate scram time for given sequence.

        Args:
            sequence: Optional scram sequence (uses default if None)
            rod_length: Optional rod length [cm] (uses average if None)

        Returns:
            Scram time [s]
        """
        if sequence is None:
            sequence = SMRScramSequence(
                name="default",
                scram_type=ScramType.FULL,
                insertion_velocity=self.scram_velocity,
            )

        if rod_length is None:
            # Use average rod length from banks
            if self.banks:
                rod_lengths = [rod.length for bank in self.banks for rod in bank.rods]
                if rod_lengths:
                    rod_length = np.mean(rod_lengths)
                else:
                    rod_length = 365.76  # Default SMR rod length [cm]
            else:
                rod_length = 365.76

        return sequence.calculate_scram_time(rod_length, len(self.banks))

    def calculate_scram_worth(self, k_eff: float = 1.0) -> Dict[str, float]:
        """
        Calculate scram worth for SMR compact core.

        Args:
            k_eff: Current k-eff (for shutdown margin calculation)

        Returns:
            Dictionary with scram metrics:
            - 'total_worth': Total scram worth [pcm]
            - 'shutdown_margin': Shutdown margin [pcm]
            - 'scram_effectiveness': Scram effectiveness (fraction)
        """
        # Calculate total worth with all rods inserted
        total_worth = sum(
            bank.max_worth if bank.max_worth is not None else bank.total_worth()
            for bank in self.banks
        )

        # Calculate shutdown margin
        beta_eff = 650.0  # pcm (typical for LWR)
        current_reactivity = (k_eff - 1.0) / k_eff * 1e5  # Convert to pcm
        shutdown_margin = total_worth - current_reactivity

        # Scram effectiveness (should be > 1.0 for safe shutdown)
        scram_effectiveness = shutdown_margin / beta_eff if beta_eff > 0 else 0.0

        return {
            "total_worth": total_worth,
            "shutdown_margin": shutdown_margin,
            "scram_effectiveness": scram_effectiveness,
        }

    def check_auto_scram(
        self,
        power: float,
        temperature: Optional[float] = None,
        pressure: Optional[float] = None,
    ) -> Optional[ScramEvent]:
        """
        Check if auto-scram conditions are met and trigger if needed.

        Args:
            power: Current power [W]
            temperature: Optional temperature [K]
            pressure: Optional pressure [Pa]

        Returns:
            ScramEvent if scram triggered, None otherwise
        """
        if not self.auto_scram_enabled:
            return None

        trigger_reason = None

        # Check power threshold
        if self.scram_threshold and power > self.scram_threshold:
            trigger_reason = f"High power: {power:.2e} W > {self.scram_threshold:.2e} W"

        # Check custom triggers
        for trigger_name, threshold in self.scram_triggers.items():
            if (
                trigger_name == "temperature"
                and temperature
                and temperature > threshold
            ):
                trigger_reason = (
                    f"High temperature: {temperature:.1f} K > {threshold:.1f} K"
                )
            elif trigger_name == "pressure" and pressure and pressure > threshold:
                trigger_reason = (
                    f"High pressure: {pressure:.2e} Pa > {threshold:.2e} Pa"
                )

        if trigger_reason:
            # Use emergency scram sequence
            emergency_sequence = SMRScramSequence(
                name="auto-emergency",
                scram_type=ScramType.EMERGENCY,
                insertion_velocity=self.scram_velocity,
            )
            return self.scram_smr(emergency_sequence, trigger_reason=trigger_reason)

        return None

    def get_scram_statistics(self) -> Dict[str, float]:
        """
        Get statistics about scram history.

        Returns:
            Dictionary with scram statistics:
            - 'n_scrams': Number of scram events
            - 'avg_scram_time': Average scram time [s]
            - 'last_scram_time': Time since last scram [s]
        """
        n_scrams = len(self.scram_history)

        if n_scrams == 0:
            return {
                "n_scrams": 0,
                "avg_scram_time": 0.0,
                "last_scram_time": float("inf"),
            }

        # Calculate average scram time (simplified)
        avg_scram_time = self.calculate_scram_time()

        # Time since last scram
        if self.scram_history:
            last_scram = self.scram_history[-1]
            last_scram_time = (
                last_scram.timestamp
            )  # Would use current time in real system
        else:
            last_scram_time = 0.0

        return {
            "n_scrams": n_scrams,
            "avg_scram_time": avg_scram_time,
            "last_scram_time": last_scram_time,
        }


def create_nuscale_scram_system() -> SMRScramSystem:
    """
    Create NuScale-style scram system.

    NuScale uses:
    - Control rod clusters (RCCA)
    - Fast insertion velocity (~100 cm/s)
    - Emergency scram capability

    Returns:
        SMRScramSystem configured for NuScale
    """
    system = SMRScramSystem(name="NuScale-Scram")
    system.scram_velocity = 100.0  # cm/s (fast insertion)
    system.auto_scram_enabled = True
    system.scram_threshold = 1.2e9  # W (120% of rated power)

    # Add emergency scram sequence
    emergency_seq = SMRScramSequence(
        name="nuscale-emergency",
        scram_type=ScramType.EMERGENCY,
        insertion_velocity=100.0,
    )
    system.add_scram_sequence(emergency_seq)

    return system
