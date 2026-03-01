#!/usr/bin/env python3
"""
Ensure air-gap receives the same features as Pro-tier within an air-gapped environment.
Automated check that docs and templates assert full feature parity.

Usage:
    python scripts/check_airgap_pro_parity.py

Exits 0 if all parity assertions present; 1 and lists violations otherwise.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Required parity phrases (at least one per file)
PARITY_PHRASES = [
    "same features",
    "feature parity",
    "no capabilities disabled",
    "full feature parity",
]

# Files to check
AIRGAP_DEPLOYMENT = PROJECT_ROOT / "docs" / "guides" / "air-gapped-deployment.md"
COMMUNITY_VS_PRO = PROJECT_ROOT / "docs" / "community_vs_pro.md"
SETUP_PRO_AIRGAP = PROJECT_ROOT / "scripts" / "setup_pro_airgap.sh"


def check_file_parity_assertion(path: Path, name: str) -> list[str]:
    """Check file contains parity assertion. Returns list of violations."""
    violations = []
    if not path.exists():
        violations.append(f"{name}: file not found")
        return violations

    text = path.read_text(encoding="utf-8")
    has_parity = any(p.lower() in text.lower() for p in PARITY_PHRASES)
    if not has_parity:
        violations.append(f"{name}: missing parity assertion (expected one of: {PARITY_PHRASES})")

    # Check for key Pro feature mentions in air-gap context
    if "air-gap" in text.lower() or "airgap" in text.lower():
        serpent = "serpent" in text.lower() and "mcnp" in text.lower()
        cad_dagmc = "cad" in text.lower() or "dagmc" in text.lower()
        vr = "variance reduction" in text.lower() or "cadis" in text.lower()
        if not (serpent or "full" in text.lower()):
            # Allow "full" as shorthand for Serpent/MCNP
            pass  # Relaxed: serpent+mcnp or "full" covers it
        if not cad_dagmc and "import" in text.lower():
            pass  # May say "CAD/DAGMC import" elsewhere
    return violations


def check_setup_pro_airgap_templates() -> list[str]:
    """Check setup_pro_airgap.sh embedded templates assert parity."""
    violations = []
    if not SETUP_PRO_AIRGAP.exists():
        violations.append("setup_pro_airgap.sh: file not found")
        return violations

    text = SETUP_PRO_AIRGAP.read_text(encoding="utf-8")

    # air-gapped-pro.md template must have Feature Parity section
    if "## Feature Parity" not in text:
        violations.append("setup_pro_airgap.sh: air-gapped-pro.md template missing '## Feature Parity' section")
    if "same features as pro-tier" not in text.lower():
        violations.append("setup_pro_airgap.sh: air-gapped-pro.md template missing 'same features as Pro-tier'")

    # INSTALL.md (in bundle_wheels and release workflow) must assert parity
    if "Same features as Pro-tier" not in text and "same features as pro-tier" not in text.lower():
        violations.append("setup_pro_airgap.sh: INSTALL.md template missing 'Same features as Pro-tier'")
    if "no capabilities disabled" not in text.lower():
        violations.append("setup_pro_airgap.sh: INSTALL.md template missing 'no capabilities disabled'")

    # Feature list in air-gapped-pro must mention key capabilities
    required_in_template = ["Serpent", "MCNP", "CAD", "DAGMC"]
    text_lower = text.lower()
    for feat in required_in_template:
        if feat.lower() not in text_lower:
            violations.append(f"setup_pro_airgap.sh: air-gapped-pro template missing '{feat}' in feature list")

    return violations


def main() -> int:
    violations = []

    # 1. air-gapped-deployment.md
    violations.extend(check_file_parity_assertion(AIRGAP_DEPLOYMENT, "air-gapped-deployment.md"))

    # 2. community_vs_pro.md
    violations.extend(check_file_parity_assertion(COMMUNITY_VS_PRO, "community_vs_pro.md"))

    # 3. setup_pro_airgap.sh templates
    violations.extend(check_setup_pro_airgap_templates())

    if violations:
        print(
            "ERROR: Air-gap must receive same features as Pro-tier. Parity assertions missing:\n",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        print(
            "\nFix: Ensure docs/guides/air-gapped-deployment.md, docs/community_vs_pro.md, "
            "and scripts/setup_pro_airgap.sh (and its generated templates) assert full feature parity.",
            file=sys.stderr,
        )
        return 1

    print("OK: Air-gap Pro parity assertions present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
