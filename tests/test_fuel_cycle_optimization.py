"""
Unit tests for fuel cycle optimization module.
"""

import builtins
import importlib
import sys

import numpy as np
import pytest

from smrforge.fuel_cycle.optimization import (
    FuelCycleOptimizer,
    RefuelingStrategyOptimizer,
)


class TestFuelCycleOptimizer:
    """Tests for FuelCycleOptimizer class."""

    def test_optimize_cycle_length(self):
        """Test cycle length optimization."""
        optimizer = FuelCycleOptimizer(
            power_thermal=100e6,
            target_keff=1.0,
            max_cycle_length=2000.0,
            min_cycle_length=365.0,
        )

        # Mock burnup solver
        def burnup_solver(cycle_length):
            # Simulate: longer cycle -> lower k_eff, higher burnup
            keff = 1.05 - 0.0001 * (cycle_length - 365.0) / 365.0
            burnup = 10.0 + 0.01 * (cycle_length - 365.0) / 365.0
            return keff, burnup

        result = optimizer.optimize_cycle_length(burnup_solver)

        assert "optimal_cycle_length" in result
        assert result["optimal_cycle_length"] >= optimizer.min_cycle_length
        assert result["optimal_cycle_length"] <= optimizer.max_cycle_length

    def test_optimize_cycle_length_hits_good_match_branch(self):
        optimizer = FuelCycleOptimizer(power_thermal=100e6, target_keff=1.0)

        def burnup_solver(cycle_length):
            # Always hits the "good match" branch on the first mid evaluation.
            return 1.0, float(cycle_length)

        result = optimizer.optimize_cycle_length(burnup_solver)
        assert result["k_eff"] == pytest.approx(1.0)
        assert result["discharge_burnup"] > 0.0

    def test_optimize_cycle_length_increases_low_when_too_short(self):
        """Cover keff < target branch (low = mid)."""
        optimizer = FuelCycleOptimizer(power_thermal=100e6, target_keff=1.0)

        def burnup_solver(cycle_length):
            return 0.5, 0.0  # always too short / undercritical

        result = optimizer.optimize_cycle_length(burnup_solver)
        assert (
            optimizer.min_cycle_length
            <= result["optimal_cycle_length"]
            <= optimizer.max_cycle_length
        )

    def test_optimize_enrichment(self):
        """Test enrichment optimization."""
        optimizer = FuelCycleOptimizer(power_thermal=100e6)

        # Mock burnup solver
        def burnup_solver(enrichment, cycle_length):
            # Simulate: higher enrichment -> higher k_eff
            keff = 0.8 + 5.0 * enrichment
            burnup = 50.0 * enrichment
            return keff, burnup

        result = optimizer.optimize_enrichment(1095.0, burnup_solver)

        assert "optimal_enrichment" in result
        assert result["optimal_enrichment"] > 0.0
        assert result["optimal_enrichment"] < 0.25

    def test_optimize_enrichment_hits_good_match_branch(self):
        optimizer = FuelCycleOptimizer(power_thermal=100e6, target_keff=1.0)

        def burnup_solver(enrichment, cycle_length):
            return 1.0, 100.0 * enrichment

        result = optimizer.optimize_enrichment(365.0, burnup_solver)
        assert result["k_eff"] == pytest.approx(1.0)
        assert result["discharge_burnup"] > 0.0

    def test_multi_objective_optimization(self):
        """Test multi-objective optimization."""
        optimizer = FuelCycleOptimizer(
            power_thermal=100e6,
            optimization_objective="min_cost",
        )

        # Mock burnup solver
        def burnup_solver(enrichment, cycle_length):
            keff = 0.8 + 5.0 * enrichment
            burnup = 50.0 * enrichment
            return keff, burnup

        # Mock cost function
        def cost_function(enrichment, cycle_length):
            return 1000.0 * enrichment + 100.0 * cycle_length / 365.0

        result = optimizer.multi_objective_optimization(burnup_solver, cost_function)

        assert "optimal_parameters" in result
        if result["optimal_parameters"] is not None:
            assert "enrichment" in result["optimal_parameters"]
            assert "cycle_length" in result["optimal_parameters"]

    def test_multi_objective_optimization_grid_search_fallback_for_unknown_method(self):
        optimizer = FuelCycleOptimizer(power_thermal=100e6)

        def burnup_solver(enrichment, cycle_length):
            # Always critical so grid search can pick a best point.
            return 1.0, 10.0

        result = optimizer.multi_objective_optimization(burnup_solver, method="nope")
        assert result["optimization_method"] == "grid_search"

    def test_multi_objective_optimization_grid_search_all_fail(self):
        optimizer = FuelCycleOptimizer(power_thermal=100e6)

        def burnup_solver(enrichment, cycle_length):
            raise RuntimeError("fail")

        result = optimizer.multi_objective_optimization(
            burnup_solver, method="grid_search"
        )
        assert result["optimal_parameters"] is None
        assert result["results"] is None

    def test_multi_objective_optimization_genetic_algorithm_path_with_stub(
        self, monkeypatch
    ):
        import smrforge.fuel_cycle.optimization as opt

        optimizer = FuelCycleOptimizer(power_thermal=100e6, target_keff=1.0)

        calls = {"exception_penalty": None, "noncritical_penalty": None}

        def burnup_solver(enrichment, cycle_length):
            # Force exception for some candidates to cover penalty branch.
            if enrichment < 0.04:
                raise RuntimeError("boom")

            # Only a specific pair is "critical"; everything else is non-critical.
            if abs(enrichment - 0.05) < 1e-9 and abs(cycle_length - 500.0) < 1e-9:
                return 1.0, 20.0
            return 0.5, 0.0

        class _DummyResult:
            def __init__(self):
                self.x_opt = np.array([0.05, 500.0])
                self.f_opt = 0.123
                self.history = [{"gen": 0}]

        class _DummyGA:
            def __init__(self, objective, bounds, population_size, generations):
                self.objective = objective
                calls["exception_penalty"] = self.objective(np.array([0.03, 365.0]))
                calls["noncritical_penalty"] = self.objective(np.array([0.05, 365.0]))

            def optimize(self):
                return _DummyResult()

        monkeypatch.setattr(opt, "_ADVANCED_OPT_AVAILABLE", True)
        monkeypatch.setattr(opt, "GeneticAlgorithm", _DummyGA)

        result = optimizer.multi_objective_optimization(
            burnup_solver,
            cost_function=None,  # cover default cost function branch
            weights=None,  # cover default weights branch
            method="genetic_algorithm",
        )
        assert result["optimization_method"] == "genetic_algorithm"
        assert result["optimal_parameters"]["enrichment"] == pytest.approx(0.05)
        assert result["results"]["k_eff"] == pytest.approx(1.0)
        assert calls["exception_penalty"] == 1e10
        assert calls["noncritical_penalty"] == 1e10

    def test_multi_objective_optimization_particle_swarm_path_with_stub(
        self, monkeypatch
    ):
        import smrforge.fuel_cycle.optimization as opt

        optimizer = FuelCycleOptimizer(power_thermal=100e6, target_keff=1.0)

        def burnup_solver(enrichment, cycle_length):
            return 1.0, 10.0

        class _DummyResult:
            def __init__(self):
                self.x_opt = np.array([0.05, 400.0])
                self.f_opt = 0.5
                self.history = []

        class _DummyPSO:
            def __init__(self, objective, bounds, n_particles, max_iterations):
                self.objective = objective

            def optimize(self):
                # Call objective once to execute scoring path.
                _ = self.objective(np.array([0.05, 400.0]))
                return _DummyResult()

        monkeypatch.setattr(opt, "_ADVANCED_OPT_AVAILABLE", True)
        monkeypatch.setattr(opt, "ParticleSwarmOptimization", _DummyPSO)

        result = optimizer.multi_objective_optimization(
            burnup_solver,
            method="particle_swarm",
        )
        assert result["optimization_method"] == "particle_swarm"


def test_fuel_cycle_optimization_import_without_advanced_opt(monkeypatch):
    """Cover ImportError fallback for advanced optimization algorithms."""
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if "advanced_optimization" in name:
            raise ImportError("blocked advanced_optimization")
        return real_import(name, globals, locals, fromlist, level)

    with monkeypatch.context() as mp:
        mp.setattr(builtins, "__import__", fake_import)
        sys.modules.pop("smrforge.fuel_cycle.optimization", None)
        sys.modules.pop("smrforge.fuel_cycle.advanced_optimization", None)
        mod = importlib.import_module("smrforge.fuel_cycle.optimization")
        assert mod._ADVANCED_OPT_AVAILABLE is False

    # Restore normal module state
    import smrforge.fuel_cycle.optimization as opt

    importlib.reload(opt)


class TestRefuelingStrategyOptimizer:
    """Tests for RefuelingStrategyOptimizer class."""

    def test_optimize_batch_configuration(self):
        """Test batch configuration optimization."""
        optimizer = RefuelingStrategyOptimizer(n_assemblies=100, max_batches=3)

        # Mock burnup solver
        def burnup_solver(n_batches, batch_fractions, shuffle_pattern):
            # Simulate: more batches -> higher burnup, higher cost
            keff = 1.0
            burnup = 50.0 + 5.0 * n_batches
            cost = 1000.0 * n_batches
            return keff, burnup, cost

        result = optimizer.optimize_batch_configuration(burnup_solver)

        assert "optimal_configuration" in result
        config = result["optimal_configuration"]
        assert "n_batches" in config
        assert "shuffle_pattern" in config

    def test_optimize_batch_configuration_objective_variants(self):
        def burnup_solver(n_batches, batch_fractions, shuffle_pattern):
            return 1.0, float(n_batches), float(n_batches) * 10.0

        o1 = RefuelingStrategyOptimizer(
            n_assemblies=10, max_batches=2, optimization_objective="max_burnup"
        )
        r1 = o1.optimize_batch_configuration(burnup_solver)
        assert r1["optimal_configuration"]["n_batches"] == 2

        o2 = RefuelingStrategyOptimizer(
            n_assemblies=10, max_batches=2, optimization_objective="max_cycle"
        )
        r2 = o2.optimize_batch_configuration(burnup_solver)
        assert r2["optimal_configuration"]["n_batches"] == 2

    def test_optimize_refueling_frequency(self):
        """Test refueling frequency optimization."""
        optimizer = RefuelingStrategyOptimizer(n_assemblies=100)

        # Mock burnup solver
        def burnup_solver(frequency):
            # Simulate: longer frequency -> higher cost, higher burnup
            cost = 10000.0 / frequency  # More frequent = more expensive
            burnup = 30.0 + 10.0 * frequency  # Longer = more burnup
            return cost, burnup

        result = optimizer.optimize_refueling_frequency(burnup_solver)

        assert "optimal_frequency" in result
        assert result["optimal_frequency"] > 0.5
        assert result["optimal_frequency"] <= 5.0  # Allow equality at max

    def test_optimize_refueling_frequency_handles_zero_burnup(self):
        optimizer = RefuelingStrategyOptimizer(n_assemblies=100)

        def burnup_solver(frequency):
            return 1.0, 0.0

        result = optimizer.optimize_refueling_frequency(burnup_solver)
        assert result["optimal_frequency"] is None
