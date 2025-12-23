# Testing Infrastructure Improvements

This document summarizes the comprehensive testing improvements made to SMRForge.

## Summary

Significantly expanded test infrastructure with:
- Comprehensive test fixtures
- Test utilities and helper functions
- Integration tests
- Parametric and edge case tests
- Improved placeholder tests
- Pytest configuration

## New Files

### 1. `tests/conftest.py` (Enhanced)
Comprehensive pytest fixtures including:
- **Geometry fixtures**: `simple_geometry`, `small_geometry`, `large_geometry`
- **Cross-section fixtures**: `simple_xs_data`, `multi_group_xs_data`, `subcritical_xs_data`, `supercritical_xs_data`
- **Solver options fixtures**: `solver_options`, `fast_solver_options`, `tight_solver_options`
- **Solver fixtures**: `solver`, `solved_solver`
- **Reactors**: `sample_reactor_spec`
- **Utilities**: `test_data_dir`, `temp_dir`, `rng`, `rng_seed_123`

### 2. `tests/test_utilities.py` (New)
Test utilities and helper classes:
- `SimpleGeometry` - Simple geometry class for testing
- `create_test_xs_data()` - Generate test cross-section data
- `assert_solution_reasonable()` - Assert solution quality
- `compute_power_error()` - Compute power conservation error

### 3. `pytest.ini` (New)
Pytest configuration:
- Test discovery patterns
- Custom markers (slow, integration, unit, requires_openmc, requires_sandy)
- Coverage configuration
- Output options

### 4. `tests/test_integration.py` (New)
Integration tests for complete workflows:
- `TestCompleteWorkflow` - Full neutronics workflows
- `TestValidationIntegration` - Pydantic validation integration
- `TestPresetIntegration` - Preset reactor designs
- `TestErrorHandling` - Error handling in workflows

### 5. `tests/test_neutronics_robust.py` (New)
Robust neutronics tests:
- `TestParametricVariations` - Parametric tests with pytest.mark.parametrize
- `TestEdgeCases` - Edge cases and boundary conditions
- `TestNumericalStability` - Numerical stability tests
- `TestSolutionQuality` - Solution quality checks

### 6. Enhanced Existing Tests

**`tests/test_geometry.py`**:
- Expanded from placeholder to comprehensive tests
- Tests for `PrismaticCore`, `PebbleBedCore`, `Point3D`
- Parametric tests for different lattice sizes
- Geometry export tests

**`tests/test_thermal.py`**:
- Expanded from placeholder to comprehensive tests
- Tests for `ChannelGeometry`, `ChannelThermalHydraulics`
- Power profile setting tests

## Test Organization

### Markers

Tests are organized with markers:
- `@pytest.mark.slow` - Slow tests (skip with `-m "not slow"`)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.requires_openmc` - Tests requiring OpenMC
- `@pytest.mark.requires_sandy` - Tests requiring SANDY

### Test Categories

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test complete workflows
3. **Parametric Tests** - Test with multiple configurations
4. **Edge Case Tests** - Test boundary conditions and extreme cases
5. **Numerical Stability Tests** - Test numerical robustness

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test categories
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Run with coverage
```bash
pytest --cov=smrforge --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_neutronics.py
pytest tests/test_integration.py
```

## Test Coverage Improvements

### Before
- ~20 test cases
- Many placeholder/skip tests
- Minimal fixtures
- No integration tests
- No parametric tests

### After
- 100+ test cases
- Comprehensive fixtures
- Integration tests for workflows
- Parametric tests for multiple configurations
- Edge case tests
- Solution quality checks
- Numerical stability tests

## Key Features

### 1. Comprehensive Fixtures
Fixtures provide ready-to-use test data:
- Multiple geometry configurations
- Various cross-section data sets (2-group, 4-group, subcritical, supercritical)
- Different solver options (fast, tight tolerance)
- Pre-solved solvers for dependent tests

### 2. Test Utilities
Helper functions for common test operations:
- Solution validation
- Power conservation checks
- Test data generation

### 3. Parametric Testing
Uses `pytest.mark.parametrize` to test multiple configurations:
- Different numbers of energy groups
- Different core sizes
- Different mesh resolutions

### 4. Edge Cases
Tests handle boundary conditions:
- Very small/large cores
- Single material (no reflector)
- Subcritical/supercritical configurations
- High scattering ratios
- Zero/low absorption

### 5. Integration Tests
Test complete workflows:
- Neutronics solve → power distribution
- Reactivity coefficients
- Multiple mesh sizes
- Different group structures

### 6. Solution Quality Checks
Verify physical reasonableness:
- Flux monotonicity
- Power peaking factors
- Group flux ratios
- Power conservation

## CI/CD Integration

The tests are integrated with GitHub Actions CI:
- Runs on push/PR to main/develop
- Tests on Python 3.8, 3.9, 3.10, 3.11
- Generates coverage reports
- Uploads to Codecov

## Next Steps

To further improve testing:

1. **Increase Coverage**
   - Add more tests for validation models
   - Add tests for preset designs
   - Add tests for safety module

2. **Performance Tests**
   - Add benchmarks for solver performance
   - Regression tests for performance

3. **Property-Based Testing**
   - Consider Hypothesis for property-based tests

4. **Test Data**
   - Add reference test cases with known solutions
   - Add regression test data

5. **Visual Regression Tests**
   - For visualization module (when implemented)

## Usage Examples

### Using Fixtures in Tests

```python
def test_solver_with_fixture(solver):
    """Use solver fixture."""
    k_eff, flux = solver.solve_steady_state()
    assert 0.5 < k_eff < 2.0
```

### Parametric Tests

```python
@pytest.mark.parametrize("n_groups", [2, 4, 6])
def test_multiple_groups(n_groups, simple_geometry, solver_options):
    """Test with different numbers of groups."""
    xs_dict = create_test_xs_data(n_groups=n_groups)
    # ... test code
```

### Integration Tests

```python
@pytest.mark.integration
def test_complete_workflow(solver):
    """Test complete workflow."""
    k_eff, flux = solver.solve_steady_state()
    power = solver.compute_power_distribution(10e6)
    # ... verify results
```

## Conclusion

The test infrastructure is now significantly more robust, with:
- ✅ Comprehensive fixtures
- ✅ Integration tests
- ✅ Parametric tests
- ✅ Edge case coverage
- ✅ Solution quality checks
- ✅ CI/CD integration

This provides a solid foundation for maintaining code quality and catching regressions as the codebase evolves.

