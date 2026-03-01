"""
High-level convenience API.

This package provides simplified "one-liner" entry points for common SMRForge
tasks (reactor creation, quick k-eff, etc.) as well as optional transient
helpers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from ..geometry.core_geometry import PrismaticCore
from ..neutronics.solver import MultiGroupDiffusion
from ..utils.logging import get_logger

logger = get_logger("smrforge.convenience")

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


def pro_available() -> bool:
    """Return True if SMRForge Pro is installed and usable."""
    try:
        import smrforge_pro  # noqa: F401

        return True
    except ImportError:
        return False


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


def get_default_endf_dir() -> Path:
    """
    Return the default directory for ENDF nuclear data files.

    Returns:
        Path to standard ENDF storage directory (~/ENDF-Data on Unix, %USERPROFILE%\\ENDF-Data on Windows).

    Example:
        >>> path = get_default_endf_dir()
        >>> print(f"Store ENDF files in: {path}")
    """
    from ..core.reactor_core import get_standard_endf_directory

    return get_standard_endf_directory()


def list_endf_libraries() -> List[str]:
    """List supported ENDF nuclear data library names for downloads and caching."""
    return ["ENDF/B-VIII.0", "ENDF/B-VIII.1", "JEFF-3.3", "JENDL-5.0"]


def list_geometry_types() -> List[str]:
    """List supported core geometry type names (PrismaticCore, PebbleBedCore, etc.)."""
    return ["PrismaticCore", "PebbleBedCore", "CompactSMRCore", "MSRSMRCore"]


def list_analysis_types() -> List[str]:
    """List analysis type names supported by quick_sweep and parameter sweeps."""
    return ["keff", "burnup", "transient", "economics"]


def list_surrogates() -> List[str]:
    """List names of registered surrogate models. Returns [] if Pro not installed."""
    from ..workflows.plugin_registry import list_surrogates as _list

    return _list()


def quick_download_endf(
    library: str = "ENDF/B-VIII.1",
    output_dir: Optional[Union[str, Path]] = None,
    nuclide_set: str = "common_smr",
    show_progress: bool = True,
    **kwargs,
) -> Dict[str, Any]:
    """
    Download ENDF nuclear data files to a default or specified directory.

    Args:
        library: Library version (e.g., "ENDF/B-VIII.1").
        output_dir: Output directory. Defaults to get_default_endf_dir() if None.
        nuclide_set: Pre-defined set ("common_smr") or pass elements/isotopes via kwargs.
        show_progress: If True, show progress indicators.
        **kwargs: Passed to download_endf_data (elements, isotopes, max_workers, etc.).

    Returns:
        Dictionary with download statistics (downloaded, skipped, failed, total, output_dir).

    Example:
        >>> stats = quick_download_endf()
        >>> stats = quick_download_endf(library="ENDF/B-VIII.1", nuclide_set="common_smr")
    """
    try:
        from ..data_downloader import download_endf_data
    except ImportError as e:
        raise ImportError(
            "quick_download_endf requires data_downloader (requests). "
            f"Install: pip install requests. Original: {e}"
        ) from e

    if output_dir is None:
        output_dir = get_default_endf_dir()

    kwargs_clean = {k: v for k, v in kwargs.items() if k not in ("display",)}
    # Use nuclide_set only when elements/isotopes not specified
    use_nuclide_set = (
        nuclide_set
        if not (kwargs_clean.get("elements") or kwargs_clean.get("isotopes"))
        else None
    )
    return download_endf_data(
        library=library,
        output_dir=output_dir,
        nuclide_set=use_nuclide_set,
        show_progress=show_progress,
        **kwargs_clean,
    )


def quick_benchmark(
    benchmarks_file: Optional[Union[str, Path]] = None,
    case_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Run community benchmark cases and return pass/fail summary.

    Args:
        benchmarks_file: Path to community_benchmarks.json. Uses default if None.
        case_ids: Specific case IDs to run. If None, run all.

    Returns:
        Dict with "results" (case_id -> {passed, value, error}), "passed", "total", "report".

    Example:
        >>> out = quick_benchmark()
        >>> print(f"{out['passed']}/{out['total']} passed")
    """
    from ..benchmarks.runner import CommunityBenchmarkRunner

    path = Path(benchmarks_file) if benchmarks_file else None
    runner = CommunityBenchmarkRunner(benchmarks_path=path)
    raw = runner.run_all(case_ids=case_ids)
    results = {
        cid: {"passed": p, "value": v, "error": e} for cid, (p, v, e) in raw.items()
    }
    passed = sum(1 for r in results.values() if r["passed"])
    report = runner.generate_report(results=raw)
    return {
        "results": results,
        "passed": passed,
        "total": len(results),
        "report": report,
    }


def quick_safety_report(
    reactor_or_preset: Union["SimpleReactor", str, Path],
    constraint_set: Optional[str] = None,
    analysis_results: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Build safety margin report for a reactor or preset.

    Args:
        reactor_or_preset: Reactor instance, preset name, or path to JSON.
        constraint_set: "regulatory_limits" or "safety_margins". Default: regulatory_limits.
        analysis_results: Precomputed metrics. If None, runs reactor.solve().

    Returns:
        Dict with passed, margins, violations, metrics (from SafetyMarginReport.to_dict()).

    Example:
        >>> report = quick_safety_report("valar-10")
        >>> print("Passed:", report["passed"])
    """
    from ..validation.constraints import ConstraintSet
    from ..validation.safety_report import safety_margin_report

    reactor = _resolve_reactor(reactor_or_preset)
    cs = None
    if constraint_set:
        cs = get_constraint_set(constraint_set)
    smr = safety_margin_report(
        reactor, constraint_set=cs, analysis_results=analysis_results
    )
    return smr.to_dict()


def _resolve_reactor(
    reactor_or_preset: Union["SimpleReactor", str, Path],
) -> "SimpleReactor":
    """Resolve reactor from preset name, path, or SimpleReactor instance."""
    if hasattr(reactor_or_preset, "solve"):
        return reactor_or_preset
    path = Path(reactor_or_preset)
    if path.suffix in (".json", ".yaml", ".yml") or path.exists():
        return load_reactor(path)
    return create_reactor(str(reactor_or_preset))


def quick_template_from_preset(
    preset_name: str, name: Optional[str] = None
) -> "ReactorTemplate":
    """
    Create a ReactorTemplate from a preset design.

    Args:
        preset_name: Preset design name (e.g., "valar-10").
        name: Template name. Defaults to preset name.

    Returns:
        ReactorTemplate instance with parameters extracted from preset.

    Example:
        >>> tmpl = quick_template_from_preset("valar-10")
        >>> spec = tmpl.instantiate(enrichment=0.20)
    """
    from ..workflows.templates import ReactorTemplate

    return ReactorTemplate.from_preset(preset_name, name=name)


def list_export_formats() -> List[str]:
    """List supported export formats for reactor/converter I/O."""
    return ["json", "openmc", "serpent", "mcnp"]


def list_transient_types() -> List[str]:
    """List available transient analysis type names."""
    return ["reactivity_insertion", "decay_heat_removal", "lumped_thermal"]


def list_uq_sampling_methods() -> List[str]:
    """List sampling methods for quick_uq (method parameter)."""
    return ["mc", "lhs", "sobol"]


def list_optimization_objectives() -> List[str]:
    """List objective names for quick_optimize (objective parameter)."""
    return ["max_keff", "min_neg_keff"]


def list_optimization_methods() -> List[str]:
    """List optimization methods for quick_optimize (method parameter)."""
    return ["differential_evolution", "minimize", "genetic_algorithm"]


def list_distributions() -> List[str]:
    """List distribution names for quick_uq uncertain_params (distribution field)."""
    return ["normal", "uniform", "lognormal", "triangular"]


def list_economics_outputs() -> List[str]:
    """List output keys returned by quick_economics."""
    return ["capital_costs", "operating_costs", "lcoe", "lcoe_breakdown"]


def get_default_config_path() -> Path:
    """Return path to ~/.smrforge/config.yaml."""
    return Path.home() / ".smrforge" / "config.yaml"


def get_benchmark_path(name: Optional[str] = None) -> Path:
    """
    Return path to benchmark definition file.

    Args:
        name: "community" (default), "validation", or filename. None uses "community".

    Returns:
        Path to benchmarks/community_benchmarks.json, validation_benchmarks.json, etc.
    """
    root = Path(__file__).resolve().parents[2] / "benchmarks"
    if name is None or name == "community":
        return root / "community_benchmarks.json"
    if name == "validation":
        return root / "validation_benchmarks.json"
    return root / name


def list_templates() -> List[str]:
    """List template names in ~/.smrforge/templates/."""
    from ..workflows.templates import TemplateLibrary

    lib = TemplateLibrary()
    return lib.list_templates()


def quick_export(
    reactor_or_preset: Union["SimpleReactor", str, Path],
    fmt: str,
    path: Optional[Union[str, Path]] = None,
    **kwargs,
) -> Path:
    """
    Export reactor to a supported format.

    Args:
        reactor_or_preset: SimpleReactor, preset name, or path to reactor JSON.
        fmt: Export format: "json", "openmc", "serpent", or "mcnp".
        path: Output path. Default: output/reactor.<ext> for file, output/openmc_export for openmc.
        **kwargs: Passed to converter (e.g., particles, batches for openmc).

    Returns:
        Path to the exported file or directory (for openmc).

    Example:
        >>> quick_export("valar-10", "json", "my_reactor.json")
        >>> quick_export("valar-10", "openmc", "openmc_run")
    """
    reactor = _resolve_reactor(reactor_or_preset)
    fmt_lower = fmt.lower().strip()
    if fmt_lower not in list_export_formats():
        raise ValueError(f"format must be one of {list_export_formats()}, got {fmt!r}")

    if path is None:
        base = get_default_output_dir()
        if fmt_lower == "openmc":
            path = base / "openmc_export"
        else:
            ext = {"json": ".json", "serpent": ".serp", "mcnp": ".mcnp"}.get(
                fmt_lower, ".out"
            )
            path = base / f"reactor{ext}"
    path = Path(path)

    if fmt_lower == "json":
        if hasattr(reactor.spec, "model_dump"):
            data = reactor.spec.model_dump()
        else:
            data = dict(reactor.spec) if hasattr(reactor.spec, "__iter__") else {}
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return path

    if fmt_lower == "openmc":
        from ..io.converters import OpenMCConverter

        path.mkdir(parents=True, exist_ok=True)
        OpenMCConverter.export_reactor(
            reactor,
            path,
            particles=kwargs.get("particles", 1000),
            batches=kwargs.get("batches", 20),
        )
        return path

    if fmt_lower == "serpent":
        from ..io.converters import SerpentConverter

        if path.suffix not in (".serp", ".inp", ""):
            path = path.with_suffix(".serp")
        path.parent.mkdir(parents=True, exist_ok=True)
        SerpentConverter.export_reactor(reactor, path)
        return path

    if fmt_lower == "mcnp":
        from ..io.converters import MCNPConverter

        if path.suffix not in (".mcnp", ".inp", ""):
            path = path.with_suffix(".mcnp")
        path.parent.mkdir(parents=True, exist_ok=True)
        MCNPConverter.export_reactor(reactor, path)
        return path

    raise ValueError(f"Unsupported format: {fmt}")


def get_config(key: Optional[str] = None) -> Union[Dict[str, Any], Any]:
    """
    Read SMRForge configuration from ~/.smrforge/config.yaml.

    Args:
        key: Optional dotted key (e.g., "endf.default_directory"). If None, returns full config.

    Returns:
        Full config dict if key is None; otherwise the value for the key.

    Example:
        >>> cfg = get_config()
        >>> endf_dir = get_config("endf.default_directory")
    """
    try:
        import yaml
    except ImportError:
        raise ImportError(
            "get_config requires PyYAML. Install: pip install pyyaml"
        ) from None
    config_file = Path.home() / ".smrforge" / "config.yaml"
    if not config_file.exists():
        return {} if key is None else None
    with open(config_file, "r") as f:
        config = yaml.safe_load(f) or {}
    if key is None:
        return config
    parts = key.split(".")
    val = config
    for p in parts:
        val = val.get(p) if isinstance(val, dict) else None
        if val is None:
            return None
    return val


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

        try:
            from ..presets.msr import LiquidFuelMSR

            preset_class_map["msr-liquid"] = LiquidFuelMSR
        except ImportError:
            pass

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


def _resolve_reactor(reactor_or_preset: Union[str, Path, "SimpleReactor"]) -> "SimpleReactor":
    """Load reactor from path or preset name."""
    if isinstance(reactor_or_preset, (str, Path)):
        p = Path(reactor_or_preset)
        return load_reactor(p) if p.exists() else create_reactor(name=str(reactor_or_preset))
    return reactor_or_preset


# Re-export from convenience_utils for main API consistency
def get_nuclide(name: str) -> "Nuclide":
    """Parse nuclide string (e.g. 'U235') to Nuclide instance."""
    from ..convenience_utils import get_nuclide as _get_nuclide

    return _get_nuclide(name)


def quick_decay_heat(
    nuclides: Dict[str, float],
    time_seconds: float = 86400.0,
    cache: Optional[Any] = None,
) -> float:
    """One-liner decay heat calculation [W] for nuclide inventory."""
    from ..convenience_utils import quick_decay_heat as _quick_decay_heat

    return _quick_decay_heat(nuclides, time_seconds, cache)


def quick_validation_run(
    endf_dir: Optional[Union[str, Path]] = None,
    benchmarks_path: Optional[Union[str, Path]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    test_files: Optional[List[str]] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Run validation suite (mirror of CLI `validate run`).

    Args:
        endf_dir: Path to ENDF-B-VIII.1 (uses SMRFORGE_ENDF_DIR if None).
        benchmarks_path: Path to validation_benchmarks.json.
        output_dir: Output directory for reports (default: output/validation).
        test_files: Specific test files (default: comprehensive + e2e).
        verbose: Pass -s to pytest.

    Returns:
        Dict with exit_code, report_path, json_path, metadata.
    """
    import os

    import pytest

    base = Path(__file__).resolve().parents[2]
    if benchmarks_path is None:
        benchmarks_path = base / "benchmarks" / "validation_benchmarks.json"
    else:
        benchmarks_path = Path(benchmarks_path)
    if endf_dir:
        endf_abs = str(Path(endf_dir).absolute())
        os.environ["LOCAL_ENDF_DIR"] = endf_abs
        os.environ["SMRFORGE_ENDF_DIR"] = endf_abs
    out_dir = Path(output_dir) if output_dir else base / "output" / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = out_dir / f"validation_report_{timestamp}.txt"
    json_path = out_dir / f"validation_report_{timestamp}.json"
    files = test_files or [
        "tests/test_validation_comprehensive.py",
        "tests/test_endf_workflows_e2e.py",
    ]
    pytest_args = list(files) + ["-v", "--tb=short"]
    if verbose:
        pytest_args.append("-s")
    exit_code = pytest.main(pytest_args)
    return {
        "exit_code": exit_code,
        "report_path": str(report_path),
        "json_path": str(json_path),
        "benchmarks_path": str(benchmarks_path),
    }


def quick_openmc_run(
    reactor: Union["SimpleReactor", "PrismaticCore", "PebbleBedCore"],
    output_dir: Optional[Union[str, Path]] = None,
    particles: int = 1000,
    batches: int = 20,
    timeout: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Export reactor to OpenMC, run, parse statepoint in one call.

    Args:
        reactor: Reactor or core to export.
        output_dir: Output dir (default: openmc_run).
        particles: Neutrons per generation.
        batches: Number of batches.
        timeout: Run timeout [s].

    Returns:
        Dict with returncode, k_eff, k_eff_std, batches, tallies, etc.
    """
    from ..io.openmc_export import export_reactor_to_openmc
    from ..io.openmc_run import run_and_parse

    out = Path(output_dir or "openmc_run")
    if hasattr(reactor, "build_core") and not hasattr(reactor, "core"):
        reactor.build_core()
    export_reactor_to_openmc(reactor, out, particles=particles, batches=batches)
    return run_and_parse(out, timeout=timeout)


def quick_preprocessed_data(
    nuclides: Union[str, List[Any]] = "common_smr",
    output_dir: Optional[Union[str, Path]] = None,
    offline_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Download preprocessed library with sensible defaults.

    Args:
        nuclides: Set name ('common_smr', 'quickstart') or list of Nuclide.
        output_dir: Output directory (default: standard ENDF dir).
        offline_path: Air-gapped path to existing .zarr or ENDF dir.

    Returns:
        Dict with downloaded, failed, output_dir, etc.
    """
    from ..data_downloader import download_preprocessed_library

    return download_preprocessed_library(
        nuclides=nuclides,
        output_dir=output_dir,
        offline_path=offline_path,
        show_progress=True,
    )


def quick_design_study(
    reactor_or_preset: Union[str, Path, "SimpleReactor"],
    output_dir: Optional[Union[str, Path]] = None,
    constraint_set: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Run design point + safety report in one call.

    Args:
        reactor_or_preset: Reactor, preset name, or path to JSON.
        output_dir: Output directory (default: design_study_output).
        constraint_set: Optional ConstraintSet (default: regulatory limits).

    Returns:
        Dict with design_point, safety_report, output_dir.
    """
    from ..validation.safety_report import safety_margin_report

    r = _resolve_reactor(reactor_or_preset)
    out = Path(output_dir or "design_study_output")
    out.mkdir(parents=True, exist_ok=True)
    point = get_design_point(r)
    with open(out / "design_point.json", "w", encoding="utf-8") as f:
        json.dump(point, f, indent=2)
    if constraint_set is None:
        from ..validation.constraints import ConstraintSet

        constraint_set = ConstraintSet.get_regulatory_limits()
    report = safety_margin_report(r, constraint_set=constraint_set)
    with open(out / "safety_report.json", "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2)
    return {"design_point": point, "safety_report": report.to_dict(), "output_dir": str(out)}


def quick_atlas(
    presets: Optional[List[str]] = None,
    output_dir: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """
    Build design-space atlas for selected presets.

    Args:
        presets: Preset names (default: all from list_presets).
        output_dir: Output directory (default: atlas_output).

    Returns:
        List of AtlasEntry-like dicts (design_id, power_mw, passed, etc.).
    """
    from dataclasses import asdict

    from ..workflows.atlas import build_atlas

    out = Path(output_dir or "atlas_output")
    entries = build_atlas(out, presets=presets)
    return [asdict(e) for e in entries]


def list_validation_benchmarks(
    benchmarks_path: Optional[Union[str, Path]] = None,
) -> Dict[str, List[str]]:
    """
    List benchmark IDs from validation_benchmarks.json.

    Returns:
        Dict with keys decay_heat, cross_section, burnup, gamma_transport;
        values are lists of benchmark IDs.
    """
    base = Path(__file__).resolve().parents[2]
    path = Path(benchmarks_path) if benchmarks_path else base / "benchmarks" / "validation_benchmarks.json"
    if not path.exists():
        return {"decay_heat": [], "cross_section": [], "burnup": [], "gamma_transport": []}
    data = json.loads(path.read_text())
    return {
        "decay_heat": list(data.get("decay_heat_benchmarks", {}).keys()),
        "cross_section": list(data.get("cross_section_benchmarks", {}).keys()),
        "burnup": list(data.get("burnup_benchmarks", {}).keys()),
        "gamma_transport": list(data.get("gamma_transport_benchmarks", {}).keys()),
    }


def list_preset_types() -> Dict[str, List[str]]:
    """
    List presets grouped by reactor type (HTGR, LWR, MSR).

    Returns:
        Dict mapping type name to list of preset IDs.
    """
    presets = list_presets()
    htgr = ["valar-10", "gt-mhr-350", "htr-pm-200", "micro-htgr-1"]
    lwr = ["nuscale-77mwe", "smart-100mwe", "carem-32mwe", "bwrx-300"]
    msr = ["msr-liquid"]
    out: Dict[str, List[str]] = {"HTGR": [], "LWR": [], "MSR": []}
    for p in presets:
        if p in htgr:
            out["HTGR"].append(p)
        elif p in lwr:
            out["LWR"].append(p)
        elif p in msr:
            out["MSR"].append(p)
    return out


def list_pro_features() -> List[str]:
    """List Pro-only feature names for upgrade messaging."""
    return [
        "Serpent export/import",
        "OpenMC tally visualization",
        "MCNP full export",
        "Natural-language design",
        "Code-to-code verification",
        "Regulatory package (NRC/IAEA)",
        "Benchmark reproduction",
        "Multi-objective optimization",
        "AI/surrogate workflows",
        "Physics-informed surrogates",
    ]


def list_tier_capabilities() -> Dict[str, Dict[str, bool]]:
    """Summary of Community vs Pro capabilities for current install."""
    return {
        "Community": {
            "diffusion": True,
            "builtin_mc": True,
            "openmc_export": True,
            "basic_reporting": True,
        },
        "Pro": {
            "serpent": pro_available(),
            "tally_viz": pro_available(),
            "cad_import": pro_available(),
            "dagmc_import": pro_available(),
            "advanced_variance_reduction": pro_available(),
            "mcnp_full": pro_available(),
            "nl_design": pro_available(),
            "code_verify": pro_available(),
            "regulatory_package": pro_available(),
            "benchmark_reproduce": pro_available(),
            "multi_optimize": pro_available(),
            "surrogate": pro_available(),
        },
    }


def get_tier_info() -> Dict[str, Any]:
    """Get tier summary (equivalent to list_tier_capabilities with extra metadata)."""
    cap = list_tier_capabilities()
    cap["pro_available"] = pro_available()
    cap["current_tier"] = "Pro" if pro_available() else "Community"
    return cap


def list_workflows() -> List[str]:
    """List workflow subcommand names (smrforge workflow <name>)."""
    return [
        "run",
        "batch-keff",
        "design-point",
        "safety-report",
        "doe",
        "pareto",
        "optimize",
        "uq",
        "design-study",
        "variant",
        "sensitivity",
        "sobol",
        "scenario",
        "atlas",
        "surrogate",
        "surrogate-validate",
        "code-verify",
        "regulatory-package",
        "benchmark",
        "multi-optimize",
        "requirements-to-constraints",
        "ml-export",
        "nl-design",
    ]


def list_convenience_functions(
    group_by_prefix: bool = False,
) -> Union[List[str], Dict[str, List[str]]]:
    """
    List all convenience function names (quick_*, list_*, get_*).

    Args:
        group_by_prefix: If True, return dict with keys quick, list, get.

    Returns:
        List of names, or dict of lists if group_by_prefix.
    """
    try:
        import smrforge as smr

        names = [n for n in dir(smr) if not n.startswith("_")]
    except ImportError:
        names = []
    quick = sorted([n for n in names if n.startswith("quick_")])
    lst = sorted([n for n in names if n.startswith("list_")])
    get = sorted([n for n in names if n.startswith("get_")])
    if group_by_prefix:
        return {"quick": quick, "list": lst, "get": get}
    return quick + lst + get


def list_cli_commands() -> List[Dict[str, str]]:
    """List top-level CLI commands with help text (smrforge <command>)."""
    return [
        {"command": "serve", "help": "Launch the SMRForge web dashboard"},
        {"command": "shell", "help": "Launch interactive Python shell with SMRForge pre-loaded"},
        {"command": "workflow", "help": "Workflow operations"},
        {"command": "reactor", "help": "Reactor operations (create, analyze, list, compare)"},
        {"command": "data", "help": "Data management (setup, download, validate)"},
        {"command": "burnup", "help": "Burnup/depletion operations"},
        {"command": "decay", "help": "Decay heat calculations"},
        {"command": "validate", "help": "Validation and testing"},
        {"command": "visualize", "help": "Visualization (geometry, flux)"},
        {"command": "sweep", "help": "Parameter sweep and sensitivity"},
        {"command": "report", "help": "Generate design reports"},
        {"command": "config", "help": "Configuration management"},
        {"command": "github", "help": "GitHub Actions workflow management"},
        {"command": "transient", "help": "Transient analysis"},
        {"command": "thermal", "help": "Thermal-hydraulics operations"},
    ]


def get_quick_start_commands() -> List[Dict[str, str]]:
    """Suggested first commands for new users."""
    return [
        {"api": "create_reactor('valar-10')", "cli": "smrforge reactor create --preset valar-10 --output reactor.json", "desc": "Create a reactor from preset"},
        {"api": "quick_keff('valar-10')", "cli": "smrforge reactor analyze --reactor reactor.json --keff", "desc": "Compute k-eff"},
        {"api": "list_presets()", "cli": "smrforge reactor list", "desc": "List presets"},
        {"api": "quick_design_study('valar-10')", "cli": "smrforge workflow design-study --reactor valar-10", "desc": "Design point + safety report"},
        {"api": "help()", "cli": "smrforge shell  # then smr.help()", "desc": "Interactive help"},
    ]


def list_functions_by_category(category: str) -> List[str]:
    """
    List functions grouped by category (geometry, neutronics, burnup, etc.).

    Args:
        category: One of geometry, neutronics, burnup, thermal, decay, gamma,
                  visualization, materials, nuclides, convenience, workflows.

    Returns:
        List of function/class names in that category.
    """
    _CATEGORY_MAP: Dict[str, List[str]] = {
        "geometry": ["create_simple_core", "PrismaticCore", "PebbleBedCore", "quick_mesh_extraction"],
        "neutronics": ["quick_keff", "MultiGroupDiffusion", "create_simple_solver", "quick_keff_calculation"],
        "burnup": ["quick_burnup_calculation", "BurnupSolver", "BurnupOptions"],
        "thermal": ["ChannelThermalHydraulics", "ThermalHydraulics"],
        "decay": ["quick_decay_heat", "DecayHeatCalculator", "decay_heat_removal"],
        "gamma": ["GammaTransportSolver", "GammaTransportOptions"],
        "visualization": ["quick_plot_core", "quick_plot_mesh", "plot_core_layout"],
        "materials": ["get_material", "list_materials"],
        "nuclides": ["get_nuclide", "create_nuclide_list", "list_nuclides"],
        "convenience": ["create_reactor", "quick_validate", "quick_sweep", "quick_design_study", "load_reactor"],
        "workflows": ["quick_doe", "quick_pareto", "quick_sensitivity", "quick_atlas"],
    }
    c = category.lower()
    if c not in _CATEGORY_MAP:
        return []
    return _CATEGORY_MAP[c]


def find_endf_directory() -> Optional[Path]:
    """
    Search common locations for ENDF data directory.

    Checks: SMRFORGE_ENDF_DIR, LOCAL_ENDF_DIR, ~/ENDF-Data, standard paths.

    Returns:
        Path if found (and has content), else None.
    """
    import os

    from ..core.reactor_core import get_standard_endf_directory

    for env in ("SMRFORGE_ENDF_DIR", "LOCAL_ENDF_DIR"):
        val = os.environ.get(env)
        if val:
            p = Path(val).expanduser().resolve()
            if p.is_dir():
                return p
    default = get_standard_endf_directory()
    if default.is_dir():
        return default
    return None


def get_data_paths() -> Dict[str, Path]:
    """Return dict of standard paths (endf, output, config, examples)."""
    base = Path(__file__).resolve().parents[2]
    try:
        endf = get_default_endf_dir()
        output = get_default_output_dir()
    except Exception:
        endf = Path.home() / "ENDF-Data"
        output = base / "output"
    return {
        "endf": endf,
        "output": output,
        "config": base / "config",
        "examples": base / "examples",
        "benchmarks": base / "benchmarks",
    }


def list_available_benchmarks(
    benchmarks_path: Optional[Union[str, Path]] = None,
    detailed: bool = False,
) -> Union[Dict[str, List[str]], Dict[str, Dict[str, Any]]]:
    """
    List validation benchmarks, optionally with metadata.

    Args:
        benchmarks_path: Path to validation_benchmarks.json.
        detailed: If True, return full benchmark metadata per ID.

    Returns:
        If detailed=False: dict of category -> list of IDs.
        If detailed=True: dict of category -> {id: benchmark_dict}.
    """
    base = Path(__file__).resolve().parents[2]
    path = Path(benchmarks_path) if benchmarks_path else base / "benchmarks" / "validation_benchmarks.json"
    if not path.exists():
        return {"decay_heat": {}, "cross_section": {}, "burnup": {}, "gamma_transport": {}} if detailed else {"decay_heat": [], "cross_section": [], "burnup": [], "gamma_transport": []}
    data = json.loads(path.read_text())
    cats = ["decay_heat", "cross_section", "burnup", "gamma_transport"]
    key_map = {"decay_heat": "decay_heat_benchmarks", "cross_section": "cross_section_benchmarks", "burnup": "burnup_benchmarks", "gamma_transport": "gamma_transport_benchmarks"}
    out: Dict[str, Any] = {}
    for c in cats:
        raw = data.get(key_map[c], {})
        if detailed:
            out[c] = dict(raw)
        else:
            out[c] = list(raw.keys())
    return out


def quick_doe(
    method: str = "lhs",
    factors: Union[Dict[str, List[float]], List[Tuple[str, Tuple[float, float]]]] = None,
    n_samples: int = 10,
    seed: Optional[int] = None,
) -> List[Dict[str, float]]:
    """
    Design of Experiments one-liner (factorial, LHS, Sobol, random).

    Args:
        method: 'factorial', 'lhs', 'sobol', 'random'.
        factors: For factorial: {name: [v1,v2,...]}. For lhs/sobol/random: [(name, (low, high)), ...].
        n_samples: Samples for lhs/sobol/random.
        seed: Random seed.

    Returns:
        List of design points (dicts).
    """
    from ..workflows.doe import (
        full_factorial,
        latin_hypercube,
        random_space_filling,
        sobol_space_filling,
    )

    if factors is None:
        factors = [("enrichment", (0.15, 0.25)), ("power_mw", (50.0, 200.0))]
    if isinstance(factors, dict):
        return full_factorial(factors)
    names = [f[0] for f in factors]
    bounds = [f[1] for f in factors]
    m = method.lower()
    if m == "lhs":
        return latin_hypercube(names, bounds, n_samples, seed=seed)
    if m == "sobol":
        return sobol_space_filling(names, bounds, n_samples, seed=seed)
    if m == "random":
        return random_space_filling(names, bounds, n_samples, seed=seed)
    raise ValueError(f"Unknown method '{method}'. Use factorial, lhs, sobol, random.")


def quick_pareto(
    sweep_results: Union[str, Path, List[Dict], Dict],
    metric_x: str = "k_eff",
    metric_y: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Extract Pareto front from sweep results.

    Args:
        sweep_results: Path to JSON or list/dict of results.
        metric_x: First objective column.
        metric_y: Second objective (default: first other numeric).

    Returns:
        List of Pareto-optimal result dicts.
    """
    import numpy as np

    from ..visualization.sweep_plots import _flatten_parameters_column, _pareto_front_mask

    if isinstance(sweep_results, (str, Path)):
        data = json.loads(Path(sweep_results).read_text())
    else:
        data = sweep_results
    results = data.get("results", data) if isinstance(data, dict) else data
    if not isinstance(results, list):
        results = [results]
    try:
        import pandas as pd

        df = pd.DataFrame(results)
        df = _flatten_parameters_column(df)
    except ImportError:
        raise ImportError("pandas required for quick_pareto. pip install pandas")
    numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    my = metric_y or (([c for c in numeric if c != metric_x][0]) if len(numeric) > 1 else (numeric[0] if numeric else None))
    if my is None or metric_x not in df.columns:
        return []
    x = pd.to_numeric(df[metric_x], errors="coerce").to_numpy()
    y = pd.to_numeric(df[my], errors="coerce").to_numpy()
    ok = np.isfinite(x) & np.isfinite(y)
    mask = _pareto_front_mask(x[ok], y[ok], maximize_x=True, maximize_y=True)
    return [results[i] for i in np.where(ok)[0][mask]]


def quick_sensitivity(
    sweep_results: Union[str, Path, List[Dict], Dict],
    params: Optional[List[str]] = None,
    metric: str = "k_eff",
) -> List[Dict[str, Any]]:
    """
    Sensitivity ranking from sweep results (OAT).

    Args:
        sweep_results: Path to JSON or list/dict of results.
        params: Parameter names (default: from first result).
        metric: Output metric to rank by.

    Returns:
        List of {"parameter", "effect", "rank"} dicts.
    """
    from ..workflows.sensitivity import one_at_a_time_from_sweep

    if isinstance(sweep_results, (str, Path)):
        data = json.loads(Path(sweep_results).read_text())
    else:
        data = sweep_results
    results = data.get("results", data) if isinstance(data, dict) else data
    if not isinstance(results, list):
        results = [results]
    if not params and results:
        p0 = results[0].get("parameters", results[0])
        params = [k for k in p0 if isinstance(p0.get(k), (int, float))]
    if not params:
        return []
    rankings = one_at_a_time_from_sweep(results, params, output_metric=metric)
    return [{"parameter": r.parameter, "effect": r.effect, "rank": r.rank} for r in rankings]


def _require_pro(feature: str) -> None:
    """Raise if Pro is not available."""
    if not pro_available():
        raise ImportError(
            f"{feature} requires SMRForge Pro. Upgrade: https://smrforge.io or pip install smrforge-pro"
        )


def quick_code_verify(
    reactor_or_preset: Union[str, Path, "SimpleReactor"],
    codes: Optional[List[str]] = None,
    output_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Code-to-code verification (Pro)."""
    _require_pro("Code-to-code verification")
    from smrforge_pro.workflows.code_verification import run_code_verification

    r = _resolve_reactor(reactor_or_preset)
    return run_code_verification(r, codes=codes or ["diffusion", "openmc"], output_path=Path(output_path) if output_path else None)


def quick_regulatory_package(
    reactor_or_preset: Union[str, Path, "SimpleReactor"],
    output_dir: Optional[Union[str, Path]] = None,
    preset: str = "10_CFR_50",
) -> Dict[str, Any]:
    """Generate regulatory submission package (Pro)."""
    _require_pro("Regulatory package")
    from smrforge_pro.workflows.regulatory_package import generate_regulatory_package

    r = _resolve_reactor(reactor_or_preset)
    return generate_regulatory_package(r, Path(output_dir or "regulatory_package"), preset=preset)


def quick_benchmark_reproduce(
    benchmark_id: str,
    output_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Reproduce benchmark and compare to reference (Pro)."""
    _require_pro("Benchmark reproduction")
    from smrforge_pro.workflows.benchmark_reproduction import reproduce_benchmark

    return reproduce_benchmark(benchmark_id, output_dir=Path(output_dir) if output_dir else None)


def quick_surrogate_fit(
    sweep_results: Union[str, Path, List[Dict], Dict],
    params: List[str],
    metric: str = "k_eff",
    method: str = "rbf",
    output_path: Optional[Union[str, Path]] = None,
) -> Any:
    """Fit surrogate from sweep results (Pro)."""
    _require_pro("Surrogate fit")
    from smrforge_pro.workflows.surrogate import surrogate_from_sweep_results

    if isinstance(sweep_results, (str, Path)):
        data = json.loads(Path(sweep_results).read_text())
    else:
        data = sweep_results
    results = data.get("results", data) if isinstance(data, dict) else data
    if not isinstance(results, list):
        results = [results]
    return surrogate_from_sweep_results(results, params, output_metric=metric, method=method, output_path=output_path)


def quick_nl_design(spec: str) -> "ReactorSpecification":
    """Parse natural-language design spec to reactor spec (Pro)."""
    _require_pro("Natural-language design")
    from smrforge_pro.workflows.nl_design import parse_nl_design

    return parse_nl_design(spec)


def quick_multi_optimize(
    reactor_path: Union[str, Path],
    param_bounds: Dict[str, Tuple[float, float]],
    objectives: Optional[List[Tuple[str, str]]] = None,
    max_iter: int = 50,
    output_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Multi-objective optimization (Pro)."""
    _require_pro("Multi-objective optimization")
    from smrforge_pro.workflows.multi_objective_optimization import multi_objective_optimize

    with open(Path(reactor_path)) as f:
        template = json.load(f)
    obj = objectives or [("k_eff", "max")]
    return multi_objective_optimize(
        template,
        objectives=obj,
        param_bounds=param_bounds,
        max_iterations=max_iter,
        output_path=Path(output_path) if output_path else None,
    )


def quick_tally_visualization(
    statepoint_path: Union[str, Path],
    tally_ids: Optional[List[int]] = None,
    output_path: Optional[Union[str, Path]] = None,
) -> Any:
    """Load OpenMC tally HDF5 and plot (Pro)."""
    _require_pro("Tally visualization")
    from smrforge_pro.workflows.tally_visualization import plot_tally

    return plot_tally(
        Path(statepoint_path),
        tally_ids=tally_ids,
        output_path=Path(output_path) if output_path else None,
    )


def quick_sweep(
    preset_or_reactor: Union[str, Path, "SimpleReactor"],
    params: Dict[str, Union[tuple, list]],
    analysis: str = "keff",
    output_path: Optional[Union[str, Path]] = None,
    parallel: bool = False,
    display: bool = False,
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
        display: If True, print a Rich summary table (when Rich available).
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

    analysis_types = (
        [analysis] if analysis in ("keff", "neutronics", "burnup") else ["keff"]
    )
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

    out = {
        "results": result.results,
        "failed_cases": result.failed_cases,
        "summary_stats": result.summary_stats,
    }
    if display:
        _display_sweep_summary(out)
    return out


def quick_economics(
    reactor_or_preset: Union["SimpleReactor", str, Path],
    nth_of_a_kind: int = 1,
    display: bool = False,
    **kwargs,
) -> Dict:
    """
    Quick cost estimate from reactor or preset.

    Args:
        reactor_or_preset: SimpleReactor, preset name, or path to reactor JSON.
        nth_of_a_kind: Nth-of-a-kind (1 = FOAK).
        display: If True, print a Rich summary table (when Rich available).
        display: If True, print a Rich summary table (when Rich available).
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

    result = estimate_costs_from_spec(spec, nth_of_a_kind=nth_of_a_kind, **kwargs)
    if display:
        _display_economics_summary(result)
    return result


def quick_optimize(
    reactor_or_preset: Union["SimpleReactor", str, Path],
    params: Dict[str, Tuple[float, float]],
    objective: str = "max_keff",
    max_iter: int = 50,
    method: str = "differential_evolution",
    display: bool = False,
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
        display: If True, print a Rich summary table (when Rich available).
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

    kwargs_opt = {k: v for k, v in kwargs.items() if k != "display"}
    opt = DesignOptimizer(obj, bounds, method=method, **kwargs_opt)
    result = opt.optimize(max_iterations=max_iter, **kwargs_opt)

    optimal_point = dict(zip(param_names, result.x_opt.tolist()))
    optimal_point["k_eff"] = (
        -result.f_opt if obj_name in ("max_keff", "min_neg_keff") else result.f_opt
    )

    out = {
        "x_opt": result.x_opt.tolist(),
        "f_opt": float(result.f_opt),
        "param_names": param_names,
        "optimal_point": optimal_point,
        "success": result.success,
        "n_iterations": result.n_iterations,
        "message": result.message,
    }
    if display:
        _display_optimize_summary(out)
    return out


def quick_uq(
    reactor_or_preset: Union["SimpleReactor", str, Path],
    uncertain_params: List[Dict],
    n_samples: int = 100,
    method: str = "lhs",
    output_names: Optional[List[str]] = None,
    random_state: Optional[int] = 42,
    display: bool = False,
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
        display: If True, print a Rich summary table (when Rich available).
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

    result_out: Dict = {
        "mean": uq_results.mean.tolist() if uq_results.mean is not None else [],
        "std": uq_results.std.tolist() if uq_results.std is not None else [],
        "output_names": getattr(uq_results, "output_names", out_names),
    }
    if display:
        _display_uq_summary(result_out)
    return result_out


def _display_sweep_summary(out: Dict) -> None:
    """Print Rich table for quick_sweep results."""
    try:
        from rich.console import Console
        from rich.table import Table

        tbl = Table(title="Parameter Sweep Summary")
        tbl.add_column("Metric", style="cyan")
        tbl.add_column("Value", justify="right")
        tbl.add_row("Cases", str(len(out.get("results", []))))
        tbl.add_row("Failed", str(len(out.get("failed_cases", []))))
        stats = out.get("summary_stats", {})
        if "k_eff" in stats:
            for k, v in stats["k_eff"].items():
                tbl.add_row(f"k_eff {k}", f"{v:.4g}")
        Console().print(tbl)
    except ImportError:
        pass


def _display_economics_summary(result: Dict) -> None:
    """Print Rich table for quick_economics results."""
    try:
        from rich.console import Console
        from rich.table import Table

        tbl = Table(title="Economics Summary")
        tbl.add_column("Metric", style="cyan")
        tbl.add_column("Value", justify="right")
        if "lcoe" in result:
            v = result["lcoe"]
            tbl.add_row("LCOE", f"${float(v):.2f}/kWh")
        cap = result.get("capital_costs")
        if cap is not None:
            v = (
                cap.get("total_overnight_cost", cap.get("total", cap))
                if isinstance(cap, dict)
                else cap
            )
            tbl.add_row(
                "Capital",
                f"${float(v):,.0f}" if isinstance(v, (int, float)) else str(v),
            )
        op = result.get("operating_costs")
        if op is not None:
            v = (
                op.get("total_operating_cost", op.get("total", op))
                if isinstance(op, dict)
                else op
            )
            tbl.add_row(
                "Operating (annual)",
                f"${float(v):,.0f}" if isinstance(v, (int, float)) else str(v),
            )
        Console().print(tbl)
    except (ImportError, TypeError, KeyError):
        pass


def _display_optimize_summary(out: Dict) -> None:
    """Print Rich table for quick_optimize results."""
    try:
        from rich.console import Console
        from rich.table import Table

        tbl = Table(title="Optimization Summary")
        tbl.add_column("Parameter", style="cyan")
        tbl.add_column("Value", justify="right")
        for k, v in out.get("optimal_point", {}).items():
            tbl.add_row(k, f"{v:.4g}" if isinstance(v, (int, float)) else str(v))
        tbl.add_row(
            "Success", "[green]yes[/green]" if out.get("success") else "[red]no[/red]"
        )
        Console().print(tbl)
    except ImportError:
        pass


def _display_uq_summary(result: Dict) -> None:
    """Print Rich table for quick_uq results."""
    try:
        from rich.console import Console
        from rich.table import Table

        tbl = Table(title="UQ Summary")
        tbl.add_column("Output", style="cyan")
        tbl.add_column("Mean", justify="right")
        tbl.add_column("Std", justify="right")
        names = result.get("output_names", [])
        means = result.get("mean", [])
        stds = result.get("std", [])
        for i, name in enumerate(names):
            m = means[i] if i < len(means) else "—"
            s = stds[i] if i < len(stds) else "—"
            tbl.add_row(
                name,
                f"{m:.4g}" if isinstance(m, (int, float)) else str(m),
                f"{s:.4g}" if isinstance(s, (int, float)) else str(s),
            )
        Console().print(tbl)
    except ImportError:
        pass


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
                logger.warning(
                    "Solution validation failed, but returning k_eff = %.6f. Error: %s",
                    k_eff_val,
                    e,
                )
                return k_eff_val
            raise

    def solve(self) -> Dict:
        from ..utils.progress import phase_progress

        with phase_progress(
            ["Geometry & cross-sections", "Solving", "Power distribution"],
            verbose=True,
        ) as set_phase:
            set_phase(0)
            solver = self._get_solver()
            set_phase(1)
            k_eff, flux = solver.solve_steady_state()

            results: Dict[str, object] = {
                "k_eff": float(k_eff),
                "flux": flux,
                "name": self.spec.name,
                "power_thermal_mw": self.spec.power_thermal / 1e6,
            }

            set_phase(2)
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
    "get_default_endf_dir",
    "list_endf_libraries",
    "list_geometry_types",
    "list_analysis_types",
    "list_surrogates",
    "quick_download_endf",
    "quick_benchmark",
    "quick_safety_report",
    "quick_template_from_preset",
    "list_export_formats",
    "list_transient_types",
    "list_uq_sampling_methods",
    "list_optimization_objectives",
    "list_optimization_methods",
    "list_distributions",
    "list_economics_outputs",
    "get_default_config_path",
    "get_benchmark_path",
    "list_templates",
    "quick_export",
    "get_config",
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
    "get_nuclide",
    "quick_decay_heat",
    "quick_validation_run",
    "quick_openmc_run",
    "quick_preprocessed_data",
    "quick_design_study",
    "quick_atlas",
    "list_validation_benchmarks",
    "list_preset_types",
    "list_pro_features",
    "list_tier_capabilities",
    "get_tier_info",
    "list_workflows",
    "list_convenience_functions",
    "list_cli_commands",
    "get_quick_start_commands",
    "list_functions_by_category",
    "find_endf_directory",
    "get_data_paths",
    "list_available_benchmarks",
    "quick_doe",
    "quick_pareto",
    "quick_sensitivity",
    "quick_code_verify",
    "quick_regulatory_package",
    "quick_benchmark_reproduce",
    "quick_surrogate_fit",
    "quick_nl_design",
    "quick_multi_optimize",
    "quick_tally_visualization",
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
