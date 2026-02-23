"""
Parameter sweep and sensitivity analysis workflow utilities.

This module provides automated parameter sweeps for reactor analysis,
enabling systematic exploration of design parameter space.
"""

import json
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from ..utils.exception_handling import reraise_if_system
from ..utils.logging import get_logger

logger = get_logger("smrforge.workflows")


@dataclass
class SweepConfig:
    """
    Configuration for parameter sweep.

    Attributes:
        parameters: Dictionary mapping parameter names to sweep ranges.
                   Format: {"param_name": (start, end, step)} or {"param_name": [values]}
        analysis_types: List of analysis types to run (e.g., ["keff", "burnup"])
        reactor_template: Template reactor configuration (dict or path to JSON)
        output_dir: Directory for sweep results
        parallel: Whether to run in parallel (default: True)
        max_workers: Maximum number of parallel workers (default: None = auto)
        save_intermediate: Save results after each simulation (default: True)
        surrogate_path: Optional path to surrogate model (.onnx, .pt, .pkl); Pro: use for fast evaluation
        seed: Optional random seed for deterministic runs (Pro)
    """

    parameters: Dict[str, Union[Tuple[float, float, float], List[float]]]
    analysis_types: List[str] = field(default_factory=lambda: ["keff"])
    reactor_template: Optional[Union[Dict, Path, str]] = None
    output_dir: Path = Path("sweep_results")
    parallel: bool = True
    max_workers: Optional[int] = None
    save_intermediate: bool = True
    surrogate_path: Optional[Union[Path, str]] = None
    seed: Optional[int] = None

    def get_parameter_values(self, param_name: str) -> np.ndarray:
        """Get array of values for a parameter."""
        param_spec = self.parameters[param_name]
        if isinstance(param_spec, tuple):
            start, end, step = param_spec
            return np.arange(start, end + step / 2, step)
        elif isinstance(param_spec, list):
            return np.array(param_spec)
        else:
            raise ValueError(f"Invalid parameter specification for {param_name}")

    def get_all_combinations(self) -> List[Dict[str, float]]:
        """Get all parameter combinations as list of dictionaries."""
        param_names = list(self.parameters.keys())
        param_arrays = [self.get_parameter_values(name) for name in param_names]

        # Generate all combinations
        from itertools import product

        combinations = []
        for values in product(*param_arrays):
            combinations.append(dict(zip(param_names, values)))

        return combinations

    @classmethod
    def from_file(cls, path: Union[Path, str]) -> "SweepConfig":
        """
        Load SweepConfig from a JSON or YAML file.

        File format: parameters (param -> [start, end, step] or list of values),
        analysis_types, reactor_template (dict or path string), output_dir, parallel,
        max_workers, save_intermediate.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Sweep config file not found: {path}")
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() in (".yaml", ".yml"):
            try:
                import yaml

                data = yaml.safe_load(text)
            except ImportError:  # pragma: no cover
                raise ImportError("PyYAML required for YAML config: pip install pyyaml")
        else:
            data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("Config file must contain a single dict")
        # Normalize parameters: [a,b,c] or [start,end,step] -> tuple/list
        params = data.get("parameters", {})
        if params:
            normalized = {}
            for name, spec in params.items():
                if isinstance(spec, (list, tuple)):
                    arr = list(spec)
                    if len(arr) == 3 and all(isinstance(x, (int, float)) for x in arr):
                        normalized[name] = (float(arr[0]), float(arr[1]), float(arr[2]))
                    else:
                        normalized[name] = [float(x) for x in arr]
                else:
                    normalized[name] = spec
            data = {**data, "parameters": normalized}
        if "output_dir" in data:
            data["output_dir"] = Path(data["output_dir"])
        if "surrogate_path" in data and data["surrogate_path"]:
            data["surrogate_path"] = Path(data["surrogate_path"])
        return cls(
            **{
                k: v
                for k, v in data.items()
                if k
                in (
                    "parameters",
                    "analysis_types",
                    "reactor_template",
                    "output_dir",
                    "parallel",
                    "max_workers",
                    "save_intermediate",
                    "surrogate_path",
                    "seed",
                )
            }
        )


@dataclass
class SweepResult:
    """
    Results from a parameter sweep.

    Attributes:
        config: SweepConfig used for this sweep
        results: List of result dictionaries, one per parameter combination
        failed_cases: List of failed cases with error messages
        summary_stats: Summary statistics (mean, std, correlation, etc.)
    """

    config: SweepConfig
    results: List[Dict[str, Any]] = field(default_factory=list)
    failed_cases: List[Dict[str, Any]] = field(default_factory=list)
    summary_stats: Dict[str, Any] = field(default_factory=dict)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert results to pandas DataFrame."""
        if not self.results:
            return pd.DataFrame()

        return pd.DataFrame(self.results)

    def save(self, output_path: Path):
        """Save results to file (JSON or Parquet)."""
        output_path = Path(output_path)

        if output_path.suffix == ".parquet":
            df = self.to_dataframe()
            df.to_parquet(output_path, index=False)
        else:
            # JSON format
            data = {
                "config": asdict(self.config),
                "results": self.results,
                "failed_cases": self.failed_cases,
                "summary_stats": self.summary_stats,
            }

            # Convert Path objects to strings for JSON serialization
            def convert_paths(obj):
                if isinstance(obj, Path):
                    return str(obj)
                elif isinstance(obj, dict):
                    return {k: convert_paths(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_paths(item) for item in obj]
                return obj

            data = convert_paths(data)
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2, default=str)

        logger.info(f"Saved sweep results to {output_path}")


class ParameterSweep:
    """
    Parameter sweep workflow manager.

    Provides automated parameter sweeps with parallel execution,
    result aggregation, and statistical analysis.

    Usage:
        >>> from smrforge.workflows import ParameterSweep, SweepConfig
        >>>
        >>> config = SweepConfig(
        ...     parameters={
        ...         "enrichment": (0.10, 0.25, 0.05),
        ...         "power": [50, 75, 100]
        ...     },
        ...     analysis_types=["keff"],
        ...     reactor_template={"preset": "valar-10"}
        ... )
        >>>
        >>> sweep = ParameterSweep(config)
        >>> results = sweep.run()
        >>> results.save("sweep_results.json")
    """

    def __init__(self, config: SweepConfig):
        """
        Initialize parameter sweep.

        Args:
            config: SweepConfig specifying parameters and analysis options
        """
        self.config = config
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        self._surrogate_model = None

    def _get_surrogate(self):
        """Lazy-load surrogate when surrogate_path is set (Pro)."""
        if self._surrogate_model is not None:
            return self._surrogate_model
        if not self.config.surrogate_path:
            return None
        try:
            from smrforge_pro.ai.surrogates import load_surrogate_from_path

            path = Path(self.config.surrogate_path)
            param_names = list(self.config.parameters.keys())
            self._surrogate_model = load_surrogate_from_path(
                path, param_names=param_names
            )
            return self._surrogate_model
        except ImportError:
            logger.warning(
                "surrogate_path set but smrforge_pro not available; using physics"
            )
            return None

    def _run_single_case(self, params: Dict[str, float]) -> Dict[str, Any]:
        """
        Run analysis for a single parameter combination.

        Args:
            params: Dictionary of parameter values for this case

        Returns:
            Dictionary with results including parameters and analysis outputs
        """
        try:
            # Pro: use surrogate when surrogate_path is set
            surrogate = self._get_surrogate()
            if surrogate is not None:
                result = {"parameters": params.copy()}
                for analysis_type in self.config.analysis_types:
                    if analysis_type == "keff":
                        pred = surrogate.predict(params)
                        result["k_eff"] = float(pred)
                    else:
                        result[analysis_type] = None
                result["surrogate"] = True
                return result

            import smrforge as smr
            from smrforge.convenience import create_reactor

            # Create reactor from template with modified parameters
            reactor_spec = self._get_reactor_template()
            reactor_spec.update(params)  # Override with sweep parameters

            reactor = create_reactor(**reactor_spec)

            # Run requested analyses
            result = {"parameters": params.copy()}

            for analysis_type in self.config.analysis_types:
                if analysis_type == "keff":
                    k_eff = reactor.solve_keff()
                    result["k_eff"] = float(k_eff)
                elif analysis_type == "burnup":
                    try:
                        from smrforge.burnup import BurnupOptions, BurnupSolver
                        solver = reactor._get_solver()
                        time_steps = params.get("burnup_days", [0, 365, 730])
                        if isinstance(time_steps, (int, float)):
                            time_steps = [0, float(time_steps)]
                        opts = BurnupOptions(
                            time_steps=time_steps,
                            power_density=params.get("power_density", 1e6),
                            initial_enrichment=params.get("enrichment", 0.195),
                        )
                        burnup = BurnupSolver(solver, opts)
                        burnup.solve()
                        result["burnup"] = {
                            "final_k_eff": float(getattr(solver, "k_eff", 0.0)),
                            "final_burnup_mwd_kg": float(burnup.burnup_mwd_per_kg[-1])
                            if len(burnup.burnup_mwd_per_kg) > 0 else 0.0,
                            "n_nuclides": len(burnup.nuclides),
                            "n_time_steps": len(burnup.time_steps_sec),
                        }
                    except Exception as burnup_err:  # pragma: no cover
                        reraise_if_system(burnup_err)
                        result["burnup"] = {"error": str(burnup_err)}
                elif analysis_type == "neutronics":
                    full_results = reactor.solve()
                    result.update(
                        {
                            k: float(v) if isinstance(v, (int, float, np.number)) else v
                            for k, v in full_results.items()
                        }
                    )

            return result

        except Exception as e:  # pragma: no cover
            reraise_if_system(e)
            logger.error(f"Failed case {params}: {e}")
            return {"parameters": params, "error": str(e), "success": False}

    def _get_reactor_template(self) -> Dict[str, Any]:
        """Get reactor template configuration."""
        if self.config.reactor_template is None:
            return {}

        if isinstance(self.config.reactor_template, (str, Path)):
            path = Path(self.config.reactor_template)
            if path.exists():
                with open(path) as f:
                    return json.load(f)
            else:
                # Try as preset name
                return {"name": str(self.config.reactor_template)}
        elif isinstance(self.config.reactor_template, dict):
            return self.config.reactor_template.copy()
        else:
            return {}

    def _params_key(self, params: Dict[str, float]) -> tuple:
        """Hashable key for a parameter combination (for resume dedup)."""
        return tuple(sorted((k, float(v)) for k, v in params.items()))

    def run(self, resume: bool = False, show_progress: bool = False) -> SweepResult:
        """
        Run parameter sweep.

        Args:
            resume: If True, load latest intermediate file and skip already-done combinations.
            show_progress: If True and Rich is available, show a progress bar.

        Returns:
            SweepResult with all results and statistics
        """
        if self.config.seed is not None:
            np.random.seed(self.config.seed)
        logger.info(
            f"Starting parameter sweep with {len(self.config.parameters)} parameters"
        )

        # Get all parameter combinations
        all_combinations = self.config.get_all_combinations()
        done_keys: set = set()
        results: List[Dict[str, Any]] = []
        failed_cases: List[Dict[str, Any]] = []

        if resume:
            # Find latest intermediate file and load completed combinations
            inter_pattern = self.config.output_dir / "sweep_intermediate_*.json"
            inter_files = sorted(
                self.config.output_dir.glob("sweep_intermediate_*.json"),
                key=lambda p: (
                    int(p.stem.rsplit("_", 1)[-1])
                    if p.stem.rsplit("_", 1)[-1].isdigit()
                    else 0
                ),
            )
            if inter_files:
                latest = inter_files[-1]
                try:
                    with open(latest) as f:
                        data = json.load(f)
                    for r in data.get("results", []):
                        if "parameters" in r:
                            done_keys.add(self._params_key(r["parameters"]))
                            results.append(r)
                    for r in data.get("failed", []):
                        if "parameters" in r:
                            done_keys.add(self._params_key(r["parameters"]))
                            failed_cases.append(r)
                    logger.info(
                        f"Resuming: loaded {len(results)} results, {len(failed_cases)} failed from {latest.name}"
                    )
                except Exception as e:  # pragma: no cover
                    reraise_if_system(e)
                    logger.warning(f"Could not load intermediate {latest}: {e}")

        combinations = [
            c for c in all_combinations if self._params_key(c) not in done_keys
        ]
        n_cases = len(combinations)
        n_total = len(all_combinations)
        if n_cases == 0:
            logger.info("No remaining cases to run (resume: all done)")
            summary_stats = self._calculate_summary_stats(results)
            return SweepResult(
                config=self.config,
                results=results,
                failed_cases=failed_cases,
                summary_stats=summary_stats,
            )
        logger.info(f"Cases to run: {n_cases} (total {n_total})")

        # Resolve max_workers (env SMRFORGE_MAX_BATCH_WORKERS can cap)
        max_workers = self.config.max_workers
        if max_workers is None:
            env_max = os.environ.get("SMRFORGE_MAX_BATCH_WORKERS")
            if env_max is not None:
                try:
                    max_workers = max(1, int(env_max))
                except ValueError:  # pragma: no cover
                    pass
        if max_workers is None:
            max_workers = min(n_cases, 8)

        try:
            from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

            _RICH_AVAILABLE = True
        except ImportError:  # pragma: no cover
            _RICH_AVAILABLE = False

        completed_so_far = 0
        total_done_before = len(results) + len(failed_cases)

        def _advance(progress_cb=None):
            nonlocal completed_so_far
            completed_so_far += 1
            if progress_cb:
                progress_cb(completed_so_far)
            total_done = total_done_before + completed_so_far
            if self.config.save_intermediate and completed_so_far % 10 == 0:
                self._save_intermediate(results, failed_cases, total_done)
            if completed_so_far % max(1, n_cases // 10) == 0:
                logger.info(f"Progress: {completed_so_far}/{n_cases} cases completed")

        if self.config.parallel and n_cases > 1:
            if show_progress and _RICH_AVAILABLE and n_cases > 0:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                ) as progress:
                    task_id = progress.add_task("Sweep...", total=n_cases)
                    progress_cb = lambda n: progress.update(task_id, advance=1)
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        futures = {
                            executor.submit(self._run_single_case, params): params
                            for params in combinations
                        }
                        for future in as_completed(futures):
                            params = futures[future]
                            try:
                                result = future.result()
                                if "error" in result:
                                    failed_cases.append(result)
                                else:
                                    result["success"] = True
                                    results.append(result)
                                _advance(progress_cb)
                            except Exception as e:  # pragma: no cover
                                reraise_if_system(e)
                                logger.error(f"Failed to get result for {params}: {e}")
                                failed_cases.append(
                                    {"parameters": params, "error": str(e)}
                                )
                                _advance(progress_cb)
            else:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {
                        executor.submit(self._run_single_case, params): params
                        for params in combinations
                    }
                    for future in as_completed(futures):
                        params = futures[future]
                        try:
                            result = future.result()
                            if "error" in result:
                                failed_cases.append(result)
                            else:
                                result["success"] = True
                                results.append(result)
                            _advance(None)
                        except Exception as e:  # pragma: no cover
                            reraise_if_system(e)
                            logger.error(f"Failed to get result for {params}: {e}")
                            failed_cases.append({"parameters": params, "error": str(e)})
                            _advance(None)
        else:
            if show_progress and _RICH_AVAILABLE and n_cases > 0:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                ) as progress:
                    task_id = progress.add_task("Sweep...", total=n_cases)
                    progress_cb = lambda n: progress.update(task_id, advance=1)
                    for params in combinations:
                        result = self._run_single_case(params)
                        if "error" in result:
                            failed_cases.append(result)
                        else:
                            result["success"] = True
                            results.append(result)
                        _advance(progress_cb)
            else:
                for params in combinations:
                    result = self._run_single_case(params)
                    if "error" in result:
                        failed_cases.append(result)
                    else:
                        result["success"] = True
                        results.append(result)
                    _advance(None)

        # Calculate summary statistics
        summary_stats = self._calculate_summary_stats(results)

        return SweepResult(
            config=self.config,
            results=results,
            failed_cases=failed_cases,
            summary_stats=summary_stats,
        )

    def _save_intermediate(
        self, results: List[Dict], failed: List[Dict], case_num: int
    ):
        """Save intermediate results."""
        intermediate_file = (
            self.config.output_dir / f"sweep_intermediate_{case_num}.json"
        )
        data = {"results": results, "failed": failed, "case_num": case_num}
        with open(intermediate_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _calculate_summary_stats(self, results: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics from results."""
        if not results:
            return {}

        df = pd.DataFrame(results)
        stats = {}

        # Extract numeric columns (metrics)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [col for col in numeric_cols if col != "success"]

        for col in numeric_cols:
            if col in df.columns:
                stats[col] = {
                    "mean": float(df[col].mean()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "median": float(df[col].median()),
                }

        # Calculate correlations between parameters and results
        param_cols = [
            col
            for col in df.columns
            if col.startswith("parameters_") or col in self.config.parameters
        ]
        if param_cols and numeric_cols:
            correlations = df[param_cols + numeric_cols].corr()
            stats["correlations"] = correlations.to_dict()

        return stats
