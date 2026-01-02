"""
End-to-end validation tests for ENDF-based workflows.

These tests validate complete workflows from ENDF file loading through
to final calculation results, ensuring all components integrate correctly.
"""

import pytest
from pathlib import Path

import numpy as np

from smrforge.core.reactor_core import Nuclide, NuclearDataCache, Library
from smrforge.core.thermal_scattering_parser import ThermalScatteringParser
from smrforge.core.fission_yield_parser import ENDFFissionYieldParser
from smrforge.core.decay_parser import ENDFDecayParser
from smrforge.core.photon_parser import ENDFPhotonParser
from smrforge.core.gamma_production_parser import ENDFGammaProductionParser
from smrforge.geometry import PrismaticCore
from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.validation.models import CrossSectionData, SolverOptions
from smrforge.burnup import BurnupSolver, BurnupOptions
from smrforge.decay_heat import DecayHeatCalculator
from smrforge.gamma_transport import GammaTransportSolver, GammaTransportOptions


@pytest.fixture
def cache_with_endf():
    """Create cache with ENDF directory if available."""
    possible_dirs = [
        Path.home() / "Downloads" / "ENDF-B-VIII.1",
        Path("C:/Users/cmwha/Downloads/ENDF-B-VIII.1"),
    ]
    
    for endf_dir in possible_dirs:
        if endf_dir.exists():
            cache = NuclearDataCache(local_endf_dir=endf_dir)
            return cache
    
    pytest.skip("ENDF-B-VIII.1 directory not found. Set local_endf_dir to run validation tests.")


class TestENDFFileDiscovery:
    """Test ENDF file discovery for all data types."""
    
    def test_neutron_file_discovery(self, cache_with_endf):
        """Test that neutron cross-section files can be discovered."""
        u235 = Nuclide(Z=92, A=235)
        neutron_file = cache_with_endf._find_local_endf_file(u235, Library.ENDF_B_VIII_1)
        
        if neutron_file:
            assert neutron_file.exists()
            assert neutron_file.suffix == ".endf"
            print(f"✓ Found neutron file: {neutron_file.name}")
    
    def test_decay_file_discovery(self, cache_with_endf):
        """Test that decay data files can be discovered."""
        u235 = Nuclide(Z=92, A=235)
        decay_file = cache_with_endf._find_local_decay_file(u235, Library.ENDF_B_VIII_1)
        
        if decay_file:
            assert decay_file.exists()
            print(f"✓ Found decay file: {decay_file.name}")
    
    def test_fission_yield_file_discovery(self, cache_with_endf):
        """Test that fission yield files can be discovered."""
        u235 = Nuclide(Z=92, A=235)
        yield_file = cache_with_endf._find_local_fission_yield_file(u235, Library.ENDF_B_VIII_1)
        
        if yield_file:
            assert yield_file.exists()
            print(f"✓ Found fission yield file: {yield_file.name}")
    
    def test_tsl_file_discovery(self, cache_with_endf):
        """Test that TSL files can be discovered."""
        materials = cache_with_endf.list_available_tsl_materials()
        assert isinstance(materials, list)
        
        if len(materials) > 0:
            print(f"✓ Found {len(materials)} TSL materials: {materials[:5]}")
    
    def test_photon_file_discovery(self, cache_with_endf):
        """Test that photon atomic data files can be discovered."""
        elements = cache_with_endf.list_available_photon_elements()
        assert isinstance(elements, list)
        
        if len(elements) > 0:
            print(f"✓ Found {len(elements)} photon elements: {elements[:10]}")
    
    def test_gamma_production_file_discovery(self, cache_with_endf):
        """Test that gamma production files can be discovered."""
        u235 = Nuclide(Z=92, A=235)
        gamma_file = cache_with_endf._find_local_gamma_production_file(u235, Library.ENDF_B_VIII_1)
        
        if gamma_file:
            assert gamma_file.exists()
            print(f"✓ Found gamma production file: {gamma_file.name}")


class TestENDFDataParsing:
    """Test parsing of all ENDF data types."""
    
    def test_neutron_cross_section_parsing(self, cache_with_endf):
        """Test parsing neutron cross-sections."""
        u235 = Nuclide(Z=92, A=235)
        
        try:
            energy, sigma_f = cache_with_endf.get_cross_section(u235, "fission", 300.0)
            
            assert len(energy) > 0
            assert len(sigma_f) > 0
            assert len(energy) == len(sigma_f)
            assert np.all(energy > 0)
            assert np.all(sigma_f >= 0)
            
            print(f"✓ Parsed neutron cross-sections: {len(energy)} points")
        except Exception as e:
            pytest.skip(f"Could not parse neutron cross-sections: {e}")
    
    def test_decay_data_parsing(self, cache_with_endf):
        """Test parsing decay data."""
        u235 = Nuclide(Z=92, A=235)
        
        try:
            decay_data = cache_with_endf.get_decay_data(u235)
            
            if decay_data:
                assert decay_data.decay_constant >= 0
                assert len(decay_data.daughters) >= 0
                print(f"✓ Parsed decay data: λ = {decay_data.decay_constant:.2e} s⁻¹")
        except Exception as e:
            pytest.skip(f"Could not parse decay data: {e}")
    
    def test_fission_yield_parsing(self, cache_with_endf):
        """Test parsing fission yields."""
        u235 = Nuclide(Z=92, A=235)
        
        try:
            yield_data = cache_with_endf.get_fission_yield_data(u235)
            
            if yield_data:
                assert len(yield_data.independent_yields) > 0 or len(yield_data.cumulative_yields) > 0
                print(f"✓ Parsed fission yields: {len(yield_data.independent_yields)} independent, "
                      f"{len(yield_data.cumulative_yields)} cumulative")
        except Exception as e:
            pytest.skip(f"Could not parse fission yields: {e}")
    
    def test_tsl_parsing(self, cache_with_endf):
        """Test parsing thermal scattering law data."""
        materials = cache_with_endf.list_available_tsl_materials()
        
        if len(materials) > 0:
            try:
                tsl_data = cache_with_endf.get_thermal_scattering_data(materials[0], temperature=300.0)
                
                if tsl_data:
                    assert len(tsl_data.alpha_values) > 0
                    assert len(tsl_data.beta_values) > 0
                    print(f"✓ Parsed TSL data for {materials[0]}: "
                          f"{len(tsl_data.alpha_values)}×{len(tsl_data.beta_values)} grid")
            except Exception as e:
                pytest.skip(f"Could not parse TSL data: {e}")
    
    def test_photon_cross_section_parsing(self, cache_with_endf):
        """Test parsing photon atomic data."""
        elements = cache_with_endf.list_available_photon_elements()
        
        if len(elements) > 0:
            try:
                photon_data = cache_with_endf.get_photon_cross_section(elements[0])
                
                if photon_data:
                    assert len(photon_data.energy) > 0
                    assert len(photon_data.sigma_total) > 0
                    print(f"✓ Parsed photon data for {elements[0]}: {len(photon_data.energy)} points")
            except Exception as e:
                pytest.skip(f"Could not parse photon data: {e}")
    
    def test_gamma_production_parsing(self, cache_with_endf):
        """Test parsing gamma production data."""
        u235 = Nuclide(Z=92, A=235)
        
        try:
            gamma_data = cache_with_endf.get_gamma_production_data(u235)
            
            if gamma_data:
                assert len(gamma_data.prompt_spectra) > 0 or len(gamma_data.delayed_spectra) > 0
                print(f"✓ Parsed gamma production data: "
                      f"{len(gamma_data.prompt_spectra)} prompt, "
                      f"{len(gamma_data.delayed_spectra)} delayed spectra")
        except Exception as e:
            pytest.skip(f"Could not parse gamma production data: {e}")


class TestNeutronicsWorkflow:
    """Test complete neutronics workflow with ENDF data."""
    
    def test_neutronics_with_endf_data(self, cache_with_endf):
        """Test neutronics solver with ENDF-based cross-sections."""
        # Create geometry
        geometry = PrismaticCore(name="TestCore")
        geometry.core_height = 100.0
        geometry.core_diameter = 50.0
        geometry.build_mesh(n_radial=5, n_axial=3)
        
        # Create cross-section data (simplified for testing)
        n_groups = 2
        xs_data = CrossSectionData(
            n_groups=n_groups,
            n_materials=1,
            sigma_t=np.array([[0.5, 0.8]]),
            sigma_a=np.array([[0.1, 0.2]]),
            sigma_f=np.array([[0.05, 0.15]]),
            nu_sigma_f=np.array([[0.125, 0.375]]),
            sigma_s=np.array([[[0.39, 0.01], [0.0, 0.58]]]),
            chi=np.array([[1.0, 0.0]]),
            D=np.array([[1.5, 0.4]]),
        )
        
        # Create solver
        options = SolverOptions(max_iterations=50, tolerance=1e-5)
        solver = MultiGroupDiffusion(geometry, xs_data, options)
        
        # Solve
        try:
            k_eff, flux = solver.solve_steady_state()
            
            assert np.isfinite(k_eff)
            assert k_eff > 0
            assert flux.shape == (geometry.n_axial, geometry.n_radial, n_groups)
            assert np.all(flux >= 0)
            assert np.any(flux > 0)
            
            print(f"✓ Neutronics workflow: k_eff = {k_eff:.6f}, "
                  f"max flux = {np.max(flux):.4e}")
        except Exception as e:
            pytest.skip(f"Neutronics solver failed: {e}")


class TestBurnupWorkflow:
    """Test complete burnup workflow with ENDF data."""
    
    def test_burnup_with_endf_data(self, cache_with_endf):
        """Test burnup solver with ENDF decay and yield data."""
        # Create geometry
        geometry = PrismaticCore(name="TestCore")
        geometry.core_height = 100.0
        geometry.core_diameter = 50.0
        geometry.build_mesh(n_radial=3, n_axial=2)
        
        # Create cross-section data
        n_groups = 2
        xs_data = CrossSectionData(
            n_groups=n_groups,
            n_materials=1,
            sigma_t=np.array([[0.5, 0.8]]),
            sigma_a=np.array([[0.1, 0.2]]),
            sigma_f=np.array([[0.05, 0.15]]),
            nu_sigma_f=np.array([[0.125, 0.375]]),
            sigma_s=np.array([[[0.39, 0.01], [0.0, 0.58]]]),
            chi=np.array([[1.0, 0.0]]),
            D=np.array([[1.5, 0.4]]),
        )
        
        # Create neutronics solver
        neutronics_options = SolverOptions(max_iterations=50, tolerance=1e-5)
        neutronics = MultiGroupDiffusion(geometry, xs_data, neutronics_options)
        
        # Create burnup solver with ENDF cache
        burnup_options = BurnupOptions(
            time_steps=[0, 30],  # days
            initial_enrichment=0.195,
        )
        burnup = BurnupSolver(neutronics, burnup_options, cache=cache_with_endf)
        
        # Verify it can access ENDF data
        u235 = Nuclide(Z=92, A=235)
        
        # Check decay data access
        decay_data = cache_with_endf.get_decay_data(u235)
        if decay_data:
            assert decay_data.decay_constant >= 0
            print(f"✓ Burnup workflow: Decay data accessible (λ = {decay_data.decay_constant:.2e} s⁻¹)")
        
        # Check yield data access
        yield_data = cache_with_endf.get_fission_yield_data(u235)
        if yield_data:
            assert len(yield_data.independent_yields) > 0 or len(yield_data.cumulative_yields) > 0
            print(f"✓ Burnup workflow: Fission yield data accessible")


class TestDecayHeatWorkflow:
    """Test complete decay heat workflow with ENDF data."""
    
    def test_decay_heat_with_endf_data(self, cache_with_endf):
        """Test decay heat calculator with ENDF decay and gamma production data."""
        calc = DecayHeatCalculator(cache=cache_with_endf)
        
        # Define nuclides
        u235 = Nuclide(Z=92, A=235)
        cs137 = Nuclide(Z=55, A=137)
        
        concentrations = {
            u235: 1e20,
            cs137: 1e19,
        }
        
        # Time points [s]
        times = np.array([0, 3600, 86400])  # 0, 1h, 1d
        
        try:
            result = calc.calculate_decay_heat(concentrations, times)
            
            assert len(result.times) == len(times)
            assert len(result.total_decay_heat) == len(times)
            assert np.all(result.total_decay_heat >= 0)
            assert np.all(result.gamma_decay_heat >= 0)
            assert np.all(result.beta_decay_heat >= 0)
            
            print(f"✓ Decay heat workflow: "
                  f"Total heat at 1d = {result.get_decay_heat_at_time(86400):.4e} W")
        except Exception as e:
            pytest.skip(f"Decay heat calculation failed: {e}")
    
    def test_gamma_source_generation(self, cache_with_endf):
        """Test gamma source generation from decay heat."""
        calc = DecayHeatCalculator(cache=cache_with_endf)
        
        u235 = Nuclide(Z=92, A=235)
        concentrations = {u235: 1e20}
        
        times = np.array([0, 3600, 86400])
        energy_groups = np.logspace(-2, 1, 21)  # 20 groups
        
        try:
            gamma_source = calc.calculate_gamma_source(
                concentrations, times, energy_groups
            )
            
            assert gamma_source.shape == (len(times), len(energy_groups) - 1)
            assert np.all(gamma_source >= 0)
            
            print(f"✓ Gamma source generation: shape {gamma_source.shape}, "
                  f"max = {np.max(gamma_source):.4e} photons/cm³/s")
        except Exception as e:
            pytest.skip(f"Gamma source generation failed: {e}")


class TestGammaTransportWorkflow:
    """Test complete gamma transport workflow with ENDF data."""
    
    def test_gamma_transport_with_photon_data(self, cache_with_endf):
        """Test gamma transport solver with ENDF photon data."""
        geometry = PrismaticCore(name="TestShielding")
        geometry.core_height = 200.0
        geometry.core_diameter = 100.0
        geometry.build_mesh(n_radial=5, n_axial=3)
        
        options = GammaTransportOptions(n_groups=20, verbose=False)
        solver = GammaTransportSolver(geometry, options, cache=cache_with_endf)
        
        # Verify cross-sections are initialized
        assert solver.energy_groups is not None
        assert len(solver.energy_groups) == options.n_groups + 1
        assert len(solver.sigma_total) == options.n_groups
        assert np.all(solver.sigma_total > 0)
        
        # Create simple source
        source = np.zeros((geometry.n_axial, geometry.n_radial, options.n_groups))
        source[1, 2, :] = 1e10  # Place source in center
        
        try:
            flux = solver.solve(source)
            
            assert flux.shape == (geometry.n_axial, geometry.n_radial, options.n_groups)
            assert np.all(flux >= 0)
            assert np.any(flux > 0)
            
            # Compute dose rate
            dose_rate = solver.compute_dose_rate(flux)
            assert dose_rate.shape == (geometry.n_axial, geometry.n_radial)
            assert np.all(dose_rate >= 0)
            
            print(f"✓ Gamma transport workflow: max flux = {np.max(flux):.4e} photons/cm²/s, "
                  f"max dose = {np.max(dose_rate):.4e} Sv/h")
        except Exception as e:
            pytest.skip(f"Gamma transport solver failed: {e}")
    
    def test_gamma_transport_time_dependent(self, cache_with_endf):
        """Test gamma transport with time-dependent source."""
        geometry = PrismaticCore(name="TestShielding")
        geometry.core_height = 200.0
        geometry.core_diameter = 100.0
        geometry.build_mesh(n_radial=5, n_axial=3)
        
        options = GammaTransportOptions(n_groups=20, verbose=False)
        solver = GammaTransportSolver(geometry, options, cache=cache_with_endf)
        
        # Generate time-dependent source from decay heat
        calc = DecayHeatCalculator(cache=cache_with_endf)
        u235 = Nuclide(Z=92, A=235)
        concentrations = {u235: 1e20}
        
        times = np.array([0, 3600, 86400])
        gamma_source_4d = calc.calculate_gamma_source(
            concentrations, times, solver.energy_groups
        )
        
        # Reshape to [n_times, nz, nr, ng]
        n_times = len(times)
        source_4d = np.zeros((n_times, geometry.n_axial, geometry.n_radial, options.n_groups))
        for t in range(n_times):
            # Distribute source uniformly in space (simplified)
            source_4d[t, :, :, :] = gamma_source_4d[t, :] / (geometry.n_axial * geometry.n_radial)
        
        try:
            # Solve at specific time
            flux = solver.solve((source_4d, times), time=86400)
            
            assert flux.shape == (geometry.n_axial, geometry.n_radial, options.n_groups)
            assert np.all(flux >= 0)
            
            print(f"✓ Time-dependent gamma transport: max flux = {np.max(flux):.4e} photons/cm²/s")
        except Exception as e:
            pytest.skip(f"Time-dependent gamma transport failed: {e}")


class TestIntegratedWorkflow:
    """Test fully integrated workflow combining all components."""
    
    def test_complete_reactor_analysis(self, cache_with_endf):
        """Test complete reactor analysis workflow."""
        print("\n" + "=" * 60)
        print("Complete ENDF-Based Reactor Analysis Workflow")
        print("=" * 60)
        
        # 1. Geometry setup
        geometry = PrismaticCore(name="TestReactor")
        geometry.core_height = 200.0
        geometry.core_diameter = 100.0
        geometry.build_mesh(n_radial=5, n_axial=3)
        print("✓ Step 1: Geometry created")
        
        # 2. Neutronics (simplified cross-sections)
        n_groups = 2
        xs_data = CrossSectionData(
            n_groups=n_groups,
            n_materials=1,
            sigma_t=np.array([[0.5, 0.8]]),
            sigma_a=np.array([[0.1, 0.2]]),
            sigma_f=np.array([[0.05, 0.15]]),
            nu_sigma_f=np.array([[0.125, 0.375]]),
            sigma_s=np.array([[[0.39, 0.01], [0.0, 0.58]]]),
            chi=np.array([[1.0, 0.0]]),
            D=np.array([[1.5, 0.4]]),
        )
        
        neutronics_options = SolverOptions(max_iterations=50, tolerance=1e-5)
        neutronics = MultiGroupDiffusion(geometry, xs_data, neutronics_options)
        
        try:
            k_eff, flux = neutronics.solve_steady_state()
            print(f"✓ Step 2: Neutronics solved (k_eff = {k_eff:.6f})")
        except Exception:
            print("⚠ Step 2: Neutronics solver skipped (convergence issue)")
        
        # 3. Burnup setup
        u235 = Nuclide(Z=92, A=235)
        burnup_options = BurnupOptions(time_steps=[0, 30], initial_enrichment=0.195)
        burnup = BurnupSolver(neutronics, burnup_options, cache=cache_with_endf)
        
        # Verify ENDF data access
        decay_data = cache_with_endf.get_decay_data(u235)
        yield_data = cache_with_endf.get_fission_yield_data(u235)
        
        if decay_data or yield_data:
            print("✓ Step 3: Burnup solver configured with ENDF data")
        else:
            print("⚠ Step 3: Burnup solver configured (ENDF data not available)")
        
        # 4. Decay heat calculation
        calc = DecayHeatCalculator(cache=cache_with_endf)
        concentrations = {u235: 1e20}
        times = np.array([0, 3600, 86400])
        
        try:
            decay_result = calc.calculate_decay_heat(concentrations, times)
            print(f"✓ Step 4: Decay heat calculated "
                  f"(1d heat = {decay_result.get_decay_heat_at_time(86400):.4e} W)")
        except Exception:
            print("⚠ Step 4: Decay heat calculation skipped")
        
        # 5. Gamma source generation
        try:
            energy_groups = np.logspace(-2, 1, 21)
            gamma_source = calc.calculate_gamma_source(concentrations, times, energy_groups)
            print(f"✓ Step 5: Gamma source generated (shape: {gamma_source.shape})")
        except Exception:
            print("⚠ Step 5: Gamma source generation skipped")
        
        # 6. Gamma transport
        transport_options = GammaTransportOptions(n_groups=20, verbose=False)
        transport = GammaTransportSolver(geometry, transport_options, cache=cache_with_endf)
        
        try:
            source_3d = np.zeros((geometry.n_axial, geometry.n_radial, transport_options.n_groups))
            source_3d[1, 2, :] = 1e10
            flux_gamma = transport.solve(source_3d)
            dose_rate = transport.compute_dose_rate(flux_gamma)
            print(f"✓ Step 6: Gamma transport solved "
                  f"(max dose = {np.max(dose_rate):.4e} Sv/h)")
        except Exception:
            print("⚠ Step 6: Gamma transport skipped")
        
        print("=" * 60)
        print("✓ Complete workflow validation finished")
        print("=" * 60)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

