"""
Neutronics and reactor physics solvers
"""

try:
    from smrforge.neutronics.solver import MultiGroupDiffusion

    # MultiGroupDiffusion is the main solver class (alias for backward compatibility)
    NeutronicsSolver = MultiGroupDiffusion
    _SOLVER_AVAILABLE = True
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import neutronics solver: {e}", ImportWarning)
    _SOLVER_AVAILABLE = False

try:
    from smrforge.neutronics.monte_carlo import MonteCarloSolver

    # Alias for backward compatibility
    MonteCarlo = MonteCarloSolver
    _MC_AVAILABLE = True
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import Monte Carlo solver: {e}", ImportWarning)
    _MC_AVAILABLE = False

try:
    from smrforge.neutronics.monte_carlo_optimized import (
        OptimizedMonteCarloSolver,
        ParticleBank,
    )

    _MC_OPTIMIZED_AVAILABLE = True
except ImportError as e:
    import warnings

    warnings.warn(
        f"Could not import optimized Monte Carlo solver: {e}", ImportWarning
    )
    _MC_OPTIMIZED_AVAILABLE = False

try:
    from smrforge.neutronics.transport import Transport

    _TRANSPORT_AVAILABLE = True
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import transport solver: {e}", ImportWarning)
    _TRANSPORT_AVAILABLE = False

__all__ = []
if _SOLVER_AVAILABLE:
    __all__.extend(["NeutronicsSolver", "MultiGroupDiffusion"])
if _MC_AVAILABLE:
    __all__.extend(["MonteCarlo", "MonteCarloSolver"])
if _MC_OPTIMIZED_AVAILABLE:
    __all__.extend(["OptimizedMonteCarloSolver", "ParticleBank"])
if _TRANSPORT_AVAILABLE:
    __all__.append("Transport")
