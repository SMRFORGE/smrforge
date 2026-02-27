"""
Coupling with external system and thermal-hydraulics codes.

- RELAP/TRACE: Run as subprocess, exchange power/flow data
- CFDCoupler: Interface for CFD code coupling (power, temperature exchange)
"""

try:
    from .system_codes import (
        RELAPCoupler,
        TRACECoupler,
        system_code_available,
    )

    _SYSTEM_CODES_AVAILABLE = True
except ImportError:
    _SYSTEM_CODES_AVAILABLE = False

try:
    from .cfd_coupler import (
        CFDCoupler,
        CFDFields,
        CFDMesh,
        PowerDensityFields,
    )

    _CFD_COUPLER_AVAILABLE = True
except ImportError:
    _CFD_COUPLER_AVAILABLE = False

try:
    from .cfd_integration import (
        OpenFOAMAdapter,
        MOOSEAdapter,
        create_cfd_coupler_with_openfoam,
    )

    _CFD_INTEGRATION_AVAILABLE = True
except ImportError:
    _CFD_INTEGRATION_AVAILABLE = False

__all__ = []
if _SYSTEM_CODES_AVAILABLE:
    __all__.extend(["TRACECoupler", "RELAPCoupler", "system_code_available"])
if _CFD_COUPLER_AVAILABLE:
    __all__.extend(["CFDCoupler", "CFDMesh", "CFDFields", "PowerDensityFields"])
if _CFD_INTEGRATION_AVAILABLE:
    __all__.extend(
        ["OpenFOAMAdapter", "MOOSEAdapter", "create_cfd_coupler_with_openfoam"]
    )
