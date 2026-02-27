"""
Community capabilities integration for Pro AI features.

Exposes new Community tier features (SN 3D/hexagonal, CFD adapters,
polynomial chaos sparse/adaptive, weight windows, benchmarks, etc.)
so Pro AI workflows (nl_design, surrogates, validation) can use them.

All imports are lazy to avoid loading Community until needed.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.integration.community_capabilities")


def get_community_capabilities() -> Dict[str, Dict[str, Any]]:
    """
    Return registry of Community capabilities Pro AI can use.

    Returns:
        Dict mapping capability_id -> {description, import_fn, params}
    """
    return {
        "sn_1d": {
            "description": "1D slab SN transport (S2/S4)",
            "module": "smrforge.neutronics.sn_transport",
            "class": "SNTransportSolver",
        },
        "sn_2d_cylindrical": {
            "description": "2D r-z cylindrical SN transport",
            "module": "smrforge.neutronics.sn_transport",
            "class": "SN2DCylindricalSolver",
        },
        "sn_3d_cartesian": {
            "description": "3D Cartesian SN transport",
            "module": "smrforge.neutronics.sn_transport",
            "class": "SN3DCartesianSolver",
        },
        "sn_2d_hexagonal": {
            "description": "2D hexagonal lattice SN transport",
            "module": "smrforge.neutronics.sn_transport",
            "class": "SN2DHexagonalSolver",
        },
        "cfd_openfoam": {
            "description": "OpenFOAM CFD adapter",
            "module": "smrforge.coupling.cfd_integration",
            "class": "OpenFOAMAdapter",
        },
        "cfd_moose": {
            "description": "MOOSE CFD adapter",
            "module": "smrforge.coupling.cfd_integration",
            "class": "MOOSEAdapter",
        },
        "polynomial_chaos": {
            "description": "Polynomial chaos expansion (sparse, adaptive)",
            "module": "smrforge.uncertainty.uq",
            "func": "polynomial_chaos_expansion",
        },
        "quasi_static_transient": {
            "description": "Quasi-static spatial dynamics",
            "module": "smrforge_pro.workflows.transients",
            "func": "run_quasi_static_transient",
        },
        "weight_windows_from_importance": {
            "description": "Generate weight windows from importance map",
            "module": "smrforge.neutronics.adaptive_sampling",
            "func": "generate_weight_windows_from_importance",
        },
        "execute_and_document_benchmarks": {
            "description": "Run and document validation benchmarks",
            "module": "smrforge.validation.benchmark_runner",
            "func": "execute_and_document_benchmarks",
        },
        "pc_depletion": {
            "description": "Predictor-corrector depletion integrator",
            "module": "smrforge.burnup.predictor_corrector",
            "func": "pc_depletion_step",
        },
        "dose_tally": {
            "description": "Dose tally for MC",
            "module": "smrforge.neutronics.monte_carlo",
            "class": "DoseTally",
        },
        "pulse_height_tally": {
            "description": "Pulse-height tally for MC",
            "module": "smrforge.neutronics.monte_carlo",
            "class": "PulseHeightTally",
        },
    }


def _import_capability(capability_id: str) -> Any:
    """Lazy import of a Community capability."""
    import importlib

    caps = get_community_capabilities()
    if capability_id not in caps:
        raise ValueError(
            f"Unknown capability '{capability_id}'. Available: {list(caps.keys())}"
        )
    spec = caps[capability_id]
    mod = importlib.import_module(spec["module"])
    if "class" in spec:
        return getattr(mod, spec["class"])
    return getattr(mod, spec["func"])


def run_sn_solver(
    solver_type: str,
    sigma_t: float = 0.5,
    sigma_s: float = 0.4,
    nu_sigma_f: float = 0.1,
    n_cells: Optional[Union[int, Tuple[int, ...]]] = None,
    order: int = 2,
) -> Dict[str, Any]:
    """
    Run an SN transport solver (Pro AI access to Community SN).

    Args:
        solver_type: "sn_1d", "sn_2d_cylindrical", "sn_3d_cartesian", "sn_2d_hexagonal"
        sigma_t, sigma_s, nu_sigma_f: Cross sections
        n_cells: For 1D: int. For 2D: (n_r, n_z). For 3D: (nx, ny, nz). For hex: n_rings
        order: 2 (S2) or 4 (S4)

    Returns:
        Dict with k_eff, scalar_flux, converged, etc.
    """
    if solver_type == "sn_1d":
        n = n_cells or 20
        Cls = _import_capability("sn_1d")
        solver = Cls(n, sigma_t, sigma_s, nu_sigma_f, order=order)
    elif solver_type == "sn_2d_cylindrical":
        nc = n_cells or (5, 5)
        nr, nz = (nc[0], nc[1]) if isinstance(nc, (tuple, list)) else (5, 5)
        Cls = _import_capability("sn_2d_cylindrical")
        solver = Cls(nr, nz, sigma_t, sigma_s, nu_sigma_f, order=order)
    elif solver_type == "sn_3d_cartesian":
        nx, ny, nz = n_cells or (3, 3, 3)
        Cls = _import_capability("sn_3d_cartesian")
        solver = Cls(nx, ny, nz, sigma_t, sigma_s, nu_sigma_f, order=order)
    elif solver_type == "sn_2d_hexagonal":
        n_rings = int(n_cells) if n_cells is not None else 2
        Cls = _import_capability("sn_2d_hexagonal")
        solver = Cls(n_rings, sigma_t, sigma_s, nu_sigma_f, order=order)
    else:
        raise ValueError(f"Unknown solver_type: {solver_type}")

    result = solver.solve_eigenvalue(max_iter=200, tolerance=1e-6)
    return {
        "k_eff": result.k_eff,
        "scalar_flux": result.scalar_flux,
        "converged": result.converged,
        "n_iterations": result.n_iterations,
    }


def run_polynomial_chaos(
    parameters: List[Any],
    model: Callable,
    output_names: List[str],
    degree: int = 2,
    sparse: bool = False,
    adaptive_degree: bool = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Run polynomial chaos expansion (Pro AI access to Community UQ).

    Supports sparse and adaptive_degree options.
    """
    pce = _import_capability("polynomial_chaos")
    return pce(
        parameters,
        model,
        output_names,
        degree=degree,
        sparse=sparse,
        adaptive_degree=adaptive_degree,
        **kwargs,
    )


def run_quasi_static_transient(
    reactor: Any,
    t_span: Tuple[float, float],
    reactivity_fn: Callable[[float], float],
    **kwargs: Any,
) -> Dict[str, Any]:
    """Run quasi-static transient (Pro AI access)."""
    fn = _import_capability("quasi_static_transient")
    return fn(reactor, t_span, reactivity_fn, **kwargs)


def get_cfd_adapter(
    adapter_type: str,
    work_dir: Union[str, Path],
    **kwargs: Any,
) -> Any:
    """
    Get CFD adapter (OpenFOAM or MOOSE) for Pro AI workflows.

    Args:
        adapter_type: "cfd_openfoam" or "cfd_moose"
        work_dir: Case directory
        **kwargs: Passed to adapter constructor

    Returns:
        OpenFOAMAdapter or MOOSEAdapter instance
    """
    Cls = _import_capability(adapter_type)
    return Cls(work_dir=work_dir, **kwargs)


def get_weight_windows_from_importance(
    importance_map: Any,
    **kwargs: Any,
) -> Any:
    """Generate weight windows from importance map (Pro AI access)."""
    fn = _import_capability("weight_windows_from_importance")
    return fn(importance_map, **kwargs)


def run_execute_and_document_benchmarks(
    benchmark_names: Optional[List[str]] = None,
    output_dir: Optional[Path] = None,
    **kwargs: Any,
) -> Tuple[List[Any], Path]:
    """Run Community benchmark suite (Pro AI access)."""
    fn = _import_capability("execute_and_document_benchmarks")
    return fn(
        benchmark_names=benchmark_names,
        output_dir=output_dir,
        **kwargs,
    )


def run_reference_physics(
    spec: Union[Dict[str, Any], Any],
    solver_type: str = "reactor",
    output_metric: str = "k_eff",
) -> float:
    """
    Run reference physics for a given spec (Pro AI access).

    Use this when generating reference values for surrogate validation.
    Supports: reactor (default), sn_1d, sn_2d_cylindrical, sn_3d_cartesian, sn_2d_hexagonal.

    Args:
        spec: Reactor spec dict or preset name for reactor; or ignored for SN (uses default xs)
        solver_type: "reactor" (create_reactor + solve) or sn_* for SN solvers
        output_metric: Key to extract (e.g. "k_eff")

    Returns:
        Reference value (e.g. k_eff)
    """
    if solver_type == "reactor":
        from smrforge.convenience import create_reactor

        preset = spec.get("preset", "valar-10") if isinstance(spec, dict) else str(spec)
        kwargs = {k: v for k, v in (spec or {}).items() if k in ("power_mw", "enrichment", "cycle_length")}
        reactor = create_reactor(preset, **kwargs)
        result = reactor.solve()
        return float(result.get(output_metric, 0.0))

    if solver_type.startswith("sn_"):
        result = run_sn_solver(solver_type=solver_type)
        return float(result.get("k_eff", 0.0))

    raise ValueError(f"Unknown solver_type: {solver_type}")
