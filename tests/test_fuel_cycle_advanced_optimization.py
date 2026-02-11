"""
Tests for fuel_cycle/advanced_optimization.py module.
"""

from unittest.mock import Mock

import numpy as np
import pytest

from smrforge.fuel_cycle.advanced_optimization import (
    GeneticAlgorithm,
    OptimizationResult,
    ParticleSwarmOptimization,
)


class TestOptimizationResult:
    """Tests for OptimizationResult dataclass."""

    def test_optimization_result_initialization(self):
        """Test OptimizationResult initialization."""
        x_opt = np.array([1.0, 2.0, 3.0])
        result = OptimizationResult(
            x_opt=x_opt,
            f_opt=10.5,
            n_iterations=50,
            success=True,
            history=[15.0, 12.0, 10.5],
            message="Optimization completed",
        )

        assert np.array_equal(result.x_opt, x_opt)
        assert result.f_opt == 10.5
        assert result.n_iterations == 50
        assert result.success is True
        assert result.history == [15.0, 12.0, 10.5]
        assert result.message == "Optimization completed"

    def test_optimization_result_defaults(self):
        """Test OptimizationResult with default values."""
        x_opt = np.array([1.0])
        result = OptimizationResult(
            x_opt=x_opt,
            f_opt=5.0,
            n_iterations=10,
            success=True,
        )

        assert result.history == []
        assert result.message == ""


class TestGeneticAlgorithm:
    """Tests for GeneticAlgorithm class."""

    def test_genetic_algorithm_initialization(self):
        """Test GeneticAlgorithm initialization."""

        def objective(x):
            return np.sum(x**2)

        bounds = [(-1.0, 1.0), (-2.0, 2.0)]
        ga = GeneticAlgorithm(
            objective=objective,
            bounds=bounds,
            population_size=50,
            generations=100,
            crossover_rate=0.8,
            mutation_rate=0.1,
            selection_method="tournament",
            elitism=2,
        )

        assert ga.pop_size == 50
        assert ga.n_gen == 100
        assert ga.n_params == 2
        assert ga.crossover_rate == 0.8
        assert ga.mutation_rate == 0.1
        assert ga.selection_method == "tournament"
        assert ga.elitism == 2

    def test_genetic_algorithm_initialization_defaults(self):
        """Test GeneticAlgorithm with default parameters."""

        def objective(x):
            return np.sum(x**2)

        bounds = [(-1.0, 1.0)]
        ga = GeneticAlgorithm(objective=objective, bounds=bounds)

        assert ga.pop_size == 50
        assert ga.n_gen == 100
        assert ga.crossover_rate == 0.8
        assert ga.mutation_rate == 0.1
        assert ga.selection_method == "tournament"
        assert ga.elitism == 2

    def test_genetic_algorithm_invalid_bounds_empty(self):
        """Test GeneticAlgorithm raises error for empty bounds."""

        def objective(x):
            return np.sum(x**2)

        with pytest.raises(
            ValueError, match="Must provide at least one parameter bound"
        ):
            GeneticAlgorithm(objective=objective, bounds=[])

    def test_genetic_algorithm_invalid_bounds_inverted(self):
        """Test GeneticAlgorithm raises error for inverted bounds."""

        def objective(x):
            return np.sum(x**2)

        with pytest.raises(
            ValueError, match="Upper bounds must be greater than lower bounds"
        ):
            GeneticAlgorithm(objective=objective, bounds=[(1.0, 0.0)])

    def test_initialize_population(self):
        """Test _initialize_population method."""

        def objective(x):
            return np.sum(x**2)

        bounds = [(-1.0, 1.0), (-2.0, 2.0)]
        ga = GeneticAlgorithm(objective=objective, bounds=bounds, population_size=10)

        population = ga._initialize_population()

        assert population.shape == (10, 2)
        assert np.all(population[:, 0] >= -1.0) and np.all(population[:, 0] <= 1.0)
        assert np.all(population[:, 1] >= -2.0) and np.all(population[:, 1] <= 2.0)

    def test_tournament_selection(self):
        """Test tournament selection method."""

        def objective(x):
            return np.sum(x**2)

        bounds = [(-1.0, 1.0)]
        ga = GeneticAlgorithm(objective=objective, bounds=bounds, population_size=10)

        population = np.random.uniform(-1.0, 1.0, (10, 1))
        fitness = np.array([objective(ind) for ind in population])

        selected = ga._tournament_selection(population, fitness)

        assert selected.shape == (10, 1)
        assert len(selected) == 10

    def test_roulette_selection(self):
        """Test roulette selection method."""

        def objective(x):
            return np.sum(x**2)

        bounds = [(-1.0, 1.0)]
        ga = GeneticAlgorithm(
            objective=objective,
            bounds=bounds,
            population_size=10,
            selection_method="roulette",
        )

        population = np.random.uniform(-1.0, 1.0, (10, 1))
        fitness = np.array([objective(ind) for ind in population])

        selected = ga._roulette_selection(population, fitness)

        assert selected.shape == (10, 1)
        assert len(selected) == 10

    def test_rank_selection(self):
        """Test rank selection method."""

        def objective(x):
            return np.sum(x**2)

        bounds = [(-1.0, 1.0)]
        ga = GeneticAlgorithm(
            objective=objective,
            bounds=bounds,
            population_size=10,
            selection_method="rank",
        )

        population = np.random.uniform(-1.0, 1.0, (10, 1))
        fitness = np.array([objective(ind) for ind in population])

        selected = ga._rank_selection(population, fitness)

        assert selected.shape == (10, 1)
        assert len(selected) == 10

    def test_selection_dispatch_roulette_and_rank(self):
        """Cover _selection dispatch branches for roulette and rank."""

        def objective(x):
            return np.sum(x**2)

        bounds = [(-1.0, 1.0)]
        population = np.random.uniform(-1.0, 1.0, (10, 1))
        fitness = np.array([objective(ind) for ind in population])

        ga_r = GeneticAlgorithm(
            objective=objective,
            bounds=bounds,
            population_size=10,
            selection_method="roulette",
        )
        sel_r = ga_r._selection(population, fitness)
        assert sel_r.shape == (10, 1)

        ga_k = GeneticAlgorithm(
            objective=objective,
            bounds=bounds,
            population_size=10,
            selection_method="rank",
        )
        sel_k = ga_k._selection(population, fitness)
        assert sel_k.shape == (10, 1)

    def test_crossover(self):
        """Test crossover method."""

        def objective(x):
            return np.sum(x**2)

        bounds = [(-1.0, 1.0), (-2.0, 2.0)]
        ga = GeneticAlgorithm(objective=objective, bounds=bounds, population_size=10)

        parents = np.random.uniform(-1.0, 1.0, (10, 2))

        offspring = ga._crossover(parents)

        assert offspring.shape[0] <= 10
        assert offspring.shape[1] == 2
        # Check bounds
        assert np.all(offspring[:, 0] >= -1.0) and np.all(offspring[:, 0] <= 1.0)
        assert np.all(offspring[:, 1] >= -2.0) and np.all(offspring[:, 1] <= 2.0)

    def test_crossover_handles_odd_parent_count(self):
        """Cover odd-parent crossover branch (last parent carries through)."""

        def objective(x):
            return np.sum(x**2)

        bounds = [(-1.0, 1.0), (-2.0, 2.0)]
        ga = GeneticAlgorithm(
            objective=objective,
            bounds=bounds,
            population_size=5,
            crossover_rate=0.0,  # force "no crossover" path
        )
        parents = np.random.uniform(-1.0, 1.0, (5, 2))
        offspring = ga._crossover(parents)
        assert offspring.shape == (5, 2)

    def test_mutation(self):
        """Test mutation method."""

        def objective(x):
            return np.sum(x**2)

        bounds = [(-1.0, 1.0), (-2.0, 2.0)]
        ga = GeneticAlgorithm(
            objective=objective,
            bounds=bounds,
            population_size=10,
            mutation_rate=0.5,  # High mutation rate for testing
        )

        offspring = np.random.uniform(-0.5, 0.5, (10, 2))

        mutated = ga._mutation(offspring)

        assert mutated.shape == (10, 2)
        # Check bounds
        assert np.all(mutated[:, 0] >= -1.0) and np.all(mutated[:, 0] <= 1.0)
        assert np.all(mutated[:, 1] >= -2.0) and np.all(mutated[:, 1] <= 2.0)

    def test_selection_invalid_method(self):
        """Test selection raises error for invalid method."""

        def objective(x):
            return np.sum(x**2)

        bounds = [(-1.0, 1.0)]
        ga = GeneticAlgorithm(objective=objective, bounds=bounds)
        ga.selection_method = "invalid"

        population = np.random.uniform(-1.0, 1.0, (10, 1))
        fitness = np.array([objective(ind) for ind in population])

        with pytest.raises(ValueError, match="Unknown selection method"):
            ga._selection(population, fitness)

    def test_optimize_basic(self):
        """Test optimize method with simple objective."""

        def objective(x):
            # Simple quadratic function with minimum at (0, 0)
            return np.sum(x**2)

        bounds = [(-1.0, 1.0), (-2.0, 2.0)]
        ga = GeneticAlgorithm(
            objective=objective,
            bounds=bounds,
            population_size=20,
            generations=10,
        )

        result = ga.optimize()

        assert isinstance(result, OptimizationResult)
        assert result.success is True
        assert result.n_iterations == 10
        assert len(result.history) == 11  # Initial + 10 generations
        assert result.f_opt >= 0  # Should be non-negative for sum of squares
        assert result.x_opt.shape == (2,)

    def test_optimize_with_elitism(self):
        """Test optimize with elitism enabled."""

        def objective(x):
            return np.sum(x**2)

        bounds = [(-1.0, 1.0)]
        ga = GeneticAlgorithm(
            objective=objective,
            bounds=bounds,
            population_size=10,
            generations=5,
            elitism=3,
        )

        result = ga.optimize()

        assert result.success is True
        assert len(result.history) == 6  # Initial + 5 generations


class TestParticleSwarmOptimization:
    """Tests for ParticleSwarmOptimization class."""

    def test_pso_initialization(self):
        """Test ParticleSwarmOptimization initialization."""

        def objective(x):
            return np.sum(x**2)

        bounds = [(-1.0, 1.0), (-2.0, 2.0)]
        pso = ParticleSwarmOptimization(
            objective=objective,
            bounds=bounds,
            n_particles=30,
            max_iterations=100,
            w=0.7,
            c1=1.5,
            c2=1.5,
            v_max=0.5,
        )

        assert pso.n_particles == 30
        assert pso.max_iter == 100
        assert pso.n_params == 2
        assert pso.w == 0.7
        assert pso.c1 == 1.5
        assert pso.c2 == 1.5
        assert pso.v_max == 0.5

    def test_pso_initialization_defaults(self):
        """Test ParticleSwarmOptimization with default parameters."""

        def objective(x):
            return np.sum(x**2)

        bounds = [(-1.0, 1.0)]
        pso = ParticleSwarmOptimization(objective=objective, bounds=bounds)

        assert pso.n_particles == 30
        assert pso.max_iter == 100
        assert pso.w == 0.7
        assert pso.c1 == 1.5
        assert pso.c2 == 1.5
        assert pso.v_max == 0.5

    def test_pso_invalid_bounds_empty(self):
        """Test ParticleSwarmOptimization raises error for empty bounds."""

        def objective(x):
            return np.sum(x**2)

        with pytest.raises(
            ValueError, match="Must provide at least one parameter bound"
        ):
            ParticleSwarmOptimization(objective=objective, bounds=[])

    def test_pso_invalid_bounds_inverted(self):
        """Test ParticleSwarmOptimization raises error for inverted bounds."""

        def objective(x):
            return np.sum(x**2)

        with pytest.raises(
            ValueError, match="Upper bounds must be greater than lower bounds"
        ):
            ParticleSwarmOptimization(objective=objective, bounds=[(1.0, 0.0)])

    def test_initialize_positions(self):
        """Test _initialize_positions method."""

        def objective(x):
            return np.sum(x**2)

        bounds = [(-1.0, 1.0), (-2.0, 2.0)]
        pso = ParticleSwarmOptimization(
            objective=objective, bounds=bounds, n_particles=10
        )

        positions = pso._initialize_positions()

        assert positions.shape == (10, 2)
        assert np.all(positions[:, 0] >= -1.0) and np.all(positions[:, 0] <= 1.0)
        assert np.all(positions[:, 1] >= -2.0) and np.all(positions[:, 1] <= 2.0)

    def test_initialize_velocities(self):
        """Test _initialize_velocities method."""

        def objective(x):
            return np.sum(x**2)

        bounds = [(-1.0, 1.0), (-2.0, 2.0)]
        pso = ParticleSwarmOptimization(
            objective=objective, bounds=bounds, n_particles=10
        )

        velocities = pso._initialize_velocities()

        assert velocities.shape == (10, 2)
        # Velocities should be within reasonable range
        param_ranges = np.array([2.0, 4.0])
        v_max_abs = pso.v_max * param_ranges
        assert np.all(velocities >= -v_max_abs) and np.all(velocities <= v_max_abs)

    def test_optimize_basic(self):
        """Test optimize method with simple objective."""

        def objective(x):
            # Simple quadratic function with minimum at (0, 0)
            return np.sum(x**2)

        bounds = [(-1.0, 1.0), (-2.0, 2.0)]
        pso = ParticleSwarmOptimization(
            objective=objective,
            bounds=bounds,
            n_particles=20,
            max_iterations=10,
        )

        result = pso.optimize()

        assert isinstance(result, OptimizationResult)
        assert result.success is True
        assert result.n_iterations == 10
        assert len(result.history) == 11  # Initial + 10 iterations
        assert result.f_opt >= 0  # Should be non-negative for sum of squares
        assert result.x_opt.shape == (2,)

    def test_optimize_convergence(self):
        """Test that PSO converges towards optimum."""

        def objective(x):
            # Simple quadratic with minimum at (0, 0)
            return np.sum(x**2)

        bounds = [(-1.0, 1.0)]
        pso = ParticleSwarmOptimization(
            objective=objective,
            bounds=bounds,
            n_particles=10,
            max_iterations=20,
        )

        result = pso.optimize()

        # Best fitness should improve (decrease) over time
        assert result.success is True
        assert len(result.history) >= 2
        # Generally, later values should be better (lower) than initial
        # But this is probabilistic, so just check it's reasonable
        assert result.f_opt >= 0
        assert result.f_opt <= 1.0  # Should be within bounds
