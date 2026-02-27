"""
Tier 3: Generative & Conversational AI.

Document-specified: parse_nl_design, design_from_nl (Path C Product Updates).
"""

from .copilot import (
    design_from_natural_language,
    design_from_nl,
    parse_nl_design,
)
from .document_understanding import extract_specs_from_document
from .conversational_safety import run_safety_query

__all__ = [
    "design_from_natural_language",
    "design_from_nl",
    "parse_nl_design",
    "extract_specs_from_document",
    "run_safety_query",
]
