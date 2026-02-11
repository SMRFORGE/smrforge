"""
Advanced optimization algorithms for fuel cycle optimization.

This module provides:
- Genetic Algorithm (GA) optimizer
- Particle Swarm Optimization (PSO) optimizer
- Multi-objective optimization support
- Integration with fuel cycle optimization
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.fuel_cycle.advanced_optimization")


@dataclass
class OptimizationResult:
    """Result from optimization algorithm."""

    x_opt: np.ndarray  # Optimal parameters
    f_opt: float  # Optimal objective value
    n_iterations: int  # Number of iterations
    success: bool  # Convergence flag
    history: List[float] = field(default_factory=list)  # Optimization history
    message: str = ""  # Status message


class GeneticAlgorithm:
    """
    Genetic Algorithm optimizer for fuel cycle optimization.

    Genetic algorithms are population-based metaheuristic optimization algorithms
    inspired by natural selection. They are particularly effective for:
    - Non-convex optimization problems
    - Multi-objective optimization
    - Discrete and continuous parameter spaces
    - Global optimization (avoiding local minima)

    Attributes:
        objective: Objective function to minimize
        bounds: Parameter bounds [(min, max), ...] for each parameter
        population_size: Number of individuals in population
        generations: Maximum number of generations
        crossover_rate: Probability of crossover (default: 0.8)
        mutation_rate: Probability of mutation (default: 0.1)
        selection_method: Selection method ('tournament', 'roulette', 'rank')
        elitism: Number of best individuals to preserve (default: 2)
    """

    def __init__(
        self,
        objective: Callable[[np.ndarray], float],
        bounds: List[Tuple[float, float]],
        population_size: int = 50,
        generations: int = 100,
        crossover_rate: float = 0.8,
        mutation_rate: float = 0.1,
        selection_method: str = "tournament",
        elitism: int = 2,
    ):
        self.objective = objective
        self.bounds = np.array(bounds)
        self.pop_size = population_size
        self.n_gen = generations
        self.n_params = len(bounds)
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.selection_method = selection_method
        self.elitism = elitism

        # Validate bounds
        if self.n_params == 0:
            raise ValueError("Must provide at least one parameter bound")
        if np.any(self.bounds[:, 1] <= self.bounds[:, 0]):
            raise ValueError("Upper bounds must be greater than lower bounds")

    def optimize(self) -> OptimizationResult:
        """
        Run genetic algorithm optimization.

        Returns:
            OptimizationResult with optimal parameters and fitness
        """
        logger.info(
            f"Starting Genetic Algorithm: {self.pop_size} individuals, "
            f"{self.n_gen} generations, {self.n_params} parameters"
        )

        # Initialize population
        population = self._initialize_population()

        # Track best individual
        best_individual = None
        best_fitness = float("inf")
        history = []

        # Evaluate initial population
        fitness = np.array([self.objective(ind) for ind in population])
        min_idx = np.argmin(fitness)
        best_individual = population[min_idx].copy()
        best_fitness = fitness[min_idx]
        history.append(best_fitness)

        logger.debug(f"Initial best fitness: {best_fitness:.6f}")

        # Evolution loop
        for gen in range(self.n_gen):
            # Selection
            selected = self._selection(population, fitness)

            # Crossover
            offspring = self._crossover(selected)

            # Mutation
            mutated = self._mutation(offspring)

            # Evaluate new generation
            fitness_new = np.array([self.objective(ind) for ind in mutated])

            # Elitism: preserve best individuals
            if self.elitism > 0:
                elite_indices = np.argsort(fitness)[: self.elitism]
                worst_indices = np.argsort(fitness_new)[-self.elitism :]
                mutated[worst_indices] = population[elite_indices]
                fitness_new[worst_indices] = fitness[elite_indices]

            # Update population
            population = mutated
            fitness = fitness_new

            # Track best
            min_idx = np.argmin(fitness)
            if fitness[min_idx] < best_fitness:
                best_fitness = fitness[min_idx]
                best_individual = population[min_idx].copy()

            history.append(best_fitness)

            # Log progress
            if (gen + 1) % 10 == 0 or gen == self.n_gen - 1:
                logger.debug(
                    f"Generation {gen+1}/{self.n_gen}: "
                    f"best fitness = {best_fitness:.6f}"
                )

        logger.info(f"GA optimization complete: best fitness = {best_fitness:.6f}")

        return OptimizationResult(
            x_opt=best_individual,
            f_opt=best_fitness,
            n_iterations=self.n_gen,
            success=True,
            history=history,
            message="Optimization completed successfully",
        )

    def _initialize_population(self) -> np.ndarray:
        """Initialize random population within bounds."""
        population = np.random.uniform(
            low=self.bounds[:, 0],
            high=self.bounds[:, 1],
            size=(self.pop_size, self.n_params),
        )
        return population

    def _selection(self, population: np.ndarray, fitness: np.ndarray) -> np.ndarray:
        """Select individuals for reproduction."""
        if self.selection_method == "tournament":
            return self._tournament_selection(population, fitness)
        elif self.selection_method == "roulette":
            return self._roulette_selection(population, fitness)
        elif self.selection_method == "rank":
            return self._rank_selection(population, fitness)
        else:
            raise ValueError(f"Unknown selection method: {self.selection_method}")

    def _tournament_selection(
        self, population: np.ndarray, fitness: np.ndarray
    ) -> np.ndarray:
        """Tournament selection (select best from random subset)."""
        selected = []
        tournament_size = 3

        for _ in range(self.pop_size):
            # Random tournament
            indices = np.random.choice(
                self.pop_size, size=tournament_size, replace=False
            )
            winner_idx = indices[np.argmin(fitness[indices])]
            selected.append(population[winner_idx])

        return np.array(selected)

    def _roulette_selection(
        self, population: np.ndarray, fitness: np.ndarray
    ) -> np.ndarray:
        """Roulette wheel selection (probability proportional to fitness)."""
        # Convert to probabilities (minimize -> invert fitness)
        max_fitness = np.max(fitness)
        probabilities = (max_fitness - fitness + 1e-10) / (
            np.sum(max_fitness - fitness) + 1e-10
        )

        selected_indices = np.random.choice(
            self.pop_size, size=self.pop_size, p=probabilities
        )
        return population[selected_indices]

    def _rank_selection(
        self, population: np.ndarray, fitness: np.ndarray
    ) -> np.ndarray:
        """Rank-based selection."""
        # Rank individuals (1 = best, pop_size = worst)
        ranks = np.argsort(np.argsort(fitness)) + 1
        probabilities = (self.pop_size - ranks + 1) / np.sum(self.pop_size - ranks + 1)

        selected_indices = np.random.choice(
            self.pop_size, size=self.pop_size, p=probabilities
        )
        return population[selected_indices]

    def _crossover(self, parents: np.ndarray) -> np.ndarray:
        """Crossover (recombination) of parent individuals."""
        offspring = []

        for i in range(0, len(parents), 2):
            if i + 1 < len(parents):
                if np.random.random() < self.crossover_rate:
                    # Blend crossover (continuous)
                    alpha = np.random.random(self.n_params)
                    child1 = alpha * parents[i] + (1 - alpha) * parents[i + 1]
                    child2 = (1 - alpha) * parents[i] + alpha * parents[i + 1]

                    # Clip to bounds
                    child1 = np.clip(child1, self.bounds[:, 0], self.bounds[:, 1])
                    child2 = np.clip(child2, self.bounds[:, 0], self.bounds[:, 1])

                    offspring.extend([child1, child2])
                else:
                    # No crossover
                    offspring.extend([parents[i], parents[i + 1]])
            else:
                offspring.append(parents[i])

        return np.array(offspring[: self.pop_size])

    def _mutation(self, offspring: np.ndarray) -> np.ndarray:
        """Mutate offspring individuals."""
        mutated = offspring.copy()

        for i in range(len(mutated)):
            for j in range(self.n_params):
                if np.random.random() < self.mutation_rate:
                    # Gaussian mutation
                    sigma = 0.1 * (self.bounds[j, 1] - self.bounds[j, 0])
                    mutated[i, j] += np.random.normal(0, sigma)

                    # Clip to bounds
                    mutated[i, j] = np.clip(
                        mutated[i, j], self.bounds[j, 0], self.bounds[j, 1]
                    )

        return mutated


class ParticleSwarmOptimization:
    """
    Particle Swarm Optimization (PSO) for fuel cycle optimization.

    PSO is a population-based optimization algorithm inspired by social behavior
    of bird flocking. It is effective for:
    - Continuous optimization problems
    - Smooth objective functions
    - Fast convergence for well-behaved problems
    - Global optimization

    Attributes:
        objective: Objective function to minimize
        bounds: Parameter bounds [(min, max), ...] for each parameter
        n_particles: Number of particles in swarm
        max_iterations: Maximum number of iterations
        w: Inertia weight (default: 0.7)
        c1: Cognitive coefficient (default: 1.5)
        c2: Social coefficient (default: 1.5)
        v_max: Maximum velocity (as fraction of parameter range, default: 0.5)
    """

    def __init__(
        self,
        objective: Callable[[np.ndarray], float],
        bounds: List[Tuple[float, float]],
        n_particles: int = 30,
        max_iterations: int = 100,
        w: float = 0.7,
        c1: float = 1.5,
        c2: float = 1.5,
        v_max: float = 0.5,
    ):
        self.objective = objective
        self.bounds = np.array(bounds)
        self.n_particles = n_particles
        self.max_iter = max_iterations
        self.n_params = len(bounds)
        self.w = w  # Inertia weight
        self.c1 = c1  # Cognitive coefficient
        self.c2 = c2  # Social coefficient
        self.v_max = v_max  # Maximum velocity fraction

        # Validate bounds
        if self.n_params == 0:
            raise ValueError("Must provide at least one parameter bound")
        if np.any(self.bounds[:, 1] <= self.bounds[:, 0]):
            raise ValueError("Upper bounds must be greater than lower bounds")

    def optimize(self) -> OptimizationResult:
        """
        Run particle swarm optimization.

        Returns:
            OptimizationResult with optimal parameters and fitness
        """
        logger.info(
            f"Starting Particle Swarm Optimization: {self.n_particles} particles, "
            f"{self.max_iter} iterations, {self.n_params} parameters"
        )

        # Initialize particles
        positions = self._initialize_positions()
        velocities = self._initialize_velocities()

        # Evaluate initial fitness
        fitness = np.array([self.objective(pos) for pos in positions])

        # Personal best (best position each particle has seen)
        pbest_positions = positions.copy()
        pbest_fitness = fitness.copy()

        # Global best (best position in entire swarm)
        gbest_idx = np.argmin(fitness)
        gbest_position = positions[gbest_idx].copy()
        gbest_fitness = fitness[gbest_idx]

        history = [gbest_fitness]
        logger.debug(f"Initial best fitness: {gbest_fitness:.6f}")

        # PSO iteration loop
        for iteration in range(self.max_iter):
            # Update velocities and positions
            for i in range(self.n_particles):
                # Update velocity
                r1 = np.random.random(self.n_params)
                r2 = np.random.random(self.n_params)

                cognitive = self.c1 * r1 * (pbest_positions[i] - positions[i])
                social = self.c2 * r2 * (gbest_position - positions[i])

                velocities[i] = self.w * velocities[i] + cognitive + social

                # Limit velocity
                param_ranges = self.bounds[:, 1] - self.bounds[:, 0]
                v_max_abs = self.v_max * param_ranges
                velocities[i] = np.clip(velocities[i], -v_max_abs, v_max_abs)

                # Update position
                positions[i] += velocities[i]

                # Clip to bounds
                positions[i] = np.clip(
                    positions[i], self.bounds[:, 0], self.bounds[:, 1]
                )

            # Evaluate fitness
            fitness = np.array([self.objective(pos) for pos in positions])

            # Update personal best
            improved = fitness < pbest_fitness
            pbest_positions[improved] = positions[improved]
            pbest_fitness[improved] = fitness[improved]

            # Update global best
            min_idx = np.argmin(fitness)
            if fitness[min_idx] < gbest_fitness:
                gbest_fitness = fitness[min_idx]
                gbest_position = positions[min_idx].copy()

            history.append(gbest_fitness)

            # Log progress
            if (iteration + 1) % 10 == 0 or iteration == self.max_iter - 1:
                logger.debug(
                    f"Iteration {iteration+1}/{self.max_iter}: "
                    f"best fitness = {gbest_fitness:.6f}"
                )

        logger.info(f"PSO optimization complete: best fitness = {gbest_fitness:.6f}")

        return OptimizationResult(
            x_opt=gbest_position,
            f_opt=gbest_fitness,
            n_iterations=self.max_iter,
            success=True,
            history=history,
            message="Optimization completed successfully",
        )

    def _initialize_positions(self) -> np.ndarray:
        """Initialize particle positions randomly within bounds."""
        positions = np.random.uniform(
            low=self.bounds[:, 0],
            high=self.bounds[:, 1],
            size=(self.n_particles, self.n_params),
        )
        return positions

    def _initialize_velocities(self) -> np.ndarray:
        """Initialize particle velocities (small random values)."""
        param_ranges = self.bounds[:, 1] - self.bounds[:, 0]
        velocities = np.random.uniform(
            low=-self.v_max * param_ranges,
            high=self.v_max * param_ranges,
            size=(self.n_particles, self.n_params),
        )
        return velocities
