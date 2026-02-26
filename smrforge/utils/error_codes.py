"""
SMRForge error codes for user-friendly diagnostics and documentation.

Each error includes:
- SMR-Exxx code
- Message
- Recovery suggestions
- Doc link: https://smrforge.io/docs/errors/Exxx (or docs/guides/error-codes.md)
"""

from dataclasses import dataclass, field
from typing import List, Optional

_DOC_BASE = "https://smrforge.io/docs/errors"
_DOC_FALLBACK = "https://github.com/SMRFORGE/smrforge/blob/main/docs/guides/error-codes.md"


@dataclass
class ErrorCode:
    """Error code definition with message and recovery suggestions."""

    code: str  # e.g. "SMR-E001"
    message: str
    suggestions: List[str] = field(default_factory=list)
    doc_path: Optional[str] = None

    @property
    def doc_url(self) -> str:
        """Full URL to error documentation."""
        if self.doc_path:
            return f"{_DOC_BASE}/{self.doc_path}"
        code_num = self.code.replace("SMR-", "")
        return f"{_DOC_BASE}/{code_num}"

    def format(self, detail: Optional[str] = None, include_doc: bool = True) -> str:
        """Format error message with code, detail, suggestions, and doc link."""
        parts = [f"{self.code}: {self.message}"]
        if detail:
            parts.append(f" {detail}")
        if self.suggestions:
            parts.append("\nRecovery suggestions:\n  - ")
            parts.append("\n  - ".join(self.suggestions))
        if include_doc:
            parts.append(f"\nSee: {self.doc_url}")
        return "".join(parts)


# Registry of error codes. Add new codes here.
ERROR_REGISTRY: dict[str, ErrorCode] = {
    "E001": ErrorCode(
        code="SMR-E001",
        message="Solver failed to converge",
        suggestions=[
            "Increase max_iterations (e.g., 2000 instead of 1000)",
            "Relax tolerance (e.g., 1e-5 instead of 1e-6)",
            "Check cross-section data validity",
            "Verify geometry is physical (non-zero dimensions)",
        ],
    ),
    "E002": ErrorCode(
        code="SMR-E002",
        message="k_eff or flux became invalid (NaN/Inf)",
        suggestions=[
            "Check for negative cross sections in your data",
            "Verify all input values are finite",
            "Check geometry mesh is valid",
            "Ensure power density is positive",
        ],
    ),
    "E003": ErrorCode(
        code="SMR-E003",
        message="ENDF or nuclear data not found",
        suggestions=[
            "Run: smrforge data setup",
            "Set SMRFORGE_ENDF_DIR to your ENDF data directory",
            "Use: python -m smrforge.core.endf_setup",
            "See: docs/technical/endf-documentation.md",
        ],
    ),
    "E004": ErrorCode(
        code="SMR-E004",
        message="Solution validation failed (non-physical result)",
        suggestions=[
            "Review enrichment (use fraction 0.195, not 19.5)",
            "Check geometry dimensions (core_height, core_diameter)",
            "Verify cross-section data matches material IDs",
        ],
    ),
    "E005": ErrorCode(
        code="SMR-E005",
        message="Invalid input parameter",
        suggestions=[
            "Check enrichment is 0-1 (fraction, not percent)",
            "Ensure power_mw > 0",
            "Verify temperatures are in Kelvin",
        ],
    ),
    "E006": ErrorCode(
        code="SMR-E006",
        message="Burnup solver failed",
        suggestions=[
            "Check time_steps are in days",
            "Verify power_density is positive",
            "Ensure initial_enrichment is in valid range",
        ],
    ),
    "E007": ErrorCode(
        code="SMR-E007",
        message="Pro feature requires SMRForge Pro",
        suggestions=[
            "Install: pip install smrforge-pro",
            "See: docs/community_vs_pro.md",
        ],
    ),
    "E008": ErrorCode(
        code="SMR-E008",
        message="Geometry or mesh error",
        suggestions=[
            "Call geometry.build_mesh() before solving",
            "Check mesh dimensions (n_radial, n_axial) are positive",
            "Verify core_height and core_diameter are valid",
        ],
    ),
}


def get_error_code(key: str) -> Optional[ErrorCode]:
    """Get error code by key (e.g., 'E001' or 'SMR-E001')."""
    code = key.replace("SMR-", "") if key.startswith("SMR-") else key
    return ERROR_REGISTRY.get(code)


def format_error(
    code_key: str,
    detail: Optional[str] = None,
    suggestions_extra: Optional[List[str]] = None,
    include_doc: bool = True,
) -> str:
    """
    Format an error message with code, suggestions, and doc link.

    Args:
        code_key: Error code key (e.g., 'E001', 'SMR-E001')
        detail: Optional additional detail to append
        suggestions_extra: Optional extra suggestions to add
        include_doc: Whether to include doc URL

    Returns:
        Formatted error string
    """
    ec = get_error_code(code_key)
    if ec is None:
        base = f"SMR-{code_key}: {detail}" if detail else f"SMR-{code_key}: Unknown error"
        if include_doc:
            return f"{base}\nSee: {_DOC_FALLBACK}"
        return base

    all_suggestions = list(ec.suggestions)
    if suggestions_extra:
        all_suggestions.extend(suggestions_extra)

    if all_suggestions != ec.suggestions:
        ec = ErrorCode(
            code=ec.code,
            message=ec.message,
            suggestions=all_suggestions,
            doc_path=ec.doc_path,
        )

    return ec.format(detail=detail, include_doc=include_doc)


class SMRForgeError(RuntimeError):
    """SMRForge error with code and recovery suggestions."""

    def __init__(
        self,
        code_key: str,
        detail: Optional[str] = None,
        suggestions_extra: Optional[List[str]] = None,
    ):
        self.code_key = code_key
        self.detail = detail
        msg = format_error(code_key, detail, suggestions_extra)
        super().__init__(msg)
