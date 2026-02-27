"""
SMRForge CLI command handlers.

Each module implements handlers for a group of related CLI commands.
"""

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

__all__ = [
    "burnup_run",
    "burnup_visualize",
    "config_init",
    "config_set",
    "config_show",
    "data_download",
    "data_interpolate",
    "data_setup",
    "data_shield",
    "data_validate",
    "decay_heat_calculate",
    "GITHUB_ACTIONS_FEATURES",
    "_github_paths",
    "_github_repo_root",
    "_read_workflows_config",
    "_read_workflows_enabled",
    "_write_workflows_config",
    "github_actions_configure",
    "github_actions_disable",
    "github_actions_enable",
    "github_actions_list",
    "github_actions_set",
    "github_actions_status",
    "shell_interactive",
    "template_create",
    "template_modify",
    "template_validate",
    "thermal_lumped",
    "transient_run",
    "report_design",
    "validate_benchmark",
    "validate_design",
    "validate_run",
    "visualize_flux",
    "visualize_geometry",
]
