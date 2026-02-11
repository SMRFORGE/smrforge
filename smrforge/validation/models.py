"""
Pydantic models for SMRForge validation.
This module provides aliases for models defined in pydantic_layer.py
to maintain backward compatibility with existing imports.
"""

# Re-export all models from pydantic_layer
from smrforge.validation.pydantic_layer import (  # Enums; Core Models; Type validators
    BurnupResultSummary,
    CrossSectionData,
    EnrichmentClass,
    FuelType,
    GeometryParameters,
    GraphiteGrade,
    KeffResult,
    MaterialComposition,
    NormalizedArray,
    NumpyArray,
    PositiveArray,
    ReactorSpecification,
    ReactorType,
    SolverOptions,
)

__all__ = [
    # Enums
    "ReactorType",
    "FuelType",
    "EnrichmentClass",
    "GraphiteGrade",
    # Core Models
    "ReactorSpecification",
    "CrossSectionData",
    "SolverOptions",
    "GeometryParameters",
    "MaterialComposition",
    "KeffResult",
    "BurnupResultSummary",
    # Type validators
    "NumpyArray",
    "PositiveArray",
    "NormalizedArray",
]
