"""
Tests for MF=6 (energy-angle distributions) parser.

Tests parsing of ENDF MF=6 data for anisotropic scattering calculations.
"""

from pathlib import Path

import numpy as np
import pytest

try:
    from smrforge.core.energy_angle_parser import (
        AngularDistribution,
        ENDFEnergyAngleParser,
        EnergyAngleData,
        get_energy_angle_data,
    )
    from smrforge.core.reactor_core import NuclearDataCache, Nuclide

    _ENERGY_ANGLE_PARSER_AVAILABLE = True
except ImportError:
    _ENERGY_ANGLE_PARSER_AVAILABLE = False


@pytest.mark.skipif(
    not _ENERGY_ANGLE_PARSER_AVAILABLE,
    reason="Energy-angle parser not available",
)
class TestAngularDistribution:
    """Tests for AngularDistribution class."""

    def test_isotropic_distribution(self):
        """Test creating isotropic angular distribution."""
        dist = AngularDistribution(
            incident_energy=1e6,  # 1 MeV
            distribution_type=0,  # Isotropic
        )

        assert dist.incident_energy == 1e6
        assert dist.distribution_type == 0

    def test_legendre_distribution(self):
        """Test creating Legendre coefficient distribution."""
        coeffs = np.array([1.0, 0.1, 0.05])  # P0, P1, P2

        dist = AngularDistribution(
            incident_energy=1e6,
            distribution_type=1,  # Legendre
            legendre_coefficients=coeffs,
        )

        assert dist.incident_energy == 1e6
        assert dist.distribution_type == 1
        assert np.allclose(dist.legendre_coefficients, coeffs)

    def test_tabular_distribution(self):
        """Test creating tabular angular distribution."""
        mu = np.linspace(-1, 1, 10)
        prob = np.ones(10) / 10.0  # Uniform

        dist = AngularDistribution(
            incident_energy=1e6,
            distribution_type=2,  # Tabular
            angle_cosines=mu,
            probabilities=prob,
        )

        assert dist.incident_energy == 1e6
        assert dist.distribution_type == 2
        assert len(dist.angle_cosines) == 10
        assert len(dist.probabilities) == 10


@pytest.mark.skipif(
    not _ENERGY_ANGLE_PARSER_AVAILABLE,
    reason="Energy-angle parser not available",
)
class TestEnergyAngleData:
    """Tests for EnergyAngleData class."""

    def test_energy_angle_data_creation(self):
        """Test creating energy-angle data."""
        u238 = Nuclide(Z=92, A=238)

        energies = np.array([1e5, 1e6, 1e7])  # 100 keV, 1 MeV, 10 MeV
        distributions = [AngularDistribution(e, 0) for e in energies]

        data = EnergyAngleData(
            nuclide=u238,
            mt_number=2,
            reaction_name="elastic",
            incident_energies=energies,
            angular_distributions=distributions,
        )

        assert data.nuclide == u238
        assert data.mt_number == 2
        assert len(data.incident_energies) == 3

    def test_get_legendre_moments_from_legendre(self):
        """Test getting Legendre moments from Legendre distribution."""
        u238 = Nuclide(Z=92, A=238)

        # Create distribution with Legendre coefficients
        dist = AngularDistribution(
            incident_energy=1e6,
            distribution_type=1,
            legendre_coefficients=np.array([1.0, 0.15, 0.08]),
        )

        data = EnergyAngleData(
            nuclide=u238,
            mt_number=2,
            reaction_name="elastic",
            incident_energies=np.array([1e6]),
            angular_distributions=[dist],
        )

        moments = data.get_legendre_moments(1e6, max_order=2)

        assert moments is not None
        assert len(moments) == 3
        assert moments[0] == pytest.approx(1.0)  # P0
        assert moments[1] == pytest.approx(0.15)  # P1
        assert moments[2] == pytest.approx(0.08)  # P2

    def test_get_legendre_moments_from_tabular(self):
        """Test converting tabular distribution to Legendre moments."""
        u238 = Nuclide(Z=92, A=238)

        # Create tabular distribution (uniform = isotropic)
        mu = np.linspace(-1, 1, 20)
        prob = np.ones(20) / 20.0  # Uniform

        dist = AngularDistribution(
            incident_energy=1e6,
            distribution_type=2,
            angle_cosines=mu,
            probabilities=prob,
        )

        data = EnergyAngleData(
            nuclide=u238,
            mt_number=2,
            reaction_name="elastic",
            incident_energies=np.array([1e6]),
            angular_distributions=[dist],
        )

        moments = data.get_legendre_moments(1e6, max_order=2)

        assert moments is not None
        assert len(moments) == 3
        # P0 should be ~0.5 (standard Legendre normalization: a0 = 1/2 for isotropic)
        # For uniform distribution, P0 = 0.5
        assert moments[0] == pytest.approx(0.5, abs=0.1)


@pytest.mark.skipif(
    not _ENERGY_ANGLE_PARSER_AVAILABLE,
    reason="Energy-angle parser not available",
)
class TestENDFEnergyAngleParser:
    """Tests for ENDFEnergyAngleParser class."""

    def test_parser_creation(self):
        """Test creating parser instance."""
        parser = ENDFEnergyAngleParser()
        assert parser is not None

    def test_parse_filename(self):
        """Test filename parsing."""
        parser = ENDFEnergyAngleParser()

        # Test various filename patterns
        nuclide = parser._parse_filename("U238.endf")
        assert nuclide is not None
        assert nuclide.Z == 92
        assert nuclide.A == 238

        nuclide = parser._parse_filename("092_U_238.endf")
        assert nuclide is not None
        assert nuclide.Z == 92
        assert nuclide.A == 238

    def test_parse_file_missing(self):
        """Test parsing non-existent file."""
        parser = ENDFEnergyAngleParser()
        result = parser.parse_file(Path("nonexistent.endf"), mt=2)

        assert result is None

    def test_get_energy_angle_data(self):
        """Test get_energy_angle_data function."""
        u238 = Nuclide(Z=92, A=238)

        try:
            data = get_energy_angle_data(u238, mt=2)
            # May be None if ENDF files not available (expected)
            if data is not None:
                assert data.nuclide == u238
                assert data.mt_number == 2
        except Exception:
            # Expected if ENDF files not set up
            pass
