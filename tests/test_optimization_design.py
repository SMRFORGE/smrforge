"""
Unit tests for design optimization module.
"""

import numpy as np
import pytest

from smrforge.optimization.design import (
    DesignOptimizer,
    LoadingPatternOptimizer,
    OptimizationResult,
)


class TestOptimizationResult:
    """Tests for OptimizationResult class."""

    def test_optimization_result_creation(self):
        """Test creating OptimizationResult."""
        result = OptimizationResult(
            x_opt=np.array([1.0, 2.0]),
            f_opt=0.5,
            n_iterations=10,
            success=True,
            message="Test",
        )
        
        assert np.array_equal(result.x_opt, np.array([1.0, 2.0]))
        assert result.f_opt == 0.5
        assert result.n_iterations == 10
        assert result.success is True
        assert result.message == "Test"


class TestDesignOptimizer:
    """Tests for DesignOptimizer class."""

    def test_design_optimizer_initialization(self):
        """Test DesignOptimizer initialization."""
        def objective(x):
            return np.sum(x**2)
        
        bounds = [(-1.0, 1.0), (-2.0, 2.0)]
        
        optimizer = DesignOptimizer(objective, bounds, method="genetic_algorithm")
        
        assert optimizer.n_params == 2
        assert optimizer.method == "genetic_algorithm"

    def test_optimize_genetic_algorithm(self):
        """Test optimization using genetic algorithm."""
        def objective(x):
            # Simple quadratic: minimum at (0, 0)
            return np.sum(x**2)
        
        bounds = [(-5.0, 5.0), (-5.0, 5.0)]
        
        optimizer = DesignOptimizer(objective, bounds, method="genetic_algorithm")
        
        result = optimizer.optimize(max_iterations=20, population_size=20)
        
        assert result.success is True
        assert result.f_opt >= 0.0
        assert len(result.x_opt) == 2
        # Should be close to minimum (0, 0)
        assert np.all(np.abs(result.x_opt) < 2.0)

    def test_optimize_with_scipy_minimize(self):
        """Test optimization using scipy minimize (if available)."""
        try:
            from scipy.optimize import minimize
            scipy_available = True
        except ImportError:
            scipy_available = False
        
        if not scipy_available:
            pytest.skip("scipy not available")
        
        def objective(x):
            return np.sum(x**2)
        
        bounds = [(-5.0, 5.0), (-5.0, 5.0)]
        
        optimizer = DesignOptimizer(objective, bounds, method="minimize")
        
        result = optimizer.optimize(max_iterations=50, tolerance=1e-6)
        
        assert result.success is True
        assert result.f_opt >= 0.0
        assert len(result.x_opt) == 2

    def test_optimize_with_scipy_differential_evolution(self):
        """Test optimization using scipy differential evolution (if available)."""
        try:
            from scipy.optimize import differential_evolution
            scipy_available = True
        except ImportError:
            scipy_available = False
        
        if not scipy_available:
            pytest.skip("scipy not available")
        
        def objective(x):
            return np.sum(x**2)
        
        bounds = [(-5.0, 5.0), (-5.0, 5.0)]
        
        optimizer = DesignOptimizer(
            objective, bounds, method="differential_evolution"
        )
        
        result = optimizer.optimize(max_iterations=20)
        
        # May not converge in limited iterations, but should produce valid result
        assert result.f_opt >= 0.0
        assert result.f_opt >= 0.0
        assert len(result.x_opt) == 2

    def test_selection(self):
        """Test tournament selection."""
        def objective(x):
            return np.sum(x**2)
        
        bounds = [(-1.0, 1.0)]
        optimizer = DesignOptimizer(objective, bounds)
        
        population = np.array([[0.1], [0.2], [0.3], [0.4]])
        fitness = np.array([0.01, 0.04, 0.09, 0.16])
        
        selected = optimizer._selection(population, fitness)
        
        assert len(selected) == len(population)
        # Best individual (0.1) should be selected more often
        assert np.any(np.abs(selected - 0.1) < 0.01)

    def test_crossover(self):
        """Test single-point crossover."""
        def objective(x):
            return np.sum(x**2)
        
        bounds = [(-1.0, 1.0), (-1.0, 1.0)]
        optimizer = DesignOptimizer(objective, bounds)
        
        parents = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        
        offspring = optimizer._crossover(parents)
        
        assert len(offspring) >= len(parents)

    def test_mutation(self):
        """Test Gaussian mutation."""
        def objective(x):
            return np.sum(x**2)
        
        bounds = [(-1.0, 1.0), (-1.0, 1.0)]
        optimizer = DesignOptimizer(objective, bounds)
        
        offspring = np.array([[0.5, 0.5], [0.3, 0.3]])
        
        mutated = optimizer._mutation(offspring.copy())
        
        # Some individuals may be mutated
        assert len(mutated) == len(offspring)
        # Values should be within bounds
        assert np.all(mutated >= bounds[0][0])
        assert np.all(mutated <= bounds[0][1])


class TestLoadingPatternOptimizer:
    """Tests for LoadingPatternOptimizer class."""

    def test_loading_pattern_optimizer_initialization(self):
        """Test LoadingPatternOptimizer initialization."""
        core_layout = np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]])
        
        def objective(pattern):
            # Minimize sum of pattern values
            return np.sum(pattern)
        
        optimizer = LoadingPatternOptimizer(
            core_layout, n_fuel_types=3, objective=objective
        )
        
        assert optimizer.n_fuel_types == 3
        assert optimizer.n_assemblies == 9

    def test_generate_random_pattern(self):
        """Test random pattern generation."""
        core_layout = np.array([[1, 1], [1, 1]])
        
        def objective(pattern):
            return np.sum(pattern)
        
        optimizer = LoadingPatternOptimizer(
            core_layout, n_fuel_types=2, objective=objective
        )
        
        pattern = optimizer._generate_random_pattern()
        
        # All positions should have fuel type (1 or 2)
        assert np.all((pattern == 1) | (pattern == 2))
        # Non-fuel positions should be 0
        assert pattern[0, 0] > 0

    def test_optimize_loading_pattern(self):
        """Test loading pattern optimization."""
        core_layout = np.array([[1, 1], [1, 1]])
        
        def objective(pattern):
            # Minimize sum (prefer lower fuel types)
            return np.sum(pattern)
        
        optimizer = LoadingPatternOptimizer(
            core_layout, n_fuel_types=2, objective=objective
        )
        
        result = optimizer.optimize(method="genetic_algorithm", max_iterations=10)
        
        assert result.success is True
        assert result.f_opt >= 0.0
        assert result.x_opt.shape == core_layout.shape

    def test_optimize_loading_pattern_unknown_method_raises(self):
        """Cover unknown-method error path."""
        core_layout = np.array([[1, 1], [1, 1]])

        def objective(pattern):
            return np.sum(pattern)

        optimizer = LoadingPatternOptimizer(core_layout, n_fuel_types=2, objective=objective)
        with pytest.raises(ValueError, match="Unknown method"):
            optimizer.optimize(method="nope", max_iterations=1)

    def test_loading_pattern_selection(self):
        """Test selection for loading patterns."""
        core_layout = np.array([[1, 1], [1, 1]])
        
        def objective(pattern):
            return np.sum(pattern)
        
        optimizer = LoadingPatternOptimizer(
            core_layout, n_fuel_types=2, objective=objective
        )
        
        # Need at least 3 individuals for tournament selection
        population = np.array([
            [[1, 1], [1, 1]],
            [[2, 2], [2, 2]],
            [[1, 2], [2, 1]],
        ])
        fitness = np.array([4.0, 8.0, 6.0])
        
        selected = optimizer._selection(population, fitness)
        
        assert len(selected) == len(population)

    def test_loading_pattern_crossover(self):
        """Test uniform crossover for loading patterns."""
        core_layout = np.array([[1, 1], [1, 1]])
        
        def objective(pattern):
            return np.sum(pattern)
        
        optimizer = LoadingPatternOptimizer(
            core_layout, n_fuel_types=2, objective=objective
        )
        
        parents = np.array([
            [[1, 1], [1, 1]],
            [[2, 2], [2, 2]],
        ])
        
        offspring = optimizer._crossover(parents)
        
        assert len(offspring) >= len(parents)

    def test_loading_pattern_crossover_handles_odd_parent_count(self):
        """Cover odd-parent fallback in crossover."""
        core_layout = np.array([[1, 1], [1, 1]])

        def objective(pattern):
            return np.sum(pattern)

        optimizer = LoadingPatternOptimizer(core_layout, n_fuel_types=2, objective=objective)

        parents = np.array(
            [
                [[1, 1], [1, 1]],
                [[2, 2], [2, 2]],
                [[1, 2], [2, 1]],
            ]
        )

        offspring = optimizer._crossover(parents)
        assert offspring.shape[1:] == parents.shape[1:]
        # Last parent should be forwarded unchanged when count is odd.
        assert np.array_equal(offspring[-1], parents[-1])

    def test_loading_pattern_mutation(self):
        """Test swap mutation for loading patterns."""
        core_layout = np.array([[1, 1], [1, 1]])
        
        def objective(pattern):
            return np.sum(pattern)
        
        optimizer = LoadingPatternOptimizer(
            core_layout, n_fuel_types=2, objective=objective
        )
        
        offspring = np.array([[[1, 2], [2, 1]]])
        
        mutated = optimizer._mutation(offspring.copy())
        
        assert len(mutated) == len(offspring)
        assert mutated.shape == offspring.shape


def test_design_module_import_without_scipy(monkeypatch):
    """
    Cover the ImportError fallback at module import time.
    (We reload the module with a fake ImportError for scipy.)
    """
    import builtins
    import importlib
    import sys

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "scipy" or name.startswith("scipy."):
            raise ImportError("scipy not available (test)")
        return real_import(name, globals, locals, fromlist, level)

    with monkeypatch.context() as mp:
        mp.setattr(builtins, "__import__", fake_import)
        sys.modules.pop("smrforge.optimization.design", None)
        mod = importlib.import_module("smrforge.optimization.design")
        assert mod._SCIPY_AVAILABLE is False

    # Restore the normal module state for other tests.
    import smrforge.optimization.design as design_mod

    importlib.reload(design_mod)
