"""
Surrogate validation report - compare predictions vs reference physics.

Pro tier: SurrogateValidationReport with save_json, save_pdf.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np


@dataclass
class SurrogateValidationReport:
    """
    Report comparing surrogate predictions vs reference physics results.

    Attributes:
        metric_name: Name of output metric (e.g., k_eff)
        n_samples: Number of comparison points
        mae: Mean Absolute Error
        rmse: Root Mean Square Error
        max_err: Maximum absolute error
        pred_vs_ref: List of (pred, ref) pairs for detailed analysis
    """

    metric_name: str = "output"
    n_samples: int = 0
    mae: float = 0.0
    rmse: float = 0.0
    max_err: float = 0.0
    pred_vs_ref: List[tuple] = field(default_factory=list)

    def save_json(self, path: Union[str, Path]) -> None:
        """Save report to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "metric_name": self.metric_name,
            "n_samples": self.n_samples,
            "mae": self.mae,
            "rmse": self.rmse,
            "max_err": self.max_err,
            "pred_vs_ref": [
                [float(p), float(r)] for p, r in self.pred_vs_ref
            ],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def save_pdf(self, path: Union[str, Path]) -> None:
        """Save report to PDF using reportlab or similar."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table
            from reportlab.lib.units import inch

            doc = SimpleDocTemplate(
                str(path),
                pagesize=letter,
                rightMargin=inch,
                leftMargin=inch,
                topMargin=inch,
                bottomMargin=inch,
            )
            styles = getSampleStyleSheet()
            story = []

            story.append(Paragraph("Surrogate Validation Report", styles["Title"]))
            story.append(Spacer(1, 12))

            story.append(Paragraph(f"Metric: {self.metric_name}", styles["Heading2"]))
            story.append(Paragraph(f"Samples: {self.n_samples}", styles["Normal"]))
            story.append(Paragraph(f"MAE: {self.mae:.6f}", styles["Normal"]))
            story.append(Paragraph(f"RMSE: {self.rmse:.6f}", styles["Normal"]))
            story.append(Paragraph(f"Max Error: {self.max_err:.6f}", styles["Normal"]))
            story.append(Spacer(1, 12))

            if self.pred_vs_ref:
                rows = [["Predicted", "Reference"]] + [
                    [f"{p:.6f}", f"{r:.6f}"]
                    for p, r in self.pred_vs_ref[:50]  # limit rows
                ]
                if len(self.pred_vs_ref) > 50:
                    rows.append(["...", f"({len(self.pred_vs_ref)} total)"])
                t = Table(rows)
                story.append(Paragraph("Predicted vs Reference (sample)", styles["Heading2"]))
                story.append(t)

            doc.build(story)

        except ImportError as e:
            raise ImportError(
                "PDF export requires reportlab. pip install reportlab or smrforge-pro[reporting]"
            ) from e


def generate_validation_report(
    predictions: np.ndarray,
    reference: np.ndarray,
    metric_name: str = "output",
) -> SurrogateValidationReport:
    """
    Compare surrogate predictions vs reference physics results.

    Args:
        predictions: Array of surrogate predictions
        reference: Array of reference (physics) values
        metric_name: Name of output metric for report

    Returns:
        SurrogateValidationReport with MAE, RMSE, max_err, pred_vs_ref
    """
    pred = np.asarray(predictions).flatten()
    ref = np.asarray(reference).flatten()
    if pred.shape != ref.shape:
        raise ValueError(
            f"Shape mismatch: predictions {pred.shape} vs reference {ref.shape}"
        )

    n = len(pred)
    err = pred - ref
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err ** 2)))
    max_err = float(np.max(np.abs(err)))
    pred_vs_ref = [(float(p), float(r)) for p, r in zip(pred, ref)]

    return SurrogateValidationReport(
        metric_name=metric_name,
        n_samples=n,
        mae=mae,
        rmse=rmse,
        max_err=max_err,
        pred_vs_ref=pred_vs_ref,
    )
