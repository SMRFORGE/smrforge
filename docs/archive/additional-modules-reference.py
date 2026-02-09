"""
Additional SMRForge Modules
===========================
This file contains starter implementations for missing modules:
1. Fuel Performance
2. Materials Database
3. I/O Utilities
4. Visualization Tools
5. Optimization
6. Control Systems
7. Economics

Place these in their respective directories after migration.

Archived from repo root — reference only.
"""

# ============================================================================
# FILE: smrforge/fuel/performance.py
# ============================================================================

FUEL_PERFORMANCE = '''"""
Fuel Performance Module
======================
Models fuel behavior including temperature, swelling, and fission gas release.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional

@dataclass
class FuelProperties:
    """Fuel pellet properties"""
    diameter: float  # cm
    height: float  # cm
    density: float  # g/cm^3
    enrichment: float  # % U-235
    burnup: float = 0.0  # MWd/kgU
    
@dataclass
class CladProperties:
    """Cladding properties"""
    inner_diameter: float  # cm
    outer_diameter: float  # cm
    material: str = "Zircaloy-4"
    
class FuelPerformance:
    """Fuel performance analysis"""
    
    def __init__(self, fuel: FuelProperties, clad: CladProperties):
        self.fuel = fuel
        self.clad = clad
        
    def fuel_centerline_temperature(self, linear_power: float, 
                                   coolant_temp: float) -> float:
        """
        Calculate fuel centerline temperature
        
        Args:
            linear_power: kW/m
            coolant_temp: K
            
        Returns:
            Centerline temperature in K
        """
        # Simplified correlation
        q_prime = linear_power * 1000  # W/m
        k_fuel = 3.0  # W/m-K (simplified UO2 conductivity)
        r_fuel = self.fuel.diameter / 2 / 100  # m
        
        # Temperature rise in fuel
        delta_T_fuel = q_prime / (4 * np.pi * k_fuel)
        
        # Add gap and clad resistance (simplified)
        delta_T_gap = q_prime * 0.0001  # Simplified
        
        T_centerline = coolant_temp + delta_T_fuel + delta_T_gap
        return T_centerline
    
    def fission_gas_release(self, temperature: float, 
                           burnup: float) -> float:
        """
        Calculate fission gas release fraction
        
        Args:
            temperature: K
            burnup: MWd/kgU
            
        Returns:
            FGR fraction (0-1)
        """
        # Simplified Forsberg-Massih model
        if temperature < 1273:  # Below threshold
            return 0.01 * burnup / 50000  # Linear with burnup
        else:
            # Temperature-dependent release
            fgr = 0.01 * (temperature - 1273) / 500 * burnup / 30000
            return min(fgr, 0.15)  # Cap at 15%
    
    def fuel_swelling(self, burnup: float, temperature: float) -> float:
        """
        Calculate fuel swelling
        
        Args:
            burnup: MWd/kgU
            temperature: K
            
        Returns:
            Volumetric swelling (%)
        """
        # Simplified model: swelling increases with burnup
        swelling = 0.5 * burnup / 10000  # 0.5% per 10 GWd/tU
        
        # Temperature enhancement
        if temperature > 1500:
            swelling *= 1.2
            
        return swelling
'''

# ============================================================================
# FILE: smrforge/materials/database.py
# ============================================================================

MATERIALS_DATABASE = '''"""
Materials Property Database
===========================
Centralized database for material properties with temperature dependence.
"""

import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class Material:
    """Material properties"""
    name: str
    density: float  # g/cm^3 at reference temperature
    thermal_conductivity: callable  # k(T) in W/m-K
    specific_heat: callable  # cp(T) in J/kg-K
    melting_point: Optional[float] = None  # K
    
class MaterialDatabase:
    """Database of nuclear materials"""
    
    def __init__(self):
        self.materials: Dict[str, Material] = {}
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize with common materials"""
        
        # UO2 fuel
        self.materials['UO2'] = Material(
            name='Uranium Dioxide',
            density=10.96,
            thermal_conductivity=self._uo2_conductivity,
            specific_heat=self._uo2_specific_heat,
            melting_point=3120.0
        )
        
        # Zircaloy-4 cladding
        self.materials['Zircaloy-4'] = Material(
            name='Zircaloy-4',
            density=6.56,
            thermal_conductivity=self._zircaloy_conductivity,
            specific_heat=self._zircaloy_specific_heat,
            melting_point=2125.0
        )
        
        # Water
        self.materials['H2O'] = Material(
            name='Water',
            density=1.0,
            thermal_conductivity=self._water_conductivity,
            specific_heat=self._water_specific_heat,
            melting_point=273.15
        )
    
    @staticmethod
    def _uo2_conductivity(T: float) -> float:
        """UO2 thermal conductivity (W/m-K)"""
        # Simplified Fink-Petty correlation
        k = 100.0 / (7.5408 + 17.692 * T/1000 + 3.6142 * (T/1000)**2)
        return k + 6400.0 / T**2.5 * np.exp(-16.35/T*1000)
    
    @staticmethod
    def _uo2_specific_heat(T: float) -> float:
        """UO2 specific heat (J/kg-K)"""
        # Simplified correlation
        theta = T / 1000
        cp = 302.27 + 8.463e-3 * T + 8.741e7 / T**2
        return cp
    
    @staticmethod
    def _zircaloy_conductivity(T: float) -> float:
        """Zircaloy-4 thermal conductivity (W/m-K)"""
        return 7.51 + 2.09e-2 * T - 1.45e-5 * T**2 + 7.67e-9 * T**3
    
    @staticmethod
    def _zircaloy_specific_heat(T: float) -> float:
        """Zircaloy-4 specific heat (J/kg-K)"""
        return 252.54 + 0.11474 * T
    
    @staticmethod
    def _water_conductivity(T: float) -> float:
        """Water thermal conductivity (W/m-K) - simplified"""
        return 0.6  # Approximate constant
    
    @staticmethod
    def _water_specific_heat(T: float) -> float:
        """Water specific heat (J/kg-K) - simplified"""
        return 4180.0  # Approximate constant
    
    def get_material(self, name: str) -> Material:
        """Get material by name"""
        if name not in self.materials:
            raise ValueError(f"Material '{name}' not in database")
        return self.materials[name]
    
    def add_material(self, material: Material):
        """Add custom material to database"""
        self.materials[material.name] = material
'''

# ============================================================================
# FILE: smrforge/io/readers.py
# ============================================================================

IO_READERS = '''"""
Input File Readers
=================
Read various input formats for reactor configurations.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any

class InputReader:
    """Base class for input readers"""
    
    @staticmethod
    def read_json(filepath: Path) -> Dict[str, Any]:
        """Read JSON input file"""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def read_yaml(filepath: Path) -> Dict[str, Any]:
        """Read YAML input file"""
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def read_legacy_input(filepath: Path) -> Dict[str, Any]:
        """Read legacy card-based input format"""
        config = {}
        
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse card format: KEY = VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        
        return config

class OutputWriter:
    """Output file writers"""
    
    @staticmethod
    def write_json(data: Dict[str, Any], filepath: Path):
        """Write JSON output"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def write_csv(data: Dict[str, list], filepath: Path):
        """Write CSV output"""
        import csv
        
        with open(filepath, 'w', newline='') as f:
            if not data:
                return
            
            writer = csv.DictWriter(f, fieldnames=data.keys())
            writer.writeheader()
            
            # Transpose data
            n_rows = len(next(iter(data.values())))
            for i in range(n_rows):
                row = {key: values[i] for key, values in data.items()}
                writer.writerow(row)
'''

# ============================================================================
# FILE: smrforge/visualization/plots.py
# ============================================================================

VISUALIZATION = '''"""
Visualization Tools
==================
Plotting and visualization utilities for reactor analysis.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, List, Tuple

class ReactorPlots:
    """Standard reactor visualization plots"""
    
    @staticmethod
    def plot_flux_distribution(r: np.ndarray, flux: np.ndarray, 
                              title: str = "Radial Flux Distribution"):
        """Plot radial flux distribution"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(r, flux, 'b-', linewidth=2)
        ax.set_xlabel('Radius (cm)', fontsize=12)
        ax.set_ylabel('Relative Flux', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig, ax
    
    @staticmethod
    def plot_temperature_profile(r: np.ndarray, T: np.ndarray,
                                T_fuel: Optional[np.ndarray] = None):
        """Plot temperature profile"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(r, T, 'r-', linewidth=2, label='Coolant')
        if T_fuel is not None:
            ax.plot(r, T_fuel, 'b-', linewidth=2, label='Fuel')
        
        ax.set_xlabel('Radius (cm)', fontsize=12)
        ax.set_ylabel('Temperature (K)', fontsize=12)
        ax.set_title('Temperature Distribution', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig, ax
    
    @staticmethod
    def plot_transient_response(time: np.ndarray, power: np.ndarray,
                               temperature: Optional[np.ndarray] = None):
        """Plot transient response"""
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        # Power
        axes[0].plot(time, power, 'b-', linewidth=2)
        axes[0].set_xlabel('Time (s)', fontsize=12)
        axes[0].set_ylabel('Relative Power', fontsize=12)
        axes[0].set_title('Power Response', fontsize=13, fontweight='bold')
        axes[0].grid(True, alpha=0.3)
        
        # Temperature
        if temperature is not None:
            axes[1].plot(time, temperature, 'r-', linewidth=2)
            axes[1].set_xlabel('Time (s)', fontsize=12)
            axes[1].set_ylabel('Temperature (K)', fontsize=12)
            axes[1].set_title('Temperature Response', fontsize=13, fontweight='bold')
            axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig, axes
    
    @staticmethod
    def plot_core_map(assembly_powers: np.ndarray, title: str = "Core Power Map"):
        """Plot 2D core power map"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        im = ax.imshow(assembly_powers, cmap='hot', interpolation='nearest')
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Relative Power', fontsize=11)
        
        # Add grid
        ax.set_xticks(np.arange(assembly_powers.shape[1]))
        ax.set_yticks(np.arange(assembly_powers.shape[0]))
        ax.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
        
        plt.tight_layout()
        return fig, ax
'''

# ============================================================================
# FILE: smrforge/optimization/optimizer.py
# ============================================================================

OPTIMIZATION = '''"""
Design Optimization
==================
Optimization algorithms for reactor design.
"""

import numpy as np
from typing import Callable, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class OptimizationResult:
    """Optimization result"""
    x_opt: np.ndarray  # Optimal parameters
    f_opt: float  # Optimal objective value
    n_iterations: int  # Number of iterations
    success: bool  # Convergence flag
    
class GeneticAlgorithm:
    """Genetic algorithm optimizer"""
    
    def __init__(self, objective: Callable, 
                 bounds: List[Tuple[float, float]],
                 population_size: int = 50,
                 generations: int = 100):
        self.objective = objective
        self.bounds = np.array(bounds)
        self.pop_size = population_size
        self.n_gen = generations
        self.n_params = len(bounds)
    
    def optimize(self) -> OptimizationResult:
        """Run genetic algorithm"""
        # Initialize population
        population = self._initialize_population()
        
        best_individual = None
        best_fitness = float('inf')
        
        for gen in range(self.n_gen):
            # Evaluate fitness
            fitness = np.array([self.objective(ind) for ind in population])
            
            # Track best
            min_idx = np.argmin(fitness)
            if fitness[min_idx] < best_fitness:
                best_fitness = fitness[min_idx]
                best_individual = population[min_idx].copy()
            
            # Selection
            selected = self._selection(population, fitness)
            
            # Crossover
            offspring = self._crossover(selected)
            
            # Mutation
            population = self._mutation(offspring)
        
        return OptimizationResult(
            x_opt=best_individual,
            f_opt=best_fitness,
            n_iterations=self.n_gen,
            success=True
        )
    
    def _initialize_population(self) -> np.ndarray:
        """Initialize random population"""
        pop = np.random.uniform(
            low=self.bounds[:, 0],
            high=self.bounds[:, 1],
            size=(self.pop_size, self.n_params)
        )
        return pop
    
    def _selection(self, population: np.ndarray, 
                  fitness: np.ndarray) -> np.ndarray:
        """Tournament selection"""
        selected = []
        for _ in range(self.pop_size):
            # Tournament
            idx = np.random.choice(self.pop_size, size=3, replace=False)
            winner = idx[np.argmin(fitness[idx])]
            selected.append(population[winner])
        return np.array(selected)
    
    def _crossover(self, parents: np.ndarray) -> np.ndarray:
        """Single-point crossover"""
        offspring = []
        for i in range(0, len(parents), 2):
            if i + 1 < len(parents):
                point = np.random.randint(1, self.n_params)
                child1 = np.concatenate([parents[i][:point], parents[i+1][point:]])
                child2 = np.concatenate([parents[i+1][:point], parents[i][point:]])
                offspring.extend([child1, child2])
            else:
                offspring.append(parents[i])
        return np.array(offspring)
    
    def _mutation(self, offspring: np.ndarray) -> np.ndarray:
        """Gaussian mutation"""
        mutation_rate = 0.1
        for i in range(len(offspring)):
            if np.random.random() < mutation_rate:
                gene = np.random.randint(self.n_params)
                offspring[i, gene] += np.random.normal(0, 0.1)
                # Clip to bounds
                offspring[i, gene] = np.clip(
                    offspring[i, gene],
                    self.bounds[gene, 0],
                    self.bounds[gene, 1]
                )
        return offspring
'''

# ============================================================================
# FILE: smrforge/control/pid.py
# ============================================================================

CONTROL_SYSTEMS = '''"""
Control Systems
==============
PID controllers and reactor control logic.
"""

import numpy as np
from dataclasses import dataclass

@dataclass
class PIDController:
    """PID controller implementation"""
    Kp: float  # Proportional gain
    Ki: float  # Integral gain
    Kd: float  # Derivative gain
    setpoint: float = 0.0
    
    def __post_init__(self):
        self.integral = 0.0
        self.last_error = 0.0
    
    def update(self, measurement: float, dt: float) -> float:
        """
        Update PID controller
        
        Args:
            measurement: Current process variable
            dt: Time step
            
        Returns:
            Control output
        """
        error = self.setpoint - measurement
        
        # Proportional term
        P = self.Kp * error
        
        # Integral term
        self.integral += error * dt
        I = self.Ki * self.integral
        
        # Derivative term
        derivative = (error - self.last_error) / dt if dt > 0 else 0
        D = self.Kd * derivative
        
        # Update state
        self.last_error = error
        
        # Control output
        output = P + I + D
        return output
    
    def reset(self):
        """Reset controller state"""
        self.integral = 0.0
        self.last_error = 0.0

class ReactorController:
    """Reactor power control system"""
    
    def __init__(self, power_setpoint: float):
        # Power controller
        self.power_controller = PIDController(
            Kp=0.5,
            Ki=0.1,
            Kd=0.05,
            setpoint=power_setpoint
        )
        
        # Temperature controller
        self.temp_controller = PIDController(
            Kp=1.0,
            Ki=0.2,
            Kd=0.1,
            setpoint=600.0  # K
        )
    
    def control_step(self, power: float, temperature: float, 
                    dt: float) -> dict:
        """
        Execute control step
        
        Returns:
            Dictionary with control rod position and other commands
        """
        # Calculate control rod insertion
        power_signal = self.power_controller.update(power, dt)
        temp_signal = self.temp_controller.update(temperature, dt)
        
        # Combine signals (simple weighted sum)
        rod_position = 0.7 * power_signal + 0.3 * temp_signal
        
        # Limit rod position (0-100%)
        rod_position = np.clip(rod_position, 0, 100)
        
        return {
            'rod_position': rod_position,
            'power_error': self.power_controller.last_error,
            'temp_error': self.temp_controller.last_error
        }
'''

# ============================================================================
# FILE: smrforge/economics/lcoe.py
# ============================================================================

ECONOMICS = '''"""
Economic Analysis
================
Cost modeling and LCOE calculations.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional

@dataclass
class EconomicParameters:
    """Economic parameters for LCOE calculation"""
    capital_cost: float  # $ million
    annual_om_cost: float  # $ million/year
    fuel_cost: float  # $/kgU
    discount_rate: float = 0.07  # 7%
    plant_lifetime: int = 60  # years
    capacity_factor: float = 0.90
    thermal_power: float = 160.0  # MWth
    thermal_efficiency: float = 0.33
    
class LCOE:
    """Levelized Cost of Electricity calculator"""
    
    def __init__(self, params: EconomicParameters):
        self.params = params
    
    def calculate_lcoe(self) -> float:
        """
        Calculate LCOE in $/MWh
        
        Returns:
            LCOE in $/MWh
        """
        # Capital recovery factor
        r = self.params.discount_rate
        n = self.params.plant_lifetime
        CRF = r * (1 + r)**n / ((1 + r)**n - 1)
        
        # Annual capital cost
        annual_capital = self.params.capital_cost * 1e6 * CRF
        
        # Annual O&M cost
        annual_om = self.params.annual_om_cost * 1e6
        
        # Total annual cost
        total_annual_cost = annual_capital + annual_om
        
        # Annual energy production
        electric_power = (self.params.thermal_power * 
                         self.params.thermal_efficiency)  # MWe
        annual_energy = (electric_power * 8760 * 
                        self.params.capacity_factor)  # MWh/year
        
        # LCOE
        lcoe = total_annual_cost / annual_energy
        
        return lcoe
    
    def sensitivity_analysis(self, parameter: str, 
                           variation: np.ndarray) -> np.ndarray:
        """
        Perform sensitivity analysis on a parameter
        
        Args:
            parameter: Parameter name to vary
            variation: Array of multipliers (e.g., [0.8, 0.9, 1.0, 1.1, 1.2])
            
        Returns:
            Array of LCOE values
        """
        lcoe_values = []
        
        for mult in variation:
            # Create modified parameters
            params_copy = EconomicParameters(**self.params.__dict__)
            
            if hasattr(params_copy, parameter):
                setattr(params_copy, parameter, 
                       getattr(params_copy, parameter) * mult)
                
                # Calculate LCOE with modified parameter
                calc = LCOE(params_copy)
                lcoe_values.append(calc.calculate_lcoe())
        
        return np.array(lcoe_values)
'''

# Print all modules
print("="*70)
print("Additional SMRForge Modules")
print("="*70)
print("\nGenerated modules:")
print("1. fuel/performance.py")
print("2. materials/database.py")
print("3. io/readers.py")
print("4. visualization/plots.py")
print("5. optimization/optimizer.py")
print("6. control/pid.py")
print("7. economics/lcoe.py")
print("\nSave each section to its respective file after running migration script.")
print("="*70)
