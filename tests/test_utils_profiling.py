import re


def test_run_with_memory_profile_returns_report_and_result():
    from smrforge.utils.profiling import run_with_memory_profile

    def workload(x, y=3):
        # Allocate a little memory to ensure tracemalloc sees something.
        a = [0] * (x * 10)
        return len(a) + y

    result, report = run_with_memory_profile(workload, 5, y=7, top_n=5)
    assert result == 5 * 10 + 7
    assert isinstance(report, dict)
    assert "peak_mb" in report
    assert "current_mb" in report
    assert "top_allocations" in report
    assert isinstance(report["top_allocations"], list)
    assert report["peak_mb"] >= 0.0
    assert report["current_mb"] >= 0.0


def test_format_memory_report_contains_expected_sections():
    from smrforge.utils.profiling import format_memory_report

    report = {
        "peak_mb": 12.3456,
        "current_mb": 1.2345,
        "top_allocations": [
            {"size_mb": 0.5, "count": 2, "traceback": "File \"x.py\", line 1"},
        ],
    }
    text = format_memory_report(report)
    assert "Memory Profile" in text
    assert "Peak traced memory" in text
    assert "Top allocations" in text
    assert re.search(r"12\.35", text)  # rounded to 2 decimals

