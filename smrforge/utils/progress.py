"""
Progress visibility for long-running operations.

Provides phase labels ("Cross-sections…", "Solving…", "Writing…") and
optional ETA for batch operations. Integrates with Rich when available.
"""

from contextlib import contextmanager
from typing import Callable, Iterator, Optional

from ..utils.logging import get_logger

logger = get_logger("smrforge.utils.progress")

try:
    from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False
    Progress = None


@contextmanager
def phase_progress(
    phases: list[str],
    *,
    verbose: bool = True,
    show_eta: bool = False,
) -> Iterator[Callable[[int, Optional[str]], None]]:
    """
    Context manager for phase-based progress in long operations.

    Args:
        phases: List of phase names, e.g. ["Cross-sections", "Solving", "Writing"]
        verbose: If True, log and optionally show Rich progress
        show_eta: If True and Rich available, show ETA (only meaningful for phased work with known duration)

    Yields:
        A callback set_phase(phase_index, sub_msg) to update progress.
        Call set_phase(0, None) to enter phase 0, set_phase(1, "iteration 5") for phase 1 with sub-message.

    Example:
        with phase_progress(["Loading", "Solving", "Writing"]) as set_phase:
            set_phase(0)
            load_data()
            set_phase(1)
            result = solve()
            set_phase(2, "results.json")
            save(result)
    """
    current = [0]  # mutable to allow update from inner scope

    def set_phase(phase_index: int, sub_msg: Optional[str] = None) -> None:
        current[0] = phase_index
        label = phases[phase_index] if phase_index < len(phases) else str(phase_index)
        display = f"{label}…" if not sub_msg else f"{label}: {sub_msg}"
        if verbose:
            logger.info("[%d/%d] %s", phase_index + 1, len(phases), display)

    if _RICH_AVAILABLE and verbose:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=None,
        ) as progress:
            task = progress.add_task(f"{phases[0]}…", total=len(phases))

            def set_phase_rich(phase_index: int, sub_msg: Optional[str] = None) -> None:
                current[0] = phase_index
                label = phases[phase_index] if phase_index < len(phases) else str(phase_index)
                display = f"{label}…" if not sub_msg else f"{label}: {sub_msg}"
                progress.update(task, description=display, completed=phase_index)
                logger.info("[%d/%d] %s", phase_index + 1, len(phases), display)

            yield set_phase_rich
            progress.update(task, completed=len(phases))
    else:
        yield set_phase


def log_phase(phase: str, sub_msg: Optional[str] = None) -> None:
    """Log a phase label (no Rich, just logging)."""
    display = f"{phase}…" if not sub_msg else f"{phase}: {sub_msg}"
    logger.info(display)
