"""
Design constraints and validation framework.

Provides automated constraint checking for reactor designs,
including safety margins and regulatory compliance checks.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.validation.constraints")


@dataclass
class ConstraintViolation:
    """Represents a constraint violation."""
    constraint_name: str
    value: float
    limit: float
    unit: str
    severity: str  # "error", "warning"
    message: str


@dataclass
class ValidationResult:
    """Result of design validation."""
    passed: bool
    violations: List[ConstraintViolation] = field(default_factory=list)
    warnings: List[ConstraintViolation] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def has_errors(self) -> bool:
        """Check if there are any error-level violations."""
        return any(v.severity == "error" for v in self.violations)
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0


@dataclass
class ConstraintSet:
    """
    Set of design constraints.
    
    Attributes:
        name: Constraint set name
        constraints: Dictionary of constraint definitions
                    Format: {"constraint_name": {"limit": value, "type": "max"/"min", "unit": str}}
        description: Description of constraint set
    """
    name: str
    constraints: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    description: str = ""
    
    def add_constraint(self, name: str, limit: float, constraint_type: str = "max", 
                      unit: str = "", description: str = ""):
        """Add a constraint to the set."""
        self.constraints[name] = {
            "limit": limit,
            "type": constraint_type,
            "unit": unit,
            "description": description
        }
    
    @classmethod
    def get_regulatory_limits(cls) -> "ConstraintSet":
        """Get standard regulatory constraint set."""
        constraints = cls(
            name="regulatory_limits",
            description="Standard regulatory safety limits"
        )
        
        # Typical PWR limits (adjust as needed)
        constraints.add_constraint(
            "max_power_density", 100.0, "max", "W/cm³",
            "Maximum local power density"
        )
        constraints.add_constraint(
            "max_temperature", 1200.0, "max", "K",
            "Maximum fuel temperature"
        )
        constraints.add_constraint(
            "min_k_eff", 1.0, "min", "",
            "Minimum criticality (safety margin)"
        )
        constraints.add_constraint(
            "max_burnup", 50.0, "max", "MWd/kg",
            "Maximum fuel burnup"
        )
        
        return constraints
    
    @classmethod
    def get_safety_margins(cls) -> "ConstraintSet":
        """Get safety margin constraint set."""
        constraints = cls(
            name="safety_margins",
            description="Safety margin requirements"
        )
        
        constraints.add_constraint(
            "shutdown_margin", 0.005, "min", "",
            "Shutdown margin (k_eff < 0.995)"
        )
        constraints.add_constraint(
            "power_peak_factor", 1.5, "max", "",
            "Power peaking factor"
        )
        
        return constraints
    
    def save(self, file_path: Path):
        """Save constraint set to JSON file."""
        data = {
            "name": self.name,
            "description": self.description,
            "constraints": self.constraints
        }
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved constraint set '{self.name}' to {file_path}")
    
    @classmethod
    def load(cls, file_path: Path) -> "ConstraintSet":
        """Load constraint set from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        constraints = cls(
            name=data["name"],
            description=data.get("description", ""),
            constraints=data.get("constraints", {})
        )
        logger.info(f"Loaded constraint set '{constraints.name}' from {file_path}")
        return constraints


class DesignValidator:
    """
    Validates reactor designs against constraints.
    
    Usage:
        >>> from smrforge.validation.constraints import DesignValidator, ConstraintSet
        >>> 
        >>> constraints = ConstraintSet.get_regulatory_limits()
        >>> validator = DesignValidator(constraints)
        >>> 
        >>> reactor = create_reactor("valar-10")
        >>> results = reactor.solve()
        >>> 
        >>> validation = validator.validate(reactor, results)
        >>> if not validation.passed:
        ...     print(validation.violations)
    """
    
    def __init__(self, constraint_set: ConstraintSet):
        """
        Initialize validator.
        
        Args:
            constraint_set: ConstraintSet to validate against
        """
        self.constraint_set = constraint_set
    
    def validate(self, reactor, analysis_results: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate reactor design.
        
        Args:
            reactor: Reactor instance
            analysis_results: Optional analysis results dictionary
        
        Returns:
            ValidationResult with validation status and violations
        """
        violations = []
        warnings = []
        metrics = {}
        
        # Run analysis if not provided
        if analysis_results is None:
            try:
                analysis_results = reactor.solve()
            except Exception as e:
                logger.error(f"Failed to run analysis for validation: {e}")
                violations.append(ConstraintViolation(
                    "analysis_failure", 0.0, 0.0, "", "error",
                    f"Analysis failed: {e}"
                ))
                return ValidationResult(
                    passed=False,
                    violations=violations,
                    metrics=metrics
                )
        
        # Extract metrics from results
        metrics["k_eff"] = analysis_results.get("k_eff", 0.0)
        if "power" in analysis_results:
            power_array = analysis_results["power"]
            if isinstance(power_array, np.ndarray):
                metrics["max_power_density"] = float(np.max(power_array))
                metrics["power_peak_factor"] = float(np.max(power_array) / np.mean(power_array))
        
        # Check each constraint
        for constraint_name, constraint_def in self.constraint_set.constraints.items():
            limit = constraint_def["limit"]
            constraint_type = constraint_def.get("type", "max")
            unit = constraint_def.get("unit", "")
            
            # Get actual value
            if constraint_name in metrics:
                value = metrics[constraint_name]
            elif constraint_name == "min_k_eff" and "k_eff" in metrics:
                # Special handling for k_eff constraints
                value = metrics["k_eff"]
                if constraint_type == "min":
                    violation = value < limit
                else:
                    violation = value > limit
                
                if violation:
                    violations.append(ConstraintViolation(
                        constraint_name, value, limit, unit, "error",
                        f"{constraint_name}: {value:.6f} {'<' if constraint_type == 'min' else '>'} {limit}"
                    ))
                continue
            else:
                # Try to get from reactor spec
                if hasattr(reactor, 'spec'):
                    if hasattr(reactor.spec, constraint_name):
                        value = getattr(reactor.spec, constraint_name)
                    else:
                        continue  # Skip if can't find value
                else:
                    continue
            
            # Check constraint (skip if value is None or not a number)
            if value is None or not isinstance(value, (int, float, np.number)):
                continue
            
            if constraint_type == "max":
                violation = value > limit
                if violation:
                    # Error if exceeds limit significantly, warning if just over
                    severity = "warning" if limit * 0.9 < value <= limit * 1.1 else "error"
                else:
                    severity = None  # No violation
            elif constraint_type == "min":
                violation = value < limit
                if violation:
                    # Error if below limit significantly, warning if just under
                    severity = "error" if value < limit * 0.9 else "warning"
                else:
                    severity = None  # No violation
            else:
                continue
            
            if violation:
                viol = ConstraintViolation(
                    constraint_name, value, limit, unit, severity,
                    f"{constraint_name}: {value:.3f} {unit} {'exceeds' if constraint_type == 'max' else 'below'} limit {limit:.3f} {unit}"
                )
                if severity == "error":
                    violations.append(viol)
                else:
                    warnings.append(viol)
        
        passed = len([v for v in violations if v.severity == "error"]) == 0
        
        return ValidationResult(
            passed=passed,
            violations=violations,
            warnings=warnings,
            metrics=metrics
        )
