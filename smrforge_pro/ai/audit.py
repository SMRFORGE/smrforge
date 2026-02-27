"""
AI model audit for regulatory traceability.

Records AI/ML model usage in CalculationAuditTrail for licensing and reproducibility.
"""

from typing import Any, Dict, Optional


def record_ai_model(
    trail: Any,
    name: str,
    version: Optional[str] = None,
    config_hash: Optional[str] = None,
    **extra: Any,
) -> None:
    """Record AI model usage in audit trail."""
    entry: Dict[str, Any] = {"name": name}
    if version is not None:
        entry["version"] = version
    if config_hash is not None:
        entry["config_hash"] = config_hash
    entry.update(extra)
    trail.ai_models_used.append(entry)
