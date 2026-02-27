"""
Real-time digital twin: live surrogate updates from plant/solver data.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.digital_twin")


def create_digital_twin(
    initial_surrogate: Any,
    update_fn: Optional[Callable[[np.ndarray, np.ndarray], Any]] = None,
    drift_threshold: float = 0.05,
) -> "DigitalTwinSurrogate":
    """Create digital twin with optional online update."""
    return DigitalTwinSurrogate(initial_surrogate, update_fn, drift_threshold)


class DigitalTwinSurrogate:
    """Digital twin surrogate with streaming update and drift detection."""

    def __init__(
        self,
        surrogate: Any,
        update_fn: Optional[Callable] = None,
        drift_threshold: float = 0.05,
    ):
        self._surrogate = surrogate
        self._update_fn = update_fn
        self._drift_threshold = drift_threshold
        self._history: List[Dict[str, Any]] = []
        self._last_pred: Optional[float] = None

    def predict(self, params: Dict[str, float]) -> float:
        """Predict and optionally check drift."""
        pred = self._surrogate.predict(params)
        self._last_pred = pred
        self._history.append({"params": params.copy(), "pred": pred})
        return pred

    def update(self, X: np.ndarray, y: np.ndarray) -> None:
        """Update surrogate with new data (online learning)."""
        if self._update_fn is not None:
            self._surrogate = self._update_fn(X, y)
        logger.info("Digital twin updated with %d new samples", len(y))

    def check_drift(self, observed: float) -> bool:
        """Check if observed value suggests drift."""
        if self._last_pred is None:
            return False
        err = abs(observed - self._last_pred)
        return err > self._drift_threshold
