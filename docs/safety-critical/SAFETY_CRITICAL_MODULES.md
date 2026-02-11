# Safety-Critical Paths and 90%+ Coverage (SC-5)

## Safety-Critical Modules

| Module | Purpose | Coverage Target | Current |
|--------|---------|-----------------|---------|
| `neutronics/solver.py` | Multi-group diffusion, k-eff | 90%+ | ~90%+ |
| `burnup/solver.py` | Depletion, decay chains | 90%+ | ~75-80% |
| `validation/constraints.py` | Safety limits, margins | 90%+ | ~75-80% |
| `validation/regulatory_traceability.py` | Audit trails, margins | 90%+ | High |
| `core/reactor_core.py` | Nuclear data, cross-sections | 90%+ | 86.5% |
| `core/endf_parser.py` | ENDF parsing | 90%+ | 97.3% |

## Running Safety-Critical Coverage

```bash
# Coverage for safety-critical modules
pytest tests/ \
  --cov=smrforge.neutronics.solver \
  --cov=smrforge.burnup.solver \
  --cov=smrforge.validation.constraints \
  --cov=smrforge.validation.regulatory_traceability \
  --cov=smrforge.core.reactor_core \
  --cov=smrforge.core.endf_parser \
  --cov-report=term-missing \
  --cov-fail-under=90
```

## Pytest Marker (Optional)

Tests can be marked `@pytest.mark.safety_critical` for safety-critical path tests. Add to `conftest.py`:

```python
markers =
    safety_critical: marks tests for safety-critical path coverage
```

## Exclusions

- `safety/transients.py` - Excluded from main coverage (optional module); add to safety-critical scope if used for licensing.
- Numba JIT functions - Marked `# pragma: no cover` where untestable.
- GUI, visualization - Not safety-critical for core physics.

## Target: 90%+

All safety-critical modules should achieve 90%+ coverage. Use `--cov-fail-under=90` in CI for safety-critical builds.
