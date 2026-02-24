"""
AI model audit helpers for regulatory traceability.

Pro tier: Full implementation of record_ai_model.
"""

from pathlib import Path
from typing import Any, Dict, Optional


def record_ai_model(
    trail,
    name: str,
    version: Optional[str] = None,
    config_hash: Optional[str] = None,
    model_hash: Optional[str] = None,
    **extra: Any,
) -> None:
    """
    Append AI model usage to CalculationAuditTrail.ai_models_used.

    Args:
        trail: CalculationAuditTrail instance (must have ai_models_used list)
        name: Model name (e.g., "rbf_surrogate", "onnx_keff")
        version: Optional version string
        config_hash: Optional hash of training config for audit trail
        model_hash: Optional SHA-256 hash of model file/weights
        **extra: Additional fields to record (e.g., param_names, output_metric)
    """
    entry: Dict[str, Any] = {"name": name}
    if version is not None:
        entry["version"] = version
    if config_hash is not None:
        entry["config_hash"] = config_hash
    if model_hash is not None:
        entry["model_hash"] = model_hash
    entry.update(extra)
    trail.ai_models_used.append(entry)
