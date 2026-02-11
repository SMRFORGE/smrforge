"""
Memory and performance profiling utilities.

Provides tracemalloc-based memory profiling: peak usage, top allocations
by file:line. Used by scripts/profile_performance.py and custom workflows.
"""

from __future__ import annotations

import tracemalloc
from typing import Any, Callable, Dict, List, Tuple


def run_with_memory_profile(
    func: Callable[..., Any],
    *args: Any,
    top_n: int = 10,
    **kwargs: Any,
) -> Tuple[Any, Dict[str, Any]]:
    """
    Run a callable under tracemalloc and collect memory stats.

    Args:
        func: Callable to run (e.g. a function that performs keff or mesh).
        *args: Positional arguments for func.
        top_n: Number of top allocation sites to report.
        **kwargs: Keyword arguments for func.

    Returns:
        (result, report_dict) where result is func(*args, **kwargs) and
        report_dict has keys: peak_mb, current_mb, top_allocations.
        top_allocations is a list of dicts with keys: size_mb, count, traceback.
    """
    tracemalloc.start(10)
    try:
        s1 = tracemalloc.take_snapshot()
        result = func(*args, **kwargs)
        s2 = tracemalloc.take_snapshot()
        current, peak = tracemalloc.get_traced_memory()
        stats = s2.compare_to(s1, "lineno")
        top: List[Dict[str, Any]] = []
        for i, stat in enumerate(stats):
            if i >= top_n:
                break
            top.append(
                {
                    "size_mb": stat.size_diff / (1024 * 1024),
                    "count": stat.count_diff,
                    "traceback": (
                        "\n".join(stat.traceback.format()) if stat.traceback else ""
                    ),
                }
            )
        report: Dict[str, Any] = {
            "peak_mb": peak / (1024 * 1024),
            "current_mb": current / (1024 * 1024),
            "top_allocations": top,
        }
        return result, report
    finally:
        tracemalloc.stop()


def format_memory_report(report: Dict[str, Any]) -> str:
    """Format report_dict from run_with_memory_profile as human-readable text."""
    lines = [
        "Memory Profile",
        "=" * 50,
        f"Peak traced memory:   {report['peak_mb']:.2f} MiB",
        f"Current traced:       {report['current_mb']:.2f} MiB",
        "",
        "Top allocations (during run):",
    ]
    for i, a in enumerate(report["top_allocations"], 1):
        lines.append(f"  {i}. {a['size_mb']:.3f} MiB, {a['count']} blocks")
        if a["traceback"]:
            for frame in a["traceback"].strip().split("\n")[:3]:
                lines.append(f"      {frame.strip()}")
    return "\n".join(lines)
