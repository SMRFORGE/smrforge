"""
BYOS (Bring Your Own Surrogate) - Load ONNX, TorchScript, sklearn from file path.

Pro tier: Full implementation with model_hash for audit trail.
"""

import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np


def model_hash(path: Union[str, Path]) -> str:
    """
    SHA-256 hash of model file or serialized weights for audit trail.

    Args:
        path: Path to model file (.onnx, .pt, .pth, .pkl, .pickle)

    Returns:
        Hex digest of file contents
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


class SurrogateModelBase(ABC):
    """Base for surrogate models with predict(spec), model_hash(), optional validate_against_physics()."""

    def __init__(self, path: Path, param_names: Optional[List[str]] = None):
        self.path = Path(path)
        self.param_names = param_names or []
        self._hash: Optional[str] = None

    def model_hash(self) -> str:
        """SHA-256 hash of model file for audit trail."""
        if self._hash is None:
            self._hash = model_hash(self.path)
        return self._hash

    def predict(
        self,
        spec: Union[Dict[str, Any], "ReactorSpecification", np.ndarray],
    ) -> Union[float, np.ndarray]:
        """
        Predict output from reactor spec or param dict.

        Args:
            spec: ReactorSpecification, dict (model_dump or param->value), or feature array

        Returns:
            Predicted value(s)
        """
        x = self._spec_to_features(spec)
        return self._predict_array(x)

    @abstractmethod
    def _predict_array(self, x: np.ndarray) -> Union[float, np.ndarray]:
        """Predict from feature array. Subclasses implement."""
        pass

    def _spec_to_features(
        self,
        spec: Union[Dict[str, Any], "ReactorSpecification", np.ndarray],
    ) -> np.ndarray:
        """Convert spec to feature vector using param_names."""
        if isinstance(spec, np.ndarray):
            return np.atleast_2d(spec)
        if hasattr(spec, "model_dump"):
            d = spec.model_dump()
        elif isinstance(spec, dict):
            d = spec
        else:
            raise TypeError(f"Expected dict, ReactorSpecification, or ndarray, got {type(spec)}")
        # Handle nested parameters
        params = d.get("parameters", d) if "parameters" in d else d
        vals = []
        for name in self.param_names:
            if name in params:
                vals.append(float(params[name]))
            else:
                raise ValueError(f"Missing parameter {name} for surrogate prediction")
        return np.array([vals])

    def validate_against_physics(
        self, spec: Any, reference: float, tolerance: float = 0.1
    ) -> bool:
        """
        Optional: Compare prediction to reference physics result.

        Returns True if |pred - ref| / max(|ref|, 1e-10) <= tolerance.
        """
        pred = self.predict(spec)
        if isinstance(pred, np.ndarray):
            pred = float(pred.flat[0])
        denom = max(abs(reference), 1e-10)
        return abs(float(pred) - reference) / denom <= tolerance


# Optional ONNX
try:
    import onnxruntime as ort

    _ONNX_AVAILABLE = True
except ImportError:
    _ONNX_AVAILABLE = False
    ort = None  # type: ignore


class ONNXSurrogate(SurrogateModelBase):
    """Surrogate loaded from ONNX file. Requires onnxruntime (smrforge_pro[ai] extra)."""

    def __init__(
        self,
        path: Path,
        param_names: Optional[List[str]] = None,
        input_name: Optional[str] = None,
        output_name: Optional[str] = None,
    ):
        if not _ONNX_AVAILABLE:
            raise ImportError(
                "ONNX surrogate requires onnxruntime. pip install onnxruntime or smrforge_pro[ai]"
            )
        super().__init__(path, param_names)
        self.session = ort.InferenceSession(
            str(path), providers=["CPUExecutionProvider"]
        )
        inames = [i.name for i in self.session.get_inputs()]
        onames = [o.name for o in self.session.get_outputs()]
        self.input_name = input_name or (inames[0] if inames else "input")
        self.output_name = output_name or (onames[0] if onames else "output")

    def _predict_array(self, x: np.ndarray) -> Union[float, np.ndarray]:
        x = np.asarray(x, dtype=np.float32)
        if x.ndim == 1:
            x = x.reshape(1, -1)
        out = self.session.run(
            [self.output_name],
            {self.input_name: x},
        )[0]
        if out.size == 1:
            return float(out.flat[0])
        return out


# TorchScript
try:
    import torch

    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False
    torch = None  # type: ignore


class TorchScriptSurrogate(SurrogateModelBase):
    """Surrogate loaded from TorchScript (.pt/.pth). Requires torch."""

    def __init__(self, path: Path, param_names: Optional[List[str]] = None):
        if not _TORCH_AVAILABLE:
            raise ImportError("TorchScript surrogate requires torch. pip install torch")
        super().__init__(path, param_names)
        self.model = torch.jit.load(str(path))
        self.model.eval()

    def _predict_array(self, x: np.ndarray) -> Union[float, np.ndarray]:
        x = np.asarray(x, dtype=np.float32)
        if x.ndim == 1:
            x = x.reshape(1, -1)
        t = torch.from_numpy(x)
        with torch.no_grad():
            out = self.model(t)
        arr = out.numpy()
        if arr.size == 1:
            return float(arr.flat[0])
        return arr


# Sklearn (pickle)
class SklearnSurrogate(SurrogateModelBase):
    """Surrogate loaded from sklearn/pickle (.pkl/.pickle)."""

    def __init__(self, path: Path, param_names: Optional[List[str]] = None):
        super().__init__(path, param_names)
        import pickle

        with open(path, "rb") as f:
            self.model = pickle.load(f)

    def _predict_array(self, x: np.ndarray) -> Union[float, np.ndarray]:
        x = np.asarray(x)
        if x.ndim == 1:
            x = x.reshape(1, -1)
        out = self.model.predict(x)
        if hasattr(out, "flat") and out.size == 1:
            return float(out.flat[0])
        return out


def load_surrogate_from_path(
    path: Union[str, Path],
    param_names: Optional[List[str]] = None,
    **kwargs: Any,
) -> SurrogateModelBase:
    """
    Load surrogate from file path. Detect format by suffix.

    Supported:
        .onnx -> ONNXSurrogate (onnxruntime, optional)
        .pt, .pth -> TorchScriptSurrogate (torch)
        .pkl, .pickle -> SklearnSurrogate (pickle)

    Args:
        path: Path to model file
        param_names: Ordered list of parameter names for spec->feature mapping
        **kwargs: Passed to surrogate constructor (e.g., input_name for ONNX)

    Returns:
        SurrogateModel-like object with predict(spec), model_hash()
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".onnx":
        return ONNXSurrogate(path, param_names=param_names, **kwargs)
    if suffix in (".pt", ".pth"):
        return TorchScriptSurrogate(path, param_names=param_names)
    if suffix in (".pkl", ".pickle"):
        return SklearnSurrogate(path, param_names=param_names)

    raise ValueError(
        f"Unknown model format: {suffix}. Use .onnx, .pt, .pth, .pkl, or .pickle"
    )
