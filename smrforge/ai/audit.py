"""
AI model audit helpers for regulatory traceability.

Record which AI/ML models, versions, and config were used in a run.
Needed for NQA-1 dedication and reproducibility of AI-assisted workflows.
"""

from typing import Any, Dict, List, Optional

from ..validation.regulatory_traceability import CalculationAuditTrail


def record_ai_model(
    trail: CalculationAuditTrail,
    name: str,
    version: Optional[str] = None,
    config_hash: Optional[str] = None,
    **extra: Any,
) -> None:
    """
    Append an AI/ML model to the audit trail's ai_models_used list.

    Call after using a surrogate, GP, or other ML model in a calculation
    to maintain regulatory traceability.

    Args:
        trail: CalculationAuditTrail to update (modified in-place).
        name: Model name (e.g., "gp", "rbf", "custom_nn").
        version: Model version string (e.g., "1.0", "sklearn-1.3.0").
        config_hash: Hash of config/hyperparams for reproducibility.
        **extra: Additional fields (e.g., prompt_hash for LLMs).

    Example:
        >>> from smrforge.validation.regulatory_traceability import create_audit_trail
        >>> trail = create_audit_trail("keff", inputs={}, outputs={"k_eff": 1.0})
        >>> record_ai_model(trail, "rbf", version="scipy-1.11", config_hash="abc123")
        >>> trail.ai_models_used
        [{"name": "rbf", "version": "scipy-1.11", "config_hash": "abc123"}]
    """
    entry: Dict[str, Any] = {"name": name, **extra}
    if version is not None:
        entry["version"] = version
    if config_hash is not None:
        entry["config_hash"] = config_hash
    trail.ai_models_used.append(entry)
