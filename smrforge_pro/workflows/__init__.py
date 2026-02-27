"""
Pro workflows: surrogate, ml_export, plugin_registry, code_verification, regulatory_package, benchmark_reproduction, multi_objective_optimization.
"""

from .surrogate_validation import generate_surrogate_validation_report
from .code_verification import run_code_verification
from .regulatory_package import generate_regulatory_package
from .benchmark_reproduction import reproduce_benchmark
from .multi_objective_optimization import multi_objective_optimize
from .surrogate import (
    SurrogateModel,
    fit_surrogate,
    physics_informed_surrogate_from_sweep,
    surrogate_from_sweep_results,
)
from .ml_export import export_ml_dataset
from .plugin_registry import (
    get_surrogate,
    list_surrogates,
    register_surrogate,
    unregister_surrogate,
)

__all__ = [
    "SurrogateModel",
    "fit_surrogate",
    "generate_surrogate_validation_report",
    "physics_informed_surrogate_from_sweep",
    "surrogate_from_sweep_results",
    "export_ml_dataset",
    "get_surrogate",
    "list_surrogates",
    "register_surrogate",
    "unregister_surrogate",
    "run_code_verification",
    "generate_regulatory_package",
    "reproduce_benchmark",
    "multi_objective_optimize",
]
