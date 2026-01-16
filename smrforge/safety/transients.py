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

from ..utils.logging import get_logger

# Get logger for this module
logger = get_logger("smrforge.safety.transients")


class TransientType(Enum):
    """
    Types of transient scenarios for HTGR and LWR SMR safety analysis.
    
    Enum values identify different accident scenarios and operational transients
    that may occur in HTGRs and LWR SMRs. Each transient type requires different
    modeling approaches and has different safety implications.
    
    Attributes:
        LOFC: Loss of Forced Cooling - design basis accident, loss of primary
            coolant circulation (HTGR).
        ATWS: Anticipated Transient Without Scram - failure to scram during
            a transient event.
        RIA: Reactivity Insertion Accident - uncontrolled reactivity addition.
        LOCA: Loss of Coolant Accident - breach in primary pressure boundary (HTGR).
        AIR_INGRESS: Air ingress accident - air enters the primary circuit (HTGR).
        WATER_INGRESS: Water ingress accident - water enters the primary circuit (HTGR).
        LOAD_FOLLOWING: Normal operational transient for load following.
        # PWR SMR-specific transients
        STEAM_LINE_BREAK: Steam line break - rupture in main steam line (PWR SMR).
        MSIV_CLOSURE: Main steam isolation valve closure - rapid steam line isolation (PWR SMR).
        FEEDWATER_LINE_BREAK: Feedwater line break - rupture in feedwater line (PWR SMR).
        PRESSURIZER_TRANSIENT: Pressurizer pressure/temperature transient (PWR SMR).
        SB_LOCA: Small break LOCA - small break in primary system (PWR SMR).
        LB_LOCA: Large break LOCA - large break in primary system (PWR SMR).
        # BWR SMR-specific transients
        STEAM_SEPARATOR_ISSUE: Steam separator malfunction (BWR SMR).
        RECIRCULATION_PUMP_TRIP: Recirculation pump trip - loss of forced circulation (BWR SMR).
        MAIN_STEAM_LINE_ISOLATION: Main steam line isolation (BWR SMR).
        FEEDWATER_PUMP_TRIP: Feedwater pump trip (BWR SMR).
        BWR_LOCA: BWR-specific LOCA scenario (BWR SMR).
        # Integral SMR transients
        STEAM_GENERATOR_TUBE_RUPTURE: In-vessel steam generator tube rupture (Integral SMR).
        INTEGRAL_PRIMARY_TRANSIENT: Integrated primary system transient (Integral SMR).
    """

    LOFC = "loss_of_forced_cooling"
    ATWS = "anticipated_transient_without_scram"
    RIA = "reactivity_insertion_accident"
    LOCA = "loss_of_coolant_accident"
    AIR_INGRESS = "air_ingress"
    WATER_INGRESS = "water_ingress"
    LOAD_FOLLOWING = "load_following"
    # PWR SMR-specific
    STEAM_LINE_BREAK = "steam_line_break"
    MSIV_CLOSURE = "msiv_closure"
    FEEDWATER_LINE_BREAK = "feedwater_line_break"
    PRESSURIZER_TRANSIENT = "pressurizer_transient"
    SB_LOCA = "small_break_loca"
    LB_LOCA = "large_break_loca"
    # BWR SMR-specific
    STEAM_SEPARATOR_ISSUE = "steam_separator_issue"
    RECIRCULATION_PUMP_TRIP = "recirculation_pump_trip"
    MAIN_STEAM_LINE_ISOLATION = "main_steam_line_isolation"
    FEEDWATER_PUMP_TRIP = "feedwater_pump_trip"
    BWR_LOCA = "bwr_loca"
    # Integral SMR
    STEAM_GENERATOR_TUBE_RUPTURE = "steam_generator_tube_rupture"
    INTEGRAL_PRIMARY_TRANSIENT = "integral_primary_transient"


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
    Point kinetics solver with temperature feedback.

    Solves the point kinetics equations for reactor transients with temperature-dependent
    reactivity feedback. This is a zero-dimensional model that represents the entire
    reactor core as a single point, suitable for analysis of global transients where
    spatial effects are less important than temporal behavior.

    Examples:
        Basic usage with constant reactivity::

            from smrforge.safety.transients import PointKineticsParameters, PointKineticsSolver
            import numpy as np

            # Define parameters (6-group delayed neutrons for HTGR)
            beta = np.array([0.00021, 0.00141, 0.00127, 0.00255, 0.00074, 0.00027])
            lambda_d = np.array([0.0127, 0.0317, 0.115, 0.311, 1.40, 3.87])

            params = PointKineticsParameters(
                beta=beta,
                lambda_d=lambda_d,
                alpha_fuel=-5e-5,  # Negative = stable
                alpha_moderator=-2e-5,
                Lambda=1e-4,  # Prompt lifetime (s)
                fuel_heat_capacity=1e6,  # J/K
                moderator_heat_capacity=5e5,  # J/K
            )

            solver = PointKineticsSolver(params)

            # Constant reactivity step
            rho = lambda t: 0.001 if t > 0 else 0.0  # 1 m$ reactivity insertion
            power_removal = lambda t, T_fuel, T_mod: 1e6  # Constant power removal

            initial_state = {
                "power": 1e6,  # W
                "precursors": np.array([1e20, 1e20, 1e20, 1e20, 1e20, 1e20]),
                "T_fuel": 1200.0,  # K
                "T_moderator": 800.0,  # K
            }

            result = solver.solve_transient(
                rho_external=rho,
                power_removal=power_removal,
                initial_state=initial_state,
                t_span=(0.0, 100.0),
                max_step=0.1,
            )

            print(f"Final power: {result['power'][-1]/1e6:.2f} MW")

        With temperature feedback::

            # Temperature-dependent reactivity
            def reactivity_with_feedback(t):
                if t < 0:
                    return 0.0
                # Initial reactivity insertion
                rho_0 = 0.002  # 2 m$
                # Feedback reduces reactivity as temperature rises
                return rho_0 * np.exp(-0.01 * t)  # Decay over time

            result = solver.solve_transient(
                rho_external=reactivity_with_feedback,
                power_removal=lambda t, T_f, T_m: 1e6,
                initial_state=initial_state,
                t_span=(0.0, 100.0),
            )

    Attributes:
        params: PointKineticsParameters object containing all physical parameters

    Note:
        The solver uses scipy's solve_ivp for numerical integration. Temperature
        feedback is computed from power balance equations, and reactivity is updated
        based on temperature changes using the reactivity coefficients in params.
    """
    def __init__(self, params: PointKineticsParameters):
        """
        Initialize point kinetics solver.

        Args:
            params: PointKineticsParameters instance with delayed neutron
                data, reactivity coefficients, and heat capacities. Must contain
                valid delayed neutron parameters, reactivity coefficients, and
                heat capacities.

        Raises:
            ValueError: If params is invalid (wrong type, empty arrays, non-positive
                       values, etc.)

        Example:
            >>> params = PointKineticsParameters(
            ...     beta=np.array([0.00021, 0.00141, ...]),
            ...     lambda_d=np.array([0.0127, 0.0317, ...]),
            ...     alpha_fuel=-5e-5,
            ...     alpha_moderator=-2e-5,
            ...     Lambda=1e-4,
            ...     fuel_heat_capacity=1e6,
            ...     moderator_heat_capacity=5e5,
            ... )
            >>> solver = PointKineticsSolver(params)
        """
        # Validate inputs
        if not isinstance(params, PointKineticsParameters):
            raise ValueError(
                f"params must be PointKineticsParameters, got {type(params)}"
            )

        if len(params.beta) != len(params.lambda_d):
            raise ValueError(
                f"beta and lambda_d must have same length, "
                f"got {len(params.beta)} and {len(params.lambda_d)}"
            )

        if len(params.beta) == 0:
            raise ValueError("params.beta must have at least one group")

        if params.Lambda <= 0:
            raise ValueError(f"params.Lambda must be > 0, got {params.Lambda}")

        if params.fuel_heat_capacity <= 0:
            raise ValueError(
                f"params.fuel_heat_capacity must be > 0, got {params.fuel_heat_capacity}"
            )

        if params.moderator_heat_capacity <= 0:
            raise ValueError(
                f"params.moderator_heat_capacity must be > 0, "
                f"got {params.moderator_heat_capacity}"
            )

        self.params = params
        self.n_groups = len(params.beta)

        logger.debug(
            f"PointKineticsSolver initialized: {self.n_groups} delayed neutron groups, "
            f"Lambda={params.Lambda:.2e} s, beta_total={params.beta_total:.4f}"
        )

    def solve_transient(
        self,
        rho_external: Callable[[float], float],
        power_removal: Callable[[float, float, float], float],
        initial_state: Dict,
        t_span: Tuple[float, float],
        max_step: Optional[float] = None,
        adaptive: bool = True,
        long_term_optimization: bool = False,
    ) -> Dict:
        """
        Solve point kinetics equations with temperature feedback.

        Integrates the coupled system of ODEs for power, delayed neutron
        precursors, fuel temperature, and moderator temperature. Includes
        temperature feedback reactivity and external reactivity insertion.

        Args:
            rho_external: Callable function rho(t) returning external reactivity
                in dk/k units (dimensionless). Can model scram, control rod insertion,
                or any time-dependent reactivity change. Must accept float (time) and
                return float (reactivity).
            power_removal: Callable function Q(t, T_fuel, T_mod) returning heat removal
                rate in Watts. Must accept three float arguments (time, fuel temperature,
                moderator temperature) and return float (power).
            initial_state: Dictionary with keys:
                - "power": Initial reactor power in Watts (float)
                - "T_fuel": Initial fuel temperature in Kelvin (float)
                - "T_moderator": Initial moderator temperature in Kelvin (float)
                - "precursors" (optional): Initial delayed neutron precursor concentrations
                  as numpy array. If not provided, computed from steady-state balance.
            t_span: Tuple (t_start, t_end) defining simulation time span in seconds.
            max_step: Maximum time step for ODE integrator in seconds (default: None for adaptive).
                If None and long_term_optimization is True, uses adaptive stepping based on time scale.
            adaptive: Use adaptive time stepping for efficiency (default: True).
            long_term_optimization: Optimize for long transients (>1 day) with larger time steps
                and decay heat approximations (default: False).

        Returns:
            Dictionary containing time history with keys:
                - "time": Time array [s]
                - "power": Power array [W]
                - "T_fuel": Fuel temperature array [K]
                - "T_moderator": Moderator temperature array [K]
                - "reactivity": Total reactivity array [dk/k]
                - "precursors": Precursor concentrations array [variable units]

        Raises:
            ValueError: If inputs are invalid (non-callable functions, missing keys,
                       non-physical values, etc.)
            RuntimeError: If ODE solver fails to converge or produces invalid results

        Example:
            >>> # Reactivity insertion with scram
            >>> def rho_ext(t):
            ...     if t < 5.0:
            ...         return 0.002  # 2 m$ insertion
            ...     else:
            ...         return -0.05  # Scram insertion
            >>> 
            >>> def Q_removal(t, T_fuel, T_mod):
            ...     return 0.9 * 1e6  # 90% of initial power
            >>> 
            >>> initial_state = {
            ...     "power": 1e6,  # 1 MWth
            ...     "T_fuel": 1200.0,  # K
            ...     "T_moderator": 900.0,  # K
            ... }
            >>> 
            >>> result = solver.solve_transient(
            ...     rho_external=rho_ext,
            ...     power_removal=Q_removal,
            ...     initial_state=initial_state,
            ...     t_span=(0.0, 100.0),
            ...     max_step=0.1,
            ... )
            >>> 
            >>> print(f"Peak power: {np.max(result['power'])/1e6:.2f} MW")
            >>> print(f"Final power: {result['power'][-1]/1e6:.2f} MW")
        """
        # Validate inputs
        if not callable(rho_external):
            raise ValueError(f"rho_external must be callable, got {type(rho_external)}")
        if not callable(power_removal):
            raise ValueError(f"power_removal must be callable, got {type(power_removal)}")

        if not isinstance(initial_state, dict):
            raise ValueError(f"initial_state must be dict, got {type(initial_state)}")

        required_keys = ["power", "T_fuel", "T_mod"]
        for key in required_keys:
            if key not in initial_state:
                raise ValueError(f"initial_state missing required key: {key}")

        P0 = initial_state["power"]
        T_fuel0 = initial_state["T_fuel"]
        T_mod0 = initial_state["T_mod"]

        if P0 <= 0:
            raise ValueError(f"initial_state['power'] must be > 0, got {P0}")
        if T_fuel0 <= 0:
            raise ValueError(f"initial_state['T_fuel'] must be > 0, got {T_fuel0}")
        if T_mod0 <= 0:
            raise ValueError(f"initial_state['T_mod'] must be > 0, got {T_mod0}")

        if len(t_span) != 2:
            raise ValueError(f"t_span must be tuple of length 2, got {len(t_span)}")
        if t_span[1] <= t_span[0]:
            raise ValueError(f"t_span[1] must be > t_span[0], got {t_span}")

        # Set default max_step based on time span and optimization mode
        total_time = t_span[1] - t_span[0]
        if max_step is None:
            if long_term_optimization and total_time > 86400:  # > 1 day
                # For long transients, use adaptive stepping with larger initial step
                max_step = min(3600.0, 0.01 * total_time)  # 1 hour or 1% of span
            else:
                # For short transients, use smaller steps
                max_step = min(0.1, 0.001 * total_time)  # 0.1s or 0.1% of span
        
        if max_step <= 0:
            raise ValueError(f"max_step must be > 0, got {max_step}")

        logger.debug(
            f"Starting transient solution: t_span={t_span}, "
            f"P0={P0/1e6:.2f} MW, T_fuel0={T_fuel0:.1f} K, T_mod0={T_mod0:.1f} K"
        )

        # Initial state vector
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
        # For long transients, use adaptive stepping with relaxed tolerances
        if long_term_optimization and total_time > 86400:  # > 1 day
            # Relaxed tolerances for long transients (decay heat is slowly varying)
            rtol = 1e-5
            atol = 1e-7
            # Use adaptive stepping (dense_output allows interpolation)
            adaptive_stepping = True
        else:
            # Standard tolerances for short transients
            rtol = 1e-6
            atol = 1e-8
            adaptive_stepping = adaptive

        try:
            if adaptive_stepping:
                # Adaptive time stepping (more efficient for long transients)
                sol = solve_ivp(
                    derivatives,
                    t_span,
                    y0,
                    method="BDF",  # Backward differentiation (good for stiff)
                    max_step=max_step,
                    dense_output=True,
                    rtol=rtol,
                    atol=atol,
                )
            else:
                # Fixed time steps (for short, fast transients)
                t_eval = np.arange(t_span[0], t_span[1], max_step)
                if len(t_eval) > 100000:  # Limit number of evaluation points
                    # For very long fixed-step runs, use adaptive instead
                    logger.warning(
                        f"Too many fixed time steps ({len(t_eval)}). "
                        f"Switching to adaptive stepping."
                    )
                    sol = solve_ivp(
                        derivatives,
                        t_span,
                        y0,
                        method="BDF",
                        max_step=max_step,
                        dense_output=True,
                        rtol=rtol,
                        atol=atol,
                    )
                else:
                    sol = solve_ivp(
                        derivatives,
                        t_span,
                        y0,
                        t_eval=t_eval,
                        method="BDF",
                        rtol=rtol,
                        atol=atol,
                    )
        except ValueError as e:
            # Re-raise with more context
            if "max_step" in str(e):
                raise ValueError(f"max_step must be > 0, got {max_step}") from e
            raise RuntimeError(f"ODE solver failed: {e}") from e
        except Exception as e:
            raise RuntimeError(f"ODE solver failed: {e}") from e

        # Validate solution
        if not sol.success:
            raise RuntimeError(
                f"ODE solver did not converge: {sol.message}. "
                f"Try adjusting max_step or t_span."
            )

        if np.any(sol.y < 0):
            logger.warning("Solution contains negative values (may be unphysical)")

        logger.info(
            f"Transient solution complete: {len(sol.t)} time steps, "
            f"final P={sol.y[0, -1]/1e6:.2f} MW, "
            f"final T_fuel={sol.y[1, -1]:.1f} K"
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

        Raises:
            ValueError: If inputs are invalid
        """
        if reactor_spec is None:
            raise ValueError("reactor_spec cannot be None")
        if core_geometry is None:
            raise ValueError("core_geometry cannot be None")

        self.spec = reactor_spec
        self.geometry = core_geometry
        self.console = Console()

        logger.debug("LOFCTransient initialized")

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

        Args:
            conditions: TransientConditions object defining initial state and transient parameters

        Returns:
            Dict with time history of power, temperatures, etc.

        Raises:
            ValueError: If conditions are invalid
        """
        # Validate conditions
        if not isinstance(conditions, TransientConditions):
            raise ValueError(
                f"conditions must be TransientConditions, got {type(conditions)}"
            )

        if conditions.initial_power <= 0:
            raise ValueError(
                f"conditions.initial_power must be > 0, got {conditions.initial_power}"
            )

        if conditions.initial_temperature <= 0:
            raise ValueError(
                f"conditions.initial_temperature must be > 0, "
                f"got {conditions.initial_temperature}"
            )

        logger.info(
            f"Starting LOFC simulation: P0={conditions.initial_power/1e6:.2f} MW, "
            f"T0={conditions.initial_temperature:.1f} K, "
            f"scram_available={conditions.scram_available}"
        )

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
        """
        Initialize ATWS transient analyzer.

        Args:
            reactor_spec: Reactor specification object
            core_geometry: Core geometry object

        Raises:
            ValueError: If inputs are invalid
        """
        if reactor_spec is None:
            raise ValueError("reactor_spec cannot be None")
        if core_geometry is None:
            raise ValueError("core_geometry cannot be None")

        self.spec = reactor_spec
        self.geometry = core_geometry
        self.console = Console()

        logger.debug("ATWSTransient initialized")

    def simulate(self, conditions: TransientConditions) -> Dict:
        """
        Simulate ATWS scenario.

        Sequence:
        1. Normal operation
        2. Loss of heat sink (e.g., turbine trip)
        3. Temperature rise → negative feedback
        4. Self-limiting power excursion
        5. Stabilization via inherent safety

        Args:
            conditions: TransientConditions object

        Returns:
            Dict with time history of power, temperatures, etc.

        Raises:
            ValueError: If conditions are invalid
        """
        # Validate conditions
        if not isinstance(conditions, TransientConditions):
            raise ValueError(
                f"conditions must be TransientConditions, got {type(conditions)}"
            )

        logger.info(
            f"Starting ATWS simulation: P0={conditions.initial_power/1e6:.2f} MW, "
            f"T0={conditions.initial_temperature:.1f} K"
        )

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
# ============================================================================
# LWR SMR-Specific Transient Classes
# ============================================================================


class PWRSMRTransient:
    """
    Base class for PWR SMR transient analysis.
    
    Provides common functionality for PWR SMR-specific transients including
    steam line breaks, feedwater line breaks, pressurizer transients, and LOCA scenarios.
    
    Attributes:
        reactor_spec: Reactor specification object.
        geometry: Core geometry object.
        console: Rich console for progress output.
    """
    
    def __init__(self, reactor_spec, core_geometry):
        """
        Initialize PWR SMR transient analyzer.
        
        Args:
            reactor_spec: Reactor specification object.
            core_geometry: Core geometry object.
        
        Raises:
            ValueError: If inputs are invalid.
        """
        if reactor_spec is None:
            raise ValueError("reactor_spec cannot be None")
        if core_geometry is None:
            raise ValueError("core_geometry cannot be None")
        
        self.spec = reactor_spec
        self.geometry = core_geometry
        self.console = Console()
        
        logger.debug("PWRSMRTransient initialized")
    
    def _calculate_steam_flow_loss(self, break_area: float, pressure: float, temperature: float) -> float:
        """
        Calculate steam flow rate through break.
        
        Uses critical flow model for choked flow conditions.
        
        Args:
            break_area: Break area [m²]
            pressure: Steam pressure [Pa]
            temperature: Steam temperature [K]
        
        Returns:
            Steam mass flow rate [kg/s]
        """
        # Simplified critical flow model
        R = 461.5  # J/(kg·K) for steam
        gamma = 1.3  # Specific heat ratio for steam
        
        # Critical pressure ratio
        P_crit_ratio = (2 / (gamma + 1)) ** (gamma / (gamma - 1))
        P_crit = pressure * P_crit_ratio
        
        # Critical velocity
        v_crit = np.sqrt(gamma * R * temperature * (2 / (gamma + 1)))
        
        # Critical density
        rho_crit = P_crit / (R * temperature)
        
        # Mass flow rate
        m_dot = break_area * rho_crit * v_crit
        
        return m_dot


class SteamLineBreakTransient(PWRSMRTransient):
    """
    Steam line break (SLB) transient for PWR SMRs.
    
    Models the response to a rupture in the main steam line, which causes:
    1. Rapid depressurization of secondary system
    2. Increased heat removal from primary system
    3. Reactor power reduction due to negative reactivity feedback
    4. Potential pressurizer level changes
    
    Attributes:
        spec: Reactor specification object.
        geometry: Core geometry object.
        console: Rich console for progress output.
    
    Example:
        >>> from smrforge.geometry.lwr_smr import PWRSMRCore
        >>> core = PWRSMRCore(...)
        >>> slb = SteamLineBreakTransient(reactor_spec, core)
        >>> conditions = TransientConditions(
        ...     initial_power=77e6,  # 77 MWe NuScale
        ...     initial_temperature=600.0,
        ...     initial_flow_rate=100.0,
        ...     initial_pressure=15.5e6,  # 15.5 MPa
        ...     transient_type=TransientType.STEAM_LINE_BREAK,
        ...     trigger_time=0.0
        ... )
        >>> result = slb.simulate(conditions, break_area=0.01)  # 0.01 m² break
    """
    
    def simulate(
        self,
        conditions: TransientConditions,
        break_area: float = 0.01,  # m²
        break_location: str = "main_steam_line",
    ) -> Dict:
        """
        Simulate steam line break transient.
        
        Args:
            conditions: TransientConditions object.
            break_area: Break area [m²] (default: 0.01 m²).
            break_location: Break location ("main_steam_line", "steam_generator_outlet").
        
        Returns:
            Dictionary with time history of power, pressure, temperature, etc.
        
        Raises:
            ValueError: If conditions are invalid.
        """
        if not isinstance(conditions, TransientConditions):
            raise ValueError(f"conditions must be TransientConditions, got {type(conditions)}")
        
        if break_area <= 0:
            raise ValueError(f"break_area must be > 0, got {break_area}")
        
        logger.info(
            f"Starting SLB simulation: P0={conditions.initial_power/1e6:.2f} MW, "
            f"break_area={break_area:.4f} m²"
        )
        
        self.console.print(f"[bold cyan]Simulating Steam Line Break[/bold cyan]")
        
        # Time array
        t = np.linspace(conditions.t_start, conditions.t_end, 1000)
        dt = t[1] - t[0]
        
        # Initialize arrays
        power = np.zeros_like(t)
        pressure = np.zeros_like(t)
        temperature = np.zeros_like(t)
        steam_flow = np.zeros_like(t)
        
        # Initial conditions
        power[0] = conditions.initial_power
        pressure[0] = conditions.initial_pressure
        temperature[0] = conditions.initial_temperature
        
        # Simulate transient
        for i in range(1, len(t)):
            # Calculate steam flow loss
            if t[i] >= conditions.trigger_time:
                steam_flow[i] = self._calculate_steam_flow_loss(
                    break_area, pressure[i-1], temperature[i-1]
                )
            else:
                steam_flow[i] = 0.0
            
            # Heat removal increases due to increased steam flow
            # Simplified model: power reduction proportional to steam flow
            if t[i] >= conditions.trigger_time:
                heat_removal_factor = 1.0 + 0.5 * (steam_flow[i] / 10.0)  # Simplified
                power[i] = power[i-1] / heat_removal_factor
            else:
                power[i] = power[i-1]
            
            # Pressure decreases due to steam loss
            if t[i] >= conditions.trigger_time:
                pressure_loss_rate = -steam_flow[i] * 1e5  # Simplified
                pressure[i] = max(pressure[i-1] + pressure_loss_rate * dt, 1e5)  # Min 1 bar
            else:
                pressure[i] = pressure[i-1]
            
            # Temperature decreases due to increased heat removal
            if t[i] >= conditions.trigger_time:
                temp_change = -0.1 * (power[i] - power[i-1]) / conditions.initial_power * 100.0
                temperature[i] = max(temperature[i-1] + temp_change, 300.0)
            else:
                temperature[i] = temperature[i-1]
        
        return {
            "time": t,
            "power": power,
            "pressure": pressure,
            "temperature": temperature,
            "steam_flow": steam_flow,
            "transient_type": conditions.transient_type.value,
        }


class FeedwaterLineBreakTransient(PWRSMRTransient):
    """
    Feedwater line break transient for PWR SMRs.
    
    Models the response to a rupture in the feedwater line, which causes:
    1. Loss of feedwater flow
    2. Reduced heat removal from secondary system
    3. Primary system temperature increase
    4. Potential reactor scram
    
    Example:
        >>> fwlb = FeedwaterLineBreakTransient(reactor_spec, core)
        >>> conditions = TransientConditions(
        ...     initial_power=77e6,
        ...     initial_temperature=600.0,
        ...     initial_flow_rate=100.0,
        ...     initial_pressure=15.5e6,
        ...     transient_type=TransientType.FEEDWATER_LINE_BREAK,
        ...     trigger_time=0.0
        ... )
        >>> result = fwlb.simulate(conditions, break_area=0.02)
    """
    
    def simulate(
        self,
        conditions: TransientConditions,
        break_area: float = 0.02,  # m²
    ) -> Dict:
        """
        Simulate feedwater line break transient.
        
        Args:
            conditions: TransientConditions object.
            break_area: Break area [m²].
        
        Returns:
            Dictionary with time history.
        """
        if not isinstance(conditions, TransientConditions):
            raise ValueError(f"conditions must be TransientConditions, got {type(conditions)}")
        
        logger.info(f"Starting feedwater line break simulation")
        
        self.console.print(f"[bold cyan]Simulating Feedwater Line Break[/bold cyan]")
        
        t = np.linspace(conditions.t_start, conditions.t_end, 1000)
        dt = t[1] - t[0]
        
        power = np.zeros_like(t)
        temperature = np.zeros_like(t)
        feedwater_flow = np.zeros_like(t)
        
        power[0] = conditions.initial_power
        temperature[0] = conditions.initial_temperature
        feedwater_flow[0] = conditions.initial_flow_rate
        
        for i in range(1, len(t)):
            if t[i] >= conditions.trigger_time:
                # Feedwater flow lost
                feedwater_flow[i] = max(0.0, feedwater_flow[i-1] - break_area * 10.0 * dt)
                
                # Heat removal decreases
                heat_removal_factor = feedwater_flow[i] / conditions.initial_flow_rate
                power[i] = power[i-1] * (1.0 + 0.1 * (1.0 - heat_removal_factor))
                
                # Temperature increases
                temp_increase = 0.5 * (power[i] - power[i-1]) / conditions.initial_power * 50.0
                temperature[i] = min(temperature[i-1] + temp_increase, 1000.0)
            else:
                power[i] = power[i-1]
                temperature[i] = temperature[i-1]
                feedwater_flow[i] = feedwater_flow[i-1]
        
        return {
            "time": t,
            "power": power,
            "temperature": temperature,
            "feedwater_flow": feedwater_flow,
            "transient_type": conditions.transient_type.value,
        }


class PressurizerTransient(PWRSMRTransient):
    """
    Pressurizer pressure/temperature transient for PWR SMRs.
    
    Models pressurizer response to pressure/temperature changes, which can occur
    due to power changes, coolant temperature changes, or control system actions.
    
    Example:
        >>> press = PressurizerTransient(reactor_spec, core)
        >>> conditions = TransientConditions(
        ...     initial_power=77e6,
        ...     initial_temperature=600.0,
        ...     initial_pressure=15.5e6,
        ...     transient_type=TransientType.PRESSURIZER_TRANSIENT,
        ...     trigger_time=0.0
        ... )
        >>> result = press.simulate(conditions, pressure_setpoint=15.5e6)
    """
    
    def simulate(
        self,
        conditions: TransientConditions,
        pressure_setpoint: float = 15.5e6,  # Pa
        pressure_change_rate: float = 1e5,  # Pa/s
    ) -> Dict:
        """
        Simulate pressurizer transient.
        
        Args:
            conditions: TransientConditions object.
            pressure_setpoint: Target pressure setpoint [Pa].
            pressure_change_rate: Rate of pressure change [Pa/s].
        
        Returns:
            Dictionary with time history.
        """
        if not isinstance(conditions, TransientConditions):
            raise ValueError(f"conditions must be TransientConditions, got {type(conditions)}")
        
        logger.info(f"Starting pressurizer transient simulation")
        
        t = np.linspace(conditions.t_start, conditions.t_end, 1000)
        dt = t[1] - t[0]
        
        pressure = np.zeros_like(t)
        temperature = np.zeros_like(t)
        spray_flow = np.zeros_like(t)
        
        pressure[0] = conditions.initial_pressure
        temperature[0] = conditions.initial_temperature
        
        for i in range(1, len(t)):
            if t[i] >= conditions.trigger_time:
                # Pressure control
                pressure_error = pressure_setpoint - pressure[i-1]
                pressure[i] = pressure[i-1] + np.sign(pressure_error) * min(
                    abs(pressure_error), abs(pressure_change_rate * dt)
                )
                
                # Temperature follows pressure (simplified)
                temperature[i] = temperature[i-1] + 0.1 * (pressure[i] - pressure[i-1]) / 1e6 * 10.0
                
                # Spray flow for pressure control
                if pressure[i] > pressure_setpoint:
                    spray_flow[i] = 0.1 * (pressure[i] - pressure_setpoint) / 1e6
                else:
                    spray_flow[i] = 0.0
            else:
                pressure[i] = pressure[i-1]
                temperature[i] = temperature[i-1]
                spray_flow[i] = 0.0
        
        return {
            "time": t,
            "pressure": pressure,
            "temperature": temperature,
            "spray_flow": spray_flow,
            "transient_type": conditions.transient_type.value,
        }


class LOCATransientLWR(PWRSMRTransient):
    """
    Loss of Coolant Accident (LOCA) for LWR SMRs.
    
    Models both small break (SB-LOCA) and large break (LB-LOCA) scenarios.
    Different from HTGR LOCA due to two-phase flow and different pressure regimes.
    
    Example:
        >>> loca = LOCATransientLWR(reactor_spec, core)
        >>> conditions = TransientConditions(
        ...     initial_power=77e6,
        ...     initial_temperature=600.0,
        ...     initial_pressure=15.5e6,
        ...     transient_type=TransientType.SB_LOCA,  # or LB_LOCA
        ...     trigger_time=0.0
        ... )
        >>> result = loca.simulate(conditions, break_area=0.05, break_type="small")
    """
    
    def simulate(
        self,
        conditions: TransientConditions,
        break_area: float = 0.05,  # m²
        break_type: str = "small",  # "small" or "large"
    ) -> Dict:
        """
        Simulate LOCA transient.
        
        Args:
            conditions: TransientConditions object.
            break_area: Break area [m²].
            break_type: Break type ("small" or "large").
        
        Returns:
            Dictionary with time history.
        """
        if not isinstance(conditions, TransientConditions):
            raise ValueError(f"conditions must be TransientConditions, got {type(conditions)}")
        
        if break_type not in ["small", "large"]:
            raise ValueError(f"break_type must be 'small' or 'large', got {break_type}")
        
        logger.info(f"Starting {break_type} LOCA simulation")
        
        self.console.print(f"[bold cyan]Simulating {break_type.upper()} LOCA[/bold cyan]")
        
        t = np.linspace(conditions.t_start, conditions.t_end, 1000)
        dt = t[1] - t[0]
        
        power = np.zeros_like(t)
        pressure = np.zeros_like(t)
        temperature = np.zeros_like(t)
        coolant_flow = np.zeros_like(t)
        
        power[0] = conditions.initial_power
        pressure[0] = conditions.initial_pressure
        temperature[0] = conditions.initial_temperature
        coolant_flow[0] = conditions.initial_flow_rate
        
        # Break severity factor
        severity = 2.0 if break_type == "large" else 0.5
        
        for i in range(1, len(t)):
            if t[i] >= conditions.trigger_time:
                # Coolant loss
                coolant_loss_rate = break_area * severity * 100.0  # kg/s
                coolant_flow[i] = max(0.0, coolant_flow[i-1] - coolant_loss_rate * dt)
                
                # Pressure decreases
                pressure_loss_rate = -severity * 1e6  # Pa/s
                pressure[i] = max(pressure[i-1] + pressure_loss_rate * dt, 1e5)
                
                # Power decreases due to scram (if available)
                if conditions.scram_available and t[i] >= conditions.trigger_time + conditions.scram_delay:
                    power[i] = power[i-1] * 0.1  # Rapid power reduction
                else:
                    power[i] = power[i-1] * (1.0 - 0.01 * dt)
                
                # Temperature increases initially, then decreases
                if pressure[i] > 5e6:  # High pressure phase
                    temp_increase = 0.2 * (power[i] - power[i-1]) / conditions.initial_power * 50.0
                    temperature[i] = min(temperature[i-1] + temp_increase, 800.0)
                else:  # Low pressure phase
                    temperature[i] = max(temperature[i-1] - 0.5 * dt, 373.0)  # Cooling
            else:
                power[i] = power[i-1]
                pressure[i] = pressure[i-1]
                temperature[i] = temperature[i-1]
                coolant_flow[i] = coolant_flow[i-1]
        
        return {
            "time": t,
            "power": power,
            "pressure": pressure,
            "temperature": temperature,
            "coolant_flow": coolant_flow,
            "transient_type": conditions.transient_type.value,
            "break_type": break_type,
        }


class BWRSMRTransient:
    """
    Base class for BWR SMR transient analysis.
    
    Provides common functionality for BWR SMR-specific transients including
    steam separator issues, recirculation pump trips, and BWR-specific LOCA scenarios.
    
    Attributes:
        reactor_spec: Reactor specification object.
        geometry: Core geometry object.
        console: Rich console for progress output.
    """
    
    def __init__(self, reactor_spec, core_geometry):
        """
        Initialize BWR SMR transient analyzer.
        
        Args:
            reactor_spec: Reactor specification object.
            core_geometry: Core geometry object.
        
        Raises:
            ValueError: If inputs are invalid.
        """
        if reactor_spec is None:
            raise ValueError("reactor_spec cannot be None")
        if core_geometry is None:
            raise ValueError("core_geometry cannot be None")
        
        self.spec = reactor_spec
        self.geometry = core_geometry
        self.console = Console()
        
        logger.debug("BWRSMRTransient initialized")


class RecirculationPumpTripTransient(BWRSMRTransient):
    """
    Recirculation pump trip transient for BWR SMRs.
    
    Models the response to loss of forced recirculation, which causes:
    1. Reduced coolant flow through core
    2. Increased void fraction
    3. Negative reactivity insertion (void coefficient)
    4. Power reduction
    
    Example:
        >>> rpt = RecirculationPumpTripTransient(reactor_spec, core)
        >>> conditions = TransientConditions(
        ...     initial_power=160e6,  # 160 MWe SMR
        ...     initial_temperature=550.0,
        ...     initial_flow_rate=200.0,
        ...     initial_pressure=7.0e6,
        ...     transient_type=TransientType.RECIRCULATION_PUMP_TRIP,
        ...     trigger_time=0.0
        ... )
        >>> result = rpt.simulate(conditions)
    """
    
    def simulate(self, conditions: TransientConditions) -> Dict:
        """
        Simulate recirculation pump trip transient.
        
        Args:
            conditions: TransientConditions object.
        
        Returns:
            Dictionary with time history.
        """
        if not isinstance(conditions, TransientConditions):
            raise ValueError(f"conditions must be TransientConditions, got {type(conditions)}")
        
        logger.info("Starting recirculation pump trip simulation")
        
        self.console.print(f"[bold cyan]Simulating Recirculation Pump Trip[/bold cyan]")
        
        t = np.linspace(conditions.t_start, conditions.t_end, 1000)
        dt = t[1] - t[0]
        
        power = np.zeros_like(t)
        flow_rate = np.zeros_like(t)
        void_fraction = np.zeros_like(t)
        pressure = np.zeros_like(t)
        
        power[0] = conditions.initial_power
        flow_rate[0] = conditions.initial_flow_rate
        void_fraction[0] = 0.3  # Initial void fraction for BWR
        pressure[0] = conditions.initial_pressure
        
        for i in range(1, len(t)):
            if t[i] >= conditions.trigger_time:
                # Flow rate decreases
                flow_rate[i] = max(0.0, flow_rate[i-1] * np.exp(-dt / 10.0))  # Exponential decay
                
                # Void fraction increases (less flow = more void)
                void_fraction[i] = min(0.8, void_fraction[i-1] + 0.1 * (1.0 - flow_rate[i] / conditions.initial_flow_rate))
                
                # Negative reactivity from void (BWR void coefficient ~ -0.01 dk/k per % void)
                void_reactivity = -0.01 * (void_fraction[i] - void_fraction[0]) * 100.0
                
                # Power decreases due to negative reactivity
                power[i] = power[i-1] * (1.0 + void_reactivity * dt)
                
                # Pressure slightly decreases
                pressure[i] = pressure[i-1] * (1.0 - 0.001 * dt)
            else:
                power[i] = power[i-1]
                flow_rate[i] = flow_rate[i-1]
                void_fraction[i] = void_fraction[i-1]
                pressure[i] = pressure[i-1]
        
        return {
            "time": t,
            "power": power,
            "flow_rate": flow_rate,
            "void_fraction": void_fraction,
            "pressure": pressure,
            "transient_type": conditions.transient_type.value,
        }


class SteamSeparatorIssueTransient(BWRSMRTransient):
    """
    Steam separator malfunction transient for BWR SMRs.
    
    Models the response to steam separator issues, which can cause:
    1. Reduced steam quality
    2. Increased moisture carryover
    3. Potential power oscillations
    
    Example:
        >>> ssi = SteamSeparatorIssueTransient(reactor_spec, core)
        >>> conditions = TransientConditions(
        ...     initial_power=160e6,
        ...     initial_temperature=550.0,
        ...     initial_pressure=7.0e6,
        ...     transient_type=TransientType.STEAM_SEPARATOR_ISSUE,
        ...     trigger_time=0.0
        ... )
        >>> result = ssi.simulate(conditions, separator_efficiency=0.5)
    """
    
    def simulate(
        self,
        conditions: TransientConditions,
        separator_efficiency: float = 0.5,  # Reduced efficiency
    ) -> Dict:
        """
        Simulate steam separator issue transient.
        
        Args:
            conditions: TransientConditions object.
            separator_efficiency: Separator efficiency (0.0 to 1.0).
        
        Returns:
            Dictionary with time history.
        """
        if not isinstance(conditions, TransientConditions):
            raise ValueError(f"conditions must be TransientConditions, got {type(conditions)}")
        
        if not 0.0 <= separator_efficiency <= 1.0:
            raise ValueError(f"separator_efficiency must be between 0 and 1, got {separator_efficiency}")
        
        logger.info(f"Starting steam separator issue simulation (efficiency={separator_efficiency})")
        
        t = np.linspace(conditions.t_start, conditions.t_end, 1000)
        dt = t[1] - t[0]
        
        power = np.zeros_like(t)
        steam_quality = np.zeros_like(t)
        moisture_carryover = np.zeros_like(t)
        
        power[0] = conditions.initial_power
        steam_quality[0] = 0.99  # Normal BWR steam quality
        moisture_carryover[0] = 0.01
        
        for i in range(1, len(t)):
            if t[i] >= conditions.trigger_time:
                # Steam quality decreases
                steam_quality[i] = max(0.5, steam_quality[i-1] * separator_efficiency)
                
                # Moisture carryover increases
                moisture_carryover[i] = min(0.2, 1.0 - steam_quality[i])
                
                # Power slightly decreases due to reduced efficiency
                power[i] = power[i-1] * (1.0 - 0.01 * moisture_carryover[i] * dt)
            else:
                power[i] = power[i-1]
                steam_quality[i] = steam_quality[i-1]
                moisture_carryover[i] = moisture_carryover[i-1]
        
        return {
            "time": t,
            "power": power,
            "steam_quality": steam_quality,
            "moisture_carryover": moisture_carryover,
            "transient_type": conditions.transient_type.value,
        }


class IntegralSMRTransient:
    """
    Base class for integral SMR transient analysis.
    
    Handles transients specific to integral SMR designs where the steam generator
    and primary system are integrated in a single vessel.
    
    Attributes:
        reactor_spec: Reactor specification object.
        geometry: Core geometry object.
        console: Rich console for progress output.
    """
    
    def __init__(self, reactor_spec, core_geometry):
        """
        Initialize integral SMR transient analyzer.
        
        Args:
            reactor_spec: Reactor specification object.
            core_geometry: Core geometry object.
        
        Raises:
            ValueError: If inputs are invalid.
        """
        if reactor_spec is None:
            raise ValueError("reactor_spec cannot be None")
        if core_geometry is None:
            raise ValueError("core_geometry cannot be None")
        
        self.spec = reactor_spec
        self.geometry = core_geometry
        self.console = Console()
        
        logger.debug("IntegralSMRTransient initialized")


class SteamGeneratorTubeRuptureTransient(IntegralSMRTransient):
    """
    In-vessel steam generator tube rupture transient for integral SMRs.
    
    Models the response to a tube rupture in the in-vessel steam generator, which causes:
    1. Primary-to-secondary leakage
    2. Pressure equalization
    3. Potential contamination of secondary system
    4. Reactor scram
    
    Example:
        >>> sgt = SteamGeneratorTubeRuptureTransient(reactor_spec, core)
        >>> conditions = TransientConditions(
        ...     initial_power=100e6,
        ...     initial_temperature=600.0,
        ...     initial_pressure=15.5e6,
        ...     transient_type=TransientType.STEAM_GENERATOR_TUBE_RUPTURE,
        ...     trigger_time=0.0
        ... )
        >>> result = sgt.simulate(conditions, tube_rupture_count=1)
    """
    
    def simulate(
        self,
        conditions: TransientConditions,
        tube_rupture_count: int = 1,
        rupture_area_per_tube: float = 1e-4,  # m²
    ) -> Dict:
        """
        Simulate steam generator tube rupture transient.
        
        Args:
            conditions: TransientConditions object.
            tube_rupture_count: Number of tubes ruptured.
            rupture_area_per_tube: Rupture area per tube [m²].
        
        Returns:
            Dictionary with time history.
        """
        if not isinstance(conditions, TransientConditions):
            raise ValueError(f"conditions must be TransientConditions, got {type(conditions)}")
        
        if tube_rupture_count < 1:
            raise ValueError(f"tube_rupture_count must be >= 1, got {tube_rupture_count}")
        
        logger.info(f"Starting SG tube rupture simulation ({tube_rupture_count} tubes)")
        
        self.console.print(f"[bold cyan]Simulating Steam Generator Tube Rupture[/bold cyan]")
        
        t = np.linspace(conditions.t_start, conditions.t_end, 1000)
        dt = t[1] - t[0]
        
        power = np.zeros_like(t)
        primary_pressure = np.zeros_like(t)
        secondary_pressure = np.zeros_like(t)
        leakage_rate = np.zeros_like(t)
        
        power[0] = conditions.initial_power
        primary_pressure[0] = conditions.initial_pressure
        secondary_pressure[0] = 6.0e6  # Typical secondary pressure
        leakage_rate[0] = 0.0
        
        total_rupture_area = tube_rupture_count * rupture_area_per_tube
        
        for i in range(1, len(t)):
            if t[i] >= conditions.trigger_time:
                # Leakage rate (simplified)
                pressure_diff = primary_pressure[i-1] - secondary_pressure[i-1]
                leakage_rate[i] = total_rupture_area * np.sqrt(2 * pressure_diff / 1000.0) * 100.0  # kg/s
                
                # Pressure equalization
                primary_pressure[i] = primary_pressure[i-1] - leakage_rate[i] * 1e4 * dt
                secondary_pressure[i] = secondary_pressure[i-1] + leakage_rate[i] * 1e4 * dt
                
                # Reactor scram (if available)
                if conditions.scram_available and t[i] >= conditions.trigger_time + conditions.scram_delay:
                    power[i] = power[i-1] * 0.1
                else:
                    power[i] = power[i-1] * (1.0 - 0.01 * dt)
            else:
                power[i] = power[i-1]
                primary_pressure[i] = primary_pressure[i-1]
                secondary_pressure[i] = secondary_pressure[i-1]
                leakage_rate[i] = 0.0
        
        return {
            "time": t,
            "power": power,
            "primary_pressure": primary_pressure,
            "secondary_pressure": secondary_pressure,
            "leakage_rate": leakage_rate,
            "transient_type": conditions.transient_type.value,
            "tube_rupture_count": tube_rupture_count,
        }


def decay_heat_ans_standard(t: np.ndarray, P0: float, t_operate: float) -> np.ndarray:  # pragma: no cover
    """
    ANS 5.1 standard decay heat curve.
    Fast Numba implementation.

    Note: This function is excluded from coverage reporting because Numba JIT
    compilation makes line-by-line coverage tracking unreliable. This function
    is tested in tests/test_safety.py.

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
