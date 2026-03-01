"""
Tests for variance reduction module.

Community: Basic ImportanceMap, WeightWindow.
Pro: Advanced CADIS from diffusion adjoint—raises ImportError when Pro not installed.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestVarianceReductionProGating:
    """Pro-tier variance reduction raises ImportError when Pro not available."""

    def test_generate_cadis_raises_without_pro(self):
        """generate_cadis_weight_windows_from_diffusion raises ImportError when Pro not available."""
        from smrforge.neutronics.variance_reduction import (
            generate_cadis_weight_windows_from_diffusion,
        )

        mock_reactor = MagicMock()
        mock_solver = MagicMock()
        with patch(
            "smrforge.neutronics.variance_reduction._pro_available", return_value=False
        ):
            with pytest.raises(ImportError, match="SMRForge Pro"):
                generate_cadis_weight_windows_from_diffusion(
                    reactor=mock_reactor, diffusion_solver=mock_solver
                )

    def test_export_weight_windows_raises_without_pro(self, tmp_path):
        """export_weight_windows_to_openmc raises ImportError when Pro not available."""
        from smrforge.neutronics.variance_reduction import (
            export_weight_windows_to_openmc,
        )

        ww = {"weight_windows": MagicMock(), "importance_map": MagicMock()}
        out = tmp_path / "ww.h5"
        with patch(
            "smrforge.neutronics.variance_reduction._pro_available", return_value=False
        ):
            with pytest.raises(ImportError, match="SMRForge Pro"):
                export_weight_windows_to_openmc(ww, output_path=out)

    def test_get_smr_preset_importance_raises_without_pro(self):
        """get_smr_preset_importance raises ImportError when Pro not available."""
        from smrforge.neutronics.variance_reduction import get_smr_preset_importance

        with patch(
            "smrforge.neutronics.variance_reduction._pro_available", return_value=False
        ):
            with pytest.raises(ImportError, match="SMRForge Pro"):
                get_smr_preset_importance("htgr")
