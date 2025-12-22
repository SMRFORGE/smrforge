# validation/decorators.py
"""
Decorators and utilities for automatic validation integration.
Apply to functions/classes to enforce validation rules.
"""

import functools
import inspect
from typing import Callable, Any, Dict
import numpy as np
from .validators import (
    DataValidator, ValidationResult, ValidationLevel, ValidationIssue
)


def validate_inputs(**validators):
    """
    Decorator to validate function inputs automatically.
    
    Usage:
        @validate_inputs(
            temperature=lambda T: PhysicalValidator.validate_temperature(T),
            pressure=lambda P: PhysicalValidator.validate_pressure(P)
        )
        def my_function(temperature, pressure):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            # Validate each parameter
            combined_result = ValidationResult(valid=True)
            
            for param_name, validator_func in validators.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    result = validator_func(value)
                    combined_result.issues.extend(result.issues)
            
            # Raise if critical errors
            if combined_result.has_errors():
                error_msgs = [str(i) for i in combined_result.issues 
                            if i.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]]
                raise ValueError(f"Validation failed:\n" + "\n".join(error_msgs))
            
            # Warn if warnings
            warnings = [i for i in combined_result.issues 
                       if i.level == ValidationLevel.WARNING]
            if warnings:
                import warnings as warn_module
                for issue in warnings:
                    warn_module.warn(str(issue), UserWarning)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_outputs(**validators):
    """
    Decorator to validate function outputs.
    
    Usage:
        @validate_outputs(
            k_eff=lambda k: PhysicalValidator.validate_k_eff(k)
        )
        def solve_eigenvalue():
            return {'k_eff': 1.05, ...}
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Validate outputs
            combined_result = ValidationResult(valid=True)
            
            if isinstance(result, dict):
                for output_name, validator_func in validators.items():
                    if output_name in result:
                        value = result[output_name]
                        validation = validator_func(value)
                        combined_result.issues.extend(validation.issues)
            elif isinstance(result, tuple):
                # Handle tuple returns
                for i, validator_func in enumerate(validators.values()):
                    if i < len(result):
                        validation = validator_func(result[i])
                        combined_result.issues.extend(validation.issues)
            
            # Raise if errors
            if combined_result.has_errors():
                error_msgs = [str(i) for i in combined_result.issues]
                raise ValueError(f"Output validation failed:\n" + "\n".join(error_msgs))
            
            return result
        
        return wrapper
    return decorator


def validate_array(arr: np.ndarray, name: str = "array",
                  allow_negative: bool = False,
                  allow_nan: bool = False,
                  allow_inf: bool = False,
                  min_val: float = None,
                  max_val: float = None) -> ValidationResult:
    """Validate numpy array properties."""
    result = ValidationResult(valid=True)
    
    if not isinstance(arr, np.ndarray):
        result.add_issue(ValidationLevel.ERROR, name,
                       "Not a numpy array", value=type(arr))
        return result
    
    if arr.size == 0:
        result.add_issue(ValidationLevel.WARNING, name,
                       "Empty array")
        return result
    
    if not allow_nan and np.any(np.isnan(arr)):
        result.add_issue(ValidationLevel.ERROR, name,
                       f"Contains {np.sum(np.isnan(arr))} NaN values")
    
    if not allow_inf and np.any(np.isinf(arr)):
        result.add_issue(ValidationLevel.ERROR, name,
                       f"Contains {np.sum(np.isinf(arr))} Inf values")
    
    if not allow_negative and np.any(arr < 0):
        result.add_issue(ValidationLevel.ERROR, name,
                       f"Contains {np.sum(arr < 0)} negative values",
                       value=f"min={np.min(arr)}")
    
    if min_val is not None and np.any(arr < min_val):
        result.add_issue(ValidationLevel.WARNING, name,
                       f"Values below minimum",
                       value=f"min={np.min(arr)}",
                       expected=f">= {min_val}")
    
    if max_val is not None and np.any(arr > max_val):
        result.add_issue(ValidationLevel.WARNING, name,
                       f"Values above maximum",
                       value=f"max={np.max(arr)}",
                       expected=f"<= {max_val}")
    
    return result


class ValidatedClass:
    """
    Base class for classes that need automatic validation.
    Override _validate() method to define validation rules.
    """
    
    def __init__(self):
        self._validation_enabled = True
        self._last_validation: ValidationResult = None
    
    def _validate(self) -> ValidationResult:
        """Override this method to define validation rules."""
        return ValidationResult(valid=True)
    
    def validate(self, raise_on_error: bool = True) -> ValidationResult:
        """Run validation checks."""
        result = self._validate()
        self._last_validation = result
        
        if raise_on_error and result.has_errors():
            raise ValueError(f"Validation failed:\n{result}")
        
        return result
    
    def disable_validation(self):
        """Disable automatic validation (use with caution!)."""
        self._validation_enabled = False
    
    def enable_validation(self):
        """Re-enable automatic validation."""
        self._validation_enabled = True


# Example integration with existing classes
class ValidatedReactorSpec(ValidatedClass):
    """Example of validated reactor specification."""
    
    def __init__(self, spec):
        super().__init__()
        self.spec = spec
        self.validator = DataValidator()
        
        # Validate on construction
        if self._validation_enabled:
            self.validate()
    
    def _validate(self) -> ValidationResult:
        """Validate reactor specification."""
        return self.validator.validate_reactor_spec(self.spec)


class ValidatedSolver(ValidatedClass):
    """Example of validated solver."""
    
    def __init__(self, geometry, xs_data, options):
        super().__init__()
        self.geometry = geometry
        self.xs_data = xs_data
        self.options = options
        self.validator = DataValidator()
        
        if self._validation_enabled:
            self.validate()
    
    def _validate(self) -> ValidationResult:
        """Validate solver inputs."""
        return self.validator.validate_solver_inputs(
            self.geometry, self.xs_data, self.options
        )
    
    def solve_with_validation(self):
        """Solve with automatic output validation."""
        # Run solver
        k_eff, flux = self._solve_internal()
        power = self._compute_power(flux)
        
        # Validate outputs
        if self._validation_enabled:
            result = self.validator.validate_solution(
                k_eff, flux, power, self.options.power_target
            )
            
            if result.has_errors():
                raise ValueError(f"Solution validation failed:\n{result}")
        
        return k_eff, flux, power


# Utility functions for common validation patterns
def check_positive(value: float, name: str = "value"):
    """Quick check for positive values."""
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def check_range(value: float, min_val: float, max_val: float, 
                name: str = "value"):
    """Quick range check."""
    if not (min_val <= value <= max_val):
        raise ValueError(
            f"{name} must be in [{min_val}, {max_val}], got {value}"
        )


def check_normalized(arr: np.ndarray, tolerance: float = 1e-6,
                    name: str = "array"):
    """Check if array sums to 1."""
    total = np.sum(arr)
    if abs(total - 1.0) > tolerance:
        raise ValueError(
            f"{name} must sum to 1, got sum={total}"
        )


def check_physical_temperature(T: float, name: str = "temperature"):
    """Quick physical temperature check."""
    if T <= 0:
        raise ValueError(f"{name} below absolute zero: {T} K")
    if T > 4000:
        raise ValueError(f"{name} exceeds physical limits: {T} K")


# Context manager for temporary validation disable
class ValidationContext:
    """Context manager to temporarily disable validation."""
    
    def __init__(self, obj: ValidatedClass):
        self.obj = obj
        self.original_state = None
    
    def __enter__(self):
        self.original_state = self.obj._validation_enabled
        self.obj._validation_enabled = False
        return self.obj
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.obj._validation_enabled = self.original_state


# Example usage documentation
if __name__ == "__main__":
    from rich.console import Console
    console = Console()
    
    console.print("[bold cyan]Validation Integration Examples[/bold cyan]\n")
    
    # Example 1: Input validation decorator
    console.print("[bold]Example 1: Input Validation[/bold]")
    
    from smrforge.validation.validators import PhysicalValidator
    
    @validate_inputs(
        T=lambda T: PhysicalValidator.validate_temperature(T, min_T=273, max_T=3000),
        P=lambda P: PhysicalValidator.validate_pressure(P, min_P=1e5, max_P=10e6)
    )
    def calculate_density(T, P):
        """Calculate helium density."""
        R = 2077.0
        return P / (R * T)
    
    try:
        rho = calculate_density(1000.0, 7e6)
        console.print(f"  ✓ Valid: ρ = {rho:.4f} kg/m³")
    except ValueError as e:
        console.print(f"  ✗ Error: {e}")
    
    try:
        rho = calculate_density(-100.0, 7e6)  # Invalid temperature
    except ValueError as e:
        console.print(f"  ✗ Caught error: {e}")
    
    # Example 2: Output validation
    console.print("\n[bold]Example 2: Output Validation[/bold]")
    
    @validate_outputs(
        k_eff=lambda k: PhysicalValidator.validate_k_eff(k)
    )
    def mock_eigenvalue_solver():
        """Mock solver."""
        return {'k_eff': 1.045, 'iterations': 25}
    
    result = mock_eigenvalue_solver()
    console.print(f"  ✓ k_eff = {result['k_eff']:.6f}")
    
    # Example 3: Array validation
    console.print("\n[bold]Example 3: Array Validation[/bold]")
    
    flux = np.array([1e13, 2e13, 1.5e13, 1.2e13, 8e12])
    result = validate_array(flux, "flux", allow_negative=False, min_val=0)
    
    if result.valid:
        console.print("  ✓ Flux array valid")
    else:
        console.print("  ✗ Flux array has issues:")
        for issue in result.issues:
            console.print(f"    - {issue}")
    
    # Example 4: Quick checks
    console.print("\n[bold]Example 4: Quick Checks[/bold]")
    
    try:
        check_positive(1200.0, "temperature")
        console.print("  ✓ Temperature positive")
    except ValueError as e:
        console.print(f"  ✗ {e}")
    
    try:
        check_range(0.195, 0.0, 0.20, "enrichment")
        console.print("  ✓ Enrichment in range")
    except ValueError as e:
        console.print(f"  ✗ {e}")
    
    chi = np.array([0.6, 0.3, 0.08, 0.015, 0.004, 0.001])
    try:
        check_normalized(chi, name="fission_spectrum")
        console.print("  ✓ Spectrum normalized")
    except ValueError as e:
        console.print(f"  ✗ {e}")
    
    console.print("\n[bold green]Validation integration examples complete![/bold green]")
