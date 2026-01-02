"""
Decay heat calculation module.

This module provides:
- DecayHeatCalculator: Time-dependent decay heat calculations
- Energy-weighted decay heat from gamma/beta spectra
- Post-shutdown decay heat analysis
"""

from .calculator import DecayHeatCalculator, DecayHeatResult

__all__ = ["DecayHeatCalculator", "DecayHeatResult"]

