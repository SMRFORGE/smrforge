"""
Regulatory traceability and audit trail functionality.

Provides capabilities for:
- Calculation audit trails (input → output traceability)
- Model assumption documentation
- Safety margin reporting
- BEPU (Best Estimate Plus Uncertainty) methodology support

Supports alignment with regulatory standards:
- 10 CFR Part 50/52 (US NRC) - safety analysis, design basis
- IAEA Safety Standards - international guidance
- ANSI/ANS standards - decay heat, benchmarks
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.logging import get_logger

logger = get_logger("smrforge.validation.regulatory_traceability")


@dataclass
class ModelAssumption:
    """
    Model assumption documentation.

    Attributes:
        category: Assumption category (e.g., "neutronics", "thermal", "fuel")
        assumption: Description of the assumption
        justification: Justification for the assumption
        impact: Impact if assumption is violated
        uncertainty: Uncertainty associated with assumption
    """

    category: str
    assumption: str
    justification: Optional[str] = None
    impact: Optional[str] = None
    uncertainty: Optional[float] = None


@dataclass
class CalculationAuditTrail:
    """
    Audit trail for a calculation, tracking inputs and outputs.

    Provides full traceability from inputs to outputs for regulatory compliance.

    Attributes:
        calculation_id: Unique identifier for the calculation
        calculation_type: Type of calculation (e.g., "keff", "burnup", "transient")
        timestamp: Calculation timestamp
        inputs: Input parameters (reactor spec, solver options, etc.)
        outputs: Output results (k-eff, power distribution, etc.)
        assumptions: Model assumptions used
        solver_info: Solver version and configuration
        metadata: Additional metadata (user, computer, etc.)
        ai_models_used: AI/ML models used (name, version, config_hash) for audit.
    """

    calculation_id: str
    calculation_type: str
    timestamp: datetime
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    assumptions: List[ModelAssumption] = field(default_factory=list)
    solver_info: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    ai_models_used: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit trail to dictionary for serialization."""
        return {
            "calculation_id": self.calculation_id,
            "calculation_type": self.calculation_type,
            "timestamp": self.timestamp.isoformat(),
            "inputs": self._serialize_dict(self.inputs),
            "outputs": self._serialize_dict(self.outputs),
            "assumptions": [
                {
                    "category": a.category,
                    "assumption": a.assumption,
                    "justification": a.justification,
                    "impact": a.impact,
                    "uncertainty": a.uncertainty,
                }
                for a in self.assumptions
            ],
            "solver_info": self.solver_info,
            "metadata": self.metadata,
            "ai_models_used": self.ai_models_used,
        }

    def _serialize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize dictionary, handling numpy arrays and complex types."""
        serialized = {}
        for key, value in data.items():
            if hasattr(value, "model_dump"):  # Pydantic models
                serialized[key] = value.model_dump()
            elif hasattr(value, "tolist"):  # NumPy arrays
                serialized[key] = value.tolist()
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                serialized[key] = self._serialize_dict(value)
            elif isinstance(value, list):
                serialized[key] = [
                    v.tolist() if hasattr(v, "tolist") else v for v in value
                ]
            else:
                serialized[key] = value
        return serialized

    def save(self, filepath: Path):
        """
        Save audit trail to JSON file.

        Args:
            filepath: Path to save audit trail JSON file

        Raises:
            OSError: If file cannot be written.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

        logger.info(f"Audit trail saved: {filepath}")

    @classmethod
    def load(cls, filepath: Path) -> "CalculationAuditTrail":
        """
        Load audit trail from JSON file.

        Args:
            filepath: Path to audit trail JSON file

        Returns:
            CalculationAuditTrail instance

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If file format is invalid.
        """
        with open(filepath, "r") as f:
            data = json.load(f)

        # Convert timestamp
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        # Convert assumptions
        data["assumptions"] = [
            ModelAssumption(**a) for a in data.get("assumptions", [])
        ]
        data.setdefault("ai_models_used", [])

        return cls(**data)


@dataclass
class SafetyMargin:
    """
    Safety margin calculation for a parameter.

    Attributes:
        parameter: Parameter name (e.g., "fuel_temperature", "power_peak")
        calculated_value: Calculated value
        limit: Design limit or constraint
        margin: Safety margin (limit - calculated_value) or (limit/calculated_value - 1)
        margin_percent: Safety margin as percentage
        units: Units for the parameter
    """

    parameter: str
    calculated_value: float
    limit: float
    margin: float
    margin_percent: float
    units: str

    @classmethod
    def calculate_absolute(
        cls, parameter: str, calculated: float, limit: float, units: str
    ) -> "SafetyMargin":
        """Calculate absolute safety margin (limit - calculated)."""
        margin = limit - calculated
        margin_percent = (margin / limit) * 100.0 if limit != 0 else 0.0
        return cls(
            parameter=parameter,
            calculated_value=calculated,
            limit=limit,
            margin=margin,
            margin_percent=margin_percent,
            units=units,
        )

    @classmethod
    def calculate_relative(
        cls, parameter: str, calculated: float, limit: float, units: str
    ) -> "SafetyMargin":
        """Calculate relative safety margin ((limit/calculated - 1) * 100%)."""
        if calculated == 0:
            raise ValueError("Calculated value cannot be zero for relative margin")
        margin_ratio = limit / calculated
        margin_percent = (margin_ratio - 1.0) * 100.0
        margin = margin_percent / 100.0 * calculated
        return cls(
            parameter=parameter,
            calculated_value=calculated,
            limit=limit,
            margin=margin,
            margin_percent=margin_percent,
            units=units,
        )


@dataclass
class SafetyMarginReport:
    """
    Safety margin report for regulatory compliance.

    Provides automated safety margin calculations for key reactor parameters.

    Attributes:
        calculation_id: Associated calculation ID
        timestamp: Report timestamp
        margins: List of safety margins
        summary: Summary statistics (number passing/failing)
    """

    calculation_id: str
    timestamp: datetime
    margins: List[SafetyMargin] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def add_margin(self, margin: SafetyMargin):
        """Add a safety margin to the report."""
        self.margins.append(margin)
        self._update_summary()

    def _update_summary(self):
        """Update summary statistics."""
        if not self.margins:
            self.summary = {
                "total_margins": 0,
                "passing": 0,
                "failing": 0,
                "min_margin_percent": None,
            }
            return

        passing = sum(1 for m in self.margins if m.margin > 0)
        failing = len(self.margins) - passing
        min_margin = (
            min(m.margin_percent for m in self.margins) if self.margins else None
        )

        self.summary = {
            "total_margins": len(self.margins),
            "passing": passing,
            "failing": failing,
            "min_margin_percent": min_margin,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "calculation_id": self.calculation_id,
            "timestamp": self.timestamp.isoformat(),
            "margins": [
                {
                    "parameter": m.parameter,
                    "calculated_value": m.calculated_value,
                    "limit": m.limit,
                    "margin": m.margin,
                    "margin_percent": m.margin_percent,
                    "units": m.units,
                }
                for m in self.margins
            ],
            "summary": self.summary,
        }

    def save(self, filepath: Path):
        """
        Save safety margin report to JSON file.

        Args:
            filepath: Path to save report JSON file

        Raises:
            OSError: If file cannot be written.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

        logger.info(f"Safety margin report saved: {filepath}")

    def _format_margin(self, value: Any) -> str:
        """Format margin value for display."""
        if isinstance(value, str) or value is None:
            return str(value) if value is not None else "N/A"
        try:
            return f"{float(value):.2f}"
        except (ValueError, TypeError):
            return str(value)

    def to_text(self) -> str:
        """
        Generate human-readable text report.

        Returns:
            Formatted text report string
        """
        lines = [
            "=" * 70,
            "SAFETY MARGIN REPORT",
            "=" * 70,
            f"Calculation ID: {self.calculation_id}",
            f"Timestamp: {self.timestamp.isoformat()}",
            "",
            "Summary:",
            f"  Total margins evaluated: {self.summary.get('total_margins', 0)}",
            f"  Passing: {self.summary.get('passing', 0)}",
            f"  Failing: {self.summary.get('failing', 0)}",
            f"  Minimum margin: {self._format_margin(self.summary.get('min_margin_percent', 'N/A'))}%",
            "",
            "Detailed Margins:",
            "-" * 70,
        ]

        for margin in self.margins:
            status = "✓ PASS" if margin.margin > 0 else "✗ FAIL"
            lines.append(
                f"{status} | {margin.parameter:30s} | "
                f"Value: {margin.calculated_value:10.3f} {margin.units:8s} | "
                f"Limit: {margin.limit:10.3f} {margin.units:8s} | "
                f"Margin: {margin.margin_percent:+7.2f}%"
            )

        lines.append("=" * 70)

        return "\n".join(lines)


def create_audit_trail(
    calculation_type: str,
    inputs: Dict[str, Any],
    outputs: Dict[str, Any],
    assumptions: Optional[List[ModelAssumption]] = None,
    calculation_id: Optional[str] = None,
    ai_models_used: Optional[List[Dict[str, Any]]] = None,
    **metadata,
) -> CalculationAuditTrail:
    """
    Create calculation audit trail.

    Convenience function for creating audit trails with automatic ID generation.

    Args:
        calculation_type: Type of calculation (e.g., "keff", "burnup", "transient")
        inputs: Input parameters dictionary
        outputs: Output results dictionary
        assumptions: Model assumptions (optional)
        calculation_id: Unique calculation ID (auto-generated if None)
        ai_models_used: AI/ML models used (list of {"name", "version", "config_hash", ...})
        **metadata: Additional metadata (user, computer, solver_version, etc.)

    Returns:
        CalculationAuditTrail instance

    Example:
        >>> from smrforge.validation.regulatory_traceability import (
        ...     create_audit_trail, ModelAssumption
        ... )
        >>>
        >>> # Define assumptions
        >>> assumptions = [
        ...     ModelAssumption(
        ...         category="neutronics",
        ...         assumption="Diffusion approximation valid",
        ...         justification="Large core, low leakage",
        ...         impact="May underestimate flux gradients"
        ...     )
        ... ]
        >>>
        >>> # Create audit trail
        >>> trail = create_audit_trail(
        ...     calculation_type="keff",
        ...     inputs={"reactor_spec": spec.model_dump(), "solver_options": opts.model_dump()},
        ...     outputs={"k_eff": 1.00234, "flux": flux.tolist()},
        ...     assumptions=assumptions,
        ...     solver_version="0.1.0"
        ... )
        >>>
        >>> # Save audit trail
        >>> trail.save("audit_trails/keff_calc_001.json")
    """
    if calculation_id is None:
        # Generate ID from timestamp
        timestamp = datetime.now()
        calculation_id = f"{calculation_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}"

    # Get solver info from metadata or defaults
    solver_info = {
        "version": metadata.pop("solver_version", "unknown"),
        "method": metadata.pop("solver_method", "unknown"),
    }

    return CalculationAuditTrail(
        calculation_id=calculation_id,
        calculation_type=calculation_type,
        timestamp=datetime.now(),
        inputs=inputs,
        outputs=outputs,
        assumptions=assumptions or [],
        solver_info=solver_info,
        metadata=metadata,
        ai_models_used=ai_models_used or [],
    )


def generate_safety_margins_from_reactor(
    reactor_spec,
    calculated_results: Dict[str, float],
) -> SafetyMarginReport:
    """
    Generate safety margin report from reactor specification and results.

    Automatically calculates safety margins for key reactor parameters:
    - Fuel temperature (max_fuel_temperature limit)
    - Power density (design limits)
    - Reactivity margins (shutdown margin)

    Args:
        reactor_spec: ReactorSpecification object
        calculated_results: Dictionary of calculated values
            - "max_fuel_temperature": Maximum fuel temperature [K]
            - "peak_power_density": Peak power density [W/m³]
            - "k_eff": k-effective value
            - etc.

    Returns:
        SafetyMarginReport with calculated margins

    Example:
        >>> from smrforge.validation.regulatory_traceability import (
        ...     generate_safety_margins_from_reactor
        ... )
        >>>
        >>> # After calculation
        >>> results = {
        ...     "max_fuel_temperature": 1873.0,  # K
        ...     "peak_power_density": 15.5e6,  # W/m³
        ...     "k_eff": 1.00234,
        ... }
        >>>
        >>> report = generate_safety_margins_from_reactor(reactor_spec, results)
        >>>
        >>> # Print report
        >>> print(report.to_text())
        >>>
        >>> # Save report
        >>> report.save("safety_margins/report_001.json")
    """
    # Ensure calculation_id is a string
    calc_id = calculated_results.get("calculation_id", "unknown")
    calc_id_str = str(calc_id) if calc_id is not None else "unknown"

    report = SafetyMarginReport(
        calculation_id=calc_id_str,
        timestamp=datetime.now(),
    )

    # Fuel temperature margin
    if "max_fuel_temperature" in calculated_results:
        calc_temp = calculated_results["max_fuel_temperature"]
        limit_temp = reactor_spec.max_fuel_temperature
        margin = SafetyMargin.calculate_absolute(
            "max_fuel_temperature",
            calc_temp,
            limit_temp,
            "K",
        )
        report.add_margin(margin)

    # Reactivity margin (shutdown margin)
    if "k_eff" in calculated_results and hasattr(reactor_spec, "shutdown_margin"):
        k_eff = calculated_results["k_eff"]
        shutdown_k = 1.0 - reactor_spec.shutdown_margin  # k-eff for shutdown margin
        margin = SafetyMargin.calculate_relative(
            "shutdown_margin",
            k_eff,
            shutdown_k,
            "dk/k",
        )
        # For shutdown margin, negative margin is good (k_eff < shutdown_k)
        margin.margin = shutdown_k - k_eff
        margin.margin_percent = -margin.margin_percent
        report.add_margin(margin)

    # Power density margin (if limit is defined)
    if "peak_power_density" in calculated_results:
        # Typical limit for HTGR: ~20 MW/m³
        # This could be in reactor_spec or use default
        limit_power_density = getattr(reactor_spec, "max_power_density", 20e6)  # W/m³
        calc_power_density = calculated_results["peak_power_density"]
        margin = SafetyMargin.calculate_absolute(
            "peak_power_density",
            calc_power_density,
            limit_power_density,
            "W/m³",
        )
        report.add_margin(margin)

    return report
