"""
Requirements → constraints: parse structured requirements (YAML or dict) into ConstraintSet.

Minimal DSL: list of constraints with name, min/max, value or (min, max).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..utils.logging import get_logger
from .constraints import ConstraintSet

logger = get_logger("smrforge.validation.requirements_parser")

try:
    import yaml

    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


def parse_requirements_to_constraint_set(
    spec: Union[Dict[str, Any], Path, str],
    name: str = "from_requirements",
    description: str = "Constraint set from requirements spec",
) -> ConstraintSet:
    """
    Parse a requirements spec into a ConstraintSet.

    Spec format (dict or YAML/JSON file):
      requirements:
        - name: k_eff
          min: 0.98
          max: 1.05
          unit: ""
        - name: max_power_density
          max: 100
          unit: "W/cm³"
    Or shorthand:
      requirements:
        - name: min_k_eff
          limit: 1.0
          type: min
          unit: ""

    Args:
        spec: Dict with "requirements" list, or path to YAML/JSON file.
        name: Constraint set name.
        description: Description.

    Returns:
        ConstraintSet.
    """
    if isinstance(spec, (Path, str)):
        path = Path(spec)
        if not path.exists():
            raise FileNotFoundError(f"Requirements file not found: {path}")
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() in (".yaml", ".yml"):
            if not _YAML_AVAILABLE:
                raise ImportError(
                    "PyYAML required for YAML requirements: pip install pyyaml"
                )
            data = yaml.safe_load(text)
        else:
            import json

            data = json.loads(text)
        spec = data
        logger.info("Loaded requirements from %s", path)
    if not isinstance(spec, dict):
        raise ValueError("spec must be dict or path to YAML/JSON")
    req_list = spec.get("requirements", spec.get("constraints", []))
    if not isinstance(req_list, list):
        raise ValueError("spec must contain 'requirements' or 'constraints' list")
    cs = ConstraintSet(name=name, description=description)
    for r in req_list:
        if not isinstance(r, dict):
            continue
        cname = r.get("name")
        if not cname:
            continue
        unit = r.get("unit", "")
        if "limit" in r and "type" in r:
            limit = float(r["limit"])
            ctype = r["type"]
            cs.add_constraint(cname, limit, ctype, unit, r.get("description", ""))
        elif "min" in r and "max" in r:
            # Create two constraints: min and max
            lo, hi = float(r["min"]), float(r["max"])
            cs.add_constraint(
                f"min_{cname}" if cname != "k_eff" else "min_k_eff", lo, "min", unit, ""
            )
            cs.add_constraint(f"max_{cname}", hi, "max", unit, "")
        elif "min" in r:
            cs.add_constraint(
                cname if cname.startswith("min_") else f"min_{cname}",
                float(r["min"]),
                "min",
                unit,
                "",
            )
        elif "max" in r:
            cs.add_constraint(
                cname if cname.startswith("max_") else f"max_{cname}",
                float(r["max"]),
                "max",
                unit,
                "",
            )
    return cs
