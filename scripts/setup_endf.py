#!/usr/bin/env python
"""
Command-line entry point for ENDF data setup wizard.

Usage:
    python -m smrforge.core.endf_setup
    python scripts/setup_endf.py
    smrforge-setup-endf  (if installed as package)
"""

import sys
from pathlib import Path

# Add parent directory to path if running as script
if __name__ == "__main__" and not __package__:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from smrforge.core.endf_setup import setup_endf_data_interactive

if __name__ == "__main__":
    result = setup_endf_data_interactive()
    if result:
        print(f"\n✓ Setup complete! ENDF directory: {result}")
        sys.exit(0)
    else:
        print("\n✗ Setup incomplete or cancelled.")
        sys.exit(1)

