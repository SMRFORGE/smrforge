"""
LWR SMR-specific burnup features.

Provides enhanced burnup capabilities for LWR SMRs including:
- Gadolinium burnable poison depletion
- Assembly-wise and rod-wise burnup tracking
- Control rod shadowing effects
- Long-cycle burnup optimization
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..core.reactor_core import Nuclide, NuclearDataCache
from ..utils.logging import get_logger
from .solver import BurnupSolver, NuclideInventory

logger = get_logger("smrforge.burnup.lwr_burnup")


@dataclass
class GadoliniumPoison:
    """
    Gadolinium burnable poison configuration.
    
    Gadolinium (Gd) is commonly used as a burnable poison in LWR fuel to
    control initial reactivity and flatten power distribution. This class
    tracks Gd depletion during burnup.
    
    Attributes:
        nuclides: List of gadolinium isotopes (typically Gd-155, Gd-157)
        initial_concentrations: Initial concentrations [atoms/cm³] for each isotope
        depletion_rates: Depletion rates [1/s] for each isotope (calculated from flux)
    """
    
    nuclides: List[Nuclide]
    initial_concentrations: np.ndarray  # [atoms/cm³]
    depletion_rates: Optional[np.ndarray] = None  # [1/s], calculated from flux


@dataclass
class AssemblyBurnup:
    """
    Assembly-wise burnup tracking for LWR SMRs.
    
    Tracks burnup distribution across fuel assemblies in a square lattice core.
    Useful for SMRs with compact cores where assembly-to-assembly variation
    is important.
    
    Attributes:
        assembly_id: Assembly identifier
        position: Assembly position (row, col) in lattice
        burnup: Burnup [MWd/kgU] for this assembly
        average_enrichment: Average enrichment [fraction]
        peak_power: Peak power density [W/cm³]
        nuclide_inventory: NuclideInventory for this assembly
    """
    
    assembly_id: str
    position: Tuple[int, int]  # (row, col)
    burnup: float  # MWd/kgU
    average_enrichment: float
    peak_power: float  # W/cm³
    nuclide_inventory: Optional[NuclideInventory] = None


@dataclass
class RodBurnup:
    """
    Fuel rod-wise burnup tracking for LWR SMRs.
    
    Tracks burnup distribution within a single fuel assembly, accounting for
    intra-assembly variation due to flux gradients and control rod shadowing.
    
    Attributes:
        rod_id: Rod identifier within assembly
        position: Rod position (row, col) within assembly lattice
        burnup: Burnup [MWd/kgU] for this rod
        enrichment: Enrichment [fraction] for this rod
        gadolinium_content: Gadolinium content [atoms/cm³] (if applicable)
        control_rod_proximity: Distance to nearest control rod [cm]
        shadowing_factor: Control rod shadowing factor (0.0 to 1.0)
    """
    
    rod_id: str
    position: Tuple[int, int]  # (row, col) within assembly
    burnup: float  # MWd/kgU
    enrichment: float
    gadolinium_content: float = 0.0  # atoms/cm³
    control_rod_proximity: float = 0.0  # cm
    shadowing_factor: float = 1.0  # 1.0 = no shadowing, 0.0 = fully shadowed


class GadoliniumDepletion:
    """
    Gadolinium burnable poison depletion calculator.
    
    Calculates the depletion of gadolinium isotopes (Gd-155, Gd-157) during
    burnup. These isotopes have very high thermal capture cross-sections and
    deplete rapidly, providing initial reactivity control.
    
    Usage:
        >>> from smrforge.burnup.lwr_burnup import GadoliniumDepletion
        >>> from smrforge.core.reactor_core import Nuclide
        >>> 
        >>> gd = GadoliniumDepletion(cache)
        >>> gd155 = Nuclide(Z=64, A=155)
        >>> gd157 = Nuclide(Z=64, A=157)
        >>> 
        >>> # Initial concentrations (typical: 2-4 wt% Gd2O3 in UO2)
        >>> initial_gd155 = 1e20  # atoms/cm³
        >>> initial_gd157 = 1e20
        >>> 
        >>> # Calculate depletion over time
        >>> flux = 1e14  # n/cm²/s
        >>> time = 365 * 24 * 3600  # 1 year in seconds
        >>> 
        >>> final_gd155 = gd.deplete(gd155, initial_gd155, flux, time)
        >>> print(f"Gd-155 remaining: {final_gd155/initial_gd155*100:.1f}%")
    """
    
    def __init__(self, cache: Optional[NuclearDataCache] = None):
        """
        Initialize gadolinium depletion calculator.
        
        Args:
            cache: Optional NuclearDataCache for accessing cross-section data.
        """
        self.cache = cache if cache is not None else NuclearDataCache()
        
        # Gd-155 and Gd-157 are the main burnable poison isotopes
        self.gd155 = Nuclide(Z=64, A=155)
        self.gd157 = Nuclide(Z=64, A=157)
        
        logger.debug("GadoliniumDepletion initialized")
    
    def get_capture_cross_section(self, nuclide: Nuclide, temperature: float = 600.0) -> float:
        """
        Get thermal capture cross-section for gadolinium isotope.
        
        Args:
            nuclide: Gadolinium nuclide (typically Gd-155 or Gd-157).
            temperature: Temperature [K] (default: 600 K).
        
        Returns:
            Thermal capture cross-section [barns].
        """
        try:
            energy, xs = self.cache.get_cross_section(nuclide, "capture", temperature)
            # Use thermal energy (0.025 eV) cross-section
            thermal_idx = np.argmin(np.abs(energy - 0.025))
            return xs[thermal_idx]
        except Exception:
            # Fallback values (typical for Gd-155 and Gd-157)
            if nuclide == self.gd155:
                return 61000.0  # barns (very high!)
            elif nuclide == self.gd157:
                return 254000.0  # barns (extremely high!)
            else:
                return 1000.0  # Default
    
    def deplete(
        self,
        nuclide: Nuclide,
        initial_concentration: float,
        flux: float,
        time: float,
        temperature: float = 600.0,
    ) -> float:
        """
        Calculate gadolinium depletion over time.
        
        Uses exponential decay model: N(t) = N0 * exp(-sigma * phi * t)
        where:
            N(t) = concentration at time t
            N0 = initial concentration
            sigma = capture cross-section
            phi = neutron flux
            t = time
        
        Args:
            nuclide: Gadolinium nuclide.
            initial_concentration: Initial concentration [atoms/cm³].
            flux: Neutron flux [n/cm²/s].
            time: Time [s].
            temperature: Temperature [K] (default: 600 K).
        
        Returns:
            Final concentration [atoms/cm³].
        """
        if initial_concentration <= 0:
            return 0.0
        
        if flux <= 0 or time <= 0:
            return initial_concentration
        
        # Get capture cross-section
        sigma = self.get_capture_cross_section(nuclide, temperature)  # barns
        sigma_cm2 = sigma * 1e-24  # Convert barns to cm²
        
        # Exponential depletion
        depletion_rate = sigma_cm2 * flux  # 1/s
        final_concentration = initial_concentration * np.exp(-depletion_rate * time)
        
        return max(0.0, final_concentration)
    
    def calculate_reactivity_worth(
        self,
        gd_poison: GadoliniumPoison,
        flux: float,
        time: float,
        temperature: float = 600.0,
    ) -> float:
        """
        Calculate reactivity worth of gadolinium poison.
        
        The reactivity worth decreases as gadolinium depletes. This is useful
        for understanding how initial reactivity control evolves during burnup.
        
        Args:
            gd_poison: GadoliniumPoison configuration.
            flux: Neutron flux [n/cm²/s].
            time: Time [s].
            temperature: Temperature [K].
        
        Returns:
            Reactivity worth [dk/k] (negative = negative reactivity).
        """
        total_worth = 0.0
        
        for i, nuclide in enumerate(gd_poison.nuclides):
            initial_conc = gd_poison.initial_concentrations[i]
            final_conc = self.deplete(nuclide, initial_conc, flux, time, temperature)
            
            # Simplified reactivity worth calculation
            # More accurate would require detailed flux calculations
            depletion_fraction = 1.0 - (final_conc / initial_conc) if initial_conc > 0 else 0.0
            sigma = self.get_capture_cross_section(nuclide, temperature)
            
            # Rough estimate: -0.01 dk/k per 1e20 atoms/cm³ of Gd
            worth_per_atom = -0.01 / 1e20  # dk/k per atom/cm³
            worth = initial_conc * worth_per_atom * (1.0 - depletion_fraction)
            total_worth += worth
        
        return total_worth


class AssemblyWiseBurnupTracker:
    """
    Assembly-wise burnup tracking for LWR SMR square lattice cores.
    
    Tracks burnup distribution across fuel assemblies, accounting for:
    - Assembly-to-assembly flux variation
    - Control rod shadowing effects
    - Assembly enrichment differences
    - Power distribution
    
    Usage:
        >>> from smrforge.burnup.lwr_burnup import AssemblyWiseBurnupTracker
        >>> 
        >>> tracker = AssemblyWiseBurnupTracker(n_assemblies=37)  # NuScale
        >>> 
        >>> # Track burnup for each assembly
        >>> for assembly_id in range(37):
        ...     position = tracker.get_assembly_position(assembly_id)
        ...     burnup = calculate_assembly_burnup(assembly_id)
        ...     tracker.update_assembly(assembly_id, position, burnup)
        >>> 
        >>> # Get burnup distribution
        >>> distribution = tracker.get_burnup_distribution()
    """
    
    def __init__(self, n_assemblies: int, lattice_size: Optional[Tuple[int, int]] = None):
        """
        Initialize assembly-wise burnup tracker.
        
        Args:
            n_assemblies: Number of fuel assemblies.
            lattice_size: Optional (rows, cols) tuple. If None, calculates from n_assemblies.
        """
        self.n_assemblies = n_assemblies
        
        # Calculate lattice size if not provided
        if lattice_size is None:
            # Approximate square lattice
            n_side = int(np.ceil(np.sqrt(n_assemblies)))
            self.lattice_size = (n_side, n_side)
        else:
            self.lattice_size = lattice_size
        
        # Assembly data storage
        self.assemblies: Dict[int, AssemblyBurnup] = {}
        
        logger.debug(f"AssemblyWiseBurnupTracker initialized: {n_assemblies} assemblies")
    
    def get_assembly_position(self, assembly_id: int) -> Tuple[int, int]:
        """
        Get assembly position in lattice.
        
        Args:
            assembly_id: Assembly identifier (0-indexed).
        
        Returns:
            (row, col) tuple.
        """
        if assembly_id < 0 or assembly_id >= self.n_assemblies:
            raise ValueError(f"assembly_id must be 0-{self.n_assemblies-1}, got {assembly_id}")
        
        row = assembly_id // self.lattice_size[1]
        col = assembly_id % self.lattice_size[1]
        
        return (row, col)
    
    def update_assembly(
        self,
        assembly_id: int,
        position: Tuple[int, int],
        burnup: float,
        enrichment: float = 0.045,
        peak_power: float = 0.0,
        nuclide_inventory: Optional[NuclideInventory] = None,
    ):
        """
        Update burnup data for an assembly.
        
        Args:
            assembly_id: Assembly identifier.
            position: Assembly position (row, col).
            burnup: Burnup [MWd/kgU].
            enrichment: Average enrichment [fraction].
            peak_power: Peak power density [W/cm³].
            nuclide_inventory: Optional NuclideInventory for this assembly.
        """
        self.assemblies[assembly_id] = AssemblyBurnup(
            assembly_id=f"Assembly-{assembly_id}",
            position=position,
            burnup=burnup,
            average_enrichment=enrichment,
            peak_power=peak_power,
            nuclide_inventory=nuclide_inventory,
        )
    
    def get_burnup_distribution(self) -> np.ndarray:
        """
        Get burnup distribution across assemblies.
        
        Returns:
            2D array [rows, cols] with burnup values [MWd/kgU].
        """
        distribution = np.zeros(self.lattice_size)
        
        for assembly_id, assembly in self.assemblies.items():
            row, col = assembly.position
            if 0 <= row < self.lattice_size[0] and 0 <= col < self.lattice_size[1]:
                distribution[row, col] = assembly.burnup
        
        return distribution
    
    def get_average_burnup(self) -> float:
        """
        Get average burnup across all assemblies.
        
        Returns:
            Average burnup [MWd/kgU].
        """
        if not self.assemblies:
            return 0.0
        
        burnups = [a.burnup for a in self.assemblies.values()]
        return np.mean(burnups)
    
    def get_peak_burnup(self) -> float:
        """
        Get peak burnup across all assemblies.
        
        Returns:
            Peak burnup [MWd/kgU].
        """
        if not self.assemblies:
            return 0.0
        
        burnups = [a.burnup for a in self.assemblies.values()]
        return np.max(burnups)


class RodWiseBurnupTracker:
    """
    Fuel rod-wise burnup tracking within a fuel assembly.
    
    Tracks burnup distribution within a single fuel assembly, accounting for:
    - Intra-assembly flux gradients
    - Control rod shadowing effects
    - Rod-to-rod enrichment variation
    - Gadolinium distribution
    
    Usage:
        >>> from smrforge.burnup.lwr_burnup import RodWiseBurnupTracker
        >>> 
        >>> # 17x17 assembly
        >>> tracker = RodWiseBurnupTracker(assembly_size=(17, 17))
        >>> 
        >>> # Track burnup for each rod
        >>> for rod_id in range(17 * 17):
        ...     position = tracker.get_rod_position(rod_id)
        ...     burnup = calculate_rod_burnup(rod_id)
        ...     shadowing = calculate_shadowing(position, control_rods)
        ...     tracker.update_rod(rod_id, position, burnup, shadowing_factor=shadowing)
        >>> 
        >>> # Get burnup distribution
        >>> distribution = tracker.get_burnup_distribution()
    """
    
    def __init__(self, assembly_size: Tuple[int, int]):
        """
        Initialize rod-wise burnup tracker.
        
        Args:
            assembly_size: (rows, cols) tuple for assembly lattice (e.g., (17, 17)).
        """
        self.assembly_size = assembly_size
        self.n_rods = assembly_size[0] * assembly_size[1]
        
        # Rod data storage
        self.rods: Dict[int, RodBurnup] = {}
        
        logger.debug(f"RodWiseBurnupTracker initialized: {self.n_rods} rods")
    
    def get_rod_position(self, rod_id: int) -> Tuple[int, int]:
        """
        Get rod position within assembly.
        
        Args:
            rod_id: Rod identifier (0-indexed).
        
        Returns:
            (row, col) tuple.
        """
        if rod_id < 0 or rod_id >= self.n_rods:
            raise ValueError(f"rod_id must be 0-{self.n_rods-1}, got {rod_id}")
        
        row = rod_id // self.assembly_size[1]
        col = rod_id % self.assembly_size[1]
        
        return (row, col)
    
    def calculate_shadowing_factor(
        self,
        rod_position: Tuple[int, int],
        control_rod_positions: List[Tuple[int, int]],
        pitch: float = 1.26,  # cm (typical PWR pitch)
    ) -> float:
        """
        Calculate control rod shadowing factor for a rod.
        
        Rods near control rods experience reduced flux due to shadowing.
        Shadowing factor: 1.0 = no shadowing, 0.0 = fully shadowed.
        
        Args:
            rod_position: Rod position (row, col).
            control_rod_positions: List of control rod positions [(row, col), ...].
            pitch: Rod pitch [cm].
        
        Returns:
            Shadowing factor (0.0 to 1.0).
        """
        if not control_rod_positions:
            return 1.0
        
        # Vectorized distance calculation for better performance
        if control_rod_positions:
            cr_positions = np.array(control_rod_positions)  # [n_rods, 2]
            rod_pos = np.array(rod_position)  # [2]
            
            # Vectorized: compute distances to all control rods at once
            # [n_rods, 2] - [2] = [n_rods, 2] (broadcasting)
            deltas = cr_positions - rod_pos
            distances = np.sqrt(np.sum(deltas**2, axis=1)) * pitch  # [n_rods]
            min_distance = np.min(distances)
        else:
            min_distance = float('inf')
        
        # Shadowing decreases with distance
        # Simplified model: shadowing factor = 1 - exp(-distance / characteristic_length)
        characteristic_length = 5.0 * pitch  # ~5 rod pitches
        shadowing = 1.0 - 0.3 * np.exp(-min_distance / characteristic_length)
        
        return max(0.0, min(1.0, shadowing))
    
    def update_rod(
        self,
        rod_id: int,
        position: Tuple[int, int],
        burnup: float,
        enrichment: float = 0.045,
        gadolinium_content: float = 0.0,
        control_rod_proximity: float = 0.0,
        shadowing_factor: float = 1.0,
    ):
        """
        Update burnup data for a rod.
        
        Args:
            rod_id: Rod identifier.
            position: Rod position (row, col).
            burnup: Burnup [MWd/kgU].
            enrichment: Enrichment [fraction].
            gadolinium_content: Gadolinium content [atoms/cm³].
            control_rod_proximity: Distance to nearest control rod [cm].
            shadowing_factor: Control rod shadowing factor (0.0 to 1.0).
        """
        self.rods[rod_id] = RodBurnup(
            rod_id=f"Rod-{rod_id}",
            position=position,
            burnup=burnup,
            enrichment=enrichment,
            gadolinium_content=gadolinium_content,
            control_rod_proximity=control_rod_proximity,
            shadowing_factor=shadowing_factor,
        )
    
    def get_burnup_distribution(self) -> np.ndarray:
        """
        Get burnup distribution within assembly.
        
        Returns:
            2D array [rows, cols] with burnup values [MWd/kgU].
        """
        distribution = np.zeros(self.assembly_size)
        
        for rod_id, rod in self.rods.items():
            row, col = rod.position
            if 0 <= row < self.assembly_size[0] and 0 <= col < self.assembly_size[1]:
                distribution[row, col] = rod.burnup
        
        return distribution
    
    def get_average_burnup(self) -> float:
        """
        Get average burnup across all rods.
        
        Returns:
            Average burnup [MWd/kgU].
        """
        if not self.rods:
            return 0.0
        
        burnups = [r.burnup for r in self.rods.values()]
        return np.mean(burnups)
    
    def get_peak_burnup(self) -> float:
        """
        Get peak burnup across all rods.
        
        Returns:
            Peak burnup [MWd/kgU].
        """
        if not self.rods:
            return 0.0
        
        burnups = [r.burnup for r in self.rods.values()]
        return np.max(burnups)
