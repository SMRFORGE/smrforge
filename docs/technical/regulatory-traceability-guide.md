# Regulatory Traceability and Audit Trail Guide

**Date:** January 2026  
**Purpose:** Guide for using SMRForge's regulatory traceability features for licensing and compliance

---

## Overview

SMRForge provides comprehensive regulatory traceability features to support licensing applications and regulatory compliance. These features ensure:

- **Input → Output Traceability:** Complete audit trail of all calculations
- **Assumption Documentation:** Explicit documentation of model assumptions
- **Safety Margin Reporting:** Automated calculation of safety margins
- **BEPU Support:** Best Estimate Plus Uncertainty methodology support

---

## 1. Calculation Audit Trails

### Purpose

Audit trails provide complete traceability from inputs to outputs, which is essential for:
- Regulatory review
- Code verification
- Quality assurance
- Repeatability

### Basic Usage

```python
from smrforge.validation.regulatory_traceability import (
    create_audit_trail,
    ModelAssumption
)
import smrforge as smr

# Define model assumptions
assumptions = [
    ModelAssumption(
        category="neutronics",
        assumption="Diffusion approximation valid for large cores",
        justification="Core diameter > 100 cm, low leakage",
        impact="May underestimate flux gradients near boundaries",
        uncertainty=0.02  # ±2% estimated
    ),
    ModelAssumption(
        category="thermal",
        assumption="Constant coolant properties",
        justification="Narrow temperature range (823-1023 K)",
        impact="Small error in heat transfer"
    )
]

# Run calculation
reactor = smr.create_reactor("valar-10")
results = reactor.solve_keff()

# Create audit trail
trail = create_audit_trail(
    calculation_type="keff",
    inputs={
        "reactor_spec": reactor.spec.model_dump(),
        "solver_options": reactor.solver.options.model_dump(),
    },
    outputs={
        "k_eff": results["k_eff"],
        "flux": results["flux"].tolist(),
    },
    assumptions=assumptions,
    solver_version=smr.__version__,
    user="engineer_name",
    computer="workstation_01"
)

# Save audit trail
trail.save("audit_trails/keff_20260101_001.json")
```

### Loading Audit Trails

```python
from smrforge.validation.regulatory_traceability import CalculationAuditTrail

# Load previously saved audit trail
trail = CalculationAuditTrail.load("audit_trails/keff_20260101_001.json")

print(f"Calculation: {trail.calculation_id}")
print(f"Type: {trail.calculation_type}")
print(f"Timestamp: {trail.timestamp}")
print(f"Assumptions: {len(trail.assumptions)}")
```

---

## 2. Safety Margin Reports

### Purpose

Safety margin reports automatically calculate margins between calculated values and design limits, which is critical for:
- Safety analysis
- Regulatory compliance
- Design optimization
- Risk assessment

### Basic Usage

```python
from smrforge.validation.regulatory_traceability import (
    generate_safety_margins_from_reactor,
    SafetyMargin
)

# After calculation
reactor = smr.create_reactor("valar-10")
results = reactor.solve_keff()
thermal_results = reactor.solve_thermal()

# Collect calculated values
calculated = {
    "max_fuel_temperature": thermal_results["max_temperature"],  # K
    "peak_power_density": thermal_results["peak_power_density"],  # W/m³
    "k_eff": results["k_eff"],
}

# Generate safety margin report
report = generate_safety_margins_from_reactor(
    reactor_spec=reactor.spec,
    calculated_results=calculated
)

# Print human-readable report
print(report.to_text())

# Save report
report.save("safety_margins/report_001.json")
```

### Custom Safety Margins

```python
from smrforge.validation.regulatory_traceability import (
    SafetyMargin,
    SafetyMarginReport
)
from datetime import datetime

# Create custom report
report = SafetyMarginReport(
    calculation_id="calc_001",
    timestamp=datetime.now()
)

# Add custom margins
margin1 = SafetyMargin.calculate_absolute(
    "fuel_temperature",
    calculated=1873.0,  # K
    limit=1973.0,  # K (design limit)
    units="K"
)
report.add_margin(margin1)

margin2 = SafetyMargin.calculate_relative(
    "reactivity_margin",
    calculated=1.00234,  # k-eff
    limit=0.95,  # shutdown margin k-eff
    units="dk/k"
)
report.add_margin(margin2)

# Check summary
print(f"Total margins: {report.summary['total_margins']}")
print(f"Passing: {report.summary['passing']}")
print(f"Failing: {report.summary['failing']}")
```

---

## 3. Model Assumptions Documentation

### Purpose

Documenting model assumptions is essential for:
- Transparent calculations
- Uncertainty quantification
- Regulatory review
- Method validation

### Best Practices

1. **Document All Assumptions:**
   - Physical models (diffusion, transport, etc.)
   - Numerical methods (discretization, convergence)
   - Material properties (temperature dependence, etc.)
   - Boundary conditions

2. **Include Justification:**
   - Why the assumption is valid
   - Under what conditions it holds
   - Literature references if applicable

3. **Quantify Uncertainty:**
   - Estimated uncertainty from assumption
   - Impact on results
   - Sensitivity to assumption violation

### Example: Complete Assumption Set

```python
from smrforge.validation.regulatory_traceability import ModelAssumption

assumptions = [
    # Neutronics assumptions
    ModelAssumption(
        category="neutronics",
        assumption="Multi-group diffusion approximation",
        justification="Large core (>100 cm), low leakage, validated for HTGRs",
        impact="Flux gradients near boundaries may be underestimated",
        uncertainty=0.02
    ),
    
    # Thermal assumptions
    ModelAssumption(
        category="thermal",
        assumption="Constant coolant properties (Helium)",
        justification="Narrow temperature range (823-1023 K), properties vary <5%",
        impact="Small error in heat transfer coefficient",
        uncertainty=0.01
    ),
    
    # Material property assumptions
    ModelAssumption(
        category="materials",
        assumption="Temperature-independent thermal conductivity",
        justification="Graphite conductivity varies <10% in operating range",
        impact="Temperature distribution may have small error",
        uncertainty=0.03
    ),
    
    # Numerical method assumptions
    ModelAssumption(
        category="numerical",
        assumption="Power iteration convergence tolerance: 1e-6",
        justification="Standard tolerance for eigenvalue problems",
        impact="k-eff accurate to ~0.0001",
        uncertainty=0.0001
    ),
]
```

---

## 4. BEPU Methodology

### Best Estimate Plus Uncertainty (BEPU)

BEPU methodology combines best-estimate calculations with uncertainty quantification to demonstrate safety margins.

### BEPU Workflow

```python
from smrforge.uncertainty.uq import MonteCarloSampling
from smrforge.validation.regulatory_traceability import (
    create_audit_trail,
    generate_safety_margins_from_reactor
)
import numpy as np

# 1. Define uncertainty distributions for inputs
input_distributions = {
    "enrichment": ("normal", 0.195, 0.01),  # mean, std
    "power": ("normal", 10e6, 0.5e6),  # W
    "temperature_coefficient": ("normal", -3.5e-5, 0.5e-5),
}

# 2. Run uncertainty quantification
uq = MonteCarloSampling(n_samples=1000)
samples = uq.sample(input_distributions)

results = []
for sample in samples:
    # Create reactor with sampled parameters
    reactor = create_reactor(
        enrichment=sample["enrichment"],
        power_mw=sample["power"] / 1e6
    )
    
    # Run calculation
    result = reactor.solve_keff()
    results.append(result["k_eff"])

# 3. Calculate statistics
mean_keff = np.mean(results)
std_keff = np.std(results)
p95_keff = np.percentile(results, 95)  # 95th percentile

# 4. Generate safety margin using 95th percentile
report = generate_safety_margins_from_reactor(
    reactor_spec=reactor.spec,
    calculated_results={
        "k_eff": p95_keff,  # Use 95th percentile for conservative margin
        "max_fuel_temperature": np.percentile(temperatures, 95),
    }
)

# 5. Create audit trail with UQ results
trail = create_audit_trail(
    calculation_type="bepu_keff",
    inputs={
        "uncertainty_distributions": input_distributions,
        "n_samples": 1000,
        "reactor_spec": reactor.spec.model_dump(),
    },
    outputs={
        "mean_k_eff": mean_keff,
        "std_k_eff": std_keff,
        "p95_k_eff": p95_keff,
        "safety_margin": report.summary,
    },
    assumptions=assumptions,
    methodology="BEPU",
)
```

---

## 5. Integration with Validation Framework

### Combining with Benchmarks

```python
from smrforge.validation.benchmarking import ValidationBenchmarker
from smrforge.validation.regulatory_traceability import create_audit_trail

# Run validation benchmark
benchmarker = ValidationBenchmarker()
validation_result = benchmarker.compare_with_benchmark(
    calculation_result=results,
    benchmark_name="IAEA_3D_BENCHMARK"
)

# Include validation in audit trail
trail = create_audit_trail(
    calculation_type="keff",
    inputs={...},
    outputs={
        "k_eff": results["k_eff"],
        "validation": {
            "benchmark": "IAEA_3D_BENCHMARK",
            "benchmark_value": validation_result.benchmark_value,
            "difference": validation_result.difference,
            "within_tolerance": validation_result.within_tolerance,
        }
    },
    assumptions=assumptions,
)
```

---

## 6. Regulatory Compliance Checklist

When preparing calculations for regulatory submission:

- [ ] **Audit Trail Created:** All calculations have audit trails
- [ ] **Assumptions Documented:** All model assumptions are explicitly documented
- [ ] **Safety Margins Calculated:** Key safety margins are calculated and reported
- [ ] **Validation Performed:** Calculations validated against benchmarks where available
- [ ] **Uncertainty Quantified:** BEPU methodology applied for safety calculations
- [ ] **Documentation Complete:** All relevant documentation attached to audit trail
- [ ] **Version Control:** Solver and library versions documented
- [ ] **Reproducibility:** Calculation can be reproduced from audit trail

---

## 7. File Organization

Recommended directory structure for regulatory submissions:

```
regulatory_submission/
├── audit_trails/
│   ├── keff_20260101_001.json
│   ├── burnup_20260101_002.json
│   └── transient_20260101_003.json
├── safety_margins/
│   ├── report_001.json
│   └── report_001.txt
├── assumptions/
│   └── model_assumptions_20260101.md
├── validation/
│   └── benchmark_comparisons.json
└── documentation/
    ├── calculation_procedures.md
    └── bepu_methodology.md
```

---

## 8. Example: Complete Regulatory Workflow

```python
"""
Complete workflow for regulatory-compliant calculation.
"""

from smrforge.validation.regulatory_traceability import (
    create_audit_trail,
    generate_safety_margins_from_reactor,
    ModelAssumption
)
import smrforge as smr

# 1. Define assumptions upfront
assumptions = [
    ModelAssumption(
        category="neutronics",
        assumption="Multi-group diffusion (4 groups)",
        justification="Validated for HTGR geometries",
    ),
    # ... more assumptions
]

# 2. Run calculation
reactor = smr.create_reactor("valar-10")
neutronics_results = reactor.solve_keff()
thermal_results = reactor.solve_thermal()

# 3. Generate safety margins
safety_report = generate_safety_margins_from_reactor(
    reactor_spec=reactor.spec,
    calculated_results={
        "k_eff": neutronics_results["k_eff"],
        "max_fuel_temperature": thermal_results["max_temperature"],
    }
)

# 4. Create audit trail
trail = create_audit_trail(
    calculation_type="safety_analysis",
    inputs={
        "reactor_spec": reactor.spec.model_dump(),
    },
    outputs={
        "neutronics": neutronics_results,
        "thermal": thermal_results,
        "safety_margins": safety_report.to_dict(),
    },
    assumptions=assumptions,
    solver_version=smr.__version__,
)

# 5. Save all documentation
trail.save("regulatory_submission/audit_trails/safety_analysis_001.json")
safety_report.save("regulatory_submission/safety_margins/report_001.json")

# 6. Print summary
print("=" * 70)
print("REGULATORY COMPLIANCE SUMMARY")
print("=" * 70)
print(f"\nCalculation ID: {trail.calculation_id}")
print(f"Assumptions documented: {len(trail.assumptions)}")
print(f"\nSafety Margins:")
print(safety_report.to_text())
```

---

## References

- NRC Regulatory Guide 1.203: Transient and Accident Analysis Methods
- ANSI/ANS-20.1: Nuclear Safety Analysis
- IAEA Safety Standards Series No. SSG-2: Deterministic Safety Analysis

---

**Status:** Implementation complete - All features available in `smrforge.validation.regulatory_traceability`
