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

def config_show(args):
    """Show current configuration."""
    try:
        config_dir = Path.home() / ".smrforge"
        config_file = config_dir / "config.yaml"

        if not config_file.exists():
            _print_info("No configuration file found")
            _print_info(f"Configuration file location: {config_file}")
            _print_info(
                "Use 'smrforge config init' to create a default configuration file"
            )
            return

        if not _YAML_AVAILABLE:
            _print_error("PyYAML not available. Install PyYAML: pip install pyyaml")
            sys.exit(1)

        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}

        if args.key:
            # Show specific key
            keys = args.key.split(".")
            value = config
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    _print_error(f"Configuration key not found: {args.key}")
                    sys.exit(1)

            if _RICH_AVAILABLE:
                console.print(f"[cyan]{args.key}[/cyan]: {value}")
            else:
                print(f"{args.key}: {value}")
        else:
            # Show all config
            if _RICH_AVAILABLE:
                table = Table(title="SMRForge Configuration")
                table.add_column("Key", style="cyan")
                table.add_column("Value", style="green")

                def add_config_rows(data, prefix=""):
                    for key, value in data.items():
                        full_key = f"{prefix}.{key}" if prefix else key
                        if isinstance(value, dict):
                            add_config_rows(value, full_key)  # pragma: no cover
                        else:
                            table.add_row(full_key, str(value))

                add_config_rows(config)
                console.print(table)
            else:
                print("\nSMRForge Configuration:")
                print("=" * 60)

                def print_config(data, prefix=""):
                    for key, value in data.items():
                        full_key = f"{prefix}.{key}" if prefix else key
                        if isinstance(value, dict):
                            print_config(value, full_key)
                        else:
                            print(f"{full_key}: {value}")

                print_config(config)
                print("=" * 60)

            _print_info(f"\nConfiguration file: {config_file}")

    except Exception as e:
        _print_error(f"Failed to show configuration: {e}")
        if args.verbose if hasattr(args, "verbose") else False:
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)




def config_set(args):
    """Set configuration value."""
    try:
        if not _YAML_AVAILABLE:
            _print_error("PyYAML not available. Install PyYAML: pip install pyyaml")
            sys.exit(1)
            return  # ensure we don't fall through when exit is mocked

        config_dir = Path.home() / ".smrforge"
        config_file = config_dir / "config.yaml"

        # Load existing config or create new
        if config_file.exists():
            with open(config_file, "r") as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}
            config_dir.mkdir(parents=True, exist_ok=True)

        # Parse key and set value
        keys = args.key.split(".")
        value = args.value

        # Convert value to appropriate type
        try:
            # Try to convert to number
            if "." in value:
                value = float(value)
            else:
                value = int(value)
        except ValueError:
            # Keep as string, but check for boolean strings
            if value.lower() in ("true", "yes", "on"):
                value = True
            elif value.lower() in ("false", "no", "off"):
                value = False  # pragma: no cover

        # Navigate/create nested structure
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}  # pragma: no cover
            current = current[key]

        # Set the value
        old_value = current.get(keys[-1], None)
        current[keys[-1]] = value

        # Save config
        with open(config_file, "w") as f:
            yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

        if old_value is not None:
            _print_success(f"Updated {args.key}: {old_value} -> {value}")
        else:
            _print_success(f"Set {args.key} = {value}")

        _print_info(f"Configuration saved to: {config_file}")

    except Exception as e:  # pragma: no cover
        _print_error(f"Failed to set configuration: {e}")  # pragma: no cover
        if args.verbose if hasattr(args, "verbose") else False:  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover
        return  # pragma: no cover




def config_init(args):
    """Initialize configuration file."""
    try:
        if not _YAML_AVAILABLE:
            _print_error(
                "PyYAML not available. Install PyYAML: pip install pyyaml"
            )  # pragma: no cover
            sys.exit(1)  # pragma: no cover
            return  # pragma: no cover

        config_dir = Path.home() / ".smrforge"
        config_file = config_dir / "config.yaml"

        if config_file.exists() and not args.force:
            _print_error(f"Configuration file already exists: {config_file}")
            _print_info("Use --force to overwrite existing configuration")
            sys.exit(1)
            return  # ensure we don't fall through when exit is mocked

        # Create default config
        default_config = {
            "endf": {
                "default_directory": str(Path.home() / "ENDF-Data"),
                "default_library": "ENDF-B-VIII.1",
            },
            "cache": {
                "directory": str(config_dir / "cache"),
            },
            "output": {
                "default_directory": "./results",
            },
            "log_level": "INFO",
        }

        # Template-specific configs
        if args.template == "production":
            default_config["log_level"] = "WARNING"
            default_config["cache"] = {
                "directory": str(config_dir / "cache"),
                "cleanup_interval_days": 30,
            }
        elif args.template == "development":
            default_config["log_level"] = "DEBUG"

        # Create directory
        config_dir.mkdir(parents=True, exist_ok=True)

        # Write config
        with open(config_file, "w") as f:
            yaml.safe_dump(default_config, f, default_flow_style=False, sort_keys=False)

        _print_success(f"Initialized configuration file: {config_file}")

        if _RICH_AVAILABLE:
            console.print(f"\n[bold]Default configuration:[/bold]")
            table = Table(show_header=False, box=None)
            table.add_column("", style="cyan")
            table.add_column("", style="green")
            for key, value in default_config.items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        table.add_row(f"  {key}.{subkey}", str(subvalue))
                else:
                    table.add_row(key, str(value))
            console.print(table)
        else:
            print("\nDefault configuration:")
            for key, value in default_config.items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        print(f"  {key}.{subkey}: {subvalue}")
                else:
                    print(f"  {key}: {value}")

        _print_info("\nYou can modify the configuration using:")
        print("  smrforge config set <key> <value>")
        print("  smrforge config show")

    except Exception as e:  # pragma: no cover
        _print_error(f"Failed to initialize configuration: {e}")  # pragma: no cover
        if args.verbose if hasattr(args, "verbose") else False:  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover
        return  # pragma: no cover


