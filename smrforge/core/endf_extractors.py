"""
ENDF Data Extraction Utilities

Helper functions for extracting specialized data from ENDF files:
- nu (neutrons per fission)
- chi (fission spectrum)
- Scattering matrices (with TSL support)
"""

from typing import Dict, Optional, Tuple

import numpy as np

from ..utils.logging import get_logger


def _collapse_to_multigroup_flux_weighted(
    energy: np.ndarray,
    sigma: np.ndarray,
    group_structure: np.ndarray,
    flux_energy: Optional[np.ndarray] = None,
    flux_phi: Optional[np.ndarray] = None,
    n_sub_per_group: int = 16,
) -> np.ndarray:
    """
    Collapse continuous-energy cross-section to multi-group with flux-weighting.

    σ_g = ∫ σ(E) φ(E) dE / ∫ φ(E) dE   over group g

    When flux is not provided, uses 1/E spectrum (typical for LWR slowing-down).
    See docs/FLUX_WEIGHTING_LIMITATION.md.

    Args:
        energy: Continuous energy grid [eV]
        sigma: Cross-section on energy grid [barns]
        group_structure: Group boundaries [eV], low to high
        flux_energy: Optional flux energy grid [eV]
        flux_phi: Optional flux φ(E) on flux_energy grid
        n_sub_per_group: Sub-divisions for integration per group

    Returns:
        Multi-group cross-section [n_groups]
    """
    n_groups = len(group_structure) - 1
    sigma_mg = np.zeros(n_groups)
    energy = np.asarray(energy)
    sigma = np.asarray(sigma)
    # Ensure energy is sorted low to high
    if energy[-1] < energy[0]:
        energy = energy[::-1]
        sigma = sigma[::-1]

    for g in range(n_groups):
        E_lo = group_structure[g]
        E_hi = group_structure[g + 1]
        if E_lo >= E_hi:
            E_lo, E_hi = E_hi, E_lo

        # Sub-grid for integration
        E_sub = np.linspace(E_lo, E_hi, n_sub_per_group)
        sigma_sub = np.interp(E_sub, energy, sigma)

        if flux_energy is not None and flux_phi is not None:
            phi_sub = np.interp(E_sub, flux_energy, flux_phi)
        else:
            # Default: 1/E spectrum (LWR slowing-down)
            phi_sub = 1.0 / np.maximum(E_sub, 1e-10)

        num = np.trapz(sigma_sub * phi_sub, E_sub)
        denom = np.trapz(phi_sub, E_sub)
        if denom > 1e-30:
            sigma_mg[g] = num / denom
        else:
            sigma_mg[g] = np.interp((E_lo + E_hi) / 2, energy, sigma)

    return sigma_mg


from .constants import FISSION_SPECTRUM_PARAMS, watt_spectrum

logger = get_logger("smrforge.core.endf_extractors")
from .reactor_core import NuclearDataCache, Nuclide, get_thermal_scattering_data
from .thermal_scattering_parser import ThermalScatteringParser, get_tsl_material_name


def extract_nu_from_endf(
    cache: NuclearDataCache,
    nuclide: Nuclide,
    group_structure: np.ndarray,
    temperature: float = 293.6,
    use_energy_dependence: bool = True,
) -> np.ndarray:
    """
    Extract nu (neutrons per fission) from ENDF file with full energy dependence.

    Provides energy-dependent nu-bar values. Nu-bar increases with neutron energy
    because fast neutrons produce more neutrons per fission than thermal neutrons.

    Args:
        cache: NuclearDataCache instance (for potential future ENDF parsing)
        nuclide: Nuclide instance
        group_structure: Energy group boundaries [eV]
        temperature: Temperature [K] (currently unused, for future use)
        use_energy_dependence: If True, use energy-dependent nu (default: True)

    Returns:
        nu values for each energy group [n_groups]

    Note:
        Energy dependence is now fully implemented. Nu-bar increases from
        thermal (~2.4) to fast (~2.6-2.7) for typical fissile nuclides.
    """
    n_groups = len(group_structure) - 1
    group_centers = (group_structure[:-1] + group_structure[1:]) / 2  # eV

    # Nuclide-specific base values with energy dependence
    nu_params = {
        "U235": {
            "base": 2.43,  # Thermal (0.025 eV)
            "fast": 2.58,  # Fast (>1 MeV)
            "thermal_energy": 0.025,  # eV
            "fast_energy": 1e6,  # eV
            "interpolation": "log",  # Logarithmic interpolation
        },
        "U238": {
            "base": 2.40,
            "fast": 2.70,
            "thermal_energy": 0.025,
            "fast_energy": 1e6,
            "interpolation": "log",
        },
        "Pu239": {
            "base": 2.87,
            "fast": 2.95,
            "thermal_energy": 0.025,
            "fast_energy": 1e6,
            "interpolation": "log",
        },
        "Pu241": {
            "base": 2.94,
            "fast": 3.00,
            "thermal_energy": 0.025,
            "fast_energy": 1e6,
            "interpolation": "log",
        },
    }

    # Get parameters for this nuclide
    if nuclide.name in nu_params:
        params = nu_params[nuclide.name]
    else:
        # Default values
        params = {
            "base": 2.5,
            "fast": 2.6,
            "thermal_energy": 0.025,
            "fast_energy": 1e6,
            "interpolation": "log",
        }

    if not use_energy_dependence:
        # Return constant value
        return np.ones(n_groups) * params["base"]

    # Energy-dependent nu: increases with neutron energy
    # Fast neutrons produce more neutrons per fission
    nu = np.zeros(n_groups)

    for g in range(n_groups):
        E = group_centers[g]  # eV

        if E < params["thermal_energy"]:
            # Below thermal: use base value
            nu[g] = params["base"]
        elif E >= params["fast_energy"]:
            # Fast: use fast value
            nu[g] = params["fast"]
        else:
            # Interpolate between thermal and fast
            if params["interpolation"] == "log":
                # Logarithmic interpolation (recommended for energy)
                log_E = np.log10(max(E, params["thermal_energy"]))
                log_E_fast = np.log10(params["fast_energy"])
                log_E_thermal = np.log10(params["thermal_energy"])

                if log_E_fast > log_E_thermal:
                    frac = (log_E - log_E_thermal) / (log_E_fast - log_E_thermal)
                    nu[g] = params["base"] + frac * (params["fast"] - params["base"])
                else:
                    nu[g] = params["base"]
            else:
                # Linear interpolation
                frac = (E - params["thermal_energy"]) / (
                    params["fast_energy"] - params["thermal_energy"]
                )
                nu[g] = params["base"] + frac * (params["fast"] - params["base"])

    return nu


def extract_chi_prompt_delayed(
    cache: NuclearDataCache,
    nuclide: Nuclide,
    group_structure: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract prompt and delayed chi (fission spectra) separately.

    Separates the total fission spectrum into prompt and delayed components.
    Prompt neutrons are emitted immediately, delayed neutrons come from
    fission product decay.

    Args:
        cache: NuclearDataCache instance
        nuclide: Nuclide instance
        group_structure: Energy group boundaries [eV]

    Returns:
        Tuple of (chi_prompt, chi_delayed):
            - chi_prompt: Prompt fission spectrum [n_groups], normalized
            - chi_delayed: Delayed fission spectrum [n_groups], normalized

    Note:
        Delayed neutrons typically have lower average energy than prompt neutrons.
        Default: 99% prompt, 1% delayed (typical for thermal fission).
    """
    n_groups = len(group_structure) - 1
    group_centers = (group_structure[:-1] + group_structure[1:]) / 2  # eV

    # Get total chi
    chi_total = extract_chi_from_endf(cache, nuclide, group_structure)

    # Delayed neutron fraction (beta) - typically 0.0065 for U235
    beta_values = {
        "U235": 0.0065,
        "U238": 0.0148,
        "Pu239": 0.0021,
        "Pu241": 0.0015,
    }
    beta = beta_values.get(nuclide.name, 0.0065)

    # Delayed neutrons have lower average energy
    # Use softer spectrum for delayed (more thermal)
    chi_delayed = np.zeros(n_groups)
    chi_prompt = np.zeros(n_groups)

    # Delayed spectrum: more thermal (lower energy)
    # Use Maxwellian-like distribution centered at ~0.5 MeV
    for g in range(n_groups):
        E = group_centers[g] / 1e6  # Convert to MeV
        # Maxwellian-like for delayed (softer)
        chi_delayed[g] = E * np.exp(-E / 0.5) if E > 0 else 0.0

    # Normalize delayed
    chi_delayed_sum = np.sum(chi_delayed)
    if chi_delayed_sum > 0:
        chi_delayed = chi_delayed / chi_delayed_sum

    # Prompt spectrum: use total chi, adjusted for delayed fraction
    chi_prompt = chi_total * (1.0 - beta)

    # Add delayed contribution
    chi_delayed_weighted = chi_delayed * beta

    # Renormalize to ensure sum = 1
    chi_total_sep = chi_prompt + chi_delayed_weighted
    chi_total_sep_sum = np.sum(chi_total_sep)
    if chi_total_sep_sum > 0:
        chi_prompt = chi_prompt / chi_total_sep_sum
        chi_delayed_weighted = chi_delayed_weighted / chi_total_sep_sum

    # Return normalized prompt and delayed
    chi_prompt_norm = (
        chi_prompt / np.sum(chi_prompt) if np.sum(chi_prompt) > 0 else chi_prompt
    )
    chi_delayed_norm = (
        chi_delayed_weighted / np.sum(chi_delayed_weighted)
        if np.sum(chi_delayed_weighted) > 0
        else chi_delayed_weighted
    )

    return chi_prompt_norm, chi_delayed_norm


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
    except Exception as e:
        logger.warning(
            "Watt spectrum fallback: used hardcoded fission spectrum (Watt computation failed: %s)",
            e,
        )
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
    flux_energy: Optional[np.ndarray] = None,
    flux_phi: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Compute improved scattering matrix from elastic cross-section with TSL support.

    For thermal groups, uses thermal scattering law (TSL) data when available.
    For fast groups, uses energy-dependent downscattering model:
    - Fast groups: more downscattering (70% same, 25% next, 5% skip)
    - Thermal groups: TSL-corrected or mostly same group (90% same, 10% next)

    Multi-group elastic collapse uses flux-weighting: σ_g = ∫σ(E)φ(E)dE/∫φ(E)dE.
    When flux_energy/flux_phi not provided, uses 1/E default spectrum.

    Args:
        cache: NuclearDataCache instance
        nuclide: Nuclide instance
        group_structure: Energy group boundaries [eV]
        temperature: Temperature [K]
        elastic_mg: Pre-computed multi-group elastic cross-section [n_groups]
            If None, will compute from continuous-energy data with flux-weighting
        material_name: Optional material name for TSL lookup (e.g., "H2O", "graphite")
        use_tsl: If True, attempt to use TSL data for thermal groups
        flux_energy: Optional flux spectrum energy grid [eV] for collapse
        flux_phi: Optional flux φ(E) on flux_energy grid

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
            # Flux-weighted collapse: σ_g = ∫σ(E)φ(E)dE/∫φ(E)dE.
            # Uses 1/E default spectrum when flux not provided. See docs/FLUX_WEIGHTING_LIMITATION.md.
            elastic_mg = _collapse_to_multigroup_flux_weighted(
                energy,
                sigma_elastic,
                group_structure,
                flux_energy=flux_energy,
                flux_phi=flux_phi,
            )
        except Exception as e:
            # Fallback: use simple model (log for transparency and regulatory traceability)
            logger.warning(
                "Elastic cross-section fallback: used default 5 barns for %r (temperature=%s). "
                "Original error: %s. Consider documenting in model assumptions.",
                nuclide,
                temperature,
                e,
            )
            elastic_mg = np.ones(n_groups) * 5.0  # Default 5 barns

    # Try to get TSL data if material name provided and TSL enabled
    tsl_data = None
    if use_tsl and material_name:
        try:
            tsl_material_name = get_tsl_material_name(material_name)
            if tsl_material_name:
                tsl_data = get_thermal_scattering_data(tsl_material_name, cache=cache)
        except Exception as e:
            logger.warning(
                "TSL fallback: could not load thermal scattering data for %s. "
                "Using standard scattering. Error: %s",
                material_name,
                e,
            )

    # Compute scattering matrix
    parser = ThermalScatteringParser()

    for g in range(n_groups):
        group_center = (group_structure[g] + group_structure[g + 1]) / 2
        is_thermal = group_center < 1.0  # Below 1 eV (thermal range)

        if is_thermal and tsl_data is not None:
            # Use TSL for thermal groups with full upscattering support
            # Compute scattering from group g to all groups (including upscattering)
            E_in = group_center

            for g_out in range(n_groups):
                E_out_center = (group_structure[g_out] + group_structure[g_out + 1]) / 2
                E_out_low = group_structure[g_out + 1]
                E_out_high = group_structure[g_out]

                # Check if upscattering is possible (E_out > E_in)
                is_upscatter = E_out_center > E_in

                # For thermal groups, allow both downscattering and upscattering
                # Upscattering occurs when neutron gains energy from thermal motion
                if is_upscatter:
                    # Upscattering: neutron gains energy
                    # Use TSL to compute probability of upscattering
                    # β = (E_in - E_out) / (k_B*T) will be negative for upscattering
                    xs_tsl = parser.compute_thermal_scattering_xs(
                        tsl_data, E_in, E_out_center, temperature
                    )

                    # Upscattering probability is typically smaller than downscattering
                    # Weight by detailed balance: σ_s(E→E') * φ(E) = σ_s(E'→E) * φ(E') * exp((E'-E)/(kT))
                    # For upscattering, apply detailed balance correction
                    k_B = 8.617333262e-5  # eV/K
                    kT = k_B * temperature
                    if E_in > 0:
                        detailed_balance_factor = np.sqrt(E_out_center / E_in) * np.exp(
                            (E_out_center - E_in) / kT
                        )
                    else:
                        detailed_balance_factor = 0.0

                    # Weight by group width and detailed balance
                    group_width = E_out_high - E_out_low
                    sigma_s[g, g_out] = xs_tsl * group_width * detailed_balance_factor
                else:
                    # Downscattering: neutron loses energy (normal case)
                    xs_tsl = parser.compute_thermal_scattering_xs(
                        tsl_data, E_in, E_out_center, temperature
                    )

                    # Weight by group width
                    group_width = E_out_high - E_out_low
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
                # Thermal/epithermal groups: mostly same group with some upscattering
                sigma_s[g, g] = 0.85 * elastic_mg[g]  # Same group
                if g < n_groups - 1:
                    sigma_s[g, g + 1] = 0.1 * elastic_mg[g]  # Downscattering
                if g > 0:
                    # Upscattering: neutron gains energy from thermal motion
                    # Probability decreases with energy gain
                    k_B = 8.617333262e-5  # eV/K
                    kT = k_B * temperature
                    E_g = group_center
                    E_g_minus_1 = (group_structure[g - 1] + group_structure[g]) / 2
                    energy_gain = E_g_minus_1 - E_g

                    # Upscattering probability follows Maxwell-Boltzmann distribution
                    # P(upscatter) ∝ exp(-ΔE / (kT))
                    if energy_gain > 0 and kT > 0:
                        upscatter_prob = 0.05 * np.exp(-energy_gain / kT)
                        sigma_s[g, g - 1] = upscatter_prob * elastic_mg[g]
                    else:
                        sigma_s[g, g - 1] = 0.0

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
        cache,
        nuclide,
        group_structure,
        temperature,
        elastic_mg=elastic_mg,
        material_name=material_name,
        use_tsl=use_tsl,
    )

    # Initialize Legendre moment matrices
    sigma_s_legendre = np.zeros((n_legendre, n_groups, n_groups))
    sigma_s_legendre[0] = sigma_s_isotropic  # P0 = isotropic

    # Try to get MF=6 data for accurate Legendre moments
    mf6_data = None
    try:
        from .energy_angle_parser import get_energy_angle_data

        mf6_data = get_energy_angle_data(nuclide, mt=2, cache=cache)  # MT=2 is elastic
    except Exception as e:
        logger.warning(
            "MF6 energy-angle parser fallback: using simplified P1/P2 models for %r (%s)",
            nuclide,
            e,
        )
        # Fallback to simplified models

    # Get elastic cross-section if not provided (uses flux-weighted collapse via compute_improved_scattering_matrix)
    if elastic_mg is None:
        try:
            energy, sigma_elastic = cache.get_cross_section(
                nuclide, "elastic", temperature
            )
            elastic_mg = _collapse_to_multigroup_flux_weighted(
                energy, sigma_elastic, group_structure
            )
        except Exception as e:
            logger.warning(
                "Elastic cross-section fallback (anisotropic P1): used default 5 barns for %r (temperature=%s). "
                "Original error: %s.",
                nuclide,
                temperature,
                e,
            )
            elastic_mg = np.ones(n_groups) * 5.0  # Default 5 barns

    # Compute P1 moment (linear anisotropy)
    # P1 represents forward/backward scattering preference
    if max_legendre_order >= 1:
        for g in range(n_groups):
            group_center = (group_structure[g] + group_structure[g + 1]) / 2
            is_thermal = group_center < 1.0  # Below 1 eV

            # Try to get P1 from MF=6 data
            p1_moment = None
            if mf6_data is not None:
                moments = mf6_data.get_legendre_moments(group_center, max_order=1)
                if moments is not None and len(moments) > 1:
                    p1_moment = moments[1]  # P1 coefficient

            # Use MF=6 data if available, otherwise use simplified model
            if p1_moment is not None:
                # Use actual MF=6 P1 moment
                p1_factor = abs(p1_moment) / elastic_mg[g] if elastic_mg[g] > 0 else 0.0
                p1_factor = np.clip(p1_factor, 0.0, 0.3)  # Reasonable bounds
            else:
                # Simplified model: P1 ≈ 0.1 * P0 for fast neutrons, smaller for thermal
                if is_thermal:
                    p1_factor = 0.05  # 5% anisotropy
                else:
                    p1_factor = 0.15  # 15% anisotropy

            # P1 moment: forward scattering preference
            # Positive P1 means forward scattering
            for g_out in range(n_groups):
                if g_out == g:
                    # Same group: forward scattering
                    sigma_s_legendre[1, g, g_out] = (
                        p1_factor * sigma_s_isotropic[g, g_out]
                    )
                elif g_out < g:
                    # Downscattering: less forward preference
                    sigma_s_legendre[1, g, g_out] = (
                        -0.5 * p1_factor * sigma_s_isotropic[g, g_out]
                    )
                else:
                    # Upscattering: forward preference (rare)
                    sigma_s_legendre[1, g, g_out] = 0.0

    # Compute P2 moment (quadratic anisotropy)
    # P2 represents angular distribution shape (peaked vs. flat)
    if max_legendre_order >= 2:
        for g in range(n_groups):
            group_center = (group_structure[g] + group_structure[g + 1]) / 2
            is_thermal = group_center < 1.0

            # Try to get P2 from MF=6 data
            p2_moment = None
            if mf6_data is not None:
                moments = mf6_data.get_legendre_moments(group_center, max_order=2)
                if moments is not None and len(moments) > 2:
                    p2_moment = moments[2]  # P2 coefficient

            # Use MF=6 data if available, otherwise use simplified model
            if p2_moment is not None:
                # Use actual MF=6 P2 moment
                p2_factor = abs(p2_moment) / elastic_mg[g] if elastic_mg[g] > 0 else 0.0
                p2_factor = np.clip(p2_factor, 0.0, 0.2)  # Reasonable bounds
            else:
                # Simplified model: P2 ≈ 0.05 * P0
                if is_thermal:
                    p2_factor = 0.02  # Minimal P2 for thermal
                else:
                    p2_factor = 0.08  # Some angular peaking for fast

            for g_out in range(n_groups):
                if g_out == g:
                    # Same group: peaked distribution
                    sigma_s_legendre[2, g, g_out] = (
                        p2_factor * sigma_s_isotropic[g, g_out]
                    )
                else:
                    # Other groups: reduced P2
                    sigma_s_legendre[2, g, g_out] = (
                        0.5 * p2_factor * sigma_s_isotropic[g, g_out]
                    )

    # Normalize: ensure P0 dominates (sum of all moments should be reasonable)
    # In production, this normalization would come from actual MF=6 data

    return sigma_s_isotropic, sigma_s_legendre
