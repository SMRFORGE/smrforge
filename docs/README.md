# SMRForge Documentation

**Last Updated:** January 28, 2026

This directory contains all SMRForge documentation organized by category. See **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** for the full index.

---

## 📚 Documentation Structure

### User Guides (`guides/`)
- Installation instructions
- Tutorials
- Usage examples
- Docker guide
- Help system documentation

### Technical Documentation (`technical/`)
- ENDF file documentation
- Nuclear data backends
- Logging usage
- Architecture notes
- Regulatory traceability and compliance
- OpenMC comparison and improvements
- Multi-physics coupling framework
- Advanced control algorithms (MPC)

### Development (`development/`)
- Code style guide
- Release process
- Testing documentation
- Coverage information

### Roadmaps (`roadmaps/`)
- **CONSOLIDATED-ROADMAP** (primary), development roadmap
- Implementation priority analysis, optimization suggestions
- Superseded items in `archive/roadmaps-superseded/`

### Status (`status/`)
- Feature status
- Production readiness
- Missing features analysis
- Test coverage summary

### Implementation Summaries (`implementation/`)
- Help system implementation
- Optimization summaries
- Feature implementation details
- Complete implementation summaries

### Validation (`validation/`)
- Validation summaries
- ENDF workflow validation
- File type analysis

### Visualization
- See [Visualization Implementation](implementation/visualization.md) for current implementation
- Historical assessments archived in `archive/`

### Archive (`archive/`)
- Historical phase reports
- Documentation consolidation history
- Past updates
- Archived redundant/outdated documents:
  - Coverage improvements (merged into test-coverage-summary.md)
  - Outdated status reports (replaced by next-steps-complete.md)
  - Historical visualization assessments (features now implemented)

### Sphinx Documentation (`sphinx/` or root of `docs/`)
- API reference
- Generated documentation
- See `docs/README.md` for Sphinx build instructions

---

## 🔗 Quick Links

- **[Documentation Index](DOCUMENTATION_INDEX.md)** - Complete index of all documentation (see below)
- **[Main README](../README.md)** - Project overview
- **[Contributing Guide](../CONTRIBUTING.md)** - How to contribute

## 📚 Documentation Index

**Core Documentation (Root):**
- **[README.md](../README.md)** - Main project overview and quick start
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history and changes
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Guidelines for contributing
- **[LICENSE](../LICENSE)** - License information

**User Guides (`guides/`):**
- **[Installation Guide](guides/installation.md)** - Installation instructions
- **[Tutorial](guides/tutorial.md)** - Step-by-step tutorial for beginners
- **[Usage Guide](guides/usage.md)** - Usage guide with examples
- **[CLI Guide](guides/cli-guide.md)** - Command-line interface
- **[Dashboard Guide](guides/dashboard-guide.md)** - Web dashboard usage
- **[Docker Guide](guides/docker.md)** - Docker usage and troubleshooting

**Technical Documentation (`technical/`):**
- **[ENDF Documentation](technical/endf-documentation.md)** - Complete ENDF file usage guide
- **[Performance Optimizations](technical/OPTIMIZATION-STATUS-REPORT.md)** - Performance improvements (Phase 1-3 complete)
- **[Optimization Roadmap](technical/OPTIMIZATION-ROADMAP.md)** - Future optimization plans
- **[Phase 2 Summary](technical/PHASE2-IMPLEMENTATION-SUMMARY.md)** - Algorithmic improvements summary
- **[Regulatory Traceability Guide](technical/regulatory-traceability-guide.md)** - Complete guide for licensing applications and regulatory compliance
- **[OpenMC Regulatory Analysis](technical/openmc-regulatory-traceability-analysis.md)** - OpenMC comparison and SMRForge advantages
- **Multi-Physics Coupling** - Comprehensive unified coupling framework integrating neutronics, thermal-hydraulics, structural mechanics, control systems, and burnup
- **Advanced Control Systems** - Model Predictive Control (MPC) for predictive reactor control with constraint handling

**Status (`status/`):**
- **[Feature Status](status/feature-status.md)** - Module status and capabilities
- **[Production Readiness](status/production-readiness-status.md)** - Production readiness assessment
- **[Test Coverage](status/test-coverage-summary.md)** - Test coverage details
- **[Pain Points Assessment](status/pain-points-assessment.md)** - Gap analysis and pain points (includes recent improvements: creep models, multi-physics coupling, MPC)

**Development (`development/`):**
- **[Code Style Guide](development/code-style.md)** - Code style and formatting
- **[Release Process](development/release-process.md)** - Release workflow
- **[Testing Documentation](development/testing-and-coverage.md)** - Testing guidelines

**Archive (`archive/`):**
- Historical implementation summaries
- Past phase reports
- Archived redundant/outdated documents

---

## 📖 Finding Documentation

### For Users
- Start with `guides/installation.md`
- Read `guides/tutorial.md`
- Check `guides/usage.md`

### For Developers
- See `development/code-style.md`
- Review `development/release-process.md`
- Check `roadmaps/development-roadmap.md`

### For Contributors
- Read `../CONTRIBUTING.md`
- See `development/` for development guidelines
- Check `status/feature-status.md` for current status

---

## 🆕 Recent Features (January 2026)

- **Creep Models & Material Degradation**: Comprehensive creep models (primary, secondary, tertiary, irradiation-enhanced) and material degradation for long-term fuel rod analysis
- **Multi-Physics Coupling Framework**: Unified coupling framework (`MultiPhysicsCoupling`) integrating all physics domains with bidirectional feedback
- **Model Predictive Control (MPC)**: Advanced predictive control algorithm with prediction horizon optimization and constraint handling

## 🔄 Documentation Updates

When updating documentation:
1. Update the "Last Updated" date
2. Update cross-references if needed
3. Update `../DOCUMENTATION_INDEX.md` if structure changes

---

## 📝 Note

This directory structure is part of the documentation reorganization plan. See `../DOCUMENTATION_REORGANIZATION_PLAN.md` for details.
