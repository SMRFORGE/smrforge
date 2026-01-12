"""
Advanced control rod worth calculations for SMRs.

Provides sophisticated reactivity worth calculations for control rods,
including flux-weighted worth, worth profiles, and worth interpolation.
"""

import numpy as np
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from ..utils.logging import get_logger

logger = get_logger("smrforge.core.control_rod_worth")


@dataclass
class WorthProfile:
    """
    Axial worth profile for control rods.
    
    Represents how reactivity worth varies with axial position.
    Typically, worth is higher in the center of the core where flux is highest.
    
    Attributes:
        positions: Axial positions [cm] (normalized 0-1 or absolute)
        worth_fractions: Worth fraction at each position (0-1)
        profile_type: Type of profile ("uniform", "cosine", "parabolic", "custom")
    """
    
    positions: np.ndarray  # [n_points] normalized (0-1) or absolute [cm]
    worth_fractions: np.ndarray  # [n_points] worth fraction (0-1)
    profile_type: str = "custom"  # "uniform", "cosine", "parabolic", "custom"
    
    def get_worth_fraction(self, position: float) -> float:
        """
        Get worth fraction at a specific axial position.
        
        Args:
            position: Axial position (normalized 0-1 or absolute [cm])
        
        Returns:
            Worth fraction (0-1)
        """
        # Normalize position if needed
        if position > 1.0:
            # Assume absolute position, normalize by max
            position = position / np.max(self.positions) if np.max(self.positions) > 0 else 0.0
        
        # Interpolate
        return np.interp(position, self.positions, self.worth_fractions)
    
    @classmethod
    def uniform(cls, n_points: int = 20) -> "WorthProfile":
        """Create uniform worth profile (constant worth)."""
        positions = np.linspace(0.0, 1.0, n_points)
        worth_fractions = np.ones(n_points)
        return cls(positions, worth_fractions, profile_type="uniform")
    
    @classmethod
    def cosine(cls, n_points: int = 20, peak_position: float = 0.5) -> "WorthProfile":
        """
        Create cosine worth profile (peaked at center).
        
        Args:
            n_points: Number of profile points
            peak_position: Position of peak (0-1, default 0.5 = center)
        """
        positions = np.linspace(0.0, 1.0, n_points)
        # Cosine shape: cos(π * (x - peak) / width)
        # Normalize so max = 1.0
        worth_fractions = np.cos(np.pi * (positions - peak_position))
        worth_fractions = (worth_fractions + 1.0) / 2.0  # Normalize to 0-1
        return cls(positions, worth_fractions, profile_type="cosine")
    
    @classmethod
    def parabolic(cls, n_points: int = 20, peak_position: float = 0.5) -> "WorthProfile":
        """
        Create parabolic worth profile (peaked at center).
        
        Args:
            n_points: Number of profile points
            peak_position: Position of peak (0-1, default 0.5 = center)
        """
        positions = np.linspace(0.0, 1.0, n_points)
        # Parabolic: 1 - 4*(x - peak)^2
        worth_fractions = 1.0 - 4.0 * (positions - peak_position) ** 2
        worth_fractions = np.clip(worth_fractions, 0.0, 1.0)
        return cls(positions, worth_fractions, profile_type="parabolic")


@dataclass
class ControlRodWorthCalculator:
    """
    Advanced control rod worth calculator for SMRs.
    
    Calculates reactivity worth using flux-weighted methods and worth profiles.
    Supports both analytical and numerical worth calculations.
    
    Attributes:
        max_worth: Maximum reactivity worth when fully inserted [pcm or dk/k]
        worth_profile: Axial worth profile
        flux_shape: Optional flux shape function for flux-weighted worth
        worth_interpolation: Method for worth interpolation ("linear", "cubic")
    """
    
    max_worth: float  # pcm or dk/k
    worth_profile: Optional[WorthProfile] = None
    flux_shape: Optional[Callable[[float], float]] = None
    worth_interpolation: str = "linear"
    
    def __post_init__(self):
        """Initialize default worth profile if not provided."""
        if self.worth_profile is None:
            self.worth_profile = WorthProfile.cosine()
    
    def calculate_worth(
        self,
        insertion: float,
        flux: Optional[np.ndarray] = None,
        axial_positions: Optional[np.ndarray] = None,
    ) -> float:
        """
        Calculate reactivity worth at given insertion.
        
        Args:
            insertion: Insertion fraction (0.0 = fully withdrawn, 1.0 = fully inserted)
            flux: Optional flux distribution [n_axial] for flux-weighted worth
            axial_positions: Optional axial positions [cm] corresponding to flux
        
        Returns:
            Reactivity worth [pcm or dk/k]
        """
        insertion = np.clip(insertion, 0.0, 1.0)
        
        if insertion == 0.0:
            return 0.0  # Fully withdrawn = no worth
        
        if flux is not None and axial_positions is not None:
            # Flux-weighted worth calculation
            return self._calculate_flux_weighted_worth(insertion, flux, axial_positions)
        else:
            # Simple profile-based calculation
            return self._calculate_profile_based_worth(insertion)
    
    def _calculate_profile_based_worth(self, insertion: float) -> float:
        """Calculate worth using worth profile."""
        if self.worth_profile is None:
            # Uniform worth
            return self.max_worth * insertion
        
        # Integrate worth profile over inserted length
        n_points = 50
        positions = np.linspace(0.0, insertion, n_points)
        
        total_worth = 0.0
        for pos in positions:
            worth_fraction = self.worth_profile.get_worth_fraction(pos)
            total_worth += worth_fraction
        
        # Average and scale
        avg_worth_fraction = total_worth / n_points
        return self.max_worth * avg_worth_fraction * insertion
    
    def _calculate_flux_weighted_worth(
        self,
        insertion: float,
        flux: np.ndarray,
        axial_positions: np.ndarray,
    ) -> float:
        """
        Calculate flux-weighted worth.
        
        Worth is weighted by local flux, so regions with higher flux
        contribute more to reactivity worth.
        """
        # Normalize positions to 0-1
        if np.max(axial_positions) > 1.0:
            axial_positions_norm = axial_positions / np.max(axial_positions)
        else:
            axial_positions_norm = axial_positions
        
        # Find inserted region
        inserted_mask = axial_positions_norm <= insertion
        
        if not np.any(inserted_mask):
            return 0.0
        
        # Get flux and worth profile in inserted region
        inserted_flux = flux[inserted_mask]
        inserted_positions = axial_positions_norm[inserted_mask]
        
        # Calculate worth fraction at each position
        worth_fractions = np.array([
            self.worth_profile.get_worth_fraction(pos)
            for pos in inserted_positions
        ])
        
        # Flux-weighted average
        if np.sum(inserted_flux) > 0:
            flux_weighted_worth = np.sum(inserted_flux * worth_fractions) / np.sum(inserted_flux)
        else:
            flux_weighted_worth = np.mean(worth_fractions)
        
        # Scale by insertion and max worth
        return self.max_worth * flux_weighted_worth * insertion
    
    def calculate_worth_gradient(
        self,
        insertion: float,
        delta_insertion: float = 0.01,
    ) -> float:
        """
        Calculate worth gradient (dρ/d(insertion)).
        
        Useful for control rod worth sensitivity analysis.
        
        Args:
            insertion: Current insertion fraction
            delta_insertion: Small change in insertion for gradient calculation
        
        Returns:
            Worth gradient [pcm per insertion fraction]
        """
        worth1 = self.calculate_worth(insertion)
        worth2 = self.calculate_worth(insertion + delta_insertion)
        
        return (worth2 - worth1) / delta_insertion
    
    def interpolate_worth(
        self,
        insertions: np.ndarray,
        calculated_worths: np.ndarray,
        target_insertion: float,
    ) -> float:
        """
        Interpolate worth at target insertion from calculated values.
        
        Args:
            insertions: Array of insertion fractions where worth was calculated
            calculated_worths: Array of calculated worth values
            target_insertion: Target insertion fraction
        
        Returns:
            Interpolated worth
        """
        if self.worth_interpolation == "cubic":
            from scipy.interpolate import interp1d
            interp_func = interp1d(insertions, calculated_worths, kind="cubic", fill_value="extrapolate")
            return float(interp_func(target_insertion))
        else:
            # Linear interpolation
            return float(np.interp(target_insertion, insertions, calculated_worths))


def calculate_rod_worth_from_neutronics(
    k_eff_without_rod: float,
    k_eff_with_rod: float,
) -> float:
    """
    Calculate control rod worth from neutronics calculations.
    
    Worth is calculated as: ρ = (k_eff_without - k_eff_with) / k_eff_without
    
    Args:
        k_eff_without_rod: k-eff without control rod
        k_eff_with_rod: k-eff with control rod inserted
    
    Returns:
        Reactivity worth [dk/k] (can be converted to pcm: worth_pcm = worth_dk_k * 1e5)
    """
    if k_eff_without_rod <= 0:
        raise ValueError("k_eff_without_rod must be > 0")
    
    worth_dk_k = (k_eff_without_rod - k_eff_with_rod) / k_eff_without_rod
    
    return worth_dk_k


def calculate_rod_worth_pcm(
    k_eff_without_rod: float,
    k_eff_with_rod: float,
) -> float:
    """
    Calculate control rod worth in pcm (per cent mille).
    
    Args:
        k_eff_without_rod: k-eff without control rod
        k_eff_with_rod: k-eff with control rod inserted
    
    Returns:
        Reactivity worth [pcm]
    """
    worth_dk_k = calculate_rod_worth_from_neutronics(k_eff_without_rod, k_eff_with_rod)
    return worth_dk_k * 1e5  # Convert to pcm


def calculate_worth_profile_from_neutronics(
    insertions: np.ndarray,
    k_eff_values: np.ndarray,
    k_eff_critical: float = 1.0,
) -> Tuple[np.ndarray, WorthProfile]:
    """
    Calculate worth profile from neutronics calculations at different insertions.
    
    Args:
        insertions: Array of insertion fractions (0-1)
        k_eff_values: Array of k-eff values at each insertion
        k_eff_critical: Critical k-eff (default 1.0)
    
    Returns:
        Tuple of (worths [pcm], WorthProfile)
    """
    # Calculate worth at each insertion
    worths = np.array([
        calculate_rod_worth_pcm(k_eff_critical, k_eff)
        for k_eff in k_eff_values
    ])
    
    # Normalize to 0-1 for profile
    max_worth = np.max(worths) if np.max(worths) > 0 else 1.0
    worth_fractions = worths / max_worth
    
    # Create worth profile
    profile = WorthProfile(
        positions=insertions,
        worth_fractions=worth_fractions,
        profile_type="custom",
    )
    
    return worths, profile
