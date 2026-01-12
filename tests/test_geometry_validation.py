"""
Comprehensive tests for geometry/validation.py to improve coverage.

Tests cover:
- ValidationReport and Gap dataclasses
- validate_geometry_completeness
- check_gaps_and_boundaries
- validate_material_connectivity
- check_distances_and_clearances
- validate_assembly_placement
- validate_control_rod_insertion
- validate_fuel_loading_pattern
- comprehensive_validation
- ImportError handling when geometry types unavailable
"""

import numpy as np
import pytest
from unittest.mock import patch, MagicMock

try:
    from smrforge.geometry.core_geometry import (
        PrismaticCore,
        PebbleBedCore,
        GraphiteBlock,
        Point3D,
        FuelChannel,
        CoolantChannel,
    )
    from smrforge.geometry.validation import (
        ValidationReport,
        Gap,
        validate_geometry_completeness,
        check_gaps_and_boundaries,
        validate_material_connectivity,
        check_distances_and_clearances,
        validate_assembly_placement,
        validate_control_rod_insertion,
        validate_fuel_loading_pattern,
        comprehensive_validation,
    )
    GEOMETRY_AVAILABLE = True
except ImportError:
    GEOMETRY_AVAILABLE = False


@pytest.fixture
def simple_prismatic_core():
    """Create a simple PrismaticCore for testing."""
    if not GEOMETRY_AVAILABLE:
        pytest.skip("Geometry module not available")
    
    core = PrismaticCore(
        core_diameter=200.0,
        core_height=800.0,
        n_rings=1,
    )
    return core


@pytest.fixture
def simple_pebble_bed_core():
    """Create a simple PebbleBedCore for testing."""
    if not GEOMETRY_AVAILABLE:
        pytest.skip("Geometry module not available")
    
    core = PebbleBedCore(
        core_diameter=200.0,
        core_height=800.0,
        packing_fraction=0.60,
    )
    return core


@pytest.fixture
def blocks_with_gaps():
    """Create blocks with gaps for testing."""
    if not GEOMETRY_AVAILABLE:
        pytest.skip("Geometry module not available")
    
    block1 = GraphiteBlock(
        id=1,
        position=Point3D(0, 0, 0),
        flat_to_flat=36.0,
        height=800.0,
    )
    block2 = GraphiteBlock(
        id=2,
        position=Point3D(40.0, 0, 0),  # Gap of ~4 cm
        flat_to_flat=36.0,
        height=800.0,
    )
    block3 = GraphiteBlock(
        id=3,
        position=Point3D(0, 40.0, 0),  # Gap of ~4 cm
        flat_to_flat=36.0,
        height=800.0,
    )
    return [block1, block2, block3]


class TestGap:
    """Test Gap dataclass."""
    
    def test_gap_creation(self):
        """Test creating a Gap."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        gap = Gap(
            element1_id="Block_1",
            element2_id="Block_2",
            distance=40.0,
            expected_distance=36.0,
            gap_size=4.0,
            location=Point3D(20.0, 0, 0),
        )
        
        assert gap.element1_id == "Block_1"
        assert gap.element2_id == "Block_2"
        assert gap.distance == 40.0
        assert gap.gap_size == 4.0
        assert gap.severity == "info"  # 4.0 < 5.0
    
    def test_gap_severity_error(self):
        """Test gap severity calculation for error (overlap)."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        gap = Gap(
            element1_id="Block_1",
            element2_id="Block_2",
            distance=30.0,
            expected_distance=36.0,
            gap_size=-6.0,  # Overlap
            location=Point3D(15.0, 0, 0),
        )
        
        assert gap.severity == "error"  # gap_size < -1.0
    
    def test_gap_severity_warning_overlap(self):
        """Test gap severity calculation for warning (small overlap)."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        gap = Gap(
            element1_id="Block_1",
            element2_id="Block_2",
            distance=35.5,
            expected_distance=36.0,
            gap_size=-0.5,  # Small overlap
            location=Point3D(17.75, 0, 0),
        )
        
        assert gap.severity == "warning"  # -1.0 < gap_size < 0
    
    def test_gap_severity_warning_large_gap(self):
        """Test gap severity calculation for warning (large gap)."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        gap = Gap(
            element1_id="Block_1",
            element2_id="Block_2",
            distance=45.0,
            expected_distance=36.0,
            gap_size=9.0,  # Large gap
            location=Point3D(22.5, 0, 0),
        )
        
        assert gap.severity == "warning"  # gap_size > 5.0


class TestValidationReport:
    """Test ValidationReport dataclass."""
    
    def test_validation_report_creation(self):
        """Test creating a ValidationReport."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        report = ValidationReport()
        
        assert report.valid is True
        assert len(report.errors) == 0
        assert len(report.warnings) == 0
        assert len(report.info) == 0
    
    def test_validation_report_add_error(self):
        """Test adding error to report."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        report = ValidationReport()
        report.add_error("Test error")
        
        assert report.valid is False
        assert len(report.errors) == 1
        assert "Test error" in report.errors
    
    def test_validation_report_add_warning(self):
        """Test adding warning to report."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        report = ValidationReport()
        report.add_warning("Test warning")
        
        assert report.valid is True  # Warnings don't invalidate
        assert len(report.warnings) == 1
        assert "Test warning" in report.warnings
    
    def test_validation_report_add_info(self):
        """Test adding info to report."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        report = ValidationReport()
        report.add_info("Test info")
        
        assert report.valid is True
        assert len(report.info) == 1
        assert "Test info" in report.info
    
    def test_validation_report_summary(self):
        """Test generating summary string."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        report = ValidationReport()
        report.add_error("Error 1")
        report.add_warning("Warning 1")
        report.add_info("Info 1")
        
        summary = report.summary()
        
        assert "INVALID" in summary
        assert "Errors: 1" in summary
        assert "Warnings: 1" in summary
        assert "Info: 1" in summary


class TestValidateGeometryCompleteness:
    """Test validate_geometry_completeness function."""
    
    def test_validate_prismatic_core_empty_blocks(self):
        """Test validation with empty blocks."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        core = PrismaticCore(
            core_diameter=200.0,
            core_height=800.0,
            n_rings=0,
        )
        core.blocks = []
        
        report = validate_geometry_completeness(core)
        
        assert not report.valid
        assert len(report.errors) > 0
        assert "No blocks found" in report.errors[0]
    
    def test_validate_prismatic_core_invalid_height(self):
        """Test validation with invalid core height."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        core = simple_prismatic_core()
        core.core_height = -100.0
        
        report = validate_geometry_completeness(core)
        
        assert not report.valid
        assert any("height must be positive" in err for err in report.errors)
    
    def test_validate_prismatic_core_invalid_diameter(self):
        """Test validation with invalid core diameter."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        core = simple_prismatic_core()
        core.core_diameter = 0.0
        
        report = validate_geometry_completeness(core)
        
        assert not report.valid
        assert any("diameter must be positive" in err for err in report.errors)
    
    def test_validate_prismatic_core_block_count_warning(self):
        """Test validation with fewer blocks than expected."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        core = PrismaticCore(
            core_diameter=200.0,
            core_height=800.0,
            n_rings=2,  # Expects 19 blocks (1 + 6 + 12)
        )
        # Only add a few blocks
        core.blocks = [
            GraphiteBlock(id=i, position=Point3D(0, 0, 0), flat_to_flat=36.0, height=800.0)
            for i in range(5)
        ]
        
        report = validate_geometry_completeness(core)
        
        assert any("Fewer blocks than expected" in warn for warn in report.warnings)
    
    def test_validate_pebble_bed_core_invalid_packing(self):
        """Test validation with invalid packing fraction."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        core = PebbleBedCore(
            core_diameter=200.0,
            core_height=800.0,
            packing_fraction=1.5,  # Invalid (> 1.0)
        )
        
        report = validate_geometry_completeness(core)
        
        assert not report.valid
        assert any("Invalid packing fraction" in err for err in report.errors)
    
    def test_validate_pebble_bed_core_unusual_packing(self):
        """Test validation with unusual packing fraction."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        core = PebbleBedCore(
            core_diameter=200.0,
            core_height=800.0,
            packing_fraction=0.40,  # Unusual (< 0.5)
        )
        
        report = validate_geometry_completeness(core)
        
        assert any("Unusual packing fraction" in warn for warn in report.warnings)
    
    def test_validate_geometry_unavailable(self):
        """Test validation when geometry types unavailable."""
        with patch('smrforge.geometry.validation._GEOMETRY_TYPES_AVAILABLE', False):
            with pytest.raises(ImportError, match="Geometry module not available"):
                validate_geometry_completeness(MagicMock())


class TestCheckGapsAndBoundaries:
    """Test check_gaps_and_boundaries function."""
    
    def test_check_gaps_basic(self, blocks_with_gaps):
        """Test basic gap checking."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        gaps = check_gaps_and_boundaries(blocks_with_gaps)
        
        assert len(gaps) > 0
        assert all(isinstance(gap, Gap) for gap in gaps)
    
    def test_check_gaps_empty_list(self):
        """Test gap checking with empty block list."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        gaps = check_gaps_and_boundaries([])
        
        assert len(gaps) == 0
    
    def test_check_gaps_single_block(self):
        """Test gap checking with single block."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        block = GraphiteBlock(
            id=1,
            position=Point3D(0, 0, 0),
            flat_to_flat=36.0,
            height=800.0,
        )
        
        gaps = check_gaps_and_boundaries([block])
        
        assert len(gaps) == 0
    
    def test_check_gaps_unavailable(self):
        """Test gap checking when geometry types unavailable."""
        with patch('smrforge.geometry.validation._GEOMETRY_TYPES_AVAILABLE', False):
            with pytest.raises(ImportError, match="Geometry module not available"):
                check_gaps_and_boundaries([])


class TestValidateMaterialConnectivity:
    """Test validate_material_connectivity function."""
    
    def test_validate_connectivity_basic(self, simple_prismatic_core):
        """Test basic material connectivity validation."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        report = validate_material_connectivity(simple_prismatic_core)
        
        assert isinstance(report, ValidationReport)
    
    def test_validate_connectivity_isolated_block(self, simple_prismatic_core):
        """Test connectivity validation with isolated block."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        # Add an isolated block far from others
        isolated_block = GraphiteBlock(
            id=999,
            position=Point3D(1000.0, 1000.0, 0),  # Far away
            flat_to_flat=36.0,
            height=800.0,
        )
        isolated_block.material = "graphite"
        simple_prismatic_core.blocks.append(isolated_block)
        
        report = validate_material_connectivity(simple_prismatic_core, check_continuity=True)
        
        # Should find isolated block warning
        assert any("isolated" in issue.lower() for issue in report.connectivity_issues)
    
    def test_validate_connectivity_unavailable(self):
        """Test connectivity validation when geometry types unavailable."""
        with patch('smrforge.geometry.validation._GEOMETRY_TYPES_AVAILABLE', False):
            with pytest.raises(ImportError, match="Geometry module not available"):
                validate_material_connectivity(MagicMock())


class TestCheckDistancesAndClearances:
    """Test check_distances_and_clearances function."""
    
    def test_check_clearances_basic(self, simple_prismatic_core):
        """Test basic clearance checking."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        report = check_distances_and_clearances(simple_prismatic_core)
        
        assert isinstance(report, ValidationReport)
    
    def test_check_clearances_unavailable(self):
        """Test clearance checking when geometry types unavailable."""
        with patch('smrforge.geometry.validation._GEOMETRY_TYPES_AVAILABLE', False):
            with pytest.raises(ImportError, match="Geometry module not available"):
                check_distances_and_clearances(MagicMock())


class TestValidateAssemblyPlacement:
    """Test validate_assembly_placement function."""
    
    def test_validate_assembly_basic(self, simple_prismatic_core):
        """Test basic assembly placement validation."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        report = validate_assembly_placement(simple_prismatic_core)
        
        assert isinstance(report, ValidationReport)
    
    def test_validate_assembly_empty_blocks(self):
        """Test assembly validation with empty blocks."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        core = PrismaticCore(
            core_diameter=200.0,
            core_height=800.0,
            n_rings=0,
        )
        core.blocks = []
        
        report = validate_assembly_placement(core)
        
        assert not report.valid
        assert "No blocks found" in report.errors[0]
    
    def test_validate_assembly_unavailable(self):
        """Test assembly validation when geometry types unavailable."""
        with patch('smrforge.geometry.validation._GEOMETRY_TYPES_AVAILABLE', False):
            with pytest.raises(ImportError, match="Geometry module not available"):
                validate_assembly_placement(MagicMock())


class TestValidateControlRodInsertion:
    """Test validate_control_rod_insertion function."""
    
    def test_validate_control_rods_no_rods(self, simple_prismatic_core):
        """Test control rod validation with no rods."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        report = validate_control_rod_insertion(simple_prismatic_core)
        
        assert isinstance(report, ValidationReport)
        assert any("No control rods found" in info for info in report.info)
    
    def test_validate_control_rods_unavailable(self):
        """Test control rod validation when geometry types unavailable."""
        with patch('smrforge.geometry.validation._GEOMETRY_TYPES_AVAILABLE', False):
            with pytest.raises(ImportError, match="Geometry module not available"):
                validate_control_rod_insertion(MagicMock())


class TestValidateFuelLoadingPattern:
    """Test validate_fuel_loading_pattern function."""
    
    def test_validate_fuel_loading_basic(self, simple_prismatic_core):
        """Test basic fuel loading pattern validation."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        report = validate_fuel_loading_pattern(simple_prismatic_core)
        
        assert isinstance(report, ValidationReport)
    
    def test_validate_fuel_loading_with_pattern(self, simple_prismatic_core):
        """Test fuel loading validation with expected pattern."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        expected_pattern = {"Block_1": "fuel", "Block_2": "reflector"}
        
        report = validate_fuel_loading_pattern(simple_prismatic_core, expected_pattern=expected_pattern)
        
        assert isinstance(report, ValidationReport)
    
    def test_validate_fuel_loading_unavailable(self):
        """Test fuel loading validation when geometry types unavailable."""
        with patch('smrforge.geometry.validation._GEOMETRY_TYPES_AVAILABLE', False):
            with pytest.raises(ImportError, match="Geometry module not available"):
                validate_fuel_loading_pattern(MagicMock())


class TestComprehensiveValidation:
    """Test comprehensive_validation function."""
    
    def test_comprehensive_validation_basic(self, simple_prismatic_core):
        """Test basic comprehensive validation."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        report = comprehensive_validation(simple_prismatic_core)
        
        assert isinstance(report, ValidationReport)
        assert hasattr(report, 'summary')
    
    def test_comprehensive_validation_pebble_bed(self, simple_pebble_bed_core):
        """Test comprehensive validation for pebble bed core."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        report = comprehensive_validation(simple_pebble_bed_core)
        
        assert isinstance(report, ValidationReport)
    
    def test_comprehensive_validation_options(self, simple_prismatic_core):
        """Test comprehensive validation with different options."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        report = comprehensive_validation(
            simple_prismatic_core,
            check_gaps=False,
            check_connectivity=False,
            check_clearances=False,
            check_assemblies=False,
            check_control_rods=False,
            check_fuel_loading=False,
        )
        
        assert isinstance(report, ValidationReport)
    
    def test_comprehensive_validation_with_gaps(self, simple_prismatic_core, blocks_with_gaps):
        """Test comprehensive validation that includes gap checking."""
        if not GEOMETRY_AVAILABLE:
            pytest.skip("Geometry module not available")
        
        simple_prismatic_core.blocks = blocks_with_gaps
        
        report = comprehensive_validation(simple_prismatic_core, check_gaps=True)
        
        assert isinstance(report, ValidationReport)
        assert len(report.gaps) > 0
