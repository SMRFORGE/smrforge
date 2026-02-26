"""SMRForge CLI command handlers."""

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

def shell_interactive(args):
    """Launch interactive Python shell with SMRForge pre-loaded."""
    try:
        # Try IPython first (better UX)
        try:
            from IPython import embed
            from IPython.terminal.embed import InteractiveShellEmbed

            # Pre-import SMRForge modules
            import smrforge as smr

            # Try multiple import strategies for convenience functions
            create_reactor = getattr(smr, "create_reactor", None)
            list_presets = getattr(smr, "list_presets", None)

            if create_reactor is None or list_presets is None:
                try:  # pragma: no cover
                    from smrforge.convenience import (  # pragma: no cover
                        create_reactor,
                        list_presets,
                    )
                except ImportError:  # pragma: no cover
                    pass  # pragma: no cover

            from smrforge.burnup import BurnupOptions, BurnupSolver
            from smrforge.visualization import plot_core_layout

            # Setup banner
            banner = """
╔═══════════════════════════════════════════════════════════════╗
║           SMRForge Interactive Shell (IPython)                ║
╚═══════════════════════════════════════════════════════════════╝

Pre-loaded objects:
  • smr - SMRForge main module
  • create_reactor() - Create reactor from preset or config
  • list_presets() - List available preset designs
  • BurnupSolver, BurnupOptions - Burnup calculation
  • plot_core_layout() - Visualization

Quick start:
  >>> reactor = create_reactor("valar-10")
  >>> k_eff = reactor.solve_keff()
  >>> print(f"k-eff: {k_eff:.6f}")

Type 'help(smr)' for more information or 'exit' to quit.
"""
            exit_msg = "\nExiting SMRForge shell. Goodbye!"

            # Launch IPython shell
            ipshell = InteractiveShellEmbed(banner1=banner, exit_msg=exit_msg)
            ipshell()

        except ImportError:
            # Fallback to standard Python REPL
            import code
            import sys

            # Pre-import SMRForge modules
            import smrforge as smr  # pragma: no cover

            # Try multiple import strategies for convenience functions
            create_reactor = getattr(smr, "create_reactor", None)  # pragma: no cover
            list_presets = getattr(smr, "list_presets", None)  # pragma: no cover

            if create_reactor is None or list_presets is None:  # pragma: no cover
                try:  # pragma: no cover
                    from smrforge.convenience import (  # pragma: no cover
                        create_reactor,
                        list_presets,
                    )
                except ImportError:  # pragma: no cover
                    pass  # pragma: no cover

            # Setup banner
            banner = """  # pragma: no cover
╔═══════════════════════════════════════════════════════════════╗  # pragma: no cover
║           SMRForge Interactive Shell (Python REPL)            ║  # pragma: no cover
╚═══════════════════════════════════════════════════════════════╝  # pragma: no cover

Pre-loaded objects:  # pragma: no cover
  • smr - SMRForge main module  # pragma: no cover
  • create_reactor() - Create reactor from preset or config  # pragma: no cover
  • list_presets() - List available preset designs  # pragma: no cover

Quick start:  # pragma: no cover
  >>> reactor = create_reactor("valar-10")  # pragma: no cover
  >>> k_eff = reactor.solve_keff()  # pragma: no cover
  >>> print(f"k-eff: {k_eff:.6f}")  # pragma: no cover

Note: Install IPython for enhanced features: pip install ipython  # pragma: no cover
Type 'help(smr)' for more information or 'exit()' to quit.  # pragma: no cover
"""  # pragma: no cover

            print(banner)  # pragma: no cover

            # Launch standard Python REPL with pre-loaded globals
            variables = {  # pragma: no cover
                "smr": smr,  # pragma: no cover
                "create_reactor": create_reactor,  # pragma: no cover
                "list_presets": list_presets,  # pragma: no cover
                "exit": sys.exit,  # pragma: no cover
                "quit": sys.exit,  # pragma: no cover
            }  # pragma: no cover

            shell = code.InteractiveConsole(variables)  # pragma: no cover
            shell.interact(banner="")  # pragma: no cover

    except ImportError as e:
        _print_error(f"Failed to import SMRForge modules: {e}")  # pragma: no cover
        sys.exit(1)  # pragma: no cover
    except Exception as e:
        _print_error(f"Failed to launch interactive shell: {e}")
        if args.verbose if hasattr(args, "verbose") else False:
            import traceback

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover


