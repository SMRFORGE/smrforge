"""
Design optimization algorithms for reactor design.

This module provides optimization algorithms for:
- Reactor design optimization
- Fuel loading pattern optimization
- Core reload optimization
"""

import numpy as np
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from ..utils.logging import get_logger

logger = get_logger("smrforge.optimization.design")

try:
    from scipy.optimize import minimize, differential_evolution
    _SCIPY_AVAILABLE = True
except ImportError:
    _SCIPY_AVAILABLE = False
    logger.warning("scipy not available, some optimization methods will be limited")


@dataclass
class OptimizationResult:
    """
    Optimization result.
    
    Attributes:
        x_opt: Optimal parameters
        f_opt: Optimal objective value
        n_iterations: Number of iterations
        success: Whether optimization converged
        message: Optimization message
        history: Optional iteration history
    """
    
    x_opt: np.ndarray
    f_opt: float
    n_iterations: int
    success: bool
    message: str = ""
    history: Optional[List[Dict]] = None


class DesignOptimizer:
    """
    Reactor design optimization.
    
    Provides optimization algorithms for reactor design parameters
    such as core dimensions, enrichment, and material compositions.
    
    Attributes:
        objective: Objective function to minimize
        bounds: Parameter bounds [(min, max), ...]
        method: Optimization method ('differential_evolution', 'minimize', 'genetic_algorithm')
    """
    
    def __init__(
        self,
        objective: Callable[[np.ndarray], float],
        bounds: List[Tuple[float, float]],
        method: str = "differential_evolution",
    ):
        """
        Initialize design optimizer.
        
        Args:
            objective: Objective function f(x) -> float to minimize
            bounds: List of (min, max) bounds for each parameter
            method: Optimization method
        """
        self.objective = objective
        self.bounds = np.array(bounds)
        self.method = method
        self.n_params = len(bounds)
    
    def optimize(
        self,
        max_iterations: int = 100,
        tolerance: float = 1e-6,
        **kwargs,
    ) -> OptimizationResult:
        """
        Optimize design parameters.
        
        Args:
            max_iterations: Maximum number of iterations
            tolerance: Convergence tolerance
            **kwargs: Additional method-specific arguments
            
        Returns:
            OptimizationResult with optimal parameters and objective value
        """
        if self.method == "differential_evolution" and _SCIPY_AVAILABLE:
            return self._optimize_differential_evolution(max_iterations, **kwargs)
        elif self.method == "minimize" and _SCIPY_AVAILABLE:
            return self._optimize_minimize(max_iterations, tolerance, **kwargs)
        else:
            return self._optimize_genetic_algorithm(max_iterations, **kwargs)
    
    def _optimize_differential_evolution(
        self, max_iterations: int, **kwargs
    ) -> OptimizationResult:
        """Optimize using scipy's differential evolution."""
        result = differential_evolution(
            self.objective,
            self.bounds,
            maxiter=max_iterations,
            **kwargs,
        )
        
        return OptimizationResult(
            x_opt=result.x,
            f_opt=result.fun,
            n_iterations=result.nit,
            success=result.success,
            message=result.message,
        )
    
    def _optimize_minimize(
        self, max_iterations: int, tolerance: float, **kwargs
    ) -> OptimizationResult:
        """Optimize using scipy's minimize."""
        # Initial guess: center of bounds
        x0 = np.mean(self.bounds, axis=1)
        
        result = minimize(
            self.objective,
            x0,
            method="L-BFGS-B",
            bounds=self.bounds,
            options={"maxiter": max_iterations, "ftol": tolerance},
            **kwargs,
        )
        
        return OptimizationResult(
            x_opt=result.x,
            f_opt=result.fun,
            n_iterations=result.nit if hasattr(result, "nit") else max_iterations,
            success=result.success,
            message=result.message,
        )
    
    def _optimize_genetic_algorithm(
        self, max_iterations: int, **kwargs
    ) -> OptimizationResult:
        """Optimize using genetic algorithm (fallback)."""
        population_size = kwargs.get("population_size", 50)
        
        # Initialize population
        population = np.random.uniform(
            low=self.bounds[:, 0],
            high=self.bounds[:, 1],
            size=(population_size, self.n_params),
        )
        
        best_individual = None
        best_fitness = float("inf")
        history = []
        
        for gen in range(max_iterations):
            # Evaluate fitness
            fitness = np.array([self.objective(ind) for ind in population])
            
            # Track best
            min_idx = np.argmin(fitness)
            if fitness[min_idx] < best_fitness:
                best_fitness = fitness[min_idx]
                best_individual = population[min_idx].copy()
            
            history.append({"generation": gen, "best_fitness": best_fitness})
            
            # Selection, crossover, mutation
            selected = self._selection(population, fitness)
            offspring = self._crossover(selected)
            population = self._mutation(offspring)
        
        return OptimizationResult(
            x_opt=best_individual if best_individual is not None else population[0],
            f_opt=best_fitness,
            n_iterations=max_iterations,
            success=True,
            message="Genetic algorithm completed",
            history=history,
        )
    
    def _selection(
        self, population: np.ndarray, fitness: np.ndarray
    ) -> np.ndarray:
        """Tournament selection."""
        selected = []
        for _ in range(len(population)):
            # Tournament of 3
            idx = np.random.choice(len(population), size=3, replace=False)
            winner = idx[np.argmin(fitness[idx])]
            selected.append(population[winner])
        return np.array(selected)
    
    def _crossover(self, parents: np.ndarray) -> np.ndarray:
        """Single-point crossover."""
        offspring = []
        for i in range(0, len(parents), 2):
            if i + 1 < len(parents):
                point = np.random.randint(1, self.n_params)
                child1 = np.concatenate([parents[i][:point], parents[i + 1][point:]])
                child2 = np.concatenate([parents[i + 1][:point], parents[i][point:]])
                offspring.extend([child1, child2])
            else:
                offspring.append(parents[i])
        return np.array(offspring)
    
    def _mutation(self, offspring: np.ndarray) -> np.ndarray:
        """Gaussian mutation."""
        mutation_rate = 0.1
        for i in range(len(offspring)):
            if np.random.random() < mutation_rate:
                gene = np.random.randint(self.n_params)
                mutation = np.random.normal(0, 0.1 * (self.bounds[gene, 1] - self.bounds[gene, 0]))
                offspring[i, gene] += mutation
                # Clip to bounds
                offspring[i, gene] = np.clip(
                    offspring[i, gene], self.bounds[gene, 0], self.bounds[gene, 1]
                )
        return offspring


class LoadingPatternOptimizer:
    """
    Fuel loading pattern optimization.
    
    Optimizes fuel assembly loading patterns for refueling operations.
    
    Attributes:
        core_layout: Core layout (n_assemblies x n_assemblies)
        n_fuel_types: Number of different fuel types
        objective: Objective function
    """
    
    def __init__(
        self,
        core_layout: np.ndarray,
        n_fuel_types: int,
        objective: Callable[[np.ndarray], float],
    ):
        """
        Initialize loading pattern optimizer.
        
        Args:
            core_layout: Core layout array (0 = empty, >0 = assembly positions)
            n_fuel_types: Number of fuel types (1, 2, 3, ...)
            objective: Objective function f(pattern) -> float
        """
        self.core_layout = core_layout
        self.n_fuel_types = n_fuel_types
        self.objective = objective
        self.n_assemblies = int(np.sum(core_layout > 0))
    
    def optimize(
        self,
        method: str = "genetic_algorithm",
        max_iterations: int = 100,
    ) -> OptimizationResult:
        """
        Optimize loading pattern.
        
        Args:
            method: Optimization method
            max_iterations: Maximum iterations
            
        Returns:
            OptimizationResult with optimal pattern
        """
        if method == "genetic_algorithm":
            return self._optimize_genetic_algorithm(max_iterations)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _optimize_genetic_algorithm(
        self, max_iterations: int
    ) -> OptimizationResult:
        """Optimize using genetic algorithm."""
        population_size = 50
        
        # Initialize population (random patterns)
        population = []
        for _ in range(population_size):
            pattern = self._generate_random_pattern()
            population.append(pattern)
        population = np.array(population)
        
        best_pattern = None
        best_fitness = float("inf")
        history = []
        
        for gen in range(max_iterations):
            # Evaluate fitness
            fitness = np.array([self.objective(p) for p in population])
            
            # Track best
            min_idx = np.argmin(fitness)
            if fitness[min_idx] < best_fitness:
                best_fitness = fitness[min_idx]
                best_pattern = population[min_idx].copy()
            
            history.append({"generation": gen, "best_fitness": best_fitness})
            
            # Selection, crossover, mutation
            selected = self._selection(population, fitness)
            offspring = self._crossover(selected)
            population = self._mutation(offspring)
        
        return OptimizationResult(
            x_opt=best_pattern if best_pattern is not None else population[0],
            f_opt=best_fitness,
            n_iterations=max_iterations,
            success=True,
            message="Loading pattern optimization completed",
            history=history,
        )
    
    def _generate_random_pattern(self) -> np.ndarray:
        """Generate random loading pattern."""
        pattern = np.zeros_like(self.core_layout)
        fuel_positions = np.where(self.core_layout > 0)
        
        # Randomly assign fuel types
        for i, (r, c) in enumerate(zip(fuel_positions[0], fuel_positions[1])):
            pattern[r, c] = np.random.randint(1, self.n_fuel_types + 1)
        
        return pattern
    
    def _selection(
        self, population: np.ndarray, fitness: np.ndarray
    ) -> np.ndarray:
        """Tournament selection."""
        selected = []
        for _ in range(len(population)):
            idx = np.random.choice(len(population), size=3, replace=False)
            winner = idx[np.argmin(fitness[idx])]
            selected.append(population[winner])
        return np.array(selected)
    
    def _crossover(self, parents: np.ndarray) -> np.ndarray:
        """Uniform crossover for loading patterns."""
        offspring = []
        for i in range(0, len(parents), 2):
            if i + 1 < len(parents):
                # Uniform crossover: randomly choose from each parent
                mask = np.random.random(parents[i].shape) < 0.5
                child1 = np.where(mask, parents[i], parents[i + 1])
                child2 = np.where(mask, parents[i + 1], parents[i])
                offspring.extend([child1, child2])
            else:
                offspring.append(parents[i])
        return np.array(offspring)
    
    def _mutation(self, offspring: np.ndarray) -> np.ndarray:
        """Swap mutation for loading patterns."""
        mutation_rate = 0.1
        for i in range(len(offspring)):
            if np.random.random() < mutation_rate:
                # Swap two random fuel assemblies
                fuel_positions = np.where(self.core_layout > 0)
                if len(fuel_positions[0]) >= 2:
                    idx1, idx2 = np.random.choice(
                        len(fuel_positions[0]), size=2, replace=False
                    )
                    r1, c1 = fuel_positions[0][idx1], fuel_positions[1][idx1]
                    r2, c2 = fuel_positions[0][idx2], fuel_positions[1][idx2]
                    # Swap
                    offspring[i, r1, c1], offspring[i, r2, c2] = (
                        offspring[i, r2, c2],
                        offspring[i, r1, c1],
                    )
        return offspring
