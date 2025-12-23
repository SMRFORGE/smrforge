# docs/generate_schemas.py
"""
Generate JSON schemas from Pydantic models for documentation.
"""

import json
from pathlib import Path
from typing import Dict, Any

from smrforge.validation.models import (
    ReactorSpecification,
    CrossSectionData,
    SolverOptions,
    GeometryParameters,
    MaterialComposition,
    TransientConditions,
    SMRForgeSettings,
)


def generate_schema(model_class, output_path: Path):
    """
    Generate JSON schema for a Pydantic model.

    Args:
        model_class: Pydantic model class
        output_path: Path to save JSON schema
    """
    schema = model_class.model_json_schema()

    # Add metadata
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = f"{model_class.__name__} Schema"
    schema["description"] = model_class.__doc__ or f"Schema for {model_class.__name__}"

    # Save to file
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)

    print(f"✓ Generated schema: {output_path}")

    return schema


def generate_markdown_docs(model_class) -> str:
    """
    Generate Markdown documentation from Pydantic model.

    Args:
        model_class: Pydantic model class

    Returns:
        Markdown documentation string
    """
    schema = model_class.model_json_schema()

    md = f"# {model_class.__name__}\n\n"

    if model_class.__doc__:
        md += f"{model_class.__doc__.strip()}\n\n"

    md += "## Fields\n\n"
    md += "| Field | Type | Required | Description |\n"
    md += "|-------|------|----------|-------------|\n"

    properties = schema.get("properties", {})
    required = schema.get("required", [])

    for field_name, field_info in properties.items():
        field_type = field_info.get("type", "any")
        is_required = "✓" if field_name in required else ""
        description = field_info.get("description", "")

        # Handle complex types
        if "anyOf" in field_info:
            types = [t.get("type", "any") for t in field_info["anyOf"]]
            field_type = " | ".join(types)

        md += f"| `{field_name}` | {field_type} | {is_required} | {description} |\n"

    md += "\n## Constraints\n\n"

    # Add constraints
    for field_name, field_info in properties.items():
        constraints = []

        if "minimum" in field_info:
            constraints.append(f"minimum: {field_info['minimum']}")
        if "maximum" in field_info:
            constraints.append(f"maximum: {field_info['maximum']}")
        if "minLength" in field_info:
            constraints.append(f"min length: {field_info['minLength']}")
        if "maxLength" in field_info:
            constraints.append(f"max length: {field_info['maxLength']}")
        if "pattern" in field_info:
            constraints.append(f"pattern: `{field_info['pattern']}`")

        if constraints:
            md += f"- **{field_name}**: {', '.join(constraints)}\n"

    # Add example
    if "examples" in schema.get("json_schema_extra", {}):
        md += "\n## Example\n\n```json\n"
        example = schema["json_schema_extra"]["examples"][0]
        md += json.dumps(example, indent=2)
        md += "\n```\n"

    return md


def generate_all_schemas(output_dir: Path):
    """Generate schemas for all Pydantic models."""
    output_dir.mkdir(parents=True, exist_ok=True)

    models = [
        ReactorSpecification,
        CrossSectionData,
        SolverOptions,
        GeometryParameters,
        MaterialComposition,
        TransientConditions,
        SMRForgeSettings,
    ]

    print(f"Generating schemas in: {output_dir}\n")

    for model in models:
        # JSON schema
        schema_path = output_dir / f"{model.__name__}.schema.json"
        generate_schema(model, schema_path)

        # Markdown docs
        md_path = output_dir / f"{model.__name__}.md"
        md_content = generate_markdown_docs(model)
        with open(md_path, "w") as f:
            f.write(md_content)
        print(f"✓ Generated docs: {md_path}")

    print(f"\n✓ Generated {len(models)} schemas and docs")


def generate_openapi_spec(output_path: Path):
    """Generate OpenAPI specification for potential API."""
    from fastapi import FastAPI
    from fastapi.openapi.utils import get_openapi

    app = FastAPI(
        title="SMRForge API",
        description="HTGR Small Modular Reactor Analysis API",
        version="0.1.0",
    )

    # Add example endpoints (these would be real in production)
    @app.post("/reactor/validate", response_model=ReactorSpecification)
    def validate_reactor(spec: ReactorSpecification):
        """Validate a reactor specification."""
        return spec

    @app.post("/analysis/neutronics")
    def run_neutronics(
        spec: ReactorSpecification, xs_data: CrossSectionData, options: SolverOptions
    ):
        """Run neutronics analysis."""
        return {"status": "success", "k_eff": 1.045}

    # Generate OpenAPI spec
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)

    print(f"✓ Generated OpenAPI spec: {output_path}")


def create_example_configs(output_dir: Path):
    """Create example configuration files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Example 1: Micro-reactor
    micro_config = {
        "name": "Micro-HTGR-Example",
        "reactor_type": "prismatic",
        "power_thermal": 1000000,
        "power_electric": 350000,
        "inlet_temperature": 773.15,
        "outlet_temperature": 1073.15,
        "max_fuel_temperature": 1873.15,
        "primary_pressure": 5000000,
        "core_height": 100.0,
        "core_diameter": 50.0,
        "reflector_thickness": 20.0,
        "fuel_type": "UCO",
        "enrichment": 0.195,
        "heavy_metal_loading": 30.0,
        "coolant_flow_rate": 1.5,
        "cycle_length": 3650,
        "capacity_factor": 0.90,
        "target_burnup": 200.0,
        "doppler_coefficient": -0.00004,
        "shutdown_margin": 0.08,
    }

    with open(output_dir / "micro_htgr_example.json", "w") as f:
        json.dump(micro_config, f, indent=2)

    # Example 2: Settings
    settings_example = """# SMRForge Settings (.env file)

# Paths
SMRFORGE_CACHE_DIR=/data/smrforge/cache
SMRFORGE_OUTPUT_DIR=./results

# Nuclear data
SMRFORGE_NUCLEAR_DATA_LIBRARY=endfb8.0

# Performance
SMRFORGE_N_THREADS=8
SMRFORGE_USE_NUMBA=true

# Validation
SMRFORGE_STRICT_VALIDATION=true
SMRFORGE_VALIDATION_WARNINGS=true

# Logging
SMRFORGE_LOG_LEVEL=INFO
"""

    with open(output_dir / "example.env", "w") as f:
        f.write(settings_example)

    print(f"✓ Created example configs in: {output_dir}")


def generate_validation_guide(output_path: Path):
    """Generate comprehensive validation guide."""
    guide = """# SMRForge Validation Guide

## Overview

SMRForge uses [Pydantic v2](https://docs.pydantic.dev/) for automatic data validation. All inputs are validated before processing, ensuring physical correctness and catching errors early.

## What Gets Validated

### Automatic Validations (Pydantic)

1. **Type Checking**: All fields must match declared types
2. **Bounds Checking**: Numeric values must be within specified ranges
3. **Required Fields**: All required fields must be provided
4. **Enum Values**: String fields must match allowed values
5. **Cross-Field**: Complex relationships between fields are validated

### Physics Validations (Custom)

Beyond Pydantic, SMRForge includes domain-specific validators:

1. **Cross Sections**: Physical relationships (σ_f ≤ σ_a ≤ σ_t)
2. **Energy Balance**: Power generation = power removal
3. **Mass Conservation**: Material balance closure
4. **Solution Quality**: NaN/Inf checks, flux positivity

## Common Validation Errors

### Error 1: Temperature Order

```python
# WRONG
spec = ReactorSpecification(
    inlet_temperature=1000.0,
    outlet_temperature=800.0  # Less than inlet!
)

# Error: Inlet temperature must be less than outlet
```

**Fix**: Ensure inlet < outlet

### Error 2: Negative Power

```python
# WRONG
spec = ReactorSpecification(
    power_thermal=-100  # Negative!
)

# Error: Input should be greater than 0
```

**Fix**: Use positive power values

### Error 3: Enrichment Out of Bounds

```python
# WRONG
spec = ReactorSpecification(
    enrichment=1.5  # 150%!
)

# Error: Input should be less than or equal to 1.0
```

**Fix**: Use enrichment in [0, 1] (fraction, not percent)

### Error 4: Non-Physical Cross Sections

```python
# WRONG
xs = CrossSectionData(
    sigma_t=np.array([[0.5]]),
    sigma_a=np.array([[0.6]])  # Greater than total!
)

# Error: Absorption XS cannot exceed total XS
```

**Fix**: Ensure σ_a ≤ σ_t everywhere

## Handling ValidationError

```python
from pydantic import ValidationError
from smrforge.validation.models import ReactorSpecification

try:
    spec = ReactorSpecification(
        # ... parameters
    )
except ValidationError as e:
    # Print human-readable error
    print(e)
    
    # Or access programmatically
    for error in e.errors():
        print(f"Field: {error['loc']}")
        print(f"Error: {error['msg']}")
        print(f"Input: {error['input']}")
```

## Validation in Tests

```python
import pytest
from pydantic import ValidationError

def test_negative_power_rejected():
    with pytest.raises(ValidationError) as exc_info:
        ReactorSpecification(power_thermal=-100)
    
    assert "greater than 0" in str(exc_info.value)
```

## Best Practices

1. **Validate Early**: Create Pydantic models as soon as you have data
2. **Handle Errors**: Use try-except to catch ValidationError
3. **Read Messages**: Pydantic gives clear, actionable error messages
4. **Use Warnings**: Pay attention to warnings for design improvements
5. **Test Validation**: Write tests that verify invalid inputs are rejected

## Disabling Validation (Advanced)

For performance-critical code with trusted data:

```python
# WARNING: Only use with fully trusted data!
spec_dict = {...}  # Known valid
spec = ReactorSpecification.model_construct(**spec_dict)
# Skips validation - use with caution!
```

## Additional Resources

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SMRForge API Reference](./api/)
- [Example Configurations](./examples/)

"""

    with open(output_path, "w") as f:
        f.write(guide)

    print(f"✓ Generated validation guide: {output_path}")


if __name__ == "__main__":
    from rich.console import Console

    console = Console()

    console.print("[bold cyan]Generating Schemas and Documentation[/bold cyan]\n")

    # Setup output directories
    docs_dir = Path("./docs")
    schemas_dir = docs_dir / "schemas"
    examples_dir = docs_dir / "examples"

    # Generate everything
    generate_all_schemas(schemas_dir)
    console.print()

    create_example_configs(examples_dir)
    console.print()

    generate_validation_guide(docs_dir / "validation_guide.md")
    console.print()

    try:
        generate_openapi_spec(docs_dir / "openapi.json")
    except ImportError:
        console.print("[yellow]⚠ FastAPI not installed, skipping OpenAPI spec[/yellow]")

    console.print("\n[bold green]✓ Documentation generation complete![/bold green]")
    console.print(f"\nGenerated files in:")
    console.print(f"  • Schemas: {schemas_dir}")
    console.print(f"  • Examples: {examples_dir}")
    console.print(f"  • Guide: {docs_dir / 'validation_guide.md'}")
