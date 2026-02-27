"""
Workflow utilities for parameter sweeps, sensitivity analysis, and batch processing.
"""

from .atlas import AtlasEntry, build_atlas, filter_atlas
from .audit_log import RunRecord, append_run
from .doe import (
    full_factorial,
    latin_hypercube,
    random_space_filling,
    sobol_space_filling,
)
from .parameter_sweep import ParameterSweep, SweepConfig, SweepResult
from .pareto_report import pareto_knee_point, pareto_summary_report
from .scenario_design import (
    ScenarioResult,
    run_scenario_design,
    scenario_comparison_report,
)
from .sensitivity import SensitivityRanking, morris_screening, one_at_a_time_from_sweep
from .sobol_indices import sobol_indices_from_samples, sobol_indices_from_sweep_results
from .ml_export import export_ml_dataset
from .plugin_registry import (
    clear_hooks,
    get_surrogate,
    list_surrogates,
    register_hook,
    register_surrogate,
    run_hooks,
    unregister_surrogate,
)
from .surrogate import SurrogateModel, fit_surrogate, surrogate_from_sweep_results
from .surrogate_validation import generate_surrogate_validation_report

__all__ = [
    "ParameterSweep",
    "SweepConfig",
    "SweepResult",
    "full_factorial",
    "latin_hypercube",
    "random_space_filling",
    "sobol_space_filling",
    "SensitivityRanking",
    "one_at_a_time_from_sweep",
    "morris_screening",
    "sobol_indices_from_samples",
    "sobol_indices_from_sweep_results",
    "pareto_knee_point",
    "pareto_summary_report",
    "RunRecord",
    "append_run",
    "SurrogateModel",
    "fit_surrogate",
    "generate_surrogate_validation_report",
    "surrogate_from_sweep_results",
    "ScenarioResult",
    "run_scenario_design",
    "scenario_comparison_report",
    "AtlasEntry",
    "build_atlas",
    "filter_atlas",
    "register_surrogate",
    "get_surrogate",
    "list_surrogates",
    "unregister_surrogate",
    "register_hook",
    "run_hooks",
    "clear_hooks",
    "export_ml_dataset",
]
