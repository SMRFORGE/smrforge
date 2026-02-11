"""
Simple report generation for SMRForge Community.

Generates Markdown (and optionally PDF) design summaries from analysis results.
For full regulatory reports and traceability matrices, see SMRForge Pro.
"""

from smrforge.reporting.simple_report import generate_markdown_report

__all__ = ["generate_markdown_report"]
