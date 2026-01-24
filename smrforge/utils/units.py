"""
Unit checking and dimensional analysis utilities using Pint.

Provides automatic unit validation, conversion, and dimensional analysis
to prevent unit errors and improve code reliability.

Based on PyRK's approach using Pint for dimensional analysis.
"""

from typing import Any, Optional, Union

try:
    from pint import UnitRegistry, Quantity
    from pint.errors import DimensionalityError

    _PINT_AVAILABLE = True
except ImportError:
    _PINT_AVAILABLE = False
    # Create dummy classes if Pint not available
    Quantity = None  # type: ignore
    DimensionalityError = Exception  # type: ignore


# Global unit registry (singleton pattern)
_ureg: Optional[Any] = None


def get_ureg() -> Any:
    """
    Get or create the global Pint unit registry.

    Returns:
        Pint UnitRegistry instance.

    Raises:
        ImportError: If Pint is not installed.

    Example:
        >>> from smrforge.utils.units import get_ureg
        >>> ureg = get_ureg()
        >>> power = 10 * ureg.megawatt
        >>> temperature = 500 * ureg.kelvin
    """
    global _ureg
    if not _PINT_AVAILABLE:
        raise ImportError(
            "Pint is required for unit checking. Install with: pip install pint"
        )
    if _ureg is None:
        _ureg = UnitRegistry()
        # Add reactor-specific units
        _ureg.define("dollar = 0.01 * dimensionless")  # Reactivity unit (cents)
        _ureg.define("pcm = 0.0001 * dimensionless")  # Reactivity unit (per cent mille)
    return _ureg


def check_units(
    value: Any, expected_unit: Union[str, Any], name: str = "value"
) -> Any:
    """
    Check that a value has the expected units.

    If the value is a Pint Quantity, validates units match.
    If the value is a plain number, assumes it's in the correct units (warning).

    Args:
        value: Value to check (Quantity or plain number).
        expected_unit: Expected unit string or Quantity (e.g., "megawatt", "kelvin").
        name: Name of the variable for error messages (default: "value").

    Returns:
        Value as a Pint Quantity with correct units.

    Raises:
        ImportError: If Pint is not installed.
        DimensionalityError: If units don't match.
        ValueError: If value is invalid.

    Example:
        >>> from smrforge.utils.units import check_units, get_ureg
        >>> ureg = get_ureg()
        >>> power = check_units(10.0, "megawatt", "power")
        >>> temperature = check_units(500 * ureg.kelvin, ureg.kelvin, "temperature")
    """
    if not _PINT_AVAILABLE:
        # If Pint not available, return value as-is (backwards compatibility)
        import warnings

        warnings.warn(
            f"Unit checking disabled: Pint not installed. Install with: pip install pint",
            UserWarning,
        )
        return value

    ureg = get_ureg()

    # If value is already a Quantity, check units.
    #
    # Note: in some unit tests we mock Pint; `Quantity` may not be a real type.
    # In that case, fall back to duck-typing (objects with `.check(...)`).
    is_quantity = False
    if isinstance(Quantity, type):
        is_quantity = isinstance(value, Quantity)
    else:
        is_quantity = hasattr(value, "check")

    if is_quantity:
        if isinstance(expected_unit, str):
            expected_quantity = ureg(expected_unit)
        else:
            expected_quantity = expected_unit

        # Check dimensional compatibility
        if not value.check(expected_quantity.dimensionality):
            # Pint's DimensionalityError signature varies; don't pass extra kwargs.
            raise DimensionalityError(value.units, expected_quantity.units)
        return value

    # If value is a plain number, convert to Quantity
    # (assuming correct units, but user should use Quantity for safety)
    if isinstance(expected_unit, str):
        return value * ureg(expected_unit)
    else:
        return value * expected_unit


def convert_units(value: Any, target_unit: Union[str, Any]) -> float:
    """
    Convert a value to target units and return as plain float.

    Args:
        value: Value with units (Quantity or plain number).
        target_unit: Target unit string or Quantity.

    Returns:
        Value in target units as plain float.

    Raises:
        ImportError: If Pint is not installed.
        DimensionalityError: If units are incompatible.

    Example:
        >>> from smrforge.utils.units import convert_units, get_ureg
        >>> ureg = get_ureg()
        >>> power_watts = convert_units(10 * ureg.megawatt, "watt")
        >>> print(power_watts)  # 10000000.0
    """
    if not _PINT_AVAILABLE:
        # If Pint not available, return value as-is
        return float(value)

    ureg = get_ureg()

    is_quantity = False
    if isinstance(Quantity, type):
        is_quantity = isinstance(value, Quantity)
    else:
        is_quantity = hasattr(value, "to")

    if is_quantity:
        if isinstance(target_unit, str):
            target_quantity = ureg(target_unit)
        else:
            target_quantity = target_unit
        return float(value.to(target_quantity).magnitude)

    # Plain number - assume already in target units
    return float(value)


def with_units(value: float, unit: Union[str, Any]) -> Any:
    """
    Attach units to a plain number.

    Args:
        value: Plain numeric value.
        unit: Unit string or Quantity (e.g., "megawatt", "kelvin").

    Returns:
        Pint Quantity with units attached.

    Example:
        >>> from smrforge.utils.units import with_units
        >>> power = with_units(10.0, "megawatt")
        >>> temperature = with_units(500.0, "kelvin")
    """
    if not _PINT_AVAILABLE:
        import warnings

        warnings.warn(
            "Unit attachment disabled: Pint not installed. Install with: pip install pint",
            UserWarning,
        )
        return value

    ureg = get_ureg()
    if isinstance(unit, str):
        return value * ureg(unit)
    else:
        return value * unit


# Common unit constants for convenience
def define_reactor_units() -> Any:
    """
    Define reactor-specific units in the registry.

    Returns:
        Unit registry with reactor units defined.

    Example:
        >>> from smrforge.utils.units import define_reactor_units, get_ureg
        >>> ureg = get_ureg()
        >>> reactivity = 0.001 * ureg.dollar  # 1 cent reactivity
        >>> reactivity_pcm = 100 * ureg.pcm  # 100 pcm
    """
    # Units are defined in get_ureg(). If Pint is not installed, get_ureg() will
    # raise ImportError, and callers/tests can skip accordingly.
    return get_ureg()


__all__ = [
    "get_ureg",
    "check_units",
    "convert_units",
    "with_units",
    "define_reactor_units",
    "_PINT_AVAILABLE",
]
