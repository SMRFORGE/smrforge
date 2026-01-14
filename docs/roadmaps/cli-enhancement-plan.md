# CLI Enhancement Plan for SMR Development and Simulation

**Date:** January 2026  
**Status:** Analysis and Recommendations

---

## Executive Summary

The current SMRForge CLI is minimal, providing only a `serve` command for launching the web dashboard. To make SMRForge robust for SMR development and simulation, we need a comprehensive CLI that enables users to perform common tasks from the command line without writing Python scripts.

---

## Current State Analysis

### Existing CLI Commands

1. **`smrforge serve`** - Launches web dashboard
   - Options: `--host`, `--port`, `--debug`
   - Well-implemented with good error handling

2. **`smrforge-setup-endf`** - Interactive ENDF data setup
   - Separate entry point
   - Could be integrated into main CLI

### Current Limitations

- ❌ No commands for reactor creation/analysis
- ❌ No commands for burnup calculations
- ❌ No commands for validation/testing
- ❌ No commands for data management
- ❌ No commands for batch processing
- ❌ No commands for result export
- ❌ No configuration management
- ❌ Limited help/documentation from CLI

---

## Recommended CLI Structure

### Command Organization

```
smrforge
├── serve              # Launch dashboard (existing)
├── reactor            # Reactor operations
│   ├── create         # Create reactor from preset or config
│   ├── analyze        # Run analysis (neutronics, burnup, etc.)
│   ├── compare        # Compare multiple designs
│   └── list           # List available presets
├── burnup             # Burnup/depletion operations
│   ├── run            # Run burnup calculation
│   ├── visualize      # Plot burnup results
│   └── export         # Export burnup data
├── data               # Data management
│   ├── download       # Download ENDF data
│   ├── setup          # Setup ENDF directory
│   ├── validate       # Validate ENDF files
│   └── list           # List available data
├── validate           # Validation and testing
│   ├── run            # Run validation tests
│   ├── benchmark      # Compare with benchmarks
│   └── report         # Generate validation report
├── visualize          # Visualization
│   ├── geometry       # Visualize geometry
│   ├── flux           # Plot flux distribution
│   └── burnup         # Plot burnup results
├── config             # Configuration
│   ├── show           # Show current config
│   ├── set            # Set configuration value
│   └── init           # Initialize config file
└── help               # Enhanced help system
```

---

## Detailed Command Specifications

### 1. Reactor Commands

#### `smrforge reactor create`

Create a reactor from preset or configuration file.

```bash
# Create from preset
smrforge reactor create --preset valar-10 --output reactor.json

# Create from config file
smrforge reactor create --config reactor_config.yaml --output reactor.json

# Create with custom parameters
smrforge reactor create \
    --power 10 \
    --enrichment 0.195 \
    --type htgr \
    --output reactor.json

# Create and immediately analyze
smrforge reactor create --preset valar-10 | smrforge reactor analyze
```

**Options:**
- `--preset NAME` - Use preset design
- `--config FILE` - Load from config file
- `--power FLOAT` - Thermal power [MW]
- `--enrichment FLOAT` - Fuel enrichment
- `--type TYPE` - Reactor type (htgr, pwr, bwr, fast)
- `--output FILE` - Save reactor to file
- `--format FORMAT` - Output format (json, yaml, hdf5)

#### `smrforge reactor analyze`

Run analysis on a reactor.

```bash
# Quick k-eff calculation
smrforge reactor analyze reactor.json --keff

# Full analysis
smrforge reactor analyze reactor.json --full

# Specific analysis types
smrforge reactor analyze reactor.json --neutronics --burnup --safety

# With options
smrforge reactor analyze reactor.json \
    --keff \
    --max-iterations 100 \
    --tolerance 1e-5 \
    --output results.json
```

**Options:**
- `--keff` - Calculate k-effective only
- `--neutronics` - Full neutronics analysis
- `--burnup` - Burnup calculation
- `--safety` - Safety transient analysis
- `--thermal` - Thermal-hydraulics analysis
- `--full` - Run all analyses
- `--max-iterations INT` - Solver max iterations
- `--tolerance FLOAT` - Solver tolerance
- `--output FILE` - Save results to file
- `--format FORMAT` - Output format (json, yaml, hdf5)

#### `smrforge reactor compare`

Compare multiple reactor designs.

```bash
# Compare presets
smrforge reactor compare --presets valar-10 gt-mhr-350 htr-pm-200

# Compare from files
smrforge reactor compare --reactors reactor1.json reactor2.json

# Compare with specific metrics
smrforge reactor compare --presets valar-10 gt-mhr-350 \
    --metrics keff power peak-flux \
    --output comparison.json
```

**Options:**
- `--presets NAMES` - Compare preset designs
- `--reactors FILES` - Compare reactor files
- `--metrics METRICS` - Metrics to compare
- `--output FILE` - Save comparison results

#### `smrforge reactor list`

List available preset designs.

```bash
# List all presets
smrforge reactor list

# List with details
smrforge reactor list --detailed

# Filter by type
smrforge reactor list --type htgr
```

---

### 2. Burnup Commands

#### `smrforge burnup run`

Run burnup/depletion calculation.

```bash
# Basic burnup
smrforge burnup run reactor.json \
    --time-steps 0 365 730 1095 \
    --power-density 1e6 \
    --output burnup_results.h5

# With options
smrforge burnup run reactor.json \
    --time-steps 0 365 730 \
    --power-density 1e6 \
    --adaptive-tracking \
    --nuclide-threshold 1e15 \
    --output burnup_results.h5

# From config file
smrforge burnup run --config burnup_config.yaml
```

**Options:**
- `--time-steps FLOATS` - Time steps [days]
- `--power-density FLOAT` - Power density [W/cm³]
- `--adaptive-tracking` - Enable adaptive nuclide tracking
- `--nuclide-threshold FLOAT` - Nuclide concentration threshold
- `--output FILE` - Save results
- `--format FORMAT` - Output format (hdf5, json, zarr)

#### `smrforge burnup visualize`

Visualize burnup results.

```bash
# Plot nuclide concentrations
smrforge burnup visualize burnup_results.h5 --nuclides U235 U238 Pu239

# Plot burnup over time
smrforge burnup visualize burnup_results.h5 --burnup

# Plot k-eff evolution
smrforge burnup visualize burnup_results.h5 --keff

# Export plots
smrforge burnup visualize burnup_results.h5 --keff --output keff_plot.png
```

**Options:**
- `--nuclides NAMES` - Plot specific nuclides
- `--burnup` - Plot burnup over time
- `--keff` - Plot k-eff evolution
- `--composition` - Plot composition changes
- `--output FILE` - Save plot
- `--format FORMAT` - Plot format (png, pdf, svg)

---

### 3. Data Management Commands

#### `smrforge data download`

Download ENDF nuclear data.

```bash
# Download common SMR nuclides
smrforge data download --library ENDF-B-VIII.1 --nuclide-set common_smr

# Download specific nuclides
smrforge data download --library ENDF-B-VIII.1 --nuclides U235 U238 Pu239

# With options
smrforge data download \
    --library ENDF-B-VIII.1 \
    --nuclide-set common_smr \
    --output ~/ENDF-Data \
    --max-workers 5 \
    --validate
```

**Options:**
- `--library NAME` - ENDF library (ENDF-B-VIII.1, JEFF-3.3, etc.)
- `--nuclide-set SET` - Predefined nuclide set (common_smr, actinides, etc.)
- `--nuclides NAMES` - Specific nuclides
- `--output DIR` - Output directory
- `--max-workers INT` - Parallel downloads
- `--validate` - Validate downloaded files
- `--resume` - Resume interrupted download

#### `smrforge data setup`

Interactive ENDF data setup (integrate existing `smrforge-setup-endf`).

```bash
# Interactive setup
smrforge data setup

# Non-interactive setup
smrforge data setup --endf-dir ~/ENDF-Data --library ENDF-B-VIII.1
```

#### `smrforge data validate`

Validate ENDF files.

```bash
# Validate directory
smrforge data validate --endf-dir ~/ENDF-Data

# Validate specific files
smrforge data validate --files file1.endf file2.endf

# Generate report
smrforge data validate --endf-dir ~/ENDF-Data --output validation_report.json
```

---

### 4. Validation Commands

#### `smrforge validate run`

Run validation tests.

```bash
# Run all validation tests
smrforge validate run --endf-dir ~/ENDF-B-VIII.1

# Run specific test suite
smrforge validate run --tests tsl fission-yield decay-heat

# With benchmark comparison
smrforge validate run \
    --endf-dir ~/ENDF-B-VIII.1 \
    --benchmarks benchmarks.json \
    --output validation_results.json
```

**Options:**
- `--endf-dir DIR` - ENDF directory
- `--tests NAMES` - Specific test suites
- `--benchmarks FILE` - Benchmark database
- `--output FILE` - Save results
- `--verbose` - Verbose output

#### `smrforge validate benchmark`

Compare results with benchmarks.

```bash
# Compare calculated values with benchmarks
smrforge validate benchmark \
    --results results.json \
    --benchmarks benchmarks.json \
    --output comparison.json
```

#### `smrforge validate report`

Generate validation report.

```bash
# Generate report from results
smrforge validate report \
    --results validation_results.json \
    --benchmarks benchmarks.json \
    --output report.md
```

---

### 5. Visualization Commands

#### `smrforge visualize geometry`

Visualize reactor geometry.

```bash
# Visualize from reactor file
smrforge visualize geometry reactor.json --output geometry.png

# 3D visualization
smrforge visualize geometry reactor.json --3d --output geometry.html

# Interactive viewer
smrforge visualize geometry reactor.json --interactive
```

#### `smrforge visualize flux`

Plot flux distribution.

```bash
# Plot flux from results
smrforge visualize flux results.json --output flux.png

# Plot specific energy group
smrforge visualize flux results.json --group 0 --output flux_group0.png
```

---

### 6. Configuration Commands

#### `smrforge config show`

Show current configuration.

```bash
# Show all config
smrforge config show

# Show specific setting
smrforge config show --key endf_dir
```

#### `smrforge config set`

Set configuration value.

```bash
# Set ENDF directory
smrforge config set endf_dir ~/ENDF-Data

# Set default library
smrforge config set default_library ENDF-B-VIII.1
```

#### `smrforge config init`

Initialize configuration file.

```bash
# Create default config
smrforge config init

# Create from template
smrforge config init --template production
```

---

## Implementation Recommendations

### 1. Use Click or Typer for Better UX

**Current:** Uses `argparse` (basic but functional)  
**Recommendation:** Migrate to `click` or `typer` for:
- Better help formatting
- Automatic shell completion
- Command grouping
- Better error messages
- Progress bars
- Colored output

**Example with Click:**
```python
import click

@click.group()
def cli():
    """SMRForge - Small Modular Reactor Design and Analysis Toolkit"""
    pass

@cli.group()
def reactor():
    """Reactor operations"""
    pass

@reactor.command()
@click.option('--preset', help='Preset design name')
@click.option('--output', type=click.Path(), help='Output file')
def create(preset, output):
    """Create a reactor"""
    # Implementation
    pass
```

### 2. Add Configuration Management

**Recommendation:** Use `pydantic-settings` for configuration:
- Global config file (`~/.smrforge/config.yaml`)
- Project-specific config (`.smrforge/config.yaml`)
- Environment variable support
- Validation with Pydantic

### 3. Add Progress Indicators

**Recommendation:** Use `rich` library (already a dependency):
- Progress bars for long operations
- Spinners for quick operations
- Colored output
- Tables for results

### 4. Add Result Export Formats

**Recommendation:** Support multiple formats:
- JSON (human-readable, easy to parse)
- YAML (human-readable, structured)
- HDF5 (efficient for large datasets)
- Zarr (efficient for arrays)
- CSV (for tabular data)
- Parquet (for dataframes)

### 5. Add Batch Processing

**Recommendation:** Support batch operations:
```bash
# Process multiple reactors
smrforge reactor analyze --batch reactors/*.json --output results/

# Parallel processing
smrforge reactor analyze --batch reactors/*.json --parallel --workers 4
```

### 6. Add Interactive Mode

**Recommendation:** Add interactive shell:
```bash
# Launch interactive shell
smrforge shell

# In shell:
>>> create_reactor("valar-10")
>>> analyze()
>>> visualize()
```

### 7. Add Workflow Scripts

**Recommendation:** Support workflow files:
```yaml
# workflow.yaml
steps:
  - type: create_reactor
    preset: valar-10
  - type: analyze
    keff: true
    burnup: true
  - type: visualize
    output: results/
```

Run with:
```bash
smrforge workflow run workflow.yaml
```

---

## User Experience Improvements

### 1. Better Error Messages

- Clear, actionable error messages
- Suggestions for fixing common issues
- Links to documentation

### 2. Helpful Defaults

- Sensible defaults for all options
- Auto-detection when possible (e.g., ENDF directory)
- Smart file format detection

### 3. Command Aliases

- Short aliases for common commands
- `smrforge r create` → `smrforge reactor create`
- `smrforge b run` → `smrforge burnup run`

### 4. Tab Completion

- Bash/Zsh completion scripts
- Fish shell completion
- PowerShell completion (Windows)

### 5. Examples in Help

- Show examples for each command
- Common use cases
- Best practices

---

## Implementation Priority

### Phase 1: Core Commands (High Priority)
1. ✅ `smrforge serve` - Already implemented
2. 🔴 `smrforge reactor create` - Essential for workflow
3. 🔴 `smrforge reactor analyze` - Core functionality
4. 🔴 `smrforge reactor list` - User discovery
5. 🔴 `smrforge data setup` - Integrate existing command

### Phase 2: Analysis Commands (High Priority)
6. 🔴 `smrforge burnup run` - Critical for fuel cycle analysis
7. 🔴 `smrforge validate run` - Quality assurance
8. 🟡 `smrforge reactor compare` - Design comparison

### Phase 3: Data Management (Medium Priority)
9. 🟡 `smrforge data download` - Convenience
10. 🟡 `smrforge data validate` - Data quality

### Phase 4: Visualization (Medium Priority)
11. 🟡 `smrforge visualize geometry` - Quick visualization
12. 🟡 `smrforge visualize flux` - Result visualization
13. 🟡 `smrforge burnup visualize` - Burnup plots

### Phase 5: Advanced Features (Low Priority)
14. 🟢 `smrforge config` - Configuration management
15. 🟢 `smrforge workflow` - Workflow scripts
16. 🟢 `smrforge shell` - Interactive mode
17. 🟢 Batch processing
18. 🟢 Tab completion

---

## Example Usage Scenarios

### Scenario 1: Quick Reactor Analysis

```bash
# Create and analyze in one command
smrforge reactor create --preset valar-10 | \
    smrforge reactor analyze --keff --output results.json

# View results
cat results.json | jq '.k_eff'
```

### Scenario 2: Fuel Cycle Analysis

```bash
# Create reactor
smrforge reactor create --preset valar-10 --output reactor.json

# Run burnup
smrforge burnup run reactor.json \
    --time-steps 0 365 730 1095 \
    --power-density 1e6 \
    --output burnup.h5

# Visualize results
smrforge burnup visualize burnup.h5 --keff --output keff_plot.png
```

### Scenario 3: Design Comparison

```bash
# Compare multiple designs
smrforge reactor compare \
    --presets valar-10 gt-mhr-350 htr-pm-200 \
    --metrics keff power peak-flux \
    --output comparison.json

# View comparison
smrforge reactor compare --view comparison.json
```

### Scenario 4: Validation Workflow

```bash
# Run validation
smrforge validate run \
    --endf-dir ~/ENDF-B-VIII.1 \
    --benchmarks benchmarks.json \
    --output validation.json

# Generate report
smrforge validate report \
    --results validation.json \
    --output report.md
```

---

## Technical Considerations

### 1. Backward Compatibility

- Keep existing `smrforge serve` command
- Maintain `smrforge-setup-endf` or integrate into `smrforge data setup`
- Don't break existing Python API

### 2. Performance

- Use async/parallel processing where possible
- Cache results when appropriate
- Optimize for common workflows

### 3. Error Handling

- Graceful degradation
- Clear error messages
- Recovery suggestions
- Logging for debugging

### 4. Testing

- Unit tests for each command
- Integration tests for workflows
- Test error cases
- Test with real data

---

## Next Steps

1. **Review and approve** this enhancement plan
2. **Prioritize** commands based on user needs
3. **Implement** Phase 1 commands first
4. **Gather feedback** from users
5. **Iterate** based on feedback

---

## Related Documentation

- Current CLI: `smrforge/cli.py`
- Convenience functions: `smrforge/convenience.py`
- Preset designs: `smrforge/presets/`
- Examples: `examples/`
- Workflow guide: `docs/guides/complete-workflow-examples.md`
