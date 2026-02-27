"""
Neural operators (FNO, DeepONet) for full-field outputs.

Tier 1: Learn discretization-invariant mappings design -> flux, power.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.ai.neural_operators")


def fit_fno_surrogate(
    X: np.ndarray,
    y_fields: np.ndarray,
    param_names: Optional[List[str]] = None,
    n_modes: int = 4,
    n_epochs: int = 200,
    **kwargs: Any,
) -> "FNOSurrogate":
    """
    Fit Fourier Neural Operator surrogate for field outputs.

    Simplified FNO: design params -> field (e.g. flux shape).
    Full FNO operates on function spaces; this is a reduced version.

    Args:
        X: Design points
        y_fields: Field outputs (n_samples, n_spatial)
        param_names: Parameter names
        n_modes: Fourier modes
        n_epochs: Training epochs
        **kwargs: Passed to backend

    Returns:
        FNOSurrogate model
    """
    try:
        import torch
        import torch.nn as nn
    except ImportError:
        raise ImportError("PyTorch required for FNO: pip install torch")

    param_names = param_names or [f"x{i}" for i in range(X.shape[1])]
    in_dim = X.shape[1]
    out_dim = y_fields.shape[1] if y_fields.ndim > 1 else 1

    class FNOBlock(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc = nn.Linear(in_dim + n_modes * 2, 64)
            self.fc2 = nn.Linear(64, out_dim)

        def forward(self, x):
            mode_feat = torch.cat([torch.sin(x[:, :n_modes]), torch.cos(x[:, :n_modes])], dim=1)
            pad = torch.zeros(x.shape[0], n_modes * 2 - min(n_modes * 2, x.shape[1]), device=x.device)
            mode_feat = torch.cat([mode_feat, pad[:, : max(0, n_modes * 2 - mode_feat.shape[1])]], dim=1)[:, : n_modes * 2]
            h = torch.cat([x, mode_feat], dim=1)[:, : in_dim + n_modes * 2]
            h = torch.relu(self.fc(h))
            return self.fc2(h)

    net = FNOBlock()
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    X_t = torch.tensor(X, dtype=torch.float32)
    y_t = torch.tensor(y_fields, dtype=torch.float32)
    if y_t.ndim == 1:
        y_t = y_t.reshape(-1, 1)

    for _ in range(n_epochs):
        opt.zero_grad()
        loss = ((net(X_t) - y_t) ** 2).mean()
        loss.backward()
        opt.step()

    return FNOSurrogate(net, param_names, out_dim)


class FNOSurrogate:
    """FNO-style surrogate for field prediction."""

    def __init__(self, net: Any, param_names: List[str], out_dim: int = 1):
        self._net = net
        self._param_names = param_names
        self._out_dim = out_dim

    def predict(self, params: Dict[str, float]) -> np.ndarray:
        """Predict field for given parameters."""
        try:
            import torch
        except ImportError:
            raise ImportError("PyTorch required")
        order = self._param_names or sorted(params.keys())
        x = torch.tensor([[params.get(k, 0.0) for k in order]], dtype=torch.float32)
        with torch.no_grad():
            out = self._net(x).numpy()
        return out.flatten()

    def predict_scalar(self, params: Dict[str, float]) -> float:
        """Predict scalar (e.g. mean flux) for compatibility."""
        return float(self.predict(params).mean())
