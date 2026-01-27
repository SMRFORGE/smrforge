"""
Benchmark data structures and utilities for validation.

This module provides data structures and utilities for storing and comparing
benchmark values from standards (ANSI/ANS, MCNP, IAEA benchmarks, etc.).
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json
import numpy as np


@dataclass
class BenchmarkValue:
    """Single benchmark value with uncertainty."""
    value: float
    uncertainty: Optional[float] = None
    unit: str = ""
    source: str = ""
    notes: str = ""
    
    def relative_error(self, calculated: float) -> float:
        """Calculate relative error between calculated and benchmark value."""
        if self.value == 0:
            return float('inf') if calculated != 0 else 0.0
        return abs((calculated - self.value) / self.value)
    
    def within_uncertainty(self, calculated: float, n_sigma: float = 2.0) -> bool:
        """Check if calculated value is within n_sigma uncertainty."""
        if self.uncertainty is None:
            return False
        diff = abs(calculated - self.value)
        return diff <= n_sigma * self.uncertainty


@dataclass
class DecayHeatBenchmark:
    """ANSI/ANS decay heat benchmark data."""
    test_case: str
    nuclides: Dict[str, float]  # Nuclide name -> concentration
    initial_power: float  # MW
    shutdown_time: float  # seconds
    time_points: List[float]  # seconds
    benchmark_values: List[BenchmarkValue]  # Decay heat at each time point
    standard: str = "ANSI/ANS-5.1"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "test_case": self.test_case,
            "nuclides": self.nuclides,
            "initial_power": self.initial_power,
            "shutdown_time": self.shutdown_time,
            "time_points": self.time_points,
            "benchmark_values": [
                {
                    "value": bv.value,
                    "uncertainty": bv.uncertainty,
                    "unit": bv.unit,
                    "source": bv.source,
                    "notes": bv.notes,
                }
                for bv in self.benchmark_values
            ],
            "standard": self.standard,
        }


@dataclass
class GammaTransportBenchmark:
    """MCNP or other code gamma transport benchmark data."""
    test_case: str
    geometry_description: str
    source_description: str
    energy_groups: List[float]
    benchmark_flux: List[BenchmarkValue]  # Flux at detector location
    benchmark_dose_rate: BenchmarkValue
    reference_code: str = "MCNP"
    reference_version: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "test_case": self.test_case,
            "geometry_description": self.geometry_description,
            "source_description": self.source_description,
            "energy_groups": self.energy_groups,
            "benchmark_flux": [
                {
                    "value": bv.value,
                    "uncertainty": bv.uncertainty,
                    "unit": bv.unit,
                    "source": bv.source,
                }
                for bv in self.benchmark_flux
            ],
            "benchmark_dose_rate": {
                "value": self.benchmark_dose_rate.value,
                "uncertainty": self.benchmark_dose_rate.uncertainty,
                "unit": self.benchmark_dose_rate.unit,
                "source": self.benchmark_dose_rate.source,
            },
            "reference_code": self.reference_code,
            "reference_version": self.reference_version,
        }


@dataclass
class BurnupBenchmark:
    """IAEA or other burnup benchmark data."""
    test_case: str
    problem_description: str
    initial_composition: Dict[str, float]  # Nuclide -> concentration
    time_steps: List[float]  # days
    benchmark_compositions: List[Dict[str, float]]  # Composition at each time step
    benchmark_k_eff: List[BenchmarkValue]  # k-effective at each time step
    reference_source: str = "IAEA"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "test_case": self.test_case,
            "problem_description": self.problem_description,
            "initial_composition": self.initial_composition,
            "time_steps": self.time_steps,
            "benchmark_compositions": self.benchmark_compositions,
            "benchmark_k_eff": [
                {
                    "value": bv.value,
                    "uncertainty": bv.uncertainty,
                    "unit": bv.unit,
                    "source": bv.source,
                }
                for bv in self.benchmark_k_eff
            ],
            "reference_source": self.reference_source,
        }


class BenchmarkDatabase:
    """Database of benchmark values for validation."""
    
    def __init__(self, data_file: Optional[Path] = None):
        """Initialize benchmark database."""
        self.decay_heat_benchmarks: Dict[str, DecayHeatBenchmark] = {}
        self.gamma_transport_benchmarks: Dict[str, GammaTransportBenchmark] = {}
        self.burnup_benchmarks: Dict[str, BurnupBenchmark] = {}
        self.cross_section_benchmarks: Dict[str, Dict[str, Any]] = {}
        self.data_file = data_file
        
        if data_file and data_file.exists():
            self.load(data_file)
    
    def add_decay_heat_benchmark(self, benchmark: DecayHeatBenchmark):
        """Add decay heat benchmark."""
        self.decay_heat_benchmarks[benchmark.test_case] = benchmark
    
    def add_gamma_transport_benchmark(self, benchmark: GammaTransportBenchmark):
        """Add gamma transport benchmark."""
        self.gamma_transport_benchmarks[benchmark.test_case] = benchmark
    
    def add_burnup_benchmark(self, benchmark: BurnupBenchmark):
        """Add burnup benchmark."""
        self.burnup_benchmarks[benchmark.test_case] = benchmark
    
    def save(self, output_file: Path):
        """Save benchmark database to JSON file."""
        data = {
            "decay_heat_benchmarks": {
                name: bm.to_dict()
                for name, bm in self.decay_heat_benchmarks.items()
            },
            "gamma_transport_benchmarks": {
                name: bm.to_dict()
                for name, bm in self.gamma_transport_benchmarks.items()
            },
            "burnup_benchmarks": {
                name: bm.to_dict()
                for name, bm in self.burnup_benchmarks.items()
            },
            "cross_section_benchmarks": self.cross_section_benchmarks,
        }
        
        output_file.write_text(json.dumps(data, indent=2))
    
    def load(self, input_file: Path):
        """Load benchmark database from JSON file."""
        data = json.loads(input_file.read_text())
        
        # Load decay heat benchmarks
        for name, bm_data in data.get("decay_heat_benchmarks", {}).items():
            benchmark_values = [
                BenchmarkValue(
                    value=bv["value"],
                    uncertainty=bv.get("uncertainty"),
                    unit=bv.get("unit", ""),
                    source=bv.get("source", ""),
                    notes=bv.get("notes", ""),
                )
                for bv in bm_data["benchmark_values"]
            ]
            benchmark = DecayHeatBenchmark(
                test_case=bm_data["test_case"],
                nuclides=bm_data["nuclides"],
                initial_power=bm_data["initial_power"],
                shutdown_time=bm_data["shutdown_time"],
                time_points=bm_data["time_points"],
                benchmark_values=benchmark_values,
                standard=bm_data.get("standard", "ANSI/ANS-5.1"),
            )
            self.decay_heat_benchmarks[name] = benchmark
        
        # Load gamma transport benchmarks
        for name, bm_data in data.get("gamma_transport_benchmarks", {}).items():
            benchmark_flux = [
                BenchmarkValue(
                    value=bv["value"],
                    uncertainty=bv.get("uncertainty"),
                    unit=bv.get("unit", ""),
                    source=bv.get("source", ""),
                )
                for bv in bm_data["benchmark_flux"]
            ]
            benchmark_dose_rate = BenchmarkValue(
                value=bm_data["benchmark_dose_rate"]["value"],
                uncertainty=bm_data["benchmark_dose_rate"].get("uncertainty"),
                unit=bm_data["benchmark_dose_rate"].get("unit", ""),
                source=bm_data["benchmark_dose_rate"].get("source", ""),
            )
            benchmark = GammaTransportBenchmark(
                test_case=bm_data["test_case"],
                geometry_description=bm_data["geometry_description"],
                source_description=bm_data["source_description"],
                energy_groups=bm_data["energy_groups"],
                benchmark_flux=benchmark_flux,
                benchmark_dose_rate=benchmark_dose_rate,
                reference_code=bm_data.get("reference_code", "MCNP"),
                reference_version=bm_data.get("reference_version", ""),
            )
            self.gamma_transport_benchmarks[name] = benchmark
        
        # Load burnup benchmarks
        for name, bm_data in data.get("burnup_benchmarks", {}).items():
            benchmark_k_eff = [
                BenchmarkValue(
                    value=bv["value"],
                    uncertainty=bv.get("uncertainty"),
                    unit=bv.get("unit", ""),
                    source=bv.get("source", ""),
                )
                for bv in bm_data["benchmark_k_eff"]
            ]
            benchmark = BurnupBenchmark(
                test_case=bm_data["test_case"],
                problem_description=bm_data["problem_description"],
                initial_composition=bm_data["initial_composition"],
                time_steps=bm_data["time_steps"],
                benchmark_compositions=bm_data["benchmark_compositions"],
                benchmark_k_eff=benchmark_k_eff,
                reference_source=bm_data.get("reference_source", "IAEA"),
            )
            self.burnup_benchmarks[name] = benchmark
        
        # Load cross-section benchmarks (simple dict format)
        self.cross_section_benchmarks = data.get("cross_section_benchmarks", {})


def compare_with_benchmark(
    calculated: float,
    benchmark: BenchmarkValue,
    tolerance: float = 0.05,  # 5% default tolerance
) -> Dict[str, Any]:
    """
    Compare calculated value with benchmark.
    
    Returns:
        Dictionary with comparison results including:
        - relative_error: Relative error
        - absolute_error: Absolute error
        - within_tolerance: Boolean
        - within_uncertainty: Boolean (if uncertainty available)
    """
    relative_error = benchmark.relative_error(calculated)
    absolute_error = abs(calculated - benchmark.value)
    within_tolerance = relative_error <= tolerance
    within_uncertainty = benchmark.within_uncertainty(calculated) if benchmark.uncertainty else None
    
    return {
        "calculated": calculated,
        "benchmark": benchmark.value,
        "relative_error": relative_error,
        "relative_error_percent": relative_error * 100,
        "absolute_error": absolute_error,
        "within_tolerance": within_tolerance,
        "within_uncertainty": within_uncertainty,
        "tolerance": tolerance,
    }
