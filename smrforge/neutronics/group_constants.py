"""
Group constant generation for nodal and system codes.

Homogenizes multi-group cross-sections to few-group format.
Output compatible with nodal diffusion codes (e.g. DYN3D, PARCS).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from .solver import MultiGroupDiffusion

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.neutronics.group_constants")


@dataclass
class FewGroupConstants:
    """Few-group homogenized cross-section constants."""

    n_groups: int
    sigma_t: np.ndarray  # [n_materials, n_groups]
    sigma_a: np.ndarray
    sigma_f: np.ndarray
    nu_sigma_f: np.ndarray
    sigma_s: np.ndarray  # [n_materials, n_groups, n_groups]
    chi: np.ndarray
    D: np.ndarray
    materials: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Export to dictionary for JSON/serialization."""
        return {
            "n_groups": self.n_groups,
            "n_materials": len(self.materials),
            "sigma_t": self.sigma_t.tolist(),
            "sigma_a": self.sigma_a.tolist(),
            "sigma_f": self.sigma_f.tolist(),
            "nu_sigma_f": self.nu_sigma_f.tolist(),
            "sigma_s": self.sigma_s.tolist(),
            "chi": self.chi.tolist(),
            "D": self.D.tolist(),
            "materials": self.materials,
        }


class GroupConstantGenerator:
    """
    Generate few-group constants from multi-group flux-weighted homogenization.

    Collapses fine-group cross-sections using flux and optionally adjoint weighting.
    """

    def __init__(
        self,
        sigma_t: np.ndarray,
        sigma_a: np.ndarray,
        sigma_f: np.ndarray,
        nu_sigma_f: np.ndarray,
        sigma_s: np.ndarray,
        chi: np.ndarray,
        D: np.ndarray,
        n_fine_groups: int,
    ):
        self.sigma_t = np.asarray(sigma_t)
        self.sigma_a = np.asarray(sigma_a)
        self.sigma_f = np.asarray(sigma_f)
        self.nu_sigma_f = np.asarray(nu_sigma_f)
        self.sigma_s = np.asarray(sigma_s)
        self.chi = np.asarray(chi)
        self.D = np.asarray(D)
        self.n_fine = n_fine_groups

    def collapse_to_few_groups(
        self,
        flux: np.ndarray,
        group_boundaries: List[int],
        materials: Optional[List[str]] = None,
    ) -> FewGroupConstants:
        """
        Collapse fine groups to few groups using flux weighting.

        Args:
            flux: Fine-group flux [n_cells, n_fine] or [n_fine] for homogenized
            group_boundaries: Fine group indices defining few-group boundaries
                e.g. [0, 4, 8, 12] for 4 few-groups from 12 fine
            materials: Material labels

        Returns:
            FewGroupConstants with homogenized data
        """
        n_coarse = len(group_boundaries) - 1
        if flux.ndim == 1:
            flux = flux[np.newaxis, :]
        n_materials = self.sigma_t.shape[0]
        ng = self.sigma_t.shape[1]

        sigma_t_c = np.zeros((n_materials, n_coarse))
        sigma_a_c = np.zeros((n_materials, n_coarse))
        sigma_f_c = np.zeros((n_materials, n_coarse))
        nu_sigma_f_c = np.zeros((n_materials, n_coarse))
        sigma_s_c = np.zeros((n_materials, n_coarse, n_coarse))
        chi_c = np.zeros((n_materials, n_coarse))
        D_c = np.zeros((n_materials, n_coarse))

        for g in range(n_coarse):
            lo, hi = group_boundaries[g], group_boundaries[g + 1]
            if flux.shape[0] == 1:
                w = flux[0, lo:hi]
            else:
                w = np.mean(flux[:, lo:hi], axis=0)
            w_sum = np.sum(w) + 1e-30
            for m in range(n_materials):
                sigma_t_c[m, g] = np.sum(self.sigma_t[m, lo:hi] * w) / w_sum
                sigma_a_c[m, g] = np.sum(self.sigma_a[m, lo:hi] * w) / w_sum
                sigma_f_c[m, g] = np.sum(self.sigma_f[m, lo:hi] * w) / w_sum
                nu_sigma_f_c[m, g] = np.sum(self.nu_sigma_f[m, lo:hi] * w) / w_sum
                D_c[m, g] = np.sum(self.D[m, lo:hi] * w) / w_sum
                chi_c[m, g] = np.sum(self.chi[m, lo:hi] * w) / w_sum
                for gp in range(n_coarse):
                    lop, hip = group_boundaries[gp], group_boundaries[gp + 1]
                    if flux.shape[0] == 1:
                        wp = flux[0, lop:hip]
                    else:
                        wp = np.mean(flux[:, lop:hip], axis=0)
                    wp_sum = np.sum(wp) + 1e-30
                    # Flux-weighted scatter collapse: sum_g' sum_g sigma_s(g'->g) * phi(g') * phi(g)
                    sc = self.sigma_s[m, lo:hi, lop:hip]  # [ng_g, ng_gp]
                    wg = w[: sc.shape[0]]
                    wgp = wp[: sc.shape[1]]
                    sigma_s_c[m, g, gp] = np.sum(sc * np.outer(wg, wgp)) / (w_sum * wp_sum)

        mats = materials or [f"mat_{i}" for i in range(n_materials)]
        return FewGroupConstants(
            n_groups=n_coarse,
            sigma_t=sigma_t_c,
            sigma_a=sigma_a_c,
            sigma_f=sigma_f_c,
            nu_sigma_f=nu_sigma_f_c,
            sigma_s=sigma_s_c,
            chi=chi_c,
            D=D_c,
            materials=mats,
        )

    def export_to_file(self, fg: FewGroupConstants, path: Path, format: str = "json") -> None:
        """Export few-group constants to file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if format == "json":
            import json

            with open(path, "w") as f:
                json.dump(fg.to_dict(), f, indent=2)
        else:
            np.savez(
                path,
                sigma_t=fg.sigma_t,
                sigma_a=fg.sigma_a,
                sigma_f=fg.sigma_f,
                nu_sigma_f=fg.nu_sigma_f,
                sigma_s=fg.sigma_s,
                chi=fg.chi,
                D=fg.D,
            )

    @classmethod
    def from_diffusion_solver(
        cls,
        solver: "MultiGroupDiffusion",
        group_boundaries: List[int],
        materials: Optional[List[str]] = None,
    ) -> Tuple["GroupConstantGenerator", FewGroupConstants]:
        """
        Create generator and collapse from diffusion solver flux.

        Extracts cross-sections and flux from MultiGroupDiffusion,
        collapses to few groups, returns both generator and result.

        Args:
            solver: MultiGroupDiffusion with solved flux
            group_boundaries: Fine group indices e.g. [0, 4, 8, 12]
            materials: Material labels (default: mat_0, mat_1, ...)

        Returns:
            (GroupConstantGenerator, FewGroupConstants)
        """
        from .solver import MultiGroupDiffusion

        xs = solver.xs
        ng = xs.n_groups
        n_mats = xs.n_materials
        gen = cls(
            sigma_t=xs.sigma_t,
            sigma_a=xs.sigma_a,
            sigma_f=xs.sigma_f,
            nu_sigma_f=xs.nu_sigma_f,
            sigma_s=xs.sigma_s,
            chi=xs.chi,
            D=xs.D,
            n_fine_groups=ng,
        )
        flux = solver.flux
        if flux is None:
            raise ValueError("Diffusion solver must have solved flux")
        # Cell-wise flux: [nz, nr, ng] -> [nz*nr, ng]
        flux_flat = flux.reshape(-1, ng)
        fg = gen.collapse_to_few_groups(
            flux_flat, group_boundaries, materials=materials
        )
        return gen, fg
