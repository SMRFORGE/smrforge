"""
Physics-Informed Neural Networks (PINNs) for reactor analysis.

Tier 1: Embed PDE residuals in loss for better generalization.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.ai.pinn")


def fit_pinn_surrogate(
    X: np.ndarray,
    y: np.ndarray,
    physics_residual_fn: Optional[Callable[[np.ndarray, np.ndarray], np.ndarray]] = None,
    param_names: Optional[List[str]] = None,
    n_epochs: int = 500,
    hidden_layers: Tuple[int, ...] = (64, 64),
    physics_weight: float = 0.1,
    **kwargs: Any,
):
    """Fit Physics-Informed Neural Network surrogate."""
    try:
        import torch
        import torch.nn as nn
    except ImportError:
        raise ImportError("PyTorch required for PINN: pip install torch")

    param_names = param_names or [f"x{i}" for i in range(X.shape[1])]
    X_t = torch.tensor(X, dtype=torch.float32)
    y_t = torch.tensor(y.reshape(-1, 1), dtype=torch.float32)

    in_dim = X.shape[1]
    layers = [nn.Linear(in_dim, hidden_layers[0]), nn.Tanh()]
    for i in range(len(hidden_layers) - 1):
        layers.extend([nn.Linear(hidden_layers[i], hidden_layers[i + 1]), nn.Tanh()])
    layers.append(nn.Linear(hidden_layers[-1], 1))
    net = nn.Sequential(*layers)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)

    for _ in range(n_epochs):
        opt.zero_grad()
        y_pred = net(X_t)
        loss = ((y_pred - y_t) ** 2).mean()
        if physics_residual_fn is not None:
            res = physics_residual_fn(X_t.detach().numpy(), y_pred.detach().numpy())
            loss = loss + physics_weight * float(np.square(res).mean())
        loss.backward()
        opt.step()

    return PINNSurrogate(net, param_names)


class PINNSurrogate:
    """PINN surrogate with predict(params) interface."""

    def __init__(self, net: Any, param_names: List[str]):
        self._net = net
        self._param_names = param_names

    def predict(self, params: Dict[str, float]) -> float:
        """Predict output for given parameters."""
        try:
            import torch
        except ImportError:
            raise ImportError("PyTorch required")
        order = self._param_names or sorted(params.keys())
        x = torch.tensor([[params.get(k, 0.0) for k in order]], dtype=torch.float32)
        with torch.no_grad():
            return float(self._net(x).item())

    def save(self, path: Path) -> None:
        """Save model."""
        try:
            import torch
        except ImportError:
            raise ImportError("PyTorch required")
        path = Path(path)
        if path.suffix != ".pt":
            path = path.with_suffix(".pt")
        torch.jit.save(torch.jit.script(self._net), str(path))
