"""
Edge export: quantize and export for CPU/embedded deployment.
"""

from pathlib import Path
from typing import Any, Optional

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.edge")


def quantize_surrogate(surrogate: Any, bits: int = 8) -> Any:
    """Quantize surrogate for smaller footprint (scaffold)."""
    logger.info("Quantize surrogate to %d bits (scaffold)", bits)
    return surrogate


def export_for_edge(
    surrogate: Any,
    output_path: Path,
    format: str = "onnx",
    optimize: bool = True,
) -> Path:
    """Export surrogate for edge deployment (ONNX, TFLite)."""
    output_path = Path(output_path)
    if format == "onnx":
        try:
            import torch
            model = getattr(surrogate, "_backend", surrogate)
            if hasattr(model, "parameters"):
                in_dim = next(model.parameters()).shape[1] if list(model.parameters()) else 4
            else:
                in_dim = 4
            dummy = torch.randn(1, in_dim)
            torch.onnx.export(model, dummy, str(output_path), input_names=["input"], output_names=["output"])
        except ImportError:
            logger.warning("PyTorch required for ONNX export")
        except Exception as e:
            logger.warning("ONNX export failed: %s", e)
    return output_path
