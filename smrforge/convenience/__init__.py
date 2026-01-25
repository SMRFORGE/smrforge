"""
High-level convenience API.

This package provides simplified "one-liner" entry points for common SMRForge
tasks (reactor creation, quick k-eff, etc.) as well as optional transient
helpers.

Why this lives in a package:
- The repository also contains a legacy `smrforge/convenience.py` file that is
  used in a few coverage-focused tests via direct file loading.
- Python prefers packages over modules for `import smrforge.convenience`, so the
  public API must be implemented here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np

from ..geometry.core_geometry import PrismaticCore
from ..neutronics.solver import MultiGroupDiffusion

# Core imports - required for convenience functions
from ..validation.models import (
    CrossSectionData,
    FuelType,
    ReactorSpecification,
    ReactorType,
    SolverOptions,
)

# Import presets (optional)
try:
    from ..presets.htgr import (
        GTMHR350,
        HTRPM200,
        DesignLibrary,
        MicroHTGR,
        ValarAtomicsReactor,
    )

    _PRESETS_AVAILABLE = True
except ImportError:
    _PRESETS_AVAILABLE = False

    # Dummy classes for type hints and for tests that validate import-error paths
    class DesignLibrary:  # type: ignore[no-redef]
        pass

    class ValarAtomicsReactor:  # type: ignore[no-redef]
        pass

    class GTMHR350:  # type: ignore[no-redef]
        pass

    class HTRPM200:  # type: ignore[no-redef]
        pass

    class MicroHTGR:  # type: ignore[no-redef]
        pass


# -----------------------------------------------------------------------------
# Library caching
# -----------------------------------------------------------------------------

_design_library: Optional[DesignLibrary] = None


def _get_library() -> DesignLibrary:
    """Lazy-load the preset design library."""
    global _design_library
    if not _PRESETS_AVAILABLE:
        raise ImportError("Preset designs not available. Install required dependencies.")
    if _design_library is None:
        _design_library = DesignLibrary()
    return _design_library


_CONVENIENCE_MAIN_AVAILABLE = True


def list_presets() -> List[str]:
    """List all available preset reactor designs."""
    return _get_library().list_designs()


def get_preset(name: str) -> ReactorSpecification:
    """Get a preset reactor design specification."""
    return _get_library().get_design(name)


def create_reactor(
    name: Optional[str] = None,
    power_mw: Optional[float] = None,
    core_height: Optional[float] = None,
    core_diameter: Optional[float] = None,
    enrichment: Optional[float] = None,
    **kwargs,
) -> "SimpleReactor":
    """
    Create a reactor with sensible defaults.

    If called as `create_reactor("<preset-name>")` (i.e., only the `name`
    positional argument is provided), the name is interpreted as a **preset**
    design name and unknown presets raise `ValueError` (as tests expect).

    If called with keyword arguments (e.g. `create_reactor(name="MyReactor", ...)`)
    the name is treated as a custom reactor name unless it matches a known preset.
    """
    preset_names: List[str] = []
    if _PRESETS_AVAILABLE:
        try:
            preset_names = list_presets()
        except Exception:
            preset_names = []

    positional_preset_request = (
        name is not None
        and power_mw is None
        and core_height is None
        and core_diameter is None
        and enrichment is None
        and not kwargs
    )

    if name and (name in preset_names or positional_preset_request):
        if name not in preset_names:
            raise ValueError(f"Unknown preset '{name}'. Available: {preset_names}")

        preset_class = {
            "valar-10": ValarAtomicsReactor,
            "gt-mhr-350": GTMHR350,
            "htr-pm-200": HTRPM200,
            "micro-htgr-1": MicroHTGR,
        }.get(name)

        if preset_class is None:
            raise ValueError(f"Unknown preset '{name}'. Available: {preset_names}")

        preset = preset_class()
        return SimpleReactor.from_preset(preset)

    # Create custom reactor
    if name:
        kwargs.setdefault("name", name)

    return SimpleReactor(
        power_mw=power_mw or 10.0,
        core_height=core_height or 200.0,
        core_diameter=core_diameter or 100.0,
        enrichment=enrichment or 0.195,
        **kwargs,
    )


def quick_keff(
    power_mw: float = 10.0,
    enrichment: float = 0.195,
    core_height: float = 200.0,
    core_diameter: float = 100.0,
    **kwargs,
) -> float:
    """Quick one-liner to get k-eff for a simple reactor."""
    reactor = create_reactor(
        power_mw=power_mw,
        enrichment=enrichment,
        core_height=core_height,
        core_diameter=core_diameter,
        **kwargs,
    )
    return reactor.solve_keff()


def analyze_preset(design_name: str) -> Dict:
    """Analyze a preset design with one line."""
    reactor = create_reactor(design_name)
    return reactor.solve()


def compare_designs(design_names: List[str]) -> Dict[str, Dict]:
    """Compare multiple designs side-by-side (best-effort)."""
    results: Dict[str, Dict] = {}
    for design in design_names:
        try:
            results[design] = analyze_preset(design)
        except Exception as e:
            results[design] = {"error": str(e)}
    return results


# When this module is reloaded (tests exercise this), class objects are recreated.
# Some tests keep earlier `SimpleReactor` references and still expect `isinstance`
# checks to succeed after reload. Make the reloaded class a subclass of the prior
# class (when present) to preserve `isinstance` behavior.
_PreviousSimpleReactor = globals().get("SimpleReactor")
_SimpleReactorBase = _PreviousSimpleReactor if isinstance(_PreviousSimpleReactor, type) else object


class SimpleReactor(_SimpleReactorBase):
    """High-level reactor wrapper for easy usage."""

    def __init__(
        self,
        power_mw: float = 10.0,
        core_height: float = 200.0,
        core_diameter: float = 100.0,
        enrichment: float = 0.195,
        reactor_type: ReactorType = ReactorType.PRISMATIC,
        fuel_type: FuelType = FuelType.UCO,
        **kwargs,
    ):
        # Rough estimate: ~10-15 kg/MWth
        estimated_hm_loading = kwargs.get("heavy_metal_loading", power_mw * 15.0)

        spec_kwargs: Dict[str, object] = {
            "name": kwargs.get("name", "Custom-Reactor"),
            "reactor_type": reactor_type,
            "power_thermal": power_mw * 1e6,  # MW -> W
            "core_height": core_height,
            "core_diameter": core_diameter,
            "enrichment": enrichment,
            "fuel_type": fuel_type,
            "inlet_temperature": kwargs.get("inlet_temperature", 823.15),  # 550°C
            "outlet_temperature": kwargs.get("outlet_temperature", 1023.15),  # 750°C
            "max_fuel_temperature": kwargs.get("max_fuel_temperature", 1873.15),  # 1600°C
            "primary_pressure": kwargs.get("primary_pressure", 7.0e6),
            "reflector_thickness": kwargs.get("reflector_thickness", 30.0),
            "heavy_metal_loading": estimated_hm_loading,
            "coolant_flow_rate": kwargs.get("coolant_flow_rate", power_mw * 0.8),
            "cycle_length": kwargs.get("cycle_length", 3650),
            "capacity_factor": kwargs.get("capacity_factor", 0.95),
            "target_burnup": kwargs.get("target_burnup", 150.0),
            "doppler_coefficient": kwargs.get("doppler_coefficient", -3.5e-5),
            "shutdown_margin": kwargs.get("shutdown_margin", 0.05),
        }

        # Pass through any *recognized* ReactorSpecification fields not already set.
        # Unknown extras (e.g. "custom_field") are ignored to keep the convenience
        # API permissive.
        allowed = set(getattr(ReactorSpecification, "model_fields", {}).keys())
        for k, v in kwargs.items():
            if k in allowed and k not in spec_kwargs:
                spec_kwargs[k] = v

        self.spec = ReactorSpecification(**spec_kwargs)

        self._core: Optional[PrismaticCore] = None
        self._xs_data: Optional[CrossSectionData] = None
        self._solver: Optional[MultiGroupDiffusion] = None

    @classmethod
    def from_preset(cls, preset_reactor) -> "SimpleReactor":
        instance = cls.__new__(cls)
        instance.spec = preset_reactor.spec
        instance._core = None
        instance._xs_data = None
        instance._solver = None
        instance._preset = preset_reactor
        return instance

    def _get_core(self) -> PrismaticCore:
        if self._core is None:
            if hasattr(self, "_preset"):
                self._core = self._preset.build_core()
            else:
                self._core = PrismaticCore(name=self.spec.name)
                n_rings = max(2, int(self.spec.core_diameter / 80))
                self._core.build_hexagonal_lattice(
                    n_rings=n_rings,
                    pitch=40.0,
                    block_height=self.spec.core_height / 4,
                    n_axial=4,
                    flat_to_flat=36.0,
                )
                self._core.generate_mesh(n_radial=15, n_axial=20)
        return self._core

    def _get_xs_data(self) -> CrossSectionData:
        if self._xs_data is None:
            if hasattr(self, "_preset"):
                self._xs_data = self._preset.get_cross_sections()
            else:
                self._xs_data = self._create_simple_xs()
        return self._xs_data

    def _create_simple_xs(self) -> CrossSectionData:
        # Simplified 2-group cross sections (typical HTGR-ish values)
        return CrossSectionData(
            n_groups=2,
            n_materials=2,
            sigma_t=np.array([[0.30, 0.90], [0.28, 0.75]]),
            sigma_a=np.array([[0.008, 0.12], [0.002, 0.025]]),
            sigma_f=np.array([[0.006, 0.10], [0.0, 0.0]]),
            nu_sigma_f=np.array([[0.008, 0.10], [0.0, 0.0]]),
            sigma_s=np.array([[[0.29, 0.01], [0.0, 0.78]], [[0.28, 0.0], [0.0, 0.73]]]),
            chi=np.array([[1.0, 0.0], [0.0, 0.0]]),
            D=np.array([[1.0, 0.4], [1.2, 0.5]]),
        )

    def _get_solver(self) -> MultiGroupDiffusion:
        if self._solver is None:
            options = SolverOptions(max_iterations=1000, tolerance=1e-6, verbose=False)
            self._solver = MultiGroupDiffusion(self._get_core(), self._get_xs_data(), options)
        return self._solver

    def solve_keff(self) -> float:
        solver = self._get_solver()
        try:
            k_eff, _ = solver.solve_steady_state()
            return float(k_eff)
        except ValueError as e:
            # If validation fails but k_eff was computed, return it anyway
            k_eff_raw = getattr(solver, "k_eff", None)
            # Only use the fallback if it's *actually numeric*. This avoids treating
            # MagicMock's auto-created attributes as a real k_eff value.
            if isinstance(k_eff_raw, (int, float, np.floating)):
                k_eff_val = float(k_eff_raw)
                import warnings

                warnings.warn(
                    f"Solution validation failed, but returning k_eff = {k_eff_val:.6f}. Error: {e}",
                    UserWarning,
                )
                return k_eff_val
            raise

    def solve(self) -> Dict:
        solver = self._get_solver()
        k_eff, flux = solver.solve_steady_state()

        results: Dict[str, object] = {
            "k_eff": float(k_eff),
            "flux": flux,
            "name": self.spec.name,
            "power_thermal_mw": self.spec.power_thermal / 1e6,
        }

        try:
            power = solver.compute_power_distribution(self.spec.power_thermal)
            results["power_distribution"] = power
        except Exception:
            pass

        return results

    def save(self, filepath: Union[str, Path]):
        filepath = Path(filepath)
        with open(filepath, "w") as f:
            f.write(self.spec.model_dump_json(indent=2))

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "SimpleReactor":
        filepath = Path(filepath)
        with open(filepath) as f:
            spec = ReactorSpecification.model_validate_json(f.read())

        instance = cls.__new__(cls)
        instance.spec = spec
        instance._core = None
        instance._xs_data = None
        instance._solver = None
        return instance


# -----------------------------------------------------------------------------
# Optional transient convenience functions
# -----------------------------------------------------------------------------

try:
    from smrforge.convenience.transients import (
        decay_heat_removal,
        quick_transient,
        reactivity_insertion,
    )

    _TRANSIENT_CONVENIENCE_AVAILABLE = True
except ImportError:
    _TRANSIENT_CONVENIENCE_AVAILABLE = False


__all__ = [
    "_CONVENIENCE_MAIN_AVAILABLE",
    "_TRANSIENT_CONVENIENCE_AVAILABLE",
    "_PRESETS_AVAILABLE",
    "_design_library",
    "_get_library",
    "list_presets",
    "get_preset",
    "create_reactor",
    "analyze_preset",
    "compare_designs",
    "quick_keff",
    "SimpleReactor",
]

if _TRANSIENT_CONVENIENCE_AVAILABLE:
    __all__.extend(["quick_transient", "reactivity_insertion", "decay_heat_removal"])

# Ensure `smrforge.convenience` attribute on the parent package always points to
# the module object that is actually registered in `sys.modules`.
# Some tests temporarily swap `sys.modules['smrforge.convenience']` and then
# reload; without this, the parent package can end up referencing a stale module
# object, breaking `importlib.reload(smrforge.convenience)`.
import sys as _sys

_parent_pkg = _sys.modules.get("smrforge")
if _parent_pkg is not None:
    setattr(_parent_pkg, "convenience", _sys.modules[__name__])
