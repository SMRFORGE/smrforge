"""Tests for advanced mesh generation module."""

import numpy as np
import pytest

from smrforge.geometry.mesh_generation import (
    AdvancedMeshGenerator,
    MeshQuality,
    MeshType,
    compute_mesh_gradient,
)


class TestMeshType:
    """Test MeshType enum."""

    def test_mesh_type_values(self):
        """Test mesh type enum values."""
        assert MeshType.STRUCTURED.value == "structured"
        assert MeshType.UNSTRUCTURED.value == "unstructured"
        assert MeshType.HYBRID.value == "hybrid"


class TestAdvancedMeshGenerator:
    """Test AdvancedMeshGenerator class."""

    def test_generator_creation(self):
        """Test mesh generator creation."""
        generator = AdvancedMeshGenerator(mesh_type=MeshType.STRUCTURED)
        assert generator.mesh_type == MeshType.STRUCTURED

        generator = AdvancedMeshGenerator(mesh_type=MeshType.UNSTRUCTURED)
        assert generator.mesh_type == MeshType.UNSTRUCTURED

    def test_generate_radial_mesh_uniform(self):
        """Test uniform radial mesh generation."""
        generator = AdvancedMeshGenerator()
        mesh = generator.generate_radial_mesh(core_diameter=300.0, n_points=50)

        assert len(mesh) == 50
        assert mesh[0] == 0.0  # Starts at center
        assert mesh[-1] == pytest.approx(150.0)  # Ends at radius
        assert np.all(mesh >= 0)  # All non-negative
        assert np.all(np.diff(mesh) > 0)  # Monotonically increasing

    def test_generate_radial_mesh_with_refinement(self):
        """Test radial mesh with local refinement."""
        generator = AdvancedMeshGenerator()
        refinement_regions = [
            (0.0, 50.0, 20),  # Refine inner region
            (100.0, 150.0, 15),  # Refine outer region
        ]

        mesh = generator.generate_radial_mesh(
            core_diameter=300.0, n_points=30, refinement_regions=refinement_regions
        )

        assert len(mesh) > 30  # Should have more points due to refinement
        assert mesh[0] == 0.0
        assert mesh[-1] == pytest.approx(150.0)

        # Check that refinement regions have more points
        inner_points = mesh[(mesh >= 0) & (mesh <= 50)]
        assert len(inner_points) > 10  # More points in refined region

    def test_generate_axial_mesh_uniform(self):
        """Test uniform axial mesh generation."""
        generator = AdvancedMeshGenerator()
        mesh = generator.generate_axial_mesh(core_height=793.0, n_points=50)

        assert len(mesh) == 50
        assert mesh[0] == 0.0  # Starts at bottom
        assert mesh[-1] == pytest.approx(793.0)  # Ends at top
        assert np.all(mesh >= 0)
        assert np.all(np.diff(mesh) > 0)

    def test_generate_axial_mesh_with_refinement(self):
        """Test axial mesh with local refinement."""
        generator = AdvancedMeshGenerator()
        refinement_regions = [
            (0.0, 100.0, 20),  # Refine bottom
            (600.0, 793.0, 15),  # Refine top
        ]

        mesh = generator.generate_axial_mesh(
            core_height=793.0, n_points=40, refinement_regions=refinement_regions
        )

        assert len(mesh) > 40  # Should have more points
        assert mesh[0] == 0.0
        assert mesh[-1] == pytest.approx(793.0)

    def test_generate_2d_unstructured_mesh(self):
        """Test 2D unstructured mesh generation."""
        generator = AdvancedMeshGenerator()

        # Create test points
        points = np.array([[10.0, 10.0], [20.0, 10.0], [15.0, 20.0]])
        boundary_points = np.array([[0.0, 0.0], [30.0, 0.0], [30.0, 30.0], [0.0, 30.0]])

        vertices, triangles = generator.generate_2d_unstructured_mesh(
            points, boundary_points
        )

        assert vertices.shape[1] == 2  # 2D
        assert triangles.shape[1] == 3  # Triangles have 3 vertices
        assert len(vertices) >= len(points) + len(boundary_points)
        assert len(triangles) > 0

    def test_generate_2d_unstructured_mesh_no_boundary(self):
        """Test unstructured mesh without boundary points."""
        generator = AdvancedMeshGenerator()

        points = np.array([[0.0, 0.0], [10.0, 0.0], [5.0, 10.0]])
        vertices, triangles = generator.generate_2d_unstructured_mesh(points, None)

        assert vertices.shape[1] == 2
        assert triangles.shape[1] == 3
        assert len(vertices) >= len(points)

    def test_evaluate_mesh_quality_good_mesh(self):
        """Test mesh quality evaluation for good mesh."""
        generator = AdvancedMeshGenerator()

        # Create a good quality mesh (nearly equilateral triangles)
        vertices = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, np.sqrt(3) / 2], [1.5, np.sqrt(3) / 2]])
        triangles = np.array([[0, 1, 2], [1, 3, 2]])

        quality = generator.evaluate_mesh_quality(vertices, triangles)

        assert isinstance(quality, MeshQuality)
        assert quality.min_angle > 0
        assert quality.max_angle < 180
        assert quality.aspect_ratio > 0
        assert quality.skewness > 0

    def test_evaluate_mesh_quality_is_good(self):
        """Test is_good() method for mesh quality."""
        generator = AdvancedMeshGenerator()

        # Good quality mesh
        vertices = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, np.sqrt(3) / 2]])
        triangles = np.array([[0, 1, 2]])

        quality = generator.evaluate_mesh_quality(vertices, triangles)
        # Should be good for equilateral triangle
        # All angles should be ~60 degrees
        assert quality.min_angle > 50
        assert quality.max_angle < 70
        assert quality.is_good() == True  # Use == instead of 'is' for numpy bool

    def test_evaluate_mesh_quality_bad_mesh(self):
        """Test mesh quality for poor quality mesh."""
        generator = AdvancedMeshGenerator()

        # Poor quality mesh (very skinny triangle)
        vertices = np.array([[0.0, 0.0], [100.0, 0.0], [50.0, 0.1]])
        triangles = np.array([[0, 1, 2]])

        quality = generator.evaluate_mesh_quality(vertices, triangles)

        # Should have poor quality metrics
        # Very skinny triangle will have very small angles and high aspect ratio
        # Check that it fails at least one quality criterion
        # (min_angle > 10, max_angle < 170, aspect_ratio < 10, skewness > 0.3)
        assert quality.is_good() == False  # Should fail quality checks (use == for numpy bool)

    def test_refine_mesh_no_criteria(self):
        """Test mesh refinement without criteria."""
        generator = AdvancedMeshGenerator()

        vertices = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, 1.0]])
        triangles = np.array([[0, 1, 2]])

        new_vertices, new_triangles = generator.refine_mesh(vertices, triangles, None)

        # Should return unchanged
        assert np.array_equal(new_vertices, vertices)
        assert np.array_equal(new_triangles, triangles)

    def test_refine_mesh_with_criteria(self):
        """Test mesh refinement with criteria."""
        generator = AdvancedMeshGenerator()

        vertices = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, 1.0]])
        triangles = np.array([[0, 1, 2]])
        criteria = np.array([2.0])  # High refinement indicator

        new_vertices, new_triangles = generator.refine_mesh(vertices, triangles, criteria)

        # Should have more vertices and triangles after refinement
        assert len(new_vertices) > len(vertices)  # Added midpoints
        assert len(new_triangles) > len(triangles)  # Split into 4 triangles
        assert len(new_triangles) == 4  # One triangle split into 4

    def test_refine_mesh_with_low_criteria(self):
        """Test mesh refinement with low criteria (should not refine)."""
        generator = AdvancedMeshGenerator()

        vertices = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, 1.0], [1.5, 0.5]])
        triangles = np.array([[0, 1, 2], [1, 3, 2]])
        # Use criteria where most are low, so median is low and threshold filters them out
        criteria = np.array([0.1, 0.2])  # Low refinement indicators

        new_vertices, new_triangles = generator.refine_mesh(vertices, triangles, criteria)

        # Should return unchanged for low criteria (threshold = 0.15 * 1.5 = 0.225, both < threshold)
        assert np.array_equal(new_vertices, vertices)
        assert np.array_equal(new_triangles, triangles)

    def test_refine_mesh_midpoint_cache_and_mixed_refine_flags(self):
        """
        Hit two tricky branches:
        - re-using an already-created midpoint for a shared edge
        - keeping (not refining) some triangles while refining others
        """
        generator = AdvancedMeshGenerator()

        # Two adjacent squares split into 4 triangles.
        vertices = np.array(
            [
                [0.0, 0.0],  # 0
                [1.0, 0.0],  # 1
                [0.0, 1.0],  # 2
                [1.0, 1.0],  # 3
                [2.0, 0.0],  # 4
                [2.0, 1.0],  # 5
            ]
        )
        triangles = np.array(
            [
                [0, 1, 2],  # left square tri A (refine)
                [1, 3, 2],  # left square tri B (refine) shares edge (1,2)
                [1, 4, 3],  # right square tri A (keep)
                [4, 5, 3],  # right square tri B (keep)
            ]
        )

        # With 4 values, median = (1 + 10) / 2 = 5.5 => threshold = 8.25.
        # This refines exactly the two 10.0 triangles and keeps the 1.0 triangles.
        criteria = np.array([10.0, 10.0, 1.0, 1.0])

        new_vertices, new_triangles = generator.refine_mesh(vertices, triangles, criteria)

        # Two refined triangles each create 3 midpoints, but they share one edge midpoint.
        assert len(new_vertices) == len(vertices) + 5
        assert len(new_triangles) == 10  # 2 kept + 2 refined * 4

        # Ensure at least one kept triangle is present unchanged.
        assert any(np.all(t == np.array([1, 4, 3])) for t in new_triangles)

    def test_refine_mesh_criteria_length_mismatch(self):
        """Test that criteria length mismatch raises ValueError."""
        generator = AdvancedMeshGenerator()

        vertices = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, 1.0]])
        triangles = np.array([[0, 1, 2]])
        criteria = np.array([1.0, 2.0])  # Wrong length

        with pytest.raises(ValueError, match="refinement_criteria length"):
            generator.refine_mesh(vertices, triangles, criteria)


class TestMeshQuality:
    """Test MeshQuality class."""

    def test_mesh_quality_creation(self):
        """Test mesh quality creation."""
        quality = MeshQuality(
            min_angle=30.0,
            max_angle=120.0,
            aspect_ratio=2.0,
            skewness=0.8,
            jacobian=0.9,
        )

        assert quality.min_angle == 30.0
        assert quality.max_angle == 120.0
        assert quality.aspect_ratio == 2.0
        assert quality.skewness == 0.8
        assert quality.jacobian == 0.9

    def test_mesh_quality_is_good(self):
        """Test is_good() method."""
        # Good quality
        quality = MeshQuality(
            min_angle=30.0,
            max_angle=120.0,
            aspect_ratio=2.0,
            skewness=0.8,
            jacobian=1.0,
        )
        assert quality.is_good() is True

        # Bad quality - small angle
        quality = MeshQuality(
            min_angle=5.0,
            max_angle=120.0,
            aspect_ratio=2.0,
            skewness=0.8,
            jacobian=1.0,
        )
        assert quality.is_good() is False

        # Bad quality - large angle
        quality = MeshQuality(
            min_angle=30.0,
            max_angle=175.0,
            aspect_ratio=2.0,
            skewness=0.8,
            jacobian=1.0,
        )
        assert quality.is_good() is False

        # Bad quality - high aspect ratio
        quality = MeshQuality(
            min_angle=30.0,
            max_angle=120.0,
            aspect_ratio=15.0,
            skewness=0.8,
            jacobian=1.0,
        )
        assert quality.is_good() is False

        # Bad quality - low skewness
        quality = MeshQuality(
            min_angle=30.0,
            max_angle=120.0,
            aspect_ratio=2.0,
            skewness=0.2,
            jacobian=1.0,
        )
        assert quality.is_good() is False


class TestComputeMeshGradient:
    """Test gradient computation functions."""

    def test_compute_mesh_gradient_central(self):
        """Test central difference gradient."""
        mesh = np.linspace(0, 10, 11)
        field = mesh**2  # x^2, gradient should be 2x

        gradient = compute_mesh_gradient(field, mesh, method="central")

        assert len(gradient) == len(field)
        # Check approximate values (gradient of x^2 = 2x)
        assert gradient[5] == pytest.approx(10.0, rel=0.1)  # At x=5, gradient should be ~10

    def test_compute_mesh_gradient_forward(self):
        """Test forward difference gradient."""
        mesh = np.linspace(0, 10, 11)
        field = mesh**2

        gradient = compute_mesh_gradient(field, mesh, method="forward")

        assert len(gradient) == len(field)

    def test_compute_mesh_gradient_backward(self):
        """Test backward difference gradient."""
        mesh = np.linspace(0, 10, 11)
        field = mesh**2

        gradient = compute_mesh_gradient(field, mesh, method="backward")

        assert len(gradient) == len(field)

    def test_compute_mesh_gradient_invalid_method(self):
        """Test invalid method raises error."""
        mesh = np.linspace(0, 10, 11)
        field = np.ones_like(mesh)

        with pytest.raises(ValueError, match="Unknown method"):
            compute_mesh_gradient(field, mesh, method="invalid")

