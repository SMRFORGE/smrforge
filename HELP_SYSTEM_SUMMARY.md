# Help System Implementation Summary

**Date:** January 2025  
**Status:** ✅ Complete

---

## Overview

A comprehensive interactive help system has been implemented for SMRForge to aid users in understanding how to use each function, class, and feature. The help system provides:

- Interactive help menu
- Function and class documentation
- Category-based help
- Usage examples
- Getting started guides
- Workflow documentation

---

## What Was Added

### 1. Help Module

**File:** `smrforge/help.py`

A comprehensive help system module that provides:

- **Main Help Menu**: Overview of all available help categories
- **Function/Class Help**: Detailed documentation for specific functions and classes
- **Category Help**: Help organized by feature category
- **Examples**: Usage examples for common functions
- **Getting Started Guide**: Step-by-step introduction
- **Workflow Documentation**: Common usage patterns

### 2. Integration

**File:** `smrforge/__init__.py`

The help system is exported as `smr.help()` and is always available:

```python
import smrforge as smr
smr.help()  # Show main help menu
smr.help('create_reactor')  # Help on specific function
smr.help('geometry')  # Help on category
```

---

## Features

### Main Help Menu

Displays all available help categories:

- **geometry**: Geometry creation and manipulation
- **neutronics**: Neutronics solvers and calculations
- **burnup**: Burnup and depletion calculations
- **thermal**: Thermal-hydraulics analysis
- **decay**: Decay heat calculations
- **gamma**: Gamma transport and shielding
- **visualization**: 3D visualization and plotting
- **materials**: Material database and properties
- **nuclides**: Nuclide operations
- **convenience**: Convenience functions and shortcuts
- **presets**: Preset reactor designs

### Function/Class Help

For any function or class, the help system displays:

- **Documentation**: Full docstring with formatting
- **Signature**: Function signature with parameters
- **Parameters**: Detailed parameter table with types and defaults
- **Return Type**: Return type annotation
- **Examples**: Usage examples (if available)

### Category Help

Each category provides:

- Overview of features in that category
- Key functions and classes
- Usage examples
- Related topics

### Special Topics

- **getting_started**: Quick start guide
- **examples**: Code examples
- **workflows**: Common usage patterns
- **troubleshooting**: Common issues and solutions

---

## Usage Examples

### Basic Usage

```python
import smrforge as smr

# Show main help menu
smr.help()

# Get help on a function
smr.help('create_reactor')

# Get help on a category
smr.help('geometry')

# Get help on getting started
smr.help('getting_started')
```

### Getting Help on Functions

```python
# Help on convenience functions
smr.help('create_simple_core')
smr.help('quick_keff_calculation')
smr.help('get_nuclide')
smr.help('get_material')
```

### Getting Help on Categories

```python
# Category help
smr.help('geometry')
smr.help('neutronics')
smr.help('burnup')
smr.help('visualization')
smr.help('materials')
```

### Getting Help on Objects

```python
from smrforge import create_simple_core

# Get help on function object
smr.help(create_simple_core)
```

---

## Implementation Details

### Rich Formatting

The help system uses the `rich` library (if available) for beautiful terminal output:

- Color-coded categories
- Formatted tables
- Markdown rendering
- Panel borders

If `rich` is not available, the system falls back to plain text output.

### Introspection

The help system uses Python's `inspect` module to:

- Extract function signatures
- Parse parameter types and defaults
- Extract docstrings
- Format type annotations

### Examples Database

A built-in examples database provides usage examples for common functions:

- `create_reactor`
- `create_simple_core`
- `create_simple_solver`
- `quick_keff_calculation`
- `get_nuclide`
- `get_material`
- `list_materials`
- `quick_mesh_extraction`
- `quick_plot_core`
- `quick_plot_mesh`
- `run_complete_analysis`

---

## Example Output

### Main Menu

```
SMRForge Help System

Available Help Categories
┌──────────────┬──────────────────────────────┬─────────────────────────┐
│ Category     │ Description                  │ Example                 │
├──────────────┼──────────────────────────────┼─────────────────────────┤
│ geometry     │ Geometry creation and        │ smr.help('geometry')    │
│              │ manipulation                 │                         │
│ neutronics   │ Neutronics solvers and       │ smr.help('neutronics')  │
│              │ calculations                 │                         │
│ ...          │ ...                          │ ...                     │
└──────────────┴──────────────────────────────┴─────────────────────────┘
```

### Function Help

```
┌────────────────────── create_simple_core ──────────────────────┐
│ Create a simple prismatic core with sensible defaults.         │
│                                                                 │
│ Args:                                                           │
│   name: Core name                                              │
│   n_rings: Number of hexagonal rings                            │
│   pitch: Block-to-block pitch [cm]                             │
│   ...                                                           │
│                                                                 │
│ Returns: PrismaticCore instance with mesh generated            │
└─────────────────────────────────────────────────────────────────┘

Signature:
  create_simple_core(name: str = 'SimpleCore', n_rings: int = 3, ...)

Parameters:
┌──────────────┬──────────┬─────────────┐
│ Parameter    │ Type     │ Default     │
├──────────────┼──────────┼─────────────┤
│ name         │ str      │ 'SimpleCore'│
│ n_rings      │ int      │ 3           │
│ pitch        │ float    │ 40.0        │
│ ...          │ ...      │ ...         │
└──────────────┴──────────┴─────────────┘

Returns: geometry.PrismaticCore

Examples:
  # Create simple core
  core = create_simple_core(n_rings=3, pitch=40.0)
```

---

## Files Modified

1. **`smrforge/help.py`** (new): Main help system implementation
2. **`smrforge/__init__.py`**: Added help system export
3. **`examples/help_system_example.py`** (new): Example demonstrating help system usage

---

## Dependencies

- **rich** (optional): For beautiful terminal output. Falls back to plain text if not available.
- **inspect** (built-in): For function/class introspection

---

## Benefits

1. **Discoverability**: Users can easily discover available functions and features
2. **Documentation**: Inline help reduces need to consult external documentation
3. **Examples**: Usage examples help users get started quickly
4. **Consistency**: Standardized help format across all features
5. **Accessibility**: Available directly in Python without external tools

---

## Future Enhancements

Potential future improvements:

1. **Interactive Mode**: Interactive help browser with navigation
2. **Search**: Search functionality for help topics
3. **Tutorial Mode**: Step-by-step tutorials for common tasks
4. **Context-Sensitive Help**: Help based on current code context
5. **Web Interface**: HTML-based help interface
6. **Video Tutorials**: Links to video tutorials
7. **API Reference**: Complete API reference generation

---

## Testing

The help system can be tested with:

```python
# Test main menu
python -c "import smrforge as smr; smr.help()"

# Test function help
python -c "import smrforge as smr; smr.help('create_simple_core')"

# Test category help
python -c "import smrforge as smr; smr.help('geometry')"

# Run example
python examples/help_system_example.py
```

---

## Summary

The help system provides comprehensive, interactive documentation for SMRForge, making it easier for users to discover and use features. It integrates seamlessly with the existing codebase and provides a consistent interface for accessing documentation and examples.
