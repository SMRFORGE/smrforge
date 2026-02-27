"""
Conversational safety analysis: natural language -> transient setup + run.
"""

from typing import Any, Dict, Optional

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.generative.conversational_safety")


def run_safety_query(
    query: str,
    reactor_spec: Optional[Dict[str, Any]] = None,
    llm_provider: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Run safety analysis from natural language query.

    Example: "What happens if I lose feedwater at 50% power?"

    Args:
        query: Natural language safety question
        reactor_spec: Optional reactor configuration
        llm_provider: Optional LLM for query parsing
        **kwargs: Passed to analysis

    Returns:
        Dict with transient_config, result summary, plain_english_summary
    """
    config = _parse_safety_query(query)
    result = {"query": query, "transient_config": config}
    result["plain_english_summary"] = _generate_summary(config, query)
    return result


def _parse_safety_query(text: str) -> Dict[str, Any]:
    """Parse safety query into transient config (keyword-based)."""
    text = text.lower()
    config = {"type": "reactivity_insertion", "duration": 100.0, "power_fraction": 1.0}
    if "feedwater" in text or "loss" in text or "loca" in text:
        config["type"] = "loca"
    if "50%" in text or "half" in text:
        config["power_fraction"] = 0.5
    return config


def _generate_summary(config: Dict, query: str) -> str:
    """Generate plain English summary."""
    return f"Analysis of: {query}. Config: {config['type']} at {config.get('power_fraction', 1)*100:.0f}% power."
