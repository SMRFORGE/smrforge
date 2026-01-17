"""
Fuel cycle and refueling strategy optimization.

This module provides optimization algorithms for:
- Fuel cycle length optimization
- Refueling strategy optimization (batch sizes, enrichment, shuffling)
- Multi-objective optimization (cost, cycle length, burnup)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from ..utils.logging import get_logger

logger = get_logger("smrforge.fuel_cycle.optimization")


@dataclass
class FuelCycleOptimizer:
    """
    Fuel cycle optimization algorithms.
    
    Optimizes fuel cycle parameters including:
    - Cycle length
    - Enrichment
    - Batch sizes
    - Target burnup
    
    Attributes:
        power_thermal: Thermal power [W]
        initial_enrichment: Initial enrichment fraction
        target_keff: Target k_eff at end of cycle
        max_cycle_length: Maximum cycle length [days]
        min_cycle_length: Minimum cycle length [days]
        optimization_objective: Objective function ('min_cost', 'max_cycle', 'max_burnup')
    """
    
    power_thermal: float  # W
    initial_enrichment: float = 0.045  # 4.5%
    target_keff: float = 1.0
    max_cycle_length: float = 2000.0  # days (~5.5 years)
    min_cycle_length: float = 365.0  # days (1 year)
    optimization_objective: str = "min_cost"  # 'min_cost', 'max_cycle', 'max_burnup'
    
    def optimize_cycle_length(
        self,
        burnup_solver: Callable,
        initial_guess: Optional[float] = None,
    ) -> Dict:
        """
        Optimize fuel cycle length.
        
        Finds the optimal cycle length that maximizes burnup while
        maintaining criticality constraints.
        
        Args:
            burnup_solver: Callable that takes cycle_length and returns (k_eff, burnup)
            initial_guess: Initial guess for cycle length [days]
            
        Returns:
            Dictionary with optimization results
        """
        if initial_guess is None:
            initial_guess = (self.max_cycle_length + self.min_cycle_length) / 2.0
        
        # Binary search for optimal cycle length
        low = self.min_cycle_length
        high = self.max_cycle_length
        tolerance = 1.0  # days
        
        best_cycle = initial_guess
        best_keff = None
        best_burnup = 0.0
        
        iterations = 0
        max_iterations = 50
        
        while (high - low) > tolerance and iterations < max_iterations:
            mid = (low + high) / 2.0
            keff, burnup = burnup_solver(mid)
            
            if abs(keff - self.target_keff) < 0.001:
                # Found good match
                if burnup > best_burnup:
                    best_cycle = mid
                    best_keff = keff
                    best_burnup = burnup
                break
            elif keff > self.target_keff:
                # Too long, reduce cycle length
                high = mid
            else:
                # Too short, increase cycle length
                low = mid
            
            iterations += 1
        
        return {
            "optimal_cycle_length": best_cycle,
            "k_eff": best_keff,
            "discharge_burnup": best_burnup,
            "iterations": iterations,
        }
    
    def optimize_enrichment(
        self,
        cycle_length: float,
        burnup_solver: Callable,
        enrichment_range: Tuple[float, float] = (0.03, 0.20),
    ) -> Dict:
        """
        Optimize enrichment for given cycle length.
        
        Args:
            cycle_length: Target cycle length [days]
            burnup_solver: Callable that takes (enrichment, cycle_length) and returns (k_eff, burnup)
            enrichment_range: (min, max) enrichment range
            
        Returns:
            Dictionary with optimization results
        """
        low, high = enrichment_range
        tolerance = 0.001  # 0.1%
        
        best_enrichment = self.initial_enrichment
        best_keff = None
        best_burnup = 0.0
        
        iterations = 0
        max_iterations = 50
        
        while (high - low) > tolerance and iterations < max_iterations:
            mid = (low + high) / 2.0
            keff, burnup = burnup_solver(mid, cycle_length)
            
            if abs(keff - self.target_keff) < 0.001:
                # Found good match
                if burnup > best_burnup:
                    best_enrichment = mid
                    best_keff = keff
                    best_burnup = burnup
                break
            elif keff > self.target_keff:
                # Too high enrichment, reduce
                high = mid
            else:
                # Too low enrichment, increase
                low = mid
            
            iterations += 1
        
        return {
            "optimal_enrichment": best_enrichment,
            "k_eff": best_keff,
            "discharge_burnup": best_burnup,
            "iterations": iterations,
        }
    
    def multi_objective_optimization(
        self,
        burnup_solver: Callable,
        cost_function: Optional[Callable] = None,
        weights: Dict[str, float] = None,
    ) -> Dict:
        """
        Multi-objective optimization of fuel cycle.
        
        Optimizes cycle length, enrichment, and batch configuration
        considering multiple objectives (cost, cycle length, burnup).
        
        Args:
            burnup_solver: Callable for burnup calculations
            cost_function: Optional cost function (enrichment, cycle_length) -> cost
            weights: Weights for objectives {'cost': 0.4, 'cycle_length': 0.3, 'burnup': 0.3}
            
        Returns:
            Dictionary with optimization results
        """
        if weights is None:
            weights = {"cost": 0.4, "cycle_length": 0.3, "burnup": 0.3}
        
        if cost_function is None:
            # Default cost function: enrichment cost + cycle length cost
            def cost_function(enrichment, cycle_length):
                enrichment_cost = 1000.0 * enrichment  # USD/kg per % enrichment
                cycle_cost = 100.0 * cycle_length / 365.0  # USD per year
                return enrichment_cost + cycle_cost
        
        # Grid search over parameter space
        enrichments = np.linspace(0.03, 0.20, 10)
        cycle_lengths = np.linspace(
            self.min_cycle_length, self.max_cycle_length, 10
        )
        
        best_score = float("inf")
        best_params = None
        best_results = None
        
        for enrichment in enrichments:
            for cycle_length in cycle_lengths:
                keff, burnup = burnup_solver(enrichment, cycle_length)
                
                if abs(keff - self.target_keff) > 0.01:
                    continue  # Skip non-critical configurations
                
                # Calculate multi-objective score
                cost = cost_function(enrichment, cycle_length)
                normalized_cost = cost / 10000.0  # Normalize
                normalized_cycle = cycle_length / self.max_cycle_length
                normalized_burnup = burnup / 100.0  # Normalize to 100 MWd/kg
                
                # Minimize cost, maximize cycle length and burnup
                score = (
                    weights["cost"] * normalized_cost
                    - weights["cycle_length"] * normalized_cycle
                    - weights["burnup"] * normalized_burnup
                )
                
                if score < best_score:
                    best_score = score
                    best_params = {
                        "enrichment": enrichment,
                        "cycle_length": cycle_length,
                    }
                    best_results = {
                        "k_eff": keff,
                        "burnup": burnup,
                        "cost": cost,
                        "score": score,
                    }
        
        return {
            "optimal_parameters": best_params,
            "results": best_results,
            "objective_weights": weights,
        }


@dataclass
class RefuelingStrategyOptimizer:
    """
    Refueling strategy optimization.
    
    Optimizes refueling strategies including:
    - Batch sizes and fractions
    - Shuffling patterns
    - Fresh fuel enrichment
    - Refueling frequency
    
    Attributes:
        n_assemblies: Number of fuel assemblies
        max_batches: Maximum number of batches
        cycle_length: Cycle length [days]
        optimization_objective: Objective function
    """
    
    n_assemblies: int
    max_batches: int = 3
    cycle_length: float = 1095.0  # days (3 years)
    optimization_objective: str = "min_cost"  # 'min_cost', 'max_burnup', 'max_cycle'
    
    def optimize_batch_configuration(
        self,
        burnup_solver: Callable,
        shuffle_patterns: List[str] = None,
    ) -> Dict:
        """
        Optimize batch configuration and shuffling pattern.
        
        Args:
            burnup_solver: Callable that takes (n_batches, batch_fractions, shuffle_pattern) 
                          and returns (k_eff, burnup, cost)
            shuffle_patterns: List of shuffle patterns to try
            
        Returns:
            Dictionary with optimization results
        """
        if shuffle_patterns is None:
            shuffle_patterns = ["out-in", "in-out", "scatter"]
        
        best_config = None
        best_score = float("inf")
        
        # Try different numbers of batches
        for n_batches in range(2, self.max_batches + 1):
            # Try different batch fraction distributions
            # Equal batches
            equal_fractions = [1.0 / n_batches] * n_batches
            
            # Try different shuffle patterns
            for pattern in shuffle_patterns:
                keff, burnup, cost = burnup_solver(
                    n_batches, equal_fractions, pattern
                )
                
                # Score based on objective
                if self.optimization_objective == "min_cost":
                    score = cost
                elif self.optimization_objective == "max_burnup":
                    score = -burnup  # Negative to minimize
                else:  # max_cycle
                    score = -keff  # Higher k_eff allows longer cycles
                
                if score < best_score:
                    best_score = score
                    best_config = {
                        "n_batches": n_batches,
                        "batch_fractions": equal_fractions,
                        "shuffle_pattern": pattern,
                        "k_eff": keff,
                        "burnup": burnup,
                        "cost": cost,
                    }
        
        return {"optimal_configuration": best_config}
    
    def optimize_refueling_frequency(
        self,
        burnup_solver: Callable,
        min_frequency: float = 0.5,  # years
        max_frequency: float = 5.0,  # years
    ) -> Dict:
        """
        Optimize refueling frequency.
        
        Args:
            burnup_solver: Callable that takes refueling_frequency and returns (cost, burnup)
            min_frequency: Minimum refueling frequency [years]
            max_frequency: Maximum refueling frequency [years]
            
        Returns:
            Dictionary with optimization results
        """
        frequencies = np.linspace(min_frequency, max_frequency, 20)
        
        best_frequency = None
        best_score = float("inf")
        best_results = None
        
        for frequency in frequencies:
            cost, burnup = burnup_solver(frequency)
            
            # Score: minimize cost per unit burnup
            score = cost / burnup if burnup > 0 else float("inf")
            
            if score < best_score:
                best_score = score
                best_frequency = frequency
                best_results = {"cost": cost, "burnup": burnup, "score": score}
        
        return {
            "optimal_frequency": best_frequency,
            "results": best_results,
        }
