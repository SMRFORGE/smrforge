# smrforge/validation/integration.py
"""
Decorators and utilities for automatic validation integration.
Apply to functions/classes to enforce validation rules.
"""

import functools
import inspect
from typing import Any, Callable, Dict, Optional

import numpy as np

from .validators import (
    DataValidator,
    ValidationIssue,
    ValidationLevel,
    ValidationResult,
)


def validate_inputs(**validators: Callable[[Any], ValidationResult]) -> Callable[[Callable], Callable]:
    """
    Decorator to validate function inputs automatically.
    
    Applies validation functions to function arguments before the function
    is called. Raises ValueError if validation fails, or issues warnings
    for validation issues at the WARNING level.
    
    Args:
        **validators: Keyword arguments mapping parameter names to validation
            functions. Each validator function should take the parameter value
            and return a ValidationResult object.
    
    Returns:
        Decorated function with input validation enabled.
    
    Raises:
        ValueError: If any parameter fails validation (ERROR or CRITICAL level).
        UserWarning: If any parameter has validation warnings (WARNING level).
    
    Example:
        >>> from smrforge.validation.validators import PhysicalValidator
        >>> 
        >>> @validate_inputs(
        ...     temperature=lambda T: PhysicalValidator.validate_temperature(T, min_T=273, max_T=3000),
        ...     pressure=lambda P: PhysicalValidator.validate_pressure(P, min_P=1e5, max_P=10e6)
        ... )
        ... def calculate_density(temperature, pressure):
        ...     R = 2077.0  # Helium specific gas constant
        ...     return pressure / (R * temperature)
        >>> 
        >>> # Valid call
        >>> rho = calculate_density(1000.0, 7e6)  # Returns density
        >>> 
        >>> # Invalid call - raises ValueError
        >>> rho = calculate_density(-100.0, 7e6)  # Raises ValueError: temperature < min_T
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
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
                error_msgs = [
                    str(i)
                    for i in combined_result.issues
                    if i.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]
                ]
                raise ValueError(f"Validation failed:\n" + "\n".join(error_msgs))

            # Warn if warnings
            warnings = [
                i for i in combined_result.issues if i.level == ValidationLevel.WARNING
            ]
            if warnings:
                import warnings as warn_module

                for issue in warnings:
                    warn_module.warn(str(issue), UserWarning)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_outputs(**validators: Callable[[Any], ValidationResult]) -> Callable[[Callable], Callable]:
    """
    Decorator to validate function outputs automatically.
    
    Applies validation functions to function return values after the function
    executes. Supports dictionary returns (validate by key) and tuple returns
    (validate by position). Raises ValueError if validation fails.
    
    Args:
        **validators: Keyword arguments mapping output names to validation
            functions. For dictionary returns, keys should match dictionary keys.
            For tuple returns, validators are applied in order.
            Each validator function should take the output value and return a
            ValidationResult object.
    
    Returns:
        Decorated function with output validation enabled.
    
    Raises:
        ValueError: If any output fails validation (ERROR or CRITICAL level).
    
    Example:
        >>> from smrforge.validation.validators import PhysicalValidator
        >>> 
        >>> @validate_outputs(
        ...     k_eff=lambda k: PhysicalValidator.validate_k_eff(k),
        ...     flux=lambda f: PhysicalValidator.validate_flux(f)
        ... )
        ... def solve_eigenvalue():
        ...     return {'k_eff': 1.05, 'flux': np.array([1e13, 2e13, ...])}
        >>> 
        >>> # Valid output
        >>> result = solve_eigenvalue()  # Returns validated result
        >>> 
        >>> # Invalid output - raises ValueError
        >>> @validate_outputs(k_eff=lambda k: PhysicalValidator.validate_k_eff(k))
        ... def bad_solver():
        ...     return {'k_eff': -1.0}  # Negative k_eff is invalid
        >>> result = bad_solver()  # Raises ValueError
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
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


def validate_array(
    arr: np.ndarray,
    name: str = "array",
    allow_negative: bool = False,
    allow_nan: bool = False,
    allow_inf: bool = False,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
) -> ValidationResult:
    """
    Validate numpy array properties.
    
    Performs comprehensive validation checks on a NumPy array including
    type checking, emptiness, NaN/Inf detection, sign constraints, and
    value range constraints. Returns a ValidationResult with any issues found.
    
    Args:
        arr: NumPy array to validate.
        name: Name of the array (used in error messages). Defaults to "array".
        allow_negative: If False, raises error if any values are negative.
        allow_nan: If False, raises error if any values are NaN.
        allow_inf: If False, raises error if any values are infinite.
        min_val: Optional minimum allowed value. Raises error if any value < min_val.
        max_val: Optional maximum allowed value. Raises error if any value > max_val.
    
    Returns:
        ValidationResult object with valid=True if all checks pass, or
        valid=False with issues list if problems are found.
    
    Example:
        >>> flux = np.array([1e13, 2e13, 1.5e13, 1.2e13, 8e12])
        >>> result = validate_array(
        ...     flux,
        ...     name="neutron_flux",
        ...     allow_negative=False,
        ...     min_val=0.0
        ... )
        >>> if result.valid:
        ...     print("Flux array is valid")
        ... else:
        ...     for issue in result.issues:
        ...         print(f"Issue: {issue}")
    """
    result = ValidationResult(valid=True)

    if not isinstance(arr, np.ndarray):
        result.add_issue(
            ValidationLevel.ERROR, name, "Not a numpy array", value=type(arr)
        )
        return result

    if arr.size == 0:
        result.add_issue(ValidationLevel.WARNING, name, "Empty array")
        return result

    if not allow_nan and np.any(np.isnan(arr)):
        result.add_issue(
            ValidationLevel.ERROR, name, f"Contains {np.sum(np.isnan(arr))} NaN values"
        )

    if not allow_inf and np.any(np.isinf(arr)):
        result.add_issue(
            ValidationLevel.ERROR, name, f"Contains {np.sum(np.isinf(arr))} Inf values"
        )

    if not allow_negative and np.any(arr < 0):
        result.add_issue(
            ValidationLevel.ERROR,
            name,
            f"Contains {np.sum(arr < 0)} negative values",
            value=f"min={np.min(arr)}",
        )

    if min_val is not None and np.any(arr < min_val):
        result.add_issue(
            ValidationLevel.WARNING,
            name,
            f"Values below minimum",
            value=f"min={np.min(arr)}",
            expected=f">= {min_val}",
        )

    if max_val is not None and np.any(arr > max_val):
        result.add_issue(
            ValidationLevel.WARNING,
            name,
            f"Values above maximum",
            value=f"max={np.max(arr)}",
            expected=f"<= {max_val}",
        )

    return result


class ValidatedClass:
    """
    Base class for classes that need automatic validation.
    
    Provides a framework for classes that require validation of their state.
    Subclasses should override the _validate() method to implement custom
    validation logic. Validation can be enabled/disabled and run manually
    or automatically (e.g., on object construction).
    
    Attributes:
        _validation_enabled: Boolean flag controlling whether validation
            is active (can be toggled with enable_validation/disable_validation).
        _last_validation: Most recent ValidationResult from validate() call.
    
    Example:
        >>> class ValidatedReactor(ValidatedClass):
        ...     def __init__(self, power, temperature):
        ...         super().__init__()
        ...         self.power = power
        ...         self.temperature = temperature
        ...         if self._validation_enabled:
        ...             self.validate()
        ...     
        ...     def _validate(self) -> ValidationResult:
        ...         result = ValidationResult(valid=True)
        ...         if self.power < 0:
        ...             result.add_issue(ValidationLevel.ERROR, "power", "Must be positive")
        ...         if self.temperature < 273:
        ...             result.add_issue(ValidationLevel.ERROR, "temperature", "Below absolute zero")
        ...         return result
    """

    def __init__(self):
        """
        Initialize validated class.
        
        Sets up validation infrastructure with validation enabled by default.
        """
        self._validation_enabled = True
        self._last_validation: Optional[ValidationResult] = None

    def _validate(self) -> ValidationResult:
        """
        Override this method to define validation rules.
        
        Subclasses should implement this method to perform validation checks
        on the object's state. This method is called by validate().
        
        Returns:
            ValidationResult object indicating whether validation passed
            and listing any issues found.
        """
        return ValidationResult(valid=True)

    def validate(self, raise_on_error: bool = True) -> ValidationResult:
        """
        Run validation checks on the object.
        
        Calls _validate() to perform validation and stores the result.
        Optionally raises ValueError if validation fails.
        
        Args:
            raise_on_error: If True, raises ValueError if validation fails
                (has errors at ERROR or CRITICAL level). If False, returns
                result without raising.
        
        Returns:
            ValidationResult object with validation status and any issues.
        
        Raises:
            ValueError: If raise_on_error=True and validation fails.
        
        Example:
            >>> obj = ValidatedClass()
            >>> result = obj.validate(raise_on_error=False)
            >>> if not result.valid:
            ...     print("Validation issues:", result.issues)
        """
        result = self._validate()
        self._last_validation = result

        if raise_on_error and result.has_errors():
            raise ValueError(f"Validation failed:\n{result}")

        return result

    def disable_validation(self):
        """
        Disable automatic validation (use with caution!).
        
        Turns off validation checks. Useful for performance-critical code
        or when constructing objects in a temporary invalid state that will
        be corrected before use.
        
        Warning:
            Disabling validation can lead to runtime errors if invalid data
            is used. Only disable when absolutely necessary and re-enable
            as soon as possible.
        """
        self._validation_enabled = False

    def enable_validation(self):
        """
        Re-enable automatic validation.
        
        Turns validation checks back on after disable_validation() has been
        called. Validation will be active for subsequent validate() calls.
        """
        self._validation_enabled = True


# Example integration with existing classes
class ValidatedReactorSpec(ValidatedClass):
    """Example of validated reactor specification."""

    def __init__(self, spec: Any) -> None:
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

    def __init__(self, geometry: Any, xs_data: Any, options: Any) -> None:
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

    def solve_with_validation(self) -> tuple[float, np.ndarray, np.ndarray]:
        """Solve with automatic output validation."""
        # Run solver
        k_eff, flux = self._solve_internal()  # type: ignore
        power = self._compute_power(flux)  # type: ignore

        # Validate outputs
        if self._validation_enabled:
            result = self.validator.validate_solution(
                k_eff, flux, power, self.options.power_target
            )

            if result.has_errors():
                raise ValueError(f"Solution validation failed:\n{result}")

        return k_eff, flux, power


# Utility functions for common validation patterns
def check_positive(value: float, name: str = "value") -> None:
    """Quick check for positive values."""
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def check_range(value: float, min_val: float, max_val: float, name: str = "value") -> None:
    """Quick range check."""
    if not (min_val <= value <= max_val):
        raise ValueError(f"{name} must be in [{min_val}, {max_val}], got {value}")


def check_normalized(arr: np.ndarray, tolerance: float = 1e-6, name: str = "array") -> None:
    """Check if array sums to 1."""
    total = np.sum(arr)
    if abs(total - 1.0) > tolerance:
        raise ValueError(f"{name} must sum to 1, got sum={total}")


def check_physical_temperature(T: float, name: str = "temperature") -> None:
    """Quick physical temperature check."""
    if T <= 0:
        raise ValueError(f"{name} below absolute zero: {T} K")
    if T > 4000:
        raise ValueError(f"{name} exceeds physical limits: {T} K")


# Context manager for temporary validation disable
class ValidationContext:
    """Context manager to temporarily disable validation."""

    def __init__(self, obj: ValidatedClass) -> None:
        self.obj = obj
        self.original_state: Optional[bool] = None

    def __enter__(self) -> ValidatedClass:
        self.original_state = self.obj._validation_enabled
        self.obj._validation_enabled = False
        return self.obj

    def __exit__(
        self, 
        exc_type: Optional[type[BaseException]], 
        exc_val: Optional[BaseException], 
        exc_tb: Optional[Any]
    ) -> None:
        if self.original_state is not None:
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
        P=lambda P: PhysicalValidator.validate_pressure(P, min_P=1e5, max_P=10e6),
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

    @validate_outputs(k_eff=lambda k: PhysicalValidator.validate_k_eff(k))
    def mock_eigenvalue_solver():
        """Mock solver."""
        return {"k_eff": 1.045, "iterations": 25}

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

    console.print(
        "\n[bold green]Validation integration examples complete![/bold green]"
    )
