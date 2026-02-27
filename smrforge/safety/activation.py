"""
R2S-style (Rigorous Two-Step) activation workflow for shutdown dose.

Workflow:
1. Neutron transport → flux/reaction rates (from diffusion or MC)
2. Activation calculation → photon source from (n,gamma) and decay
3. Photon transport → dose rate at detector locations

Integrates with decay_heat and gamma_transport modules.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.safety.activation")


@dataclass
class PhotonSourceMesh:
    """Mesh-based photon source from activation (R2S step 2 output)."""

    positions: np.ndarray  # [n_cells, 3] or [nz, nr] for 2D
    energies: np.ndarray  # [n_groups] MeV
    source_strength: np.ndarray  # [n_cells, n_groups] or [nz, nr, n_groups] photons/s
    decay_time: float = 0.0  # seconds after shutdown


@dataclass
class R2SResult:
    """Result of R2S shutdown dose calculation."""

    dose_rate: np.ndarray  # [n_detectors] Sv/h or Gy/h
    detector_positions: np.ndarray  # [n_detectors, 3]
    shutdown_times: np.ndarray  # [n_times] s
    dose_vs_time: Optional[np.ndarray] = None  # [n_detectors, n_times]


def compute_activation_photon_source(
    neutron_flux: np.ndarray,
    sigma_capture: np.ndarray,
    material_composition: np.ndarray,
    decay_times: np.ndarray,
    gamma_yields: Optional[Dict[str, np.ndarray]] = None,
) -> List[PhotonSourceMesh]:
    """
    Compute photon source from neutron activation (simplified R2S step 2).

    Activation rate = flux * sigma_capture * concentration.
    Decay produces photons; simplified: use constant gamma yield per decay.

    Args:
        neutron_flux: [n_cells, n_groups] or [nz, nr, ng]
        sigma_capture: [n_materials, n_groups] capture cross-section
        material_composition: [n_cells] or [nz, nr] material index
        decay_times: Times [s] after shutdown to evaluate
        gamma_yields: Optional nuclide -> energy spectrum

    Returns:
        List of PhotonSourceMesh, one per decay time
    """
    flux = np.asarray(neutron_flux)
    sigma = np.asarray(sigma_capture)
    comp = np.asarray(material_composition, dtype=int)

    if flux.ndim == 3:
        nz, nr, ng = flux.shape
        n_cells = nz * nr
        flux_flat = flux.reshape(n_cells, ng)
        comp_flat = comp.reshape(n_cells)
    else:
        n_cells, ng = flux.shape
        flux_flat = flux
        comp_flat = comp

    # Activation rate ~ flux * sigma (simplified: no decay chain)
    # Units: reactions/s per cm³
    activation = np.zeros(n_cells)
    for c in range(n_cells):
        mat = min(comp_flat[c], sigma.shape[0] - 1) if comp_flat[c] >= 0 else 0
        activation[c] = np.sum(flux_flat[c, :] * sigma[mat, :])

    # Simplified decay: source ~ activation * exp(-lambda*t) with effective lambda
    # Placeholder effective half-life ~ 1 hour
    lam = 0.693 / 3600.0  # 1/h in 1/s
    n_groups = max(1, sigma.shape[1] if sigma.ndim > 1 else 10)
    energies = np.linspace(0.1, 10.0, n_groups)
    positions = np.zeros((n_cells, 3))  # Would come from mesh geometry

    results = []
    for t in decay_times:
        decay_factor = np.exp(-lam * t)
        # [n_cells] -> [n_cells, n_groups]: same activation scaled by decay, uniform spectrum
        src_1d = activation * decay_factor
        source_strength = np.tile(src_1d[:, np.newaxis], (1, n_groups))
        results.append(
            PhotonSourceMesh(
                positions=positions,
                energies=energies,
                source_strength=source_strength,
                decay_time=t,
            )
        )
    return results


def _interpolate_dose_at_detectors(
    dose_mesh: np.ndarray,
    z_centers: np.ndarray,
    r_centers: np.ndarray,
    detector_positions: np.ndarray,
) -> np.ndarray:
    """Interpolate dose from 2D mesh to detector positions (z, r assumed; theta ignored)."""
    from scipy.interpolate import RegularGridInterpolator

    det = np.atleast_2d(detector_positions)
    n_det = det.shape[0]
    if n_det == 0:
        return np.array([])
    z_coord = det[:, 0]
    if det.shape[1] >= 3:
        r_coord = np.sqrt(det[:, 1] ** 2 + det[:, 2] ** 2)
    else:
        r_coord = np.abs(det[:, 1]) if det.shape[1] > 1 else np.zeros(n_det)
    interp = RegularGridInterpolator(
        (z_centers, r_centers), dose_mesh, bounds_error=False, fill_value=0.0
    )
    pts = np.column_stack([z_coord, r_coord])
    return interp(pts)


def r2s_shutdown_dose(
    neutron_flux: np.ndarray,
    sigma_capture: np.ndarray,
    material_map: np.ndarray,
    detector_positions: np.ndarray,
    shutdown_times: np.ndarray,
    gamma_solver: Any = None,
    geometry: Any = None,
) -> R2SResult:
    """
    Full R2S workflow: activation → photon source → dose.

    Args:
        neutron_flux: [nz, nr, ng] or [n_cells, ng]
        sigma_capture: [n_materials, ng]
        material_map: [nz, nr] or [n_cells]
        detector_positions: [n_detectors, 3] cm (z, x, y or z, r, theta)
        shutdown_times: [n_times] seconds after shutdown
        gamma_solver: Optional GammaTransportSolver for transport-based dose
        geometry: Optional PrismaticCore; required for gamma_solver integration

    Returns:
        R2SResult with dose rates
    """
    sources = compute_activation_photon_source(
        neutron_flux, sigma_capture, material_map, shutdown_times
    )
    n_det = len(detector_positions)
    n_times = len(shutdown_times)
    dose_vs_time = np.zeros((n_det, n_times))

    # Reshape source to [nz, nr, ng] if needed for gamma solver
    flux = np.asarray(neutron_flux)
    if flux.ndim == 3:
        nz, nr, ng = flux.shape
        source_3d_shape = (nz, nr, max(ng, sources[0].source_strength.shape[1]))
    else:
        nz, nr = 1, int(np.sqrt(flux.shape[0]))
        if nz * nr != flux.shape[0]:
            nr = flux.shape[0]
            nz = 1
        source_3d_shape = (nz, nr, sources[0].source_strength.shape[1])

    for it, src in enumerate(sources):
        src_arr = src.source_strength
        if src_arr.ndim == 2:
            n_cells, n_grp = src_arr.shape
            if n_cells == source_3d_shape[0] * source_3d_shape[1]:
                src_3d = src_arr.reshape(source_3d_shape[0], source_3d_shape[1], -1)
            else:
                src_3d = np.zeros(source_3d_shape)
                src_3d.flat[: min(src_arr.size, src_3d.size)] = src_arr.flat[: src_3d.size]
        else:
            src_3d = src_arr

        if gamma_solver is not None and geometry is not None:
            # Match group count to solver
            solver_ng = getattr(gamma_solver, "ng", src_3d.shape[2])
            if src_3d.shape[2] != solver_ng:
                from scipy.interpolate import interp1d

                old_ng = src_3d.shape[2]
                new_src = np.zeros((src_3d.shape[0], src_3d.shape[1], solver_ng))
                for iz in range(src_3d.shape[0]):
                    for ir in range(src_3d.shape[1]):
                        f = interp1d(
                            np.linspace(0, 1, old_ng),
                            src_3d[iz, ir, :],
                            kind="linear",
                            fill_value="extrapolate",
                        )
                        new_src[iz, ir, :] = f(np.linspace(0, 1, solver_ng))
                src_3d = new_src
            flux_g = gamma_solver.solve(src_3d)
            dose_mesh = gamma_solver.compute_dose_rate(flux_g)
            z_c = getattr(gamma_solver, "z_centers", np.array([0.0]))
            r_c = getattr(gamma_solver, "r_centers", np.array([0.0]))
            dose_vs_time[:, it] = _interpolate_dose_at_detectors(
                dose_mesh, z_c, r_c, detector_positions
            )
        else:
            # Fallback: simplified dose scaling
            total_source = np.sum(src_3d)
            dose_vs_time[:, it] = total_source * 1e-12  # Sv/h (placeholder)

    dose_rate = dose_vs_time[:, -1] if n_times > 0 else np.zeros(n_det)
    return R2SResult(
        dose_rate=dose_rate,
        detector_positions=np.asarray(detector_positions),
        shutdown_times=np.asarray(shutdown_times),
        dose_vs_time=dose_vs_time,
    )


def r2s_available() -> bool:
    """Check if R2S workflow dependencies are available."""
    try:
        from ..gamma_transport import GammaTransportSolver

        return True
    except ImportError:
        return False
