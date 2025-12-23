"""
Test utilities and helper classes for SMRForge tests.
"""

from typing import Optional, Tuple

import numpy as np


class SimpleGeometry:
    """Simple geometry for testing."""

    def __init__(
        self,
        core_diameter: float = 200.0,
        core_height: float = 400.0,
        n_radial: int = 11,
        n_axial: int = 21,
    ):
        """
        Initialize simple cylindrical geometry.

        Args:
            core_diameter: Core diameter in cm
            core_height: Core height in cm
            n_radial: Number of radial mesh points
            n_axial: Number of axial mesh points
        """
        self.core_diameter = core_diameter
        self.core_height = core_height
        # Create mesh
        self.radial_mesh = np.linspace(0, core_diameter / 2, n_radial)
        self.axial_mesh = np.linspace(0, core_height, n_axial)

    def get_material_map(self, fuel_radius: Optional[float] = None) -> np.ndarray:
        """
        Get material map (0=fuel, 1=reflector).

        Args:
            fuel_radius: Fuel radius. If None, uses 0.8 * core_diameter/2

        Returns:
            2D array with material IDs
        """
        if fuel_radius is None:
            fuel_radius = 0.8 * self.core_diameter / 2

        r_centers = (self.radial_mesh[:-1] + self.radial_mesh[1:]) / 2
        z_centers = (self.axial_mesh[:-1] + self.axial_mesh[1:]) / 2

        material_map = np.zeros((len(z_centers), len(r_centers)), dtype=int)

        for i, r in enumerate(r_centers):
            if r > fuel_radius:
                material_map[:, i] = 1  # Reflector

        return material_map


def create_test_xs_data(
    n_groups: int = 2,
    n_materials: int = 2,
    k_eff_target: Optional[float] = None,
    rng: Optional[np.random.Generator] = None,
) -> dict:
    """
    Create test cross-section data with optional k-eff target.

    Args:
        n_groups: Number of energy groups
        n_materials: Number of materials
        k_eff_target: Target k-effective (adjusts nu_sigma_f if provided)
        rng: Random number generator for generating data

    Returns:
        Dictionary with cross-section arrays
    """
    if rng is None:
        rng = np.random.default_rng(42)

    # Base values
    sigma_t = 0.3 + 0.6 * rng.random((n_materials, n_groups))
    sigma_a = 0.05 * sigma_t + 0.01 * rng.random((n_materials, n_groups))
    sigma_f = np.zeros_like(sigma_a)
    nu_sigma_f = np.zeros_like(sigma_a)

    # Only first material (fuel) has fission
    sigma_f[0, :] = 0.8 * sigma_a[0, :] + 0.01 * rng.random(n_groups)
    nu_sigma_f[0, :] = 2.5 * sigma_f[0, :]  # nu ~ 2.5

    # Adjust for target k-eff
    if k_eff_target is not None and k_eff_target > 0:
        # Rough scaling: increase nu_sigma_f for higher k_eff
        current_scale = np.mean(nu_sigma_f[0, :])
        target_scale = current_scale * k_eff_target
        nu_sigma_f[0, :] *= target_scale / current_scale
        sigma_f[0, :] *= target_scale / current_scale

    # Scattering matrix
    sigma_s = np.zeros((n_materials, n_groups, n_groups))
    for m in range(n_materials):
        for g in range(n_groups):
            sigma_s[m, g, g] = sigma_t[m, g] - sigma_a[m, g]  # Self-scattering
            if g < n_groups - 1:
                # Some downscatter
                sigma_s[m, g, g + 1] = 0.01 * rng.random()

    # Fission spectrum (all fast)
    chi = np.zeros((n_materials, n_groups))
    chi[:, 0] = 1.0

    # Diffusion coefficients
    D = 1.0 + 0.5 * rng.random((n_materials, n_groups))

    return {
        "sigma_t": sigma_t,
        "sigma_a": sigma_a,
        "sigma_f": sigma_f,
        "nu_sigma_f": nu_sigma_f,
        "sigma_s": sigma_s,
        "chi": chi,
        "D": D,
    }


def assert_solution_reasonable(
    k_eff: float,
    flux: np.ndarray,
    k_eff_range: Tuple[float, float] = (0.5, 2.0),
    check_flux_nonnegative: bool = True,
    check_flux_finite: bool = True,
    check_flux_shape: Optional[Tuple[int, ...]] = None,
) -> None:
    """
    Assert that solution values are reasonable.

    Args:
        k_eff: Effective multiplication factor
        flux: Flux array
        k_eff_range: Valid range for k_eff
        check_flux_nonnegative: Whether to check flux >= 0
        check_flux_finite: Whether to check flux is finite
        check_flux_shape: Expected flux shape (if provided)
    """
    assert np.isfinite(k_eff), f"k_eff must be finite, got {k_eff}"
    assert (
        k_eff_range[0] <= k_eff <= k_eff_range[1]
    ), f"k_eff = {k_eff} outside reasonable range {k_eff_range}"

    assert flux is not None, "Flux must not be None"
    assert isinstance(flux, np.ndarray), "Flux must be numpy array"

    if check_flux_shape is not None:
        assert (
            flux.shape == check_flux_shape
        ), f"Flux shape {flux.shape} != expected {check_flux_shape}"

    if check_flux_nonnegative:
        assert np.all(flux >= 0), "Flux must be non-negative"

    if check_flux_finite:
        assert np.all(np.isfinite(flux)), "Flux must be finite"


def compute_power_error(
    power: np.ndarray, volumes: np.ndarray, target_power: float, rtol: float = 1e-3
) -> Tuple[float, bool]:
    """
    Compute power distribution error and check if within tolerance.

    Args:
        power: Power distribution array
        volumes: Cell volumes array
        target_power: Target total power
        rtol: Relative tolerance

    Returns:
        (error, is_valid) tuple
    """
    total_power = np.sum(power * volumes)
    error = abs(total_power - target_power) / target_power
    is_valid = error < rtol
    return error, is_valid
