"""
AI surrogate model wrappers for Bring-Your-Own Surrogate (BYOS).

Provides ONNX, TorchScript, and scikit-learn surrogates for fast reactor
evaluation without re-running physics. Supports offline-first, deterministic
workflows with full audit trail integration.

Requires optional deps: pip install smrforge[ai] for onnxruntime, scikit-learn
is already required. TorchScript requires PyTorch (torch).
"""

import hashlib
import pickle
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.ai.surrogate")

# Optional backends - graceful degradation
_ONNX_AVAILABLE = False
_TORCH_AVAILABLE = False

try:
    import onnxruntime as ort  # noqa: F401
    _ONNX_AVAILABLE = True
except ImportError:
    pass

try:
    import torch  # noqa: F401
    _TORCH_AVAILABLE = True
except ImportError:
    pass


def model_hash(path: Union[str, Path]) -> str:
    """Compute SHA-256 hash of a model file for audit trail."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_surrogate_from_path(
    path: Union[str, Path],
    param_names: Optional[List[str]] = None,
    output_name: str = "output",
) -> "LoadableSurrogate":
    """
    Load a surrogate model from file path (BYOS).

    Supports: .onnx, .pt/.pth (TorchScript), .pkl (pickle/SurrogateModel).

    Args:
        path: Path to model file.
        param_names: Parameter names (for metadata).
        output_name: Output label.

    Returns:
        LoadableSurrogate with .predict(X) method.

    Example:
        >>> sur = load_surrogate_from_path("keff_model.onnx", param_names=["x", "y"])
        >>> sur.predict(np.array([[0.1, 0.2]]))
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".onnx":
        return ONNXSurrogate.from_file(path, param_names=param_names, output_name=output_name)
    elif suffix in (".pt", ".pth", ".ptl"):
        return TorchScriptSurrogate.from_file(path, param_names=param_names, output_name=output_name)
    elif suffix in (".pkl", ".pickle"):
        obj = pickle.loads(path.read_bytes())
        return _wrap_pickle_surrogate(obj, path, param_names, output_name)
    else:
        raise ValueError(
            f"Unsupported model format: {suffix}. Use .onnx, .pt, .pth, or .pkl"
        )


def _wrap_pickle_surrogate(
    obj: Any,
    path: Path,
    param_names: Optional[List[str]],
    output_name: str,
) -> "LoadableSurrogate":
    """Wrap a pickled SurrogateModel or predict-callable as LoadableSurrogate."""
    if hasattr(obj, "predict") and callable(obj.predict):
        pnames = getattr(obj, "param_names", param_names or [])
        oname = getattr(obj, "output_name", output_name)
        return LoadableSurrogate(
            predict_fn=obj.predict,
            method="pickle",
            param_names=pnames,
            output_name=oname,
            n_samples=getattr(obj, "n_samples", 0),
            model_path=str(path),
            config_hash=model_hash(path),
        )
    raise ValueError("Pickled object must have a .predict(X) callable")


class LoadableSurrogate:
    """
    Surrogate loaded from file with predict and metadata for audit.

    Implements the SurrogateModel interface expected by fit_surrogate
    registry integration.
    """

    def __init__(
        self,
        predict_fn: Callable[[np.ndarray], np.ndarray],
        method: str,
        param_names: List[str],
        output_name: str,
        n_samples: int = 0,
        model_path: Optional[str] = None,
        config_hash: Optional[str] = None,
    ):
        self.predict = predict_fn
        self.method = method
        self.param_names = param_names
        self.output_name = output_name
        self.n_samples = n_samples
        self.model_path = model_path
        self.config_hash = config_hash or (model_hash(Path(model_path)) if model_path else None)

    def model_hash(self) -> str:
        """Return hash for audit trail (deterministic)."""
        return self.config_hash or "unknown"


class ONNXSurrogate(LoadableSurrogate):
    """ONNX runtime surrogate. Requires onnxruntime (smrforge[ai])."""

    @classmethod
    def from_file(
        cls,
        path: Path,
        param_names: Optional[List[str]] = None,
        output_name: str = "output",
    ) -> "ONNXSurrogate":
        if not _ONNX_AVAILABLE:
            raise ImportError(
                "onnxruntime required for ONNX surrogates. Install: pip install onnxruntime"
            )
        import onnxruntime as ort

        sess = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        input_name = sess.get_inputs()[0].name
        output_name_onnx = sess.get_outputs()[0].name
        shape = sess.get_inputs()[0].shape
        n_params = 1
        if isinstance(shape, (list, tuple)):
            for dim in shape:
                if isinstance(dim, (int, float)):
                    n_params = int(dim)
                    break
        pnames = param_names or [f"x{i}" for i in range(n_params)]

        def predict(X: np.ndarray) -> np.ndarray:
            X = np.asarray(X, dtype=np.float32)
            if X.ndim == 1:
                X = X.reshape(1, -1)
            out = sess.run([output_name_onnx], {input_name: X})[0]
            return np.asarray(out).ravel()

        return cls(
            predict_fn=predict,
            method="onnx",
            param_names=pnames,
            output_name=output_name,
            model_path=str(path),
            config_hash=model_hash(path),
        )


class TorchScriptSurrogate(LoadableSurrogate):
    """TorchScript surrogate. Requires torch."""

    @classmethod
    def from_file(
        cls,
        path: Path,
        param_names: Optional[List[str]] = None,
        output_name: str = "output",
    ) -> "TorchScriptSurrogate":
        if not _TORCH_AVAILABLE:
            raise ImportError("PyTorch required for TorchScript surrogates. Install: pip install torch")
        import torch as th

        model = th.jit.load(str(path))
        model.eval()

        def predict(X: np.ndarray) -> np.ndarray:
            X = np.asarray(X, dtype=np.float32)
            if X.ndim == 1:
                X = X.reshape(1, -1)
            with th.no_grad():
                t = th.from_numpy(X)
                out = model(t)
            return np.asarray(out.cpu().numpy()).ravel()

        pnames = param_names or ["x0"]
        return cls(
            predict_fn=predict,
            method="torchscript",
            param_names=list(pnames) if isinstance(pnames, (list, tuple)) else [f"x{i}" for i in range(1)],
            output_name=output_name,
            model_path=str(path),
            config_hash=model_hash(path),
        )


class SklearnSurrogateFactory:
    """
    Factory for scikit-learn surrogates (Gaussian Process, etc.).

    Use with register_surrogate("sklearn_gp", SklearnSurrogateFactory("gp")).
    """

    def __init__(self, estimator_type: str = "gp"):
        self.estimator_type = estimator_type

    def __call__(
        self,
        X: np.ndarray,
        y: np.ndarray,
        param_names: Optional[List[str]] = None,
        output_name: str = "output",
        **kwargs: Any,
    ) -> Any:
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import RBF, ConstantKernel

        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float).ravel()
        n_params = X.shape[1]
        param_names = param_names or [f"x{i}" for i in range(n_params)]

        if self.estimator_type == "gp":
            kernel = ConstantKernel(1.0) * RBF(length_scale=1.0)
            gp = GaussianProcessRegressor(kernel=kernel, **kwargs)
            gp.fit(X, y)

            class _SklearnPredict:
                def predict(self, Xnew):
                    return gp.predict(np.asarray(Xnew, dtype=float))

            return _SklearnPredict()
        raise ValueError(f"Unknown sklearn type: {self.estimator_type}")


def register_surrogate_from_path(
    name: str,
    path: Union[str, Path],
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Register a surrogate from file path (BYOS convenience).

    Creates a lazy factory that loads the model when first used.
    Compatible with fit_surrogate(method=name) for inference-only workflows.

    Args:
        name: Registry name (e.g., "my_onnx_model").
        path: Path to .onnx, .pt, or .pkl file.
        metadata: Optional metadata for audit (e.g., validity_envelope).
    """
    from ..workflows.plugin_registry import register_surrogate

    path = Path(path)
    meta = dict(metadata) if metadata else {}

    def factory(
        X: np.ndarray,
        y: np.ndarray,
        param_names: Optional[List[str]] = None,
        output_name: str = "output",
        **kwargs: Any,
    ):
        # Load from path; X,y shape used for param_names if not provided
        pnames = param_names or [f"x{i}" for i in range(X.shape[1] if hasattr(X, "shape") else 1)]
        return load_surrogate_from_path(path, param_names=pnames, output_name=output_name)

    register_surrogate(name, factory)
    logger.info("Registered surrogate %r from %s", name, path)


def fit_surrogate_with_audit(
    X: np.ndarray,
    y: np.ndarray,
    audit_trail: Optional[Any] = None,
    param_names: Optional[List[str]] = None,
    output_name: str = "output",
    method: str = "rbf",
    seed: Optional[int] = None,
    **kwargs: Any,
):
    """
    Fit a surrogate and optionally record to audit trail (convenience).

    Args:
        X: Training inputs.
        y: Training outputs.
        audit_trail: CalculationAuditTrail to append ai_models_used (optional).
        param_names: Parameter names.
        output_name: Output label.
        method: "rbf", "linear", or registered name.
        seed: RNG seed for deterministic fit (for methods that support it).
        **kwargs: Passed to fit_surrogate.

    Returns:
        SurrogateModel from fit_surrogate.
    """
    from ..workflows.surrogate import fit_surrogate

    if seed is not None:
        np.random.seed(seed)
    sur = fit_surrogate(
        X, y,
        param_names=param_names,
        output_name=output_name,
        method=method,
        audit_trail=audit_trail,
        **kwargs,
    )
    return sur
