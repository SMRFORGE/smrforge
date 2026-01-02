#!/usr/bin/env python3
"""
Script to reorganize SMRForge documentation according to DOCUMENTATION_REORGANIZATION_PLAN.md

This script:
1. Creates the new directory structure
2. Moves files to their new locations
3. Updates links in documentation files
4. Creates a summary of changes
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

# File mapping: old_path -> new_path
FILE_MAPPINGS = {
    # Guides
    "INSTALLATION.md": "docs/guides/installation.md",
    "TUTORIAL.md": "docs/guides/tutorial.md",
    "USAGE.md": "docs/guides/usage.md",
    "DOCKER.md": "docs/guides/docker.md",
    "HELP_SYSTEM_SUMMARY.md": "docs/guides/help-system.md",
    
    # Technical
    "ENDF_DOCUMENTATION.md": "docs/technical/endf-documentation.md",
    "NUCLEAR_DATA_BACKENDS.md": "docs/technical/nuclear-data-backends.md",
    "LOGGING_USAGE.md": "docs/technical/logging-usage.md",
    "COUPLING_REDUCTION.md": "docs/technical/coupling-reduction.md",
    "ENDF_CODEBASE_IMPROVEMENTS.md": "docs/technical/endf-codebase-improvements.md",
    "ENDF_IMPROVEMENTS_IMPLEMENTED.md": "docs/technical/endf-improvements-implemented.md",
    
    # Development
    "CODE_STYLE.md": "docs/development/code-style.md",
    "RELEASE_PROCESS.md": "docs/development/release-process.md",
    "TESTING_AND_COVERAGE.md": "docs/development/testing-and-coverage.md",
    "COVERAGE_EXCLUSIONS.md": "docs/development/coverage-exclusions.md",
    "COVERAGE_INVENTORY.md": "docs/development/coverage-inventory.md",
    
    # Roadmaps
    "DEVELOPMENT_ROADMAP.md": "docs/roadmaps/development-roadmap.md",
    "NEXT_STEPS.md": "docs/roadmaps/next-steps.md",
    "NEXT_WORK_OPTIONS.md": "docs/roadmaps/next-work-options.md",
    "IMPLEMENTATION_PRIORITY_ANALYSIS.md": "docs/roadmaps/implementation-priority-analysis.md",
    "OPTIMIZATION_SUGGESTIONS.md": "docs/roadmaps/optimization-suggestions.md",
    
    # Status
    "FEATURE_STATUS.md": "docs/status/feature-status.md",
    "PRODUCTION_READINESS_STATUS.md": "docs/status/production-readiness-status.md",
    "MISSING_FEATURES_ANALYSIS.md": "docs/status/missing-features-analysis.md",
    "TEST_COVERAGE_SUMMARY.md": "docs/status/test-coverage-summary.md",
    "SMRFORGE_FACT_SHEET.md": "docs/status/smrforge-fact-sheet.md",
    
    # Implementation
    "OPTIMIZATION_IMPLEMENTATION_SUMMARY.md": "docs/implementation/optimization.md",
    "CONVENIENCE_METHODS_SUMMARY.md": "docs/implementation/convenience-methods.md",
    "VISUALIZATION_IMPLEMENTATION_COMPLETE.md": "docs/implementation/visualization.md",
    "MESH_3D_IMPLEMENTATION_SUMMARY.md": "docs/implementation/mesh-3d.md",
    "PHOTON_GAMMA_INTEGRATION_SUMMARY.md": "docs/implementation/photon-gamma-integration.md",
    "THERMAL_SCATTERING_IMPLEMENTATION.md": "docs/implementation/thermal-scattering.md",
    "BURNUP_SOLVER_IMPLEMENTATION.md": "docs/implementation/burnup-solver.md",
    "FISSION_YIELDS_DECAY_IMPLEMENTATION.md": "docs/implementation/fission-yields-decay.md",
    "IMPLEMENTATION_COMPLETE_SUMMARY.md": "docs/implementation/complete-summary.md",
    "IMPLEMENTATION_STATUS_HIGH_MEDIUM.md": "docs/implementation/status-high-medium.md",
    "IMPLEMENTATION_SUMMARY_OPTIONS_1_2_4_6.md": "docs/implementation/options-1-2-4-6.md",
    "FEATURE_IMPLEMENTATION_SUMMARY.md": "docs/implementation/feature-implementation-summary.md",
    "NEXT_STEPS_IMPLEMENTATION_COMPLETE.md": "docs/implementation/next-steps-complete.md",
    
    # Validation
    "VALIDATION_SUMMARY.md": "docs/validation/validation-summary.md",
    "ENDF_WORKFLOW_VALIDATION.md": "docs/validation/endf-workflow-validation.md",
    "ENDF_FILE_TYPES_ANALYSIS.md": "docs/validation/endf-file-types-analysis.md",
    
    # Visualization
    "VISUALIZATION_READINESS_ASSESSMENT.md": "docs/visualization/readiness-assessment.md",
    "ADVANCED_VISUALIZATION_REQUIREMENTS.md": "docs/visualization/advanced-requirements.md",
    
    # Archive
    "PHASE1_COMPLETION_REPORT.md": "docs/archive/phase1-completion-report.md",
    "PHASE2_COMPLETION_REPORT.md": "docs/archive/phase2-completion-report.md",
    "PHASE3_COMPLETION_REPORT.md": "docs/archive/phase3-completion-report.md",
    "DOCUMENTATION_CONSOLIDATION_SUMMARY.md": "docs/archive/documentation-consolidation-summary.md",
    "DOCUMENTATION_UPDATE_2026_01_01.md": "docs/archive/documentation-update-2026-01-01.md",
}

# Files to keep in root
KEEP_IN_ROOT = {
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "DOCUMENTATION_INDEX.md",
    "DOCUMENTATION_REORGANIZATION_PLAN.md",
}

# Create reverse mapping for link updates
OLD_TO_NEW = {old: new for old, new in FILE_MAPPINGS.items()}
NEW_TO_OLD = {new: old for old, new in FILE_MAPPINGS.items()}


def create_directory_structure(base_path: Path):
    """Create all necessary directories."""
    directories = set()
    for new_path_str in FILE_MAPPINGS.values():
        new_path = Path(new_path_str)
        dir_path = base_path / new_path.parent
        directories.add(dir_path)
    
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")


def move_files(base_path: Path) -> List[Tuple[str, str]]:
    """Move files to their new locations."""
    moved_files = []
    
    for old_file, new_file in FILE_MAPPINGS.items():
        old_path = base_path / old_file
        new_path = base_path / Path(new_file)
        
        if old_path.exists():
            # Create parent directory if needed
            new_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            shutil.move(str(old_path), str(new_path))
            moved_files.append((old_file, new_file))
            print(f"Moved: {old_file} -> {new_file}")
        else:
            print(f"Warning: {old_file} not found, skipping")
    
    return moved_files


def update_links_in_file(file_path: Path, moved_files: List[Tuple[str, str]]) -> bool:
    """Update links in a markdown file."""
    if not file_path.exists() or not file_path.suffix == '.md':
        return False
    
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Update links for each moved file
        for old_file, new_file in moved_files:
            old_name = old_file.replace('.md', '')
            new_name = new_file.replace('.md', '').replace('docs/', '')
            
            # Pattern 1: [text](OLD_FILE.md)
            pattern1 = rf'\[([^\]]+)\]\({re.escape(old_file)}\)'
            replacement1 = rf'[\1]({new_file})'
            content = re.sub(pattern1, replacement1, content)
            
            # Pattern 2: [text](OLD_FILE) (without .md)
            pattern2 = rf'\[([^\]]+)\]\({re.escape(old_name)}\)'
            replacement2 = rf'[\1]({new_file})'
            content = re.sub(pattern2, replacement2, content)
            
            # Pattern 3: `OLD_FILE.md` references
            pattern3 = rf'`{re.escape(old_file)}`'
            replacement3 = f'`{new_file}`'
            content = re.sub(pattern3, replacement3, content)
            
            # Pattern 4: See [`OLD_FILE.md`](OLD_FILE.md)
            pattern4 = rf'\[`{re.escape(old_file)}`\]\({re.escape(old_file)}\)'
            replacement4 = f'[`{new_file}`]({new_file})'
            content = re.sub(pattern4, replacement4, content)
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False


def update_all_links(base_path: Path, moved_files: List[Tuple[str, str]]):
    """Update links in all markdown files."""
    updated_files = []
    
    # Update links in root markdown files
    for md_file in base_path.glob("*.md"):
        if md_file.name not in FILE_MAPPINGS:
            if update_links_in_file(md_file, moved_files):
                updated_files.append(md_file.name)
                print(f"Updated links in: {md_file.name}")
    
    # Update links in docs directory
    for md_file in base_path.rglob("*.md"):
        if md_file.name not in FILE_MAPPINGS.values():
            if update_links_in_file(md_file, moved_files):
                updated_files.append(md_file.name)
                print(f"Updated links in: {md_file.name}")
    
    return updated_files


def create_implementation_index(base_path: Path):
    """Create an index file for the implementation directory."""
    index_content = """# Implementation Summaries

**Last Updated:** January 1, 2026

This directory contains summaries of feature implementations in SMRForge.

## Available Summaries

"""
    
    impl_dir = base_path / "docs/implementation"
    if impl_dir.exists():
        for md_file in sorted(impl_dir.glob("*.md")):
            if md_file.name != "README.md":
                title = md_file.stem.replace("-", " ").replace("_", " ").title()
                index_content += f"- [{title}]({md_file.name})\n"
    
    index_path = impl_dir / "README.md"
    index_path.write_text(index_content, encoding='utf-8')
    print(f"Created implementation index: {index_path}")


def main():
    """Main reorganization function."""
    base_path = Path(__file__).parent.parent
    
    print("=" * 70)
    print("SMRForge Documentation Reorganization")
    print("=" * 70)
    print()
    
    print("Step 1: Creating directory structure...")
    create_directory_structure(base_path)
    print()
    
    print("Step 2: Moving files...")
    moved_files = move_files(base_path)
    print(f"Moved {len(moved_files)} files")
    print()
    
    print("Step 3: Updating links...")
    updated_files = update_all_links(base_path, moved_files)
    print(f"Updated links in {len(updated_files)} files")
    print()
    
    print("Step 4: Creating implementation index...")
    create_implementation_index(base_path)
    print()
    
    print("=" * 70)
    print("Reorganization complete!")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  - Files moved: {len(moved_files)}")
    print(f"  - Files with updated links: {len(updated_files)}")
    print()
    print("Next steps:")
    print("  1. Review the changes")
    print("  2. Update DOCUMENTATION_INDEX.md with new paths")
    print("  3. Update README.md links if needed")
    print("  4. Commit and push changes")


if __name__ == "__main__":
    main()

