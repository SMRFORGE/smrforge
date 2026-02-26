"""Extract CLI command modules from monolith. Run from project root."""
from pathlib import Path

ROOT = Path(__file__).parent.parent
CLI_SRC = ROOT / "smrforge" / "cli.py"
COMMANDS_DIR = ROOT / "smrforge" / "cli" / "commands"

# (module_file, [func_names]) - order matters for dependencies
MODULES = [
    ("serve", ["serve_dashboard"]),
    (
        "reactor",
        [
            "reactor_create",
            "reactor_analyze",
            "_reactor_analyze_batch",
            "reactor_list",
            "reactor_compare",
            "_load_reactor_from_args",
            "template_create",
            "template_modify",
            "template_validate",
        ],
    ),
    ("data", ["data_setup", "data_download", "data_validate", "data_interpolate", "data_shield"]),
    (
        "workflow",
        [
            "workflow_run",
            "batch_keff_run",
            "workflow_design_point",
            "workflow_safety_report",
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
            "workflow_ml_export",
            "workflow_requirements_to_constraints",
        ],
    ),
    ("convert", ["convert_export"]),
    (
        "visualize",
        ["visualize_geometry", "visualize_tally", "visualize_flux", "burnup_visualize"],
    ),
    ("validate", ["validate_run", "validate_benchmark", "validate_design"]),
    ("report", ["report_design", "report_validation"]),
    ("burnup", ["burnup_run"]),
    ("decay", ["decay_heat_calculate"]),
    ("transient", ["transient_run"]),
    ("thermal", ["thermal_lumped"]),
    ("config", ["config_show", "config_set", "config_init"]),
    (
        "github",
        [
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
        ],
    ),
    ("sweep", ["sweep_run"]),
    ("shell", ["shell_interactive"]),
]

BASE_IMPORTS = '''"""SMRForge CLI command handlers."""

import json
import sys
from pathlib import Path

from ..utils import (
    _GLYPH_ERROR,
    _GLYPH_SUCCESS,
    _RICH_AVAILABLE,
    _YAML_AVAILABLE,
    _print_error,
    _print_info,
    _print_success,
    _print_warning,
    _save_workflow_plot,
    _to_jsonable,
    console,
    rprint,
    yaml,
)
try:
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    Panel = None  # type: ignore
    Table = None  # type: ignore
'''

# workflow needs _load_reactor_from_args from reactor
WORKFLOW_IMPORT = "from .reactor import _load_reactor_from_args\n"


def find_function_bounds(lines, func_name):
    """Return (start_idx, end_idx) 0-based. End is exclusive."""
    start = None
    for i, line in enumerate(lines):
        if line.startswith(f"def {func_name}(") or line.startswith(f"def {func_name} "):
            start = i
            break
    if start is None:
        return None, None
    # Find end: next top-level def (column 0)
    end = len(lines)
    for i in range(start + 1, len(lines)):
        stripped = lines[i].lstrip()
        if stripped.startswith("def ") and lines[i][0] != " " and lines[i][0] != "\t":
            end = i
            break
    return start, end


def extract_function(lines, start, end, func_name):
    """Extract function, handling nested defs (include them)."""
    out = []
    for i in range(start, end):
        out.append(lines[i])
    return "".join(out)


def main():
    content = CLI_SRC.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)

    # GITHUB_ACTIONS_FEATURES constant
    gh_start, gh_end = 3066, 3119  # 1-based to 0-based, inclusive
    gh_const = "".join(lines[gh_start:gh_end])

    COMMANDS_DIR.mkdir(parents=True, exist_ok=True)

    for mod_name, func_names in MODULES:
        chunks = []
        for fn in func_names:
            s, e = find_function_bounds(lines, fn)
            if s is not None:
                chunks.append(extract_function(lines, s, e, fn))
            else:
                print(f"  Warning: {fn} not found")

        body = "\n\n".join(chunks)

        imports = BASE_IMPORTS
        if mod_name == "workflow":
            imports += WORKFLOW_IMPORT
        if mod_name == "github":
            imports += "\n" + gh_const + "\n"

        out_path = COMMANDS_DIR / f"{mod_name}.py"
        out_path.write_text(imports + "\n" + body, encoding="utf-8")
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
