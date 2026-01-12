"""
Advanced multi-group processing methods for SMR neutronics.

Implements SPH (Superhomogenization) method and equivalence theory for
improved accuracy in multi-group cross-section collapse, especially for
heterogeneous fuel assemblies in SMRs.
"""

import numpy as np
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..utils.logging import get_logger

logger = get_logger("smrforge.core.multigroup_advanced")


@dataclass
class SPHFactors:
    """
    Superhomogenization (SPH) factors for multi-group cross-section correction.
    
    SPH factors correct homogenized cross-sections to preserve reaction rates
    in heterogeneous geometries (e.g., fuel pins in water moderator).
    
    Attributes:
        nuclide: Nuclide name
        reaction: Reaction type
        groups: Energy group indices
        sph_factors: SPH factors [n_groups] (typically 0.8-1.2)
        flux_fine: Fine-group flux used for SPH calculation
        flux_coarse: Coarse-group flux used for SPH calculation
    """
    
    nuclide: str
    reaction: str
    groups: np.ndarray
    sph_factors: np.ndarray  # [n_groups]
    flux_fine: Optional[np.ndarray] = None
    flux_coarse: Optional[np.ndarray] = None


class SPHMethod:
    """
    Superhomogenization (SPH) method for multi-group cross-section correction.
    
    SPH factors correct homogenized cross-sections to preserve reaction rates
    when collapsing from fine-group to coarse-group structures. Essential for
    accurate SMR neutronics calculations with heterogeneous fuel assemblies.
    
    The SPH factor μ_g for group g is defined as:
        μ_g = Σ_fine_g / Σ_coarse_g
    
    Where:
        Σ_fine_g = fine-group cross-section (preserves reaction rates)
        Σ_coarse_g = coarse-group cross-section (standard collapse)
    
    Usage:
        >>> from smrforge.core.multigroup_advanced import SPHMethod
        >>> from smrforge.core.reactor_core import Nuclide
        >>> 
        >>> sph = SPHMethod()
        >>> u238 = Nuclide(Z=92, A=238)
        >>> 
        >>> # Calculate SPH factors
        >>> factors = sph.calculate_sph_factors(
        ...     nuclide=u238,
        ...     reaction="capture",
        ...     fine_group_structure=np.logspace(7, -5, 100),  # 100 fine groups
        ...     coarse_group_structure=np.array([2e7, 1e6, 1e5, 1e4, 1e-5]),  # 4 coarse groups
        ...     fine_flux=fine_flux,  # Fine-group flux
        ...     temperature=900.0,
        ... )
        >>> 
        >>> # Apply SPH correction to coarse-group cross-sections
        >>> corrected_xs = sph.apply_sph_correction(coarse_xs, factors)
    """
    
    def __init__(self):
        """Initialize SPH method."""
        self._sph_cache: Dict[str, SPHFactors] = {}
    
    def calculate_sph_factors(
        self,
        nuclide,
        reaction: str,
        fine_group_structure: np.ndarray,
        coarse_group_structure: np.ndarray,
        fine_flux: np.ndarray,
        temperature: float = 900.0,
        cache: Optional[Any] = None,
    ) -> SPHFactors:
        """
        Calculate SPH factors for a nuclide/reaction.
        
        SPH factors preserve reaction rates when collapsing from fine-group
        to coarse-group structures. This is critical for heterogeneous
        geometries like fuel pins in water moderator.
        
        Args:
            nuclide: Nuclide instance
            reaction: Reaction type (e.g., "capture", "fission")
            fine_group_structure: Fine-group energy boundaries [eV] (descending)
            coarse_group_structure: Coarse-group energy boundaries [eV] (descending)
            fine_flux: Fine-group flux [n_fine_groups]
            temperature: Temperature [K]
            cache: Optional NuclearDataCache instance
        
        Returns:
            SPHFactors object with SPH factors for each coarse group
        """
        from .reactor_core import NuclearDataCache, CrossSectionTable
        
        if cache is None:
            cache = NuclearDataCache()
        
        # Get continuous-energy cross-section
        energy, xs = cache.get_cross_section(nuclide, reaction, temperature)
        
        # Collapse to fine groups (preserves reaction rates)
        fine_xs = CrossSectionTable._collapse_to_multigroup(
            energy, xs, fine_group_structure, weighting_flux=None
        )
        
        # Collapse to coarse groups (standard method)
        coarse_xs = CrossSectionTable._collapse_to_multigroup(
            energy, xs, coarse_group_structure, weighting_flux=None
        )
        
        # Calculate fine-group flux-weighted cross-sections
        fine_flux_weighted_xs = self._calculate_flux_weighted_xs(
            fine_group_structure, fine_xs, fine_flux
        )
        
        # Map fine groups to coarse groups and calculate SPH factors
        n_coarse = len(coarse_group_structure) - 1
        sph_factors = np.ones(n_coarse)
        groups = np.arange(n_coarse)
        
        for g_coarse in range(n_coarse):
            # Find fine groups that map to this coarse group
            fine_groups_in_coarse = self._map_fine_to_coarse(
                fine_group_structure, coarse_group_structure, g_coarse
            )
            
            if len(fine_groups_in_coarse) > 0:
                # Calculate reaction rate in fine groups
                fine_reaction_rate = np.sum(
                    fine_flux_weighted_xs[fine_groups_in_coarse] *
                    fine_flux[fine_groups_in_coarse]
                )
                
                # Calculate reaction rate in coarse group (standard collapse)
                coarse_reaction_rate = coarse_xs[g_coarse] * np.sum(
                    fine_flux[fine_groups_in_coarse]
                )
                
                # SPH factor preserves reaction rate
                if coarse_reaction_rate > 0:
                    sph_factors[g_coarse] = fine_reaction_rate / coarse_reaction_rate
                else:
                    sph_factors[g_coarse] = 1.0
            else:
                sph_factors[g_coarse] = 1.0
        
        # Create SPHFactors object
        factors = SPHFactors(
            nuclide=nuclide.name,
            reaction=reaction,
            groups=groups,
            sph_factors=sph_factors,
            flux_fine=fine_flux,
        )
        
        # Cache results
        cache_key = f"{nuclide.name}/{reaction}/{temperature:.1f}K"
        self._sph_cache[cache_key] = factors
        
        return factors
    
    def apply_sph_correction(
        self,
        coarse_xs: np.ndarray,
        sph_factors: SPHFactors,
    ) -> np.ndarray:
        """
        Apply SPH correction to coarse-group cross-sections.
        
        Args:
            coarse_xs: Coarse-group cross-sections [n_coarse_groups]
            sph_factors: SPHFactors object
        
        Returns:
            SPH-corrected cross-sections [n_coarse_groups]
        """
        if len(coarse_xs) != len(sph_factors.sph_factors):
            raise ValueError(
                f"Cross-section length ({len(coarse_xs)}) must match "
                f"SPH factors length ({len(sph_factors.sph_factors)})"
            )
        
        return coarse_xs * sph_factors.sph_factors
    
    def _calculate_flux_weighted_xs(
        self,
        group_structure: np.ndarray,
        xs: np.ndarray,
        flux: np.ndarray,
    ) -> np.ndarray:
        """Calculate flux-weighted cross-sections."""
        # Simple flux-weighted average
        if np.sum(flux) > 0:
            return xs * flux / np.sum(flux)
        else:
            return xs
    
    def _map_fine_to_coarse(
        self,
        fine_structure: np.ndarray,
        coarse_structure: np.ndarray,
        coarse_group: int,
    ) -> np.ndarray:
        """Map fine groups to a coarse group."""
        # Get energy range for coarse group
        e_min_coarse = coarse_structure[coarse_group + 1]
        e_max_coarse = coarse_structure[coarse_group]
        
        # Find fine groups within this range
        fine_groups = []
        for g_fine in range(len(fine_structure) - 1):
            e_min_fine = fine_structure[g_fine + 1]
            e_max_fine = fine_structure[g_fine]
            
            # Check if fine group overlaps with coarse group
            if e_max_fine >= e_min_coarse and e_min_fine <= e_max_coarse:
                fine_groups.append(g_fine)
        
        return np.array(fine_groups)


@dataclass
class EquivalenceTheoryParams:
    """
    Parameters for equivalence theory (Bell-Wigner) method.
    
    Equivalence theory is used to homogenize fuel pin cross-sections
    in heterogeneous geometries (fuel + moderator).
    
    Attributes:
        fuel_xs: Fuel cross-sections [n_groups]
        moderator_xs: Moderator cross-sections [n_groups]
        fuel_volume_fraction: Fuel volume fraction (0-1)
        dancoff_factor: Dancoff factor (fuel pin interaction)
        escape_probability: Escape probability from fuel pin
    """
    
    fuel_xs: np.ndarray
    moderator_xs: np.ndarray
    fuel_volume_fraction: float
    dancoff_factor: float = 0.0
    escape_probability: float = 1.0


class EquivalenceTheory:
    """
    Equivalence theory (Bell-Wigner) for fuel pin homogenization.
    
    Used to calculate equivalent homogeneous cross-sections for fuel pins
    in heterogeneous geometries. Essential for accurate SMR neutronics
    with fuel assemblies.
    
    The method accounts for:
    - Fuel pin geometry (radius, pitch)
    - Moderator properties
    - Dancoff factor (fuel pin interaction)
    - Escape probability
    
    Usage:
        >>> from smrforge.core.multigroup_advanced import EquivalenceTheory
        >>> 
        >>> equiv = EquivalenceTheory()
        >>> 
        >>> # Calculate equivalent cross-sections
        >>> equiv_xs = equiv.calculate_equivalent_xs(
        ...     fuel_xs=fuel_cross_sections,
        ...     moderator_xs=moderator_cross_sections,
        ...     fuel_volume_fraction=0.4,
        ...     fuel_pin_radius=0.4,  # cm
        ...     pin_pitch=1.26,  # cm
        ... )
    """
    
    def calculate_equivalent_xs(
        self,
        fuel_xs: np.ndarray,
        moderator_xs: np.ndarray,
        fuel_volume_fraction: float,
        fuel_pin_radius: float = 0.4,  # cm
        pin_pitch: float = 1.26,  # cm
        dancoff_factor: Optional[float] = None,
    ) -> np.ndarray:
        """
        Calculate equivalent homogeneous cross-sections.
        
        Args:
            fuel_xs: Fuel cross-sections [n_groups]
            moderator_xs: Moderator cross-sections [n_groups]
            fuel_volume_fraction: Fuel volume fraction (0-1)
            fuel_pin_radius: Fuel pin radius [cm]
            pin_pitch: Pin pitch (center-to-center) [cm]
            dancoff_factor: Optional Dancoff factor (auto-calculated if None)
        
        Returns:
            Equivalent homogeneous cross-sections [n_groups]
        """
        if len(fuel_xs) != len(moderator_xs):
            raise ValueError(
                f"Fuel and moderator XS must have same length: "
                f"{len(fuel_xs)} vs {len(moderator_xs)}"
            )
        
        # Calculate Dancoff factor if not provided
        if dancoff_factor is None:
            dancoff_factor = self._calculate_dancoff_factor(
                fuel_pin_radius, pin_pitch
            )
        
        # Calculate escape probability
        escape_prob = self._calculate_escape_probability(
            fuel_pin_radius, pin_pitch, dancoff_factor
        )
        
        # Volume-weighted average with equivalence correction
        moderator_volume_fraction = 1.0 - fuel_volume_fraction
        
        # Equivalent cross-section
        equiv_xs = (
            fuel_volume_fraction * fuel_xs * escape_prob +
            moderator_volume_fraction * moderator_xs
        )
        
        return equiv_xs


def collapse_with_adjoint_weighting(
    fine_group_structure: np.ndarray,
    coarse_group_structure: np.ndarray,
    fine_cross_sections: np.ndarray,
    fine_flux: np.ndarray,
    fine_adjoint: np.ndarray,
) -> np.ndarray:
    """
    Collapse cross-sections using adjoint flux weighting.
    
    Adjoint flux weighting uses both forward and adjoint fluxes for importance-
    weighted cross-section collapse. This is more accurate than flux-weighted
    collapse for certain applications (e.g., reactivity worth calculations).
    
    The adjoint-weighted cross-section is:
        Σ_coarse_g = Σ_fine_g * (φ_fine * φ*_fine) / (φ_coarse * φ*_coarse)
    
    Where:
        φ_fine = fine-group forward flux
        φ*_fine = fine-group adjoint flux
        φ_coarse = coarse-group forward flux
        φ*_coarse = coarse-group adjoint flux
    
    Args:
        fine_group_structure: Fine-group energy boundaries [eV] [n_fine+1]
        coarse_group_structure: Coarse-group energy boundaries [eV] [n_coarse+1]
        fine_cross_sections: Fine-group cross-sections [n_fine] [barn]
        fine_flux: Fine-group forward flux [n_fine] [n/cm²/s]
        fine_adjoint: Fine-group adjoint flux [n_fine] [n/cm²/s]
    
    Returns:
        Coarse-group cross-sections [n_coarse] [barn]
    
    Example:
        >>> from smrforge.core.multigroup_advanced import collapse_with_adjoint_weighting
        >>> 
        >>> # Fine-group structure (100 groups)
        >>> fine_groups = np.logspace(7, -5, 101)
        >>> 
        >>> # Coarse-group structure (4 groups)
        >>> coarse_groups = np.array([2e7, 1e6, 1e5, 1e-5])
        >>> 
        >>> # Fine-group data
        >>> fine_xs = np.ones(100) * 5.0  # 5 barns
        >>> fine_flux = np.ones(100)  # Uniform flux
        >>> fine_adjoint = np.ones(100)  # Uniform adjoint
        >>> 
        >>> # Collapse with adjoint weighting
        >>> coarse_xs = collapse_with_adjoint_weighting(
        ...     fine_groups, coarse_groups, fine_xs, fine_flux, fine_adjoint
        ... )
    """
    n_fine = len(fine_group_structure) - 1
    n_coarse = len(coarse_group_structure) - 1
    
    if len(fine_cross_sections) != n_fine:
        raise ValueError(
            f"Fine cross-sections length ({len(fine_cross_sections)}) must match "
            f"fine groups ({n_fine})"
        )
    if len(fine_flux) != n_fine:
        raise ValueError(
            f"Fine flux length ({len(fine_flux)}) must match fine groups ({n_fine})"
        )
    if len(fine_adjoint) != n_fine:
        raise ValueError(
            f"Fine adjoint length ({len(fine_adjoint)}) must match fine groups ({n_fine})"
        )
    
    # Calculate importance (forward * adjoint)
    fine_importance = fine_flux * fine_adjoint
    
    # Collapse importance to coarse groups
    coarse_importance = np.zeros(n_coarse)
    coarse_flux = np.zeros(n_coarse)
    coarse_adjoint = np.zeros(n_coarse)
    
    # Map fine groups to coarse groups
    for g_fine in range(n_fine):
        # Find which coarse group this fine group belongs to
        E_low = fine_group_structure[g_fine]
        E_high = fine_group_structure[g_fine + 1]
        E_center = (E_low + E_high) / 2
        
        # Find coarse group index
        # Check if boundaries are in descending or ascending order
        is_descending = coarse_group_structure[0] > coarse_group_structure[-1]
        
        g_coarse = 0
        if is_descending:
            # Descending: [E_high, ..., E_low] -> groups: [E_high, E_mid), [E_mid, E_low)
            for c in range(n_coarse):
                low_bound = coarse_group_structure[c + 1]
                high_bound = coarse_group_structure[c]
                if low_bound <= E_center < high_bound:
                    g_coarse = c
                    break
            # Handle edge cases
            if E_center >= coarse_group_structure[0]:
                g_coarse = 0
            elif E_center < coarse_group_structure[-1]:
                g_coarse = n_coarse - 1
        else:
            # Ascending: [E_low, ..., E_high] -> groups: [E_low, E_mid), [E_mid, E_high)
            for c in range(n_coarse):
                if coarse_group_structure[c] <= E_center < coarse_group_structure[c + 1]:
                    g_coarse = c
                    break
            # Handle edge cases
            if E_center >= coarse_group_structure[-1]:
                g_coarse = n_coarse - 1
            elif E_center < coarse_group_structure[0]:
                g_coarse = 0
        
        # Group width
        dE = E_high - E_low
        
        # Accumulate importance-weighted quantities
        if 0 <= g_coarse < n_coarse:
            coarse_importance[g_coarse] += fine_importance[g_fine] * dE
            coarse_flux[g_coarse] += fine_flux[g_fine] * dE
            coarse_adjoint[g_coarse] += fine_adjoint[g_fine] * dE
    
    # Calculate adjoint-weighted cross-sections
    coarse_xs = np.zeros(n_coarse)
    
    for g_coarse in range(n_coarse):
        if coarse_importance[g_coarse] > 0:
            # Calculate weighted average
            numerator = 0.0
            denominator = 0.0
            
            for g_fine in range(n_fine):
                E_low = fine_group_structure[g_fine]
                E_high = fine_group_structure[g_fine + 1]
                E_center = (E_low + E_high) / 2
                
                # Find which coarse group this belongs to
                is_descending = coarse_group_structure[0] > coarse_group_structure[-1]
                g_coarse_check = 0
                if is_descending:
                    for c in range(n_coarse):
                        if coarse_group_structure[c + 1] <= E_center < coarse_group_structure[c]:
                            g_coarse_check = c
                            break
                    if E_center >= coarse_group_structure[0]:
                        g_coarse_check = 0
                    elif E_center < coarse_group_structure[-1]:
                        g_coarse_check = n_coarse - 1
                else:
                    for c in range(n_coarse):
                        if coarse_group_structure[c] <= E_center < coarse_group_structure[c + 1]:
                            g_coarse_check = c
                            break
                    if E_center >= coarse_group_structure[-1]:
                        g_coarse_check = n_coarse - 1
                    elif E_center < coarse_group_structure[0]:
                        g_coarse_check = 0
                
                if g_coarse_check == g_coarse:
                    dE = E_high - E_low
                    importance = fine_importance[g_fine]
                    numerator += fine_cross_sections[g_fine] * importance * dE
                    denominator += importance * dE
            
            if denominator > 0:
                coarse_xs[g_coarse] = numerator / denominator
            else:
                # Fallback to flux-weighted
                if coarse_flux[g_coarse] > 0:
                    numerator_flux = 0.0
                    for g_fine in range(n_fine):
                        E_low = fine_group_structure[g_fine]
                        E_high = fine_group_structure[g_fine + 1]
                        E_center = (E_low + E_high) / 2
                        
                        g_coarse_check = 0
                        for c in range(n_coarse):
                            if coarse_group_structure[c] <= E_center < coarse_group_structure[c + 1]:
                                g_coarse_check = c
                                break
                        if E_center >= coarse_group_structure[-1]:
                            g_coarse_check = n_coarse - 1
                        elif E_center < coarse_group_structure[0]:
                            g_coarse_check = 0
                        
                        if g_coarse_check == g_coarse:
                            dE = E_high - E_low
                            numerator_flux += fine_cross_sections[g_fine] * fine_flux[g_fine] * dE
                    coarse_xs[g_coarse] = numerator_flux / coarse_flux[g_coarse]
                else:
                    # Uniform collapse
                    count = 0
                    for g_fine in range(n_fine):
                        E_low = fine_group_structure[g_fine]
                        E_high = fine_group_structure[g_fine + 1]
                        E_center = (E_low + E_high) / 2
                        
                        g_coarse_check = 0
                        for c in range(n_coarse):
                            if coarse_group_structure[c] <= E_center < coarse_group_structure[c + 1]:
                                g_coarse_check = c
                                break
                        if E_center >= coarse_group_structure[-1]:
                            g_coarse_check = n_coarse - 1
                        elif E_center < coarse_group_structure[0]:
                            g_coarse_check = 0
                        
                        if g_coarse_check == g_coarse:
                            coarse_xs[g_coarse] += fine_cross_sections[g_fine]
                            count += 1
                    if count > 0:
                        coarse_xs[g_coarse] /= count
        else:
            # No importance in this group, use flux-weighted
            if coarse_flux[g_coarse] > 0:
                numerator = 0.0
                for g_fine in range(n_fine):
                    E_low = fine_group_structure[g_fine]
                    E_high = fine_group_structure[g_fine + 1]
                    E_center = (E_low + E_high) / 2
                    
                    g_coarse_check = 0
                    for c in range(n_coarse):
                        if coarse_group_structure[c] <= E_center < coarse_group_structure[c + 1]:
                            g_coarse_check = c
                            break
                    if E_center >= coarse_group_structure[-1]:
                        g_coarse_check = n_coarse - 1
                    elif E_center < coarse_group_structure[0]:
                        g_coarse_check = 0
                    
                    if g_coarse_check == g_coarse:
                        dE = E_high - E_low
                        numerator += fine_cross_sections[g_fine] * fine_flux[g_fine] * dE
                coarse_xs[g_coarse] = numerator / coarse_flux[g_coarse]
    
    return coarse_xs
    
    def _calculate_dancoff_factor(
        self,
        fuel_radius: float,
        pin_pitch: float,
    ) -> float:
        """
        Calculate Dancoff factor for fuel pin array.
        
        Dancoff factor accounts for neutron interaction between fuel pins.
        
        Args:
            fuel_radius: Fuel pin radius [cm]
            pin_pitch: Pin pitch [cm]
        
        Returns:
            Dancoff factor (0-1)
        """
        # Simplified model: Dancoff factor based on pitch-to-diameter ratio
        pitch_to_diameter = pin_pitch / (2 * fuel_radius)
        
        # Typical values: 0.0 (isolated pins) to 0.3 (tight lattice)
        # Simplified correlation
        if pitch_to_diameter > 2.0:
            dancoff = 0.0  # Isolated pins
        elif pitch_to_diameter < 1.2:
            dancoff = 0.3  # Very tight lattice
        else:
            # Linear interpolation
            dancoff = 0.3 * (2.0 - pitch_to_diameter) / (2.0 - 1.2)
        
        return dancoff
    
    def _calculate_escape_probability(
        self,
        fuel_radius: float,
        pin_pitch: float,
        dancoff_factor: float,
    ) -> float:
        """
        Calculate escape probability from fuel pin.
        
        Escape probability accounts for neutrons escaping the fuel pin
        into the moderator.
        
        Args:
            fuel_radius: Fuel pin radius [cm]
            pin_pitch: Pin pitch [cm]
            dancoff_factor: Dancoff factor
        
        Returns:
            Escape probability (0-1)
        """
        # Simplified model: escape probability increases with pitch
        # and decreases with Dancoff factor
        pitch_to_diameter = pin_pitch / (2 * fuel_radius)
        
        # Base escape probability (increases with pitch)
        base_escape = min(1.0, 0.5 + 0.3 * (pitch_to_diameter - 1.0))
        
        # Correct for Dancoff factor (higher Dancoff = lower escape)
        escape_prob = base_escape * (1.0 - 0.5 * dancoff_factor)
        
        return np.clip(escape_prob, 0.0, 1.0)


def apply_sph_to_multigroup_table(
    xs_table: Dict[str, np.ndarray],
    sph_factors: Dict[str, SPHFactors],
) -> Dict[str, np.ndarray]:
    """
    Apply SPH correction to a multi-group cross-section table.
    
    Args:
        xs_table: Dictionary mapping "nuclide/reaction" -> cross-sections [n_groups]
        sph_factors: Dictionary mapping "nuclide/reaction" -> SPHFactors
    
    Returns:
        SPH-corrected cross-section table
    """
    corrected_table = {}
    
    for key, xs in xs_table.items():
        if key in sph_factors:
            factors = sph_factors[key]
            sph_method = SPHMethod()
            corrected_table[key] = sph_method.apply_sph_correction(xs, factors)
        else:
            corrected_table[key] = xs  # No correction available
    
    return corrected_table
