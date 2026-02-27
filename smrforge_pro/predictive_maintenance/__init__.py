"""
Tier 2: Predictive maintenance - degradation models, RUL estimation.
"""

from .degradation import fit_degradation_model, predict_rul

__all__ = ["fit_degradation_model", "predict_rul"]
