"""
Code-to-code verification: run diffusion, MC, OpenMC, Serpent, MCNP on same reactor.

Pro tier — unified comparison report for V&V.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.workflows.code_verification")


def run_code_verification(
    reactor: Any,
    codes: Optional[List[str]] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Run multiple neutronics codes on the same reactor and produce unified comparison report.

    Args:
        reactor: Reactor instance (PrismaticCore, PebbleBedCore, or preset)
        codes: List of codes to run: ["diffusion", "mc", "openmc", "serpent", "mcnp"].
               Default: ["diffusion", "openmc"] (most available).
        output_path: Path to save report.json

    Returns:
        Dict with code results, k_eff per code, comparison summary.
    """
    codes = codes or ["diffusion", "openmc"]
    report: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "codes": codes,
        "results": {},
        "summary": {},
    }

    core = _get_core(reactor)

    if "diffusion" in codes:
        try:
            k = _run_diffusion(reactor)
            report["results"]["diffusion"] = {"k_eff": k}
        except Exception as e:
            report["results"]["diffusion"] = {"k_eff": None, "error": str(e)}

    if "mc" in codes or "openmc" in codes:
        try:
            k = _run_openmc(reactor)
            report["results"]["openmc"] = {"k_eff": k}
        except Exception as e:
            report["results"]["openmc"] = {"k_eff": None, "error": str(e)}

    if "serpent" in codes:
        try:
            k = _run_serpent(reactor)
            report["results"]["serpent"] = {"k_eff": k}
        except Exception as e:
            report["results"]["serpent"] = {"k_eff": None, "error": str(e)}

    if "mcnp" in codes:
        try:
            k = _run_mcnp(reactor)
            report["results"]["mcnp"] = {"k_eff": k}
        except Exception as e:
            report["results"]["mcnp"] = {"k_eff": None, "error": str(e)}

    keffs = {
        k: v.get("k_eff")
        for k, v in report["results"].items()
        if v.get("k_eff") is not None
    }
    if len(keffs) >= 2:
        vals = list(keffs.values())
        report["summary"] = {
            "mean_keff": sum(vals) / len(vals),
            "max_diff": max(vals) - min(vals),
            "codes_converged": list(keffs.keys()),
        }

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(report, indent=2), encoding="utf-8")

    return report


def _get_core(reactor):
    if hasattr(reactor, "core"):
        return reactor.core
    if hasattr(reactor, "build_core"):
        reactor.build_core()
        return getattr(reactor, "core", reactor)
    return reactor


def _run_diffusion(reactor):
    if hasattr(reactor, "solve_keff"):
        return reactor.solve_keff()
    from smrforge.convenience import create_reactor, get_design_point
    r = create_reactor(name=str(reactor)) if isinstance(reactor, str) else reactor
    return get_design_point(r).get("k_eff")


def _run_openmc(reactor):
    from smrforge.io.converters import OpenMCConverter
    from smrforge.io.openmc_run import run_and_parse

    out_dir = Path("code_verify_openmc")
    out_dir.mkdir(exist_ok=True)
    OpenMCConverter.export_reactor(reactor, out_dir)
    parsed = run_and_parse(out_dir)
    return parsed.get("k_eff")


def _run_serpent(reactor):
    from smrforge.io.converters import SerpentConverter
    from smrforge.io.serpent_run import run_serpent, parse_res_file

    out_dir = Path("code_verify_serpent")
    out_dir.mkdir(parents=True, exist_ok=True)
    inp = out_dir / "model.serp"
    SerpentConverter.export_reactor(reactor, inp)
    run_serpent(out_dir, inp)
    res = parse_res_file(out_dir / "model_res.m")
    return res.get("k_eff")

def _run_mcnp(reactor):
    from smrforge.io.converters import MCNPConverter
    from smrforge.io.mcnp_run import run_mcnp, parse_mcnp_output

    out_dir = Path("code_verify_mcnp")
    out_dir.mkdir(exist_ok=True)
    inp = out_dir / "model.inp"
    MCNPConverter.export_reactor(reactor, inp)
    proc = run_mcnp(out_dir, inp)
    parsed = parse_mcnp_output((proc.stdout or "") + (proc.stderr or ""))
    return parsed.get("k_eff")
