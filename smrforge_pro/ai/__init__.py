"""
SMRForge Pro AI module - surrogate models, audit trail, validation reports.
"""

from .audit import record_ai_model
from .surrogates import (
    SklearnSurrogate,
    load_surrogate_from_path,
    model_hash,
)
from .validation_report import (
    SurrogateValidationReport,
    generate_validation_report,
)

try:
    from .surrogates import ONNXSurrogate, TorchScriptSurrogate
except ImportError:
    ONNXSurrogate = None  # type: ignore
    TorchScriptSurrogate = None  # type: ignore

__all__ = [
    "record_ai_model",
    "load_surrogate_from_path",
    "model_hash",
    "SklearnSurrogate",
    "ONNXSurrogate",
    "TorchScriptSurrogate",
    "SurrogateValidationReport",
    "generate_validation_report",
]
