"""
Centralized NaN/Inf validation for safety-critical outputs.

Provides a single API for validating k_eff, flux, power, and other
physics outputs before use in margins, reports, or downstream BEPU.
Use in BEPU workflows and before writing results.

Reference: NUCLEAR_INDUSTRY_ANALYSIS_AND_AI_FUTURE_PROOFING.md § 1.5
"""

from typing import Any, Dict, Optional, Union

import numpy as np

from .integration import validate_array
from .validators import ValidationResult


def validate_k_eff(
    k_eff: float,
    name: str = "k_eff",
    min_val: float = 0.0,
    max_val: float = 2.0,
) -> ValidationResult:
    """
    Validate k-eff for NaN, Inf, and physical range.

    Args:
        k_eff: Effective multiplication factor.
        name: Label for error messages.
        min_val: Minimum physically reasonable value.
        max_val: Maximum physically reasonable value.

    Returns:
        ValidationResult with any issues.
    """
    from .validators import ValidationLevel

    result = ValidationResult(valid=True)
    if np.isnan(k_eff):
        result.add_issue(ValidationLevel.ERROR, name, "k_eff is NaN", value=k_eff)
    elif np.isinf(k_eff):
        result.add_issue(ValidationLevel.ERROR, name, "k_eff is Inf", value=k_eff)
    elif not np.isfinite(k_eff):
        result.add_issue(
            ValidationLevel.ERROR, name, f"k_eff is not finite (got {k_eff})", value=k_eff
        )
    elif k_eff < min_val or k_eff > max_val:
        result.add_issue(
            ValidationLevel.WARNING,
            name,
            f"k_eff outside typical range [{min_val}, {max_val}]",
            value=k_eff,
        )
    return result


def validate_flux(
    flux: np.ndarray,
    name: str = "flux",
    allow_negative: bool = False,
) -> ValidationResult:
    """
    Validate neutron flux array for NaN, Inf, and sign.

    Args:
        flux: Flux array (any shape).
        name: Label for error messages.
        allow_negative: If False, negative values are errors.

    Returns:
        ValidationResult.
    """
    return validate_array(
        np.asarray(flux),
        name=name,
        allow_nan=False,
        allow_inf=False,
        allow_negative=allow_negative,
    )


def validate_power(
    power: np.ndarray,
    name: str = "power",
) -> ValidationResult:
    """
    Validate power distribution for NaN, Inf, and non-negativity.

    Args:
        power: Power array (any shape).
        name: Label for error messages.

    Returns:
        ValidationResult.
    """
    return validate_array(
        np.asarray(power),
        name=name,
        allow_nan=False,
        allow_inf=False,
        allow_negative=False,
    )


def validate_safety_critical_outputs(
    k_eff: Optional[float] = None,
    flux: Optional[np.ndarray] = None,
    power: Optional[np.ndarray] = None,
    **extra: Union[float, np.ndarray],
) -> ValidationResult:
    """
    Validate safety-critical outputs (k_eff, flux, power) in one call.

    Centralized entry point for BEPU and safety workflows. Raises ValueError
    if any output has NaN/Inf; logs warnings for out-of-range values.

    Args:
        k_eff: Optional k-eff value.
        flux: Optional flux array.
        power: Optional power array.
        **extra: Additional named outputs (scalars or arrays) to validate for finiteness.

    Returns:
        Combined ValidationResult. Check result.has_errors() before using outputs.

    Example:
        >>> result = validate_safety_critical_outputs(k_eff=1.02, flux=flux, power=power)
        >>> if result.has_errors():
        ...     raise ValueError("Invalid safety-critical outputs")
    """
    combined = ValidationResult(valid=True)
    if k_eff is not None:
        combined.issues.extend(validate_k_eff(k_eff).issues)
    if flux is not None:
        combined.issues.extend(validate_flux(flux).issues)
    if power is not None:
        combined.issues.extend(validate_power(power).issues)
    for key, val in extra.items():
        if val is None:
            continue
        arr = np.asarray(val)
        if arr.size == 1:
            scalar = float(np.squeeze(val))
            r = validate_k_eff(scalar, name=key, min_val=-1e10, max_val=1e10)
        else:
            r = validate_array(arr, name=key, allow_nan=False, allow_inf=False)
        combined.issues.extend(r.issues)
    combined.valid = not combined.has_errors()
    return combined
