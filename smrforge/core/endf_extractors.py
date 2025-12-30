"""
ENDF Data Extraction Utilities

Helper functions for extracting specialized data from ENDF files:
- nu (neutrons per fission)
- chi (fission spectrum)
- Scattering matrices
"""

import numpy as np
from typing import Optional, Dict
from pathlib import Path

from .reactor_core import NuclearDataCache, Nuclide
from .constants import FISSION_SPECTRUM_PARAMS, watt_spectrum


def extract_nu_from_endf(
    cache: NuclearDataCache,
    nuclide: Nuclide,
    group_structure: np.ndarray,
    temperature: float = 293.6,
) -> np.ndarray:
    """
    Extract nu (neutrons per fission) from ENDF file or use energy-dependent approximation.
    
    Currently uses nuclide-specific defaults with energy dependence.
    Future: Parse MF=1, MT=452 or MF=3, MT=456 from ENDF files.
    
    Args:
        cache: NuclearDataCache instance (for potential future ENDF parsing)
        nuclide: Nuclide instance
        group_structure: Energy group boundaries [eV]
        temperature: Temperature [K] (currently unused, for future use)
    
    Returns:
        nu values for each energy group [n_groups]
    """
    n_groups = len(group_structure) - 1
    group_centers = (group_structure[:-1] + group_structure[1:]) / 2  # eV
    
    # Nuclide-specific base values
    nu_params = {
        "U235": {"base": 2.43, "fast": 2.58, "thermal_energy": 0.025},  # eV
        "U238": {"base": 2.40, "fast": 2.70, "thermal_energy": 0.025},
        "Pu239": {"base": 2.87, "fast": 2.95, "thermal_energy": 0.025},
        "Pu241": {"base": 2.94, "fast": 3.00, "thermal_energy": 0.025},
    }
    
    # Get parameters for this nuclide
    if nuclide.name in nu_params:
        params = nu_params[nuclide.name]
    else:
        # Default values
        params = {"base": 2.5, "fast": 2.6, "thermal_energy": 0.025}
    
    # Energy-dependent nu: increases with neutron energy
    # Fast neutrons produce more neutrons per fission
    nu = np.zeros(n_groups)
    
    for g in range(n_groups):
        E = group_centers[g]  # eV
        
        if E < 1e6:  # Thermal/epithermal
            # Linear interpolation between thermal and fast
            # At thermal (0.025 eV): use base value
            # At 1 MeV: use fast value
            if E < params["thermal_energy"]:
                nu[g] = params["base"]
            else:
                # Interpolate
                log_E = np.log10(max(E, params["thermal_energy"]))
                log_E_fast = np.log10(1e6)
                log_E_thermal = np.log10(params["thermal_energy"])
                
                if log_E_fast > log_E_thermal:
                    frac = (log_E - log_E_thermal) / (log_E_fast - log_E_thermal)
                    nu[g] = params["base"] + frac * (params["fast"] - params["base"])
                else:
                    nu[g] = params["base"]
        else:  # Fast
            nu[g] = params["fast"]
    
    return nu


def extract_chi_from_endf(
    cache: NuclearDataCache,
    nuclide: Nuclide,
    group_structure: np.ndarray,
) -> np.ndarray:
    """
    Extract chi (fission spectrum) from ENDF file or use proper Watt spectrum.
    
    Currently uses Watt spectrum with nuclide-specific parameters.
    Future: Parse MF=5 from ENDF files.
    
    Args:
        cache: NuclearDataCache instance (for potential future ENDF parsing)
        nuclide: Nuclide instance
        group_structure: Energy group boundaries [eV]
    
    Returns:
        chi values for each energy group [n_groups], normalized to sum=1
    """
    n_groups = len(group_structure) - 1
    
    # Get Watt parameters for this nuclide
    key = f"{nuclide.name}_thermal"
    if key in FISSION_SPECTRUM_PARAMS:
        params = FISSION_SPECTRUM_PARAMS[key]
    elif nuclide.name == "U238":
        # U238 fast fission spectrum
        params = {"a": 0.88, "b": 3.0}
    elif nuclide.name == "Pu239":
        params = {"a": 0.966, "b": 2.383}
    else:
        # Default U235 thermal
        params = {"a": 0.988, "b": 2.249}
    
    # Convert group boundaries to MeV
    group_centers_mev = (group_structure[:-1] + group_structure[1:]) / 2 / 1e6
    
    # Compute Watt spectrum
    try:
        chi = watt_spectrum(group_centers_mev, params["a"], params["b"])
    except Exception:
        # Fallback to hardcoded spectrum if Watt computation fails
        chi = np.zeros(n_groups)
        chi[0] = 0.6
        chi[1] = 0.3
        chi[2] = 0.08
        chi[3] = 0.015
        chi[4] = 0.004
        chi[5] = 0.001
        if n_groups > 6:
            chi[6:] = 0.0
    
    # Normalize to ensure sum = 1
    chi_sum = np.sum(chi)
    if chi_sum > 0:
        chi = chi / chi_sum
    else:
        # Fallback: uniform distribution
        chi = np.ones(n_groups) / n_groups
    
    return chi


def compute_improved_scattering_matrix(
    cache: NuclearDataCache,
    nuclide: Nuclide,
    group_structure: np.ndarray,
    temperature: float,
    elastic_mg: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Compute improved scattering matrix from elastic cross-section.
    
    Uses energy-dependent downscattering model:
    - Fast groups: more downscattering (70% same, 25% next, 5% skip)
    - Thermal groups: mostly same group (90% same, 10% next)
    
    Args:
        cache: NuclearDataCache instance
        nuclide: Nuclide instance
        group_structure: Energy group boundaries [eV]
        temperature: Temperature [K]
        elastic_mg: Pre-computed multi-group elastic cross-section [n_groups]
            If None, will compute from continuous-energy data
    
    Returns:
        Scattering matrix [n_groups, n_groups]
    """
    n_groups = len(group_structure) - 1
    sigma_s = np.zeros((n_groups, n_groups))
    
    # Get elastic cross-section if not provided
    if elastic_mg is None:
        try:
            energy, sigma_elastic = cache.get_cross_section(
                nuclide, "elastic", temperature
            )
            # Collapse to multi-group (simple average for now)
            # TODO: Use proper flux-weighting
            group_centers = (group_structure[:-1] + group_structure[1:]) / 2
            elastic_mg = np.array([
                np.interp(center, energy, sigma_elastic) 
                for center in group_centers
            ])
        except Exception:
            # Fallback: use simple model
            elastic_mg = np.ones(n_groups) * 5.0  # Default 5 barns
    
    # Compute scattering matrix with energy-dependent model
    for g in range(n_groups):
        # Determine if this is a fast or thermal group
        group_center = (group_structure[g] + group_structure[g + 1]) / 2
        is_fast = group_center > 1e5  # Above 100 keV
        
        if is_fast:
            # Fast groups: more downscattering
            sigma_s[g, g] = 0.7 * elastic_mg[g]
            if g < n_groups - 1:
                sigma_s[g, g + 1] = 0.25 * elastic_mg[g]
            if g < n_groups - 2:
                sigma_s[g, g + 2] = 0.05 * elastic_mg[g]
        else:
            # Thermal groups: mostly same group
            sigma_s[g, g] = 0.9 * elastic_mg[g]
            if g < n_groups - 1:
                sigma_s[g, g + 1] = 0.1 * elastic_mg[g]
    
    return sigma_s

