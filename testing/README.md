# SMRForge Manual Testing Guide

This directory contains comprehensive testing materials for manually testing all SMRForge features.

## Quick Start

1. **Review the Checklist**: Read `docs/testing/MANUAL_TESTING_CHECKLIST.md` for an overview
2. **Run Test Scripts**: Use the Python test scripts in this directory (`test_*.py`)
3. **Use Jupyter Notebooks**: Convert test scripts to notebooks or use provided notebooks
4. **Document Results**: Record your findings in each notebook/script

## Available Test Scripts

Each test script focuses on a specific feature category:

1. `test_01_cli_commands.py` - CLI command testing
2. `test_02_reactor_creation.py` - Reactor creation and analysis
3. `test_03_burnup.py` - Burnup calculations
4. `test_04_parameter_sweep.py` - Parameter sweep workflow
5. `test_05_templates.py` - Template library system
6. `test_06_constraints.py` - Design constraints validation
7. `test_07_io_converters.py` - I/O converters
8. `test_08_data_management.py` - Data management
9. `test_09_validation.py` - Validation framework
10. `test_10_visualization.py` - Visualization features
11. `test_11_workflows.py` - Workflow scripts
12. `test_12_config.py` - Configuration management
13. `test_13_advanced.py` - Advanced features

## Running Tests

### As Python Scripts
```bash
cd testing
python test_01_cli_commands.py
python test_02_reactor_creation.py
# ... etc
```

### As Jupyter Notebooks
1. Convert scripts to notebooks: `jupyter nbconvert --to notebook --execute test_01_cli_commands.py`
2. Or create notebooks manually from the scripts
3. Open in Jupyter: `jupyter notebook`

## Test Results Template

For each test, document:
- ✅ Working features
- ⚠️ Features with minor issues
- ❌ Features with major issues
- 💡 Suggestions for improvements
- 📝 Notes on usability and clarity

## Prerequisites

- SMRForge installed: `pip install -e .`
- ENDF data configured (optional, some tests require it)
- All dependencies installed
- Jupyter notebook (optional, for notebook format)
