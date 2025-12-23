"""
Data validation and schema enforcement
"""

# Import models
from smrforge.validation.models import (
    CrossSectionData,
    EnrichmentClass,
    FuelType,
    GraphiteGrade,
    ReactorSpecification,
    ReactorType,
    SolverOptions,
)

# Import validators
from smrforge.validation.validators import (
    ConsistencyValidator,
    DataValidator,
    GeometryValidator,
    NeutronicsValidator,
    PhysicalValidator,
    ThermalValidator,
    ValidationIssue,
    ValidationLevel,
    ValidationResult,
)

# Import integration utilities
try:
    from smrforge.validation.integration import (
        ValidatedClass,
        ValidatedReactorSpec,
        ValidatedSolver,
    )

    _INTEGRATION_AVAILABLE = True
except ImportError:
    _INTEGRATION_AVAILABLE = False

__all__ = [
    # Models
    "ReactorType",
    "FuelType",
    "EnrichmentClass",
    "GraphiteGrade",
    "ReactorSpecification",
    "CrossSectionData",
    "SolverOptions",
    # Validators
    "ValidationLevel",
    "ValidationIssue",
    "ValidationResult",
    "DataValidator",
    "PhysicalValidator",
    "GeometryValidator",
    "NeutronicsValidator",
    "ThermalValidator",
    "ConsistencyValidator",
]

if _INTEGRATION_AVAILABLE:
    __all__.extend(["ValidatedClass", "ValidatedReactorSpec", "ValidatedSolver"])
