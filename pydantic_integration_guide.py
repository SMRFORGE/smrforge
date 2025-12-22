# INTEGRATION_GUIDE.md (as Python comments)
"""
=============================================================================
PYDANTIC v2 INTEGRATION GUIDE FOR SMRFORGE
=============================================================================

This guide shows how to integrate Pydantic models with existing SMRForge code.

STEP 1: Update pyproject.toml
=============================================================================
"""

# Add to pyproject.toml:
"""
[project]
dependencies = [
    # ... existing dependencies
    "pydantic>=2.5",
    "pydantic-settings>=2.1",
    "python-dotenv>=1.0",  # For .env file loading
]
"""

"""
STEP 2: Update Existing Classes
=============================================================================
"""

# BEFORE (old dataclass approach):
"""
from dataclasses import dataclass

@dataclass
class ReactorSpec:
    power_thermal: float
    temperature: float
    
    def __post_init__(self):
        if self.power_thermal <= 0:
            raise ValueError("Power must be positive")
"""

# AFTER (Pydantic):
"""
from smrforge.validation.models import ReactorSpecification

# Just use the Pydantic model - validation is automatic!
spec = ReactorSpecification(
    name="My-Reactor",
    reactor_type="prismatic",
    power_thermal=10e6,
    # ... other fields
)

# Validation happens automatically on construction
# Invalid values raise pydantic.ValidationError with clear messages
"""

"""
STEP 3: Migrate Reference Designs
=============================================================================
"""

# BEFORE:
"""
class ValarAtomicsReactor:
    def __init__(self):
        self.spec = ReactorSpecification(...)  # Custom class
"""

# AFTER:
"""
from smrforge.validation.models import ReactorSpecification, ReactorType, FuelType

class ValarAtomicsReactor:
    def __init__(self):
        # Use Pydantic model - gets automatic validation
        self.spec = ReactorSpecification(
            name="Valar-10",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=10e6,
            power_electric=3.5e6,
            inlet_temperature=823.15,  # Auto-validates > 273.15
            outlet_temperature=1023.15,  # Auto-validates > inlet
            max_fuel_temperature=1873.15,
            primary_pressure=7.0e6,
            core_height=200.0,
            core_diameter=100.0,
            reflector_thickness=30.0,
            fuel_type=FuelType.UCO,
            enrichment=0.195,  # Auto-validates 0-100%
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,  # Auto-validates negative
            shutdown_margin=0.05,
        )
    
    # Can now serialize easily:
    def to_json(self, filepath):
        with open(filepath, 'w') as f:
            f.write(self.spec.model_dump_json(indent=2))
    
    @classmethod
    def from_json(cls, filepath):
        with open(filepath) as f:
            spec = ReactorSpecification.model_validate_json(f.read())
        reactor = cls.__new__(cls)
        reactor.spec = spec
        return reactor
"""

"""
STEP 4: Migrate Solver Classes
=============================================================================
"""

# BEFORE:
"""
class MultiGroupDiffusion:
    def __init__(self, geometry, xs_data, options):
        self.geometry = geometry
        self.xs_data = xs_data
        self.options = options
        # Manual validation...
"""

# AFTER:
"""
from smrforge.validation.models import CrossSectionData, SolverOptions

class MultiGroupDiffusion:
    def __init__(self, geometry, xs_data: CrossSectionData, 
                 options: SolverOptions):
        # Type hints + Pydantic ensures xs_data and options are valid
        self.geometry = geometry
        self.xs_data = xs_data  # Already validated by Pydantic
        self.options = options  # Already validated by Pydantic
        
        # Additional domain-specific validation if needed
        self._validate_geometry()
    
    def _validate_geometry(self):
        # Custom physics validation beyond Pydantic
        from validation.validators import DataValidator
        validator = DataValidator()
        result = validator.validate_solver_inputs(
            self.geometry, self.xs_data, self.options
        )
        if result.has_errors():
            raise ValueError(f"Geometry validation failed: {result}")
"""

"""
STEP 5: Configuration Files
=============================================================================
"""

# Create reactor_config.yaml:
"""
name: "My-HTGR"
reactor_type: "prismatic"
power_thermal: 50000000  # 50 MW
power_electric: 20000000  # 20 MW
inlet_temperature: 823.15
outlet_temperature: 1073.15
max_fuel_temperature: 1873.15
primary_pressure: 7000000
core_height: 300.0
core_diameter: 150.0
reflector_thickness: 50.0
fuel_type: "UCO"
enrichment: 0.19
heavy_metal_loading: 500.0
coolant_flow_rate: 15.0
cycle_length: 1825
capacity_factor: 0.92
target_burnup: 100.0
doppler_coefficient: -0.000035
shutdown_margin: 0.08
"""

# Load in Python:
"""
from smrforge.validation.models import load_reactor_from_yaml

spec = load_reactor_from_yaml("reactor_config.yaml")
# Automatically validated on load!
"""

"""
STEP 6: Environment-Based Settings
=============================================================================
"""

# Create .env file:
"""
SMRFORGE_CACHE_DIR=/data/smrforge/cache
SMRFORGE_OUTPUT_DIR=/results
SMRFORGE_NUCLEAR_DATA_LIBRARY=endfb8.0
SMRFORGE_N_THREADS=16
SMRFORGE_STRICT_VALIDATION=true
"""

# Use in code:
"""
from smrforge.validation.models import SMRForgeSettings

settings = SMRForgeSettings()  # Auto-loads from environment
print(settings.cache_dir)  # Path('/data/smrforge/cache')
print(settings.n_threads)  # 16
"""

"""
STEP 7: API Integration (FastAPI example)
=============================================================================
"""

# If building a web API:
"""
from fastapi import FastAPI, HTTPException
from smrforge.validation.models import ReactorSpecification

app = FastAPI()

@app.post("/analyze/")
def analyze_reactor(spec: ReactorSpecification):
    '''
    POST /analyze/
    Body: {
        "name": "Test-Reactor",
        "reactor_type": "prismatic",
        "power_thermal": 10000000,
        ... all other fields
    }
    
    Pydantic automatically:
    - Validates all fields
    - Returns 422 with detailed errors if invalid
    - Converts types (string "10000000" -> float 10000000.0)
    '''
    
    # spec is guaranteed valid here
    from smrforge.analysis import run_complete_analysis
    
    try:
        results = run_complete_analysis(spec)
        return {"status": "success", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Auto-generated OpenAPI docs at http://localhost:8000/docs
"""

"""
STEP 8: Validation Error Handling
=============================================================================
"""

# Pydantic provides detailed error messages:
"""
from pydantic import ValidationError
from smrforge.validation.models import ReactorSpecification

try:
    spec = ReactorSpecification(
        name="Bad-Reactor",
        reactor_type="prismatic",
        power_thermal=-1000,  # Negative! Invalid
        inlet_temperature=1500,
        outlet_temperature=1000,  # Less than inlet! Invalid
        # ... missing required fields!
    )
except ValidationError as e:
    print(e.json(indent=2))
    '''
    Output:
    [
      {
        "type": "greater_than",
        "loc": ["power_thermal"],
        "msg": "Input should be greater than 0",
        "input": -1000
      },
      {
        "type": "missing",
        "loc": ["max_fuel_temperature"],
        "msg": "Field required"
      },
      {
        "type": "value_error",
        "loc": ["__root__"],
        "msg": "Inlet temperature must be less than outlet"
      }
    ]
    '''
"""

"""
STEP 9: Testing with Pydantic
=============================================================================
"""

# pytest example:
"""
import pytest
from pydantic import ValidationError
from smrforge.validation.models import ReactorSpecification

def test_valid_reactor_spec():
    spec = ReactorSpecification(
        name="Test",
        reactor_type="prismatic",
        power_thermal=10e6,
        # ... all required fields
    )
    assert spec.power_thermal == 10e6
    assert spec.enrichment_class == "LEU"

def test_negative_power_rejected():
    with pytest.raises(ValidationError) as exc_info:
        ReactorSpecification(
            name="Bad",
            power_thermal=-100,
            # ...
        )
    assert "greater than 0" in str(exc_info.value)

def test_temperature_order_validated():
    with pytest.raises(ValidationError) as exc_info:
        ReactorSpecification(
            name="Bad-Temps",
            inlet_temperature=1000,
            outlet_temperature=800,  # Wrong order
            # ...
        )
    assert "Inlet temperature must be less than outlet" in str(exc_info.value)
"""

"""
STEP 10: Performance Considerations
=============================================================================
"""

# Pydantic v2 is fast, but for hot paths:
"""
from smrforge.validation.models import ReactorSpecification

# Disable validation for trusted data (use carefully!):
spec_dict = {...}  # Known valid data
spec = ReactorSpecification.model_construct(**spec_dict)
# Bypasses validation - use only for performance-critical paths

# For batch operations:
specs = [ReactorSpecification.model_validate(d) for d in data_list]
# Validates each, but Pydantic v2 is fast enough (Rust core)

# Benchmark:
import time
start = time.time()
for i in range(1000):
    spec = ReactorSpecification(...)  # Full validation
elapsed = time.time() - start
print(f"1000 validations: {elapsed:.3f} s")  # ~0.1-0.5s typical
"""

"""
STEP 11: Combining Pydantic with Custom Validators
=============================================================================
"""

# Best practice: Pydantic for data, custom for physics
"""
from smrforge.validation.models import ReactorSpecification
from smrforge.validation.validators import DataValidator, PhysicalValidator

# Step 1: Pydantic validates structure and basic bounds
spec = ReactorSpecification(...)  # Auto-validated

# Step 2: Custom validators for complex physics
validator = DataValidator()
result = validator.validate_reactor_spec(spec)

if result.has_errors():
    print("Physics validation failed:")
    result.print_report()
    raise ValueError("Invalid design")

# Step 3: Proceed with analysis
from smrforge.neutronics.solver import MultiGroupDiffusion
solver = MultiGroupDiffusion(core, xs_data, options)
k_eff, flux = solver.solve_steady_state()
"""

"""
STEP 12: Schema Generation for Documentation
=============================================================================
"""

# Auto-generate JSON Schema:
"""
from smrforge.validation.models import ReactorSpecification
import json

schema = ReactorSpecification.model_json_schema()

# Save for documentation
with open('reactor_spec_schema.json', 'w') as f:
    json.dump(schema, f, indent=2)

# Use in API documentation, form generators, etc.
# Schema includes:
# - Field types
# - Constraints (min, max, etc.)
# - Descriptions
# - Examples
"""

"""
MIGRATION CHECKLIST
=============================================================================

□ Install pydantic and pydantic-settings
□ Create validation/models.py with Pydantic models
□ Update ReactorSpecification classes to use Pydantic
□ Update solver options to use SolverOptions model
□ Update cross section data to use CrossSectionData model
□ Create SMRForgeSettings for configuration
□ Update tests to handle ValidationError
□ Add JSON/YAML loading utilities
□ Update documentation with examples
□ Add schema generation to docs build
□ Profile performance (should be fast with Pydantic v2)
□ Keep custom validators for complex physics
□ Add validation to CI/CD pipeline

BENEFITS ACHIEVED
=============================================================================

✓ Automatic validation on construction
✓ Type safety with runtime checks
✓ Clear error messages with field locations
✓ JSON/YAML serialization built-in
✓ Auto-generated API documentation
✓ Configuration file support
✓ Environment variable support
✓ 5-50x faster than pure Python validation
✓ Wide industry adoption (proven)
✓ Excellent documentation
✓ IDE autocomplete support
✓ Reduced boilerplate code
"""


# =============================================================================
# EXAMPLE: Complete Workflow with Pydantic
# =============================================================================

def complete_workflow_example():
    """Example showing complete workflow with Pydantic validation."""
    from rich.console import Console
    from smrforge.validation.models import (
        ReactorSpecification, GeometryParameters, 
        SolverOptions, SMRForgeSettings, FuelType, ReactorType
    )
    
    console = Console()
    console.print("[bold cyan]Complete Pydantic Workflow Example[/bold cyan]\n")
    
    # 1. Load settings
    settings = SMRForgeSettings()
    console.print(f"[bold]Settings:[/bold]")
    console.print(f"  Cache: {settings.cache_dir}")
    console.print(f"  Library: {settings.nuclear_data_library}")
    
    # 2. Create reactor spec (auto-validated)
    console.print("\n[bold]Creating reactor specification...[/bold]")
    try:
        spec = ReactorSpecification(
            name="Example-HTGR",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=25e6,
            power_electric=10e6,
            inlet_temperature=773.15,
            outlet_temperature=1073.15,
            max_fuel_temperature=1873.15,
            primary_pressure=7.0e6,
            core_height=250.0,
            core_diameter=120.0,
            reflector_thickness=40.0,
            fuel_type=FuelType.UCO,
            enrichment=0.19,
            heavy_metal_loading=300.0,
            coolant_flow_rate=12.0,
            cycle_length=2190,
            capacity_factor=0.93,
            target_burnup=120.0,
            doppler_coefficient=-3.2e-5,
            shutdown_margin=0.06
        )
        console.print(f"  ✓ Spec created: {spec.name}")
        console.print(f"    Power density: {spec.power_density:.2f} MW/m³")
        console.print(f"    Efficiency: {spec.thermal_efficiency*100:.1f}%")
    except Exception as e:
        console.print(f"  ✗ Validation failed: {e}")
        return
    
    # 3. Save to file
    console.print("\n[bold]Saving to JSON...[/bold]")
    from pathlib import Path
    from smrforge.validation.models import save_reactor_to_json
    save_reactor_to_json(spec, Path("example_reactor.json"))
    console.print("  ✓ Saved to example_reactor.json")
    
    # 4. Load from file
    console.print("\n[bold]Loading from JSON...[/bold]")
    from smrforge.validation.models import load_reactor_from_json
    spec_loaded = load_reactor_from_json(Path("example_reactor.json"))
    console.print(f"  ✓ Loaded: {spec_loaded.name}")
    
    # 5. Geometry parameters
    console.print("\n[bold]Creating geometry...[/bold]")
    geom = GeometryParameters(
        n_rings=4,
        lattice_pitch=38.0,
        block_height=62.5,
        n_axial_blocks=4,
        n_radial_mesh=25,
        n_axial_mesh=60
    )
    console.print(f"  ✓ Geometry: {geom.n_rings} rings, {geom.n_axial_blocks} axial")
    
    # 6. Solver options
    console.print("\n[bold]Configuring solver...[/bold]")
    options = SolverOptions(
        max_iterations=500,
        tolerance=1e-6,
        acceleration="chebyshev",
        verbose=True
    )
    console.print(f"  ✓ Solver: {options.eigen_method} method, tol={options.tolerance}")
    
    console.print("\n[bold green]All validations passed![/bold green]")
    console.print(f"\nReactor: {spec.name}")
    console.print(f"  Type: {spec.reactor_type.value}")
    console.print(f"  Power: {spec.power_thermal/1e6:.1f} MWth")
    console.print(f"  Enrichment: {spec.enrichment*100:.1f}% ({spec.enrichment_class.value})")
    console.print(f"  Core: {spec.core_height:.0f} cm H × {spec.core_diameter:.0f} cm D")
    console.print(f"  Aspect ratio: {spec.aspect_ratio:.2f}")


if __name__ == "__main__":
    complete_workflow_example()
