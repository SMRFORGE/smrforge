"""
Parameter sweep and sensitivity analysis workflow utilities.

This module provides automated parameter sweeps for reactor analysis,
enabling systematic exploration of design parameter space.
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import numpy as np
import pandas as pd

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
    """
    parameters: Dict[str, Union[Tuple[float, float, float], List[float]]]
    analysis_types: List[str] = field(default_factory=lambda: ["keff"])
    reactor_template: Optional[Union[Dict, Path, str]] = None
    output_dir: Path = Path("sweep_results")
    parallel: bool = True
    max_workers: Optional[int] = None
    save_intermediate: bool = True
    
    def get_parameter_values(self, param_name: str) -> np.ndarray:
        """Get array of values for a parameter."""
        param_spec = self.parameters[param_name]
        if isinstance(param_spec, tuple):
            start, end, step = param_spec
            return np.arange(start, end + step/2, step)
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
        
        if output_path.suffix == '.parquet':
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
            with open(output_path, 'w') as f:
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
        
    def _run_single_case(self, params: Dict[str, float]) -> Dict[str, Any]:
        """
        Run analysis for a single parameter combination.
        
        Args:
            params: Dictionary of parameter values for this case
        
        Returns:
            Dictionary with results including parameters and analysis outputs
        """
        try:
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
                    # Would need burnup solver setup
                    result["burnup"] = None  # Placeholder
                elif analysis_type == "neutronics":
                    full_results = reactor.solve()
                    result.update({k: float(v) if isinstance(v, (int, float, np.number)) else v 
                                  for k, v in full_results.items()})
            
            return result
            
        except Exception as e:
            logger.error(f"Failed case {params}: {e}")
            return {
                "parameters": params,
                "error": str(e),
                "success": False
            }
    
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
    
    def run(self) -> SweepResult:
        """
        Run parameter sweep.
        
        Returns:
            SweepResult with all results and statistics
        """
        logger.info(f"Starting parameter sweep with {len(self.config.parameters)} parameters")
        
        # Get all parameter combinations
        combinations = self.config.get_all_combinations()
        n_cases = len(combinations)
        logger.info(f"Total cases: {n_cases}")
        
        results = []
        failed_cases = []
        
        # Run cases
        if self.config.parallel and n_cases > 1:
            # Parallel execution
            max_workers = self.config.max_workers or min(n_cases, 8)
            logger.info(f"Running {n_cases} cases in parallel (max_workers={max_workers})")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(self._run_single_case, params): params 
                          for params in combinations}
                
                for i, future in enumerate(as_completed(futures), 1):
                    params = futures[future]
                    try:
                        result = future.result()
                        if "error" in result:
                            failed_cases.append(result)
                        else:
                            result["success"] = True
                            results.append(result)
                        
                        if self.config.save_intermediate and i % 10 == 0:
                            self._save_intermediate(results, failed_cases, i)
                        
                        if i % max(1, n_cases // 10) == 0:
                            logger.info(f"Progress: {i}/{n_cases} cases completed")
                    except Exception as e:
                        logger.error(f"Failed to get result for {params}: {e}")
                        failed_cases.append({"parameters": params, "error": str(e)})
        else:
            # Sequential execution
            logger.info(f"Running {n_cases} cases sequentially")
            for i, params in enumerate(combinations, 1):
                result = self._run_single_case(params)
                if "error" in result:
                    failed_cases.append(result)
                else:
                    result["success"] = True
                    results.append(result)
                
                if self.config.save_intermediate and i % 10 == 0:
                    self._save_intermediate(results, failed_cases, i)
                
                if i % max(1, n_cases // 10) == 0:
                    logger.info(f"Progress: {i}/{n_cases} cases completed")
        
        # Calculate summary statistics
        summary_stats = self._calculate_summary_stats(results)
        
        return SweepResult(
            config=self.config,
            results=results,
            failed_cases=failed_cases,
            summary_stats=summary_stats
        )
    
    def _save_intermediate(self, results: List[Dict], failed: List[Dict], case_num: int):
        """Save intermediate results."""
        intermediate_file = self.config.output_dir / f"sweep_intermediate_{case_num}.json"
        data = {"results": results, "failed": failed, "case_num": case_num}
        with open(intermediate_file, 'w') as f:
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
        param_cols = [col for col in df.columns if col.startswith("parameters_") or col in self.config.parameters]
        if param_cols and numeric_cols:
            correlations = df[param_cols + numeric_cols].corr()
            stats["correlations"] = correlations.to_dict()
        
        return stats
