"""
Cross-section covariance data parsing and uncertainty propagation.

ENDF files contain covariance data in MF31-40. This module provides:
- Parsing of covariance matrices from ENDF
- Integration with UQ for nuclear data uncertainty
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.core.covariance")


@dataclass
class CovarianceBlock:
    """Covariance matrix block for a reaction pair."""

    mt1: int
    mt2: int
    matrix: np.ndarray
    energy_bounds: Optional[Tuple[float, float]] = None


def parse_endf_covariance_mf33(filepath: Path) -> List[CovarianceBlock]:
    """
    Parse ENDF MF33 (covariance matrix) section.

    Placeholder: full implementation requires ENDF covariance format parsing.
    MF33 contains reaction-reaction or energy-reaction covariances.

    Args:
        filepath: Path to ENDF file

    Returns:
        List of CovarianceBlock (empty if parsing not implemented)
    """
    blocks: List[CovarianceBlock] = []
    try:
        with open(filepath) as f:
            for line in f:
                if " 33 " in line[:66] or " 33 " in line[70:72]:
                    logger.debug("MF33 section found - full parser not yet implemented")
                    break
    except Exception as e:
        logger.warning(f"Covariance parse failed for {filepath}: {e}")
    return blocks


def sample_cross_sections_with_covariance(
    mean: np.ndarray,
    covariance: np.ndarray,
    n_samples: int,
    rng: Optional[np.random.Generator] = None,
) -> np.ndarray:
    """
    Sample cross-sections from multivariate normal using covariance.

    Args:
        mean: Mean cross-section values [n]
        covariance: Covariance matrix [n,n]
        n_samples: Number of samples
        rng: Random number generator

    Returns:
        Samples [n_samples, n]
    """
    rng = rng or np.random.default_rng()
    try:
        L = np.linalg.cholesky(covariance + 1e-10 * np.eye(len(mean)))
        z = rng.standard_normal((n_samples, len(mean)))
        return mean + (z @ L.T)
    except np.linalg.LinAlgError:
        logger.warning("Covariance not positive definite, using diagonal")
        std = np.sqrt(np.diag(covariance) + 1e-20)
        return mean + rng.standard_normal((n_samples, len(mean))) * std
