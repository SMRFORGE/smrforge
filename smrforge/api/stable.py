"""
Stable public API surface for SMRForge.

Re-exports stable symbols for integration partners and AI/automation.
Versioned; see docs/API_STABILITY.md for deprecation policy.

Heavy modules (neutronics, burnup) are loaded lazily on first access.
"""

# Lightweight imports (always loaded)
from ..validation.models import CrossSectionData, ReactorSpecification, SolverOptions
from ..validation.regulatory_traceability import (
    CalculationAuditTrail,
    create_audit_trail,
)
from ..workflows.ml_export import export_ml_dataset
from ..workflows.plugin_registry import (
    get_surrogate,
    list_surrogates,
    register_hook,
    register_surrogate,
    run_hooks,
)
from ..workflows.surrogate import fit_surrogate, surrogate_from_sweep_results


def __getattr__(name: str):
    """Lazy load neutronics and burnup only when first accessed."""
    if name == "MultiGroupDiffusion":
        try:
            from ..neutronics.solver import MultiGroupDiffusion as _cls

            globals()["MultiGroupDiffusion"] = _cls
            return _cls
        except ImportError:
            globals()["MultiGroupDiffusion"] = None
            return None  # type: ignore
    if name == "BurnupSolver":
        try:
            from ..burnup.solver import BurnupSolver as _cls

            globals()["BurnupSolver"] = _cls
            return _cls
        except ImportError:
            globals()["BurnupSolver"] = None
            return None  # type: ignore
    if name == "load_surrogate_from_path":
        from ..ai.surrogate import load_surrogate_from_path
        return load_surrogate_from_path
    if name == "record_ai_model":
        from ..ai.audit import record_ai_model
        return record_ai_model
    if name == "fit_surrogate_with_audit":
        from ..ai.surrogate import fit_surrogate_with_audit
        return fit_surrogate_with_audit
    if name == "generate_validation_report":
        from ..ai.validation import generate_validation_report
        return generate_validation_report
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BurnupSolver",
    "export_ml_dataset",
    "CalculationAuditTrail",
    "CrossSectionData",
    "MultiGroupDiffusion",
    "ReactorSpecification",
    "SolverOptions",
    "create_audit_trail",
    "fit_surrogate",
    "surrogate_from_sweep_results",
    "fit_surrogate_with_audit",
    "load_surrogate_from_path",
    "record_ai_model",
    "generate_validation_report",
    "get_surrogate",
    "list_surrogates",
    "register_hook",
    "register_surrogate",
    "run_hooks",
]
