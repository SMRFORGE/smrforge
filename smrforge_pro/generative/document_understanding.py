"""
Document understanding: extract specs from PDF, Excel, Word.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.generative.document")


def extract_specs_from_document(
    path: Union[str, Path],
    format: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Extract reactor specs from document.

    Args:
        path: Path to PDF, Excel, or Word document
        format: Optional override ("pdf", "xlsx", "docx")
        **kwargs: Passed to parser

    Returns:
        Extracted spec dict
    """
    path = Path(path)
    fmt = format or path.suffix.lower().lstrip(".")
    if fmt == "pdf":
        return _extract_pdf(path)
    if fmt in ("xlsx", "xls"):
        return _extract_excel(path)
    if fmt in ("docx", "doc"):
        return _extract_docx(path)
    return {"source": str(path), "extracted": {}}


def _extract_pdf(path: Path) -> Dict:
    """Extract from PDF (scaffold)."""
    try:
        import PyPDF2
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = "".join(p.extract_text() or "" for p in reader.pages)
        return {"source": str(path), "text_preview": text[:500], "extracted": {}}
    except ImportError:
        return {"source": str(path), "extracted": {}, "note": "PyPDF2 required"}


def _extract_excel(path: Path) -> Dict:
    """Extract from Excel (scaffold)."""
    try:
        import pandas as pd
        df = pd.read_excel(path)
        return {"source": str(path), "columns": list(df.columns), "extracted": {}}
    except ImportError:
        return {"source": str(path), "extracted": {}, "note": "openpyxl required"}


def _extract_docx(path: Path) -> Dict:
    """Extract from Word (scaffold)."""
    try:
        import docx
        doc = docx.Document(path)
        text = "\n".join(p.text for p in doc.paragraphs)
        return {"source": str(path), "text_preview": text[:500], "extracted": {}}
    except ImportError:
        return {"source": str(path), "extracted": {}, "note": "python-docx required"}
