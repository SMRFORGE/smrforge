# Code Certification / Standards Compliance (SC-2)

**Applicable Standards:** NQA-1, IEC 61508, IEC 60880 (nuclear software)

## NQA-1 (Nuclear Quality Assurance) Checklist

| Requirement | Status | Notes |
|-------------|--------|-------|
| Design control | ⬜ | Configuration management (Git), design reviews |
| Document control | ⬜ | CHANGELOG, versioning, release process |
| Configuration management | ✅ | Git, tagging, branch strategy |
| Traceability | ✅ | `regulatory_traceability.py`, audit trails |
| Verification & Validation | ✅ | V&V framework, benchmark comparison |
| Records retention | ⬜ | Define retention policy |
| Corrective action | ⬜ | Issue tracking (GitHub Issues) |

## IEC 61508 / IEC 60880 Checklist

| Requirement | Status | Notes |
|-------------|--------|-------|
| Software safety lifecycle | ⬜ | Define lifecycle phases |
| Requirements traceability | ✅ | Validation models, constraints |
| Static analysis | ✅ | mypy, flake8, bandit in CI |
| Test coverage | ✅ | 90%+ in-scope; safety-critical path coverage |
| Diversity / redundancy | ⬜ | Multi-backend nuclear data |
| Failure modes analysis | ⬜ | Document known limitations |

## SMRForge Capabilities

- **Traceability:** `CalculationAuditTrail`, `SafetyMarginReport` in `validation/regulatory_traceability.py`
- **Standards alignment:** `standards_parser.py` (ANSI/ANS, IAEA)
- **Test coverage:** See `SAFETY_CRITICAL_MODULES.md` for safety-critical path coverage
- **CI quality gates:** black, isort, flake8, mypy, pytest

## Next Steps for Certification

1. Formal quality manual
2. Document control procedures
3. Independent V&V (see SC-3)
4. Software safety analysis report
