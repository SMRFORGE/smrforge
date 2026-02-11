# Version-Lock Requirements for Reproducibility

**Purpose:** Document version-locking strategy for NQA-1 dedication and reproducibility.  
**Reference:** NUCLEAR_INDUSTRY_ANALYSIS_AND_AI_FUTURE_PROOFING.md § 1.6

---

## Rationale

Nuclear safety analysis and licensing require reproducible runs. Unpinned dependencies (`numpy>=1.20.0`, etc.) can yield different numerical results across environments. NQA-1 commercial-grade dedication requires a controlled, validated environment.

## Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Loose constraints for development (min versions). |
| `requirements-lock.txt` | **Pinned** versions for releases and validation. |

## Usage

### Development
```bash
pip install -r requirements.txt
```

### Release / Validation / Production
```bash
pip install -r requirements-lock.txt
```

### Regenerating the Lock File
```bash
# Using pip-tools (recommended)
pip install pip-tools
pip-compile requirements.txt -o requirements-lock.txt

# Or from existing environment
pip freeze | grep -E "numpy|scipy|matplotlib|pandas|numba|h5py|zarr|polars|pydantic|pint|rich|requests|httpx|tqdm|pyyaml|scikit-learn|plotly|pyvista|dash|SALib|seaborn" > requirements-lock.txt
```

## Version-Lock Policy

1. **Releases:** Generate `requirements-lock.txt` from the validated dev environment before each release tag.
2. **V&V:** Document in the V&V plan which locked versions were used for validation runs.
3. **CI:** Optional CI job to verify `pip install -r requirements-lock.txt` succeeds and tests pass.
4. **Updates:** When upgrading dependencies, regenerate the lock file and re-run full test suite.

## Packages to Pin (Core Physics Stack)

| Package | Role |
|---------|------|
| numpy | Numerical core; version affects numerics |
| scipy | Solvers, integration, sparse; version affects results |
| numba | JIT; version affects performance and possibly numerics |
| pydantic | Validation; version affects schema behavior |
| h5py, zarr | Data I/O; version affects file compatibility |

## References

- NRC Regulatory Guide 1.231 (commercial-grade computer programs)
- NUCLEAR_INDUSTRY_ANALYSIS_AND_AI_FUTURE_PROOFING.md
