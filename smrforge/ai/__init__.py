"""
AI integration namespace for SMRForge.

Future: AI/ML models, surrogates, audit trails for AI-assisted runs.
Reference: NUCLEAR_INDUSTRY_ANALYSIS_AND_AI_FUTURE_PROOFING.md § 3.3
"""

from .audit import record_ai_model

__all__ = ["record_ai_model"]
