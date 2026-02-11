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

# Import numerical validation (NaN/Inf, safety-critical outputs)
from smrforge.validation.numerical_validation import (
    validate_flux,
    validate_k_eff,
    validate_power,
    validate_safety_critical_outputs,
)

# Import regulatory traceability (always available)
from smrforge.validation.regulatory_traceability import (
    CalculationAuditTrail,
    ModelAssumption,
    SafetyMargin,
    SafetyMarginReport,
    create_audit_trail,
    generate_safety_margins_from_reactor,
)

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
    # Regulatory Traceability
    "CalculationAuditTrail",
    "validate_k_eff",
    "validate_flux",
    "validate_power",
    "validate_safety_critical_outputs",
    "ModelAssumption",
    "SafetyMargin",
    "SafetyMarginReport",
    "create_audit_trail",
    "generate_safety_margins_from_reactor",
]

if _INTEGRATION_AVAILABLE:
    __all__.extend(["ValidatedClass", "ValidatedReactorSpec", "ValidatedSolver"])
