"""
ENDF Data Extraction Utilities

Helper functions for extracting specialized data from ENDF files:
- nu (neutrons per fission)
- chi (fission spectrum)
- Scattering matrices (with TSL support)
"""

import numpy as np
from typing import Optional, Dict, Tuple

from .reactor_core import NuclearDataCache, Nuclide, get_thermal_scattering_data
from .constants import FISSION_SPECTRUM_PARAMS, watt_spectrum
from .thermal_scattering_parser import get_tsl_material_name, ThermalScatteringParser


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
    Extract chi (fission spectrum) from ENDF file or use Watt spectrum approximation.
    
    Currently uses Watt spectrum with nuclide-specific parameters.
    Future: Parse MF=5, MT=18 (fission spectrum) from ENDF files.
    
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
    material_name: Optional[str] = None,
    use_tsl: bool = True,
) -> np.ndarray:
    """
    Compute improved scattering matrix from elastic cross-section with TSL support.
    
    For thermal groups, uses thermal scattering law (TSL) data when available.
    For fast groups, uses energy-dependent downscattering model:
    - Fast groups: more downscattering (70% same, 25% next, 5% skip)
    - Thermal groups: TSL-corrected or mostly same group (90% same, 10% next)
    
    Args:
        cache: NuclearDataCache instance
        nuclide: Nuclide instance
        group_structure: Energy group boundaries [eV]
        temperature: Temperature [K]
        elastic_mg: Pre-computed multi-group elastic cross-section [n_groups]
            If None, will compute from continuous-energy data
        material_name: Optional material name for TSL lookup (e.g., "H2O", "graphite")
        use_tsl: If True, attempt to use TSL data for thermal groups
    
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
    
    # Try to get TSL data if material name provided and TSL enabled
    tsl_data = None
    if use_tsl and material_name:
        try:
            tsl_material_name = get_tsl_material_name(material_name)
            if tsl_material_name:
                tsl_data = get_thermal_scattering_data(tsl_material_name, cache=cache)
        except Exception:
            pass  # Fallback to standard scattering
    
    # Compute scattering matrix
    parser = ThermalScatteringParser()
    
    for g in range(n_groups):
        group_center = (group_structure[g] + group_structure[g + 1]) / 2
        is_thermal = group_center < 1.0  # Below 1 eV (thermal range)
        
        if is_thermal and tsl_data is not None:
            # Use TSL for thermal groups
            # Compute scattering from group g to all groups
            for g_out in range(n_groups):
                if g_out <= g:  # Only downscattering (thermal groups)
                    E_in = group_center
                    E_out = (group_structure[g_out] + group_structure[g_out + 1]) / 2
                    
                    # Compute TSL cross-section
                    xs_tsl = parser.compute_thermal_scattering_xs(
                        tsl_data, E_in, E_out, temperature
                    )
                    
                    # Weight by group width
                    group_width = group_structure[g] - group_structure[g + 1]
                    sigma_s[g, g_out] = xs_tsl * group_width
        else:
            # Use standard model for fast groups or when TSL not available
            is_fast = group_center > 1e5  # Above 100 keV
            
            if is_fast:
                # Fast groups: more downscattering
                sigma_s[g, g] = 0.7 * elastic_mg[g]
                if g < n_groups - 1:
                    sigma_s[g, g + 1] = 0.25 * elastic_mg[g]
                if g < n_groups - 2:
                    sigma_s[g, g + 2] = 0.05 * elastic_mg[g]
            else:
                # Thermal/epithermal groups: mostly same group
                sigma_s[g, g] = 0.9 * elastic_mg[g]
                if g < n_groups - 1:
                    sigma_s[g, g + 1] = 0.1 * elastic_mg[g]
    
    # Normalize rows to ensure conservation
    for g in range(n_groups):
        row_sum = np.sum(sigma_s[g, :])
        if row_sum > 0:
            sigma_s[g, :] = sigma_s[g, :] * elastic_mg[g] / row_sum
    
    return sigma_s


def compute_anisotropic_scattering_matrix(
    cache: NuclearDataCache,
    nuclide: Nuclide,
    group_structure: np.ndarray,
    temperature: float,
    max_legendre_order: int = 2,
    elastic_mg: Optional[np.ndarray] = None,
    material_name: Optional[str] = None,
    use_tsl: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute anisotropic scattering matrix with Legendre moments (P0, P1, P2, ...).
    
    For thermal SMRs, anisotropic scattering is important for accurate flux
    distributions. This function computes scattering matrices for each Legendre
    moment, allowing the neutronics solver to account for angular dependence.
    
    The scattering kernel is expanded in Legendre polynomials:
    σ_s(E' → E, μ) = Σ_l (2l+1)/2 * σ_s^l(E' → E) * P_l(μ)
    
    Where:
    - P_l(μ) are Legendre polynomials
    - σ_s^l are the Legendre moments (P0, P1, P2, ...)
    - μ = cos(θ) is the scattering angle cosine
    
    Args:
        cache: NuclearDataCache instance
        nuclide: Nuclide instance
        group_structure: Energy group boundaries [eV]
        temperature: Temperature [K]
        max_legendre_order: Maximum Legendre order (0=P0, 1=P1, 2=P2, etc.)
            Default is 2 (P0, P1, P2)
        elastic_mg: Pre-computed multi-group elastic cross-section [n_groups]
            If None, will compute from continuous-energy data
        material_name: Optional material name for TSL lookup (e.g., "H2O", "graphite")
        use_tsl: If True, attempt to use TSL data for thermal groups
    
    Returns:
        Tuple of (sigma_s_isotropic, sigma_s_legendre):
        - sigma_s_isotropic: Isotropic scattering matrix [n_groups, n_groups]
            This is the P0 moment (same as compute_improved_scattering_matrix)
        - sigma_s_legendre: Anisotropic scattering matrices [n_legendre, n_groups, n_groups]
            Where n_legendre = max_legendre_order + 1
            sigma_s_legendre[0] = P0 (isotropic)
            sigma_s_legendre[1] = P1 (linear anisotropy)
            sigma_s_legendre[2] = P2 (quadratic anisotropy)
            etc.
    
    Note:
        Currently uses simplified models for P1 and P2 moments. In production,
        these should be computed from MF=6 (energy-angle distributions) data
        or from TSL data when available.
    
    Example:
        >>> from smrforge.core.reactor_core import NuclearDataCache, Nuclide
        >>> from smrforge.core.endf_extractors import compute_anisotropic_scattering_matrix
        >>> import numpy as np
        >>> 
        >>> cache = NuclearDataCache()
        >>> u238 = Nuclide(Z=92, A=238)
        >>> group_structure = np.array([1e-5, 1.0, 1e6, 2e7])  # 3 groups
        >>> 
        >>> sigma_s_iso, sigma_s_leg = compute_anisotropic_scattering_matrix(
        ...     cache, u238, group_structure, temperature=900.0, max_legendre_order=2
        ... )
        >>> 
        >>> # sigma_s_iso is [3, 3] - isotropic scattering
        >>> # sigma_s_leg is [3, 3, 3] - P0, P1, P2 moments
        >>> print(f"P0 matrix shape: {sigma_s_leg[0].shape}")
        >>> print(f"P1 matrix shape: {sigma_s_leg[1].shape}")
        >>> print(f"P2 matrix shape: {sigma_s_leg[2].shape}")
    """
    n_groups = len(group_structure) - 1
    n_legendre = max_legendre_order + 1
    
    # Get isotropic scattering matrix (P0)
    sigma_s_isotropic = compute_improved_scattering_matrix(
        cache, nuclide, group_structure, temperature,
        elastic_mg=elastic_mg, material_name=material_name, use_tsl=use_tsl
    )
    
    # Initialize Legendre moment matrices
    sigma_s_legendre = np.zeros((n_legendre, n_groups, n_groups))
    sigma_s_legendre[0] = sigma_s_isotropic  # P0 = isotropic
    
    # For P1 and higher, use simplified models
    # In production, these should come from MF=6 data or TSL
    
    # Get elastic cross-section if not provided
    if elastic_mg is None:
        try:
            energy, sigma_elastic = cache.get_cross_section(
                nuclide, "elastic", temperature
            )
            group_centers = (group_structure[:-1] + group_structure[1:]) / 2
            elastic_mg = np.array([
                np.interp(center, energy, sigma_elastic) 
                for center in group_centers
            ])
        except Exception:
            elastic_mg = np.ones(n_groups) * 5.0  # Default 5 barns
    
    # Compute P1 moment (linear anisotropy)
    # P1 represents forward/backward scattering preference
    # Simplified model: P1 ≈ 0.1 * P0 for fast neutrons, smaller for thermal
    if max_legendre_order >= 1:
        for g in range(n_groups):
            group_center = (group_structure[g] + group_structure[g + 1]) / 2
            is_thermal = group_center < 1.0  # Below 1 eV
            
            if is_thermal:
                # Thermal: less anisotropy (mostly isotropic)
                p1_factor = 0.05  # 5% anisotropy
            else:
                # Fast/epithermal: more forward scattering
                p1_factor = 0.15  # 15% anisotropy
            
            # P1 moment: forward scattering preference
            # Positive P1 means forward scattering
            for g_out in range(n_groups):
                if g_out == g:
                    # Same group: forward scattering
                    sigma_s_legendre[1, g, g_out] = p1_factor * sigma_s_isotropic[g, g_out]
                elif g_out < g:
                    # Downscattering: less forward preference
                    sigma_s_legendre[1, g, g_out] = -0.5 * p1_factor * sigma_s_isotropic[g, g_out]
                else:
                    # Upscattering: forward preference (rare)
                    sigma_s_legendre[1, g, g_out] = 0.0
    
    # Compute P2 moment (quadratic anisotropy)
    # P2 represents angular distribution shape (peaked vs. flat)
    # Simplified model: P2 ≈ 0.05 * P0
    if max_legendre_order >= 2:
        for g in range(n_groups):
            group_center = (group_structure[g] + group_structure[g + 1]) / 2
            is_thermal = group_center < 1.0
            
            if is_thermal:
                # Thermal: minimal P2 (mostly isotropic)
                p2_factor = 0.02
            else:
                # Fast: some angular peaking
                p2_factor = 0.08
            
            for g_out in range(n_groups):
                if g_out == g:
                    # Same group: peaked distribution
                    sigma_s_legendre[2, g, g_out] = p2_factor * sigma_s_isotropic[g, g_out]
                else:
                    # Other groups: reduced P2
                    sigma_s_legendre[2, g, g_out] = 0.5 * p2_factor * sigma_s_isotropic[g, g_out]
    
    # Normalize: ensure P0 dominates (sum of all moments should be reasonable)
    # In production, this normalization would come from actual MF=6 data
    
    return sigma_s_isotropic, sigma_s_legendre