"""Script to split cli.py into package structure. Run from project root."""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
CLI_SRC = ROOT / "smrforge" / "cli.py"
CLI_DIR = ROOT / "smrforge" / "cli"
COMMANDS_DIR = CLI_DIR / "commands"

# Module to function mapping (function: module_file)
MODULE_MAP = {
    "serve_dashboard": "serve",
    "reactor_create": "reactor",
    "reactor_analyze": "reactor",
    "_reactor_analyze_batch": "reactor",
    "reactor_list": "reactor",
    "reactor_compare": "reactor",
    "_load_reactor_from_args": "reactor",
    "template_create": "reactor",
    "template_modify": "reactor",
    "template_validate": "reactor",
    "data_setup": "data",
    "data_download": "data",
    "data_validate": "data",
    "data_interpolate": "data",
    "data_shield": "data",
    "workflow_run": "workflow",
    "batch_keff_run": "workflow",
    "workflow_design_point": "workflow",
    "workflow_safety_report": "workflow",
    "workflow_doe": "workflow",
    "workflow_pareto": "workflow",
    "workflow_optimize": "workflow",
    "workflow_uq": "workflow",
    "_write_design_study_html": "workflow",
    "workflow_design_study": "workflow",
    "workflow_variant": "workflow",
    "workflow_sensitivity": "workflow",
    "workflow_sobol": "workflow",
    "workflow_scenario": "workflow",
    "workflow_atlas": "workflow",
    "workflow_surrogate": "workflow",
    "workflow_ml_export": "workflow",
    "workflow_requirements_to_constraints": "workflow",
    "convert_export": "convert",
    "visualize_geometry": "visualize",
    "visualize_tally": "visualize",
    "visualize_flux": "visualize",
    "burnup_visualize": "visualize",
    "validate_run": "validate",
    "validate_benchmark": "validate",
    "validate_design": "validate",
    "report_design": "report",
    "report_validation": "report",
    "burnup_run": "burnup",
    "decay_heat_calculate": "decay",
    "transient_run": "transient",
    "thermal_lumped": "thermal",
    "config_show": "config",
    "config_set": "config",
    "config_init": "config",
    "github_actions_status": "github",
    "github_actions_enable": "github",
    "github_actions_disable": "github",
    "github_actions_list": "github",
    "github_actions_set": "github",
    "github_actions_configure": "github",
    "_github_repo_root": "github",
    "_github_paths": "github",
    "_read_workflows_enabled": "github",
    "_read_workflows_config": "github",
    "_write_workflows_config": "github",
    "sweep_run": "sweep",
    "shell_interactive": "shell",
}

# GITHUB_ACTIONS_FEATURES constant (lines 3067-3118)
GITHUB_CONST_START = 3066
GITHUB_CONST_END = 3118


def get_utils_imports():
    return '''"""
SMRForge CLI command handlers.
"""

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
)
'''


def main():
    content = CLI_SRC.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)

    # Ensure dirs exist
    COMMANDS_DIR.mkdir(parents=True, exist_ok=True)

    # Extract by regex for function defs
    func_pattern = re.compile(r"^def ([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")
    func_starts = {}
    for i, line in enumerate(lines):
        m = func_pattern.match(line)
        if m:
            func_starts[m.group(1)] = i  # 0-based

    # Build module content
    modules = {}
    for func_name, mod_file in MODULE_MAP.items():
        if func_name not in func_starts:
            print(f"Warning: {func_name} not found")
            continue
        start = func_starts[func_name]
        # Find end: next def at same indent (0) or end of file
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if lines[j].startswith("def ") and not lines[j].startswith(" "):
                end = j
                break
        mod_content = "".join(lines[start:end])
        if mod_file not in modules:
            modules[mod_file] = []
        modules[mod_file].append((start, mod_content))

    for mod_file, chunks in modules.items():
        chunks.sort(key=lambda x: x[0])
        body = "\n\n".join(c[1] for c in chunks)
        # Add imports
        imports = get_utils_imports()
        if mod_file == "workflow":
            imports += "\nfrom .reactor import _load_reactor_from_args\n"
        if mod_file == "github":
            # Add GITHUB_ACTIONS_FEATURES and yaml, Table
            gh_const = "".join(lines[GITHUB_CONST_START : GITHUB_CONST_END + 1])
            imports += "\n" + gh_const + "\n"
        full = imports + "\n" + body
        out_path = COMMANDS_DIR / f"{mod_file}.py"
        out_path.write_text(full, encoding="utf-8")
        print(f"Wrote {out_path}")

    print("Done. Run manually to add module-specific imports (yaml, Table, etc.)")


if __name__ == "__main__":
    main()
