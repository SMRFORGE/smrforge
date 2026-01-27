"""
Enhanced burnup visualization tools.

Provides visualization capabilities for:
- Batch comparison plots
- Refueling cycle visualization
- Multi-cycle burnup evolution
- Control rod effects visualization
"""

from typing import Dict, List, Optional, Any
from pathlib import Path

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.burnup.visualization")

# Try to import visualization backends
try:
    import matplotlib.pyplot as plt
    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    _MATPLOTLIB_AVAILABLE = False

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    _PLOTLY_AVAILABLE = True
except ImportError:
    _PLOTLY_AVAILABLE = False


def plot_batch_comparison(
    batch_inventories: Dict[int, Any],
    *,
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot burnup comparison across multiple fuel batches.
    
    Args:
        batch_inventories: Dictionary mapping batch number to NuclideInventory
        backend: Visualization backend ('plotly' or 'matplotlib')
        title: Optional plot title
        **kwargs: Additional plotting arguments
    
    Returns:
        Figure object (plotly) or (fig, ax) tuple (matplotlib)
    """
    if not batch_inventories:
        raise ValueError("batch_inventories cannot be empty")
    
    plot_title = title or "Burnup Comparison by Batch"
    
    if backend == "plotly":
        if not _PLOTLY_AVAILABLE:
            raise ImportError("plotly is required for plotly backend")
        
        fig = go.Figure()
        
        for batch, inventory in sorted(batch_inventories.items()):
            times_s = np.asarray(inventory.times, dtype=float)
            burnup = np.asarray(inventory.burnup, dtype=float)
            times_days = times_s / (24 * 3600)
            
            fig.add_trace(go.Scatter(
                x=times_days,
                y=burnup,
                mode="lines+markers",
                name=f"Batch {batch}",
                line=dict(width=2),
            ))
        
        fig.update_layout(
            title=plot_title,
            xaxis_title="Time (days)",
            yaxis_title="Burnup (MWd/kgU)",
            hovermode="x unified",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        )
        
        return fig
    
    elif backend == "matplotlib":
        if not _MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required for matplotlib backend")
        
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 6)))
        
        for batch, inventory in sorted(batch_inventories.items()):
            times_s = np.asarray(inventory.times, dtype=float)
            burnup = np.asarray(inventory.burnup, dtype=float)
            times_days = times_s / (24 * 3600)
            
            ax.plot(times_days, burnup, "o-", linewidth=2, label=f"Batch {batch}")
        
        ax.set_title(plot_title)
        ax.set_xlabel("Time (days)")
        ax.set_ylabel("Burnup (MWd/kgU)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        
        return fig, ax
    
    else:
        raise ValueError(f"Unknown backend: {backend}")


def plot_refueling_cycles(
    cycle_inventories: Dict[int, List[Any]],
    *,
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot burnup evolution across multiple refueling cycles.
    
    Args:
        cycle_inventories: Dictionary mapping assembly ID to list of NuclideInventory (one per cycle)
        backend: Visualization backend ('plotly' or 'matplotlib')
        title: Optional plot title
        **kwargs: Additional plotting arguments
    
    Returns:
        Figure object (plotly) or (fig, ax) tuple (matplotlib)
    """
    if not cycle_inventories:
        raise ValueError("cycle_inventories cannot be empty")
    
    plot_title = title or "Multi-Cycle Burnup Evolution"
    
    if backend == "plotly":
        if not _PLOTLY_AVAILABLE:
            raise ImportError("plotly is required for plotly backend")
        
        fig = go.Figure()
        
        for assembly_id, inventories in sorted(cycle_inventories.items()):
            all_times = []
            all_burnup = []
            
            for cycle_idx, inventory in enumerate(inventories):
                times_s = np.asarray(inventory.times, dtype=float)
                burnup = np.asarray(inventory.burnup, dtype=float)
                times_days = times_s / (24 * 3600)
                
                # Offset time by cycle number
                cycle_offset = cycle_idx * 365 * 3  # Assume 3-year cycles
                all_times.extend(times_days + cycle_offset)
                all_burnup.extend(burnup)
            
            fig.add_trace(go.Scatter(
                x=all_times,
                y=all_burnup,
                mode="lines+markers",
                name=f"Assembly {assembly_id}",
                line=dict(width=2),
            ))
        
        fig.update_layout(
            title=plot_title,
            xaxis_title="Time (days)",
            yaxis_title="Burnup (MWd/kgU)",
            hovermode="x unified",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        )
        
        return fig
    
    elif backend == "matplotlib":
        if not _MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required for matplotlib backend")
        
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (12, 6)))
        
        for assembly_id, inventories in sorted(cycle_inventories.items()):
            all_times = []
            all_burnup = []
            
            for cycle_idx, inventory in enumerate(inventories):
                times_s = np.asarray(inventory.times, dtype=float)
                burnup = np.asarray(inventory.burnup, dtype=float)
                times_days = times_s / (24 * 3600)
                
                # Offset time by cycle number
                cycle_offset = cycle_idx * 365 * 3  # Assume 3-year cycles
                all_times.extend(times_days + cycle_offset)
                all_burnup.extend(burnup)
            
            ax.plot(all_times, all_burnup, "o-", linewidth=2, label=f"Assembly {assembly_id}")
        
        ax.set_title(plot_title)
        ax.set_xlabel("Time (days)")
        ax.set_ylabel("Burnup (MWd/kgU)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        
        return fig, ax
    
    else:
        raise ValueError(f"Unknown backend: {backend}")


def plot_control_rod_effects(
    burnup_with_rods: Dict[str, Any],
    burnup_without_rods: Optional[Any] = None,
    *,
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Plot burnup evolution comparing cases with and without control rods.
    
    Args:
        burnup_with_rods: NuclideInventory or dict with control rod effects
        burnup_without_rods: Optional NuclideInventory without control rods (for comparison)
        backend: Visualization backend ('plotly' or 'matplotlib')
        title: Optional plot title
        **kwargs: Additional plotting arguments
    
    Returns:
        Figure object (plotly) or (fig, ax) tuple (matplotlib)
    """
    plot_title = title or "Control Rod Effects on Burnup"
    
    if backend == "plotly":
        if not _PLOTLY_AVAILABLE:
            raise ImportError("plotly is required for plotly backend")
        
        fig = go.Figure()
        
        # Plot with control rods
        if hasattr(burnup_with_rods, 'times'):
            inventory = burnup_with_rods
        else:
            inventory = burnup_with_rods.get('inventory', burnup_with_rods)
        
        times_s = np.asarray(inventory.times, dtype=float)
        burnup = np.asarray(inventory.burnup, dtype=float)
        times_days = times_s / (24 * 3600)
        
        fig.add_trace(go.Scatter(
            x=times_days,
            y=burnup,
            mode="lines+markers",
            name="With Control Rods",
            line=dict(width=2, color="red"),
        ))
        
        # Plot without control rods (if provided)
        if burnup_without_rods is not None:
            if hasattr(burnup_without_rods, 'times'):
                inventory_no_rods = burnup_without_rods
            else:
                inventory_no_rods = burnup_without_rods.get('inventory', burnup_without_rods)
            
            times_s_no = np.asarray(inventory_no_rods.times, dtype=float)
            burnup_no = np.asarray(inventory_no_rods.burnup, dtype=float)
            times_days_no = times_s_no / (24 * 3600)
            
            fig.add_trace(go.Scatter(
                x=times_days_no,
                y=burnup_no,
                mode="lines+markers",
                name="Without Control Rods",
                line=dict(width=2, color="blue", dash="dash"),
            ))
        
        fig.update_layout(
            title=plot_title,
            xaxis_title="Time (days)",
            yaxis_title="Burnup (MWd/kgU)",
            hovermode="x unified",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        )
        
        return fig
    
    elif backend == "matplotlib":
        if not _MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required for matplotlib backend")
        
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 6)))
        
        # Plot with control rods
        if hasattr(burnup_with_rods, 'times'):
            inventory = burnup_with_rods
        else:
            inventory = burnup_with_rods.get('inventory', burnup_with_rods)
        
        times_s = np.asarray(inventory.times, dtype=float)
        burnup = np.asarray(inventory.burnup, dtype=float)
        times_days = times_s / (24 * 3600)
        
        ax.plot(times_days, burnup, "o-", linewidth=2, color="red", label="With Control Rods")
        
        # Plot without control rods (if provided)
        if burnup_without_rods is not None:
            if hasattr(burnup_without_rods, 'times'):
                inventory_no_rods = burnup_without_rods
            else:
                inventory_no_rods = burnup_without_rods.get('inventory', burnup_without_rods)
            
            times_s_no = np.asarray(inventory_no_rods.times, dtype=float)
            burnup_no = np.asarray(inventory_no_rods.burnup, dtype=float)
            times_days_no = times_s_no / (24 * 3600)
            
            ax.plot(times_days_no, burnup_no, "s--", linewidth=2, color="blue", label="Without Control Rods")
        
        ax.set_title(plot_title)
        ax.set_xlabel("Time (days)")
        ax.set_ylabel("Burnup (MWd/kgU)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        
        return fig, ax
    
    else:
        raise ValueError(f"Unknown backend: {backend}")


def plot_burnup_dashboard_enhanced(
    inventory,
    batch_inventories: Optional[Dict[int, Any]] = None,
    *,
    time_unit: str = "days",
    backend: str = "plotly",
    title: Optional[str] = None,
    **kwargs,
):
    """
    Enhanced burnup dashboard with batch comparison and composition.
    
    Args:
        inventory: NuclideInventory instance
        batch_inventories: Optional dict of batch inventories for comparison
        time_unit: Time unit for display ('days', 'hours', 'years')
        backend: Visualization backend ('plotly' or 'matplotlib')
        title: Optional plot title
        **kwargs: Additional plotting arguments
    
    Returns:
        Figure object (plotly) or (fig, ax) tuple (matplotlib)
    """
    from ..visualization.material_composition import plot_burnup_dashboard
    
    # Use existing dashboard as base
    base_fig = plot_burnup_dashboard(inventory, time_unit=time_unit, backend=backend, title=title, **kwargs)
    
    if batch_inventories and backend == "plotly" and _PLOTLY_AVAILABLE:
        # Add batch comparison subplot
        if isinstance(base_fig, go.Figure):
            # Create subplot layout
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=("Burnup", "Composition (stacked)", "Batch Comparison"),
                shared_xaxes=True,
                vertical_spacing=0.08,
            )
            
            # Copy burnup plot
            for trace in base_fig.data[:1]:  # First trace is burnup
                fig.add_trace(trace, row=1, col=1)
            
            # Copy composition plot
            for trace in base_fig.data[1:]:  # Remaining traces are composition
                fig.add_trace(trace, row=2, col=1)
            
            # Add batch comparison
            for batch, batch_inv in sorted(batch_inventories.items()):
                times_s = np.asarray(batch_inv.times, dtype=float)
                burnup = np.asarray(batch_inv.burnup, dtype=float)
                times_days = times_s / (24 * 3600)
                
                fig.add_trace(go.Scatter(
                    x=times_days,
                    y=burnup,
                    mode="lines+markers",
                    name=f"Batch {batch}",
                    line=dict(width=2),
                ), row=3, col=1)
            
            fig.update_layout(
                title=title or "Enhanced Burnup Dashboard",
                height=900,
                hovermode="x unified",
            )
            
            return fig
    
    return base_fig
