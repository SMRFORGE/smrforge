"""
Callbacks for SMRForge Dashboard

All Dash callbacks organized by functionality.
"""

from smrforge.gui.callbacks.analysis import register_analysis_callbacks
from smrforge.gui.callbacks.data_manager import register_data_manager_callbacks
from smrforge.gui.callbacks.feature_lab import register_feature_lab_callbacks
from smrforge.gui.callbacks.geometry_designer import (
    register_geometry_designer_callbacks,
)
from smrforge.gui.callbacks.navigation import register_navigation_callbacks
from smrforge.gui.callbacks.projects import register_project_callbacks
from smrforge.gui.callbacks.reactor_builder import register_reactor_builder_callbacks
from smrforge.gui.callbacks.results import register_results_callbacks

__all__ = [
    "register_navigation_callbacks",
    "register_reactor_builder_callbacks",
    "register_geometry_designer_callbacks",
    "register_analysis_callbacks",
    "register_results_callbacks",
    "register_data_manager_callbacks",
    "register_project_callbacks",
    "register_feature_lab_callbacks",
]

# Theme callbacks are imported separately to avoid circular imports
