# Coverage Run Monitoring
## January 20, 2026

**Status:** 🟢 Coverage run started with monitoring

---

## Run Configuration

```bash
python -m pytest tests/ \
    --cov=smrforge \
    --cov-report=json:coverage.json \
    --cov-report=term-missing \
    --ignore=tests/performance/test_performance_benchmarks.py \
    -v --tb=short
```

### Expected Runtime
- **Test Suite Size:** 4,336 tests
- **Estimated Duration:** 10-30+ minutes
- **Output:** Real-time progress with verbose output

---

## What to Monitor

### Progress Indicators:
1. **Test Collection:** Should show ~4,336 tests collected
2. **Test Execution:** Watch for passing/failing/skipped counts
3. **Coverage Collection:** Coverage data collected as tests run
4. **Final Report:** Coverage percentage and missing lines

### Expected Results:
- **Baseline:** 61.25% (from `coverage_current.json`)
- **Expected Current:** ~79.2%+ (with 215 new tests)
- **Target:** 80%
- **Gap:** ~0.8% (~83 statements)

---

## Key Metrics to Watch

### Coverage Targets:
- ✅ **Overall Coverage:** Should be 79.2%+ (up from 61.25%)
- ✅ **Covered Lines:** Should be 13,465+ (up from baseline)
- ✅ **Missing Lines:** Should be ~4,000-5,000 (down from 8,520)

### Module-Specific Improvements:
1. `utils/logging.py` - Expected: ~75%+ (was 60.4%)
2. `validation/regulatory_traceability.py` - Expected: ~75%+ (was 40.00%)
3. `validation/standards_parser.py` - Expected: ~75%+ (was 43.98%)
4. `geometry/validation.py` - Expected: ~65-75% (was 30.27%)
5. `geometry/advanced_import.py` - Expected: ~50-60% (was 33.65%)
6. `data_downloader.py` - Expected: ~20-30% (was 13.08%)
7. `control/integration.py` - Expected: Improved (was 18.75%)
8. `core/self_shielding_integration.py` - Expected: Improved (was 52.05%)

---

## Troubleshooting

### If Coverage is Lower Than Expected:
1. Check if all tests executed (look for early termination)
2. Verify test pass rate (should be >95%)
3. Check for coverage collection errors
4. Compare with baseline to identify discrepancies

### If Run Takes Too Long:
- Normal for 4,000+ tests
- Can interrupt and analyze partial results
- Consider running specific test modules separately

---

## Next Steps After Completion

1. **Analyze Results:**
   ```bash
   python scripts/analyze_coverage.py coverage.json
   ```

2. **Compare with Baseline:**
   ```bash
   python scripts/analyze_coverage.py coverage_current.json
   ```

3. **Update Documentation:**
   - Update `COVERAGE_STATUS_AS_OF_2026_01_20.md`
   - Update `COVERAGE_TRACKING.md`
   - Create final coverage report

4. **Identify Remaining Gaps:**
   - List modules still below 80%
   - Prioritize quick wins for final 0.8%

---

*Started: January 20, 2026*  
*Monitor terminal output for real-time progress*
