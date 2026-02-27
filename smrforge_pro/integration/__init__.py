"""
Pro integration with Community tier features.

Provides access to Community solvers, CFD adapters, UQ methods, and workflows
so Pro AI features (nl_design, surrogates, validation) can use them.
"""

from .community_capabilities import (
    get_community_capabilities,
    run_sn_solver,
    run_polynomial_chaos,
    run_quasi_static_transient,
    get_cfd_adapter,
    get_weight_windows_from_importance,
    run_execute_and_document_benchmarks,
    run_reference_physics,
)

__all__ = [
    "get_community_capabilities",
    "run_sn_solver",
    "run_polynomial_chaos",
    "run_quasi_static_transient",
    "get_cfd_adapter",
    "get_weight_windows_from_importance",
    "run_execute_and_document_benchmarks",
    "run_reference_physics",
]
