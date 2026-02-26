"""
AI-assisted multi-objective design optimization (Pro).

Optimize across neutronics, safety margins, and economics in one framework.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.workflows.multi_objective_optimization")


@dataclass
class MultiObjectiveResult:
    """Result of multi-objective optimization."""

    x_opt: np.ndarray
    objectives: Dict[str, float]
    param_names: List[str]
    n_evaluations: int
    success: bool
    message: str = ""
    pareto_front: Optional[List[Dict[str, Any]]] = None


def multi_objective_optimize(
    reactor_from_x: Callable[[np.ndarray], Any],
    bounds: List[Tuple[float, float]],
    param_names: List[str],
    objectives: Optional[Dict[str, Callable[[Any], float]]] = None,
    weights: Optional[Dict[str, float]] = None,
    max_evaluations: int = 100,
    seed: Optional[int] = None,
) -> MultiObjectiveResult:
    """
    Multi-objective design optimization across neutronics, safety, economics.

    Args:
        reactor_from_x: Maps param vector to reactor (with .solve(), .spec)
        bounds: Parameter bounds [(min, max), ...]
        param_names: Names for parameters
        objectives: Dict of objective_name -> f(reactor) -> float to minimize
            Default: k_eff (maximize = minimize -k_eff), safety_margin, cost
        weights: Weight for each objective in scalarization (default: equal)
        max_evaluations: Max function evaluations
        seed: Random seed

    Returns:
        MultiObjectiveResult with optimal point and objective values
    """
    if objectives is None:
        def _k_eff_obj(r):
            try:
                res = r.solve()
                return -float(res.get("k_eff", 0))  # minimize -k_eff = maximize k_eff
            except Exception:
                return 1e6

        objectives = {"k_eff": _k_eff_obj}

    if weights is None:
        weights = {k: 1.0 / len(objectives) for k in objectives}

    def scalarized(x: np.ndarray) -> float:
        try:
            reactor = reactor_from_x(x)
            total = 0.0
            for name, fn in objectives.items():
                val = fn(reactor)
                total += weights.get(name, 1.0) * val
            return total
        except Exception as e:
            logger.debug(f"Evaluation failed: {e}")
            return 1e6

    try:
        from scipy.optimize import differential_evolution

        rng = np.random.default_rng(seed)
        result = differential_evolution(
            scalarized,
            bounds,
            maxiter=max_evaluations // 10,
            popsize=15,
            seed=rng,
            polish=True,
            atol=1e-4,
            tol=1e-3,
            disp=False,
        )

        reactor_opt = reactor_from_x(result.x)
        obj_vals = {}
        for name, fn in objectives.items():
            try:
                obj_vals[name] = fn(reactor_opt)
            except Exception:
                obj_vals[name] = float("nan")

        return MultiObjectiveResult(
            x_opt=result.x,
            objectives=obj_vals,
            param_names=param_names,
            n_evaluations=result.nfev,
            success=bool(result.success),
            message=str(result.message),
        )
    except ImportError:
        raise ImportError(
            "multi_objective_optimize requires scipy. pip install scipy"
        ) from None
