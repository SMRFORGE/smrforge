"""
Design of Experiments (DoE) for structured design-space sampling.

Provides factorial, Latin Hypercube, and space-filling designs that can
feed into parameter sweeps or optimization.
"""

from typing import Dict, List, Optional, Tuple, Union

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.workflows.doe")

try:
    from scipy.stats import qmc
    _SCIPY_QMC = True
except ImportError:
    _SCIPY_QMC = False


def full_factorial(
    levels: Dict[str, List[float]],
) -> List[Dict[str, float]]:
    """
    Full factorial design: every combination of levels for each factor.

    Args:
        levels: Map factor name -> list of values (e.g. {"enrichment": [0.1, 0.2], "power": [50, 100]}).

    Returns:
        List of dicts, each a point in the design space.
    """
    from itertools import product
    names = list(levels.keys())
    value_lists = [levels[n] for n in names]
    combinations = []
    for values in product(*value_lists):
        combinations.append(dict(zip(names, values)))
    return combinations


def latin_hypercube(
    names: List[str],
    bounds: List[Tuple[float, float]],
    n_samples: int,
    seed: Optional[int] = None,
) -> List[Dict[str, float]]:
    """
    Latin Hypercube Sampling (LHS) in the box defined by bounds.

    Args:
        names: Factor names.
        bounds: List of (low, high) for each factor.
        n_samples: Number of samples.
        seed: Random seed for reproducibility.

    Returns:
        List of dicts, each a point in the design space.
    """
    if not _SCIPY_QMC:
        raise ImportError("scipy.stats.qmc required for latin_hypercube: pip install scipy")
    sampler = qmc.LatinHypercube(d=len(names), seed=seed)
    u = sampler.random(n=n_samples)
    bounds_arr = np.array(bounds)
    scale = bounds_arr[:, 1] - bounds_arr[:, 0]
    shift = bounds_arr[:, 0]
    x = u * scale + shift
    return [dict(zip(names, row.tolist())) for row in x]


def random_space_filling(
    names: List[str],
    bounds: List[Tuple[float, float]],
    n_samples: int,
    seed: Optional[int] = None,
) -> List[Dict[str, float]]:
    """
    Uniform random sampling in the box (simple space-filling).

    Args:
        names: Factor names.
        bounds: List of (low, high) for each factor.
        n_samples: Number of samples.
        seed: Random seed.

    Returns:
        List of dicts.
    """
    rng = np.random.default_rng(seed)
    bounds_arr = np.array(bounds)
    scale = bounds_arr[:, 1] - bounds_arr[:, 0]
    shift = bounds_arr[:, 0]
    x = rng.uniform(0, 1, size=(n_samples, len(names))) * scale + shift
    return [dict(zip(names, row.tolist())) for row in x]


def sobol_space_filling(
    names: List[str],
    bounds: List[Tuple[float, float]],
    n_samples: int,
    seed: Optional[int] = None,
) -> List[Dict[str, float]]:
    """
    Sobol sequence (quasi-Monte Carlo) for low-discrepancy space-filling.

    Args:
        names: Factor names.
        bounds: List of (low, high) for each factor.
        n_samples: Number of samples.
        seed: Random seed (Sobol scramble).

    Returns:
        List of dicts.
    """
    if not _SCIPY_QMC:
        raise ImportError("scipy.stats.qmc required for sobol_space_filling: pip install scipy")
    sampler = qmc.Sobol(d=len(names), seed=seed)
    u = sampler.random(n=n_samples)
    bounds_arr = np.array(bounds)
    scale = bounds_arr[:, 1] - bounds_arr[:, 0]
    shift = bounds_arr[:, 0]
    x = u * scale + shift
    return [dict(zip(names, row.tolist())) for row in x]


def doe_to_sweep_combinations(
    design: List[Dict[str, float]],
) -> List[Dict[str, float]]:
    """Return design as-is (already list of dicts). For use with ParameterSweep-style runners."""
    return design
