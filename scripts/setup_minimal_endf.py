#!/usr/bin/env python3
"""
Create a minimal ENDF directory for running ENDF-dependent tests.

Copies only the files needed to un-skip ENDF validation tests from a full
ENDF-B-VIII.1 installation (e.g. C:\\Users\\cmwha\\Downloads\\ENDF-B-VIII.1).

Usage:
    python scripts/setup_minimal_endf.py [source_dir] [target_dir]

    source_dir: Full ENDF-B-VIII.1 path (default: from env or ~/Downloads/ENDF-B-VIII.1)
    target_dir: Where to create minimal structure (default: .endf_minimal in project root)

Environment:
    SMRFORGE_ENDF_DIR or LOCAL_ENDF_DIR: Use this as source if set and exists.
"""
import os
import shutil
import sys
from pathlib import Path

# Minimum files needed to un-skip ENDF-dependent tests
MINIMAL_FILES = {
    "thermal_scatt-version.VIII.1": [
        "tsl-HinH2O.endf",
        "tsl-crystalline-graphite.endf",
    ],
    "neutrons-version.VIII.1": [
        "n-092_U_235.endf",
        "n-092_U_238.endf",
    ],
    "decay-version.VIII.1": [
        "dec-092_U_235.endf",
        "dec-055_Cs_137.endf",
        "dec-038_Sr_090.endf",
    ],
    "nfy-version.VIII.1": [
        "nfy-092_U_235.endf",
        "nfy-092_U_238.endf",
    ],
    "photoat-version.VIII.1": [
        "photoat-001_H_000.endf",
    ],
    "gammas-version.VIII.1": [
        "g-092_U_235.endf",
    ],
}


def get_source_dir(cmdline_source: str | None) -> Path | None:
    """Resolve source ENDF directory."""
    if cmdline_source:
        p = Path(cmdline_source).expanduser().resolve()
        if p.exists():
            return p
        print(f"Source not found: {p}")
        return None
    for env_name in ("SMRFORGE_ENDF_DIR", "LOCAL_ENDF_DIR"):
        env_val = os.environ.get(env_name)
        if env_val:
            p = Path(env_val).expanduser().resolve()
            if p.exists():
                return p
    for candidate in [
        Path.home() / "Downloads" / "ENDF-B-VIII.1",
        Path(r"C:\Users\cmwha\Downloads\ENDF-B-VIII.1"),
    ]:
        if candidate.exists():
            return candidate
    return None


def main():
    project_root = Path(__file__).resolve().parent.parent
    source = get_source_dir(sys.argv[1] if len(sys.argv) > 1 else None)
    target = Path(
        sys.argv[2]
        if len(sys.argv) > 2
        else project_root / ".endf_minimal"
    ).expanduser().resolve()

    if source is None:
        print("ENDF source not found. Set SMRFORGE_ENDF_DIR or pass source path.")
        print("Example: python scripts/setup_minimal_endf.py C:\\Users\\cmwha\\Downloads\\ENDF-B-VIII.1")
        sys.exit(1)

    print(f"Source: {source}")
    print(f"Target: {target}")
    target.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped = 0
    for subdir, filenames in MINIMAL_FILES.items():
        dest_sub = target / subdir
        dest_sub.mkdir(parents=True, exist_ok=True)
        src_sub = source / subdir
        if not src_sub.exists():
            print(f"  [skip] {subdir}/ (not in source)")
            skipped += len(filenames)
            continue
        for fname in filenames:
            src_file = src_sub / fname
            dest_file = dest_sub / fname
            if src_file.exists():
                if not dest_file.exists() or dest_file.stat().st_size != src_file.stat().st_size:
                    shutil.copy2(src_file, dest_file)
                    print(f"  [copy] {subdir}/{fname}")
                    copied += 1
                else:
                    skipped += 1
            else:
                # Try alternate names (e.g. graphiteSd vs crystalline-graphite)
                alt = "tsl-graphiteSd.endf" if "crystalline-graphite" in fname else None
                if alt and (src_sub / alt).exists():
                    shutil.copy2(src_sub / alt, dest_file)
                    print(f"  [copy] {subdir}/{alt} -> {fname}")
                    copied += 1
                else:
                    print(f"  [miss] {subdir}/{fname}")

    print(f"\nDone: {copied} copied, {skipped} skipped (unchanged).")
    print(f"Set SMRFORGE_ENDF_DIR={target} to use this minimal set.")
    print(f"  Windows: $env:SMRFORGE_ENDF_DIR=\"{target}\"")
    print(f"  Unix:    export SMRFORGE_ENDF_DIR=\"{target}\"")


if __name__ == "__main__":
    main()
