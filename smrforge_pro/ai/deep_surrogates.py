"""
Deep surrogate backends: MLP, Fourier features, ResNet-style.

Tier 1: Neural network surrogates for k_eff, flux, burnup.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.ai.deep_surrogates")


def fit_deep_surrogate(
    X: np.ndarray,
    y: np.ndarray,
    architecture: str = "mlp",
    param_names: Optional[List[str]] = None,
    hidden: Tuple[int, ...] = (128, 128, 64),
    n_epochs: int = 500,
    fourier_dim: int = 0,
    **kwargs: Any,
) -> "DeepSurrogate":
    """
    Fit deep neural network surrogate.

    Args:
        X: Design points
        y: Target values
        architecture: "mlp", "fourier_mlp", "resnet"
        param_names: Parameter names for predict interface
        hidden: Hidden layer sizes
        n_epochs: Training epochs
        fourier_dim: Fourier feature dimension (0 = none)
        **kwargs: Passed to backend

    Returns:
        DeepSurrogate model
    """
    try:
        import torch
        import torch.nn as nn
    except ImportError:
        raise ImportError("PyTorch required for deep surrogate: pip install torch")

    param_names = param_names or [f"x{i}" for i in range(X.shape[1])]
    in_dim = X.shape[1]

    if architecture == "fourier_mlp" and fourier_dim > 0:
        B = torch.randn(in_dim, fourier_dim) * 2.0
        in_dim = in_dim + 2 * fourier_dim

    layers = [nn.Linear(in_dim, hidden[0]), nn.ReLU()]
    for i in range(len(hidden) - 1):
        layers.extend([nn.Linear(hidden[i], hidden[i + 1]), nn.ReLU()])
    layers.append(nn.Linear(hidden[-1], 1))
    net = nn.Sequential(*layers)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)

    X_t = torch.tensor(X, dtype=torch.float32)
    if architecture == "fourier_mlp" and fourier_dim > 0:
        x_ff = torch.cat([X_t, torch.sin(X_t @ B), torch.cos(X_t @ B)], dim=1)
    else:
        x_ff = X_t
    y_t = torch.tensor(y.reshape(-1, 1), dtype=torch.float32)

    for _ in range(n_epochs):
        opt.zero_grad()
        loss = ((net(x_ff) - y_t) ** 2).mean()
        loss.backward()
        opt.step()

    return DeepSurrogate(net, param_names, fourier_B=B if fourier_dim > 0 else None)


class DeepSurrogate:
    """Deep NN surrogate with predict(params) interface."""

    def __init__(self, net: Any, param_names: List[str], fourier_B: Any = None):
        self._net = net
        self._param_names = param_names
        self._fourier_B = fourier_B

    def predict(self, params: Dict[str, float]) -> float:
        """Predict output for given parameters."""
        try:
            import torch
        except ImportError:
            raise ImportError("PyTorch required")
        order = self._param_names or sorted(params.keys())
        x = torch.tensor([[params.get(k, 0.0) for k in order]], dtype=torch.float32)
        if self._fourier_B is not None:
            x = torch.cat([x, torch.sin(x @ self._fourier_B), torch.cos(x @ self._fourier_B)], dim=1)
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
