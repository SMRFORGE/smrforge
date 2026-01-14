"""
Standards data parser for validation benchmarks.

This module provides parsers for standards-based benchmark data including:
- ANSI/ANS-5.1 decay heat standard
- IAEA benchmarks
- Other nuclear standards

The parser loads standard benchmark values and integrates them with the
BenchmarkDatabase for validation testing.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import json
import re

from ..utils.logging import get_logger

logger = get_logger("smrforge.validation.standards_parser")


class StandardType(Enum):
    """Type of standard benchmark data."""
    ANSI_ANS_5_1 = "ANSI/ANS-5.1"  # Decay heat standard
    IAEA_BENCHMARK = "IAEA"  # IAEA benchmarks
    MCNP_REFERENCE = "MCNP"  # MCNP reference calculations
    CUSTOM = "CUSTOM"  # Custom benchmark data


@dataclass
class StandardsBenchmarkData:
    """Standard benchmark data structure."""
    standard_type: StandardType
    test_case: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "standard_type": self.standard_type.value,
            "test_case": self.test_case,
            "data": self.data,
            "metadata": self.metadata,
        }


class StandardsParser:
    """
    Parser for standards-based benchmark data.
    
    Supports parsing benchmark data from:
    - ANSI/ANS-5.1 decay heat standard (tabular data)
    - IAEA benchmark problems (JSON/YAML format)
    - MCNP reference calculations
    - Custom benchmark data files
    
    Usage:
        >>> parser = StandardsParser()
        >>> 
        >>> # Load ANSI/ANS-5.1 data
        >>> benchmarks = parser.parse_ansi_ans_5_1("path/to/ans_ans_5_1_data.json")
        >>> 
        >>> # Load IAEA benchmark
        >>> iaea_benchmark = parser.parse_iaea_benchmark("path/to/iaea_benchmark.json")
        >>> 
        >>> # Convert to BenchmarkDatabase format
        >>> from tests.validation_benchmark_data import BenchmarkDatabase
        >>> db = BenchmarkDatabase()
        >>> parser.load_into_database(benchmarks, db)
    """
    
    def __init__(self):
        """Initialize standards parser."""
        self.parsed_benchmarks: List[StandardsBenchmarkData] = []
    
    def parse_ansi_ans_5_1(
        self, 
        data_file: Union[Path, str],
        encoding: str = "utf-8"
    ) -> List[StandardsBenchmarkData]:
        """
        Parse ANSI/ANS-5.1 decay heat standard data.
        
        ANSI/ANS-5.1 provides standard decay heat values for various
        reactor operating conditions. This parser loads benchmark values
        from JSON or text files containing standard decay heat data.
        
        Expected format (JSON):
        {
            "standard": "ANSI/ANS-5.1",
            "benchmarks": [
                {
                    "test_case": "u235_thermal_fission",
                    "nuclides": {"U235": 1.0},
                    "initial_power": 100.0,
                    "operating_time": 86400.0,
                    "time_points": [3600, 86400, 604800],
                    "decay_heat_values": [
                        {"time": 3600, "value": 0.07, "unit": "MW"},
                        {"time": 86400, "value": 0.04, "unit": "MW"}
                    ]
                }
            ]
        }
        
        Args:
            data_file: Path to standards data file (JSON format)
            encoding: File encoding (default: utf-8)
        
        Returns:
            List of StandardsBenchmarkData objects
        """
        data_file = Path(data_file)
        
        if not data_file.exists():
            logger.warning(f"Standards data file not found: {data_file}")
            return []
        
        try:
            with open(data_file, "r", encoding=encoding) as f:
                data = json.load(f)
            
            benchmarks = []
            
            # Parse ANSI/ANS-5.1 format
            if "standard" in data and data["standard"] == "ANSI/ANS-5.1":
                for bm_data in data.get("benchmarks", []):
                    benchmark = StandardsBenchmarkData(
                        standard_type=StandardType.ANSI_ANS_5_1,
                        test_case=bm_data.get("test_case", "unknown"),
                        data=bm_data,
                        metadata={
                            "standard": "ANSI/ANS-5.1",
                            "source_file": str(data_file),
                        }
                    )
                    benchmarks.append(benchmark)
            
            # Also support direct benchmark format (from BenchmarkDatabase)
            elif "decay_heat_benchmarks" in data:
                for test_case, bm_data in data["decay_heat_benchmarks"].items():
                    if bm_data.get("standard") == "ANSI/ANS-5.1":
                        benchmark = StandardsBenchmarkData(
                            standard_type=StandardType.ANSI_ANS_5_1,
                            test_case=test_case,
                            data=bm_data,
                            metadata={
                                "standard": "ANSI/ANS-5.1",
                                "source_file": str(data_file),
                            }
                        )
                        benchmarks.append(benchmark)
            
            logger.info(f"Parsed {len(benchmarks)} ANSI/ANS-5.1 benchmarks from {data_file}")
            return benchmarks
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON file {data_file}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing ANSI/ANS-5.1 data from {data_file}: {e}")
            return []
    
    def parse_iaea_benchmark(
        self,
        data_file: Union[Path, str],
        encoding: str = "utf-8"
    ) -> Optional[StandardsBenchmarkData]:
        """
        Parse IAEA benchmark problem data.
        
        IAEA benchmarks provide reference problems for validation of
        nuclear codes. This parser loads IAEA benchmark data from
        JSON or YAML files.
        
        Args:
            data_file: Path to IAEA benchmark data file
            encoding: File encoding (default: utf-8)
        
        Returns:
            StandardsBenchmarkData object or None if parsing fails
        """
        data_file = Path(data_file)
        
        if not data_file.exists():
            logger.warning(f"IAEA benchmark file not found: {data_file}")
            return None
        
        try:
            with open(data_file, "r", encoding=encoding) as f:
                if data_file.suffix.lower() == ".yaml" or data_file.suffix.lower() == ".yml":
                    try:
                        import yaml
                        data = yaml.safe_load(f)
                    except ImportError:
                        logger.error("YAML support requires pyyaml package")
                        return None
                else:
                    data = json.load(f)
            
            # Extract test case name
            test_case = data.get("test_case") or data.get("problem_name") or data_file.stem
            
            benchmark = StandardsBenchmarkData(
                standard_type=StandardType.IAEA_BENCHMARK,
                test_case=test_case,
                data=data,
                metadata={
                    "standard": "IAEA",
                    "source_file": str(data_file),
                    "benchmark_id": data.get("benchmark_id", ""),
                }
            )
            
            logger.info(f"Parsed IAEA benchmark: {test_case}")
            return benchmark
            
        except Exception as e:
            logger.error(f"Error parsing IAEA benchmark from {data_file}: {e}")
            return None
    
    def parse_mcnp_reference(
        self,
        data_file: Union[Path, str],
        encoding: str = "utf-8"
    ) -> Optional[StandardsBenchmarkData]:
        """
        Parse MCNP reference calculation data.
        
        MCNP reference calculations provide benchmark values for
        comparison. This parser loads MCNP results from output files
        or summary JSON files.
        
        Args:
            data_file: Path to MCNP reference data file
            encoding: File encoding (default: utf-8)
        
        Returns:
            StandardsBenchmarkData object or None if parsing fails
        """
        data_file = Path(data_file)
        
        if not data_file.exists():
            logger.warning(f"MCNP reference file not found: {data_file}")
            return None
        
        try:
            with open(data_file, "r", encoding=encoding) as f:
                data = json.load(f)
            
            test_case = data.get("test_case") or data.get("problem_name") or data_file.stem
            
            benchmark = StandardsBenchmarkData(
                standard_type=StandardType.MCNP_REFERENCE,
                test_case=test_case,
                data=data,
                metadata={
                    "standard": "MCNP",
                    "source_file": str(data_file),
                    "mcnp_version": data.get("mcnp_version", ""),
                }
            )
            
            logger.info(f"Parsed MCNP reference: {test_case}")
            return benchmark
            
        except Exception as e:
            logger.error(f"Error parsing MCNP reference from {data_file}: {e}")
            return None
    
    def parse_custom_benchmark(
        self,
        data_file: Union[Path, str],
        standard_name: str = "CUSTOM",
        encoding: str = "utf-8"
    ) -> Optional[StandardsBenchmarkData]:
        """
        Parse custom benchmark data file.
        
        Args:
            data_file: Path to custom benchmark data file (JSON format)
            standard_name: Name of the standard/benchmark source
            encoding: File encoding (default: utf-8)
        
        Returns:
            StandardsBenchmarkData object or None if parsing fails
        """
        data_file = Path(data_file)
        
        if not data_file.exists():
            logger.warning(f"Custom benchmark file not found: {data_file}")
            return None
        
        try:
            with open(data_file, "r", encoding=encoding) as f:
                data = json.load(f)
            
            test_case = data.get("test_case") or data_file.stem
            
            benchmark = StandardsBenchmarkData(
                standard_type=StandardType.CUSTOM,
                test_case=test_case,
                data=data,
                metadata={
                    "standard": standard_name,
                    "source_file": str(data_file),
                }
            )
            
            logger.info(f"Parsed custom benchmark: {test_case}")
            return benchmark
            
        except Exception as e:
            logger.error(f"Error parsing custom benchmark from {data_file}: {e}")
            return None
    
    def load_into_database(
        self,
        benchmarks: List[StandardsBenchmarkData],
        database: Any,  # BenchmarkDatabase
    ) -> int:
        """
        Load parsed benchmarks into BenchmarkDatabase.
        
        Converts StandardsBenchmarkData objects into the format expected
        by BenchmarkDatabase and adds them to the database.
        
        Args:
            benchmarks: List of StandardsBenchmarkData objects
            database: BenchmarkDatabase instance
        
        Returns:
            Number of benchmarks successfully loaded
        """
        from tests.validation_benchmark_data import (
            DecayHeatBenchmark,
            GammaTransportBenchmark,
            BurnupBenchmark,
            BenchmarkValue,
        )
        
        loaded_count = 0
        
        for benchmark in benchmarks:
            try:
                if benchmark.standard_type == StandardType.ANSI_ANS_5_1:
                    # Convert to DecayHeatBenchmark
                    bm_data = benchmark.data
                    
                    benchmark_values = []
                    if "benchmark_values" in bm_data:
                        # Already in BenchmarkDatabase format
                        for bv in bm_data["benchmark_values"]:
                            benchmark_values.append(BenchmarkValue(
                                value=bv.get("value", 0.0),
                                uncertainty=bv.get("uncertainty"),
                                unit=bv.get("unit", ""),
                                source=bv.get("source", "ANSI/ANS-5.1"),
                                notes=bv.get("notes", ""),
                            ))
                    elif "decay_heat_values" in bm_data:
                        # Convert from standards format
                        for dhv in bm_data["decay_heat_values"]:
                            benchmark_values.append(BenchmarkValue(
                                value=dhv.get("value", 0.0),
                                uncertainty=dhv.get("uncertainty"),
                                unit=dhv.get("unit", "MW"),
                                source="ANSI/ANS-5.1",
                                notes=dhv.get("notes", ""),
                            ))
                    
                    decay_heat_bm = DecayHeatBenchmark(
                        test_case=bm_data.get("test_case", benchmark.test_case),
                        nuclides=bm_data.get("nuclides", {}),
                        initial_power=bm_data.get("initial_power", 0.0),
                        shutdown_time=bm_data.get("shutdown_time", 0.0),
                        time_points=bm_data.get("time_points", []),
                        benchmark_values=benchmark_values,
                        standard="ANSI/ANS-5.1",
                    )
                    
                    database.add_decay_heat_benchmark(decay_heat_bm)
                    loaded_count += 1
                
                elif benchmark.standard_type == StandardType.IAEA_BENCHMARK:
                    # Convert to BurnupBenchmark (IAEA benchmarks are typically burnup problems)
                    bm_data = benchmark.data
                    
                    benchmark_k_eff = []
                    for keff_data in bm_data.get("benchmark_k_eff", []):
                        if isinstance(keff_data, dict):
                            benchmark_k_eff.append(BenchmarkValue(
                                value=keff_data.get("value", 0.0),
                                uncertainty=keff_data.get("uncertainty"),
                                unit=keff_data.get("unit", ""),
                                source="IAEA",
                                notes=keff_data.get("notes", ""),
                            ))
                    
                    burnup_bm = BurnupBenchmark(
                        test_case=bm_data.get("test_case", benchmark.test_case),
                        problem_description=bm_data.get("problem_description", ""),
                        initial_composition=bm_data.get("initial_composition", {}),
                        time_steps=bm_data.get("time_steps", []),
                        benchmark_compositions=bm_data.get("benchmark_compositions", []),
                        benchmark_k_eff=benchmark_k_eff,
                        reference_source="IAEA",
                    )
                    
                    database.add_burnup_benchmark(burnup_bm)
                    loaded_count += 1
                
                elif benchmark.standard_type == StandardType.MCNP_REFERENCE:
                    # Convert to appropriate benchmark type based on data
                    bm_data = benchmark.data
                    
                    if "benchmark_flux" in bm_data or "benchmark_dose_rate" in bm_data:
                        # Gamma transport benchmark
                        benchmark_flux = []
                        for flux_data in bm_data.get("benchmark_flux", []):
                            if isinstance(flux_data, dict):
                                benchmark_flux.append(BenchmarkValue(
                                    value=flux_data.get("value", 0.0),
                                    uncertainty=flux_data.get("uncertainty"),
                                    unit=flux_data.get("unit", "photons/cm²/s"),
                                    source=f"MCNP {bm_data.get('mcnp_version', '')}",
                                    notes=flux_data.get("notes", ""),
                                ))
                        
                        benchmark_dose_rate = BenchmarkValue(
                            value=bm_data.get("benchmark_dose_rate", {}).get("value", 0.0),
                            uncertainty=bm_data.get("benchmark_dose_rate", {}).get("uncertainty"),
                            unit=bm_data.get("benchmark_dose_rate", {}).get("unit", "Sv/h"),
                            source=f"MCNP {bm_data.get('mcnp_version', '')}",
                            notes="",
                        )
                        
                        gamma_bm = GammaTransportBenchmark(
                            test_case=bm_data.get("test_case", benchmark.test_case),
                            geometry_description=bm_data.get("geometry_description", ""),
                            source_description=bm_data.get("source_description", ""),
                            energy_groups=bm_data.get("energy_groups", []),
                            benchmark_flux=benchmark_flux,
                            benchmark_dose_rate=benchmark_dose_rate,
                            reference_code="MCNP",
                            reference_version=bm_data.get("mcnp_version", ""),
                        )
                        
                        database.add_gamma_transport_benchmark(gamma_bm)
                        loaded_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to load benchmark {benchmark.test_case} into database: {e}")
                continue
        
        logger.info(f"Loaded {loaded_count} benchmarks into database")
        return loaded_count
    
    def parse_directory(
        self,
        directory: Union[Path, str],
        pattern: Optional[str] = None,
    ) -> List[StandardsBenchmarkData]:
        """
        Parse all standards data files in a directory.
        
        Args:
            directory: Directory containing standards data files
            pattern: Optional glob pattern to match files (e.g., "*.json")
        
        Returns:
            List of parsed StandardsBenchmarkData objects
        """
        directory = Path(directory)
        
        if not directory.is_dir():
            logger.warning(f"Directory not found: {directory}")
            return []
        
        benchmarks = []
        
        # Default pattern
        if pattern is None:
            pattern = "*.json"
        
        # Find all matching files
        for data_file in directory.glob(pattern):
            try:
                # Try to determine standard type from filename/content
                if "ansi" in data_file.name.lower() or "ans" in data_file.name.lower():
                    parsed = self.parse_ansi_ans_5_1(data_file)
                    benchmarks.extend(parsed)
                elif "iaea" in data_file.name.lower():
                    parsed = self.parse_iaea_benchmark(data_file)
                    if parsed:
                        benchmarks.append(parsed)
                elif "mcnp" in data_file.name.lower():
                    parsed = self.parse_mcnp_reference(data_file)
                    if parsed:
                        benchmarks.append(parsed)
                else:
                    # Try as custom benchmark
                    parsed = self.parse_custom_benchmark(data_file)
                    if parsed:
                        benchmarks.append(parsed)
            except Exception as e:
                logger.warning(f"Failed to parse {data_file}: {e}")
                continue
        
        logger.info(f"Parsed {len(benchmarks)} benchmarks from {directory}")
        return benchmarks


def parse_standards_data(
    data_file: Union[Path, str],
    standard_type: Optional[StandardType] = None,
) -> List[StandardsBenchmarkData]:
    """
    Convenience function to parse standards data.
    
    Args:
        data_file: Path to standards data file
        standard_type: Optional standard type (auto-detected if None)
    
    Returns:
        List of parsed StandardsBenchmarkData objects
    """
    parser = StandardsParser()
    data_file = Path(data_file)
    
    if standard_type is None:
        # Auto-detect from filename and file content
        name_lower = data_file.name.lower()
        
        # Try to peek at file content to determine type
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                content = f.read()
                data = json.loads(content)
                
                # Check content for standard type
                if "standard" in data and data.get("standard") == "ANSI/ANS-5.1":
                    return parser.parse_ansi_ans_5_1(data_file)
                elif "decay_heat_benchmarks" in data:
                    # Check if any benchmark has ANSI/ANS-5.1 standard
                    for bm_data in data.get("decay_heat_benchmarks", {}).values():
                        if bm_data.get("standard") == "ANSI/ANS-5.1":
                            return parser.parse_ansi_ans_5_1(data_file)
                elif "benchmark_id" in data or "iaea" in name_lower:
                    result = parser.parse_iaea_benchmark(data_file)
                    return [result] if result else []
                elif "mcnp_version" in data or "mcnp" in name_lower:
                    result = parser.parse_mcnp_reference(data_file)
                    return [result] if result else []
        except (json.JSONDecodeError, Exception):
            # If content parsing fails, fall back to filename
            pass
        
        # Fall back to filename-based detection
        if "ansi" in name_lower or "ans" in name_lower:
            return parser.parse_ansi_ans_5_1(data_file)
        elif "iaea" in name_lower:
            result = parser.parse_iaea_benchmark(data_file)
            return [result] if result else []
        elif "mcnp" in name_lower:
            result = parser.parse_mcnp_reference(data_file)
            return [result] if result else []
        else:
            result = parser.parse_custom_benchmark(data_file)
            return [result] if result else []
    else:
        # Use specified type
        if standard_type == StandardType.ANSI_ANS_5_1:
            return parser.parse_ansi_ans_5_1(data_file)
        elif standard_type == StandardType.IAEA_BENCHMARK:
            result = parser.parse_iaea_benchmark(data_file)
            return [result] if result else []
        elif standard_type == StandardType.MCNP_REFERENCE:
            result = parser.parse_mcnp_reference(data_file)
            return [result] if result else []
        else:
            result = parser.parse_custom_benchmark(data_file)
            return [result] if result else []
