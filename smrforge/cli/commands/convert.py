"""SMRForge CLI command handlers."""

import json
import sys
from pathlib import Path

from ..utils import (
    _GLYPH_ERROR,
    _GLYPH_SUCCESS,
    _RICH_AVAILABLE,
    _YAML_AVAILABLE,
    _exit_error,
    _print_error,
    _print_info,
    _print_success,
    _print_warning,
    _save_workflow_plot,
    _to_jsonable,
    Panel,
    Table,
    console,
    rprint,
    yaml,
)


def convert_export(args):
    """Export reactor to Serpent, OpenMC, or MCNP. Pro tier for Serpent/MCNP full export."""
    try:
        from smrforge.convenience import create_reactor
    except ImportError:
        _exit_error("SMRForge convenience module not available")
    reactor_spec = getattr(args, "reactor", None)
    output = getattr(args, "output", None)
    fmt = getattr(args, "format", "").lower()
    if not reactor_spec or not output:
        _exit_error("--reactor and --output required")
        return  # no fall-through when sys.exit is mocked in tests
    try:
        if Path(reactor_spec).exists():
            import json

            with open(reactor_spec) as f:
                data = json.load(f)
            reactor = create_reactor(**data)
        else:
            reactor = create_reactor(str(reactor_spec))
    except Exception as e:
        _exit_error(f"Failed to create reactor: {e}")
    output = Path(output)
    try:
        if fmt == "serpent":
            from smrforge.io.converters import SerpentConverter

            if output.suffix not in (".serp", ".inp", ""):
                output = output.with_suffix(".serp")
            SerpentConverter.export_reactor(reactor, output)
        elif fmt == "openmc":
            from smrforge.io.converters import OpenMCConverter

            output.mkdir(parents=True, exist_ok=True)
            OpenMCConverter.export_reactor(
                reactor,
                output,
                particles=getattr(args, "particles", 1000),
                batches=getattr(args, "batches", 20),
            )
        elif fmt == "mcnp":
            from smrforge.io.converters import MCNPConverter

            if output.suffix not in (".mcnp", ".inp", ""):
                output = output.with_suffix(".mcnp")
            MCNPConverter.export_reactor(reactor, output)
        else:
            _exit_error(f"Unsupported format: {fmt}. Use serpent, openmc, or mcnp")

        # Rich summary (with plain fallback)
        reactor_name = (
            reactor.spec.name
            if hasattr(reactor, "spec") and hasattr(reactor.spec, "name")
            else str(reactor_spec)
        )
        if _RICH_AVAILABLE and Panel is not None and console is not None:
            summary = f"[cyan]{reactor_name}[/cyan] → [green]{fmt}[/green] → {output}"
            console.print(Panel(summary, title="Export complete", border_style="green"))
        else:
            print(f"Export: {reactor_name} → {fmt} → {output}")
        _print_success(f"Exported to {output}")
    except Exception as e:
        _exit_error(f"Export failed: {e}")
