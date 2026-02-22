"""
AI integration namespace for SMRForge.

Bring-Your-Own Surrogate (BYOS), audit trails, and validation reports.
Reference: NUCLEAR_INDUSTRY_ANALYSIS_AND_AI_FUTURE_PROOFING.md § 3.3
"""

from .audit import record_ai_model

__all__ = [
    "record_ai_model",
    "load_surrogate_from_path",
    "register_surrogate_from_path",
    "model_hash",
    "generate_validation_report",
    "SurrogateValidationReport",
]

# Optional exports - import only when needed to avoid loading heavy deps
def __getattr__(name: str):
    if name == "load_surrogate_from_path":
        from .surrogate import load_surrogate_from_path
        return load_surrogate_from_path
    if name == "register_surrogate_from_path":
        from .surrogate import register_surrogate_from_path
        return register_surrogate_from_path
    if name == "model_hash":
        from .surrogate import model_hash
        return model_hash
    if name == "generate_validation_report":
        from .validation import generate_validation_report
        return generate_validation_report
    if name == "SurrogateValidationReport":
        from .validation import SurrogateValidationReport
        return SurrogateValidationReport
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
