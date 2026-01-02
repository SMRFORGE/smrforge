"""
Gamma-ray transport solver.

This module provides:
- GammaTransportSolver: Multi-group gamma transport solver
- Photon cross-section handling
- Gamma source term integration
- Shielding calculations
"""

from .solver import GammaTransportSolver, GammaTransportOptions

__all__ = ["GammaTransportSolver", "GammaTransportOptions"]

