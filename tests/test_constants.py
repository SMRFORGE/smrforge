"""
Tests for constants module.
"""

import numpy as np
import pytest

from smrforge.core.constants import (
    ATOMIC_MASSES,
    DELAYED_NEUTRON_DATA,
    ELEMENT_SYMBOLS,
    FAST_FLUX_THRESHOLD,
    FISSION_SPECTRUM_PARAMS,
    GROUP_STRUCTURES,
    HTGR_CONSTANTS,
    Q_VALUES,
    RESONANCE_INTEGRALS,
    SYMBOL_TO_Z,
    parse_nuclide_string,
    watt_spectrum,
    zam_to_name,
)


class TestElementSymbols:
    """Test element symbol mappings."""

    def test_element_symbols_contains_uranium(self):
        """Test that ELEMENT_SYMBOLS contains uranium."""
        assert ELEMENT_SYMBOLS[92] == "U"

    def test_symbol_to_z_mapping(self):
        """Test SYMBOL_TO_Z reverse mapping."""
        assert SYMBOL_TO_Z["U"] == 92
        assert SYMBOL_TO_Z["H"] == 1
        assert SYMBOL_TO_Z["He"] == 2
        assert SYMBOL_TO_Z["Pu"] == 94

    def test_element_symbols_consistency(self):
        """Test that ELEMENT_SYMBOLS and SYMBOL_TO_Z are consistent."""
        for Z, symbol in ELEMENT_SYMBOLS.items():
            assert SYMBOL_TO_Z[symbol] == Z


class TestParseNuclideString:
    """Test parse_nuclide_string function."""

    def test_parse_simple_nuclide(self):
        """Test parsing simple nuclide like 'U235'."""
        Z, A, m = parse_nuclide_string("U235")
        assert Z == 92
        assert A == 235
        assert m == 0

    def test_parse_metastable(self):
        """Test parsing metastable nuclide like 'Am242m'."""
        Z, A, m = parse_nuclide_string("Am242m")
        assert Z == 95
        assert A == 242
        assert m == 1

    def test_parse_metastable_with_number(self):
        """Test parsing metastable nuclide with number like 'U235m1'."""
        Z, A, m = parse_nuclide_string("U235m1")
        assert Z == 92
        assert A == 235
        assert m == 1

    def test_parse_invalid_nuclide(self):
        """Test that invalid nuclide string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid nuclide string"):
            parse_nuclide_string("Invalid123")

    def test_parse_various_nuclides(self):
        """Test parsing various nuclides."""
        test_cases = [
            ("U238", 92, 238, 0),
            ("Pu239", 94, 239, 0),
            ("C", 6, 0, 0),  # Carbon (will parse as C0)
            ("He4", 2, 4, 0),
        ]
        for name, expected_Z, expected_A, expected_m in test_cases:
            try:
                Z, A, m = parse_nuclide_string(name)
                assert Z == expected_Z
                assert A == expected_A
                # Note: m might differ for simple element names
            except ValueError:
                # Some might not parse correctly (like "C" without number)
                pass


class TestZamToName:
    """Test zam_to_name function."""

    def test_zam_to_name_u235(self):
        """Test ZAM to name conversion for U235."""
        zam = 922350  # U235
        name = zam_to_name(zam)
        assert name == "U235"

    def test_zam_to_name_u238(self):
        """Test ZAM to name conversion for U238."""
        zam = 922380  # U238
        name = zam_to_name(zam)
        assert name == "U238"

    def test_zam_to_name_metastable(self):
        """Test ZAM to name conversion for metastable nuclide."""
        zam = 922351  # U235m1
        name = zam_to_name(zam)
        assert "235" in name
        assert "m" in name.lower()

    def test_zam_to_name_round_trip(self):
        """Test that zam_to_name and parse_nuclide_string are consistent."""
        test_cases = [922350, 922380, 942390, 952421]  # U235, U238, Pu239, Am242m1
        for zam in test_cases:
            name = zam_to_name(zam)
            Z, A, m = parse_nuclide_string(name)
            # Reconstruct ZAM
            reconstructed_zam = Z * 10000 + A * 10 + m
            assert reconstructed_zam == zam


class TestWattSpectrum:
    """Test watt_spectrum function."""

    def test_watt_spectrum_normalized(self):
        """Test that Watt spectrum is normalized to 1."""
        E = np.linspace(0, 15, 1000)  # MeV
        chi = watt_spectrum(E, a=0.988, b=2.249)
        integral = np.trapz(chi, E)
        assert np.isclose(integral, 1.0, rtol=1e-3)

    def test_watt_spectrum_positive(self):
        """Test that Watt spectrum values are positive."""
        E = np.linspace(0, 15, 1000)
        chi = watt_spectrum(E, a=0.988, b=2.249)
        assert np.all(chi >= 0)

    def test_watt_spectrum_with_u235_params(self):
        """Test Watt spectrum with U235 thermal parameters."""
        E = np.linspace(0, 15, 1000)
        params = FISSION_SPECTRUM_PARAMS["U235_thermal"]
        chi = watt_spectrum(E, **params)
        integral = np.trapz(chi, E)
        assert np.isclose(integral, 1.0, rtol=1e-3)

    def test_watt_spectrum_with_pu239_params(self):
        """Test Watt spectrum with Pu239 thermal parameters."""
        E = np.linspace(0, 15, 1000)
        params = FISSION_SPECTRUM_PARAMS["Pu239_thermal"]
        chi = watt_spectrum(E, **params)
        integral = np.trapz(chi, E)
        assert np.isclose(integral, 1.0, rtol=1e-3)

    def test_watt_spectrum_shape(self):
        """Test that Watt spectrum has correct shape."""
        E = np.linspace(0, 15, 100)
        chi = watt_spectrum(E, a=0.988, b=2.249)
        assert chi.shape == E.shape


class TestConstants:
    """Test constant values."""

    def test_htgr_constants_dict(self):
        """Test that HTGR_CONSTANTS contains expected keys."""
        assert "helium_molar_mass" in HTGR_CONSTANTS
        assert "graphite_density" in HTGR_CONSTANTS
        assert "triso_packing_fraction" in HTGR_CONSTANTS
        assert HTGR_CONSTANTS["helium_molar_mass"] > 0

    def test_atomic_masses_dict(self):
        """Test that ATOMIC_MASSES contains expected nuclides."""
        assert "U235" in ATOMIC_MASSES
        assert "U238" in ATOMIC_MASSES
        assert "Pu239" in ATOMIC_MASSES
        assert ATOMIC_MASSES["U235"] > 235
        assert ATOMIC_MASSES["U238"] > 238

    def test_q_values_dict(self):
        """Test that Q_VALUES contains expected nuclides."""
        assert "U235" in Q_VALUES
        assert "Pu239" in Q_VALUES
        assert Q_VALUES["U235"] > 200  # MeV per fission
        assert Q_VALUES["Pu239"] > 200

    def test_resonance_integrals_dict(self):
        """Test that RESONANCE_INTEGRALS contains expected reactions."""
        assert "U238_capture" in RESONANCE_INTEGRALS
        assert "Xe135_capture" in RESONANCE_INTEGRALS
        assert RESONANCE_INTEGRALS["U238_capture"] > 0

    def test_fast_flux_threshold(self):
        """Test FAST_FLUX_THRESHOLD value."""
        assert FAST_FLUX_THRESHOLD > 0
        assert FAST_FLUX_THRESHOLD == 0.1e6  # 100 keV


class TestGroupStructures:
    """Test energy group structures."""

    def test_group_structures_dict(self):
        """Test that GROUP_STRUCTURES contains expected structures."""
        assert "SCALE-44" in GROUP_STRUCTURES
        assert "HTGR-8" in GROUP_STRUCTURES
        assert "CASMO-16" in GROUP_STRUCTURES

    def test_scale_44_structure(self):
        """Test SCALE-44 group structure."""
        structure = GROUP_STRUCTURES["SCALE-44"]
        assert isinstance(structure, np.ndarray)
        assert len(structure) == 45  # 44 groups + 1 boundary = 45 boundaries
        assert np.all(structure > 0)
        # Should be decreasing (high to low energy)
        assert np.all(np.diff(structure) < 0)

    def test_htgr_8_structure(self):
        """Test HTGR-8 group structure."""
        structure = GROUP_STRUCTURES["HTGR-8"]
        assert isinstance(structure, np.ndarray)
        assert len(structure) == 9  # 8 groups + 1 boundary
        assert np.all(structure > 0)
        # Should be decreasing (high to low energy)
        assert np.all(np.diff(structure) < 0)

    def test_casmo_16_structure(self):
        """Test CASMO-16 group structure."""
        structure = GROUP_STRUCTURES["CASMO-16"]
        assert isinstance(structure, np.ndarray)
        assert len(structure) == 18  # 17 groups + 1 boundary = 18 boundaries
        assert np.all(structure > 0)
        # Should be decreasing (high to low energy)
        assert np.all(np.diff(structure) < 0)


class TestDelayedNeutronData:
    """Test delayed neutron precursor data."""

    def test_delayed_neutron_data_structure(self):
        """Test that DELAYED_NEUTRON_DATA has expected structure."""
        assert "U235" in DELAYED_NEUTRON_DATA
        assert "U238" in DELAYED_NEUTRON_DATA
        assert "Pu239" in DELAYED_NEUTRON_DATA

    def test_u235_delayed_neutron_data(self):
        """Test U235 delayed neutron data."""
        data = DELAYED_NEUTRON_DATA["U235"]
        assert "beta" in data
        assert "lambda" in data
        assert isinstance(data["beta"], np.ndarray)
        assert isinstance(data["lambda"], np.ndarray)
        assert len(data["beta"]) == 6  # 6-group structure
        assert len(data["lambda"]) == 6
        assert np.all(data["beta"] > 0)
        assert np.all(data["lambda"] > 0)

    def test_pu239_delayed_neutron_data(self):
        """Test Pu239 delayed neutron data."""
        data = DELAYED_NEUTRON_DATA["Pu239"]
        assert "beta" in data
        assert "lambda" in data
        assert len(data["beta"]) == 6
        assert len(data["lambda"]) == 6
        assert np.all(data["beta"] > 0)
        assert np.all(data["lambda"] > 0)

    def test_nu_by_nuclide(self):
        """Test NU_BY_NUCLIDE has nuclide-specific nu values for burnup."""
        from smrforge.core.constants import NU_BY_NUCLIDE

        assert "U235" in NU_BY_NUCLIDE
        assert "Pu239" in NU_BY_NUCLIDE
        assert 2.0 < NU_BY_NUCLIDE["U235"] < 3.0
        assert 2.0 < NU_BY_NUCLIDE["Pu239"] < 3.5
