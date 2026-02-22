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
from ..workflows.surrogate import fit_surrogate


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
    "get_surrogate",
    "list_surrogates",
    "register_hook",
    "register_surrogate",
    "run_hooks",
]
