# smrforge/validation/data_validation.py
"""
Comprehensive data validation framework for SMRForge.
Ensures physical correctness, consistency, and bounds checking.
"""

import warnings
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
from rich.console import Console
from rich.table import Table


class ValidationLevel(Enum):
    """Severity levels for validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a validation issue."""

    level: ValidationLevel
    parameter: str
    message: str
    value: Optional[Any] = None
    expected: Optional[Any] = None
    location: Optional[str] = None

    def __str__(self) -> str:
        msg = f"[{self.level.value.upper()}] {self.parameter}: {self.message}"
        if self.value is not None:
            msg += f" (got: {self.value}"
            if self.expected is not None:
                msg += f", expected: {self.expected}"
            msg += ")"
        return msg


@dataclass
class ValidationResult:
    """Results from validation."""

    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)

    def add_issue(self, level: ValidationLevel, parameter: str, message: str, **kwargs):
        """Add a validation issue."""
        issue = ValidationIssue(level, parameter, message, **kwargs)
        self.issues.append(issue)

        # Mark as invalid if error or critical
        if level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]:
            self.valid = False

    def has_errors(self) -> bool:
        """Check if any errors or critical issues exist."""
        return any(
            i.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]
            for i in self.issues
        )

    def summary(self) -> Dict[str, int]:
        """Get count of issues by level."""
        summary = {level.value: 0 for level in ValidationLevel}
        for issue in self.issues:
            summary[issue.level.value] += 1
        return summary

    def print_report(self, console: Optional[Console] = None):
        """Print formatted validation report."""
        if console is None:
            console = Console()

        if not self.issues:
            console.print("[bold green]✓ All validations passed[/bold green]")
            return

        # Summary
        summary = self.summary()
        console.print("\n[bold]Validation Summary:[/bold]")

        table = Table(show_header=False)
        table.add_column("Level", style="cyan")
        table.add_column("Count", justify="right")

        for level in ValidationLevel:
            count = summary[level.value]
            if count > 0:
                color = {
                    "info": "blue",
                    "warning": "yellow",
                    "error": "red",
                    "critical": "bold red",
                }[level.value]
                table.add_row(level.value.upper(), f"[{color}]{count}[/{color}]")

        console.print(table)

        # Detailed issues
        if any(
            summary[level.value] > 0
            for level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]
        ):
            console.print("\n[bold red]Critical Issues:[/bold red]")
            for issue in self.issues:
                if issue.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]:
                    console.print(f"  • {issue}")

        if summary["warning"] > 0:
            console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for issue in self.issues:
                if issue.level == ValidationLevel.WARNING:
                    console.print(f"  • {issue}")


class PhysicalValidator:
    """
    Validates physical parameters for reactor analysis.
    Checks bounds, units, consistency, and physical reasonableness.
    """

    # Physical constants and limits
    ABSOLUTE_ZERO = 0.0  # K
    MAX_TEMPERATURE = 4000.0  # K (beyond material limits)
    MIN_PRESSURE = 0.0  # Pa
    MAX_PRESSURE = 50e6  # Pa (50 MPa, beyond typical reactor)
    MIN_DENSITY = 1e-6  # g/cm³
    MAX_DENSITY = 30.0  # g/cm³ (beyond heavy metals)
    MIN_ENRICHMENT = 0.0
    MAX_ENRICHMENT = 1.0

    @staticmethod
    def validate_temperature(
        T: float, name: str = "temperature", min_T: float = 273.0, max_T: float = 3000.0
    ) -> ValidationResult:
        """Validate temperature value."""
        result = ValidationResult(valid=True)

        if not isinstance(T, (int, float)):
            result.add_issue(
                ValidationLevel.ERROR, name, "Must be numeric", value=type(T)
            )
            return result

        if np.isnan(T) or np.isinf(T):
            result.add_issue(
                ValidationLevel.ERROR, name, "Invalid value (NaN or Inf)", value=T
            )
            return result

        if T <= PhysicalValidator.ABSOLUTE_ZERO:
            result.add_issue(
                ValidationLevel.ERROR,
                name,
                "Below absolute zero",
                value=T,
                expected=f"> {PhysicalValidator.ABSOLUTE_ZERO} K",
            )

        if T < min_T:
            result.add_issue(
                ValidationLevel.WARNING,
                name,
                "Below expected minimum",
                value=T,
                expected=f">= {min_T} K",
            )

        if T > max_T:
            result.add_issue(
                ValidationLevel.WARNING,
                name,
                "Above expected maximum",
                value=T,
                expected=f"<= {max_T} K",
            )

        if T > PhysicalValidator.MAX_TEMPERATURE:
            result.add_issue(
                ValidationLevel.ERROR,
                name,
                "Exceeds physical limits",
                value=T,
                expected=f"<= {PhysicalValidator.MAX_TEMPERATURE} K",
            )

        return result

    @staticmethod
    def validate_pressure(
        P: float, name: str = "pressure", min_P: float = 1e5, max_P: float = 10e6
    ) -> ValidationResult:
        """Validate pressure value."""
        result = ValidationResult(valid=True)

        if not isinstance(P, (int, float)):
            result.add_issue(
                ValidationLevel.ERROR, name, "Must be numeric", value=type(P)
            )
            return result

        if np.isnan(P) or np.isinf(P):
            result.add_issue(ValidationLevel.ERROR, name, "Invalid value", value=P)
            return result

        if P < PhysicalValidator.MIN_PRESSURE:
            result.add_issue(ValidationLevel.ERROR, name, "Negative pressure", value=P)

        if P < min_P:
            result.add_issue(
                ValidationLevel.WARNING,
                name,
                "Below expected minimum",
                value=P,
                expected=f">= {min_P} Pa",
            )

        if P > max_P:
            result.add_issue(
                ValidationLevel.WARNING,
                name,
                "Above expected maximum",
                value=P,
                expected=f"<= {max_P} Pa",
            )

        return result

    @staticmethod
    def validate_enrichment(
        enrichment: float, fuel_type: str = "LEU"
    ) -> ValidationResult:
        """Validate fuel enrichment."""
        result = ValidationResult(valid=True)

        if not isinstance(enrichment, (int, float)):
            result.add_issue(
                ValidationLevel.ERROR,
                "enrichment",
                "Must be numeric",
                value=type(enrichment),
            )
            return result

        if enrichment < PhysicalValidator.MIN_ENRICHMENT:
            result.add_issue(
                ValidationLevel.ERROR, "enrichment", "Below zero", value=enrichment
            )

        if enrichment > PhysicalValidator.MAX_ENRICHMENT:
            result.add_issue(
                ValidationLevel.ERROR, "enrichment", "Above 100%", value=enrichment
            )

        # Check fuel type limits
        if fuel_type == "LEU" and enrichment > 0.20:
            result.add_issue(
                ValidationLevel.ERROR,
                "enrichment",
                "Exceeds LEU limit (20%)",
                value=enrichment,
                expected="<= 0.20",
            )

        elif fuel_type == "HALEU" and enrichment > 0.20:
            if enrichment > 0.20 and enrichment <= 0.05:
                result.add_issue(
                    ValidationLevel.WARNING,
                    "enrichment",
                    "In HALEU range (>20%, <5%)",
                    value=enrichment,
                )

        elif fuel_type == "HEU" and enrichment < 0.20:
            result.add_issue(
                ValidationLevel.WARNING,
                "enrichment",
                "Below HEU threshold",
                value=enrichment,
            )

        return result

    @staticmethod
    def validate_power(
        power: float,
        reactor_type: str = "SMR",
        min_power: float = 1e3,
        max_power: float = 1e9,
    ) -> ValidationResult:
        """Validate power level."""
        result = ValidationResult(valid=True)

        if not isinstance(power, (int, float)):
            result.add_issue(
                ValidationLevel.ERROR, "power", "Must be numeric", value=type(power)
            )
            return result

        if power <= 0:
            result.add_issue(
                ValidationLevel.ERROR, "power", "Must be positive", value=power
            )

        if power < min_power:
            result.add_issue(
                ValidationLevel.WARNING,
                "power",
                "Very low power",
                value=power,
                expected=f">= {min_power} W",
            )

        if power > max_power:
            result.add_issue(
                ValidationLevel.WARNING,
                "power",
                "Very high power",
                value=power,
                expected=f"<= {max_power} W",
            )

        # Type-specific checks
        if reactor_type == "micro" and power > 10e6:
            result.add_issue(
                ValidationLevel.WARNING,
                "power",
                "High for micro-reactor",
                value=power,
                expected="<= 10 MWth",
            )

        elif reactor_type == "SMR" and power > 300e6:
            result.add_issue(
                ValidationLevel.WARNING,
                "power",
                "Exceeds typical SMR range",
                value=power,
                expected="<= 300 MWth",
            )

        return result

    @staticmethod
    def validate_k_eff(k_eff: float, margin: float = 0.02) -> ValidationResult:
        """Validate k-effective value."""
        result = ValidationResult(valid=True)

        if not isinstance(k_eff, (int, float)):
            result.add_issue(
                ValidationLevel.ERROR, "k_eff", "Must be numeric", value=type(k_eff)
            )
            return result

        if k_eff <= 0:
            result.add_issue(
                ValidationLevel.ERROR, "k_eff", "Must be positive", value=k_eff
            )

        if k_eff < 0.9:
            result.add_issue(
                # Subcritical solutions are expected in some workflows and tests.
                # Treat as warning (still notable, but not fatal).
                ValidationLevel.WARNING,
                "k_eff",
                "Too subcritical",
                value=k_eff,
                expected=">= 0.9",
            )

        # Extremely supercritical values are considered invalid outputs.
        # Keep a softer warning band for design exploration, but still fail fast
        # on clearly unphysical results (used by integration tests).
        if k_eff > 3.0:
            result.add_issue(
                ValidationLevel.ERROR,
                "k_eff",
                "Unphysically supercritical",
                value=k_eff,
                expected="<= 3.0",
            )
        elif k_eff > 1.2:
            result.add_issue(
                # Supercritical solutions can occur in design exploration; warn rather than error.
                ValidationLevel.WARNING,
                "k_eff",
                "Too supercritical",
                value=k_eff,
                expected="<= 1.2",
            )

        # Operating range check
        if k_eff < 1.0 - margin:
            result.add_issue(
                ValidationLevel.WARNING,
                "k_eff",
                "Below critical with margin",
                value=k_eff,
                expected=f">= {1.0 - margin}",
            )

        if k_eff > 1.0 + margin:
            result.add_issue(
                ValidationLevel.INFO, "k_eff", "Above critical with margin", value=k_eff
            )

        return result


class GeometryValidator:
    """Validates geometric parameters."""

    @staticmethod
    def validate_dimensions(
        height: float, diameter: float, min_size: float = 1.0, max_size: float = 2000.0
    ) -> ValidationResult:
        """Validate core dimensions."""
        result = ValidationResult(valid=True)

        # Height validation
        if height <= 0:
            result.add_issue(
                ValidationLevel.ERROR, "core_height", "Must be positive", value=height
            )

        if height < min_size:
            result.add_issue(
                ValidationLevel.WARNING,
                "core_height",
                "Very small",
                value=height,
                expected=f">= {min_size} cm",
            )

        if height > max_size:
            result.add_issue(
                ValidationLevel.WARNING,
                "core_height",
                "Very large",
                value=height,
                expected=f"<= {max_size} cm",
            )

        # Diameter validation
        if diameter <= 0:
            result.add_issue(
                ValidationLevel.ERROR,
                "core_diameter",
                "Must be positive",
                value=diameter,
            )

        if diameter < min_size:
            result.add_issue(
                ValidationLevel.WARNING,
                "core_diameter",
                "Very small",
                value=diameter,
                expected=f">= {min_size} cm",
            )

        if diameter > max_size:
            result.add_issue(
                ValidationLevel.WARNING,
                "core_diameter",
                "Very large",
                value=diameter,
                expected=f"<= {max_size} cm",
            )

        # Aspect ratio check
        aspect_ratio = height / diameter
        if aspect_ratio < 0.5:
            result.add_issue(
                ValidationLevel.WARNING,
                "aspect_ratio",
                "Very flat core (H/D < 0.5)",
                value=aspect_ratio,
            )

        if aspect_ratio > 5.0:
            result.add_issue(
                ValidationLevel.WARNING,
                "aspect_ratio",
                "Very tall core (H/D > 5)",
                value=aspect_ratio,
            )

        return result

    @staticmethod
    def validate_mesh(n_radial: int, n_axial: int) -> ValidationResult:
        """Validate mesh parameters."""
        result = ValidationResult(valid=True)

        if n_radial < 5:
            result.add_issue(
                ValidationLevel.WARNING,
                "n_radial",
                "Coarse radial mesh",
                value=n_radial,
                expected=">= 10",
            )

        if n_radial > 200:
            result.add_issue(
                ValidationLevel.WARNING,
                "n_radial",
                "Very fine radial mesh (slow)",
                value=n_radial,
                expected="<= 100",
            )

        if n_axial < 10:
            result.add_issue(
                ValidationLevel.WARNING,
                "n_axial",
                "Coarse axial mesh",
                value=n_axial,
                expected=">= 20",
            )

        if n_axial > 500:
            result.add_issue(
                ValidationLevel.WARNING,
                "n_axial",
                "Very fine axial mesh (slow)",
                value=n_axial,
                expected="<= 200",
            )

        return result


class NeutronicsValidator:
    """Validates neutronics parameters."""

    @staticmethod
    def validate_cross_sections(xs_data) -> ValidationResult:
        """Validate cross section data."""
        result = ValidationResult(valid=True)

        # Check for negative cross sections
        if np.any(xs_data.sigma_t < 0):
            result.add_issue(
                ValidationLevel.ERROR, "sigma_t", "Negative total cross section"
            )

        if np.any(xs_data.sigma_a < 0):
            result.add_issue(
                ValidationLevel.ERROR, "sigma_a", "Negative absorption cross section"
            )

        if np.any(xs_data.sigma_f < 0):
            result.add_issue(
                ValidationLevel.ERROR, "sigma_f", "Negative fission cross section"
            )

        # Check physical bounds
        if np.any(xs_data.sigma_a > xs_data.sigma_t):
            result.add_issue(
                ValidationLevel.ERROR,
                "cross_sections",
                "Absorption > Total (non-physical)",
            )

        if np.any(xs_data.sigma_f > xs_data.sigma_a):
            result.add_issue(
                ValidationLevel.ERROR,
                "cross_sections",
                "Fission > Absorption (non-physical)",
            )

        # Check diffusion coefficients
        if np.any(xs_data.D <= 0):
            result.add_issue(
                ValidationLevel.ERROR, "D", "Non-positive diffusion coefficient"
            )

        if np.any(xs_data.D > 10):
            result.add_issue(
                ValidationLevel.WARNING,
                "D",
                "Very large diffusion coefficient (>10 cm)",
            )

        # Check fission spectrum
        chi_sum = np.sum(xs_data.chi, axis=1)
        if not np.allclose(chi_sum[chi_sum > 0], 1.0, rtol=1e-3):
            result.add_issue(
                ValidationLevel.WARNING,
                "chi",
                "Fission spectrum not normalized",
                value=chi_sum,
            )

        return result

    @staticmethod
    def validate_flux(flux: np.ndarray, power: float) -> ValidationResult:
        """Validate flux solution."""
        result = ValidationResult(valid=True)

        if np.any(flux < 0):
            result.add_issue(ValidationLevel.ERROR, "flux", "Negative flux values")

        if np.any(np.isnan(flux)):
            result.add_issue(ValidationLevel.CRITICAL, "flux", "NaN in flux solution")

        if np.any(np.isinf(flux)):
            result.add_issue(ValidationLevel.CRITICAL, "flux", "Inf in flux solution")

        # Check reasonableness
        max_flux = np.max(flux)
        if max_flux < 1e10:
            result.add_issue(
                ValidationLevel.WARNING,
                "flux",
                "Very low flux",
                value=max_flux,
                expected=">= 1e12 n/cm²-s",
            )

        if max_flux > 1e16:
            result.add_issue(
                ValidationLevel.WARNING,
                "flux",
                "Very high flux",
                value=max_flux,
                expected="<= 1e15 n/cm²-s",
            )

        return result


class ThermalValidator:
    """Validates thermal-hydraulics parameters."""

    @staticmethod
    def validate_heat_transfer(h: float, regime: str = "turbulent") -> ValidationResult:
        """Validate heat transfer coefficient."""
        result = ValidationResult(valid=True)

        if h <= 0:
            result.add_issue(
                ValidationLevel.ERROR,
                "h",
                "Non-positive heat transfer coefficient",
                value=h,
            )

        if regime == "laminar" and h > 1000:
            result.add_issue(
                ValidationLevel.WARNING,
                "h",
                "Too high for laminar flow",
                value=h,
                expected="< 1000 W/m²-K",
            )

        if regime == "turbulent" and h < 100:
            result.add_issue(
                ValidationLevel.WARNING,
                "h",
                "Too low for turbulent flow",
                value=h,
                expected="> 100 W/m²-K",
            )

        return result

    @staticmethod
    def validate_reynolds_number(Re: float) -> ValidationResult:
        """Validate Reynolds number."""
        result = ValidationResult(valid=True)

        if Re < 0:
            result.add_issue(
                ValidationLevel.ERROR, "Re", "Negative Reynolds number", value=Re
            )

        if Re < 1:
            result.add_issue(
                ValidationLevel.WARNING, "Re", "Very low Re (creeping flow)", value=Re
            )

        if Re > 1e7:
            result.add_issue(
                ValidationLevel.WARNING,
                "Re",
                "Very high Re",
                value=Re,
                expected="< 1e7",
            )

        # Flow regime info
        if 2300 < Re < 4000:
            result.add_issue(
                ValidationLevel.INFO, "Re", "Transitional flow regime", value=Re
            )

        return result


class ConsistencyValidator:
    """Validates consistency between related parameters."""

    @staticmethod
    def validate_energy_balance(
        power_generated: float, power_removed: float, tolerance: float = 0.05
    ) -> ValidationResult:
        """Check energy balance."""
        result = ValidationResult(valid=True)

        error = abs(power_generated - power_removed) / power_generated

        if error > tolerance:
            result.add_issue(
                ValidationLevel.ERROR,
                "energy_balance",
                f"Mismatch > {tolerance*100}%",
                value=f"{error*100:.2f}%",
            )
        elif error > tolerance / 2:
            result.add_issue(
                ValidationLevel.WARNING,
                "energy_balance",
                "Small imbalance",
                value=f"{error*100:.2f}%",
            )

        return result

    @staticmethod
    def validate_material_conservation(
        mass_in: float,
        mass_out: float,
        mass_accumulated: float,
        tolerance: float = 1e-6,
    ) -> ValidationResult:
        """Check mass conservation."""
        result = ValidationResult(valid=True)

        balance = mass_in - mass_out - mass_accumulated
        relative_error = abs(balance) / max(mass_in, 1e-10)

        if relative_error > tolerance:
            result.add_issue(
                ValidationLevel.ERROR,
                "mass_balance",
                "Conservation violated",
                value=f"{relative_error:.2e}",
            )

        return result


class DataValidator:
    """Main validation coordinator."""

    def __init__(self):
        self.console = Console()
        self.physical = PhysicalValidator()
        self.geometry = GeometryValidator()
        self.neutronics = NeutronicsValidator()
        self.thermal = ThermalValidator()
        self.consistency = ConsistencyValidator()

    def validate_reactor_spec(self, spec) -> ValidationResult:
        """Validate complete reactor specification."""
        result = ValidationResult(valid=True)

        # Physical parameters
        temp_result = self.physical.validate_temperature(
            spec.inlet_temperature, "inlet_temperature", min_T=273, max_T=900
        )
        result.issues.extend(temp_result.issues)

        temp_result = self.physical.validate_temperature(
            spec.outlet_temperature, "outlet_temperature", min_T=300, max_T=1200
        )
        result.issues.extend(temp_result.issues)

        # Check inlet < outlet
        if spec.inlet_temperature >= spec.outlet_temperature:
            result.add_issue(
                ValidationLevel.ERROR, "temperatures", "Inlet >= Outlet (non-physical)"
            )

        press_result = self.physical.validate_pressure(
            spec.primary_pressure, "primary_pressure"
        )
        result.issues.extend(press_result.issues)

        enr_result = self.physical.validate_enrichment(spec.enrichment, spec.fuel_type)
        result.issues.extend(enr_result.issues)

        power_result = self.physical.validate_power(
            spec.power_thermal,
            spec.reactor_type.value if hasattr(spec, "reactor_type") else "SMR",
        )
        result.issues.extend(power_result.issues)

        # Geometry
        geom_result = self.geometry.validate_dimensions(
            spec.core_height, spec.core_diameter
        )
        result.issues.extend(geom_result.issues)

        # Update validity
        result.valid = not result.has_errors()

        return result

    def validate_solver_inputs(self, geometry, xs_data, options) -> ValidationResult:
        """Validate solver inputs."""
        result = ValidationResult(valid=True)

        # Mesh validation
        mesh_result = self.geometry.validate_mesh(
            len(geometry.radial_mesh) - 1, len(geometry.axial_mesh) - 1
        )
        result.issues.extend(mesh_result.issues)

        # Cross sections
        xs_result = self.neutronics.validate_cross_sections(xs_data)
        result.issues.extend(xs_result.issues)

        # Solver options
        if options.tolerance < 1e-10:
            result.add_issue(
                ValidationLevel.WARNING,
                "tolerance",
                "Very tight tolerance (slow)",
                value=options.tolerance,
            )

        if options.tolerance > 1e-3:
            result.add_issue(
                ValidationLevel.WARNING,
                "tolerance",
                "Loose tolerance (inaccurate)",
                value=options.tolerance,
            )

        if options.max_iterations < 10:
            result.add_issue(
                ValidationLevel.WARNING,
                "max_iterations",
                "May not converge",
                value=options.max_iterations,
            )

        result.valid = not result.has_errors()

        return result

    def validate_solution(
        self, k_eff: float, flux: np.ndarray, power: np.ndarray, power_target: float
    ) -> ValidationResult:
        """Validate solution results."""
        result = ValidationResult(valid=True)

        # k-eff
        k_result = self.physical.validate_k_eff(k_eff)
        result.issues.extend(k_result.issues)

        # Flux
        flux_result = self.neutronics.validate_flux(flux, power_target)
        result.issues.extend(flux_result.issues)

        # Power
        total_power = np.sum(power)
        power_error = abs(total_power - power_target) / power_target

        if power_error > 0.01:
            result.add_issue(
                ValidationLevel.WARNING,
                "power_normalization",
                "Power normalization error",
                value=f"{power_error*100:.2f}%",
            )

        result.valid = not result.has_errors()

        return result


if __name__ == "__main__":
    console = Console()
    console.print("[bold cyan]Data Validation Framework Demo[/bold cyan]\n")

    # Test validations
    validator = DataValidator()

    # Test 1: Valid parameters
    console.print("[bold]Test 1: Valid Parameters[/bold]")
    result1 = validator.physical.validate_temperature(1200.0, "fuel_temp")
    result1.print_report()

    # Test 2: Invalid parameters
    console.print("\n[bold]Test 2: Invalid Parameters[/bold]")
    result2 = validator.physical.validate_temperature(-50.0, "bad_temp")
    result2.print_report()

    # Test 3: Cross section validation
    console.print("\n[bold]Test 3: Cross Section Data[/bold]")
    from smrforge.neutronics.solver import CrossSectionData

    # Create test data with intentional error
    xs_test = CrossSectionData(
        n_groups=2,
        n_materials=1,
        sigma_t=np.array([[0.5, 0.8]]),
        sigma_a=np.array([[0.1, 0.6]]),  # Last value > total (error)
        sigma_f=np.array([[0.05, 0.5]]),
        nu_sigma_f=np.array([[0.125, 1.25]]),
        sigma_s=np.array([[[0.4, 0.01], [0.0, 0.2]]]),
        chi=np.array([[1.0, 0.0]]),
        D=np.array([[1.5, 0.4]]),
    )

    result3 = validator.neutronics.validate_cross_sections(xs_test)
    result3.print_report()

    console.print("\n[bold green]Validation framework ready![/bold green]")
