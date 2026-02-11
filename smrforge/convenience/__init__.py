"""
High-level convenience API.

This package provides simplified "one-liner" entry points for common SMRForge
tasks (reactor creation, quick k-eff, etc.) as well as optional transient
helpers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

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


# LWR presets (optional). These are registered in the design library when
# available, so `create_reactor("<preset>")` must support them too.
try:
    from ..presets.smr_lwr import BWRX300, CAREM32MWe, NuScalePWR77MWe, SMART100MWe

    _LWR_PRESETS_AVAILABLE = True
except Exception:
    _LWR_PRESETS_AVAILABLE = False

    # Dummy classes for type hints and for tests that validate import-error paths
    class NuScalePWR77MWe:  # type: ignore[no-redef]
        pass

    class SMART100MWe:  # type: ignore[no-redef]
        pass

    class CAREM32MWe:  # type: ignore[no-redef]
        pass

    class BWRX300:  # type: ignore[no-redef]
        pass


# -----------------------------------------------------------------------------
# Library caching
# -----------------------------------------------------------------------------

_design_library: Optional[DesignLibrary] = None


def _get_library() -> DesignLibrary:
    """Lazy-load the preset design library."""
    global _design_library
    if not _PRESETS_AVAILABLE:
        raise ImportError(
            "Preset designs not available. Install required dependencies."
        )
    if _design_library is None:
        _design_library = DesignLibrary()
    return _design_library


_CONVENIENCE_MAIN_AVAILABLE = True


def list_presets() -> List[str]:
    """List all available preset reactor designs."""
    return _get_library().list_designs()


def list_reactor_types() -> List[str]:
    """List available reactor type names for create_reactor and specs."""
    return [rt.value for rt in ReactorType]


def list_fuel_types() -> List[str]:
    """List available fuel type names for create_reactor and specs."""
    return [ft.value for ft in FuelType]


def list_constraint_sets() -> List[str]:
    """List built-in constraint set names for quick_validate."""
    return ["regulatory_limits", "safety_margins"]


def get_constraint_set(name: str) -> "ConstraintSet":
    """Get a built-in constraint set by name."""
    from ..validation.constraints import ConstraintSet

    if name == "regulatory_limits":
        return ConstraintSet.get_regulatory_limits()
    if name == "safety_margins":
        return ConstraintSet.get_safety_margins()
    raise ValueError(
        f"Unknown constraint set '{name}'. Available: {list_constraint_sets()}"
    )


def get_example_path(name: str) -> Path:
    """
    Get path to a canonical example input file.

    Args:
        name: Example name, e.g. "reactor" -> examples/inputs/reactor.json.

    Returns:
        Absolute Path to the example file.

    Example:
        >>> path = get_example_path("reactor")
        >>> reactor = load_reactor(path)
    """
    base = Path(__file__).resolve().parents[2]
    _example_map = {"reactor": base / "examples" / "inputs" / "reactor.json"}
    if name not in _example_map:
        raise ValueError(
            f"Unknown example '{name}'. Available: {list(_example_map.keys())}"
        )
    p = _example_map[name]
    if not p.exists():
        raise FileNotFoundError(f"Example file not found: {p}")
    return p


def list_examples() -> List[str]:
    """List available example script names (without .py) in examples/."""
    base = Path(__file__).resolve().parents[2] / "examples"
    if not base.exists():
        return []
    return sorted(
        f.stem for f in base.iterdir() if f.suffix == ".py" and f.name != "__init__.py"
    )


def list_nuclides() -> List[str]:
    """List common SMR nuclide names (for burnup/ENDF setup)."""
    try:
        from ..data_downloader import COMMON_SMR_NUCLIDES

        return list(COMMON_SMR_NUCLIDES)
    except ImportError:
        return []


def list_sweepable_params() -> List[str]:
    """List parameter names commonly swept in quick_sweep (from ReactorSpecification)."""
    return [
        "enrichment",
        "power_thermal",
        "core_height",
        "core_diameter",
        "reflector_thickness",
        "heavy_metal_loading",
        "inlet_temperature",
        "outlet_temperature",
        "max_fuel_temperature",
        "primary_pressure",
        "coolant_flow_rate",
        "cycle_length",
        "capacity_factor",
        "target_burnup",
        "doppler_coefficient",
        "shutdown_margin",
    ]


def get_default_output_dir() -> Path:
    """Return the default output directory used by sweeps and workflows."""
    return Path("output")


def get_preset(name: str) -> ReactorSpecification:
    """Get a preset reactor design specification."""
    return _get_library().get_design(name)


def load_reactor(path: Union[str, Path]) -> "SimpleReactor":
    """
    Load a reactor from a JSON file.

    Accepts either full ReactorSpecification schema or a simplified format
    with ``power_mw`` (converted to power_thermal). Simplified format uses
    sensible defaults for missing fields.

    Args:
        path: Path to reactor JSON file (e.g., ``examples/inputs/reactor.json``).

    Returns:
        SimpleReactor instance ready for solve_keff(), solve(), etc.

    Example:
        >>> from smrforge import load_reactor
        >>> reactor = load_reactor("examples/inputs/reactor.json")
        >>> k = reactor.solve_keff()
    """
    path = Path(path)
    data = json.loads(path.read_text())

    # Support simplified format with power_mw and minimal fields
    if "power_mw" in data and "power_thermal" not in data:
        power_mw = float(data.pop("power_mw", 10))
        data["power_thermal"] = power_mw * 1e6
        # Fill required fields with defaults if missing
        defaults = {
            "inlet_temperature": 823.15,
            "outlet_temperature": 1023.15,
            "max_fuel_temperature": 1873.15,
            "primary_pressure": 7.0e6,
            "reflector_thickness": 30.0,
            "heavy_metal_loading": power_mw * 15.0,
            "coolant_flow_rate": power_mw * 0.8,
            "cycle_length": 3650,
            "capacity_factor": 0.95,
            "target_burnup": 150.0,
            "doppler_coefficient": -3.5e-5,
            "shutdown_margin": 0.05,
        }
        for k, v in defaults.items():
            data.setdefault(k, v)

    spec = ReactorSpecification.model_validate(data)
    instance = SimpleReactor.__new__(SimpleReactor)
    instance.spec = spec
    instance._core = None
    instance._xs_data = None
    instance._solver = None
    return instance


def create_reactor(
    name: Optional[str] = None,
    power_mw: Optional[float] = None,
    core_height: Optional[float] = None,
    core_diameter: Optional[float] = None,
    enrichment: Optional[float] = None,
    config: Optional[Union[str, Path]] = None,
    **kwargs,
) -> "SimpleReactor":
    """
    Create a reactor with sensible defaults.

    If ``config`` is provided (path to JSON file), loads reactor from file.
    If called as `create_reactor("<preset-name>")` (i.e., only the `name`
    positional argument is provided), the name is interpreted as a **preset**
    design name and unknown presets raise `ValueError` (as tests expect).

    If called with keyword arguments (e.g. `create_reactor(name="MyReactor", ...)`)
    the name is treated as a custom reactor name unless it matches a known preset.
    """
    if config is not None:
        return load_reactor(config)

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

        preset_class_map = {
            "valar-10": ValarAtomicsReactor,
            "gt-mhr-350": GTMHR350,
            "htr-pm-200": HTRPM200,
            "micro-htgr-1": MicroHTGR,
        }

        if _LWR_PRESETS_AVAILABLE:
            preset_class_map.update(
                {
                    "nuscale-77mwe": NuScalePWR77MWe,
                    "smart-100mwe": SMART100MWe,
                    "carem-32mwe": CAREM32MWe,
                    "bwrx-300": BWRX300,
                }
            )

        preset_class = preset_class_map.get(name)

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


def get_design_point(reactor: "SimpleReactor") -> Dict[str, float]:
    """Steady-state design point summary (power_thermal_mw, k_eff, power densities, etc.)."""
    results = reactor.solve()
    point: Dict[str, float] = {
        "power_thermal_mw": results.get(
            "power_thermal_mw", getattr(reactor.spec, "power_thermal", 0) / 1e6
        ),
        "k_eff": float(results.get("k_eff", 0.0)),
    }
    if "power_distribution" in results:
        p = results["power_distribution"]
        if hasattr(p, "__len__") and len(p) > 0:
            arr = np.asarray(p).flatten()
            point["max_power_density"] = float(np.max(arr))
            point["mean_power_density"] = float(np.mean(arr))
            if np.mean(arr) > 0:
                point["power_peak_factor"] = float(np.max(arr) / np.mean(arr))
    if "flux" in results:
        f = results["flux"]
        if hasattr(f, "__len__") and len(f) > 0:
            arr = np.asarray(f).flatten()
            point["flux_max"] = float(np.max(arr))
            point["flux_mean"] = float(np.mean(arr))
    return point


def quick_validate(
    reactor_or_path: Union["SimpleReactor", str, Path],
    constraint_set: Optional[object] = None,
) -> "ValidationResult":
    """
    Validate a reactor design against constraints in one call.

    Args:
        reactor_or_path: SimpleReactor instance or path to reactor JSON file.
        constraint_set: Optional ConstraintSet (default: regulatory limits).

    Returns:
        ValidationResult with passed, violations, warnings, metrics.

    Example:
        >>> from smrforge import quick_validate, load_reactor
        >>> result = quick_validate("examples/inputs/reactor.json")
        >>> print(f"Passed: {result.passed}")
        >>> reactor = load_reactor("reactor.json")
        >>> result = quick_validate(reactor)
    """
    from ..validation.constraints import ConstraintSet, DesignValidator

    if isinstance(reactor_or_path, (str, Path)):
        reactor = load_reactor(reactor_or_path)
    else:
        reactor = reactor_or_path

    if constraint_set is None:
        constraint_set = ConstraintSet.get_regulatory_limits()
    validator = DesignValidator(constraint_set)
    return validator.validate(reactor)


def save_variant(
    reactor: "SimpleReactor",
    variant_name: str,
    output_dir: Optional[Union[str, Path]] = None,
) -> Path:
    """Save a reactor design as a named variant (for design branching/tracking)."""
    output_dir = Path(output_dir or ".")
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in variant_name)
    path = output_dir / f"design_{safe_name}.json"
    reactor.save(path)
    return path


def quick_sweep(
    preset_or_reactor: Union[str, Path, "SimpleReactor"],
    params: Dict[str, Union[tuple, list]],
    analysis: str = "keff",
    output_path: Optional[Union[str, Path]] = None,
    parallel: bool = False,
    **economics_kwargs,
) -> Dict:
    """
    Run a parameter sweep with minimal setup.

    Args:
        preset_or_reactor: Preset name, path to reactor JSON, or SimpleReactor.
        params: Parameter ranges, e.g. {"enrichment": (0.15, 0.25, 0.02)} or
                {"enrichment": [0.15, 0.19, 0.23]}.
        analysis: Analysis type - "keff" (default) or "neutronics".
        output_path: Optional path to save results JSON.
        parallel: Whether to run cases in parallel (default: False for simplicity).
        **economics_kwargs: Ignored; for future use.

    Returns:
        Dict with "results" (list of case dicts), "failed_cases", "summary_stats".

    Example:
        >>> from smrforge import quick_sweep
        >>> out = quick_sweep("valar-10", {"enrichment": (0.15, 0.25, 0.02)})
        >>> for r in out["results"]:
        ...     print(r["parameters"]["enrichment"], r["k_eff"])
    """
    from ..workflows.parameter_sweep import ParameterSweep, SweepConfig

    def _to_create_reactor_kwargs(data: dict) -> dict:
        """Convert spec-like dict to create_reactor kwargs (power_thermal->power_mw, etc.)."""
        d = data.copy()
        if "power_thermal" in d and "power_mw" not in d:
            d["power_mw"] = d.pop("power_thermal", 10e6) / 1e6
        return d

    if isinstance(preset_or_reactor, SimpleReactor):
        template = _to_create_reactor_kwargs(preset_or_reactor.spec.model_dump())
    elif isinstance(preset_or_reactor, (str, Path)):
        path = Path(preset_or_reactor)
        if path.exists():
            template = json.loads(path.read_text())
            if "power_mw" in template and "power_thermal" not in template:
                template["power_thermal"] = float(template.pop("power_mw", 10)) * 1e6
            template = _to_create_reactor_kwargs(template)
        else:
            # Preset name: resolve to full spec so param overrides work
            try:
                spec = get_preset(str(preset_or_reactor))
                template = _to_create_reactor_kwargs(spec.model_dump())
            except Exception:
                template = {"name": str(preset_or_reactor)}
    else:
        try:
            spec = get_preset(str(preset_or_reactor))
            template = _to_create_reactor_kwargs(spec.model_dump())
        except Exception:
            template = {"name": str(preset_or_reactor)}

    analysis_types = [analysis] if analysis in ("keff", "neutronics", "burnup") else ["keff"]
    output_dir = Path(output_path).parent if output_path else Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    config = SweepConfig(
        parameters=params,
        analysis_types=analysis_types,
        reactor_template=template,
        output_dir=output_dir,
        parallel=parallel,
        save_intermediate=False,
    )
    result = ParameterSweep(config).run(show_progress=False)

    if output_path:
        result.save(Path(output_path))

    return {
        "results": result.results,
        "failed_cases": result.failed_cases,
        "summary_stats": result.summary_stats,
    }


def quick_economics(
    reactor_or_preset: Union["SimpleReactor", str, Path],
    nth_of_a_kind: int = 1,
    **kwargs,
) -> Dict:
    """
    Quick cost estimate from reactor or preset.

    Args:
        reactor_or_preset: SimpleReactor, preset name, or path to reactor JSON.
        nth_of_a_kind: Nth-of-a-kind (1 = FOAK).
        **kwargs: Passed to estimate_costs_from_spec (modularity_factor, discount_rate, etc.).

    Returns:
        Dict with capital_costs, operating_costs, lcoe, lcoe_breakdown.

    Example:
        >>> from smrforge import quick_economics
        >>> costs = quick_economics("valar-10")
        >>> print(f"LCOE: ${costs['lcoe']:.2f}/kWh")
    """
    from ..economics.integration import estimate_costs_from_spec

    if isinstance(reactor_or_preset, SimpleReactor):
        spec = reactor_or_preset.spec
    elif isinstance(reactor_or_preset, (str, Path)):
        path = Path(reactor_or_preset)
        if path.exists():
            reactor = load_reactor(path)
            spec = reactor.spec
        else:
            spec = get_preset(str(reactor_or_preset))
    else:
        spec = get_preset(str(reactor_or_preset))

    return estimate_costs_from_spec(spec, nth_of_a_kind=nth_of_a_kind, **kwargs)


def quick_optimize(
    reactor_or_preset: Union["SimpleReactor", str, Path],
    params: Dict[str, Tuple[float, float]],
    objective: str = "max_keff",
    max_iter: int = 50,
    method: str = "differential_evolution",
    **kwargs,
) -> Dict:
    """
    Quick single-objective design optimization.

    Args:
        reactor_or_preset: Base reactor (SimpleReactor, preset name, or path to JSON).
        params: Parameter bounds {name: (low, high)}, e.g. {"enrichment": (0.15, 0.25)}.
        objective: "max_keff" (default) or "min_neg_keff" (same effect).
        max_iter: Maximum iterations.
        method: "differential_evolution" or "minimize".
        **kwargs: Passed to DesignOptimizer/optimize.

    Returns:
        Dict with x_opt, f_opt, param_names, optimal_point, success.

    Example:
        >>> out = quick_optimize("valar-10", {"enrichment": (0.15, 0.25)})
        >>> print(out["optimal_point"])
    """
    from ..optimization.design import DesignOptimizer

    if isinstance(reactor_or_preset, SimpleReactor):
        base_spec = reactor_or_preset.spec.model_dump()
    elif isinstance(reactor_or_preset, (str, Path)):
        path = Path(reactor_or_preset)
        if path.exists():
            base_spec = json.loads(path.read_text())
            if "power_mw" in base_spec and "power_thermal" not in base_spec:
                base_spec["power_thermal"] = float(base_spec.pop("power_mw", 10)) * 1e6
        else:
            base_spec = get_preset(str(reactor_or_preset)).model_dump()
    else:
        base_spec = get_preset(str(reactor_or_preset)).model_dump()

    # Convert to create_reactor-friendly format (power_mw not power_thermal)
    def _to_create_kwargs(spec: dict) -> dict:
        d = {k: v for k, v in spec.items() if k not in ("preset",)}
        if "power_thermal" in d and "power_mw" not in d:
            d["power_mw"] = d.pop("power_thermal", 10e6) / 1e6
        return d

    param_names = list(params.keys())
    bounds = [params[n] for n in param_names]

    def reactor_from_x(x):
        spec = dict(base_spec)
        for i, name in enumerate(param_names):
            spec[name] = float(x[i])
        return create_reactor(**_to_create_kwargs(spec))

    obj_name = (objective or "max_keff").strip().lower()
    if obj_name in ("max_keff", "min_neg_keff"):

        def obj(x):
            r = reactor_from_x(x)
            return -get_design_point(r)["k_eff"]

    else:
        raise ValueError(
            f"objective must be 'max_keff' or 'min_neg_keff', got {objective!r}"
        )

    opt = DesignOptimizer(obj, bounds, method=method, **kwargs)
    result = opt.optimize(max_iterations=max_iter, **kwargs)

    optimal_point = dict(zip(param_names, result.x_opt.tolist()))
    optimal_point["k_eff"] = -result.f_opt if obj_name in ("max_keff", "min_neg_keff") else result.f_opt

    return {
        "x_opt": result.x_opt.tolist(),
        "f_opt": float(result.f_opt),
        "param_names": param_names,
        "optimal_point": optimal_point,
        "success": result.success,
        "n_iterations": result.n_iterations,
        "message": result.message,
    }


def quick_uq(
    reactor_or_preset: Union["SimpleReactor", str, Path],
    uncertain_params: List[Dict],
    n_samples: int = 100,
    method: str = "lhs",
    output_names: Optional[List[str]] = None,
    random_state: Optional[int] = 42,
    **kwargs,
) -> Dict:
    """
    Quick uncertainty quantification (Monte Carlo / LHS propagation).

    Args:
        reactor_or_preset: Base reactor (SimpleReactor, preset name, or path to JSON).
        uncertain_params: List of {"name", "nominal", "distribution", "uncertainty"}.
            distribution: "normal", "uniform", "lognormal", "triangular".
            uncertainty: float (std) for normal/lognormal, or (min, max) for uniform.
        n_samples: Number of samples.
        method: "lhs", "mc", or "sobol".
        output_names: Outputs to track (default: ["k_eff", "power_thermal_mw"]).
        random_state: Random seed.
        **kwargs: Passed to UncertaintyPropagation.propagate.

    Returns:
        Dict with mean, std, output_names, samples (if requested).

    Example:
        >>> out = quick_uq("valar-10", [
        ...     {"name": "enrichment", "nominal": 0.195, "distribution": "normal", "uncertainty": 0.02},
        ... ], n_samples=50)
    """
    from ..uncertainty.uq import UncertainParameter, UncertaintyPropagation

    if isinstance(reactor_or_preset, SimpleReactor):
        base_spec = reactor_or_preset.spec.model_dump()
    elif isinstance(reactor_or_preset, (str, Path)):
        path = Path(reactor_or_preset)
        if path.exists():
            base_spec = json.loads(path.read_text())
            if "power_mw" in base_spec and "power_thermal" not in base_spec:
                base_spec["power_thermal"] = float(base_spec.pop("power_mw", 10)) * 1e6
        else:
            base_spec = get_preset(str(reactor_or_preset)).model_dump()
    else:
        base_spec = get_preset(str(reactor_or_preset)).model_dump()

    def _to_create_kwargs(spec: dict) -> dict:
        d = {k: v for k, v in spec.items() if k not in ("preset",)}
        if "power_thermal" in d and "power_mw" not in d:
            d["power_mw"] = d.pop("power_thermal", 10e6) / 1e6
        return d

    params = []
    for p in uncertain_params:
        name = p["name"]
        nominal = float(p["nominal"])
        dist = p.get("distribution", "normal")
        unc = p.get("uncertainty", 0.1)
        params.append(UncertainParameter(name, dist, nominal, unc))

    def model(x_dict):
        spec = dict(base_spec)
        spec.update(x_dict)
        r = create_reactor(**_to_create_kwargs(spec))
        return get_design_point(r)

    out_names = output_names or ["k_eff", "power_thermal_mw"]
    prop = UncertaintyPropagation(params, model, out_names)
    uq_results = prop.propagate(
        n_samples=n_samples,
        method=method,
        random_state=random_state,
        **kwargs,
    )

    result: Dict = {
        "mean": uq_results.mean.tolist() if uq_results.mean is not None else [],
        "std": uq_results.std.tolist() if uq_results.std is not None else [],
        "output_names": getattr(uq_results, "output_names", out_names),
    }
    return result


# When this module is reloaded (tests exercise this), class objects are recreated.
# Some tests keep earlier `SimpleReactor` references and still expect `isinstance`
# checks to succeed after reload. Make the reloaded class a subclass of the prior
# class (when present) to preserve `isinstance` behavior.
_PreviousSimpleReactor = globals().get("SimpleReactor")
_SimpleReactorBase = (
    _PreviousSimpleReactor if isinstance(_PreviousSimpleReactor, type) else object
)


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
            "max_fuel_temperature": kwargs.get(
                "max_fuel_temperature", 1873.15
            ),  # 1600°C
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
            self._solver = MultiGroupDiffusion(
                self._get_core(), self._get_xs_data(), options
            )
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
    "list_reactor_types",
    "list_fuel_types",
    "list_constraint_sets",
    "get_constraint_set",
    "get_example_path",
    "list_examples",
    "list_nuclides",
    "list_sweepable_params",
    "get_default_output_dir",
    "get_preset",
    "load_reactor",
    "create_reactor",
    "quick_validate",
    "quick_sweep",
    "quick_economics",
    "quick_optimize",
    "quick_uq",
    "analyze_preset",
    "compare_designs",
    "get_design_point",
    "save_variant",
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
