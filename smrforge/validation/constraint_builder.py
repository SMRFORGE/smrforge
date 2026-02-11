"""
Build ConstraintSet from a design point and target margins.

Given a reactor (or design point dict) and desired margins above/below limits,
produces a ConstraintSet that can be saved and used for validation/optimization.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..utils.logging import get_logger
from .constraints import ConstraintSet
from .safety_report import SafetyMarginReport

logger = get_logger("smrforge.validation.constraint_builder")


# Common constraint names and types used when inferring from design point
_DEFAULT_CONSTRAINT_SPEC = {
    "k_eff": ("min", ""),
    "min_k_eff": ("min", ""),
    "power_thermal_mw": ("min", "MW"),
    "max_power_density": ("max", "W/cm³"),
    "mean_power_density": ("max", "W/cm³"),
    "power_peak_factor": ("max", ""),
    "max_temperature": ("max", "K"),
    "max_burnup": ("max", "MWd/kg"),
    "flux_max": ("max", "1/cm²/s"),
    "flux_mean": ("max", "1/cm²/s"),
}


def constraint_set_from_design(
    design_point: Dict[str, float],
    target_margins: Dict[str, float],
    name: str = "from_design",
    description: str = "Constraint set derived from design point and target margins",
) -> ConstraintSet:
    """
    Build a ConstraintSet such that limits = design_value ± target_margin.

    For "min" type: limit = design_value - target_margin (so we require value >= limit).
    For "max" type: limit = design_value + target_margin (so we require value <= limit).

    Args:
        design_point: Dict of metric name -> current value (e.g. from get_design_point).
        target_margins: Dict of metric name -> margin (positive). Keys should match or
            use "min_k_eff" for k_eff. If a key is missing, that metric is skipped.
        name: Name for the ConstraintSet.
        description: Description string.

    Returns:
        ConstraintSet with limits set so that the design point satisfies limits with the given margins.
    """
    cs = ConstraintSet(name=name, description=description)
    for cname, margin in target_margins.items():
        value = design_point.get(cname)
        if value is None and cname == "min_k_eff":
            value = design_point.get("k_eff")
        if value is None or not isinstance(value, (int, float)):
            continue
        value = float(value)
        spec = _DEFAULT_CONSTRAINT_SPEC.get(cname, ("max", ""))
        ctype, unit = spec
        if ctype == "min":
            limit = value - margin  # require value >= limit
        else:
            limit = value + margin  # require value <= limit
        cs.add_constraint(cname, limit, ctype, unit, f"Target margin {margin}")
    return cs


def constraint_set_from_safety_report(
    report: Union[SafetyMarginReport, Dict[str, Any]],
    target_margins: Optional[Dict[str, float]] = None,
    name: str = "from_report",
) -> ConstraintSet:
    """
    Build a ConstraintSet from an existing safety margin report.

    Uses current values and (optionally) tightens limits by target_margins.
    If target_margins is None, uses the report's existing limits.

    Args:
        report: SafetyMarginReport or its to_dict().
        target_margins: Optional dict of constraint name -> extra margin (tighten limit by this).
        name: Constraint set name.

    Returns:
        ConstraintSet.
    """
    if hasattr(report, "to_dict"):
        report = report.to_dict()
    margins = report.get("margins", [])
    if not margins:
        return ConstraintSet(name=name, description="Empty from report")
    cs = ConstraintSet(name=name, description="From safety margin report")
    for m in margins:
        cname = m.get("name")
        limit = m.get("limit")
        ctype = "min" if "min" in str(cname).lower() else "max"
        unit = m.get("unit", "")
        if target_margins and cname in target_margins:
            delta = target_margins[cname]
            if ctype == "min":
                limit = limit - delta
            else:
                limit = limit + delta
        cs.add_constraint(cname, limit, ctype, unit, "")
    return cs
