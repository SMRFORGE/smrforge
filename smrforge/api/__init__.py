"""
Public API surface for SMRForge.

Stable symbols for integration partners and AI/automation.
See docs/API_STABILITY.md for deprecation policy.

MultiGroupDiffusion and BurnupSolver are loaded lazily on first access.
"""

from .stable import (
    CalculationAuditTrail,
    CrossSectionData,
    ReactorSpecification,
    SolverOptions,
    create_audit_trail,
    export_ml_dataset,
    fit_surrogate,
    get_surrogate,
    list_surrogates,
    register_hook,
    register_surrogate,
    run_hooks,
)


def __getattr__(name: str):
    """Lazy load neutronics and burnup only when first accessed."""
    if name in ("BurnupSolver", "MultiGroupDiffusion"):
        from . import stable

        return getattr(stable, name)
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
