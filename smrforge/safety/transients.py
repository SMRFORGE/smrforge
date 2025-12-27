# smrforge/safety/transients.py
"""
HTGR-specific transient scenarios and accident analysis.
Includes: LOFC, ATWS, reactivity insertion, air/water ingress.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from numba import njit, prange
from rich.console import Console
from rich.live import Live
from rich.progress import Progress
from rich.table import Table
from scipy.integrate import odeint, solve_ivp
from scipy.optimize import fsolve


class TransientType(Enum):
    """
    Types of transient scenarios for HTGR safety analysis.
    
    Enum values identify different accident scenarios and operational transients
    that may occur in HTGRs. Each transient type requires different modeling
    approaches and has different safety implications.
    
    Attributes:
        LOFC: Loss of Forced Cooling - design basis accident, loss of primary
            coolant circulation.
        ATWS: Anticipated Transient Without Scram - failure to scram during
            a transient event.
        RIA: Reactivity Insertion Accident - uncontrolled reactivity addition.
        LOCA: Loss of Coolant Accident - breach in primary pressure boundary.
        AIR_INGRESS: Air ingress accident - air enters the primary circuit.
        WATER_INGRESS: Water ingress accident - water enters the primary circuit.
        LOAD_FOLLOWING: Normal operational transient for load following.
    """

    LOFC = "loss_of_forced_cooling"
    ATWS = "anticipated_transient_without_scram"
    RIA = "reactivity_insertion_accident"
    LOCA = "loss_of_coolant_accident"
    AIR_INGRESS = "air_ingress"
    WATER_INGRESS = "water_ingress"
    LOAD_FOLLOWING = "load_following"


@dataclass
class TransientConditions:
    """
    Initial and boundary conditions for transient simulation.
    
    Encapsulates all conditions needed to define and run a transient scenario,
    including initial reactor state, transient trigger, time span, safety
    system availability, and environmental conditions.
    
    Attributes:
        initial_power: Initial reactor thermal power in Watts.
        initial_temperature: Initial average core temperature in Kelvin.
        initial_flow_rate: Initial primary coolant flow rate in kg/s.
        initial_pressure: Initial primary system pressure in Pascal.
        transient_type: Type of transient (TransientType enum).
        trigger_time: Time at which transient is initiated in seconds.
        t_start: Simulation start time in seconds (default: 0.0).
        t_end: Simulation end time in seconds (default: 259200 = 72 hours).
        scram_available: Whether control rod scram is available (default: True).
        scram_delay: Time delay for scram insertion in seconds (default: 1.0).
        emergency_cooling: Whether emergency cooling systems are active (default: False).
        ambient_temperature: Ambient temperature for heat transfer in Kelvin (default: 300.0).
        atmospheric_pressure: Atmospheric pressure in Pascal (default: 101325.0).
    
    Example:
        >>> conditions = TransientConditions(
        ...     initial_power=10e6,  # 10 MWth
        ...     initial_temperature=1200.0,  # 927°C
        ...     initial_flow_rate=5.0,  # kg/s
        ...     initial_pressure=7.0e6,  # 7 MPa
        ...     transient_type=TransientType.LOFC,
        ...     trigger_time=0.0,
        ...     scram_available=True,
        ...     scram_delay=1.0
        ... )
    """

    initial_power: float  # W
    initial_temperature: float  # K (average core)
    initial_flow_rate: float  # kg/s
    initial_pressure: float  # Pa

    # Transient trigger
    transient_type: TransientType
    trigger_time: float  # s

    # Time span
    t_start: float = 0.0  # s
    t_end: float = 72 * 3600  # s (72 hours default)

    # Safety systems
    scram_available: bool = True
    scram_delay: float = 1.0  # s
    emergency_cooling: bool = False

    # Environmental
    ambient_temperature: float = 300.0  # K
    atmospheric_pressure: float = 1.013e5  # Pa


@dataclass
class PointKineticsParameters:
    """
    Point kinetics parameters for transient analysis.
    
    Contains all physical parameters needed for point kinetics equations
    with temperature feedback. Used by PointKineticsSolver for transient
    simulations.
    
    Attributes:
        beta: 1D array of delayed neutron fractions for each precursor group.
            Typically 6 groups for thermal reactors. Units: dimensionless.
        lambda_d: 1D array of precursor decay constants for each group.
            Units: 1/s. Must have same length as beta.
        alpha_fuel: Fuel temperature reactivity coefficient. Units: dk/k/K
            (change in reactivity per degree Kelvin).
        alpha_moderator: Moderator temperature reactivity coefficient.
            Units: dk/k/K.
        Lambda: Prompt neutron lifetime in seconds. Typical values:
            - Thermal reactors: ~10^-4 to 10^-3 s
            - Fast reactors: ~10^-7 to 10^-6 s
        fuel_heat_capacity: Effective fuel heat capacity in J/K. Used for
            fuel temperature calculation.
        moderator_heat_capacity: Effective moderator heat capacity in J/K.
    
    Example:
        >>> # Typical HTGR delayed neutron parameters (6-group)
        >>> beta = np.array([0.00021, 0.00141, 0.00127, 0.00255, 0.00074, 0.00027])
        >>> lambda_d = np.array([0.0127, 0.0317, 0.115, 0.311, 1.40, 3.87])
        >>> params = PointKineticsParameters(
        ...     beta=beta,
        ...     lambda_d=lambda_d,
        ...     alpha_fuel=-5e-5,  # Negative = stable
        ...     alpha_moderator=-2e-5,
        ...     Lambda=1e-3,  # 1 ms
        ...     fuel_heat_capacity=1e6,  # J/K
        ...     moderator_heat_capacity=5e6  # J/K
        ... )
    """

    # Delayed neutron data (6 groups)
    beta: np.ndarray  # Delayed neutron fractions
    lambda_d: np.ndarray  # Decay constants [1/s]

    # Reactivity feedback
    alpha_fuel: float  # Fuel temperature coefficient [dk/k/K]
    alpha_moderator: float  # Moderator temperature coefficient

    # Neutron lifetime
    Lambda: float  # Prompt neutron lifetime [s]

    # Power-temperature coupling
    fuel_heat_capacity: float  # J/K
    moderator_heat_capacity: float  # J/K

    @property
    def beta_total(self) -> float:
        """
        Total delayed neutron fraction.
        
        Returns:
            Sum of all delayed neutron fractions (dimensionless).
            Typical values: 0.006-0.007 for thermal reactors.
        """
        return np.sum(self.beta)


class PointKineticsSolver:
    """
    Fast point kinetics solver with temperature feedback.
    
    Solves the point kinetics equations coupled with fuel and moderator
    temperature evolution. Suitable for HTGR transient analysis including
    LOFC, ATWS, and other design basis accidents. Uses scipy's BDF method
    for robust solution of the stiff ODE system.
    
    The solver integrates:
        - Point kinetics equations (power and delayed neutron precursors)
        - Fuel temperature evolution (energy balance)
        - Moderator temperature evolution (energy balance)
        - Temperature feedback reactivity (fuel + moderator coefficients)
    
    Attributes:
        params: PointKineticsParameters instance containing physical constants.
        n_groups: Number of delayed neutron precursor groups.
    
    Example:
        >>> params = PointKineticsParameters(...)
        >>> solver = PointKineticsSolver(params)
        >>> def rho_ext(t):
        ...     return -0.05 if t > 10.0 else 0.0  # Scram at t=10s
        >>> def Q_removal(t, T_fuel, T_mod):
        ...     return 0.9 * initial_power if t < 10.0 else 0.0
        >>> result = solver.solve_transient(
        ...     rho_external=rho_ext,
        ...     power_removal=Q_removal,
        ...     initial_state={'power': 10e6, 'T_fuel': 1200.0, 'T_mod': 900.0},
        ...     t_span=(0.0, 3600.0)
        ... )
    """

    def __init__(self, params: PointKineticsParameters):
        """
        Initialize point kinetics solver.
        
        Args:
            params: PointKineticsParameters instance with delayed neutron
                data, reactivity coefficients, and heat capacities.
        """
        self.params = params
        self.n_groups = len(params.beta)

    def solve_transient(
        self,
        rho_external: Callable[[float], float],
        power_removal: Callable[[float, float, float], float],
        initial_state: Dict,
        t_span: Tuple[float, float],
        max_step: float = 0.1,
    ) -> Dict:
        """
        Solve point kinetics equations with temperature feedback.
        
        Integrates the coupled system of ODEs for power, delayed neutron
        precursors, fuel temperature, and moderator temperature. Includes
        temperature feedback reactivity and external reactivity insertion.
        
        Args:
            rho_external: Callable function rho(t) returning external reactivity
                in dk/k units. Can model scram, control rod insertion, etc.
            power_removal: Callable function Q(t, T_fuel, T_mod) returning heat
                removal rate in Watts. Models forced cooling, natural convection, etc.
            initial_state: Dictionary with keys:
                - "power": Initial power in Watts.
                - "T_fuel": Initial fuel temperature in Kelvin.
                - "T_mod": Initial moderator temperature in Kelvin.
                - "C_i": Optional 1D array of initial precursor concentrations.
                    If not provided, calculated from steady-state assumption.
            t_span: Tuple (t_start, t_end) in seconds.
            max_step: Maximum time step for ODE solver in seconds (default: 0.1).
        
        Returns:
            Dictionary with keys:
                - "t": 1D array of time points in seconds.
                - "power": 1D array of power values in Watts.
                - "T_fuel": 1D array of fuel temperatures in Kelvin.
                - "T_moderator": 1D array of moderator temperatures in Kelvin.
                - "rho_external": 1D array of external reactivity values.
        
        Note:
            Uses scipy.integrate.solve_ivp with BDF method for stiff systems.
            Solver tolerances: rtol=1e-6, atol=1e-8.
        """
        # Initial state vector
        P0 = initial_state["power"]
        T_fuel0 = initial_state["T_fuel"]
        T_mod0 = initial_state["T_mod"]
        C0 = initial_state.get("C_i", np.zeros(self.n_groups))

        # Normalize precursor concentrations if not provided
        if np.sum(C0) == 0:
            C0 = self.params.beta / self.params.lambda_d * P0 / self.params.Lambda

        # State: [P, T_fuel, T_mod, C_1, ..., C_6]
        y0 = np.concatenate([[P0, T_fuel0, T_mod0], C0])

        def derivatives(t, y):
            """System of ODEs."""
            P = y[0]
            T_fuel = y[1]
            T_mod = y[2]
            C = y[3 : 3 + self.n_groups]

            # External reactivity
            rho_ext = rho_external(t)

            # Temperature feedback
            rho_fuel = self.params.alpha_fuel * (T_fuel - T_fuel0)
            rho_mod = self.params.alpha_moderator * (T_mod - T_mod0)
            rho_total = rho_ext + rho_fuel + rho_mod

            # Point kinetics equations
            dP_dt = (
                rho_total - self.params.beta_total
            ) / self.params.Lambda * P + np.sum(self.params.lambda_d * C)

            dC_dt = self.params.beta / self.params.Lambda * P - self.params.lambda_d * C

            # Energy balance
            Q_removal = power_removal(t, T_fuel, T_mod)

            # Heat transfer from fuel to moderator (simplified)
            h_fuel_mod = 1e5  # W/K (effective conductance)
            Q_fuel_to_mod = h_fuel_mod * (T_fuel - T_mod)

            dT_fuel_dt = (P - Q_fuel_to_mod) / self.params.fuel_heat_capacity
            dT_mod_dt = (
                Q_fuel_to_mod - Q_removal
            ) / self.params.moderator_heat_capacity

            return np.concatenate([[dP_dt, dT_fuel_dt, dT_mod_dt], dC_dt])

        # Solve stiff ODE system
        sol = solve_ivp(
            derivatives,
            t_span,
            y0,
            method="BDF",  # Backward differentiation (good for stiff)
            max_step=max_step,
            dense_output=True,
            rtol=1e-6,
            atol=1e-8,
        )

        # Extract solution
        t = sol.t
        P = sol.y[0, :]
        T_fuel = sol.y[1, :]
        T_mod = sol.y[2, :]

        # Compute reactivity history
        rho_history = np.array([rho_external(ti) for ti in t])

        return {
            "t": t,
            "power": P,
            "T_fuel": T_fuel,
            "T_moderator": T_mod,
            "rho_external": rho_history,
        }


class LOFCTransient:
    """
    Loss of Forced Cooling (LOFC) transient analysis.
    
    Implements analysis for the Loss of Forced Cooling accident, which is a
    critical design basis accident for HTGRs. In LOFC, the primary coolant
    circulation is lost (e.g., pump failure, power loss), but the reactor
    remains pressurized and can rely on passive heat removal mechanisms.
    
    Sequence of Events:
        1. Normal operation
        2. Loss of forced cooling (t=0)
        3. Reactor scram (if available, after scram_delay)
        4. Decay heat removal via passive cooling (natural convection, radiation)
        5. Temperature peak (typically 30 minutes to several hours)
        6. Long-term cooldown
    
    HTGRs are inherently safe during LOFC due to:
        - Negative temperature reactivity coefficients
        - High thermal inertia
        - Passive heat removal capability
    
    Attributes:
        spec: Reactor specification object.
        geometry: Core geometry object.
        console: Rich console for progress output.
    
    Example:
        >>> from smrforge.presets.htgr import get_htgr_spec
        >>> spec = get_htgr_spec("micro-htgr-1")
        >>> geometry = ...  # Core geometry
        >>> lofc = LOFCTransient(spec, geometry)
        >>> conditions = TransientConditions(
        ...     initial_power=1e6,  # 1 MWth
        ...     initial_temperature=1200.0,
        ...     initial_flow_rate=1.0,
        ...     initial_pressure=7.0e6,
        ...     transient_type=TransientType.LOFC,
        ...     trigger_time=0.0,
        ...     scram_available=True
        ... )
        >>> result = lofc.simulate(conditions)
    """

    def __init__(self, reactor_spec, core_geometry):
        """
        Initialize LOFC transient analyzer.
        
        Args:
            reactor_spec: Reactor specification object containing power,
                geometry parameters, and material properties.
            core_geometry: Core geometry object for spatial calculations.
        """
        self.spec = reactor_spec
        self.geometry = core_geometry
        self.console = Console()

    def simulate(self, conditions: TransientConditions) -> Dict:
        """
        Simulate LOFC transient.

        Sequence:
        1. Normal operation
        2. Loss of forced cooling (t=0)
        3. Reactor scram (if available)
        4. Decay heat removal via passive cooling
        5. Temperature peak
        6. Long-term cooldown
        """
        self.console.print(f"[bold cyan]Simulating LOFC Transient[/bold cyan]")
        self.console.print(f"Initial power: {conditions.initial_power/1e6:.1f} MWth")
        self.console.print(f"Scram available: {conditions.scram_available}")

        # Setup point kinetics
        params = self._get_kinetics_parameters()
        kinetics = PointKineticsSolver(params)

        # Define external reactivity (scram if available)
        def rho_external(t):
            if conditions.scram_available and t > conditions.scram_delay:
                # Scram: large negative reactivity insertion
                rod_worth = -0.15  # -15% dk/k
                insertion_time = 2.0  # 2 seconds to fully insert

                if t < conditions.scram_delay + insertion_time:
                    # Linear insertion
                    fraction = (t - conditions.scram_delay) / insertion_time
                    return rod_worth * fraction
                else:
                    return rod_worth
            else:
                return 0.0

        # Define heat removal (transitions from forced to passive)
        def power_removal(t, T_fuel, T_mod):
            if t < conditions.trigger_time:
                # Normal forced convection
                Q_forced = self._forced_convection_removal(
                    conditions.initial_flow_rate, T_mod
                )
                return Q_forced
            else:
                # Passive cooling only (RCCS + conduction)
                Q_passive = self._passive_cooling(
                    T_fuel, T_mod, conditions.ambient_temperature
                )
                return Q_passive

        # Initial state
        initial = {
            "power": conditions.initial_power,
            "T_fuel": conditions.initial_temperature + 100,  # Fuel hotter than average
            "T_mod": conditions.initial_temperature,
        }

        # Solve
        with Progress() as progress:
            task = progress.add_task("Running transient simulation...", total=100)

            result = kinetics.solve_transient(
                rho_external,
                power_removal,
                initial,
                (conditions.t_start, conditions.t_end),
                max_step=10.0,  # 10 second steps
            )

            progress.update(task, completed=100)

        # Find peak temperature
        idx_peak = np.argmax(result["T_fuel"])
        t_peak = result["t"][idx_peak]
        T_peak = result["T_fuel"][idx_peak]

        self.console.print(f"\n[bold]Results:[/bold]")
        self.console.print(
            f"  Peak fuel temperature: {T_peak:.1f} K ({T_peak-273:.1f}°C)"
        )
        self.console.print(f"  Time to peak: {t_peak/3600:.2f} hours")
        self.console.print(f"  Final temperature: {result['T_fuel'][-1]:.1f} K")

        # Safety assessment
        margin = self.spec.max_fuel_temperature - T_peak

        if margin > 0:
            self.console.print(
                f"  [green]✓ Within design limits (margin: {margin:.0f} K)[/green]"
            )
        else:
            self.console.print(
                f"  [red]✗ Exceeds design limit by {-margin:.0f} K[/red]"
            )

        return result

    def _get_kinetics_parameters(self) -> PointKineticsParameters:
        """Get point kinetics parameters for HTGR."""
        # U-235 dominated spectrum (adjusted for HTGR)
        return PointKineticsParameters(
            beta=np.array([2.13e-4, 1.43e-3, 1.27e-3, 2.56e-3, 7.48e-4, 2.73e-4]),
            lambda_d=np.array([0.0124, 0.0305, 0.111, 0.301, 1.14, 3.01]),
            alpha_fuel=-3.5e-5,  # Strong negative Doppler
            alpha_moderator=-1.0e-5,  # Graphite temperature coefficient
            Lambda=5e-4,  # 0.5 ms prompt neutron lifetime
            fuel_heat_capacity=1e8,  # J/K (approximate for core fuel)
            moderator_heat_capacity=5e8,  # J/K (graphite moderator)
        )

    def _forced_convection_removal(self, mdot: float, T_coolant: float) -> float:
        """Heat removal by forced helium circulation."""
        if mdot < 0.01:  # Flow stopped
            return 0.0

        # Simplified: Q = mdot * cp * deltaT
        cp_he = 5195.0  # J/kg-K
        T_inlet = 573.0  # K
        delta_T = T_coolant - T_inlet

        return mdot * cp_he * delta_T

    def _passive_cooling(self, T_fuel: float, T_mod: float, T_ambient: float) -> float:
        """
        Passive heat removal via RCCS and natural circulation.

        Mechanisms:
        1. Radiation from vessel to RCCS
        2. Natural circulation in air gaps
        3. Conduction through structures
        """
        # Radiation (simplified Stefan-Boltzmann)
        epsilon = 0.8  # Emissivity
        sigma = 5.67e-8  # W/m²-K⁴
        A_vessel = (
            2
            * np.pi
            * (self.geometry.core_diameter / 2 / 100 + 0.5)
            * (self.geometry.core_height / 100)
        )  # m²

        Q_rad = epsilon * sigma * A_vessel * (T_mod**4 - T_ambient**4)

        # Natural circulation contribution (simplified)
        h_nat = 10.0  # W/m²-K (effective heat transfer coefficient)
        Q_nat = h_nat * A_vessel * (T_mod - T_ambient)

        return Q_rad + Q_nat


class ATWSTransient:
    """
    Anticipated Transient Without Scram (ATWS).
    Loss of heat sink without reactor trip.
    """

    def __init__(self, reactor_spec, core_geometry):
        self.spec = reactor_spec
        self.geometry = core_geometry
        self.console = Console()

    def simulate(self, conditions: TransientConditions) -> Dict:
        """
        Simulate ATWS scenario.

        Sequence:
        1. Normal operation
        2. Loss of heat sink (e.g., turbine trip)
        3. Temperature rise → negative feedback
        4. Self-limiting power excursion
        5. Stabilization via inherent safety
        """
        self.console.print(f"[bold yellow]Simulating ATWS Transient[/bold yellow]")
        self.console.print(
            f"[yellow]⚠ Scram assumed FAILED - relying on inherent safety[/yellow]"
        )

        params = self._get_kinetics_parameters()
        kinetics = PointKineticsSolver(params)

        # No scram - reactivity is zero
        def rho_external(t):
            return 0.0

        # Heat sink lost at trigger time
        def power_removal(t, T_fuel, T_mod):
            if t < conditions.trigger_time:
                # Normal heat removal
                return conditions.initial_power
            else:
                # Minimal removal (only passive)
                T_ambient = conditions.ambient_temperature
                Q_passive = self._passive_cooling(T_fuel, T_mod, T_ambient)
                return Q_passive

        initial = {
            "power": conditions.initial_power,
            "T_fuel": conditions.initial_temperature + 100,
            "T_mod": conditions.initial_temperature,
        }

        result = kinetics.solve_transient(
            rho_external,
            power_removal,
            initial,
            (conditions.t_start, min(conditions.t_end, 3600)),  # 1 hour sufficient
            max_step=1.0,
        )

        # Analyze self-shutdown
        idx_peak_power = np.argmax(result["power"])
        P_peak = result["power"][idx_peak_power]
        t_peak_power = result["t"][idx_peak_power]

        T_peak = np.max(result["T_fuel"])

        self.console.print(f"\n[bold]Results:[/bold]")
        self.console.print(
            f"  Peak power: {P_peak/conditions.initial_power:.2f}× initial"
        )
        self.console.print(f"  Time to peak power: {t_peak_power:.1f} s")
        self.console.print(
            f"  Peak fuel temperature: {T_peak:.1f} K ({T_peak-273:.1f}°C)"
        )

        # Check if self-limiting
        final_power_fraction = result["power"][-1] / conditions.initial_power

        if final_power_fraction < 0.1 and T_peak < self.spec.max_fuel_temperature:
            self.console.print(
                f"  [green]✓ Inherent safety successful - reactor self-stabilized[/green]"
            )
        else:
            self.console.print(f"  [red]✗ Temperature or power remains elevated[/red]")

        return result

    def _get_kinetics_parameters(self) -> PointKineticsParameters:
        """HTGR parameters with strong negative feedback."""
        return PointKineticsParameters(
            beta=np.array([2.13e-4, 1.43e-3, 1.27e-3, 2.56e-3, 7.48e-4, 2.73e-4]),
            lambda_d=np.array([0.0124, 0.0305, 0.111, 0.301, 1.14, 3.01]),
            alpha_fuel=-4.0e-5,  # Very strong Doppler (key for ATWS survival)
            alpha_moderator=-1.2e-5,
            Lambda=5e-4,
            fuel_heat_capacity=1e8,
            moderator_heat_capacity=5e8,
        )

    def _passive_cooling(self, T_fuel: float, T_mod: float, T_ambient: float) -> float:
        """Passive heat removal."""
        epsilon = 0.8
        sigma = 5.67e-8
        A = 100.0  # m² (approximate)
        return epsilon * sigma * A * (T_mod**4 - T_ambient**4)


class ReactivityInsertionAccident:
    """
    Reactivity Insertion Accident (RIA).
    Rapid positive reactivity insertion (e.g., control rod ejection).
    """

    def __init__(self, reactor_spec):
        self.spec = reactor_spec
        self.console = Console()

    def simulate(
        self,
        rho_inserted: float,
        insertion_time: float,
        conditions: TransientConditions,
    ) -> Dict:
        """
        Simulate RIA.

        Args:
            rho_inserted: Reactivity inserted [dk/k]
            insertion_time: Duration of insertion [s]
        """
        self.console.print(
            f"[bold red]Simulating Reactivity Insertion Accident[/bold red]"
        )
        self.console.print(f"Reactivity inserted: {rho_inserted*1e5:.0f} pcm")
        self.console.print(f"Insertion time: {insertion_time:.2f} s")

        params = self._get_kinetics_parameters()
        kinetics = PointKineticsSolver(params)

        # Reactivity insertion followed by scram
        def rho_external(t):
            if t < insertion_time:
                # Ramp insertion
                return rho_inserted * (t / insertion_time)
            elif (
                conditions.scram_available
                and t > insertion_time + conditions.scram_delay
            ):
                # Scram after delay
                scram_time = 2.0
                if t < insertion_time + conditions.scram_delay + scram_time:
                    fraction = (
                        t - insertion_time - conditions.scram_delay
                    ) / scram_time
                    return rho_inserted - 0.20 * fraction  # -20% dk/k scram
                else:
                    return rho_inserted - 0.20
            else:
                return rho_inserted

        # Normal heat removal (can't respond instantly)
        def power_removal(t, T_fuel, T_mod):
            # Heat removal lags behind power (thermal inertia)
            if t < 1.0:
                return conditions.initial_power
            else:
                # Simplified: removal proportional to moderator temp
                return 1e5 * (T_mod - 300)

        initial = {
            "power": conditions.initial_power,
            "T_fuel": conditions.initial_temperature + 100,
            "T_mod": conditions.initial_temperature,
        }

        result = kinetics.solve_transient(
            rho_external,
            power_removal,
            initial,
            (0, 60),  # 1 minute sufficient for prompt excursion
            max_step=0.01,  # Small steps for fast transient
        )

        # Find prompt power peak
        idx_peak = np.argmax(result["power"])
        P_peak = result["power"][idx_peak]
        t_peak = result["t"][idx_peak]

        self.console.print(f"\n[bold]Results:[/bold]")
        self.console.print(
            f"  Peak power: {P_peak/conditions.initial_power:.1f}× initial"
        )
        self.console.print(f"  Time to peak: {t_peak:.3f} s")
        self.console.print(f"  Peak fuel temp: {np.max(result['T_fuel']):.1f} K")

        # Energy deposition (integrated power)
        energy = np.trapz(result["power"], result["t"])
        self.console.print(f"  Energy deposited: {energy/1e6:.1f} MJ")

        return result

    def _get_kinetics_parameters(self) -> PointKineticsParameters:
        """Parameters for RIA."""
        return PointKineticsParameters(
            beta=np.array([2.13e-4, 1.43e-3, 1.27e-3, 2.56e-3, 7.48e-4, 2.73e-4]),
            lambda_d=np.array([0.0124, 0.0305, 0.111, 0.301, 1.14, 3.01]),
            alpha_fuel=-3.5e-5,
            alpha_moderator=-1.0e-5,
            Lambda=5e-4,
            fuel_heat_capacity=5e7,  # Smaller for faster response
            moderator_heat_capacity=3e8,
        )


class AirWaterIngressAnalysis:
    """
    Air/water ingress analysis for HTGRs.
    Critical for depressurization accidents.
    """

    def __init__(self, reactor_spec, core_geometry):
        self.spec = reactor_spec
        self.geometry = core_geometry
        self.console = Console()

    def simulate_air_ingress(
        self, break_size: float, conditions: TransientConditions
    ) -> Dict:
        """
        Simulate air ingress following depressurization.

        Air ingress causes:
        1. Graphite oxidation (C + O2 → CO2)
        2. Heat generation
        3. Structural damage

        Args:
            break_size: Break area [cm²]
        """
        self.console.print(f"[bold magenta]Simulating Air Ingress[/bold magenta]")
        self.console.print(f"Break size: {break_size:.1f} cm²")

        # Depressurization rate
        V_vessel = (
            np.pi * (self.geometry.core_diameter / 2) ** 2 * self.geometry.core_height
        )  # cm³

        # Simple blowdown model
        def pressure_vs_time(t):
            """Pressure decay during blowdown."""
            P0 = conditions.initial_pressure
            tau = V_vessel / (break_size * 100)  # Time constant
            return P0 * np.exp(-t / tau) + conditions.atmospheric_pressure

        # Air ingress rate (after depressurization)
        t_depressurized = 600  # 10 minutes to depressurize

        def air_mass_flow(t):
            """Air entering vessel [kg/s]."""
            if t < t_depressurized:
                return 0.0
            else:
                # Molecular diffusion of air into helium
                D_eff = 1e-4  # m²/s effective diffusion
                A_break = break_size * 1e-4  # m²
                rho_air = 1.2  # kg/m³
                return D_eff * A_break * rho_air

        # Oxidation rate
        def graphite_oxidation_rate(T, O2_concentration):
            """
            Graphite oxidation: C + O2 → CO2 + heat
            Arrhenius kinetics.
            """
            A = 1e8  # Pre-exponential factor
            Ea = 180e3  # Activation energy [J/mol]
            R = 8.314

            rate = A * O2_concentration * np.exp(-Ea / (R * T))
            return rate  # kg_C/s

        # Simulate
        t_max = 72 * 3600  # 72 hours
        t = np.linspace(0, t_max, 1000)

        T_graphite = np.full_like(t, conditions.initial_temperature)
        mass_oxidized = np.zeros_like(t)

        for i in range(1, len(t)):
            dt = t[i] - t[i - 1]

            # Air mass accumulated
            m_air = air_mass_flow(t[i]) * dt
            O2_fraction = 0.21
            m_O2 = m_air * O2_fraction

            # Oxidation
            graphite_mass = 1.74 * V_vessel * 1e-6  # kg (assuming all graphite)
            O2_conc = m_O2 / (V_vessel * 1e-6)  # kg/m³

            dm_oxidized = graphite_oxidation_rate(T_graphite[i - 1], O2_conc) * dt
            mass_oxidized[i] = mass_oxidized[i - 1] + dm_oxidized

            # Heat generation from oxidation
            Q_oxidation = dm_oxidized * 32.8e6  # J (heat of combustion)

            # Temperature rise (simplified)
            cp_graphite = 1700  # J/kg-K
            dT = Q_oxidation / (graphite_mass * cp_graphite)
            T_graphite[i] = T_graphite[i - 1] + dT

        # Results
        total_oxidized = mass_oxidized[-1]
        oxidized_fraction = total_oxidized / (1.74 * V_vessel * 1e-6)

        self.console.print(f"\n[bold]Results (72 hours):[/bold]")
        self.console.print(f"  Graphite oxidized: {total_oxidized:.1f} kg")
        self.console.print(f"  Fraction oxidized: {oxidized_fraction*100:.2f}%")
        self.console.print(f"  Peak temperature: {np.max(T_graphite):.1f} K")

        if oxidized_fraction < 0.05:
            self.console.print(
                f"  [green]✓ Minimal oxidation - structure maintained[/green]"
            )
        else:
            self.console.print(
                f"  [red]✗ Significant oxidation - structural concern[/red]"
            )

        return {
            "t": t,
            "T_graphite": T_graphite,
            "mass_oxidized": mass_oxidized,
            "pressure": np.array([pressure_vs_time(ti) for ti in t]),
        }


@njit(cache=True)
def decay_heat_ans_standard(t: np.ndarray, P0: float, t_operate: float) -> np.ndarray:
    """
    ANS 5.1 standard decay heat curve.
    Fast Numba implementation.

    Args:
        t: Time after shutdown [s]
        P0: Operating power [W]
        t_operate: Operating time before shutdown [s]

    Returns:
        Decay power [W]
    """
    n = len(t)
    P_decay = np.zeros(n)

    for i in range(n):
        if t[i] < 1.0:
            # Avoid singularity
            P_decay[i] = 0.066 * P0
        else:
            # Simplified ANS formula
            tau = min(t[i], t_operate)
            P_decay[i] = 0.066 * P0 * (t[i] ** (-0.2) - (t[i] + tau) ** (-0.2))

    return P_decay


if __name__ == "__main__":
    from smrforge.presets.htgr_designs import ValarAtomicsReactor

    console = Console()
    console.print("[bold cyan]HTGR Transient Analysis Demo[/bold cyan]\n")

    # Setup
    reactor = ValarAtomicsReactor()
    core = reactor.build_core()

    # Common conditions
    base_conditions = TransientConditions(
        initial_power=10e6,
        initial_temperature=1100.0,
        initial_flow_rate=8.0,
        initial_pressure=7.0e6,
        transient_type=TransientType.LOFC,
        trigger_time=0.0,
        t_end=72 * 3600,
    )

    # Test 1: LOFC with scram
    console.print("[bold]Test 1: Loss of Forced Cooling (LOFC)[/bold]")
    lofc = LOFCTransient(reactor.spec, core)
    result_lofc = lofc.simulate(base_conditions)

    # Test 2: ATWS
    console.print("\n[bold]Test 2: ATWS (Without Scram)[/bold]")
    atws_conditions = TransientConditions(
        initial_power=10e6,
        initial_temperature=1100.0,
        initial_flow_rate=8.0,
        initial_pressure=7.0e6,
        transient_type=TransientType.ATWS,
        trigger_time=0.0,
        scram_available=False,
        t_end=3600,
    )
    atws = ATWSTransient(reactor.spec, core)
    result
