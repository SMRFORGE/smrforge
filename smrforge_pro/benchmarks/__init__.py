"""
Pro benchmarks: runner, case taxonomy, validation_benchmarks.
"""

from pathlib import Path
from typing import Any, Dict

from .runner import BenchmarkRunner

__all__ = ["BenchmarkRunner", "load_benchmark_reference"]
_REFERENCE_CACHE: Dict[str, Dict[str, Any]] = {}


def load_benchmark_reference(benchmark_id: str) -> Dict[str, Any]:
    """Load reference values for a benchmark case."""
    if benchmark_id in _REFERENCE_CACHE:
        return _REFERENCE_CACHE[benchmark_id]
    # Try validation_benchmarks.json if present
    try:
        ref_path = Path(__file__).parent / "validation_benchmarks.json"
        if ref_path.exists():
            import json
            data = json.loads(ref_path.read_text(encoding="utf-8"))
            cases = data.get("cases", data)
            for c in cases if isinstance(cases, list) else [cases]:
                bid = c.get("id", c.get("test_case", ""))
                if bid == benchmark_id:
                    _REFERENCE_CACHE[benchmark_id] = c
                    return c
    except Exception:
        pass
    # Built-in fallbacks
    builtin = {
        "c5g7": {"k_eff": 1.0, "tolerance": 0.02, "preset": "c5g7"},
        "valar-10": {"k_eff": 1.0, "tolerance": 0.02, "preset": "valar-10"},
    }
    return builtin.get(benchmark_id, {"k_eff": 1.0, "tolerance": 0.02, "preset": benchmark_id})
