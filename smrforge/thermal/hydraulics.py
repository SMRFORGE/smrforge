# smrforge/thermal/hydraulics.py
"""
Thermal-hydraulics solver for HTGR applications.
Supports 1D channel models, porous media, and conjugate heat transfer.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np
from numba import njit, prange
from scipy.integrate import odeint, solve_ivp
from scipy.optimize import fsolve


class FlowRegime(Enum):
    """Flow regime classification."""

    LAMINAR = "laminar"
    TRANSITIONAL = "transitional"
    TURBULENT = "turbulent"


@dataclass
class ChannelGeometry:
    """Geometric parameters for coolant channel."""

    length: float  # cm
    diameter: float  # cm (hydraulic diameter)
    flow_area: float  # cm²
    heated_perimeter: float  # cm

    @property
    def hydraulic_diameter(self) -> float:
        """D_h = 4A/P."""
        return 4 * self.flow_area / self.heated_perimeter


@dataclass
class FluidProperties:
    """Helium coolant properties (functions of T, P)."""

    temperature: float  # K
    pressure: float  # Pa

    def density(self) -> float:
        """ρ = P / (R_specific * T)."""
        R_specific = 2077.0  # J/kg-K for helium
        return self.pressure / (R_specific * self.temperature)

    def viscosity(self) -> float:
        """Dynamic viscosity [Pa-s] - Sutherland's formula."""
        T_ref = 273.15
        mu_ref = 1.865e-5
        C = 79.4
        return (
            mu_ref
            * (self.temperature / T_ref) ** 1.5
            * (T_ref + C)
            / (self.temperature + C)
        )

    def thermal_conductivity(self) -> float:
        """k [W/m-K]."""
        return 2.682e-3 + 1.123e-4 * self.temperature - 9.8e-9 * self.temperature**2

    def specific_heat(self) -> float:
        """c_p [J/kg-K]."""
        return 5195.0  # Nearly constant for helium

    def prandtl_number(self) -> float:
        """Pr = μ * c_p / k."""
        return self.viscosity() * self.specific_heat() / self.thermal_conductivity()


class ChannelThermalHydraulics:
    """
    1D thermal-hydraulics for single coolant channel.
    Solves coupled momentum and energy equations.
    """

    def __init__(self, geometry: ChannelGeometry, inlet_conditions: Dict):
        self.geom = geometry
        self.T_in = inlet_conditions["temperature"]  # K
        self.P_in = inlet_conditions["pressure"]  # Pa
        self.mdot = inlet_conditions["mass_flow_rate"]  # kg/s

        # Discretization
        self.nz = 100
        self.z = np.linspace(0, geometry.length, self.nz + 1)
        self.dz = self.z[1] - self.z[0]

        # Solution arrays
        self.T_coolant = np.full(self.nz + 1, self.T_in)
        self.P_coolant = np.full(self.nz + 1, self.P_in)
        self.T_wall = np.zeros(self.nz + 1)

        # Heat transfer from fuel
        self.q_linear = np.zeros(self.nz + 1)  # W/cm (linear power density)

    def set_power_profile(self, power_profile: np.ndarray):
        """
        Set axial power profile.

        Args:
            power_profile: Linear power density [W/cm] at each z
        """
        self.q_linear = power_profile

    def solve_steady_state(
        self, T_fuel: Optional[np.ndarray] = None
    ) -> Dict[str, np.ndarray]:
        """
        Solve steady-state thermal-hydraulics.

        Args:
            T_fuel: Fuel temperature profile [K] (optional)

        Returns:
            Dict with temperature, pressure profiles
        """
        # March along channel from inlet
        for i in range(self.nz):
            z = self.z[i]

            # Current state
            T = self.T_coolant[i]
            P = self.P_coolant[i]

            # Fluid properties
            fluid = FluidProperties(T, P)
            rho = fluid.density()
            mu = fluid.viscosity()
            k_fluid = fluid.thermal_conductivity()
            cp = fluid.specific_heat()
            Pr = fluid.prandtl_number()

            # Flow velocity
            v = self.mdot / (rho * self.geom.flow_area * 1e-4)  # m/s

            # Reynolds number
            Re = rho * v * (self.geom.hydraulic_diameter / 100) / mu

            # Heat transfer coefficient
            h = self._heat_transfer_coefficient(Re, Pr, k_fluid)

            # Wall temperature (from heat balance)
            if T_fuel is not None:
                self.T_wall[i] = self._compute_wall_temperature(
                    T_fuel[i], T, h, self.q_linear[i]
                )
            else:
                # Simple model without fuel temperature
                q_prime = self.q_linear[i] * 100  # W/m
                dT_wall = q_prime / (h * self.geom.heated_perimeter / 100)
                self.T_wall[i] = T + dT_wall

            # Energy equation: dT/dz = q' / (mdot * cp)
            q_total = self.q_linear[i] * self.dz  # W
            dT = q_total / (self.mdot * cp)
            self.T_coolant[i + 1] = T + dT

            # Momentum equation: dP/dz = -friction - acceleration
            f = self._friction_factor(Re)
            dP_friction = (
                -f
                * (self.dz / 100)
                / (self.geom.hydraulic_diameter / 100)
                * 0.5
                * rho
                * v**2
            )

            # Acceleration pressure drop (usually small)
            rho_next = self.P_coolant[i] / (2077.0 * self.T_coolant[i + 1])
            dP_accel = self.mdot**2 * (
                1 / (rho_next * self.geom.flow_area * 1e-4) ** 2
                - 1 / (rho * self.geom.flow_area * 1e-4) ** 2
            )

            self.P_coolant[i + 1] = P + dP_friction - dP_accel

        return {
            "z": self.z,
            "T_coolant": self.T_coolant,
            "P_coolant": self.P_coolant,
            "T_wall": self.T_wall,
        }

    def _heat_transfer_coefficient(self, Re: float, Pr: float, k: float) -> float:
        """
        Heat transfer coefficient [W/m²-K].
        Uses Gnielinski correlation for turbulent flow.
        """
        D_h = self.geom.hydraulic_diameter / 100  # m

        if Re < 2300:
            # Laminar: Nu = 4.36 for constant heat flux
            Nu = 4.36
        elif Re < 4000:
            # Transitional: interpolate
            Nu_lam = 4.36
            Nu_turb = self._gnielinski_nu(4000, Pr)
            Nu = Nu_lam + (Nu_turb - Nu_lam) * (Re - 2300) / (4000 - 2300)
        else:
            # Turbulent: Gnielinski correlation
            Nu = self._gnielinski_nu(Re, Pr)

        h = Nu * k / D_h
        return h

    @staticmethod
    def _gnielinski_nu(Re: float, Pr: float) -> float:
        """Gnielinski correlation for turbulent pipe flow."""
        f = (0.79 * np.log(Re) - 1.64) ** (-2)  # Petukhov friction
        Nu = (
            (f / 8)
            * (Re - 1000)
            * Pr
            / (1 + 12.7 * np.sqrt(f / 8) * (Pr ** (2 / 3) - 1))
        )
        return Nu

    @staticmethod
    def _friction_factor(Re: float) -> float:
        """Darcy friction factor."""
        if Re < 2300:
            # Laminar: f = 64/Re
            return 64.0 / Re
        else:
            # Turbulent: Blasius correlation
            return 0.316 * Re ** (-0.25)

    def _compute_wall_temperature(
        self, T_fuel: float, T_coolant: float, h: float, q_linear: float
    ) -> float:
        """
        Compute wall temperature from fuel to coolant heat transfer.

        Args:
            T_fuel: Fuel centerline temperature [K]
            T_coolant: Bulk coolant temperature [K]
            h: Heat transfer coefficient [W/m²-K]
            q_linear: Linear power density [W/cm]

        Returns:
            Wall temperature [K]
        """
        # Simplified 1D radial conduction through fuel and cladding
        q_total = q_linear * 100  # W/m

        # Heat flux at wall
        q_flux = q_total / (self.geom.heated_perimeter / 100)  # W/m²

        # Newton cooling: T_wall = T_coolant + q"/h
        T_wall = T_coolant + q_flux / h

        return T_wall


class FuelRodThermal:
    """
    Thermal conduction in fuel rod with TRISO particles.
    1D radial heat conduction.
    """

    def __init__(self, radius: float, n_nodes: int = 50):
        self.radius = radius  # cm
        self.n_nodes = n_nodes

        # Radial mesh
        self.r = np.linspace(0, radius, n_nodes + 1)
        self.dr = self.r[1] - self.r[0]

        # Temperature profile
        self.T = np.zeros(n_nodes + 1)

    def solve_steady_conduction(
        self, q_vol: float, k_fuel: float, T_surface: float
    ) -> np.ndarray:
        """
        Solve steady-state radial conduction.

        -1/r * d/dr(r * k * dT/dr) = q'''

        Args:
            q_vol: Volumetric heat generation [W/cm³]
            k_fuel: Fuel thermal conductivity [W/cm-K]
            T_surface: Surface temperature [K] (BC)

        Returns:
            Temperature profile [K]
        """
        # Analytical solution for constant k and q:
        # T(r) = T_surface + q''' * (R² - r²) / (4k)

        R = self.radius
        self.T = T_surface + q_vol * (R**2 - self.r**2) / (4 * k_fuel)

        return self.T

    def solve_transient_conduction(
        self,
        q_vol: np.ndarray,
        k_fuel: float,
        rho: float,
        cp: float,
        T_surface: float,
        t_span: Tuple[float, float],
        T_initial: Optional[np.ndarray] = None,
    ) -> Dict:
        """
        Solve transient radial conduction.

        ρ*cp*∂T/∂t = 1/r * ∂/∂r(r * k * ∂T/∂r) + q'''(t)

        Args:
            q_vol: Time-dependent heat generation [W/cm³] (callable or array)
            k_fuel: Thermal conductivity [W/cm-K]
            rho: Density [g/cm³]
            cp: Specific heat [J/g-K]
            T_surface: Surface BC [K]
            t_span: (t_start, t_end) [s]
            T_initial: Initial temperature profile

        Returns:
            Dict with 't', 'T' (time and temperature history)
        """
        if T_initial is None:
            T_initial = np.full_like(self.r, T_surface)

        # Time integration using scipy
        def dTdt(t, T):
            """Temperature derivative."""
            dT = np.zeros_like(T)

            # Get heat generation at time t
            q = q_vol(t) if callable(q_vol) else q_vol

            # Interior nodes (finite difference)
            for i in range(1, self.n_nodes):
                r = self.r[i]

                # Second derivative with 1/r term
                d2T_dr2 = (T[i + 1] - 2 * T[i] + T[i - 1]) / self.dr**2
                dT_dr = (T[i + 1] - T[i - 1]) / (2 * self.dr)

                dT[i] = (k_fuel / (rho * cp)) * (d2T_dr2 + dT_dr / r) + q / (rho * cp)

            # Centerline BC: dT/dr = 0 (symmetry)
            dT[0] = dT[1]

            # Surface BC: T = T_surface
            dT[-1] = 0  # Fixed temperature
            T[-1] = T_surface

            return dT

        # Solve ODE
        sol = solve_ivp(dTdt, t_span, T_initial, method="BDF", dense_output=True)

        return {"t": sol.t, "T": sol.y}  # Shape: (n_nodes+1, n_times)


class PorousMediaFlow:
    """
    Flow through porous pebble bed using Ergun equation.
    Suitable for pebble-bed HTGR cores.
    """

    def __init__(
        self,
        bed_height: float,
        bed_diameter: float,
        pebble_diameter: float,
        porosity: float,
    ):
        self.H = bed_height  # cm
        self.D = bed_diameter  # cm
        self.d_p = pebble_diameter  # cm
        self.epsilon = porosity  # void fraction

        # Discretization
        self.nz = 50
        self.z = np.linspace(0, bed_height, self.nz + 1)

        # Solution
        self.T_coolant = np.zeros(self.nz + 1)
        self.P_coolant = np.zeros(self.nz + 1)
        self.velocity = np.zeros(self.nz + 1)

    def solve_flow(
        self, mdot: float, T_in: float, P_in: float, q_vol_profile: np.ndarray
    ) -> Dict:
        """
        Solve flow through porous bed.

        Args:
            mdot: Mass flow rate [kg/s]
            T_in: Inlet temperature [K]
            P_in: Inlet pressure [Pa]
            q_vol_profile: Volumetric heat generation profile [W/cm³]

        Returns:
            Dict with flow solutions
        """
        self.T_coolant[0] = T_in
        self.P_coolant[0] = P_in

        # Flow area
        A_flow = np.pi * (self.D / 2) ** 2 * self.epsilon * 1e-4  # m²

        dz = self.z[1] - self.z[0]  # cm

        for i in range(self.nz):
            T = self.T_coolant[i]
            P = self.P_coolant[i]

            # Fluid properties
            fluid = FluidProperties(T, P)
            rho = fluid.density()
            mu = fluid.viscosity()
            cp = fluid.specific_heat()

            # Superficial velocity
            v_s = mdot / (rho * A_flow)  # m/s

            # Pressure drop (Ergun equation)
            dP_dz = self._ergun_pressure_drop(v_s, rho, mu)
            self.P_coolant[i + 1] = P - dP_dz * (dz / 100)

            # Energy balance
            q_total = q_vol_profile[i] * (A_flow * 1e4) * dz  # W
            dT = q_total / (mdot * cp)
            self.T_coolant[i + 1] = T + dT

            self.velocity[i] = v_s

        return {
            "z": self.z,
            "T_coolant": self.T_coolant,
            "P_coolant": self.P_coolant,
            "velocity": self.velocity,
        }

    def _ergun_pressure_drop(self, v_s: float, rho: float, mu: float) -> float:
        """
        Ergun equation for pressure drop in packed bed.

        dP/dz = 150*μ*v_s*(1-ε)²/(ε³*d_p²) + 1.75*ρ*v_s²*(1-ε)/(ε³*d_p)

        Args:
            v_s: Superficial velocity [m/s]
            rho: Density [kg/m³]
            mu: Viscosity [Pa-s]

        Returns:
            Pressure gradient [Pa/m]
        """
        d_p = self.d_p / 100  # m
        eps = self.epsilon

        # Viscous term
        term1 = 150 * mu * v_s * (1 - eps) ** 2 / (eps**3 * d_p**2)

        # Inertial term
        term2 = 1.75 * rho * v_s**2 * (1 - eps) / (eps**3 * d_p)

        return term1 + term2


@njit(cache=True)
def solve_tridiagonal_fast(
    a: np.ndarray, b: np.ndarray, c: np.ndarray, d: np.ndarray
) -> np.ndarray:
    """
    Fast tridiagonal solver using Thomas algorithm (Numba-accelerated).
    Solves: a[i]*x[i-1] + b[i]*x[i] + c[i]*x[i+1] = d[i]
    """
    n = len(d)
    x = np.zeros(n)

    # Forward elimination
    c_prime = np.zeros(n - 1)
    d_prime = np.zeros(n)

    c_prime[0] = c[0] / b[0]
    d_prime[0] = d[0] / b[0]

    for i in range(1, n - 1):
        denom = b[i] - a[i] * c_prime[i - 1]
        c_prime[i] = c[i] / denom
        d_prime[i] = (d[i] - a[i] * d_prime[i - 1]) / denom

    d_prime[n - 1] = (d[n - 1] - a[n - 1] * d_prime[n - 2]) / (
        b[n - 1] - a[n - 1] * c_prime[n - 2]
    )

    # Back substitution
    x[n - 1] = d_prime[n - 1]
    for i in range(n - 2, -1, -1):
        x[i] = d_prime[i] - c_prime[i] * x[i + 1]

    return x


class ConjugateHeatTransfer:
    """
    Coupled neutronics-thermal solver.
    Iterates between power distribution and temperature feedback.
    """

    def __init__(self, neutronics_solver, thermal_solver):
        self.neutronics = neutronics_solver
        self.thermal = thermal_solver

    def solve_coupled(self, max_iterations: int = 50, tolerance: float = 1e-4) -> Dict:
        """
        Solve coupled neutronics-thermal problem.

        Returns:
            Converged power and temperature distributions
        """
        # Initial guess: uniform temperature
        T_fuel = np.full_like(self.neutronics.flux[:, :, 0], 1200.0)

        for iteration in range(max_iterations):
            # 1. Solve neutronics with current temperatures
            k_eff, flux = self.neutronics.solve_steady_state()

            # 2. Compute power distribution
            power = self.neutronics.compute_power_distribution(10e6)  # 10 MW

            # 3. Solve thermal with power distribution
            T_fuel_new = self.thermal.solve_with_power(power)

            # 4. Check convergence
            error = np.max(np.abs(T_fuel_new - T_fuel)) / np.max(T_fuel)

            if error < tolerance:
                print(f"Coupled solution converged in {iteration+1} iterations")
                break

            # 5. Update temperature with relaxation
            omega = 0.5  # Under-relaxation
            T_fuel = omega * T_fuel_new + (1 - omega) * T_fuel

        return {"k_eff": k_eff, "flux": flux, "power": power, "T_fuel": T_fuel}


if __name__ == "__main__":
    from rich.console import Console

    console = Console()

    console.print("[bold cyan]HTGR Thermal-Hydraulics Demo[/bold cyan]\n")

    # Example 1: Single coolant channel
    console.print("[bold]1. Coolant Channel Analysis[/bold]")

    geom = ChannelGeometry(
        length=793.0,  # cm (core height)
        diameter=1.588,  # cm (5/8")
        flow_area=1.98,  # cm²
        heated_perimeter=4.98,  # cm
    )

    inlet = {
        "temperature": 573.0,  # K (300°C)
        "pressure": 7.0e6,  # Pa (7 MPa)
        "mass_flow_rate": 0.05,  # kg/s per channel
    }

    channel = ChannelThermalHydraulics(geom, inlet)

    # Set cosine axial power profile
    z = channel.z
    L = geom.length
    q_avg = 100.0  # W/cm average
    power_profile = q_avg * 1.5 * np.cos(np.pi * (z - L / 2) / L)
    channel.set_power_profile(power_profile)

    # Solve
    result = channel.solve_steady_state()

    console.print(
        f"   Outlet temperature: {result['T_coolant'][-1]:.1f} K "
        f"({result['T_coolant'][-1]-273:.1f}°C)"
    )
    console.print(f"   Outlet pressure: {result['P_coolant'][-1]/1e6:.2f} MPa")
    console.print(
        f"   Pressure drop: {(inlet['pressure'] - result['P_coolant'][-1])/1e3:.1f} kPa"
    )
    console.print(f"   Max wall temp: {np.max(result['T_wall']):.1f} K")

    # Example 2: Pebble bed flow
    console.print("\n[bold]2. Pebble Bed Flow[/bold]")

    pebble_bed = PorousMediaFlow(
        bed_height=1100.0,  # cm
        bed_diameter=300.0,  # cm
        pebble_diameter=6.0,  # cm
        porosity=0.39,  # Typical random packing
    )

    # Power profile
    q_vol = 5.0 * np.ones(pebble_bed.nz + 1)  # W/cm³ uniform

    bed_result = pebble_bed.solve_flow(
        mdot=50.0, T_in=573.0, P_in=7.0e6, q_vol_profile=q_vol  # kg/s total flow
    )

    console.print(f"   Outlet temperature: {bed_result['T_coolant'][-1]:.1f} K")
    console.print(
        f"   Pressure drop: {(bed_result['P_coolant'][0] - bed_result['P_coolant'][-1])/1e3:.1f} kPa"
    )

    console.print("\n[bold green]Thermal-hydraulics module ready![/bold green]")
