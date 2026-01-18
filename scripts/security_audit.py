#!/usr/bin/env python
"""
Automated security audit script for SMRForge.

Performs security scanning using multiple tools:
- pip-audit (vulnerability scanning)
- bandit (code security analysis)

Usage:
    python scripts/security_audit.py [--format FORMAT] [--output OUTPUT]
"""

import subprocess
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


def run_pip_audit(output_file: Optional[Path] = None) -> Tuple[int, str]:
    """
    Run pip-audit for dependency vulnerability scanning.
    
    Returns:
        Tuple of (exit_code, output)
    """
    print("Running pip-audit (dependency vulnerability scan)...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip_audit", "--desc", "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\n\nErrors/Warnings:\n{result.stderr}"
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            print(f"✅ pip-audit report saved to {output_file}")
        
        return result.returncode, output
    except FileNotFoundError:
        print("⚠️  pip-audit not installed. Install with: pip install pip-audit")
        return 1, "pip-audit not available"


def run_bandit(output_file: Optional[Path] = None) -> Tuple[int, str]:
    """
    Run bandit for code security analysis.
    
    Returns:
        Tuple of (exit_code, output)
    """
    print("Running bandit (code security analysis)...")
    
    project_root = Path(__file__).parent.parent
    smrforge_dir = project_root / "smrforge"
    
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "bandit",
                "-r", str(smrforge_dir),
                "-f", "json",
                "-ll",  # Low severity, low confidence
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\n\nErrors/Warnings:\n{result.stderr}"
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            print(f"✅ bandit report saved to {output_file}")
        
        return result.returncode, output
    except FileNotFoundError:
        print("⚠️  bandit not installed. Install with: pip install bandit[toml]")
        return 1, "bandit not available"


def parse_pip_audit_results(json_output: str) -> Dict:
    """Parse pip-audit JSON output."""
    try:
        data = json.loads(json_output)
        vulnerabilities = data.get("vulnerabilities", [])
        return {
            "total_vulnerabilities": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
            "packages_scanned": len(set(v.get("name", "") for v in vulnerabilities)),
        }
    except (json.JSONDecodeError, KeyError):
        return {"total_vulnerabilities": 0, "vulnerabilities": [], "packages_scanned": 0}


def parse_bandit_results(json_output: str) -> Dict:
    """Parse bandit JSON output."""
    try:
        data = json.loads(json_output)
        metrics = data.get("metrics", {})
        results = data.get("results", [])
        
        # Count by severity
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for result in results:
            severity = result.get("issue_severity", "LOW")
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return {
            "total_issues": len(results),
            "severity_counts": severity_counts,
            "files_tested": metrics.get("_totals", {}).get("loc", 0),
            "issues": results,
        }
    except (json.JSONDecodeError, KeyError):
        return {"total_issues": 0, "severity_counts": {}, "files_tested": 0, "issues": []}


def generate_summary_report(
    pip_audit_results: Dict,
    bandit_results: Dict,
    output_file: Optional[Path] = None,
) -> str:
    """Generate human-readable summary report."""
    lines = [
        "=" * 70,
        "SMRForge Security Audit Report",
        "=" * 70,
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "1. Dependency Vulnerabilities (pip-audit):",
        "-" * 70,
        f"  Total vulnerabilities found: {pip_audit_results['total_vulnerabilities']}",
        f"  Packages scanned: {pip_audit_results['packages_scanned']}",
        "",
    ]
    
    if pip_audit_results['vulnerabilities']:
        lines.append("  Vulnerabilities:")
        for vuln in pip_audit_results['vulnerabilities'][:10]:  # First 10
            name = vuln.get("name", "Unknown")
            installed = vuln.get("installed_version", "Unknown")
            vuln_id = vuln.get("vuln", {}).get("id", "Unknown")
            aliases = vuln.get("vuln", {}).get("aliases", [])
            lines.append(f"    - {name} ({installed}): {vuln_id}")
            if aliases:
                lines.append(f"      Aliases: {', '.join(aliases[:3])}")
    else:
        lines.append("  ✅ No vulnerabilities found")
    
    lines.extend([
        "",
        "2. Code Security Issues (bandit):",
        "-" * 70,
        f"  Total issues found: {bandit_results['total_issues']}",
        f"  Files tested: {bandit_results['files_tested']}",
        f"  High severity: {bandit_results['severity_counts'].get('HIGH', 0)}",
        f"  Medium severity: {bandit_results['severity_counts'].get('MEDIUM', 0)}",
        f"  Low severity: {bandit_results['severity_counts'].get('LOW', 0)}",
        "",
    ])
    
    if bandit_results['issues']:
        high_issues = [i for i in bandit_results['issues'] if i.get('issue_severity') == 'HIGH']
        if high_issues:
            lines.append("  High severity issues:")
            for issue in high_issues[:5]:  # First 5
                test_id = issue.get("test_id", "Unknown")
                test_name = issue.get("test_name", "Unknown")
                filename = issue.get("filename", "Unknown")
                line_num = issue.get("line_number", "Unknown")
                lines.append(f"    - {filename}:{line_num} - {test_name} ({test_id})")
    
    if not bandit_results['issues']:
        lines.append("  ✅ No security issues found")
    
    lines.extend([
        "",
        "=" * 70,
        "Summary:",
        "-" * 70,
    ])
    
    # Overall status
    has_vulns = pip_audit_results['total_vulnerabilities'] > 0
    has_high_severity = bandit_results['severity_counts'].get('HIGH', 0) > 0
    
    if not has_vulns and not has_high_severity:
        lines.append("  ✅ Security audit PASSED - No critical issues found")
    elif has_high_severity:
        lines.append("  ❌ Security audit FAILED - High severity issues found")
    elif has_vulns:
        lines.append("  ⚠️  Security audit WARNING - Dependency vulnerabilities found")
    else:
        lines.append("  ⚠️  Security audit WARNING - Some issues found")
    
    lines.append("")
    
    report = "\n".join(lines)
    
    if output_file:
        output_file.write_text(report)
        print(f"✅ Summary report saved to {output_file}")
    
    return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run security audit for SMRForge")
    parser.add_argument(
        "--format",
        choices=["summary", "json", "both"],
        default="summary",
        help="Output format (default: summary)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("security_reports"),
        help="Output directory for reports (default: security_reports/)"
    )
    parser.add_argument(
        "--skip-pip-audit",
        action="store_true",
        help="Skip pip-audit check"
    )
    parser.add_argument(
        "--skip-bandit",
        action="store_true",
        help="Skip bandit check"
    )
    
    args = parser.parse_args()
    
    # Create output directory
    args.output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Run pip-audit
    pip_audit_results = {"total_vulnerabilities": 0, "vulnerabilities": [], "packages_scanned": 0}
    if not args.skip_pip_audit:
        pip_audit_file = args.output_dir / f"pip_audit_{timestamp}.json"
        exit_code, output = run_pip_audit(pip_audit_file if args.format != "summary" else None)
        if exit_code == 0:
            pip_audit_results = parse_pip_audit_results(output)
    
    # Run bandit
    bandit_results = {"total_issues": 0, "severity_counts": {}, "files_tested": 0, "issues": []}
    if not args.skip_bandit:
        bandit_file = args.output_dir / f"bandit_{timestamp}.json"
        exit_code, output = run_bandit(bandit_file if args.format != "summary" else None)
        if exit_code == 0:
            bandit_results = parse_bandit_results(output)
    
    # Generate summary report
    if args.format in ["summary", "both"]:
        summary_file = args.output_dir / f"security_audit_{timestamp}.txt"
        report = generate_summary_report(pip_audit_results, bandit_results, summary_file)
        print("\n" + report)
    
    # Exit code
    has_critical = (
        pip_audit_results['total_vulnerabilities'] > 0 or
        bandit_results['severity_counts'].get('HIGH', 0) > 0
    )
    
    return 1 if has_critical else 0


if __name__ == "__main__":
    sys.exit(main())
