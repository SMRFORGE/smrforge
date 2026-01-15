# Manual Testing Checklist for SMRForge Features

This document provides a comprehensive checklist for manually testing all SMRForge features. Each feature has a corresponding Jupyter notebook with example code and instructions.

## Testing Overview

**Goal**: Verify that all features work as expected and generate user feedback on usability, performance, and any issues.

**Estimated Time**: 4-6 hours for complete testing

**Prerequisites**:
- SMRForge installed (`pip install -e .`)
- ENDF data set up (run `smrforge data setup` or use test data)
- Jupyter notebook installed (`pip install jupyter`)
- All dependencies installed

## Feature Categories

### 1. CLI Commands
- [ ] Basic CLI help and commands
- [ ] Reactor operations (create, list, analyze, compare)
- [ ] Data management (setup, download, validate)
- [ ] Burnup operations (run, visualize)
- [ ] Validation (run, design)
- [ ] Visualization (geometry, flux)
- [ ] Configuration management
- [ ] Interactive shell
- [ ] Workflow scripts
- [ ] Parameter sweep
- [ ] Templates
- [ ] I/O converters

**Notebook**: `testing/01_CLI_Commands.ipynb`

### 2. Reactor Creation and Analysis
- [ ] Create reactor from preset
- [ ] Create reactor from config file
- [ ] Create reactor with custom parameters
- [ ] List available presets
- [ ] Analyze reactor (keff, neutronics, full)
- [ ] Compare multiple reactor designs
- [ ] Batch analysis of multiple reactors

**Notebook**: `testing/02_Reactor_Creation_Analysis.ipynb`

### 3. Burnup Calculations
- [ ] Basic burnup calculation
- [ ] Burnup with checkpointing
- [ ] Resume from checkpoint
- [ ] Burnup visualization (k-eff evolution, burnup over time)
- [ ] Custom burnup options (time steps, power density, adaptive tracking)

**Notebook**: `testing/03_Burnup_Calculations.ipynb`

### 4. Parameter Sweep Workflow
- [ ] Single parameter sweep
- [ ] Multi-parameter sweep
- [ ] Parallel execution
- [ ] Results analysis and export
- [ ] Sensitivity analysis

**Notebook**: `testing/04_Parameter_Sweep.ipynb`

### 5. Template Library System
- [ ] Create template from preset
- [ ] Create template from existing reactor
- [ ] Instantiate template with defaults
- [ ] Instantiate template with overrides
- [ ] Validate template
- [ ] Save and load templates

**Notebook**: `testing/05_Template_Library.ipynb`

### 6. Design Constraints & Validation
- [ ] Create constraint set (regulatory limits, safety margins)
- [ ] Validate reactor design against constraints
- [ ] Warning vs error classification
- [ ] Multiple constraint types (k-eff, power density, etc.)

**Notebook**: `testing/06_Design_Constraints.ipynb`

### 7. I/O Converters
- [ ] Convert to Serpent format
- [ ] Convert to OpenMC format
- [ ] Convert from Serpent format (if available)
- [ ] Convert from OpenMC format (if available)
- [ ] Verify output file formats

**Notebook**: `testing/07_IO_Converters.ipynb`

### 8. Data Management
- [ ] ENDF data setup (interactive)
- [ ] ENDF data download
- [ ] ENDF data validation
- [ ] Bulk ENDF file organization
- [ ] Data directory scanning

**Notebook**: `testing/08_Data_Management.ipynb`

### 9. Validation Framework
- [ ] Run validation tests
- [ ] Compare with benchmarks
- [ ] Generate validation reports
- [ ] k-eff benchmarking
- [ ] Decay heat validation
- [ ] Burnup validation

**Notebook**: `testing/09_Validation_Framework.ipynb`

### 10. Visualization
- [ ] Geometry visualization (2D/3D)
- [ ] Flux distribution plots
- [ ] Burnup plots
- [ ] Interactive 3D viewers
- [ ] Multiple backends (Matplotlib, Plotly, PyVista)

**Notebook**: `testing/10_Visualization.ipynb`

### 11. Workflow Scripts
- [ ] Create YAML workflow
- [ ] Run workflow script
- [ ] Workflow with multiple steps
- [ ] Workflow context passing
- [ ] Error handling in workflows

**Notebook**: `testing/11_Workflow_Scripts.ipynb`

### 12. Configuration Management
- [ ] Show current configuration
- [ ] Set configuration values
- [ ] Initialize configuration
- [ ] Nested configuration keys
- [ ] Configuration persistence

**Notebook**: `testing/12_Configuration_Management.ipynb`

### 13. Advanced Features
- [ ] Batch processing
- [ ] Parallel execution
- [ ] Error handling and recovery
- [ ] Progress indicators
- [ ] Export formats (JSON, HDF5, CSV, Parquet)

**Notebook**: `testing/13_Advanced_Features.ipynb`

## Testing Notes

### For Each Test:
1. **Document Issues**: Note any errors, unexpected behavior, or unclear error messages
2. **Performance**: Record execution time for long-running operations
3. **Usability**: Note if commands/APIs are intuitive
4. **Documentation**: Check if help text/examples are clear
5. **Edge Cases**: Try invalid inputs, missing files, etc.

### Common Issues to Check:
- Error messages are helpful and actionable
- Progress indicators work correctly
- Files are saved in expected locations
- Output formats are correct
- Parallel execution doesn't cause conflicts
- Checkpointing works reliably

### Test Data:
- Use presets: `valar-10`, `htr-pm-200`, `smr-160`
- Test with both small and larger reactor designs
- Use sample ENDF files for testing

## Reporting Results

After testing, document:
1. Features that work perfectly ✅
2. Features with minor issues ⚠️
3. Features with major issues ❌
4. Missing features or functionality gaps
5. Performance concerns
6. Usability improvements
7. Documentation gaps

## Running Tests

1. Start Jupyter: `jupyter notebook`
2. Open notebooks in order (01-13)
3. Run each cell and document results
4. Save notebooks with results and notes
