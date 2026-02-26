"""
Helpful error message utilities for better user experience.

This module provides functions to generate user-friendly error messages
with suggestions and corrections, improving upon OpenMC's limitations
in error messaging. Integrates with smrforge.utils.error_codes for
SMR-Exxx codes and doc links.
"""

from typing import Any, Dict, List, Optional, Tuple

from .error_codes import format_error, get_error_code


def format_validation_error(
    field_name: str,
    value: Any,
    error_type: str,
    suggestions: Optional[List[str]] = None,
) -> str:
    """
    Format a helpful validation error message with suggestions.

    Args:
        field_name: Name of the field with the error
        value: The invalid value provided
        error_type: Type of validation error (e.g., "negative", "out_of_range")
        suggestions: Optional list of suggestions

    Returns:
        Formatted error message string
    """
    base_msg = f"Invalid {field_name}: {value}"

    # Add type-specific suggestions
    if error_type == "negative" and isinstance(value, (int, float)):
        if field_name in ["power_mw", "power_thermal"]:
            return (
                f"{base_msg}. Power must be > 0 (in MW for power_mw, or W for power_thermal). "
                f"Did you mean {abs(value)}?"
            )
        elif field_name in ["temperature", "inlet_temperature", "outlet_temperature"]:
            return (
                f"{base_msg}. Temperature must be positive (in Kelvin). "
                f"Did you mean {abs(value)} K?"
            )
        elif field_name == "enrichment":
            return (
                f"{base_msg}. Enrichment must be 0-1 (fraction, not percent). "
                f"Did you mean {abs(value)} or {abs(value) / 100}?"
            )

    elif error_type == "out_of_range" and isinstance(value, (int, float)):
        if field_name == "enrichment" and value > 1.0:
            return (
                f"{base_msg}. Enrichment must be 0-1 (fraction, not percent). "
                f"For 19.5%, use 0.195. Did you mean {value / 100}?"
            )
        elif field_name == "enrichment" and value < 0:
            return (
                f"{base_msg}. Enrichment must be >= 0. "
                f"Did you mean {abs(value)} or {abs(value) / 100}?"
            )

    elif error_type == "temperature_order":
        return (
            f"{base_msg}. Inlet temperature must be less than outlet temperature. "
            f"Check your temperature values."
        )

    elif error_type == "missing_required":
        return (
            f"Missing required field: {field_name}. "
            f"Please provide a value for {field_name}."
        )

    # Add custom suggestions if provided
    if suggestions:
        return f"{base_msg}. Suggestions: " + "; ".join(suggestions)

    return base_msg


def suggest_correction(value: Any, field_name: str) -> Optional[str]:
    """
    Suggest a correction for common input errors.

    Args:
        value: The value provided
        field_name: Name of the field

    Returns:
        Suggested corrected value or None
    """
    # Common mistake: enrichment as percentage instead of fraction
    if field_name == "enrichment" and isinstance(value, (int, float)):
        if 1.0 < value <= 100.0:
            return f"Did you mean {value / 100}? (Enrichment should be fraction, not percent)"
        elif value < 0:
            return f"Did you mean {abs(value)}? (Enrichment cannot be negative)"

    # Common mistake: power in wrong units
    if field_name == "power_mw" and isinstance(value, (int, float)):
        if value > 0 and value < 1e-6:  # Very small, might be in W
            return f"Did you mean {value * 1e6} MW? (power_mw expects MW, not W)"

    # Common mistake: temperature in Celsius instead of Kelvin
    if "temperature" in field_name.lower() and isinstance(value, (int, float)):
        if 200 <= value <= 1000:  # Could be Celsius
            return f"Did you mean {value + 273.15} K? (Temperature should be in Kelvin, not Celsius)"
        elif value < 0:
            return f"Did you mean {abs(value)} K? (Temperature must be positive)"

    return None


def format_cross_section_error(
    sigma_a: float, sigma_t: float, material_id: int, group: int
) -> str:
    """
    Format helpful error message for cross-section validation.

    Args:
        sigma_a: Absorption cross section
        sigma_t: Total cross section
        material_id: Material ID
        group: Energy group

    Returns:
        Formatted error message
    """
    return (
        f"Invalid cross sections for material {material_id}, group {group}: "
        f"σ_a ({sigma_a:.6f}) > σ_t ({sigma_t:.6f}). "
        f"Absorption cross section cannot exceed total cross section. "
        f"Check your cross-section data."
    )


def format_solver_error(
    error_msg: str,
    solver_type: str = "diffusion",
    suggestions: Optional[List[str]] = None,
    use_error_code: bool = True,
) -> str:
    """
    Format helpful solver error message with optional SMR-Exxx code and doc link.

    Args:
        error_msg: Original error message
        solver_type: Type of solver (diffusion, monte_carlo, etc.)
        suggestions: Optional list of suggestions
        use_error_code: If True, prepend SMR-E001/E002 and doc link

    Returns:
        Formatted error message
    """
    base_msg = f"{solver_type.capitalize()} solver error: {error_msg}"
    extra_suggestions: List[str] = []

    if "convergence" in error_msg.lower() or "converged" in error_msg.lower():
        extra_suggestions.extend(
            [
                "Increase max_iterations",
                "Relax tolerance (e.g., 1e-5 instead of 1e-6)",
                "Check cross-section data validity",
                "Verify geometry is physical",
            ]
        )
        if use_error_code:
            return format_error("E001", detail=error_msg, suggestions_extra=extra_suggestions)

    if "nan" in error_msg.lower() or "inf" in error_msg.lower():
        extra_suggestions.extend(
            [
                "Check for negative cross sections",
                "Verify all input values are finite",
                "Check geometry mesh is valid",
                "Ensure power density is positive",
            ]
        )
        if use_error_code:
            return format_error("E002", detail=error_msg, suggestions_extra=extra_suggestions)

    if suggestions:
        extra_suggestions.extend(suggestions)

    if extra_suggestions:
        return f"{base_msg}\nRecovery suggestions:\n  - " + "\n  - ".join(extra_suggestions)

    return base_msg


def suggest_install_pro(feature: str = "", extra: str = "openmc") -> str:
    """
    Return a helpful message suggesting SMRForge Pro installation.

    Args:
        feature: Optional feature name (e.g. "OpenMC tally visualization")
        extra: Optional pip extra to suggest (e.g. "openmc", "ai", "reporting")

    Returns:
        Formatted suggestion string
    """
    base = "SMRForge Pro is required for this feature."
    if feature:
        base = f"{feature} requires SMRForge Pro."
    cmd = f"pip install smrforge-pro[{extra}]" if extra else "pip install smrforge-pro"
    return f"{base} Install with: {cmd}"


def format_geometry_error(
    error_msg: str, geometry_type: str = "prismatic", use_error_code: bool = True
) -> str:
    """
    Format helpful geometry error message with optional SMR-E008.

    Args:
        error_msg: Original error message
        geometry_type: Type of geometry
        use_error_code: If True, use SMR-E008 with doc link

    Returns:
        Formatted error message
    """
    base_msg = f"{geometry_type.capitalize()} geometry error: {error_msg}"
    suggestions: List[str] = []

    if "mesh" in error_msg.lower():
        suggestions.extend(
            [
                "Call geometry.build_mesh() before solving",
                "Check mesh dimensions (n_radial, n_axial) are positive",
                "Verify geometry dimensions (core_height, core_diameter) are valid",
            ]
        )
    elif "material" in error_msg.lower():
        suggestions.extend(
            [
                "Check material_map is valid",
                "Verify cross-section data matches material IDs",
            ]
        )

    if use_error_code and suggestions:
        return format_error("E008", detail=error_msg, suggestions_extra=suggestions)
    if suggestions:
        return f"{base_msg}\nRecovery suggestions:\n  - " + "\n  - ".join(suggestions)
    return base_msg
