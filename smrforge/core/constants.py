# smrforge/core/constants.py
"""
Constants and element data for nuclear calculations.

This module provides:
- Element symbols and atomic numbers
- Physical constants (neutron mass, Avogadro, etc.)
- Standard energy group structures for nuclear calculations
"""

from typing import Dict

import numpy as np

# Element symbols (Z -> symbol)
ELEMENT_SYMBOLS: Dict[int, str] = {
    1: "H",
    2: "He",
    3: "Li",
    4: "Be",
    5: "B",
    6: "C",
    7: "N",
    8: "O",
    9: "F",
    10: "Ne",
    11: "Na",
    12: "Mg",
    13: "Al",
    14: "Si",
    15: "P",
    16: "S",
    17: "Cl",
    18: "Ar",
    19: "K",
    20: "Ca",
    21: "Sc",
    22: "Ti",
    23: "V",
    24: "Cr",
    25: "Mn",
    26: "Fe",
    27: "Co",
    28: "Ni",
    29: "Cu",
    30: "Zn",
    31: "Ga",
    32: "Ge",
    33: "As",
    34: "Se",
    35: "Br",
    36: "Kr",
    37: "Rb",
    38: "Sr",
    39: "Y",
    40: "Zr",
    41: "Nb",
    42: "Mo",
    43: "Tc",
    44: "Ru",
    45: "Rh",
    46: "Pd",
    47: "Ag",
    48: "Cd",
    49: "In",
    50: "Sn",
    51: "Sb",
    52: "Te",
    53: "I",
    54: "Xe",
    55: "Cs",
    56: "Ba",
    57: "La",
    58: "Ce",
    59: "Pr",
    60: "Nd",
    61: "Pm",
    62: "Sm",
    63: "Eu",
    64: "Gd",
    65: "Tb",
    66: "Dy",
    67: "Ho",
    68: "Er",
    69: "Tm",
    70: "Yb",
    71: "Lu",
    72: "Hf",
    73: "Ta",
    74: "W",
    75: "Re",
    76: "Os",
    77: "Ir",
    78: "Pt",
    79: "Au",
    80: "Hg",
    81: "Tl",
    82: "Pb",
    83: "Bi",
    84: "Po",
    85: "At",
    86: "Rn",
    87: "Fr",
    88: "Ra",
    89: "Ac",
    90: "Th",
    91: "Pa",
    92: "U",
    93: "Np",
    94: "Pu",
    95: "Am",
    96: "Cm",
    97: "Bk",
    98: "Cf",
    99: "Es",
    100: "Fm",
}

# Reverse mapping
SYMBOL_TO_Z: Dict[str, int] = {v: k for k, v in ELEMENT_SYMBOLS.items()}

# Physical constants
NEUTRON_MASS = 1.008664915  # amu
AVOGADRO = 6.02214076e23  # 1/mol
BARN = 1e-24  # cm^2
EV_TO_JOULE = 1.602176634e-19
C_LIGHT = 299792458  # m/s

# Standard energy group structures
GROUP_STRUCTURES = {
    "SCALE-44": np.array(
        [  # 44-group structure (high to low)
            2.0e7,
            6.376e6,
            3.012e6,
            1.827e6,
            1.423e6,
            9.072e5,
            4.076e5,
            1.111e5,
            1.503e4,
            3.035e3,
            5.830e2,
            1.013e2,
            2.902e1,
            1.068e1,
            3.059,
            1.855,
            1.300,
            1.125,
            1.0,
            8.764e-1,
            6.826e-1,
            6.250e-1,
            5.315e-1,
            5.0e-1,
            4.140e-1,
            3.25e-1,
            2.75e-1,
            2.25e-1,
            1.5e-1,
            1.0e-1,
            6.75e-2,
            5.0e-2,
            3.75e-2,
            2.5e-2,
            1.0e-2,
            7.5e-3,
            5.0e-3,
            4.0e-3,
            3.0e-3,
            2.5e-3,
            2.0e-3,
            1.5e-3,
            1.0e-3,
            5.0e-4,
            1.0e-5,
        ]
    ),
    "HTGR-8": np.array(
        [  # Optimized 8-group for HTGR
            1.0e7,
            8.21e5,
            5.53e3,
            6.25,
            3.93e-1,
            1.0e-1,
            1.86e-2,
            4.0e-3,
            1.0e-5,
        ]
    ),
    "CASMO-16": np.array(
        [  # 16-group structure
            1.0e7,
            8.187e5,
            5.531e3,
            6.267e1,
            9.877,
            4.0,
            2.5,
            2.25,
            1.855,
            1.3,
            1.125,
            1.0,
            6.25e-1,
            3.5e-1,
            2.8e-1,
            1.4e-1,
            5.8e-2,
            1.0e-5,
        ]
    ),
    "WIMS-69": None,  # Can add full 69-group if needed
}


# Delayed neutron precursor data (6-group)
DELAYED_NEUTRON_DATA = {
    "U235": {
        "beta": np.array([2.13e-4, 1.43e-3, 1.27e-3, 2.56e-3, 7.48e-4, 2.73e-4]),
        "lambda": np.array([0.0124, 0.0305, 0.111, 0.301, 1.14, 3.01]),  # 1/s
    },
    "U238": {
        "beta": np.array([1.52e-4, 1.36e-3, 1.22e-3, 2.69e-3, 8.64e-4, 2.75e-4]),
        "lambda": np.array([0.0133, 0.0327, 0.139, 0.325, 1.13, 2.50]),
    },
    "Pu239": {
        "beta": np.array([7.5e-5, 5.72e-4, 4.32e-4, 1.05e-3, 2.65e-4, 8.6e-5]),
        "lambda": np.array([0.0129, 0.0311, 0.134, 0.331, 1.26, 3.21]),
    },
}


# Fission spectrum (Watt distribution parameters)
FISSION_SPECTRUM_PARAMS = {
    "U235_thermal": {"a": 0.988, "b": 2.249},  # MeV
    "U238_fast": {"a": 0.88, "b": 3.0},
    "Pu239_thermal": {"a": 0.966, "b": 2.383},
}


def watt_spectrum(E: np.ndarray, a: float, b: float) -> np.ndarray:
    """
    Watt fission spectrum: chi(E) = C * exp(-E/a) * sinh(sqrt(b*E))

    Args:
        E: Energy array [MeV]
        a, b: Watt parameters

    Returns:
        Normalized spectrum
    """
    chi = np.exp(-E / a) * np.sinh(np.sqrt(b * E))
    return chi / np.trapz(chi, E)


# HTGR-specific constants
HTGR_CONSTANTS = {
    "helium_molar_mass": 4.002602,  # g/mol
    "graphite_density": 1.74,  # g/cm³ (typical for nuclear graphite)
    "triso_packing_fraction": 0.35,  # Volume fraction of TRISO in fuel
    "kernel_radius": 212.5e-4,  # cm (425 μm diameter UCO kernel)
    "buffer_thickness": 100e-4,  # cm
    "ipyc_thickness": 40e-4,  # cm
    "sic_thickness": 35e-4,  # cm
    "opyc_thickness": 40e-4,  # cm
}


def parse_nuclide_string(name: str) -> tuple:
    """
    Parse nuclide string like 'U235', 'Am242m' into (Z, A, m).

    Examples:
        'U235' -> (92, 235, 0)
        'Am242m' -> (95, 242, 1)
    """
    import re

    # Match pattern: Element + Number + optional 'm'
    match = re.match(r"([A-Z][a-z]?)(\d+)(m\d?)?", name)
    if not match:
        raise ValueError(f"Invalid nuclide string: {name}")

    element, mass, meta = match.groups()
    Z = SYMBOL_TO_Z[element]
    A = int(mass)
    m = 0 if meta is None else (int(meta[1]) if len(meta) > 1 else 1)

    return Z, A, m


def zam_to_name(zam: int) -> str:
    """Convert ZZAAAM format to name."""
    Z = zam // 10000
    A = (zam % 10000) // 10
    m = zam % 10

    symbol = ELEMENT_SYMBOLS[Z]
    suffix = f"m{m}" if m > 0 else ""
    return f"{symbol}{A}{suffix}"


# Pre-computed atomic masses (amu) for common nuclides
ATOMIC_MASSES = {
    "U235": 235.0439299,
    "U238": 238.0507882,
    "Pu239": 239.0521634,
    "Pu240": 240.0538135,
    "Pu241": 241.0568515,
    "Am241": 241.0568291,
    "C": 12.0,  # Graphite
    "He4": 4.002603,
    "B10": 10.012937,
    "B11": 11.009305,
}


# Q-values for fissions (MeV per fission)
Q_VALUES = {
    "U235": 202.5,
    "U238": 205.0,
    "Pu239": 210.0,
    "Pu241": 212.4,
}


# Resonance integral data (for quick estimates)
RESONANCE_INTEGRALS = {  # barns
    "U238_capture": 277.0,
    "Pu240_capture": 8000.0,
    "Xe135_capture": 2.65e6,
    "Sm149_capture": 4.20e4,
}


# Fast flux threshold
FAST_FLUX_THRESHOLD = 0.1e6  # eV (100 keV)


if __name__ == "__main__":
    # Test utilities
    print(f"U235: {parse_nuclide_string('U235')}")
    print(f"Am242m: {parse_nuclide_string('Am242m')}")
    print(f"920951 -> {zam_to_name(920951)}")

    # Test Watt spectrum
    E = np.linspace(0, 15, 1000)  # MeV
    chi = watt_spectrum(E, **FISSION_SPECTRUM_PARAMS["U235_thermal"])
    print(f"Spectrum integral: {np.trapz(chi, E):.6f} (should be 1.0)")
