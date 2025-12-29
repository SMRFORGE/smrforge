"""
Control rod geometry and positioning for reactor cores.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

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


@dataclass
class ControlRodBank:
    """
    Group of control rods operated together.

    Attributes:
        id: Unique identifier for bank
        name: Bank name (e.g., 'A', 'B', 'Regulation')
        rods: List of control rods in this bank
        insertion: Current insertion fraction for all rods (0.0-1.0)
        max_worth: Maximum reactivity worth when fully inserted [pcm]
    """

    id: int
    name: str
    rods: List[ControlRod] = field(default_factory=list)
    insertion: float = 1.0  # 0.0 = fully inserted, 1.0 = fully withdrawn
    max_worth: Optional[float] = None  # pcm

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
        """Calculate total reactivity worth of bank."""
        if self.max_worth is not None:
            # Simple linear model (worth proportional to insertion)
            return self.max_worth * (1.0 - self.insertion)
        return 0.0


class ControlRodSystem:
    """
    Complete control rod system for a reactor core.

    Attributes:
        name: System name
        banks: List of control rod banks
        scram_threshold: Power level that triggers scram [W] (optional)
    """

    def __init__(self, name: str = "ControlRodSystem"):
        self.name = name
        self.banks: List[ControlRodBank] = []
        self.scram_threshold: Optional[float] = None

    def add_bank(self, bank: ControlRodBank):
        """Add a control rod bank to the system."""
        self.banks.append(bank)

    def get_bank(self, name: str) -> Optional[ControlRodBank]:
        """Get bank by name."""
        for bank in self.banks:
            if bank.name == name:
                return bank
        return None

    def scram_all(self):
        """Scram all banks - fully insert all rods."""
        for bank in self.banks:
            bank.scram()

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

