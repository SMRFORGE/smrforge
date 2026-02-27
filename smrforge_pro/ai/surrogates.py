"""
Surrogate model loading for Pro tier.

Supports ONNX, TorchScript, pickle (sklearn) formats.
"""

import hashlib
import pickle
from pathlib import Path
from typing import Any, List, Optional

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.ai.surrogates")


def load_surrogate_from_path(
    path: Path,
    param_names: Optional[List[str]] = None,
) -> Any:
    """
    Load surrogate model from file.

    Supports: .pkl (sklearn), .pt/.pth (TorchScript), .onnx (ONNX).

    Args:
        path: Path to model file
        param_names: Optional list of parameter names for predict interface

    Returns:
        Model with .predict(params_dict) interface
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Surrogate model not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".pkl":
        with open(path, "rb") as f:
            model = pickle.load(f)
        return _wrap_sklearn(model, param_names)

    if suffix in (".pt", ".pth"):
        try:
            import torch

            model = torch.jit.load(str(path))
            return _wrap_torchscript(model, param_names)
        except ImportError:
            raise ImportError("PyTorch required for .pt/.pth: pip install torch")

    if suffix == ".onnx":
        try:
            import onnxruntime as ort

            sess = ort.InferenceSession(str(path))
            return _wrap_onnx(sess, param_names)
        except ImportError:
            raise ImportError("onnxruntime required for .onnx: pip install onnxruntime")

    raise ValueError(f"Unsupported surrogate format: {suffix}. Use .pkl, .pt, .onnx")


def model_hash(path: Path) -> str:
    """
    Compute SHA-256 hash of model file for audit/versioning.

    Args:
        path: Path to model file

    Returns:
        64-char hex string
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _wrap_sklearn(model: Any, param_names: Optional[List[str]]) -> Any:
    """Wrap sklearn-like model with predict(params_dict) interface."""
    order = param_names or []

    class Wrapper:
        def predict(self, params: dict) -> float:
            if isinstance(params, dict):
                keys = order or sorted(params.keys())
                X = [[params.get(k, 0.0) for k in keys]]
            else:
                X = params
            out = model.predict(X)
            return float(out[0] if hasattr(out, "__len__") else out)

    return Wrapper()


def _wrap_torchscript(model: Any, param_names: Optional[List[str]]) -> Any:
    """Wrap TorchScript model with predict(params_dict) interface."""
    import numpy as np

    param_names = param_names or []

    class Wrapper:
        def predict(self, params: dict) -> float:
            order = param_names or sorted(params.keys())
            x = np.array([[params.get(k, 0.0) for k in order]], dtype=np.float32)
            t = __import__("torch").tensor(x)
            out = model.forward(t)
            return float(out.item() if out.numel() == 1 else out[0, 0])

    return Wrapper()


def _wrap_onnx(sess: Any, param_names: Optional[List[str]]) -> Any:
    """Wrap ONNX session with predict(params_dict) interface."""
    import numpy as np

    inputs = sess.get_inputs()
    inp_name = inputs[0].name
    param_names = param_names or [f"x{i}" for i in range(inputs[0].shape[-1] if inputs[0].shape else 1)]

    class Wrapper:
        def predict(self, params: dict) -> float:
            order = param_names or sorted(params.keys())
            x = np.array([[params.get(k, 0.0) for k in order]], dtype=np.float32)
            out = sess.run(None, {inp_name: x})
            return float(out[0].item() if out[0].size == 1 else out[0][0, 0])

    return Wrapper()
