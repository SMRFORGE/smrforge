"""
AI model audit helpers for regulatory traceability.

Pro tier only. Delegates to smrforge_pro when installed.
"""

from typing import Any, Optional

_MSG = (
    "AI audit (record_ai_model) requires SMRForge Pro. "
    "Upgrade at https://smrforge.io or install smrforge-pro."
)

try:
    from smrforge_pro.ai.audit import record_ai_model as _record_ai_model
    _PRO_AVAILABLE = True
except ImportError:
    _record_ai_model = None  # type: ignore
    _PRO_AVAILABLE = False


def record_ai_model(
    trail: Any,
    name: str,
    version: Optional[str] = None,
    config_hash: Optional[str] = None,
    **extra: Any,
) -> None:
    """Pro tier only. Use SMRForge Pro for AI audit trail."""
    if _PRO_AVAILABLE:
        return _record_ai_model(trail, name, version=version, config_hash=config_hash, **extra)
    raise ImportError(_MSG)
