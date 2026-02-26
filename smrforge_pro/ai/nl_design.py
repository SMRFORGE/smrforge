"""
Natural-language reactor design (Pro).

Parse intent like "10 MW HTGR with k-eff 1.0-1.05, enrichment <20%, 20-year cycle"
and produce a reactor spec + run analysis.

Optional: plug in LLM for advanced parsing. This module uses keyword/pattern extraction
as the default, with a hook for external NL parsers.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from smrforge.validation.models import ReactorSpecification, ReactorType


@dataclass
class NLDesignResult:
    """Result of natural-language design parsing and analysis."""

    spec: ReactorSpecification
    intent_parsed: Dict[str, Any]
    analysis: Optional[Dict[str, Any]] = None
    constraints_met: Optional[bool] = None
    message: str = ""


def _extract_power_mw(text: str) -> Optional[float]:
    """Extract power in MW from text (e.g. '10 MW', '350 MWth', '77 MWe')."""
    # Match: number followed by MW, MWth, MWe, MWthermal
    m = re.search(r"(\d+(?:\.\d+)?)\s*MW(?:th|e|thermal)?", text, re.I)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+)\s*MW", text, re.I)
    if m:
        return float(m.group(1))
    return None


def _extract_enrichment(text: str) -> Optional[float]:
    """Extract enrichment as fraction (e.g. '19.5%', 'enrichment <20%', '0.195')."""
    # percent: "19.5%", "< 20%", "under 20%"
    m = re.search(r"(?:<|under|below)?\s*(\d+(?:\.\d+)?)\s*%", text, re.I)
    if m:
        return float(m.group(1)) / 100.0
    # fraction
    m = re.search(r"enrichment\s*[=:]\s*(\d+\.?\d*)", text, re.I)
    if m:
        v = float(m.group(1))
        return v if v <= 1 else v / 100
    return None


def _extract_keff_range(text: str) -> Optional[tuple]:
    """Extract k-eff range (min, max) from text."""
    # "k-eff 1.0-1.05", "keff between 1.0 and 1.05"
    m = re.search(r"k-?eff\s*(?:between\s+)?(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)", text, re.I)
    if m:
        return (float(m.group(1)), float(m.group(2)))
    m = re.search(r"keff\s*[=:]\s*(\d+\.?\d*)", text, re.I)
    if m:
        v = float(m.group(1))
        return (v - 0.01, v + 0.01)
    return None


def _extract_reactor_type(text: str) -> str:
    """Extract reactor type (HTGR, PWR, BWR, etc.)."""
    t = text.lower()
    if "htgr" in t or "htr" in t or "gas" in t or "pebble" in t:
        return "valar-10"  # HTGR preset
    if "pwr" in t or "pressurized" in t or "nuscale" in t:
        return "nuscale-77mwe"
    if "bwr" in t or "boiling" in t:
        return "bwrx-300"
    return "valar-10"


def _extract_cycle_years(text: str) -> Optional[float]:
    """Extract cycle length in years."""
    m = re.search(r"(\d+)\s*year", text, re.I)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+)\s*yr", text, re.I)
    if m:
        return float(m.group(1))
    return None


def parse_nl_design(text: str) -> Dict[str, Any]:
    """
    Parse natural-language design intent into structured parameters.

    Args:
        text: Free-form description (e.g. "10 MW HTGR, k-eff 1.0-1.05, enrichment <20%")

    Returns:
        Dict with power_mw, enrichment, keff_range, preset, cycle_length_days, etc.
    """
    intent: Dict[str, Any] = {"preset": _extract_reactor_type(text)}
    power = _extract_power_mw(text)
    if power is not None:
        intent["power_mw"] = power
    enr = _extract_enrichment(text)
    if enr is not None:
        intent["enrichment"] = enr
    keff = _extract_keff_range(text)
    if keff is not None:
        intent["keff_range"] = keff
    cyc = _extract_cycle_years(text)
    if cyc is not None:
        intent["cycle_length_days"] = cyc * 365.0
    return intent


def design_from_nl(
    text: str,
    run_analysis: bool = True,
    create_reactor_fn: Optional[Callable[..., Any]] = None,
) -> NLDesignResult:
    """
    Create reactor design from natural-language description.

    Args:
        text: Design intent (e.g. "10 MW HTGR with k-eff 1.00-1.05, enrichment <20%")
        run_analysis: If True, run neutronics and return k_eff
        create_reactor_fn: Optional factory (default: smrforge.convenience.create_reactor)

    Returns:
        NLDesignResult with spec, parsed intent, and optional analysis
    """
    intent = parse_nl_design(text)
    preset = intent.get("preset", "valar-10")

    if create_reactor_fn is None:
        try:
            from smrforge.convenience import create_reactor

            create_reactor_fn = create_reactor
        except ImportError:
            raise ImportError(
                "design_from_nl requires smrforge. Install: pip install smrforge"
            ) from None

    # Build reactor from preset + overrides
    kwargs: Dict[str, Any] = {}
    if "power_mw" in intent:
        kwargs["power_mw"] = intent["power_mw"]
    if "enrichment" in intent:
        kwargs["enrichment"] = intent["enrichment"]
    if "cycle_length_days" in intent:
        kwargs["cycle_length"] = intent["cycle_length_days"]

    try:
        reactor = create_reactor_fn(preset, **kwargs)
    except Exception:
        reactor = create_reactor_fn(
            "valar-10",
            power_mw=intent.get("power_mw", 10.0),
            enrichment=intent.get("enrichment", 0.195),
        )

    spec = getattr(reactor, "spec", None)
    if spec is None:
        from smrforge.convenience import get_preset
        spec = get_preset(preset)
        if kwargs.get("power_mw"):
            spec = spec.model_copy(update={"power_thermal": kwargs["power_mw"] * 1e6})
        if kwargs.get("enrichment") is not None:
            spec = spec.model_copy(update={"enrichment": kwargs["enrichment"]})

    analysis = None
    constraints_met = None
    if run_analysis:
        try:
            analysis = reactor.solve()
            k = analysis.get("k_eff")
            keff_range = intent.get("keff_range")
            if keff_range and k is not None:
                constraints_met = keff_range[0] <= float(k) <= keff_range[1]
            else:
                constraints_met = True
        except Exception as e:
            analysis = {"error": str(e)}
            constraints_met = False

    return NLDesignResult(
        spec=spec,
        intent_parsed=intent,
        analysis=analysis,
        constraints_met=constraints_met,
        message=f"Design from: {text[:80]}...",
    )
