"""
GitHub Actions command handlers and metadata.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

from smrforge.cli.common import (
    Table,
    _RICH_AVAILABLE,
    _print_error,
    _print_info,
    _print_success,
    console,
)


# GitHub Actions: feature IDs and metadata (must match scripts/github_workflow_check.py)
GITHUB_ACTIONS_FEATURES = [
    {
        "id": "ci",
        "name": "CI",
        "description": "Tests, lint, build, validation, coverage",
    },
    {
        "id": "ci-quick",
        "name": "CI (quick)",
        "description": "Fast check: single Python, tests without coverage",
    },
    {
        "id": "docs",
        "name": "Docs",
        "description": "Build and deploy documentation (GitHub Pages)",
    },
    {
        "id": "performance",
        "name": "Performance",
        "description": "Performance benchmarks",
    },
    {
        "id": "security",
        "name": "Security",
        "description": "Security audit (pip-audit, bandit)",
    },
    {
        "id": "release",
        "name": "Release",
        "description": "Build and publish to PyPI on version tags",
    },
    {
        "id": "nightly",
        "name": "Nightly",
        "description": "Scheduled full test and validation run",
    },
    {
        "id": "docker",
        "name": "Docker",
        "description": "Build and push container image (GHCR)",
    },
    {
        "id": "dependabot",
        "name": "Dependabot",
        "description": "Run tests on Dependabot dependency PRs",
    },
    {
        "id": "stale",
        "name": "Stale",
        "description": "Mark and close stale issues and PRs",
    },
]


def _github_repo_root(args: Any) -> Path:
    """Repo root for GitHub commands (--repo-root or cwd)."""
    root = getattr(args, "repo_root", None)
    if root is not None:
        p = Path(root).resolve()
        if not p.is_dir():
            _print_error(f"Repo root is not a directory: {p}")
            sys.exit(1)
        return p
    return Path.cwd().resolve()


def _github_paths(root: Path) -> tuple[Path, Path]:
    """Return (workflows-enabled path, workflows-config path)."""
    gh = root / ".github"
    return gh / "workflows-enabled", gh / "workflows-config.json"


def _read_workflows_enabled(root: Path) -> bool:
    """True if workflows-enabled exists and is 'true'."""
    p, _ = _github_paths(root)
    if not p.exists():
        return False
    return p.read_text().strip().lower() == "true"


def _read_workflows_config(root: Path) -> Dict[str, bool]:
    """Read per-feature config; missing file or key => use default True for backward compat."""
    _, config_path = _github_paths(root)
    out = {f["id"]: True for f in GITHUB_ACTIONS_FEATURES}
    if not config_path.exists():
        return out
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            for fid in out:
                if fid in data and isinstance(data[fid], bool):
                    out[fid] = data[fid]
    except (json.JSONDecodeError, OSError):  # pragma: no cover
        pass  # pragma: no cover
    return out


def _write_workflows_config(root: Path, config: Dict[str, bool]) -> None:
    """Write workflows-config.json (creates .github if needed)."""
    _, config_path = _github_paths(root)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    # Only include known feature IDs
    out = {f["id"]: config.get(f["id"], True) for f in GITHUB_ACTIONS_FEATURES}
    config_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")


def github_actions_status(args: Any) -> None:
    """Show GitHub Actions status (global and per-feature)."""
    try:
        root = _github_repo_root(args)
        enabled_path, config_path = _github_paths(root)
        global_on = _read_workflows_enabled(root)
        config = _read_workflows_config(root)

        if _RICH_AVAILABLE:
            status = (
                "[bold green]ENABLED[/bold green]"
                if global_on
                else "[bold red]DISABLED[/bold red]"
            )  # pragma: no cover
            console.print(f"\nGitHub Actions (global): {status}")  # pragma: no cover
            console.print(f"Control file: {enabled_path}")  # pragma: no cover
            if config_path.exists():  # pragma: no cover
                table = Table(title="Feature status")  # pragma: no cover
                table.add_column("Feature", style="cyan")  # pragma: no cover
                table.add_column("Description", style="dim")  # pragma: no cover
                table.add_column("Status", justify="center")  # pragma: no cover
                for f in GITHUB_ACTIONS_FEATURES:  # pragma: no cover
                    on = config.get(f["id"], True)  # pragma: no cover
                    s = (
                        "[green]on[/green]" if on else "[red]off[/red]"
                    )  # pragma: no cover
                    table.add_row(f["name"], f["description"], s)  # pragma: no cover
                console.print(table)  # pragma: no cover
                console.print(f"Config: {config_path}")  # pragma: no cover
            else:  # pragma: no cover
                _print_info(
                    "No per-feature config; all features follow global setting."
                )  # pragma: no cover
        else:
            status = "ENABLED" if global_on else "DISABLED"
            print(f"\nGitHub Actions (global): {status}")
            print(f"Control file: {enabled_path}")
            if config_path.exists():
                for f in GITHUB_ACTIONS_FEATURES:
                    on = config.get(f["id"], True)
                    print(f"  {f['name']}: {'on' if on else 'off'}")
            else:
                print("No per-feature config; all features follow global.")
        if getattr(args, "output", None):
            with open(args.output, "w", encoding="utf-8") as f:  # pragma: no cover
                json.dump(
                    {  # pragma: no cover
                        "enabled": global_on,  # pragma: no cover
                        "file": str(enabled_path),  # pragma: no cover
                        "config_file": (
                            str(config_path) if config_path.exists() else None
                        ),  # pragma: no cover
                        "features": config,  # pragma: no cover
                    },
                    f,
                    indent=2,
                )  # pragma: no cover
            _print_success(f"Status saved to {args.output}")  # pragma: no cover
    except Exception as e:
        _print_error(f"Failed to check GitHub Actions status: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover


def github_actions_enable(args: Any) -> None:
    """Enable GitHub Actions (global)."""
    try:
        root = _github_repo_root(args)
        enabled_path, _ = _github_paths(root)
        enabled_path.parent.mkdir(parents=True, exist_ok=True)
        enabled_path.write_text("true\n", encoding="utf-8")
        _print_success("GitHub Actions enabled")
        _print_info(f"Control file updated: {enabled_path}")
        _print_info(
            "Workflows will run on next push or pull request (subject to per-feature config)"
        )
    except Exception as e:  # pragma: no cover
        _print_error(f"Failed to enable GitHub Actions: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover


def github_actions_disable(args: Any) -> None:
    """Disable GitHub Actions (global)."""
    try:
        root = _github_repo_root(args)
        enabled_path, _ = _github_paths(root)
        enabled_path.parent.mkdir(parents=True, exist_ok=True)
        enabled_path.write_text("false\n", encoding="utf-8")
        _print_success("GitHub Actions disabled")
        _print_info(f"Control file updated: {enabled_path}")
        _print_info("Workflows will be skipped on next push or pull request")
    except Exception as e:  # pragma: no cover
        _print_error(f"Failed to disable GitHub Actions: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover


def github_actions_list(args: Any) -> None:
    """List GitHub Actions features and their status."""
    try:
        root = _github_repo_root(args)
        global_on = _read_workflows_enabled(root)
        config = _read_workflows_config(root)
        if _RICH_AVAILABLE:
            table = Table(title="GitHub Actions features")  # pragma: no cover
            table.add_column("ID", style="cyan")  # pragma: no cover
            table.add_column("Name", style="green")  # pragma: no cover
            table.add_column("Description", style="dim")  # pragma: no cover
            table.add_column("Runs", justify="center")  # pragma: no cover
            for f in GITHUB_ACTIONS_FEATURES:  # pragma: no cover
                on = config.get(f["id"], True)  # pragma: no cover
                runs = global_on and on  # pragma: no cover
                run_str = (
                    "[green]yes[/green]" if runs else "[red]no[/red]"
                )  # pragma: no cover
                table.add_row(
                    f["id"], f["name"], f["description"], run_str
                )  # pragma: no cover
            console.print(table)  # pragma: no cover
            console.print(
                f"\nGlobal: {'ON' if global_on else 'OFF'}  |  Use [cyan]smrforge github configure[/cyan] to change features"
            )  # pragma: no cover
        else:
            print(
                "ID          Name         Description                                    Runs"
            )
            print("-" * 70)
            for f in GITHUB_ACTIONS_FEATURES:
                on = config.get(f["id"], True)
                runs = "yes" if (global_on and on) else "no"
                print(f"{f['id']:<11} {f['name']:<12} {f['description']:<44} {runs}")
    except Exception as e:  # pragma: no cover
        _print_error(f"Failed to list features: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover


def github_actions_set(args: Any) -> None:
    """Set one feature on or off."""
    try:
        root = _github_repo_root(args)
        fid = getattr(args, "feature", "").strip().lower()
        if fid not in [f["id"] for f in GITHUB_ACTIONS_FEATURES]:
            _print_error(
                f"Unknown feature: {fid}. Use: {', '.join(f['id'] for f in GITHUB_ACTIONS_FEATURES)}"
            )
            sys.exit(1)
        on = getattr(args, "value", "on").strip().lower() in ("on", "true", "1", "yes")
        config = _read_workflows_config(root)
        config[fid] = on
        _write_workflows_config(root, config)
        name = next(f["name"] for f in GITHUB_ACTIONS_FEATURES if f["id"] == fid)
        _print_success(f"Feature '{name}' ({fid}) set to {'on' if on else 'off'}")
    except Exception as e:
        _print_error(f"Failed to set feature: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover


def github_actions_configure(args: Any) -> None:
    """Interactive or flag-based configuration of which features run in GitHub Actions."""
    try:
        root = _github_repo_root(args)
        _, config_path = _github_paths(root)
        config = _read_workflows_config(root)
        # Apply any --ci/--docs/--performance/--security flags (set by parser)
        for f in GITHUB_ACTIONS_FEATURES:
            key = f["id"].replace("-", "_")
            val = getattr(args, key, None)
            if val is not None:
                config[f["id"]] = val in ("on", "true", "1", "yes")
        # Interactive: prompt for each only when no feature flags were given
        feature_flags = [f["id"].replace("-", "_") for f in GITHUB_ACTIONS_FEATURES]
        any_flag = any(getattr(args, k, None) is not None for k in feature_flags)
        if not any_flag:
            if _RICH_AVAILABLE:  # pragma: no cover
                console.print(
                    "\n[bold]GitHub Actions feature selection[/bold]"
                )  # pragma: no cover
                console.print(
                    "Choose which workflows run when Actions are enabled. [y] on, [n] off, [Enter] keep current.\n"
                )  # pragma: no cover
            else:  # pragma: no cover
                print("\nGitHub Actions feature selection")  # pragma: no cover
                print(
                    "y/n = enable/disable; Enter = keep current\n"
                )  # pragma: no cover
            for f in GITHUB_ACTIONS_FEATURES:  # pragma: no cover
                cur = config.get(f["id"], True)  # pragma: no cover
                prompt = f"  {f['name']} ({f['id']}): {'on' if cur else 'off'} [y/n/Enter]: "  # pragma: no cover
                try:  # pragma: no cover
                    raw = input(prompt).strip().lower()  # pragma: no cover
                except EOFError:  # pragma: no cover
                    break  # pragma: no cover
                if raw in ("y", "yes", "on", "1", "true"):  # pragma: no cover
                    config[f["id"]] = True  # pragma: no cover
                elif raw in ("n", "no", "off", "0", "false"):  # pragma: no cover
                    config[f["id"]] = False  # pragma: no cover
        config_path.parent.mkdir(parents=True, exist_ok=True)
        _write_workflows_config(root, config)
        _print_success("GitHub Actions feature config updated")
        _print_info(f"Config file: {config_path}")
        if _RICH_AVAILABLE:
            table = Table()
            table.add_column("Feature", style="cyan")
            table.add_column("Status", justify="center")
            for f in GITHUB_ACTIONS_FEATURES:
                on = config[f["id"]]
                table.add_row(
                    f["name"], "[green]on[/green]" if on else "[red]off[/red]"
                )
            console.print(table)
    except Exception as e:  # pragma: no cover
        _print_error(f"Failed to configure GitHub Actions: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover
