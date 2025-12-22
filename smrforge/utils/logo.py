"""
Utility functions for accessing SMRForge logo and assets.
"""

from pathlib import Path
from typing import Optional


def get_logo_path() -> Path:
    """
    Get the path to the SMRForge logo file.
    
    Returns:
        Path to the logo PNG file
    """
    # Logo is in docs/logo/ relative to package root
    package_root = Path(__file__).parent.parent.parent
    logo_path = package_root / "docs" / "logo" / "nukepy-logo.png"
    
    if not logo_path.exists():
        raise FileNotFoundError(
            f"Logo not found at expected location: {logo_path}\n"
            "Make sure the package is installed correctly."
        )
    
    return logo_path


def get_logo_data() -> Optional[bytes]:
    """
    Get the logo file as bytes (useful for embedding in applications).
    
    Returns:
        Bytes of the logo PNG file, or None if not found
    """
    try:
        logo_path = get_logo_path()
        return logo_path.read_bytes()
    except FileNotFoundError:
        return None

