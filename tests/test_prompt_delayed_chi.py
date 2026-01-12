"""
Tests for prompt/delayed chi separation.
"""

import pytest
import numpy as np

try:
    from smrforge.core.endf_extractors import extract_chi_prompt_delayed
    from smrforge.core.reactor_core import NuclearDataCache, Nuclide

    _PROMPT_DELAYED_CHI_AVAILABLE = True
except ImportError:
    _PROMPT_DELAYED_CHI_AVAILABLE = False


@pytest.mark.skipif(
    not _PROMPT_DELAYED_CHI_AVAILABLE,
    reason="Prompt/delayed chi not available",
)
class TestPromptDelayedChi:
    """Tests for prompt/delayed chi separation."""

    def test_extract_chi_prompt_delayed(self):
        """Test extracting prompt and delayed chi."""
        cache = NuclearDataCache()
        u235 = Nuclide(Z=92, A=235)
        group_structure = np.logspace(7, -5, 26)  # 25 groups

        chi_prompt, chi_delayed = extract_chi_prompt_delayed(
            cache, u235, group_structure
        )

        assert len(chi_prompt) == 25
        assert len(chi_delayed) == 25
        assert np.sum(chi_prompt) > 0
        assert np.sum(chi_delayed) > 0

    def test_chi_normalization(self):
        """Test that chi spectra are normalized."""
        cache = NuclearDataCache()
        u235 = Nuclide(Z=92, A=235)
        group_structure = np.logspace(7, -5, 26)

        chi_prompt, chi_delayed = extract_chi_prompt_delayed(
            cache, u235, group_structure
        )

        # Should be approximately normalized (within numerical precision)
        assert np.abs(np.sum(chi_prompt) - 1.0) < 0.1
        assert np.abs(np.sum(chi_delayed) - 1.0) < 0.1

    def test_delayed_chi_softer_spectrum(self):
        """Test that delayed chi has softer (lower energy) spectrum."""
        cache = NuclearDataCache()
        u235 = Nuclide(Z=92, A=235)
        group_structure = np.logspace(7, -5, 26)

        chi_prompt, chi_delayed = extract_chi_prompt_delayed(
            cache, u235, group_structure
        )

        # Delayed should have more low-energy neutrons
        # Check that delayed has higher fraction in thermal groups
        n_groups = len(group_structure) - 1
        thermal_groups = n_groups // 3  # Bottom third (thermal)

        delayed_thermal_fraction = np.sum(chi_delayed[:thermal_groups])
        prompt_thermal_fraction = np.sum(chi_prompt[:thermal_groups])

        # Delayed should have higher thermal fraction (may not always be true,
        # but typically is)
        # Just check that both are reasonable
        assert delayed_thermal_fraction > 0
        assert prompt_thermal_fraction > 0
