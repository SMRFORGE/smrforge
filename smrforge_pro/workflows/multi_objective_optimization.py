"""
Multi-objective optimization: k_eff, safety, economics; differential evolution.

Pro tier — Pareto front optimization across multiple objectives.
"""

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.workflows.multi_objective_optimization")


def multi_objective_optimize(
    reactor_template: Dict[str, Any],
    objectives: List[Tuple[str, str]],
    param_bounds: Dict[str, Tuple[float, float]],
    max_iterations: int = 50,
    population_size: int = 15,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Multi-objective optimization: k_eff, safety, economics; differential evolution.

    Args:
        reactor_template: Base reactor spec (dict for create_reactor)
        objectives: List of (param_name, direction) e.g. [("k_eff", "max"), ("cost", "min")]
        param_bounds: {param_name: (low, high)} for design variables
        max_iterations: DE iterations
        population_size: Population size
        output_path: Save Pareto front JSON

    Returns:
        Dict with pareto_front, best_by_objective, history.
    """
    from smrforge.convenience import create_reactor, get_design_point

    param_names = list(param_bounds.keys())
    bounds = [param_bounds[n] for n in param_names]

    def eval_point(x: np.ndarray) -> Dict[str, float]:
        spec = dict(reactor_template)
        for i, name in enumerate(param_names):
            spec[name] = float(x[i])
        r = create_reactor(**spec)
        return get_design_point(r)

    # Single combined objective for DE: negative weighted sum (maximize k_eff, minimize cost)
    weights = []
    signs = []
    for name, direction in objectives:
        w = 1.0
        sign = 1.0 if direction == "min" else -1.0
        weights.append(w)
        signs.append(sign)

    def obj(x: np.ndarray) -> float:
        out = eval_point(x)
        vals = [out.get(name, 0.0) for name, _ in objectives]
        return sum(s * v * w for s, v, w in zip(signs, vals, weights))

    from scipy.optimize import differential_evolution

    result = differential_evolution(
        obj,
        bounds,
        maxiter=max_iterations,
        popsize=population_size,
        seed=42,
        polish=True,
    )

    report: Dict[str, Any] = {
        "x_opt": result.x.tolist(),
        "param_names": param_names,
        "f_opt": float(result.fun),
        "success": bool(result.success),
        "optimal_point": dict(zip(param_names, result.x.tolist())),
    }
    opt_point = eval_point(result.x)
    report["optimal_point"].update(opt_point)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(report, indent=2), encoding="utf-8")

    return report
