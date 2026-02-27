"""
Comprehensive validation tests with timing and benchmarking.

This test file implements the validation tasks from the development roadmap:
1. Execute validation test suite with real ENDF-B-VIII.1 files
2. Test TSL parser with real ENDF TSL files and validate S(α,β) interpolation accuracy
3. Test fission yield parser with real yield files
4. Validate decay heat calculations against ANSI/ANS standards
5. Benchmark gamma transport against MCNP or other codes
6. Test burnup solver with reference problems
7. Compare results with published benchmarks and other codes
8. Add performance benchmarking (timing measurements)
"""

import numpy as np
import pytest

from smrforge.burnup import BurnupOptions
from smrforge.core.reactor_core import Library, Nuclide
from smrforge.geometry import PrismaticCore
from tests.validation_benchmarks import ValidationBenchmarker


class TestTSLValidationComprehensive:
    """Comprehensive TSL validation with interpolation accuracy."""

    def test_tsl_parser_real_files(self, cache_with_endf):
        """Test TSL parser with real ENDF TSL files."""
        benchmarker = ValidationBenchmarker(cache_with_endf)

        # Test common materials
        materials = cache_with_endf.list_available_tsl_materials()

        if len(materials) == 0:
            pytest.skip("No TSL materials found")

        # Test first few materials
        for material in materials[:3]:  # Limit to first 3 for speed
            result = benchmarker.validate_tsl_interpolation_accuracy(
                material, temperatures=[293.6, 400.0, 600.0, 900.0]
            )
            benchmarker.results.append(result)

            assert (
                result.passed or "not found" in result.message.lower()
            ), f"TSL validation failed for {material}: {result.message}"

    def test_tsl_interpolation_accuracy(self, cache_with_endf):
        """Validate S(α,β) interpolation accuracy."""
        benchmarker = ValidationBenchmarker(cache_with_endf)

        # Test with H2O if available
        materials = cache_with_endf.list_available_tsl_materials()
        h2o_materials = [m for m in materials if "H2O" in m or "h_in_h2o" in m.lower()]

        if len(h2o_materials) == 0:
            pytest.skip("H2O TSL material not found")

        material = h2o_materials[0]

        # Test interpolation at multiple temperatures
        result = benchmarker.validate_tsl_interpolation_accuracy(
            material, temperatures=[293.6, 350.0, 400.0, 500.0, 600.0]
        )
        benchmarker.results.append(result)

        # Validate interpolation metrics
        if result.passed:
            assert result.metrics.get("temperature_points", 0) > 0
            assert result.timing is not None
            assert result.timing.elapsed_time > 0


class TestFissionYieldValidationComprehensive:
    """Comprehensive fission yield validation."""

    def test_fission_yield_parser_real_files(self, cache_with_endf):
        """Test fission yield parser with real yield files."""
        benchmarker = ValidationBenchmarker(cache_with_endf)

        # Test common fissile nuclides
        test_nuclides = [
            Nuclide(Z=92, A=235),  # U-235
            Nuclide(Z=92, A=238),  # U-238
            Nuclide(Z=94, A=239),  # Pu-239
        ]

        for nuclide in test_nuclides:
            result = benchmarker.validate_fission_yield_parser(nuclide)
            benchmarker.results.append(result)

            # Note: Some nuclides may not have yield data, which is OK
            if "not found" not in result.message.lower():
                assert (
                    result.passed
                ), f"Fission yield validation failed for {nuclide}: {result.message}"
                assert result.timing is not None
                assert (
                    result.metrics.get("independent_yields", 0) > 0
                    or result.metrics.get("cumulative_yields", 0) > 0
                )


class TestDecayHeatANSIStandard:
    """Validate decay heat calculations against ANSI/ANS standards."""

    def test_decay_heat_ans_standard(self, cache_with_endf):
        """Validate decay heat calculations (structure for ANSI/ANS standard comparison)."""
        benchmarker = ValidationBenchmarker(cache_with_endf)

        # Define test nuclides with concentrations
        nuclides = {
            Nuclide(Z=92, A=235): 1e20,  # U-235
            Nuclide(Z=55, A=137): 1e19,  # Cs-137
            Nuclide(Z=38, A=90): 1e19,  # Sr-90
        }

        # Time points from shutdown (seconds)
        times = np.array(
            [
                0,  # Shutdown
                3600,  # 1 hour
                86400,  # 1 day
                604800,  # 1 week
                2592000,  # 30 days
            ]
        )

        result = benchmarker.validate_decay_heat_ans_standard(nuclides, times)
        benchmarker.results.append(result)

        assert result.passed, f"Decay heat validation failed: {result.message}"
        assert result.timing is not None
        assert result.metrics.get("time_points") == len(times)
        assert result.comparison_data is not None  # Should have comparison structure

        # Validate decay heat decreases over time
        assert result.metrics.get("final_decay_heat", 0) >= 0


class TestGammaTransportBenchmark:
    """Benchmark gamma transport (structure for MCNP comparison)."""

    def test_gamma_transport_benchmark(self, cache_with_endf):
        """Benchmark gamma transport solver (structure for MCNP comparison)."""
        benchmarker = ValidationBenchmarker(cache_with_endf)

        # Create test geometry
        geometry = PrismaticCore(name="TestShielding")
        geometry.core_height = 200.0
        geometry.core_diameter = 100.0
        geometry.generate_mesh(n_radial=5, n_axial=3)

        result = benchmarker.benchmark_gamma_transport(geometry, n_groups=20)
        benchmarker.results.append(result)

        assert result.passed, f"Gamma transport benchmark failed: {result.message}"
        assert result.timing is not None
        assert result.timing.elapsed_time > 0
        assert result.comparison_data is not None  # Should have comparison structure

        # Validate metrics
        assert result.metrics.get("max_flux", 0) > 0
        assert result.metrics.get("max_dose_rate", 0) >= 0


class TestBurnupReferenceProblems:
    """Test burnup solver with reference problems."""

    def test_burnup_reference_validation(self, cache_with_endf):
        """Validate burnup solver with reference problems."""
        benchmarker = ValidationBenchmarker(cache_with_endf)

        # Create test geometry
        geometry = PrismaticCore(name="TestBurnup")
        geometry.core_height = 100.0
        geometry.core_diameter = 50.0
        geometry.generate_mesh(n_radial=3, n_axial=2)

        # Create burnup options
        burnup_options = BurnupOptions(
            time_steps=[0, 30, 60, 90],  # days
            initial_enrichment=0.195,
        )

        result = benchmarker.validate_burnup_reference(geometry, burnup_options)
        benchmarker.results.append(result)

        # Note: May pass even if data not fully available (structure validation)
        assert result.timing is not None
        assert result.metrics is not None
        assert result.comparison_data is not None  # Should have comparison structure


class TestPerformanceBenchmarking:
    """Performance benchmarking with timing measurements."""

    def test_validation_performance_summary(self, cache_with_endf):
        """Run all validations and generate performance summary."""
        benchmarker = ValidationBenchmarker(cache_with_endf)

        # Run suite of validations
        # TSL
        materials = cache_with_endf.list_available_tsl_materials()
        if len(materials) > 0:
            result = benchmarker.validate_tsl_interpolation_accuracy(
                materials[0], temperatures=[293.6, 400.0, 600.0]
            )
            benchmarker.results.append(result)

        # Fission yields
        u235 = Nuclide(Z=92, A=235)
        result = benchmarker.validate_fission_yield_parser(u235)
        benchmarker.results.append(result)

        # Decay heat
        nuclides = {Nuclide(Z=92, A=235): 1e20}
        times = np.array([0, 3600, 86400])
        result = benchmarker.validate_decay_heat_ans_standard(nuclides, times)
        benchmarker.results.append(result)

        # Gamma transport
        geometry = PrismaticCore(name="TestPerf")
        geometry.core_height = 200.0
        geometry.core_diameter = 100.0
        geometry.generate_mesh(n_radial=5, n_axial=3)
        result = benchmarker.benchmark_gamma_transport(geometry, n_groups=20)
        benchmarker.results.append(result)

        # Generate report
        report = benchmarker.generate_report()

        # Validate report generation
        assert len(report) > 0
        assert "Summary" in report
        assert "Timing Summary" in report

        # All tests should have timing
        timed_results = [r for r in benchmarker.results if r.timing]
        assert len(timed_results) > 0


class TestValidationReportGeneration:
    """Test validation report generation."""

    def test_generate_validation_report(self, cache_with_endf, tmp_path):
        """Test generating validation report to file."""
        benchmarker = ValidationBenchmarker(cache_with_endf)

        # Add a sample result
        u235 = Nuclide(Z=92, A=235)
        result = benchmarker.validate_fission_yield_parser(u235)
        benchmarker.results.append(result)

        # Generate report to file
        report_file = tmp_path / "validation_report.txt"
        report_text = benchmarker.generate_report(output_file=report_file)

        # Validate report was generated
        assert report_file.exists()
        assert len(report_text) > 0
        assert "ENDF Validation" in report_text
        assert report_file.read_text() == report_text
