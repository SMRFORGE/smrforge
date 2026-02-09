"""
Design space atlas: catalog of presets/variants with design point and safety report.

Builds an index of designs (e.g. all presets or a list of variants) with
power class, coolant, pass/fail, and paths to design_point and safety_report,
so users can filter and compare.
"""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.logging import get_logger

logger = get_logger("smrforge.workflows.atlas")


@dataclass
class AtlasEntry:
    """Single design entry in the atlas."""
    design_id: str  # preset name or variant name
    power_mw: float = 0.0
    coolant: str = ""
    reactor_type: str = ""
    passed: bool = False
    design_point_path: Optional[str] = None
    safety_report_path: Optional[str] = None
    metrics_summary: Dict[str, float] = field(default_factory=dict)


def build_atlas(
    output_dir: Path,
    presets: Optional[List[str]] = None,
    create_reactor: Optional[Any] = None,
    get_design_point: Optional[Any] = None,
    safety_margin_report_fn: Optional[Any] = None,
) -> List[AtlasEntry]:
    """
    Build a design space atlas: run design point + safety report for each preset and save index.

    Args:
        output_dir: Directory to write design_point.json and safety_report.json per design, plus index.json.
        presets: List of preset names (e.g. ["valar-10", "nuscale"]). If None, tries to use list_presets().
        create_reactor: Function (preset_name) -> reactor. If None, imports smrforge.convenience.create_reactor.
        get_design_point: Function (reactor) -> dict. If None, imports from convenience.
        safety_margin_report_fn: Function (reactor, ...) -> SafetyMarginReport. If None, imports from safety_report.

    Returns:
        List of AtlasEntry (also written to output_dir / "atlas_index.json").
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if create_reactor is None:
        from ..convenience import create_reactor as _cr
        create_reactor = _cr
    if get_design_point is None:
        from ..convenience import get_design_point as _gdp
        get_design_point = _gdp
    if safety_margin_report_fn is None:
        from ..validation.safety_report import safety_margin_report as _smr
        safety_margin_report_fn = _smr

    if presets is None:
        try:
            from ..convenience import list_presets
            presets = list(list_presets())
        except Exception:  # pragma: no cover
            presets = []

    entries: List[AtlasEntry] = []
    for design_id in presets:
        try:
            reactor = create_reactor(design_id)
            point = get_design_point(reactor)
            report = safety_margin_report_fn(reactor)
        except Exception as e:  # pragma: no cover
            logger.warning("Atlas: failed for %s: %s", design_id, e)
            entries.append(AtlasEntry(design_id=design_id, passed=False, metrics_summary={"error": str(e)}))
            continue
        power_mw = point.get("power_thermal_mw", 0.0)
        coolant = getattr(getattr(reactor, "spec", None), "coolant", "") or ""
        reactor_type = getattr(getattr(reactor, "spec", None), "reactor_type", "") or ""
        dp_path = output_dir / f"design_point_{design_id.replace('/', '_')}.json"
        sr_path = output_dir / f"safety_report_{design_id.replace('/', '_')}.json"
        dp_path.write_text(json.dumps(point, indent=2), encoding="utf-8")
        sr_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
        entries.append(AtlasEntry(
            design_id=design_id,
            power_mw=power_mw,
            coolant=coolant,
            reactor_type=reactor_type,
            passed=report.passed,
            design_point_path=str(dp_path),
            safety_report_path=str(sr_path),
            metrics_summary={k: v for k, v in point.items() if isinstance(v, (int, float))},
        ))
    index_path = output_dir / "atlas_index.json"
    index_data = {
        "atlas_entries": [asdict(e) for e in entries],
        "n_designs": len(entries),
        "n_passed": sum(1 for e in entries if e.passed),
    }
    index_path.write_text(json.dumps(index_data, indent=2), encoding="utf-8")
    return entries


def filter_atlas(
    entries: List[AtlasEntry],
    power_min: Optional[float] = None,
    power_max: Optional[float] = None,
    coolant: Optional[str] = None,
    passed_only: bool = False,
) -> List[AtlasEntry]:
    """Filter atlas entries by power range, coolant, and pass/fail."""
    out = list(entries)
    if power_min is not None:
        out = [e for e in out if e.power_mw >= power_min]
    if power_max is not None:
        out = [e for e in out if e.power_mw <= power_max]
    if coolant:
        out = [e for e in out if coolant.lower() in (e.coolant or "").lower()]
    if passed_only:
        out = [e for e in out if e.passed]
    return out
