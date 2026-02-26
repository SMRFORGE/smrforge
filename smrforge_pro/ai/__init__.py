"""
SMRForge Pro AI module - surrogate models, audit trail, validation reports, NL design.
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

try:
    from .nl_design import design_from_nl, parse_nl_design
except ImportError:
    design_from_nl = None  # type: ignore
    parse_nl_design = None  # type: ignore

try:
    from .physics_informed import physics_informed_surrogate_from_sweep
except ImportError:
    physics_informed_surrogate_from_sweep = None  # type: ignore

__all__ = [
    "record_ai_model",
    "load_surrogate_from_path",
    "model_hash",
    "SklearnSurrogate",
    "ONNXSurrogate",
    "TorchScriptSurrogate",
    "SurrogateValidationReport",
    "generate_validation_report",
    "design_from_nl",
    "parse_nl_design",
    "physics_informed_surrogate_from_sweep",
]
