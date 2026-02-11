"""
Control rod geometry and positioning for reactor cores.

Enhanced features include:
- Advanced control rod bank definitions (priority, dependencies, zones)
- Control rod sequencing (ordered insertion/withdrawal sequences)
- Enhanced scram geometry (full insertion with position tracking)
- Advanced worth calculations per position (axial and radial worth profiles)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

from smrforge.geometry.core_geometry import Point3D


class ControlRodType(Enum):
    """Types of control rods."""

    SHUTDOWN = "shutdown"  # Full-length shutdown rods
    REGULATION = "regulation"  # Shorter regulation rods
    BURNABLE_POISON = "burnable_poison"  # Burnable poison rods


@dataclass
class ControlRod:
    """
    Control rod geometry and properties.

    Attributes:
        id: Unique identifier
        position: Center position of control rod
        length: Full length of control rod [cm]
        diameter: Diameter of control rod [cm]
        material: Control material (e.g., 'B4C', 'AgInCd')
        rod_type: Type of control rod
        insertion: Insertion fraction (0.0 = fully inserted, 1.0 = fully withdrawn)
        worth: Reactivity worth [pcm] at current insertion (optional)
    """

    id: int
    position: Point3D
    length: float  # cm
    diameter: float  # cm
    material: str = "B4C"
    rod_type: ControlRodType = ControlRodType.SHUTDOWN
    insertion: float = 1.0  # 0.0 = fully inserted, 1.0 = fully withdrawn
    worth: Optional[float] = None  # pcm

    def volume(self) -> float:
        """Volume of control rod [cm³]."""
        return np.pi * (self.diameter / 2) ** 2 * self.length

    def inserted_length(self) -> float:
        """Currently inserted length [cm]."""
        return self.length * (1.0 - self.insertion)

    def is_fully_inserted(self) -> bool:
        """Check if rod is fully inserted."""
        return self.insertion <= 0.01

    def is_fully_withdrawn(self) -> bool:
        """Check if rod is fully withdrawn."""
        return self.insertion >= 0.99

    def worth_at_position(
        self, position: float, worth_profile: Optional[Callable[[float], float]] = None
    ) -> float:
        """
        Calculate reactivity worth at a specific axial position.

        Args:
            position: Axial position from bottom [cm] (0 = bottom of core)
            worth_profile: Optional function mapping position -> worth fraction
                          (default: uniform worth)

        Returns:
            Worth contribution at position [pcm]
        """
        if self.worth is None:
            return 0.0

        # Check if position is within inserted length
        inserted_len = self.inserted_length()
        if position > inserted_len:
            return 0.0

        # Use worth profile if provided, otherwise uniform
        if worth_profile is not None:
            worth_fraction = worth_profile(
                position / self.length if self.length > 0 else 0.0
            )
        else:
            # Uniform worth
            worth_fraction = 1.0

        # Linear approximation: worth proportional to inserted length at this position
        position_fraction = position / self.length if self.length > 0 else 0.0
        return self.worth * worth_fraction * position_fraction


class BankPriority(Enum):
    """Priority levels for control rod banks."""

    SAFETY = 1  # Safety rods (highest priority)
    SHUTDOWN = 2  # Shutdown rods
    REGULATION = 3  # Regulation rods
    MANUAL = 4  # Manual control (lowest priority)


@dataclass
class ControlRodBank:
    """
    Group of control rods operated together with advanced features.

    Attributes:
        id: Unique identifier for bank
        name: Bank name (e.g., 'A', 'B', 'Regulation')
        rods: List of control rods in this bank
        insertion: Current insertion fraction for all rods (0.0-1.0)
        max_worth: Maximum reactivity worth when fully inserted [pcm]
        priority: Bank priority level (for sequencing)
        dependencies: List of bank names that must be inserted before this bank
        zone: Optional zone identifier (e.g., 'core', 'reflector')
        worth_profile: Optional function for position-dependent worth calculation
    """

    id: int
    name: str
    rods: List[ControlRod] = field(default_factory=list)
    insertion: float = 1.0  # 0.0 = fully inserted, 1.0 = fully withdrawn
    max_worth: Optional[float] = None  # pcm
    priority: BankPriority = BankPriority.MANUAL
    dependencies: List[str] = field(default_factory=list)
    zone: Optional[str] = None
    worth_profile: Optional[Callable[[float], float]] = (
        None  # position fraction -> worth fraction
    )

    def add_rod(self, rod: ControlRod):
        """Add a control rod to this bank."""
        self.rods.append(rod)

    def set_insertion(self, insertion: float):
        """
        Set insertion for all rods in bank.

        Args:
            insertion: Insertion fraction (0.0 = fully inserted, 1.0 = withdrawn)
        """
        self.insertion = np.clip(insertion, 0.0, 1.0)
        for rod in self.rods:
            rod.insertion = self.insertion

    def scram(self):
        """Perform scram - fully insert all rods."""
        self.set_insertion(0.0)

    def withdraw(self):
        """Fully withdraw all rods."""
        self.set_insertion(1.0)

    def total_worth(self) -> float:
        """
        Calculate total reactivity worth of bank.

        Uses position-dependent worth if worth_profile is provided,
        otherwise uses simple linear model.
        """
        if self.max_worth is None:
            return 0.0

        if self.worth_profile is not None:
            # Position-dependent worth calculation
            total_worth = 0.0
            inserted_len = self.length * (1.0 - self.insertion) if self.rods else 0.0
            bank_length = max((rod.length for rod in self.rods), default=0.0)

            if bank_length > 0 and inserted_len > 0:
                # Integrate worth profile over inserted length
                n_points = 20  # Number of integration points
                positions = np.linspace(0, inserted_len, n_points)
                for pos in positions:
                    position_fraction = pos / bank_length
                    worth_fraction = self.worth_profile(position_fraction)
                    total_worth += self.max_worth * worth_fraction / n_points
            else:
                # Use simple linear model
                total_worth = self.max_worth * (1.0 - self.insertion)
        else:
            # Simple linear model (worth proportional to insertion)
            total_worth = self.max_worth * (1.0 - self.insertion)

        return total_worth

    @property
    def length(self) -> float:
        """Get maximum rod length in bank."""
        if not self.rods:
            return 0.0
        return max(rod.length for rod in self.rods)

    def get_rods_by_position(
        self, min_distance: float, max_distance: float
    ) -> List[ControlRod]:
        """
        Get rods within a distance range from a reference point.

        Args:
            min_distance: Minimum distance [cm]
            max_distance: Maximum distance [cm]

        Returns:
            List of rods within distance range
        """
        # Use first rod's position as reference (or could use core center)
        if not self.rods:
            return []

        reference = self.rods[0].position
        return [
            rod
            for rod in self.rods
            if min_distance
            <= np.sqrt(
                (rod.position.x - reference.x) ** 2
                + (rod.position.y - reference.y) ** 2
            )
            <= max_distance
        ]

    def can_insert(
        self, system: Optional["ControlRodSystem"] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if bank can be inserted based on dependencies.

        Args:
            system: Optional ControlRodSystem to check dependencies against

        Returns:
            (can_insert, reason) tuple
        """
        if not self.dependencies or system is None:
            return True, None

        for dep_name in self.dependencies:
            dep_bank = system.get_bank(dep_name)
            if dep_bank is None:
                return False, f"Dependency bank '{dep_name}' not found"
            if dep_bank.insertion > 0.1:  # Dependency not inserted
                return False, f"Dependency bank '{dep_name}' must be inserted first"

        return True, None


@dataclass
class ControlRodSequence:
    """Sequence of control rod operations."""

    name: str
    steps: List[Tuple[str, float, float]] = field(
        default_factory=list
    )  # [(bank_name, target_insertion, time_seconds), ...]
    description: str = ""


@dataclass
class ScramEvent:
    """Record of a scram event."""

    timestamp: float  # Time [s]
    trigger_reason: str  # Reason for scram
    banks_involved: List[str]  # Bank names that scrambled
    insertion_before: Dict[str, float]  # Insertion before scram
    insertion_after: Dict[str, float]  # Insertion after scram (should be 0.0)


class ControlRodSystem:
    """
    Complete control rod system for a reactor core with advanced features.

    Attributes:
        name: System name
        banks: List of control rod banks
        scram_threshold: Power level that triggers scram [W] (optional)
        sequences: List of control rod operation sequences
        scram_history: History of scram events
        axial_worth_profile: Optional function for axial worth distribution
        radial_worth_profile: Optional function for radial worth distribution
    """

    def __init__(self, name: str = "ControlRodSystem"):
        self.name = name
        self.banks: List[ControlRodBank] = []
        self.scram_threshold: Optional[float] = None
        self.sequences: List[ControlRodSequence] = []
        self.scram_history: List[ScramEvent] = []
        self.axial_worth_profile: Optional[Callable[[float], float]] = (
            None  # z_fraction -> worth_fraction
        )
        self.radial_worth_profile: Optional[Callable[[float], float]] = (
            None  # r_fraction -> worth_fraction
        )

    def add_bank(self, bank: ControlRodBank):
        """Add a control rod bank to the system."""
        self.banks.append(bank)

    def get_bank(self, name: str) -> Optional[ControlRodBank]:
        """Get bank by name."""
        for bank in self.banks:
            if bank.name == name:
                return bank
        return None

    def scram_all(
        self, trigger_reason: str = "Manual scram", timestamp: Optional[float] = None
    ):
        """
        Scram all banks - fully insert all rods with enhanced tracking.

        Args:
            trigger_reason: Reason for scram
            timestamp: Optional timestamp (uses current time if None)
        """
        if timestamp is None:
            timestamp = 0.0  # Could use time.time() if available

        # Record insertion before scram
        insertion_before = {bank.name: bank.insertion for bank in self.banks}

        # Perform scram
        banks_involved = []
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

    def total_reactivity_worth(self) -> float:
        """Calculate total reactivity worth of all banks."""
        return sum(bank.total_worth() for bank in self.banks)

    def shutdown_margin(self, k_eff: float) -> float:
        """
        Calculate shutdown margin.

        Args:
            k_eff: Current k-eff

        Returns:
            Shutdown margin (excess reactivity worth) [pcm]
        """
        # Assume all rods inserted (scram position)
        scram_worth = sum(
            bank.max_worth if bank.max_worth is not None else 0.0 for bank in self.banks
        )

        # Reactivity in dollars (assuming beta_eff ≈ 650 pcm for HTGR)
        beta_eff = 650.0  # pcm (typical for HTGR)
        current_reactivity = (k_eff - 1.0) / k_eff * 1e5  # Convert to pcm

        # Shutdown margin = scram worth - current reactivity
        margin = scram_worth - current_reactivity

        return margin

    def execute_sequence(
        self, sequence: ControlRodSequence, check_dependencies: bool = True
    ):
        """
        Execute a control rod sequence.

        Args:
            sequence: ControlRodSequence to execute
            check_dependencies: Whether to check bank dependencies before executing

        Raises:
            ValueError: If sequence cannot be executed
        """
        for bank_name, target_insertion, _time_seconds in sequence.steps:
            bank = self.get_bank(bank_name)
            if bank is None:
                raise ValueError(
                    f"Bank '{bank_name}' not found in sequence '{sequence.name}'"
                )

            if check_dependencies:
                can_insert, reason = bank.can_insert(self)
                if not can_insert:
                    raise ValueError(
                        f"Cannot execute step for bank '{bank_name}': {reason}"
                    )

            bank.set_insertion(target_insertion)

    def add_sequence(self, sequence: ControlRodSequence):
        """Add a control rod sequence to the system."""
        self.sequences.append(sequence)

    def get_sequence(self, name: str) -> Optional[ControlRodSequence]:
        """Get sequence by name."""
        for seq in self.sequences:
            if seq.name == name:
                return seq
        return None

    def calculate_worth_at_position(
        self, position: Point3D, axial_position: float, core_radius: float = 150.0
    ) -> float:
        """
        Calculate total reactivity worth contribution at a specific 3D position.

        Args:
            position: 3D position in core
            axial_position: Axial position from bottom [cm]
            core_radius: Core radius [cm] (for radial normalization)

        Returns:
            Total worth contribution at position [pcm]
        """
        total_worth = 0.0

        for bank in self.banks:
            for rod in bank.rods:
                # Calculate radial distance
                radial_dist = np.sqrt(position.x**2 + position.y**2)
                radial_fraction = radial_dist / core_radius if core_radius > 0 else 0.0

                # Apply radial worth profile if available
                radial_factor = 1.0
                if self.radial_worth_profile is not None:
                    radial_factor = self.radial_worth_profile(radial_fraction)

                # Calculate axial worth
                axial_worth = rod.worth_at_position(
                    axial_position,
                    worth_profile=bank.worth_profile or self.axial_worth_profile,
                )

                # Apply radial factor
                total_worth += axial_worth * radial_factor

        return total_worth

    def get_banks_by_priority(self, priority: BankPriority) -> List[ControlRodBank]:
        """Get all banks with specified priority."""
        return [bank for bank in self.banks if bank.priority == priority]

    def get_banks_by_zone(self, zone: str) -> List[ControlRodBank]:
        """Get all banks in specified zone."""
        return [bank for bank in self.banks if bank.zone == zone]

    def sequenced_insertion(
        self,
        target_insertion: float,
        bank_names: Optional[List[str]] = None,
        order_by_priority: bool = True,
    ):
        """
        Insert banks in sequence based on priority and dependencies.

        Args:
            target_insertion: Target insertion fraction
            bank_names: Optional list of bank names to insert (None = all)
            order_by_priority: Whether to order by priority (True) or dependency order (False)

        Raises:
            ValueError: If insertion sequence violates dependencies
        """
        # Select banks to insert
        banks_to_insert = (
            [
                self.get_bank(name)
                for name in bank_names
                if self.get_bank(name) is not None
            ]
            if bank_names
            else self.banks
        )

        # Remove None values
        banks_to_insert = [b for b in banks_to_insert if b is not None]

        # Order banks
        if order_by_priority:
            banks_to_insert.sort(key=lambda b: (b.priority.value, b.name))
        else:
            # Order by dependencies (dependencies first)
            ordered = []
            remaining = banks_to_insert.copy()

            while remaining:
                # Find banks with all dependencies satisfied
                ready = [
                    b
                    for b in remaining
                    if not b.dependencies
                    or all(dep in [o.name for o in ordered] for dep in b.dependencies)
                ]
                if not ready:
                    raise ValueError("Circular dependency in control rod banks")
                ordered.extend(sorted(ready, key=lambda b: (b.priority.value, b.name)))
                remaining = [b for b in remaining if b not in ready]

            banks_to_insert = ordered

        # Insert banks in order
        for bank in banks_to_insert:
            can_insert, reason = bank.can_insert(self)
            if not can_insert:
                raise ValueError(f"Cannot insert bank '{bank.name}': {reason}")
            bank.set_insertion(target_insertion)

    def get_scram_geometry(self) -> Dict[str, Dict[str, float]]:
        """
        Get full scram geometry (all rods fully inserted).

        Returns:
            Dictionary mapping bank_name -> {rod_id: insertion, ...}
        """
        scram_geometry = {}
        for bank in self.banks:
            scram_geometry[bank.name] = {rod.id: 0.0 for rod in bank.rods}
        return scram_geometry

    def is_in_scram_state(self) -> bool:
        """Check if system is in scram state (all rods fully inserted)."""
        return all(bank.insertion <= 0.01 for bank in self.banks)

    def create_standard_sequence(
        self, name: str, withdrawal_steps: int = 10, regulation_first: bool = True
    ) -> ControlRodSequence:
        """
        Create a standard control rod withdrawal sequence.

        Args:
            name: Sequence name
            withdrawal_steps: Number of withdrawal steps
            regulation_first: Whether to withdraw regulation rods first

        Returns:
            ControlRodSequence instance
        """
        steps = []
        insertion_values = np.linspace(1.0, 0.0, withdrawal_steps + 1)[
            1:
        ]  # Skip fully withdrawn

        # Order banks
        if regulation_first:
            regulation_banks = self.get_banks_by_priority(BankPriority.REGULATION)
            other_banks = [b for b in self.banks if b not in regulation_banks]
            ordered_banks = regulation_banks + other_banks
        else:
            ordered_banks = sorted(self.banks, key=lambda b: b.priority.value)

        # Create steps
        for insertion in insertion_values:
            for bank in ordered_banks:
                steps.append((bank.name, insertion, 1.0))  # 1 second per step

        return ControlRodSequence(
            name=name,
            steps=steps,
            description=f"Standard withdrawal sequence ({withdrawal_steps} steps)",
        )
