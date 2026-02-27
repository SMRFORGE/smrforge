"""
Tier 2: Edge/Embedded surrogates - quantization, export for deployment.
"""

from .export import export_for_edge, quantize_surrogate

__all__ = ["export_for_edge", "quantize_surrogate"]
