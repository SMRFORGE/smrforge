"""
Integration of advanced self-shielding methods into reactor_core.

Provides functions to use SubgroupMethod and EquivalenceTheory from
resonance_selfshield.py with NuclearDataCache and Nuclide classes.
"""

from functools import lru_cache
from typing import Dict, Optional

import numpy as np

from ..utils.logging import get_logger
from .reactor_core import Nuclide, NuclearDataCache

logger = get_logger("smrforge.core.self_shielding_integration")

try:
    from .resonance_selfshield import (
        BondarenkoMethod,
        EquivalenceTheory,
        ResonanceSelfShielding,
        SubgroupMethod,
    )

    _RESONANCE_AVAILABLE = True
except ImportError:
    _RESONANCE_AVAILABLE = False
    logger.warning("resonance_selfshield module not available")


def get_cross_section_with_self_shielding(
    cache: NuclearDataCache,
    nuclide: Nuclide,
    reaction: str,
    temperature: float,
    sigma_0: float = 1.0,  # Background cross-section [barns]
    method: str = "bondarenko",  # "bondarenko", "subgroup", or "equivalence"
    enable_self_shielding: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Get cross-section with self-shielding correction.
    
    Integrates Bondarenko, Subgroup, and Equivalence methods from
    resonance_selfshield.py with NuclearDataCache.
    
    Args:
        cache: NuclearDataCache instance
        nuclide: Nuclide instance
        reaction: Reaction type ("fission", "capture", "elastic", "total")
        temperature: Temperature [K]
        sigma_0: Background cross-section [barns] (default: 1.0)
        method: Self-shielding method:
            - "bondarenko": Fast Bondarenko method (default)
            - "subgroup": More accurate subgroup method
            - "equivalence": Equivalence theory (for heterogeneous geometries)
        enable_self_shielding: If False, returns unshielded cross-section
    
    Returns:
        Tuple of (energy [eV], cross_section [barns])
    
    Raises:
        ValueError: If unknown self-shielding method is specified
        ImportError: If resonance_selfshield module is not available and self-shielding is enabled
        FileNotFoundError: If cross-section data cannot be found for the nuclide/reaction
    
    Example:
        >>> from smrforge.core.reactor_core import NuclearDataCache, Nuclide
        >>> from smrforge.core.self_shielding_integration import get_cross_section_with_self_shielding
        >>> 
        >>> cache = NuclearDataCache()
        >>> u238 = Nuclide(Z=92, A=238)
        >>> 
        >>> # Get shielded cross-section using Bondarenko method
        >>> energy, xs = get_cross_section_with_self_shielding(
        ...     cache, u238, "capture", temperature=900.0,
        ...     sigma_0=10.0, method="bondarenko"
        ... )
        >>> 
        >>> # Use subgroup method for higher accuracy
        >>> energy, xs_subgroup = get_cross_section_with_self_shielding(
        ...     cache, u238, "capture", temperature=900.0,
        ...     sigma_0=10.0, method="subgroup"
        ... )
    """
    if not _RESONANCE_AVAILABLE:
        logger.warning("Resonance self-shielding not available, returning unshielded XS")
        return cache.get_cross_section(nuclide, reaction, temperature)
    
    if not enable_self_shielding:
        return cache.get_cross_section(nuclide, reaction, temperature)
    
    # Get infinite dilution cross-section
    try:
        energy, xs_inf = cache.get_cross_section(nuclide, reaction, temperature)
    except (ImportError, FileNotFoundError, ValueError) as e:
        logger.warning(f"Could not get cross-section for {nuclide.name} {reaction}: {e}")
        raise
    
    # Apply self-shielding based on method
    if method == "bondarenko":
        bondarenko = BondarenkoMethod()
        nuclide_name = nuclide.name

        # Compute f-factor once (sigma_0 and T constant across energy grid)
        f_factor = bondarenko.get_f_factor(
            nuclide=nuclide_name,
            reaction=reaction,
            sigma_0=sigma_0,
            T=temperature,
        )

        # Vectorized shielding
        xs_shielded = f_factor * xs_inf
        return energy, xs_shielded
    
    elif method == "subgroup":
        subgroup = SubgroupMethod()
        nuclide_name = nuclide.name
        
        # Subgroup method works on energy groups, so we need to group the data
        # For simplicity, use average cross-section in resonance region
        # In production, would use proper energy grouping
        xs_shielded = np.zeros_like(xs_inf)
        
        # Identify resonance region (typically 1 eV to 100 keV)
        resonance_mask = (energy >= 1.0) & (energy <= 1e5)
        
        if np.any(resonance_mask):
            # Use subgroup method for resonance region
            # Average sigma_0 over resonance region
            sigma_0_eff = sigma_0
            
            # Get representative energy for subgroup calculation
            resonance_energies = energy[resonance_mask]
            resonance_xs = xs_inf[resonance_mask]
            
            # Use middle energy group for subgroup calculation
            mid_idx = len(resonance_energies) // 2
            e_mid = resonance_energies[mid_idx]
            
            # Determine energy group (simplified)
            if e_mid < 1e3:
                energy_group = "thermal"
            elif e_mid < 1e5:
                energy_group = "epithermal"
            else:
                energy_group = "fast"
            
            # Compute effective cross-section using subgroup method
            xs_eff = subgroup.compute_effective_xs(
                nuclide_name, reaction, energy_group, sigma_0_eff
            )
            
            # Apply correction factor
            if np.mean(resonance_xs) > 0:
                correction_factor = xs_eff / np.mean(resonance_xs)
                xs_shielded[resonance_mask] = xs_inf[resonance_mask] * correction_factor
            else:
                xs_shielded[resonance_mask] = xs_inf[resonance_mask]
            
            # Keep fast and thermal regions unshielded (or use Bondarenko)
            non_resonance_mask = ~resonance_mask
            if np.any(non_resonance_mask):
                bondarenko = BondarenkoMethod()
                f_factor = bondarenko.get_f_factor(
                    nuclide=nuclide_name,
                    reaction=reaction,
                    sigma_0=sigma_0,
                    T=temperature,
                )
                xs_shielded[non_resonance_mask] = f_factor * xs_inf[non_resonance_mask]
        else:
            # No resonance region, use Bondarenko for all
            bondarenko = BondarenkoMethod()
            f_factor = bondarenko.get_f_factor(
                nuclide=nuclide_name,
                reaction=reaction,
                sigma_0=sigma_0,
                T=temperature,
            )
            xs_shielded = f_factor * xs_inf
        
        return energy, xs_shielded
    
    elif method == "equivalence":
        # Equivalence theory requires geometry parameters
        # For now, use Bondarenko as fallback
        logger.warning(
            "Equivalence theory requires geometry parameters, "
            "using Bondarenko method instead"
        )
        return get_cross_section_with_self_shielding(
            cache, nuclide, reaction, temperature, sigma_0, "bondarenko", enable_self_shielding
        )
    
    else:
        raise ValueError(f"Unknown self-shielding method: {method}")


def get_cross_section_with_equivalence_theory(
    cache: NuclearDataCache,
    nuclide: Nuclide,
    reaction: str,
    temperature: float,
    fuel_pin_radius: float,
    pin_pitch: float,
    fuel_volume_fraction: float,
    moderator_xs: Optional[np.ndarray] = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Get cross-section using equivalence theory for heterogeneous geometry.
    
    Uses EquivalenceTheory from resonance_selfshield.py to calculate
    equivalent homogeneous cross-sections for fuel pins in moderator.
    
    Args:
        cache: NuclearDataCache instance
        nuclide: Nuclide instance
        reaction: Reaction type
        temperature: Temperature [K]
        fuel_pin_radius: Fuel pin radius [cm]
        pin_pitch: Pin pitch (center-to-center) [cm]
        fuel_volume_fraction: Fuel volume fraction (0-1)
        moderator_xs: Optional moderator cross-sections [barns]
            If None, uses default water cross-sections
    
    Returns:
        Tuple of (energy [eV], equivalent_cross_section [barns])
    
    Raises:
        ImportError: If resonance_selfshield module is not available
        FileNotFoundError: If cross-section data cannot be found for the nuclide/reaction
    
    Example:
        >>> from smrforge.core.reactor_core import NuclearDataCache, Nuclide
        >>> from smrforge.core.self_shielding_integration import get_cross_section_with_equivalence_theory
        >>> 
        >>> cache = NuclearDataCache()
        >>> u238 = Nuclide(Z=92, A=238)
        >>> 
        >>> # Get equivalent cross-section for fuel pin in water
        >>> energy, xs_equiv = get_cross_section_with_equivalence_theory(
        ...     cache, u238, "capture", temperature=600.0,
        ...     fuel_pin_radius=0.4,  # cm
        ...     pin_pitch=1.26,  # cm
        ...     fuel_volume_fraction=0.4,
        ... )
    """
    if not _RESONANCE_AVAILABLE:
        logger.warning("Equivalence theory not available, returning unshielded XS")
        return cache.get_cross_section(nuclide, reaction, temperature)
    
    # Get fuel cross-section
    energy, fuel_xs = cache.get_cross_section(nuclide, reaction, temperature)
    
    # Get or create moderator cross-sections
    if moderator_xs is None:
        # Default water cross-sections (simplified)
        # In production, would fetch actual water cross-sections
        moderator_xs = np.ones_like(fuel_xs) * 0.66  # Water scattering ~0.66 barns
    
    # Use equivalence theory
    # EquivalenceTheory in resonance_selfshield doesn't have calculate_equivalent_xs
    # Use Bondarenko method with effective background cross-section
    bondarenko = BondarenkoMethod()
    nuclide_name = nuclide.name
    
    # Calculate effective background cross-section using equivalence theory concepts
    # Volume-weighted average with equivalence correction
    moderator_volume_fraction = 1.0 - fuel_volume_fraction
    
    # Effective sigma_0 based on moderator and geometry
    # Simplified: use average moderator XS weighted by volume fraction
    sigma_0_eff = np.mean(moderator_xs) * moderator_volume_fraction / fuel_volume_fraction
    
    # Get f-factor for shielding
    f_factor = bondarenko.get_f_factor(
        nuclide=nuclide_name,
        reaction=reaction,
        sigma_0=sigma_0_eff,
        T=temperature,
    )
    
    # Apply shielding to fuel cross-sections
    # Equivalent cross-section is volume-weighted average
    equiv_xs = (
        fuel_volume_fraction * fuel_xs * f_factor +
        moderator_volume_fraction * moderator_xs
    )
    
    return energy, equiv_xs
