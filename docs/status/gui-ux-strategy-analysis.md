# GUI/UX Strategy Analysis and Recommendations

**Date:** January 2026  
**Purpose:** Analyze current codebase and provide strategic options for implementing a robust user experience and user interface

---

## Executive Summary

SMRForge currently has a **strong foundation** for user experience with:
- ✅ Rich terminal-based help system
- ✅ Interactive setup wizards
- ✅ Comprehensive visualization (Plotly, PyVista, Matplotlib)
- ✅ Convenience functions for easy usage
- ✅ Extensive documentation and examples

**Current State:** CLI-focused with excellent terminal UX and web-based interactive visualizations.

**Gap:** No desktop GUI or unified user interface for complete workflows.

---

## Current UX/UI Capabilities

### 1. Terminal/CLI Interface

**Strengths:**
- **Rich library integration** (`smrforge/help.py`) - Beautiful terminal output with colors, tables, panels
- **Interactive help system** - `smr.help()` with category-based navigation
- **Interactive setup wizard** - `setup_endf_data_interactive()` for ENDF data configuration
- **Progress indicators** - `tqdm` for data downloads
- **Error messages** - Actionable error messages with suggestions

**Files:**
- `smrforge/help.py` - Comprehensive help system
- `smrforge/core/endf_setup.py` - Interactive setup wizard
- `smrforge/data_downloader.py` - Progress bars and status updates

### 2. Visualization Interface

**Strengths:**
- **Plotly integration** - Interactive HTML visualizations
- **PyVista support** - 3D mesh visualization
- **Matplotlib** - Publication-quality 2D plots
- **Dashboard creation** - `create_dashboard()` for multi-view layouts
- **Export capabilities** - HTML, PNG, PDF, SVG, VTK, STL, HDF5

**Files:**
- `smrforge/visualization/advanced.py` - Advanced visualization functions
- `smrforge/visualization/plot_api.py` - Unified Plot API
- `smrforge/visualization/mesh_3d.py` - 3D mesh visualization

### 3. Convenience API

**Strengths:**
- **One-liner functions** - `quick_keff()`, `create_reactor()`, etc.
- **Preset designs** - Easy access to reference designs
- **SimpleReactor class** - High-level wrapper hiding complexity

**Files:**
- `smrforge/convenience.py` - Convenience functions
- `smrforge/presets/` - Preset reactor designs

### 4. Configuration Management

**Current:**
- Environment variables (`SMRFORGE_ENDF_DIR`)
- Configuration file support (`~/.smrforge/config.yaml`)
- Pydantic validation for all inputs

**Files:**
- `smrforge/core/reactor_core.py` - Configuration loading
- `smrforge/validation/models.py` - Pydantic models

---

## Strategic GUI/UX Options

### Option 1: Web-Based Dashboard (Recommended for Quick Start)

**Technology Stack:**
- **Dash** (Plotly) - Most aligned with existing Plotly visualizations
- **Streamlit** - Simpler, faster development
- **Gradio** - Easiest for ML/AI workflows
- **Panel** (Holoviz) - Most flexible, enterprise-ready

**Pros:**
- ✅ Leverages existing Plotly visualizations
- ✅ Cross-platform (works on any device with browser)
- ✅ Easy deployment (local server or cloud)
- ✅ No installation required for end users
- ✅ Can embed existing HTML visualizations
- ✅ Modern, responsive design
- ✅ Easy to share and collaborate

**Cons:**
- ⚠️ Requires web server (local or remote)
- ⚠️ Less "native" feel than desktop app
- ⚠️ May have performance limitations for heavy computations

**Implementation Strategy:**
1. **Phase 1:** Create Dash app with core workflows
   - Reactor creation wizard
   - Neutronics analysis interface
   - Results visualization dashboard
   - Data downloader interface

2. **Phase 2:** Add advanced features
   - Burnup analysis interface
   - Safety transient analysis
   - Multi-reactor comparison
   - Export/import workflows

3. **Phase 3:** Enhance UX
   - Real-time progress updates
   - Interactive parameter exploration
   - Saved projects/workflows
   - Collaboration features

**Code Structure:**
```
smrforge/gui/
  ├── __init__.py
  ├── web_app.py          # Main Dash/Streamlit app
  ├── components/
  │   ├── reactor_builder.py
  │   ├── analysis_panel.py
  │   ├── visualization_panel.py
  │   └── data_manager.py
  ├── layouts/
  │   ├── main_layout.py
  │   └── sidebar.py
  └── callbacks/
      ├── reactor_callbacks.py
      └── analysis_callbacks.py
```

**Dependencies:**
- `dash>=2.0` or `streamlit>=1.0`
- `dash-bootstrap-components` (for styling)
- Existing: `plotly`, `pydantic`

**Estimated Effort:** 2-4 weeks for MVP, 2-3 months for full-featured

---

### Option 2: Desktop GUI (Native Feel)

**Technology Stack:**
- **PyQt6/PySide6** - Most powerful, professional
- **Tkinter** - Built-in, simple
- **CustomTkinter** - Modern Tkinter with better UX
- **Dear PyGui** - Fast, modern, game-engine style

**Pros:**
- ✅ Native desktop application feel
- ✅ Better performance for heavy computations
- ✅ Can integrate with system (file dialogs, notifications)
- ✅ Offline-first (no server required)
- ✅ Professional appearance (PyQt)

**Cons:**
- ⚠️ Platform-specific builds required
- ⚠️ More complex development
- ⚠️ Larger installation size
- ⚠️ Requires GUI framework knowledge

**Implementation Strategy:**
1. **Phase 1:** Core application framework
   - Main window with menu bar
   - Project management (open/save)
   - Basic reactor builder

2. **Phase 2:** Analysis interfaces
   - Neutronics solver interface
   - Burnup analysis panel
   - Safety transient panel
   - Results viewer

3. **Phase 3:** Advanced features
   - 3D visualization integration (PyVista)
   - Parameter sweeps
   - Batch processing
   - Export capabilities

**Code Structure:**
```
smrforge/gui/
  ├── __init__.py
  ├── main_window.py       # Main application window
  ├── widgets/
  │   ├── reactor_builder_widget.py
  │   ├── analysis_widget.py
  │   ├── results_viewer.py
  │   └── visualization_widget.py
  ├── dialogs/
  │   ├── reactor_dialog.py
  │   └── settings_dialog.py
  └── utils/
      ├── project_manager.py
      └── theme_manager.py
```

**Dependencies:**
- `PyQt6>=6.0` or `PySide6>=6.0`
- `pyvista` (for 3D visualization)
- `qtconsole` (for embedded Python console)

**Estimated Effort:** 4-6 weeks for MVP, 3-4 months for full-featured

---

### Option 3: Hybrid Approach (CLI + Web Dashboard)

**Strategy:** Enhance existing CLI with optional web dashboard

**Components:**
1. **Enhanced CLI** - Keep and improve terminal interface
2. **Web Dashboard** - Optional web interface for visualization and analysis
3. **API Layer** - REST API for communication between CLI and web

**Pros:**
- ✅ Best of both worlds
- ✅ Users can choose their preferred interface
- ✅ CLI for automation, web for exploration
- ✅ Leverages existing strengths

**Cons:**
- ⚠️ More code to maintain
- ⚠️ Need to keep interfaces in sync

**Implementation:**
- Keep existing CLI/terminal features
- Add `smrforge serve` command to launch web dashboard
- Web dashboard reads from same project files
- CLI can trigger web dashboard for visualization

**Estimated Effort:** 3-4 weeks for web dashboard, ongoing for CLI enhancements

---

### Option 4: Jupyter-Based Interface

**Strategy:** Create Jupyter widgets and notebooks

**Technology:**
- **ipywidgets** - Interactive widgets
- **ipympl** - Interactive matplotlib
- **voila** - Convert notebooks to standalone apps

**Pros:**
- ✅ Familiar to scientific users
- ✅ Easy to share and document
- ✅ Can embed code and results together
- ✅ Great for education and tutorials

**Cons:**
- ⚠️ Requires Jupyter installation
- ⚠️ Less polished than dedicated GUI
- ⚠️ Limited for non-technical users

**Implementation:**
- Create interactive widgets for reactor building
- Notebook templates for common workflows
- Voila dashboards for non-technical users

**Estimated Effort:** 2-3 weeks for widgets, 1 week for notebooks

---

### Option 5: VS Code Extension

**Strategy:** Create VS Code extension for SMRForge

**Technology:**
- **VS Code Extension API**
- **Webview API** for custom UI
- **Language Server Protocol** for IntelliSense

**Pros:**
- ✅ Integrates with development workflow
- ✅ Great for developers using SMRForge
- ✅ Can leverage VS Code's UI components
- ✅ Built-in terminal and file management

**Cons:**
- ⚠️ Only for VS Code users
- ⚠️ Requires VS Code installation
- ⚠️ Less suitable for end users

**Estimated Effort:** 4-6 weeks for full extension

---

### Option 6: Progressive Enhancement (Recommended Long-Term)

**Strategy:** Start with web dashboard, add desktop app later

**Phases:**

**Phase 1: Web Dashboard (Months 1-3)**
- Quick to implement
- Leverages existing Plotly
- Cross-platform immediately
- Can be deployed as web app or local server

**Phase 2: Desktop Wrapper (Months 4-6)**
- Wrap web dashboard in Electron/PyQt WebView
- Native app feel
- Offline capability
- System integration

**Phase 3: Native Desktop (Months 7-12)**
- Full native desktop app if needed
- Better performance
- Advanced features

**Pros:**
- ✅ Incremental development
- ✅ Can validate UX before major investment
- ✅ Flexible deployment options
- ✅ Users get value early

**Cons:**
- ⚠️ May require refactoring between phases
- ⚠️ Longer overall timeline

---

## Recommended Strategy: Web-Based Dashboard (Dash)

### Why Dash?

1. **Perfect Alignment with Existing Code**
   - Already using Plotly extensively
   - Dash is built on Plotly
   - Can reuse existing visualization code

2. **Rapid Development**
   - Can have MVP in 2-3 weeks
   - Python-only (no frontend framework needed)
   - Rich component library

3. **Professional Appearance**
   - Dash Bootstrap Components for styling
   - Responsive design out of the box
   - Modern, clean interface

4. **Flexible Deployment**
   - Local server (`python -m smrforge.gui.web_app`)
   - Can be packaged as desktop app (Electron wrapper)
   - Can be deployed to cloud (Heroku, AWS, etc.)

### Implementation Plan

#### Phase 1: MVP (Weeks 1-3)

**Core Features:**
1. **Reactor Builder**
   - Form-based reactor creation
   - Preset selection
   - Parameter input with validation
   - Real-time parameter checking

2. **Analysis Panel**
   - Run neutronics analysis
   - Run burnup analysis
   - Run safety transients
   - Progress indicators

3. **Results Viewer**
   - k-eff display
   - Flux distribution plots
   - Power distribution plots
   - Export options

4. **Data Manager**
   - ENDF data download interface
   - Data validation
   - Configuration management

**UI Layout:**
```
┌─────────────────────────────────────────┐
│  SMRForge Dashboard                    │
├──────────┬─────────────────────────────┤
│          │                              │
│ Sidebar  │  Main Content Area           │
│          │                              │
│ - Reactor│  - Reactor Builder           │
│   Builder│  - Analysis Panel            │
│ - Analysis│  - Results Viewer           │
│ - Results│  - Visualizations            │
│ - Data   │                              │
│   Manager│                              │
│          │                              │
└──────────┴─────────────────────────────┘
```

#### Phase 2: Enhanced Features (Weeks 4-8)

**Additional Features:**
1. **Project Management**
   - Save/load projects
   - Project history
   - Export/import

2. **Advanced Visualization**
   - 3D geometry viewer
   - Interactive parameter exploration
   - Comparison views

3. **Workflow Automation**
   - Saved workflows
   - Batch processing
   - Parameter sweeps

4. **Collaboration**
   - Share projects
   - Export reports
   - Documentation integration

#### Phase 3: Polish & Optimization (Weeks 9-12)

**Enhancements:**
1. **Performance**
   - Caching
   - Background processing
   - Progress tracking

2. **UX Improvements**
   - Tutorial/onboarding
   - Help system integration
   - Error handling

3. **Deployment**
   - Desktop app wrapper (Electron)
   - Cloud deployment option
   - Installation packages

---

## Technical Architecture

### Component Structure

```python
# smrforge/gui/web_app.py
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="SMRForge Dashboard"
)

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(sidebar, width=3),
        dbc.Col(main_content, width=9)
    ])
])

# Callbacks
@app.callback(
    Output('results-panel', 'children'),
    Input('run-analysis-button', 'n_clicks'),
    State('reactor-spec', 'data')
)
def run_analysis(n_clicks, reactor_spec):
    # Use existing SMRForge functions
    from smrforge import create_reactor
    reactor = create_reactor(**reactor_spec)
    results = reactor.solve()
    return create_results_display(results)
```

### Integration with Existing Code

**Key Integration Points:**
1. **Reuse Existing Functions**
   - `smrforge.convenience` - All convenience functions
   - `smrforge.visualization` - All visualization functions
   - `smrforge.data_downloader` - Data management

2. **Pydantic Models**
   - Use existing validation models
   - Auto-generate forms from Pydantic schemas
   - Real-time validation

3. **Visualization**
   - Embed existing Plotly figures
   - Use existing dashboard functions
   - Export capabilities

---

## Alternative: Streamlit (Simpler Option)

If Dash seems too complex, **Streamlit** offers:

**Pros:**
- ✅ Even simpler than Dash
- ✅ Faster development
- ✅ Great for data science workflows
- ✅ Automatic layout management

**Cons:**
- ⚠️ Less customizable
- ⚠️ Less professional appearance
- ⚠️ Limited interactivity compared to Dash

**Example:**
```python
# smrforge/gui/streamlit_app.py
import streamlit as st
import smrforge as smr

st.title("SMRForge Dashboard")

# Reactor builder
preset = st.selectbox("Preset Design", smr.list_presets())
power = st.slider("Power (MW)", 1.0, 200.0, 10.0)

if st.button("Create Reactor"):
    reactor = smr.create_reactor(preset, power_mw=power)
    results = reactor.solve()
    
    st.metric("k-eff", f"{results['k_eff']:.6f}")
    
    # Use existing visualization
    fig = smr.visualization.plot_core_layout_2d(reactor.core)
    st.plotly_chart(fig)
```

---

## Comparison Matrix

| Feature | Dash | Streamlit | PyQt | Jupyter | VS Code |
|---------|------|-----------|------|---------|---------|
| **Development Speed** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Customization** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Professional Look** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Integration with Existing Code** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Deployment Ease** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Performance** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Learning Curve** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Cross-Platform** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

---

## Recommendation Summary

### **Primary Recommendation: Dash Web Dashboard**

**Rationale:**
1. Best alignment with existing Plotly codebase
2. Professional appearance and customization
3. Rapid development (MVP in 2-3 weeks)
4. Flexible deployment (local, cloud, or desktop wrapper)
5. Can evolve into desktop app later if needed

### **Secondary Recommendation: Streamlit (If Speed is Critical)**

**Rationale:**
1. Fastest development (MVP in 1-2 weeks)
2. Great for prototyping and validation
3. Can migrate to Dash later if needed
4. Excellent for data science workflows

### **Long-Term: Progressive Enhancement**

1. Start with Dash/Streamlit web dashboard
2. Add desktop wrapper (Electron) for native feel
3. Consider full native app (PyQt) if performance critical

---

## Implementation Roadmap

### Week 1-2: Setup & Core Framework
- [ ] Set up Dash/Streamlit project structure
- [ ] Create basic layout and navigation
- [ ] Integrate with existing SMRForge functions
- [ ] Set up routing and state management

### Week 3-4: Reactor Builder
- [ ] Create reactor builder form
- [ ] Integrate preset designs
- [ ] Add parameter validation
- [ ] Save/load reactor specifications

### Week 5-6: Analysis Interface
- [ ] Neutronics analysis panel
- [ ] Burnup analysis panel
- [ ] Safety transient panel
- [ ] Progress indicators and status

### Week 7-8: Visualization
- [ ] Results viewer
- [ ] Interactive plots
- [ ] 3D geometry viewer
- [ ] Export capabilities

### Week 9-10: Data Management
- [ ] ENDF data downloader interface
- [ ] Configuration management
- [ ] Data validation dashboard

### Week 11-12: Polish & Testing
- [ ] UX improvements
- [ ] Error handling
- [ ] Documentation
- [ ] Testing and bug fixes

---

## Next Steps

1. **Decision:** Choose Dash or Streamlit
2. **Prototype:** Create minimal working example (1-2 days)
3. **Validate:** Get user feedback on prototype
4. **Plan:** Detailed implementation plan based on feedback
5. **Implement:** Follow roadmap above

---

## Questions to Consider

1. **Target Users:**
   - Technical users (developers/scientists)?
   - Non-technical users (managers/analysts)?
   - Both?

2. **Deployment:**
   - Local only?
   - Cloud deployment needed?
   - Desktop app required?

3. **Features Priority:**
   - Which workflows are most important?
   - What's the minimum viable product?

4. **Timeline:**
   - When is this needed?
   - What's the budget/effort available?

---

**See Also:**
- [Dash Documentation](https://dash.plotly.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [PyQt Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Existing Visualization Guide](docs/status/openmc-visualization-gaps-analysis.md)
