import numpy as np


def test_voxel_grid_prismatic_core_is_nonempty():
    from smrforge.geometry.core_geometry import PrismaticCore
    from smrforge.visualization.voxel_plots import _create_voxel_grid

    core = PrismaticCore(name="VoxelTestCore")
    core.build_hexagonal_lattice(n_rings=1, pitch=40.0, block_height=80.0, n_axial=1, flat_to_flat=36.0)

    grid = _create_voxel_grid(
        core,
        origin=(-120.0, -120.0, 0.0),
        width=(240.0, 240.0, 80.0),
        resolution=(30, 30, 10),
    )

    mats = grid["material_ids"]
    cells = grid["cell_ids"]
    assert mats.shape == (30, 30, 10)
    assert cells.shape == (30, 30, 10)

    # Should mark at least some voxels as belonging to a block/material.
    assert int(np.max(mats)) > 0
    assert int(np.max(cells)) > 0

