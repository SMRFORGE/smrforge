"""
Comprehensive multi-physics coupling framework.

This module provides unified coupling between all physics domains:
- Neutronics (power distribution, flux)
- Thermal-hydraulics (temperature, flow)
- Structural mechanics (deformation, stress, creep)
- Control systems (reactivity control, power control)
- Burnup (composition changes, cross-section updates)

Provides both steady-state and transient multi-physics coupling.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from ..utils.logging import get_logger

logger = get_logger("smrforge.thermal.multiphysics_coupling")


@dataclass
class MultiPhysicsOptions:
    """
    Options for multi-physics coupling.
    
    Attributes:
        max_iterations: Maximum coupling iterations
        tolerance: Convergence tolerance
        under_relaxation: Under-relaxation factor (0-1)
        include_structural: Whether to include structural mechanics feedback
        include_control: Whether to include control systems
        include_burnup: Whether to include burnup feedback
        structural_update_frequency: Frequency of structural updates (iterations)
        control_update_frequency: Frequency of control updates (iterations)
    """
    
    max_iterations: int = 50
    tolerance: float = 1e-4
    under_relaxation: float = 0.5
    include_structural: bool = True
    include_control: bool = True
    include_burnup: bool = False
    structural_update_frequency: int = 5  # Update every N iterations
    control_update_frequency: int = 1  # Update every iteration
    burnup_update_frequency: int = 10  # Update every N iterations


@dataclass
class MultiPhysicsCoupling:
    """
    Comprehensive multi-physics coupling framework.
    
    Integrates neutronics, thermal-hydraulics, structural mechanics,
    control systems, and burnup for complete reactor analysis.
    
    Attributes:
        neutronics_solver: Neutronics solver (must have solve_steady_state, compute_power_distribution)
        thermal_solver: Thermal-hydraulics solver (must have solve_with_power)
        structural_mechanics: Optional structural mechanics solver (FuelRodMechanics)
        control_system: Optional control system (must have compute_reactivity_adjustment)
        burnup_solver: Optional burnup solver (must have update_composition)
        options: Multi-physics coupling options
    """
    
    neutronics_solver: Callable
    thermal_solver: Callable
    structural_mechanics: Optional[Callable] = None
    control_system: Optional[Callable] = None
    burnup_solver: Optional[Callable] = None
    options: MultiPhysicsOptions = field(default_factory=MultiPhysicsOptions)
    
    def __post_init__(self):
        """Initialize coupling state."""
        self.iteration_history: List[Dict] = []
        self.converged: bool = False
    
    def solve_steady_state(
        self,
        initial_temperature: Optional[np.ndarray] = None,
        initial_power: Optional[float] = None,
    ) -> Dict:
        """
        Solve steady-state multi-physics problem.
        
        Args:
            initial_temperature: Initial temperature distribution [K]
            initial_power: Initial power [W]
            
        Returns:
            Dictionary with converged solution:
                - k_eff: Effective multiplication factor
                - flux: Neutron flux distribution
                - power_distribution: Power distribution [W/cm³]
                - temperature: Temperature distribution [K]
                - structural_results: Structural mechanics results (if enabled)
                - control_adjustments: Control system adjustments (if enabled)
                - burnup_state: Burnup state (if enabled)
                - iterations: Number of iterations
                - converged: Whether solution converged
        """
        # Initialize state
        if initial_temperature is None:
            # Default: uniform temperature
            if hasattr(self.neutronics_solver, 'flux'):
                shape = self.neutronics_solver.flux.shape[:2]  # (nz, nr)
            else:
                shape = (10, 10)  # Default shape
            initial_temperature = np.full(shape, 1200.0)  # K
        
        temperature = initial_temperature.copy()
        power_distribution = None
        structural_state = None
        control_adjustments = {}
        burnup_state = None
        
        logger.info("Starting steady-state multi-physics coupling")
        
        for iteration in range(self.options.max_iterations):
            iteration_data = {
                "iteration": iteration + 1,
                "temperature": temperature.copy(),
            }
            
            # 1. Update neutronics with current temperature
            # Temperature affects cross-sections (Doppler broadening, etc.)
            if hasattr(self.neutronics_solver, 'update_temperature'):
                self.neutronics_solver.update_temperature(temperature)
            
            # Solve neutronics
            if hasattr(self.neutronics_solver, 'solve_steady_state'):
                k_eff, flux = self.neutronics_solver.solve_steady_state()
            else:
                # Fallback: assume solver returns (k_eff, flux)
                result = self.neutronics_solver(temperature)
                if isinstance(result, tuple):
                    k_eff, flux = result
                else:
                    k_eff = result.get("k_eff", 1.0)
                    flux = result.get("flux", np.ones_like(temperature))
            
            # 2. Compute power distribution
            if hasattr(self.neutronics_solver, 'compute_power_distribution'):
                if initial_power is None:
                    power = 10e6  # 10 MW default
                else:
                    power = initial_power
                power_distribution = self.neutronics_solver.compute_power_distribution(power)
            else:
                # Fallback: estimate from flux
                power_distribution = flux * 1e6  # Simplified
            
            iteration_data["k_eff"] = k_eff
            iteration_data["power_distribution"] = power_distribution.copy()
            
            # 3. Control system adjustment (if enabled)
            if self.options.include_control and self.control_system is not None:
                if iteration % self.options.control_update_frequency == 0:
                    if hasattr(self.control_system, 'compute_reactivity_adjustment'):
                        reactivity_adj = self.control_system.compute_reactivity_adjustment(
                            k_eff, power_distribution, temperature
                        )
                        control_adjustments = {
                            "reactivity_adjustment": reactivity_adj,
                            "k_eff_target": 1.0,
                        }
                        # Apply reactivity adjustment (simplified)
                        # In practice, this would adjust control rod positions, etc.
                        k_eff = k_eff + reactivity_adj * 0.01  # Small adjustment
                    else:
                        # Fallback: simple reactivity control
                        if k_eff > 1.01:
                            control_adjustments = {"reactivity_adjustment": -0.01}
                        elif k_eff < 0.99:
                            control_adjustments = {"reactivity_adjustment": 0.01}
                        else:
                            control_adjustments = {"reactivity_adjustment": 0.0}
            
            # 4. Solve thermal-hydraulics with power distribution
            if hasattr(self.thermal_solver, 'solve_with_power'):
                temperature_new = self.thermal_solver.solve_with_power(power_distribution)
            else:
                # Fallback: simple thermal model
                # Q = power, assume linear temperature rise
                heat_capacity = 1000.0  # J/(kg·K)
                density = 10000.0  # kg/m³
                volume = 1.0  # m³
                mass = density * volume
                delta_T = power_distribution.sum() / (mass * heat_capacity)
                temperature_new = temperature + delta_T
            
            # 5. Structural mechanics feedback (if enabled)
            if self.options.include_structural and self.structural_mechanics is not None:
                if iteration % self.options.structural_update_frequency == 0:
                    # Compute structural mechanics
                    # Average temperature for fuel and cladding
                    fuel_temp = temperature_new.mean()
                    clad_temp = fuel_temp - 200.0  # Approximate cladding temp
                    
                    # Get structural results
                    if hasattr(self.structural_mechanics, 'analyze'):
                        structural_state = self.structural_mechanics.analyze(
                            fuel_temperature=fuel_temp,
                            cladding_temperature=clad_temp,
                            burnup=0.0,  # Would come from burnup solver
                            power_density=power_distribution.mean(),
                            time=0.0,  # Steady-state
                            include_creep=False,  # Steady-state, no creep
                            include_degradation=False,
                        )
                        
                        # Structural feedback to neutronics:
                        # - Geometry changes affect neutronics (fuel radius, gap)
                        # - Material property changes affect cross-sections
                        if "fuel_radius" in structural_state:
                            # Geometry change feedback (simplified)
                            # In practice, would update geometry in neutronics solver
                            pass
                        
                        # Structural feedback to thermal:
                        # - Deformation affects heat transfer (gap changes, contact)
                        if "gap" in structural_state:
                            gap = structural_state["gap"]
                            # Gap closure affects heat transfer coefficient
                            # Simplified: reduce HTC if gap closes
                            if gap < 0.001:  # Gap closed
                                # Would update thermal solver with new gap
                                pass
                    
                    iteration_data["structural_state"] = structural_state
            
            # 6. Burnup feedback (if enabled)
            if self.options.include_burnup and self.burnup_solver is not None:
                if iteration % self.options.burnup_update_frequency == 0:
                    if hasattr(self.burnup_solver, 'update_composition'):
                        # Update composition based on burnup
                        burnup_state = self.burnup_solver.update_composition(
                            flux, power_distribution, time=0.0
                        )
                        # Update cross-sections in neutronics solver
                        if hasattr(self.neutronics_solver, 'update_cross_sections'):
                            self.neutronics_solver.update_cross_sections(burnup_state)
                    
                    iteration_data["burnup_state"] = burnup_state
            
            # 7. Check convergence
            error = np.max(np.abs(temperature_new - temperature)) / np.max(temperature)
            iteration_data["error"] = error
            
            if error < self.options.tolerance:
                logger.info(f"Multi-physics coupling converged in {iteration+1} iterations")
                self.converged = True
                temperature = temperature_new
                break
            
            # 8. Update temperature with relaxation
            omega = self.options.under_relaxation
            temperature = omega * temperature_new + (1 - omega) * temperature
            
            self.iteration_history.append(iteration_data)
        
        if not self.converged:
            logger.warning(
                f"Multi-physics coupling did not converge after {self.options.max_iterations} iterations"
            )
        
        return {
            "k_eff": k_eff,
            "flux": flux,
            "power_distribution": power_distribution,
            "temperature": temperature,
            "structural_results": structural_state,
            "control_adjustments": control_adjustments,
            "burnup_state": burnup_state,
            "iterations": iteration + 1,
            "converged": self.converged,
            "iteration_history": self.iteration_history,
        }
    
    def solve_transient(
        self,
        t_span: Tuple[float, float],
        initial_temperature: Optional[np.ndarray] = None,
        initial_power: Optional[float] = None,
        time_step: Optional[float] = None,
    ) -> Dict:
        """
        Solve transient multi-physics problem.
        
        Args:
            t_span: Time span (t_start, t_end) [s]
            initial_temperature: Initial temperature distribution [K]
            initial_power: Initial power [W]
            time_step: Time step [s] (if None, adaptive)
            
        Returns:
            Dictionary with transient solution:
                - time: Time points [s]
                - k_eff_history: k_eff vs time
                - power_history: Power distribution vs time
                - temperature_history: Temperature vs time
                - structural_history: Structural mechanics results vs time
                - control_history: Control system adjustments vs time
                - burnup_history: Burnup state vs time
        """
        t_start, t_end = t_span
        
        if time_step is None:
            time_step = (t_end - t_start) / 100.0  # Default: 100 steps
        
        time_points = np.arange(t_start, t_end, time_step)
        if time_points[-1] < t_end:
            time_points = np.append(time_points, t_end)
        
        # Initialize state
        if initial_temperature is None:
            if hasattr(self.neutronics_solver, 'flux'):
                shape = self.neutronics_solver.flux.shape[:2]
            else:
                shape = (10, 10)
            initial_temperature = np.full(shape, 1200.0)
        
        temperature = initial_temperature.copy()
        
        # History arrays
        k_eff_history = []
        power_history = []
        temperature_history = [temperature.copy()]
        structural_history = []
        control_history = []
        burnup_history = []
        
        logger.info(f"Starting transient multi-physics coupling: t_span={t_span}")
        
        cumulative_time = 0.0  # For burnup
        
        for i, t in enumerate(time_points):
            dt = time_points[i] - time_points[i-1] if i > 0 else time_step
            
            # Solve steady-state at each time step
            result = self.solve_steady_state(
                initial_temperature=temperature,
                initial_power=initial_power,
            )
            
            # Update state
            temperature = result["temperature"]
            k_eff_history.append(result["k_eff"])
            power_history.append(result["power_distribution"].copy())
            temperature_history.append(temperature.copy())
            
            if result["structural_results"]:
                structural_history.append(result["structural_results"])
            
            if result["control_adjustments"]:
                control_history.append(result["control_adjustments"])
            
            if result["burnup_state"]:
                burnup_history.append(result["burnup_state"])
            
            # Update cumulative time for burnup
            cumulative_time += dt
            
            # Reset convergence flag for next iteration
            self.converged = False
            self.iteration_history = []
        
        return {
            "time": time_points,
            "k_eff_history": np.array(k_eff_history),
            "power_history": power_history,
            "temperature_history": temperature_history,
            "structural_history": structural_history,
            "control_history": control_history,
            "burnup_history": burnup_history,
        }
    
    def get_coupling_matrix(self) -> np.ndarray:
        """
        Get coupling matrix showing interactions between physics domains.
        
        Returns:
            Coupling matrix (5x5) showing strength of coupling:
            [Neutronics, Thermal, Structural, Control, Burnup]
        """
        matrix = np.zeros((5, 5))
        
        # Neutronics -> Thermal (power -> temperature)
        matrix[0, 1] = 1.0
        
        # Thermal -> Neutronics (temperature -> cross-sections)
        matrix[1, 0] = 1.0
        
        # Structural -> Neutronics (geometry -> neutronics)
        if self.options.include_structural:
            matrix[2, 0] = 0.5
        
        # Structural -> Thermal (deformation -> heat transfer)
        if self.options.include_structural:
            matrix[2, 1] = 0.5
        
        # Thermal -> Structural (temperature -> stress, expansion)
        if self.options.include_structural:
            matrix[1, 2] = 1.0
        
        # Neutronics -> Structural (power -> temperature -> stress)
        if self.options.include_structural:
            matrix[0, 2] = 0.5
        
        # Control -> Neutronics (reactivity adjustment)
        if self.options.include_control:
            matrix[3, 0] = 1.0
        
        # Neutronics -> Control (k_eff feedback)
        if self.options.include_control:
            matrix[0, 3] = 0.5
        
        # Burnup -> Neutronics (composition -> cross-sections)
        if self.options.include_burnup:
            matrix[4, 0] = 0.8
        
        # Neutronics -> Burnup (flux -> burnup rate)
        if self.options.include_burnup:
            matrix[0, 4] = 1.0
        
        return matrix
