"""
Variance reduction for Monte Carlo neutron transport.

Community: Basic ImportanceMap, WeightWindow (see transport.py, adaptive_sampling.py).
Pro: Advanced CADIS-style weight windows from diffusion adjoint—single Python stack,
no external deterministic codes. Overcomes competitor limitations (OpenMC/MCNP require
separate adjoint runs; MAGIC needs iterative MC).
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.neutronics.variance_reduction")

_ADVANCED_VR_MSG = (
    "Advanced variance reduction (CADIS, diffusion-accelerated weight windows) "
    "requires SMRForge Pro. Upgrade for CADIS-style weight window generation from "
    "diffusion adjoint—single Python stack, no external codes. "
    "See docs/community_vs_pro.md or https://smrforge.io"
)


def _pro_available() -> bool:
    """Check if SMRForge Pro is installed."""
    try:
        import smrforge_pro  # noqa: F401
        return True
    except ImportError:
        return False


def generate_cadis_weight_windows_from_diffusion(
    reactor: Any,
    diffusion_solver: Any,
    mesh: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]] = None,
    target_tally: Optional[str] = None,
    lower_bound: float = 0.5,
    upper_bound: float = 2.0,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Generate CADIS-style weight windows from diffusion adjoint flux (Pro tier).

    Uses Community's diffusion solver adjoint (solve_adjoint) to compute
    importance—no external deterministic codes (unlike OpenMC/MCNP CADIS).
    Produces weight window bounds for MonteCarloEngine.enable_variance_reduction.

    Competitor advantage:
    - OpenMC: Requires Denovo or MAGIC (iterative MC)
    - MCNP/MAVRIC: Requires SCALE Denovo
    - Serpent: Manual response matrix setup
    - SMRForge Pro: Single Python stack; diffusion adjoint already in Community

    Args:
        reactor: Reactor specification or geometry
        diffusion_solver: MultiGroupDiffusion with solve_adjoint
        mesh: Optional (r, z, e) mesh; auto from geometry if None
        target_tally: Optional tally type ('flux', 'reaction_rate')
        lower_bound: Weight window lower bound
        upper_bound: Weight window upper bound
        **kwargs: Pro-specific options

    Returns:
        Dict with 'weight_windows', 'importance_map', 'mesh_coords'

    Raises:
        ImportError: When Pro not installed
    """
    if not _pro_available():
        raise ImportError(_ADVANCED_VR_MSG)
    try:
        from smrforge_pro.neutronics.variance_reduction import (  # type: ignore[import-not-found]
            generate_cadis_weight_windows_from_diffusion as _generate,
        )
        return _generate(
            reactor=reactor,
            diffusion_solver=diffusion_solver,
            mesh=mesh,
            target_tally=target_tally,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            **kwargs,
        )
    except ImportError:
        raise ImportError(_ADVANCED_VR_MSG)


def export_weight_windows_to_openmc(
    weight_windows: Dict[str, Any],
    output_path: Union[str, Path],
    format: str = "h5",
) -> Path:
    """
    Export weight windows to OpenMC/MCNP-compatible format (Pro tier).

    Supports WWINP (MCNP) and HDF5 for OpenMC WeightWindowGenerator.

    Args:
        weight_windows: Output from generate_cadis_weight_windows_from_diffusion
        output_path: File path to write
        format: 'h5' or 'wwinp'

    Raises:
        ImportError: When Pro not installed
    """
    if not _pro_available():
        raise ImportError(_ADVANCED_VR_MSG)
    try:
        from smrforge_pro.neutronics.variance_reduction import (  # type: ignore[import-not-found]
            export_weight_windows_to_openmc as _export,
        )
        return _export(
            weight_windows=weight_windows,
            output_path=output_path,
            format=format,
        )
    except ImportError:
        raise ImportError(_ADVANCED_VR_MSG)


def get_smr_preset_importance(
    reactor_type: str = "htgr",
    core_height: float = 200.0,
    core_radius: float = 100.0,
) -> Optional[Dict[str, np.ndarray]]:
    """
    Get SMR-preset importance map for common geometries (Pro tier).

    Pre-tuned spatial importance for HTGR compact core, LWR SMR, etc.
    Reduces setup time vs. generic CADIS for SMR-specific problems.

    Args:
        reactor_type: 'htgr', 'lwr_smr', 'pebble_bed'
        core_height: Core height [cm]
        core_radius: Core radius [cm]

    Returns:
        Dict with 'importance', 'r_coords', 'z_coords' or None
    """
    if not _pro_available():
        raise ImportError(_ADVANCED_VR_MSG)
    try:
        from smrforge_pro.neutronics.variance_reduction import (  # type: ignore[import-not-found]
            get_smr_preset_importance as _get,
        )
        return _get(
            reactor_type=reactor_type,
            core_height=core_height,
            core_radius=core_radius,
        )
    except ImportError:
        raise ImportError(_ADVANCED_VR_MSG)
