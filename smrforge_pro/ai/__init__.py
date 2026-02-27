"""
Pro AI module: audit, surrogates, PINNs, deep surrogates, neural operators, UQ.
"""

from .audit import record_ai_model
from .surrogates import load_surrogate_from_path

__all__ = [
    "record_ai_model",
    "load_surrogate_from_path",
]

