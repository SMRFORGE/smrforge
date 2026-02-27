"""
SMRForge CLI

Command-line interface for SMRForge, including dashboard launcher.
All features remain available via Python API and CLI.
"""

import sys

from smrforge.cli.common import (
    _GLYPH_ERROR,
    _GLYPH_INFO,
    _GLYPH_SUCCESS,
    _GLYPH_WARNING,
    _RICH_AVAILABLE,
    _YAML_AVAILABLE,
    _parse_heat_source_safe,
    _print_error,
    _print_info,
    _print_success,
    _print_warning,
    _save_workflow_plot,
    _supports_unicode,
    _to_jsonable,
    console,
    yaml,
)
from smrforge.cli.parser import build_parser

# Command handlers - re-export for backward compatibility
from smrforge.cli.commands.burnup import burnup_run, burnup_visualize
from smrforge.cli.commands.config import config_init, config_set, config_show
from smrforge.cli.commands.data import (
    data_download,
    data_interpolate,
    data_setup,
    data_shield,
    data_validate,
)
from smrforge.cli.commands.decay import decay_heat_calculate
from smrforge.cli.commands.github import (
    GITHUB_ACTIONS_FEATURES,
    _github_paths,
    _github_repo_root,
    _read_workflows_config,
    _read_workflows_enabled,
    _write_workflows_config,
    github_actions_configure,
    github_actions_disable,
    github_actions_enable,
    github_actions_list,
    github_actions_set,
    github_actions_status,
)
from smrforge.cli.commands.reactor import (
    _reactor_analyze_batch,
    reactor_analyze,
    reactor_compare,
    reactor_create,
    reactor_list,
)
from smrforge.cli.commands.serve import serve_dashboard
from smrforge.cli.commands.shell import shell_interactive
from smrforge.cli.commands.template import (
    template_create,
    template_modify,
    template_validate,
)
from smrforge.cli.commands.transient import thermal_lumped, transient_run
from smrforge.cli.commands.validation import (
    report_design,
    validate_benchmark,
    validate_design,
    validate_run,
)
from smrforge.cli.commands.visualize import visualize_flux, visualize_geometry
from smrforge.cli.commands.workflow import (
    _load_reactor_from_args,
    _write_design_study_html,
    batch_keff_run,
    sweep_run,
    workflow_atlas,
    workflow_benchmark,
    workflow_code_verify,
    workflow_design_point,
    workflow_design_study,
    workflow_doe,
    workflow_multi_optimize,
    workflow_optimize,
    workflow_pareto,
    workflow_regulatory_package,
    workflow_requirements_to_constraints,
    workflow_run,
    workflow_safety_report,
    workflow_scenario,
    workflow_sensitivity,
    workflow_sobol,
    workflow_surrogate,
    workflow_surrogate_validate,
    workflow_variant,
    workflow_uq,
)


def main():
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()  # pragma: no cover
        sys.exit(0)  # pragma: no cover

    # Handle commands - func is set via set_defaults on each subparser
    if hasattr(args, "func"):
        args.func(args)
    else:  # pragma: no cover
        # Command without handler - show help
        parser.print_help()  # pragma: no cover
        sys.exit(0)  # pragma: no cover


__all__ = [
    "main",
    # Common
    "_RICH_AVAILABLE",
    "_YAML_AVAILABLE",
    "console",
    "_parse_heat_source_safe",
    "_supports_unicode",
    "_to_jsonable",
    "_save_workflow_plot",
    "_print_success",
    "_print_error",
    "_print_info",
    "_print_warning",
    "_GLYPH_SUCCESS",
    "_GLYPH_ERROR",
    "_GLYPH_INFO",
    "_GLYPH_WARNING",
    "yaml",
    # Handlers
    "serve_dashboard",
    "reactor_create",
    "reactor_analyze",
    "_reactor_analyze_batch",
    "reactor_list",
    "reactor_compare",
    "data_setup",
    "data_download",
    "data_validate",
    "data_interpolate",
    "data_shield",
    "burnup_run",
    "burnup_visualize",
    "validate_run",
    "report_design",
    "validate_benchmark",
    "validate_design",
    "visualize_geometry",
    "visualize_flux",
    "decay_heat_calculate",
    "_github_repo_root",
    "_github_paths",
    "_read_workflows_enabled",
    "_read_workflows_config",
    "_write_workflows_config",
    "github_actions_status",
    "github_actions_enable",
    "github_actions_disable",
    "github_actions_list",
    "github_actions_set",
    "github_actions_configure",
    "GITHUB_ACTIONS_FEATURES",
    "config_show",
    "config_set",
    "config_init",
    "shell_interactive",
    "workflow_run",
    "sweep_run",
    "batch_keff_run",
    "workflow_design_point",
    "workflow_safety_report",
    "_load_reactor_from_args",
    "workflow_doe",
    "workflow_pareto",
    "workflow_optimize",
    "workflow_uq",
    "_write_design_study_html",
    "workflow_design_study",
    "workflow_variant",
    "workflow_sensitivity",
    "workflow_sobol",
    "workflow_scenario",
    "workflow_atlas",
    "workflow_surrogate",
    "workflow_surrogate_validate",
    "workflow_requirements_to_constraints",
    "template_create",
    "template_modify",
    "template_validate",
    "transient_run",
    "thermal_lumped",
]
