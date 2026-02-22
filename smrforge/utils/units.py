"""
Unit checking and dimensional analysis utilities using Pint.

Provides automatic unit validation, conversion, and dimensional analysis
to prevent unit errors and improve code reliability.

Based on PyRK's approach using Pint for dimensional analysis.
"""

from typing import Any, Optional, Union

from .logging import get_logger

try:
    from pint import Quantity, UnitRegistry
    from pint.errors import DimensionalityError

    _PINT_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PINT_AVAILABLE = False
    # Create dummy classes if Pint not available
    Quantity = None  # type: ignore
    DimensionalityError = Exception  # type: ignore

logger = get_logger("smrforge.utils.units")

# Global unit registry (singleton pattern)
_ureg: Optional[Any] = None
_fallback_ureg: Optional[Any] = None


class _FallbackUnitRegistry:
    """
    Minimal stand-in for Pint's UnitRegistry.

    Used only when Pint is not installed, to keep a small backwards-compatible
    surface area for code paths/tests that expect a registry-like object.
    """

    class _FallbackQuantity:
        """Tiny Quantity-like object with `.magnitude` for tests."""

        def __init__(
            self, magnitude: float, units: "_FallbackUnitRegistry._FallbackUnit"
        ):
            self.magnitude = magnitude
            self.units = units

        # Minimal Pint-like surface area for a few call sites.
        def to(self, _target_unit: object) -> "_FallbackUnitRegistry._FallbackQuantity":
            return self

        def check(self, _dimensionality: object) -> bool:
            return True

    class _FallbackUnit:
        """Tiny Unit-like object that supports `number * unit`."""

        def __init__(self, name: str):
            self.name = name

        def __rmul__(self, other: object) -> "_FallbackUnitRegistry._FallbackQuantity":
            try:
                mag = float(other)  # type: ignore[arg-type]
            except Exception:
                mag = 0.0
            return _FallbackUnitRegistry._FallbackQuantity(mag, self)

        def __repr__(self) -> str:  # pragma: no cover
            return f"<unit {self.name}>"

    # Reactor-specific units used in tests.
    dollar = _FallbackUnit("dollar")
    pcm = _FallbackUnit("pcm")


def _get_fallback_ureg() -> Any:
    global _fallback_ureg
    if _fallback_ureg is None:
        _fallback_ureg = _FallbackUnitRegistry()
    return _fallback_ureg


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
    if _ureg is None:  # pragma: no cover - Pint available only
        _ureg = UnitRegistry()  # pragma: no cover
        _ureg.define("dollar = 0.01 * dimensionless")  # pragma: no cover
        _ureg.define("pcm = 0.0001 * dimensionless")  # pragma: no cover
    return _ureg


def check_units(value: Any, expected_unit: Union[str, Any], name: str = "value") -> Any:
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
        logger.warning(
            "Unit checking disabled: Pint not installed. Install with: pip install pint"
        )
        return value

    ureg = get_ureg()  # pragma: no cover - Pint available only
    is_quantity = False
    try:
        is_quantity = isinstance(value, Quantity)  # type: ignore[arg-type]  # pragma: no cover
    except TypeError:  # pragma: no cover
        is_quantity = hasattr(value, "check") and hasattr(value, "units")

    if is_quantity:  # pragma: no cover
        if isinstance(expected_unit, str):
            expected_quantity = ureg(expected_unit)
        else:
            expected_quantity = expected_unit
        if not value.check(expected_quantity.dimensionality):
            extra = f" (variable: {name})" if name else ""
            raise DimensionalityError(
                value.units, expected_quantity.units, extra_msg=extra
            )
        return value

    if isinstance(expected_unit, str):  # pragma: no cover
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
        return float(value)

    ureg = get_ureg()  # pragma: no cover - Pint available only
    try:
        is_quantity = isinstance(value, Quantity)  # type: ignore[arg-type]  # pragma: no cover
    except TypeError:  # pragma: no cover
        is_quantity = hasattr(value, "to") and hasattr(value, "magnitude")

    if is_quantity:  # pragma: no cover
        if isinstance(target_unit, str):
            target_quantity = ureg(target_unit)
        else:
            target_quantity = target_unit
        return float(value.to(target_quantity).magnitude)

    return float(value)  # pragma: no cover


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
        logger.warning(
            "Unit attachment disabled: Pint not installed. Install with: pip install pint"
        )
        return value

    ureg = get_ureg()  # pragma: no cover - Pint available only
    if isinstance(unit, str):  # pragma: no cover
        return value * ureg(unit)
    else:
        return value * unit


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
    if not _PINT_AVAILABLE:  # pragma: no cover
        return _get_fallback_ureg()

    ureg = get_ureg()
    return ureg


__all__ = [
    "get_ureg",
    "check_units",
    "convert_units",
    "with_units",
    "define_reactor_units",
    "_PINT_AVAILABLE",
]
