"""
Transient analysis workflows (Pro).

Uses Community QuasiStaticSolver for spatial dynamics (shape/amplitude factorization).
Pro integrates this for regulatory and verification workflows.
"""

from pathlib import Path
from typing import Any, Callable, Dict, Optional

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.workflows.transients")


def run_quasi_static_transient(
    reactor: Any,
    t_span: tuple,
    reactivity_fn: Callable[[float], float],
    initial_power: float = 1.0,
    n_times: int = 200,
    n_nodes: int = 10,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Run quasi-static transient using Community QuasiStaticSolver.

    Pro integration: leverages Community spatial dynamics for improved
    transient accuracy vs. point kinetics alone.

    Args:
        reactor: Reactor instance (unused; for API consistency)
        t_span: (t_start, t_end) in seconds
        reactivity_fn: reactivity(t) -> rho
        initial_power: Initial power (normalized)
        n_times: Number of time points
        n_nodes: Spatial nodes for shape function
        output_dir: Where to write results

    Returns:
        Dict with 'power_history', 'times', 'reactivity_history', etc.
    """
    try:
        from smrforge.safety.quasi_static import QuasiStaticSolver, QuasiStaticOptions
    except ImportError as e:
        raise ImportError(
            "run_quasi_static_transient requires smrforge with QuasiStaticSolver. pip install smrforge"
        ) from e

    opts = QuasiStaticOptions(
        use_constant_shape=False,
        min_shape_update_interval=0.01,
    )
    qs = QuasiStaticSolver(
        n_nodes=n_nodes,
        beta_total=0.007,
        gen_time=1e-5,
        options=opts,
    )

    result = qs.solve(
        t_span=t_span,
        reactivity_fn=reactivity_fn,
        initial_power=initial_power,
        n_times=n_times,
        material_feedback_fn=None,
    )

    out = {
        "power_history": result.power_history.tolist(),
        "times": result.times.tolist(),
        "reactivity_history": result.reactivity_history.tolist(),
        "amplitudes": result.amplitudes.tolist(),
        "n_shape_updates": result.n_shape_updates,
        "converged": result.converged,
    }

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        import json

        (output_dir / "transient_result.json").write_text(
            json.dumps(out, indent=2),
            encoding="utf-8",
        )
        logger.info("Transient results written to %s", output_dir)

    return out
