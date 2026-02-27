"""
Predictor-corrector depletion integrator.

Alternative to CRAM and SI-CE. Uses explicit Euler predictor + trapezoidal
corrector. Good for non-stiff or mildly stiff systems; less accurate than
CRAM for very stiff burnup chains.

Reference: Standard ODE predictor-corrector methods.
"""

from typing import Optional

import numpy as np
from scipy.sparse import issparse, spmatrix
from scipy.sparse.linalg import spsolve

from ..utils.logging import get_logger

logger = get_logger("smrforge.burnup.predictor_corrector")


def pc_depletion_step(
    A: np.ndarray,
    n: np.ndarray,
    dt: float,
    A_sparse: Optional[spmatrix] = None,
) -> np.ndarray:
    """
    Advance nuclide vector n by time step dt using predictor-corrector.

    Predictor: n* = n + dt * A @ n (explicit Euler)
    Corrector: n_new = n + dt/2 * (A @ n + A @ n*) (trapezoidal)

    Args:
        A: Transmutation matrix [N x N]
        n: Nuclide concentrations [N]
        dt: Time step [s]
        A_sparse: Optional sparse form (unused; kept for API compatibility)

    Returns:
        Updated concentrations n_new [N]
    """
    n = np.asarray(n, dtype=np.float64).ravel()
    N = len(n)
    if A.shape != (N, N):
        raise ValueError(f"Matrix A shape {A.shape} incompatible with n length {N}")

    A_dense = A.toarray() if issparse(A) else np.asarray(A, dtype=np.float64)

    # Predictor
    n_pred = n + dt * A_dense.dot(n)

    # Corrector
    n_new = n + (dt / 2) * (A_dense.dot(n) + A_dense.dot(n_pred))

    return np.asarray(n_new).ravel()
