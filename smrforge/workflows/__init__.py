"""
Workflow utilities for parameter sweeps, sensitivity analysis, and batch processing.
"""

from .parameter_sweep import ParameterSweep, SweepConfig, SweepResult
from .doe import (
    full_factorial,
    latin_hypercube,
    random_space_filling,
    sobol_space_filling,
)
from .sensitivity import SensitivityRanking, one_at_a_time_from_sweep, morris_screening
from .sobol_indices import sobol_indices_from_samples, sobol_indices_from_sweep_results
from .pareto_report import pareto_knee_point, pareto_summary_report
from .audit_log import RunRecord, append_run
from .surrogate import SurrogateModel, fit_surrogate, surrogate_from_sweep_results
from .scenario_design import ScenarioResult, run_scenario_design, scenario_comparison_report
from .atlas import AtlasEntry, build_atlas, filter_atlas

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
    "surrogate_from_sweep_results",
    "ScenarioResult",
    "run_scenario_design",
    "scenario_comparison_report",
    "AtlasEntry",
    "build_atlas",
    "filter_atlas",
]
