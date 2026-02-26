"""
Unified code-to-code verification (Pro).

Export the same reactor to SMRForge diffusion, built-in MC, OpenMC, Serpent, MCNP
and produce a single comparison report.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.workflows.code_verification")


@dataclass
class CodeResult:
    """Result from a single code."""

    code: str
    k_eff: Optional[float] = None
    k_std: Optional[float] = None
    output_path: Optional[Path] = None
    error: Optional[str] = None
    available: bool = True


@dataclass
class VerificationReport:
    """Unified verification report across codes."""

    reactor_name: str
    results: List[CodeResult] = field(default_factory=list)
    reference_code: str = "diffusion"
    output_dir: Path = field(default_factory=lambda: Path("verification_output"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reactor_name": self.reactor_name,
            "reference_code": self.reference_code,
            "results": [
                {
                    "code": r.code,
                    "k_eff": r.k_eff,
                    "k_std": r.k_std,
                    "output_path": str(r.output_path) if r.output_path else None,
                    "error": r.error,
                    "available": r.available,
                }
                for r in self.results
            ],
        }

    def save_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


def run_code_verification(
    reactor: Any,
    output_dir: Optional[Path] = None,
    codes: Optional[List[str]] = None,
) -> VerificationReport:
    """
    Run reactor through available codes and collect k-eff for comparison.

    Args:
        reactor: SimpleReactor or preset name
        output_dir: Where to write exports
        codes: List of codes to run (default: diffusion, monte_carlo, openmc, serpent, mcnp)

    Returns:
        VerificationReport with results from each available code
    """
    if output_dir is None:
        output_dir = Path("verification_output")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if codes is None:
        codes = ["diffusion", "monte_carlo", "openmc", "serpent", "mcnp"]

    try:
        from smrforge.convenience import create_reactor

        if isinstance(reactor, str):
            reactor = create_reactor(reactor)
    except ImportError:
        raise ImportError(
            "run_code_verification requires smrforge. pip install smrforge"
        ) from None

    reactor_name = (
        reactor.spec.name
        if hasattr(reactor, "spec") and hasattr(reactor.spec, "name")
        else "reactor"
    )
    report = VerificationReport(
        reactor_name=reactor_name,
        results=[],
        reference_code="diffusion",
        output_dir=output_dir,
    )

    # 1. SMRForge diffusion
    if "diffusion" in codes:
        try:
            results = reactor.solve()
            k = results.get("k_eff")
            report.results.append(
                CodeResult(
                    code="diffusion",
                    k_eff=float(k) if k is not None else None,
                    output_path=None,
                    available=True,
                )
            )
        except Exception as e:
            report.results.append(
                CodeResult(code="diffusion", error=str(e), available=True)
            )

    # 2. SMRForge built-in Monte Carlo
    if "monte_carlo" in codes:
        try:
            from smrforge.neutronics.monte_carlo import MonteCarloSolver
            from smrforge.neutronics.monte_carlo import SimplifiedGeometry
            from smrforge.validation.models import CrossSectionData

            core = reactor._get_core()
            geom = SimplifiedGeometry(
                core_diameter=core.core_diameter or 100,
                core_height=core.core_height or 200,
                reflector_thickness=30,
            )
            xs = getattr(reactor, "_xs_data", None) or CrossSectionData(
                n_groups=2,
                n_materials=2,
                sigma_t=[[0.5], [0.3]],
                sigma_a=[[0.05], [0.01]],
                sigma_f=[[0.04], [0.0]],
                nu_sigma_f=[[0.10], [0.0]],
                sigma_s=[[[0.41]], [[0.29]]],
                chi=[[1.0], [1.0]],
                D=[[1.0], [1.5]],
            )
            mc = MonteCarloSolver(geom, xs, n_particles=1000, n_generations=20)
            out = mc.run_eigenvalue()
            report.results.append(
                CodeResult(
                    code="monte_carlo",
                    k_eff=out.get("k_eff"),
                    k_std=out.get("k_std"),
                    available=True,
                )
            )
        except Exception as e:
            logger.debug(f"Monte Carlo not run: {e}")
            report.results.append(
                CodeResult(code="monte_carlo", error=str(e), available=False)
            )

    # 3. OpenMC export (run requires openmc executable)
    if "openmc" in codes:
        try:
            from smrforge.io.converters import OpenMCConverter

            openmc_dir = output_dir / "openmc"
            OpenMCConverter.export_reactor(reactor, openmc_dir, particles=500, batches=10)
            report.results.append(
                CodeResult(
                    code="openmc",
                    output_path=openmc_dir,
                    error="Export only; run openmc manually and add results",
                    available=True,
                )
            )
        except Exception as e:
            report.results.append(
                CodeResult(code="openmc", error=str(e), available=False)
            )

    # 4. Serpent export
    if "serpent" in codes:
        try:
            from smrforge.io.converters import SerpentConverter

            serp_path = output_dir / "reactor.serp"
            SerpentConverter.export_reactor(reactor, serp_path)
            report.results.append(
                CodeResult(
                    code="serpent",
                    output_path=serp_path,
                    error="Export only; run serpent manually",
                    available=True,
                )
            )
        except Exception as e:
            report.results.append(
                CodeResult(code="serpent", error=str(e), available=False)
            )

    # 5. MCNP export
    if "mcnp" in codes:
        try:
            from smrforge.io.converters import MCNPConverter

            mcnp_path = output_dir / "reactor.mcnp"
            MCNPConverter.export_reactor(reactor, mcnp_path)
            report.results.append(
                CodeResult(
                    code="mcnp",
                    output_path=mcnp_path,
                    error="Export only; run MCNP manually",
                    available=True,
                )
            )
        except Exception as e:
            report.results.append(
                CodeResult(code="mcnp", error=str(e), available=False)
            )

    report.save_json(output_dir / "verification_report.json")
    return report
