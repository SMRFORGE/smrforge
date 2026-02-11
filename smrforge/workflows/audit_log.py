"""
Run log / audit trail for design-study, optimize, and UQ workflows.

Appends a JSON line or record to a log file (e.g. in output dir or .smrforge_runs.json)
with timestamp, command id, workflow name, args summary, key results, and pass/fail.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from ..utils.exception_handling import reraise_if_system
from ..utils.logging import get_logger

logger = get_logger("smrforge.workflows.audit_log")


@dataclass
class RunRecord:
    """Single run record for audit log."""

    workflow: str  # "design-study" | "optimize" | "uq" | "sensitivity" | ...
    timestamp: str  # ISO format
    args_summary: Dict[str, Any] = field(default_factory=dict)
    results_summary: Dict[str, Any] = field(default_factory=dict)
    passed: Optional[bool] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def append_run(
    workflow: str,
    args_summary: Optional[Dict[str, Any]] = None,
    results_summary: Optional[Dict[str, Any]] = None,
    passed: Optional[bool] = None,
    error: Optional[str] = None,
    log_path: Optional[Path] = None,
) -> bool:
    """
    Append a run record to the audit log.

    Args:
        workflow: Workflow name (e.g. "design-study", "optimize", "uq").
        args_summary: Short summary of CLI/config (e.g. reactor path, output dir).
        results_summary: Key results (e.g. k_eff, n_iterations, n_pareto).
        passed: Whether the run passed validation or succeeded.
        error: If failed, error message.
        log_path: Where to append. If None, uses log_path = Path("output/.smrforge_runs.json").

    Returns:
        True if record was written successfully, False otherwise.
    """
    log_path = log_path or Path("output/.smrforge_runs.json")
    record = RunRecord(
        workflow=workflow,
        timestamp=datetime.now(timezone.utc).isoformat(),
        args_summary=args_summary or {},
        results_summary=results_summary or {},
        passed=passed,
        error=error,
    )
    data = record.to_dict()
    # Append to JSON array file: read existing, append, write
    try:
        if log_path.exists():
            text = log_path.read_text(encoding="utf-8")
            try:
                existing = json.loads(text)
            except json.JSONDecodeError:
                existing = []
            if not isinstance(existing, list):
                existing = [existing]
        else:
            existing = []
        existing.append(data)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        return True
    except Exception as e:  # pragma: no cover
        reraise_if_system(e)
        logger.warning(
            "Audit log append failed (run record not persisted): %s. Path: %s",
            e,
            log_path,
        )
        return False
