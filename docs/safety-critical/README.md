# Safety-Critical Use Documentation

This folder contains documentation for safety-critical and regulatory applications of SMRForge.

**Note:** These items are not required for general production use but are needed for licensing and regulatory applications (e.g., NRC licensing, international standards compliance).

## Documents

| Document | Purpose |
|----------|---------|
| [V&V_EXPERIMENTAL_BENCHMARKS.md](V&V_EXPERIMENTAL_BENCHMARKS.md) | Full V&V against experimental benchmarks (SC-1) |
| [NQA1_IEC61508_CHECKLIST.md](NQA1_IEC61508_CHECKLIST.md) | Code certification / standards compliance (SC-2) |
| [THIRD_PARTY_VERIFICATION_SCOPE.md](THIRD_PARTY_VERIFICATION_SCOPE.md) | Independent third-party verification (SC-3) |
| [REGULATORY_SUBMISSION_OUTLINE.md](REGULATORY_SUBMISSION_OUTLINE.md) | Regulatory submission documentation (SC-4) |
| [SAFETY_CRITICAL_MODULES.md](SAFETY_CRITICAL_MODULES.md) | Safety-critical paths and 90%+ coverage (SC-5) |

## Quick Reference

- **Run V&V benchmarks:** `python scripts/run_vv_benchmarks.py`
- **Safety-critical coverage:** `pytest -m safety_critical --cov=smrforge.neutronics --cov=smrforge.burnup --cov=smrforge.validation --cov-report=term-missing`
