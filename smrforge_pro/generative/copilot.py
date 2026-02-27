"""
Reactor Design Copilot: natural language -> reactor config.

Document-specified API: parse_nl_design, design_from_nl (Path C Product Updates).
"""

import re
from typing import Any, Dict, Optional

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.generative.copilot")


def parse_nl_design(text: str) -> Dict[str, Any]:
    """
    Parse natural language design description into reactor spec.

    Extracts: power (MW), enrichment (%), k_eff range, reactor type.
    Example: "10 MW HTGR with k-eff 1.0-1.05, enrichment <20%" ->
        {power_mw: 10, keff_min: 1.0, keff_max: 1.05, enrichment_max: 20, ...}

    Args:
        text: Natural language design description

    Returns:
        Spec dict with power_mw, keff_min, keff_max, enrichment_max, reactor_type, preset
    """
    spec = _parse_simple_keywords(text)
    text_lower = text.lower()

    # Enrichment: "enrichment <20%", "enrichment 5-19%", "<20%"
    enrich_match = re.search(r"enrichment\s*[<≤]?\s*(\d+(?:\.\d+)?)\s*%?", text_lower, re.I)
    if enrich_match:
        spec["enrichment_max"] = float(enrich_match.group(1))
    else:
        em = re.search(r"(\d+(?:\.\d+)?)\s*%\s*enrichment", text_lower)
        if em:
            spec["enrichment_max"] = float(em.group(1))

    # k-eff range: "k-eff 1.0-1.05", "keff 1.0 to 1.05"
    keff_match = re.search(r"k[- ]?eff\s*(\d+(?:\.\d+)?)\s*[-–to]+\s*(\d+(?:\.\d+)?)", text_lower, re.I)
    if keff_match:
        spec["keff_min"] = float(keff_match.group(1))
        spec["keff_max"] = float(keff_match.group(2))
    else:
        km = re.search(r"k[- ]?eff\s*[<>=]?\s*(\d+(?:\.\d+)?)", text_lower, re.I)
        if km:
            spec["keff_min"] = float(km.group(1))
            spec["keff_max"] = float(km.group(1))

    return spec


def design_from_nl(
    prompt: str,
    run_analysis: bool = False,
    llm_provider: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Parse natural language and optionally create reactor. Pro tier.

    Example: "10 MW HTGR with k-eff 1.0-1.05" -> reactor spec; if run_analysis, create and solve.

    Args:
        prompt: Natural language design description
        run_analysis: If True, create_reactor and run solve
        llm_provider: Optional LLM for enhancement
        **kwargs: Passed to create_reactor if run_analysis

    Returns:
        Spec dict; if run_analysis, includes 'reactor' and 'result'
    """
    spec = parse_nl_design(prompt)
    if llm_provider:
        try:
            spec = _llm_enhance(spec, prompt, llm_provider, **kwargs)
        except Exception as e:
            logger.warning("LLM enhancement skipped: %s", e)

    if run_analysis:
        from smrforge.convenience import create_reactor
        preset = spec.get("preset", "valar-10")
        reactor = create_reactor(preset, **{k: v for k, v in spec.items() if k in ("power_mw", "enrichment")})
        result = reactor.solve()
        spec["reactor"] = reactor
        spec["result"] = result

    return spec


def design_from_natural_language(
    prompt: str,
    llm_provider: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Parse natural language description into reactor spec.

    Example: "HTGR, 300 MWth, pebble bed" -> {reactor_type: "HTGR", power_mw: 300, ...}
    Alias for design_from_nl(prompt, run_analysis=False).
    """
    return design_from_nl(prompt, run_analysis=False, llm_provider=llm_provider, **kwargs)


def _parse_simple_keywords(text: str) -> Dict[str, Any]:
    """Extract spec from simple keyword patterns."""
    text = text.lower()
    spec = {"preset": "valar-10", "power_mw": 10.0}
    if "htgr" in text or "gas" in text or "pebble" in text:
        spec["preset"] = "valar-10"
        spec["reactor_type"] = "HTGR"
    if "lwr" in text or "pwr" in text or "nuscale" in text:
        spec["preset"] = "nuscale-77"
        spec["reactor_type"] = "PWR"
    for word in text.split():
        try:
            v = float(word.replace(",", ""))
            if 1 < v < 2000:
                spec["power_mw"] = v
                break
        except ValueError:
            continue
    return spec


def _llm_enhance(spec: Dict, prompt: str, provider: str, **kwargs: Any) -> Dict:
    """Use LLM to refine spec (scaffold)."""
    return spec
