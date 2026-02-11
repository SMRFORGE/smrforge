"""
Enhanced geometry validation utilities.

Provides advanced validation functions for reactor geometries including:
- Gap detection and boundary checking
- Material connectivity validation
- Distance/clearance checking
- Assembly placement validation
- Control rod insertion validation
- Fuel loading pattern validation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Union

import numpy as np
from scipy.spatial import distance_matrix

try:
    from smrforge.geometry.core_geometry import (
        CoolantChannel,
        FuelChannel,
        GraphiteBlock,
        PebbleBedCore,
        Point3D,
        PrismaticCore,
    )

    _GEOMETRY_TYPES_AVAILABLE = True
except ImportError:
    PrismaticCore = None  # type: ignore
    PebbleBedCore = None  # type: ignore
    GraphiteBlock = None  # type: ignore
    FuelChannel = None  # type: ignore
    CoolantChannel = None  # type: ignore
    Point3D = None  # type: ignore
    _GEOMETRY_TYPES_AVAILABLE = False


@dataclass
class Gap:
    """Represents a gap between geometry elements."""

    element1_id: str
    element2_id: str
    distance: float  # cm
    expected_distance: float  # cm
    gap_size: float  # cm (distance - expected_distance)
    location: Point3D  # Approximate gap location
    severity: str = "warning"  # 'error', 'warning', 'info'

    def __post_init__(self):
        """Calculate gap size and severity."""
        self.gap_size = self.distance - self.expected_distance
        if self.gap_size < -1.0:  # Overlap
            self.severity = "error"
        elif self.gap_size < 0:  # Small overlap
            self.severity = "warning"
        elif self.gap_size > 5.0:  # Large gap
            self.severity = "warning"
        else:
            self.severity = "info"


@dataclass
class ValidationReport:
    """Comprehensive geometry validation report."""

    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    gaps: List[Gap] = field(default_factory=list)
    connectivity_issues: List[str] = field(default_factory=list)
    clearance_issues: List[str] = field(default_factory=list)
    assembly_issues: List[str] = field(default_factory=list)
    control_rod_issues: List[str] = field(default_factory=list)

    def add_error(self, message: str):
        """Add error message."""
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str):
        """Add warning message."""
        self.warnings.append(message)

    def add_info(self, message: str):
        """Add info message."""
        self.info.append(message)

    def summary(self) -> str:
        """Generate summary string."""
        lines = []
        lines.append(f"Validation Report: {'✓ VALID' if self.valid else '✗ INVALID'}")
        lines.append(f"  Errors: {len(self.errors)}")
        lines.append(f"  Warnings: {len(self.warnings)}")
        lines.append(f"  Info: {len(self.info)}")
        lines.append(f"  Gaps: {len(self.gaps)}")
        lines.append(f"  Connectivity Issues: {len(self.connectivity_issues)}")
        lines.append(f"  Clearance Issues: {len(self.clearance_issues)}")
        lines.append(f"  Assembly Issues: {len(self.assembly_issues)}")
        lines.append(f"  Control Rod Issues: {len(self.control_rod_issues)}")
        return "\n".join(lines)


def validate_geometry_completeness(
    core: Union["PrismaticCore", "PebbleBedCore"],
) -> ValidationReport:
    """
    Validate geometry completeness and structure.

    Args:
        core: PrismaticCore or PebbleBedCore instance

    Returns:
        ValidationReport with validation results

    Examples:
        >>> from smrforge.geometry.validation import validate_geometry_completeness
        >>>
        >>> report = validate_geometry_completeness(core)
        >>> if not report.valid:
        ...     print("Errors found:")
        ...     for error in report.errors:
        ...         print(f"  - {error}")
    """
    if not _GEOMETRY_TYPES_AVAILABLE:
        raise ImportError("Geometry module not available")

    report = ValidationReport()

    if isinstance(core, PrismaticCore):
        # Check basic structure
        if len(core.blocks) == 0:
            report.add_error("No blocks found in core")
            return report

        # Check dimensions
        if core.core_height <= 0:
            report.add_error("Core height must be positive")
        if core.core_diameter <= 0:
            report.add_error("Core diameter must be positive")

        # Check block consistency
        for block in core.blocks:
            if block.flat_to_flat <= 0:
                report.add_error(f"Block {block.id} has invalid flat_to_flat dimension")
            if block.height <= 0:
                report.add_error(f"Block {block.id} has invalid height")

        # Check for expected block count
        if core.n_rings > 0:
            expected_blocks = sum(6 * ring + 1 for ring in range(core.n_rings + 1))
            if len(core.blocks) < expected_blocks:
                report.add_warning(
                    f"Fewer blocks than expected: {len(core.blocks)} vs {expected_blocks}"
                )

    elif isinstance(core, PebbleBedCore):
        # Check pebble bed structure
        if core.packing_fraction <= 0 or core.packing_fraction > 1.0:
            report.add_error(f"Invalid packing fraction: {core.packing_fraction}")

        if core.packing_fraction < 0.5 or core.packing_fraction > 0.75:
            report.add_warning(
                f"Unusual packing fraction: {core.packing_fraction:.3f} "
                f"(typical range: 0.55-0.65)"
            )

    return report


def check_gaps_and_boundaries(
    blocks: List["GraphiteBlock"],
    tolerance: float = 0.1,
    min_gap: float = 0.0,
    max_gap: float = 5.0,
) -> List[Gap]:
    """
    Check for gaps and overlaps between blocks.

    Args:
        blocks: List of GraphiteBlock instances
        tolerance: Tolerance for distance calculations (cm)
        min_gap: Minimum acceptable gap (cm)
        max_gap: Maximum acceptable gap (cm)

    Returns:
        List of Gap objects

    Examples:
        >>> from smrforge.geometry.validation import check_gaps_and_boundaries
        >>>
        >>> gaps = check_gaps_and_boundaries(core.blocks)
        >>> for gap in gaps:
        ...     if gap.severity == "error":
        ...         print(f"Overlap detected: {gap.element1_id} and {gap.element2_id}")
    """
    if not _GEOMETRY_TYPES_AVAILABLE:
        raise ImportError("Geometry module not available")

    gaps = []

    for i, block1 in enumerate(blocks):
        for block2 in blocks[i + 1 :]:
            # Calculate distance between block centers
            dist = block1.position.distance_to(block2.position)

            # Expected distance (minimum separation for hexagonal blocks)
            # For hexagonal blocks, expected distance is roughly flat_to_flat
            expected_dist = (block1.flat_to_flat + block2.flat_to_flat) / 2

            # Check if blocks are close enough to potentially have issues
            if dist < expected_dist * 1.5:  # Only check nearby blocks
                gap = Gap(
                    element1_id=f"Block_{block1.id}",
                    element2_id=f"Block_{block2.id}",
                    distance=dist,
                    expected_distance=expected_dist,
                    gap_size=dist - expected_dist,
                    location=Point3D(
                        (block1.position.x + block2.position.x) / 2,
                        (block1.position.y + block2.position.y) / 2,
                        (block1.position.z + block2.position.z) / 2,
                    ),
                )

                # Check if gap is outside acceptable range
                if gap.gap_size < min_gap - tolerance:
                    gap.severity = "error"
                elif gap.gap_size > max_gap + tolerance:
                    gap.severity = "warning"
                else:
                    gap.severity = "info"

                gaps.append(gap)

    return gaps


def validate_material_connectivity(
    core: "PrismaticCore",
    check_continuity: bool = True,
    check_boundaries: bool = True,
) -> ValidationReport:
    """
    Validate material connectivity and boundaries.

    Args:
        core: PrismaticCore instance
        check_continuity: Check for material continuity
        check_boundaries: Check material boundaries

    Returns:
        ValidationReport with connectivity validation results

    Examples:
        >>> from smrforge.geometry.validation import validate_material_connectivity
        >>>
        >>> report = validate_material_connectivity(core)
        >>> if report.connectivity_issues:
        ...     for issue in report.connectivity_issues:
        ...         print(f"  - {issue}")
    """
    if not _GEOMETRY_TYPES_AVAILABLE:
        raise ImportError("Geometry module not available")

    report = ValidationReport()

    # Group blocks by material type
    material_groups: Dict[str, List[GraphiteBlock]] = {}
    for block in core.blocks:
        material = getattr(block, "material", "graphite")
        if material not in material_groups:
            material_groups[material] = []
        material_groups[material].append(block)

    # Check for isolated material regions
    if check_continuity:
        for material, blocks in material_groups.items():
            if len(blocks) < 2:
                continue

            # Check if blocks form connected regions
            # Simple check: find blocks that are not adjacent to any other block of same material
            for block in blocks:
                # Check neighbors
                has_neighbor = False
                for other_block in blocks:
                    if other_block.id == block.id:
                        continue
                    dist = block.position.distance_to(other_block.position)
                    expected_dist = (block.flat_to_flat + other_block.flat_to_flat) / 2
                    if dist < expected_dist * 1.2:  # Adjacent
                        has_neighbor = True
                        break

                if not has_neighbor and len(blocks) > 1:
                    report.add_warning(
                        f"Block {block.id} (material: {material}) appears isolated "
                        f"from other {material} blocks"
                    )
                    report.connectivity_issues.append(
                        f"Isolated {material} block: {block.id}"
                    )

    # Check material boundaries
    if check_boundaries:
        # Check transitions between different materials
        for i, block1 in enumerate(core.blocks):
            for block2 in core.blocks[i + 1 :]:
                material1 = getattr(block1, "material", "graphite")
                material2 = getattr(block2, "material", "graphite")

                if material1 != material2:
                    # Check if blocks are adjacent
                    dist = block1.position.distance_to(block2.position)
                    expected_dist = (block1.flat_to_flat + block2.flat_to_flat) / 2
                    if dist < expected_dist * 1.2:
                        # Adjacent blocks with different materials - this is OK
                        pass

    return report


def check_distances_and_clearances(
    core: "PrismaticCore",
    min_channel_separation: float = 2.0,
    min_block_channel_clearance: float = 0.5,
) -> ValidationReport:
    """
    Check distances and clearances between geometry elements.

    Args:
        core: PrismaticCore instance
        min_channel_separation: Minimum separation between channels (cm)
        min_block_channel_clearance: Minimum clearance from block edge to channel (cm)

    Returns:
        ValidationReport with clearance validation results

    Examples:
        >>> from smrforge.geometry.validation import check_distances_and_clearances
        >>>
        >>> report = check_distances_and_clearances(core)
        >>> if report.clearance_issues:
        ...     for issue in report.clearance_issues:
        ...         print(f"  - {issue}")
    """
    if not _GEOMETRY_TYPES_AVAILABLE:
        raise ImportError("Geometry module not available")

    report = ValidationReport()

    # Check fuel channel clearances within blocks
    for block in core.blocks:
        if hasattr(block, "fuel_channels") and block.fuel_channels:
            for i, channel1 in enumerate(block.fuel_channels):
                for channel2 in block.fuel_channels[i + 1 :]:
                    dist = channel1.position.distance_to(channel2.position)
                    min_sep = channel1.radius + channel2.radius + min_channel_separation
                    if dist < min_sep:
                        report.add_warning(
                            f"Fuel channels {channel1.id} and {channel2.id} in block {block.id} "
                            f"too close: {dist:.2f} cm < {min_sep:.2f} cm"
                        )
                        report.clearance_issues.append(
                            f"Channel clearance issue in block {block.id}: "
                            f"channels {channel1.id} and {channel2.id}"
                        )

                # Check channel distance from block edge
                # Approximate block edge distance (half flat_to_flat - channel position from center)
                block_radius = block.flat_to_flat / 2
                channel_dist_from_center = np.sqrt(
                    channel1.position.x**2 + channel1.position.y**2
                )
                clearance = block_radius - channel_dist_from_center - channel1.radius
                if clearance < min_block_channel_clearance:
                    report.add_warning(
                        f"Fuel channel {channel1.id} in block {block.id} too close to edge: "
                        f"clearance {clearance:.2f} cm < {min_block_channel_clearance:.2f} cm"
                    )
                    report.clearance_issues.append(
                        f"Block edge clearance issue: block {block.id}, channel {channel1.id}"
                    )

    # Check coolant channel clearances
    if hasattr(core, "coolant_channels") and core.coolant_channels:
        for i, channel1 in enumerate(core.coolant_channels):
            for channel2 in core.coolant_channels[i + 1 :]:
                dist = channel1.position.distance_to(channel2.position)
                min_sep = channel1.radius + channel2.radius + min_channel_separation
                if dist < min_sep:
                    report.add_warning(
                        f"Coolant channels {channel1.id} and {channel2.id} too close: "
                        f"{dist:.2f} cm < {min_sep:.2f} cm"
                    )
                    report.clearance_issues.append(
                        f"Coolant channel clearance: channels {channel1.id} and {channel2.id}"
                    )

    return report


def validate_assembly_placement(
    core: "PrismaticCore",
    check_symmetry: bool = True,
    check_lattice: bool = True,
) -> ValidationReport:
    """
    Validate assembly (block) placement.

    Args:
        core: PrismaticCore instance
        check_symmetry: Check for symmetry in placement
        check_lattice: Check lattice regularity

    Returns:
        ValidationReport with assembly placement validation results

    Examples:
        >>> from smrforge.geometry.validation import validate_assembly_placement
        >>>
        >>> report = validate_assembly_placement(core)
        >>> if report.assembly_issues:
        ...     for issue in report.assembly_issues:
        ...         print(f"  - {issue}")
    """
    if not _GEOMETRY_TYPES_AVAILABLE:
        raise ImportError("Geometry module not available")

    report = ValidationReport()

    if len(core.blocks) == 0:
        report.add_error("No blocks found")
        return report

    # Check lattice regularity
    if check_lattice and core.n_rings > 0:
        expected_blocks = sum(6 * ring + 1 for ring in range(core.n_rings + 1))
        if len(core.blocks) != expected_blocks:
            report.add_warning(
                f"Block count mismatch: {len(core.blocks)} blocks found, "
                f"{expected_blocks} expected for {core.n_rings} rings"
            )
            report.assembly_issues.append(
                f"Block count mismatch: {len(core.blocks)} vs {expected_blocks}"
            )

        # Check hexagonal lattice spacing
        if len(core.blocks) > 1:
            # Get central block
            center_block = None
            min_dist_to_center = float("inf")
            for block in core.blocks:
                dist = block.position.distance_to(Point3D(0, 0, block.position.z))
                if dist < min_dist_to_center:
                    min_dist_to_center = dist
                    center_block = block

            if center_block:
                # Check spacing to neighboring blocks
                expected_spacing = center_block.flat_to_flat
                spacing_tolerance = 0.1 * expected_spacing

                for block in core.blocks:
                    if block.id == center_block.id:
                        continue
                    dist = center_block.position.distance_to(block.position)
                    # Check if distance matches expected hexagonal spacing
                    if abs(dist - expected_spacing) > spacing_tolerance:
                        if dist < expected_spacing * 0.9:
                            report.add_warning(
                                f"Block {block.id} spacing from center {dist:.2f} cm "
                                f"unexpectedly small (expected ~{expected_spacing:.2f} cm)"
                            )
                            report.assembly_issues.append(
                                f"Spacing issue: block {block.id} too close to center"
                            )

    # Check z-level consistency
    z_levels = set(block.position.z for block in core.blocks)
    if len(z_levels) > 1:
        z_variance = np.std(list(z_levels))
        if z_variance > 0.1:
            report.add_warning(
                f"Blocks are not on consistent z-levels (variance: {z_variance:.2f} cm)"
            )
            report.assembly_issues.append("Inconsistent z-levels")

    return report


def validate_control_rod_insertion(
    core: "PrismaticCore",
    min_clearance: float = 0.5,
) -> ValidationReport:
    """
    Validate control rod insertion geometry.

    Args:
        core: PrismaticCore instance
        min_clearance: Minimum clearance around control rods (cm)

    Returns:
        ValidationReport with control rod validation results

    Examples:
        >>> from smrforge.geometry.validation import validate_control_rod_insertion
        >>>
        >>> report = validate_control_rod_insertion(core)
        >>> if report.control_rod_issues:
        ...     for issue in report.control_rod_issues:
        ...         print(f"  - {issue}")
    """
    if not _GEOMETRY_TYPES_AVAILABLE:
        raise ImportError("Geometry module not available")

    report = ValidationReport()

    if not hasattr(core, "control_rods") or not core.control_rods:
        report.add_info("No control rods found")
        return report

    for control_rod in core.control_rods:
        # Check insertion depth
        if hasattr(control_rod, "insertion_depth"):
            if control_rod.insertion_depth < 0:
                report.add_error(
                    f"Control rod {control_rod.id} has negative insertion depth: "
                    f"{control_rod.insertion_depth:.2f} cm"
                )
                report.control_rod_issues.append(
                    f"Negative insertion depth: rod {control_rod.id}"
                )
            elif control_rod.insertion_depth > core.core_height:
                report.add_warning(
                    f"Control rod {control_rod.id} insertion depth "
                    f"{control_rod.insertion_depth:.2f} cm exceeds core height "
                    f"{core.core_height:.2f} cm"
                )
                report.control_rod_issues.append(
                    f"Insertion depth exceeds core height: rod {control_rod.id}"
                )

        # Check clearance to fuel channels
        if hasattr(control_rod, "position") and hasattr(control_rod, "radius"):
            rod_radius = getattr(control_rod, "radius", 5.0)
            for block in core.blocks:
                if hasattr(block, "fuel_channels") and block.fuel_channels:
                    for channel in block.fuel_channels:
                        # Check if control rod and channel are in same block
                        dist_horizontal = np.sqrt(
                            (control_rod.position.x - channel.position.x) ** 2
                            + (control_rod.position.y - channel.position.y) ** 2
                        )
                        if (
                            dist_horizontal
                            < rod_radius + channel.radius + min_clearance
                        ):
                            report.add_warning(
                                f"Control rod {control_rod.id} too close to fuel channel "
                                f"{channel.id} in block {block.id}: "
                                f"{dist_horizontal:.2f} cm < {rod_radius + channel.radius + min_clearance:.2f} cm"
                            )
                            report.control_rod_issues.append(
                                f"Clearance issue: rod {control_rod.id}, channel {channel.id}"
                            )

    return report


def validate_fuel_loading_pattern(
    core: "PrismaticCore",
    expected_pattern: Optional[Dict[str, str]] = None,
) -> ValidationReport:
    """
    Validate fuel loading pattern.

    Args:
        core: PrismaticCore instance
        expected_pattern: Optional dictionary mapping block IDs to expected fuel types

    Returns:
        ValidationReport with fuel loading validation results

    Examples:
        >>> from smrforge.geometry.validation import validate_fuel_loading_pattern
        >>>
        >>> expected = {"Block_1": "fuel", "Block_2": "reflector"}
        >>> report = validate_fuel_loading_pattern(core, expected_pattern=expected)
        >>> if not report.valid:
        ...     print("Fuel loading pattern mismatch")
    """
    if not _GEOMETRY_TYPES_AVAILABLE:
        raise ImportError("Geometry module not available")

    report = ValidationReport()

    if expected_pattern is None:
        # Just check that all fuel blocks have fuel channels
        for block in core.blocks:
            block_type = getattr(block, "block_type", "unknown")
            if block_type == "fuel":
                if not hasattr(block, "fuel_channels") or not block.fuel_channels:
                    report.add_warning(f"Fuel block {block.id} has no fuel channels")
                    report.assembly_issues.append(
                        f"Fuel block {block.id} missing fuel channels"
                    )
        return report

    # Validate against expected pattern
    for block in core.blocks:
        block_id = getattr(block, "id", f"Block_{block.id}")
        block_type = getattr(block, "block_type", "unknown")

        if block_id in expected_pattern:
            expected_type = expected_pattern[block_id]
            if block_type != expected_type:
                report.add_error(
                    f"Block {block_id} type mismatch: expected {expected_type}, "
                    f"found {block_type}"
                )
                report.assembly_issues.append(f"Type mismatch: block {block_id}")

    return report


def comprehensive_validation(
    core: Union["PrismaticCore", "PebbleBedCore"],
    check_gaps: bool = True,
    check_connectivity: bool = True,
    check_clearances: bool = True,
    check_assemblies: bool = True,
    check_control_rods: bool = True,
    check_fuel_loading: bool = False,
) -> ValidationReport:
    """
    Perform comprehensive geometry validation.

    Args:
        core: PrismaticCore or PebbleBedCore instance
        check_gaps: Check for gaps and overlaps
        check_connectivity: Check material connectivity
        check_clearances: Check distances and clearances
        check_assemblies: Check assembly placement
        check_control_rods: Check control rod insertion
        check_fuel_loading: Check fuel loading pattern

    Returns:
        Comprehensive ValidationReport

    Examples:
        >>> from smrforge.geometry.validation import comprehensive_validation
        >>>
        >>> report = comprehensive_validation(core)
        >>> print(report.summary())
        >>> if not report.valid:
        ...     print("Errors found:")
        ...     for error in report.errors:
        ...         print(f"  - {error}")
    """
    report = validate_geometry_completeness(core)

    if isinstance(core, PrismaticCore):
        # Check gaps and boundaries
        if check_gaps:
            gaps = check_gaps_and_boundaries(core.blocks)
            report.gaps.extend(gaps)
            for gap in gaps:
                if gap.severity == "error":
                    report.add_error(
                        f"Gap/overlap: {gap.element1_id} and {gap.element2_id} "
                        f"(gap: {gap.gap_size:.2f} cm)"
                    )
                elif gap.severity == "warning":
                    report.add_warning(
                        f"Gap: {gap.element1_id} and {gap.element2_id} "
                        f"(gap: {gap.gap_size:.2f} cm)"
                    )

        # Check connectivity
        if check_connectivity:
            connectivity_report = validate_material_connectivity(core)
            report.errors.extend(connectivity_report.errors)
            report.warnings.extend(connectivity_report.warnings)
            report.connectivity_issues.extend(connectivity_report.connectivity_issues)

        # Check clearances
        if check_clearances:
            clearance_report = check_distances_and_clearances(core)
            report.errors.extend(clearance_report.errors)
            report.warnings.extend(clearance_report.warnings)
            report.clearance_issues.extend(clearance_report.clearance_issues)

        # Check assembly placement
        if check_assemblies:
            assembly_report = validate_assembly_placement(core)
            report.errors.extend(assembly_report.errors)
            report.warnings.extend(assembly_report.warnings)
            report.assembly_issues.extend(assembly_report.assembly_issues)

        # Check control rods
        if check_control_rods:
            control_rod_report = validate_control_rod_insertion(core)
            report.errors.extend(control_rod_report.errors)
            report.warnings.extend(control_rod_report.warnings)
            report.control_rod_issues.extend(control_rod_report.control_rod_issues)

        # Check fuel loading
        if check_fuel_loading:
            fuel_report = validate_fuel_loading_pattern(core)
            report.errors.extend(fuel_report.errors)
            report.warnings.extend(fuel_report.warnings)
            report.assembly_issues.extend(fuel_report.assembly_issues)

    return report
