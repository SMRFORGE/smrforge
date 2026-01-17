"""
Unit tests for fuel cycle optimization module.
"""

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
        
        result = optimizer.multi_objective_optimization(
            burnup_solver, cost_function
        )
        
        assert "optimal_parameters" in result
        if result["optimal_parameters"] is not None:
            assert "enrichment" in result["optimal_parameters"]
            assert "cycle_length" in result["optimal_parameters"]


class TestRefuelingStrategyOptimizer:
    """Tests for RefuelingStrategyOptimizer class."""

    def test_optimize_batch_configuration(self):
        """Test batch configuration optimization."""
        optimizer = RefuelingStrategyOptimizer(
            n_assemblies=100, max_batches=3
        )
        
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
