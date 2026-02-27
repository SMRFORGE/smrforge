"""
SMRForge Pro CLI — export serpent|openmc|mcnp with --reactor and --config options.

Use: smrforge-pro export serpent|openmc|mcnp [options]
Or invoke via: python -m smrforge_pro.cli export ...
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


def _load_reactor(reactor: str, config: Optional[str]) -> object:
    """Load reactor from preset name or config file."""
    from smrforge.convenience import create_reactor

    if config and Path(config).exists():
        with open(config, encoding="utf-8") as f:
            data = json.load(f)
        return create_reactor(**data)
    return create_reactor(name=reactor)


def cmd_export(args: argparse.Namespace) -> int:
    """Export reactor to Serpent, OpenMC, or MCNP format."""
    from smrforge_pro.converters import OpenMCConverter, MCNPConverter, SerpentConverter

    reactor = _load_reactor(args.reactor, getattr(args, "config", None))
    fmt = (args.format or "openmc").lower()

    if fmt == "openmc":
        out = Path(args.output or "openmc_export")
        out.mkdir(parents=True, exist_ok=True)
        OpenMCConverter.export_reactor(reactor, out)
        print(f"Exported to {out}/")
    elif fmt == "serpent":
        out = Path(args.output or "reactor.serp")
        SerpentConverter.export_reactor(reactor, out)
        print(f"Exported to {out}")
    elif fmt == "mcnp":
        out = Path(args.output or "reactor.mcnp")
        MCNPConverter.export_reactor(reactor, out)
        print(f"Exported to {out}")
    else:
        print(f"Unknown format: {fmt}. Use serpent, openmc, or mcnp.", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    """Entry point for smrforge-pro CLI."""
    parser = argparse.ArgumentParser(prog="smrforge-pro", description="SMRForge Pro CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export", help="Export reactor to Serpent, OpenMC, or MCNP")
    export_parser.add_argument(
        "format",
        nargs="?",
        choices=["serpent", "openmc", "mcnp"],
        default="openmc",
        metavar="FORMAT",
        help="Export format: serpent, openmc, or mcnp (default: openmc)",
    )
    export_parser.add_argument("--reactor", "-r", default="valar-10", help="Reactor preset name")
    export_parser.add_argument("--config", "-c", help="Path to reactor config JSON/YAML")
    export_parser.add_argument("--output", "-o", help="Output path (file for serpent/mcnp, dir for openmc)")
    export_parser.set_defaults(func=cmd_export)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
