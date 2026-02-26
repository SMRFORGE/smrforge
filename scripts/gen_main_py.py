"""Generate main.py from cli.py. Run from project root."""
from pathlib import Path

ROOT = Path(__file__).parent.parent
CLI_SRC = ROOT / "smrforge" / "cli.py"
MAIN_OUT = ROOT / "smrforge" / "cli" / "main.py"

IMPORTS = '''"""
SMRForge CLI main entry point.

Parses arguments and delegates to command handlers.
"""

import argparse
import sys
from pathlib import Path

import smrforge

from .commands.burnup import burnup_run
from .commands.config import config_init, config_set, config_show
from .commands.convert import convert_export
from .commands.data import (
    data_download,
    data_interpolate,
    data_setup,
    data_shield,
    data_validate,
)
from .commands.decay import decay_heat_calculate
from .commands.github import (
    GITHUB_ACTIONS_FEATURES,
    github_actions_configure,
    github_actions_disable,
    github_actions_enable,
    github_actions_list,
    github_actions_set,
    github_actions_status,
)
from .commands.react import (
    reactor_analyze,
    reactor_compare,
    reactor_create,
    reactor_list,
    template_create,
    template_modify,
    template_validate,
)
from .commands.report import report_design, report_validation
from .commands.serve import serve_dashboard
from .commands.shell import shell_interactive
from .commands.sweep import sweep_run
from .commands.thermal import thermal_lumped
from .commands.transient import transient_run
from .commands.validate import validate_benchmark, validate_design, validate_run
from .commands.visualize import (
    burnup_visualize,
    visualize_flux,
    visualize_geometry,
    visualize_tally,
)
from .commands.workflow import (
    batch_keff_run,
    workflow_atlas,
    workflow_design_point,
    workflow_design_study,
    workflow_doe,
    workflow_ml_export,
    workflow_optimize,
    workflow_pareto,
    workflow_requirements_to_constraints,
    workflow_run,
    workflow_safety_report,
    workflow_scenario,
    workflow_sensitivity,
    workflow_sobol,
    workflow_surrogate,
    workflow_uq,
    workflow_variant,
)
'''


def main():
    content = CLI_SRC.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)

    # Extract main() body: lines 5671-7097 (0-indexed: 5670 to 7096)
    main_lines = lines[5670:7097]
    main_body = "".join(main_lines)

    # Fix import: react -> reactor
    imports_fixed = IMPORTS.replace("from .commands.react import", "from .commands.reactor import")

    full = imports_fixed + "\n" + main_body
    MAIN_OUT.write_text(full, encoding="utf-8")
    print(f"Wrote {MAIN_OUT}")


if __name__ == "__main__":
    main()
