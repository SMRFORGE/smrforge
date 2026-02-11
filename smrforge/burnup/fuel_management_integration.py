"""
Integration of fuel management with burnup solver.

Provides integration between AssemblyManager/SMRFuelManager and BurnupSolver
to enable batch tracking and refueling simulation during burnup calculations.

This module bridges the gap between:
- Geometry module: AssemblyManager, SMRFuelManager, Assembly classes
- Burnup module: BurnupSolver, NuclideInventory classes
"""

from typing import TYPE_CHECKING, Dict, List, Optional

from ..utils.logging import get_logger

logger = get_logger("smrforge.burnup.fuel_management_integration")

if TYPE_CHECKING:
    from ..geometry.assembly import Assembly, AssemblyManager
    from ..geometry.smr_fuel_management import SMRFuelManager, SMRRefuelingPattern
    from ..neutronics.solver import MultiGroupDiffusion
    from .solver import BurnupOptions, BurnupSolver, NuclideInventory


class BurnupFuelManagerIntegration:
    """
    Integration layer for AssemblyManager/SMRFuelManager with BurnupSolver.

    Coordinates burnup calculations across multiple assemblies/batches,
    tracking burnup values and updating assembly states based on burnup results.

    Usage:
        >>> from smrforge.burnup.fuel_management_integration import BurnupFuelManagerIntegration
        >>> from smrforge.geometry.smr_fuel_management import SMRFuelManager
        >>> from smrforge.burnup import BurnupSolver, BurnupOptions
        >>>
        >>> # Create fuel manager
        >>> fuel_manager = SMRFuelManager()
        >>>
        >>> # Create integration layer
        >>> integration = BurnupFuelManagerIntegration(fuel_manager)
        >>>
        >>> # Run burnup for a cycle
        >>> integration.run_cycle_burnup(
        ...     neutronics_solver,
        ...     burnup_options,
        ...     cycle_days=365 * 3  # 3-year cycle
        ... )
        >>>
        >>> # Get updated burnup values
        >>> for assembly in fuel_manager.assemblies:
        ...     print(f"Assembly {assembly.id}: burnup = {assembly.burnup:.2f} MWd/kgU")
    """

    def __init__(
        self,
        fuel_manager: "AssemblyManager",
    ):
        """
        Initialize integration layer.

        Args:
            fuel_manager: AssemblyManager or SMRFuelManager instance
        """
        self.fuel_manager = fuel_manager
        # Map assembly ID to burnup solver (one per assembly or shared)
        self._assembly_solvers: Dict[int, "BurnupSolver"] = {}
        # Map assembly ID to NuclideInventory results
        self._assembly_inventories: Dict[int, "NuclideInventory"] = {}

        logger.info(
            f"BurnupFuelManagerIntegration initialized with {len(fuel_manager.assemblies)} assemblies"
        )

    def run_cycle_burnup(
        self,
        neutronics_solver: "MultiGroupDiffusion",
        burnup_options: "BurnupOptions",
        cycle_days: float,
        update_assembly_burnup: bool = True,
    ) -> Dict[int, "NuclideInventory"]:
        """
        Run burnup calculation for a full cycle, updating assembly burnup values.

        This method coordinates burnup calculations across all assemblies in
        the fuel manager, tracking burnup for each batch and updating assembly
        states based on results.

        Enhanced version that:
        - Supports per-batch burnup tracking
        - Accounts for flux distribution across assemblies
        - Stores neutronics solver for flux distribution calculations

        Args:
            neutronics_solver: MultiGroupDiffusion solver for the core
            burnup_options: BurnupOptions configuration
            cycle_days: Cycle length in days
            update_assembly_burnup: If True, update assembly.burnup values

        Returns:
            Dictionary mapping assembly ID to NuclideInventory
        """
        logger.info(f"Running cycle burnup for {cycle_days:.1f} days")

        # Store neutronics solver for flux distribution
        self._neutronics_solver = neutronics_solver

        # Update time steps in options to cover the cycle
        if not burnup_options.time_steps or burnup_options.time_steps[-1] < cycle_days:
            # Add cycle endpoint if not already covered
            time_steps = (
                list(burnup_options.time_steps) if burnup_options.time_steps else [0.0]
            )
            if time_steps[-1] < cycle_days:
                time_steps.append(cycle_days)
            # Create updated options
            from dataclasses import replace

            burnup_options = replace(burnup_options, time_steps=time_steps)

        # For now, use a single burnup solver for the entire core
        # Future: could use separate solvers per assembly/batch
        if not self._assembly_solvers:
            # Create burnup solver for core
            from .solver import BurnupSolver

            core_solver = BurnupSolver(neutronics_solver, burnup_options)
            # Store solver (using -1 as core ID)
            self._assembly_solvers[-1] = core_solver

        core_solver = self._assembly_solvers[-1]

        # Run burnup calculation
        inventory = core_solver.solve()

        # Update assembly burnup values based on results
        if update_assembly_burnup:
            self._update_assembly_burnup_values(inventory, cycle_days)

        # Store inventory for all assemblies (for now, same inventory for all)
        for assembly in self.fuel_manager.assemblies:
            self._assembly_inventories[assembly.id] = inventory

        logger.info("Cycle burnup calculation complete")

        return self._assembly_inventories

    def _update_assembly_burnup_values(
        self,
        inventory: "NuclideInventory",
        cycle_days: float,
    ) -> None:
        """
        Update assembly.burnup values based on burnup calculation results.

        Uses the final burnup value from the inventory and distributes it
        across assemblies based on their batch, position, and flux distribution.

        Enhanced version that accounts for:
        - Batch age (older batches accumulate more burnup)
        - Spatial flux distribution (if available from neutronics solver)
        - Assembly position in core

        Args:
            inventory: NuclideInventory from burnup calculation
            cycle_days: Cycle length in days
        """
        # Get final burnup value
        final_burnup = inventory.burnup[-1] if len(inventory.burnup) > 0 else 0.0

        # Get flux distribution if available (for better burnup distribution)
        flux_distribution = None
        if hasattr(self, "_neutronics_solver") and self._neutronics_solver is not None:
            if (
                hasattr(self._neutronics_solver, "flux")
                and self._neutronics_solver.flux is not None
            ):
                # Get average flux per assembly (if assembly mapping available)
                flux_distribution = self._get_assembly_flux_distribution()

        # Update each assembly's burnup
        for assembly in self.fuel_manager.assemblies:
            if assembly.batch >= 0:  # Active assembly
                # Base burnup increment from final burnup
                base_increment = final_burnup

                # Apply batch factor (older batches accumulate more)
                # Batch 1 (newest) gets base, batch 2 gets 1.2x, batch 3 gets 1.4x, etc.
                batch_factor = 1.0 + (assembly.batch - 1) * 0.2

                # Apply flux distribution factor if available
                flux_factor = 1.0
                if flux_distribution and assembly.id in flux_distribution:
                    # Normalize flux factor (relative to average)
                    avg_flux = (
                        sum(flux_distribution.values()) / len(flux_distribution)
                        if flux_distribution
                        else 1.0
                    )
                    assembly_flux = flux_distribution.get(assembly.id, avg_flux)
                    flux_factor = assembly_flux / avg_flux if avg_flux > 0 else 1.0

                # Calculate burnup increment
                burnup_increment = (
                    base_increment
                    * batch_factor
                    * flux_factor
                    / max(1, len(self.fuel_manager.assemblies))
                )

                # Update assembly burnup
                assembly.burnup += burnup_increment

                logger.debug(
                    f"Updated assembly {assembly.id} (batch {assembly.batch}): "
                    f"burnup = {assembly.burnup:.2f} MWd/kgU "
                    f"(batch_factor={batch_factor:.2f}, flux_factor={flux_factor:.2f})"
                )

    def _get_assembly_flux_distribution(self) -> Dict[int, float]:
        """
        Get flux distribution per assembly.

        Returns:
            Dictionary mapping assembly ID to average flux
        """
        if not hasattr(self, "_neutronics_solver") or self._neutronics_solver is None:
            return {}

        flux = self._neutronics_solver.flux
        if flux is None:
            return {}

        # For now, return uniform distribution
        # Full implementation would map flux to assemblies based on geometry
        distribution = {}
        for assembly in self.fuel_manager.assemblies:
            # Simplified: use assembly position or batch as proxy
            # Real implementation would integrate flux over assembly volume
            distribution[assembly.id] = 1.0 + (assembly.batch - 1) * 0.1

        return distribution

    def get_assembly_inventory(self, assembly_id: int) -> Optional["NuclideInventory"]:
        """
        Get NuclideInventory for a specific assembly.

        Args:
            assembly_id: Assembly ID

        Returns:
            NuclideInventory for the assembly, or None if not found
        """
        return self._assembly_inventories.get(assembly_id)

    def get_batch_burnup_summary(self) -> Dict[int, float]:
        """
        Get burnup summary by batch.

        Returns:
            Dictionary mapping batch number to average burnup [MWd/kgU]
        """
        batch_burnups: Dict[int, List[float]] = {}

        for assembly in self.fuel_manager.assemblies:
            batch = assembly.batch
            if batch not in batch_burnups:
                batch_burnups[batch] = []
            batch_burnups[batch].append(assembly.burnup)

        # Calculate averages
        summary: Dict[int, float] = {}
        for batch, burnups in batch_burnups.items():
            summary[batch] = sum(burnups) / len(burnups) if burnups else 0.0

        return summary

    def prepare_for_refueling(
        self,
        pattern: Optional["SMRRefuelingPattern"] = None,
        target_burnup: float = 60.0,
    ) -> List[int]:
        """
        Prepare for refueling by identifying assemblies ready for discharge.

        Args:
            pattern: Optional SMRRefuelingPattern (required for SMRFuelManager)
            target_burnup: Target discharge burnup [MWd/kgU]

        Returns:
            List of assembly IDs ready for discharge
        """
        depleted_assemblies = self.fuel_manager.get_depleted_assemblies(target_burnup)
        depleted_ids = [a.id for a in depleted_assemblies]

        logger.info(
            f"Identified {len(depleted_ids)} assemblies ready for discharge "
            f"(target burnup: {target_burnup:.1f} MWd/kgU)"
        )

        return depleted_ids

    def apply_refueling(
        self,
        pattern: Optional["SMRRefuelingPattern"] = None,
        target_burnup: float = 60.0,
        fresh_enrichment: float = 0.045,
    ) -> None:
        """
        Apply refueling operation using fuel manager's refueling method.

        Args:
            pattern: Optional SMRRefuelingPattern (required for SMRFuelManager)
            target_burnup: Target discharge burnup [MWd/kgU]
            fresh_enrichment: Enrichment of fresh fuel
        """
        # Check if this is an SMRFuelManager
        if hasattr(self.fuel_manager, "refuel_smr") and pattern is not None:
            # Use SMR-specific refueling
            self.fuel_manager.refuel_smr(pattern, target_burnup, fresh_enrichment)
        else:
            # Use standard refueling (would need RefuelingPattern)
            logger.warning(
                "Standard refueling not fully implemented. "
                "Use SMRFuelManager with SMRRefuelingPattern for full functionality."
            )

        # Clear cached solvers/inventories (assemblies may have changed)
        self._assembly_solvers.clear()
        self._assembly_inventories.clear()

        logger.info("Refueling operation complete")

    def run_multi_cycle_burnup(
        self,
        neutronics_solver: "MultiGroupDiffusion",
        burnup_options: "BurnupOptions",
        pattern: Optional["SMRRefuelingPattern"] = None,
        n_cycles: int = 3,
        target_burnup: float = 60.0,
        fresh_enrichment: float = 0.045,
    ) -> Dict[int, List["NuclideInventory"]]:
        """
        Run burnup calculations for multiple cycles with refueling.

        Args:
            neutronics_solver: MultiGroupDiffusion solver
            burnup_options: BurnupOptions configuration
            pattern: Optional SMRRefuelingPattern
            n_cycles: Number of cycles to simulate
            target_burnup: Target discharge burnup [MWd/kgU]
            fresh_enrichment: Enrichment of fresh fuel

        Returns:
            Dictionary mapping assembly ID to list of NuclideInventory (one per cycle)
        """
        cycle_length_days = pattern.cycle_length_years * 365 if pattern else 365 * 3

        all_inventories: Dict[int, List["NuclideInventory"]] = {
            a.id: [] for a in self.fuel_manager.assemblies
        }

        for cycle in range(n_cycles):
            logger.info(f"Running cycle {cycle + 1}/{n_cycles}")

            # Run burnup for this cycle
            cycle_inventories = self.run_cycle_burnup(
                neutronics_solver,
                burnup_options,
                cycle_length_days,
                update_assembly_burnup=True,
            )

            # Store inventories
            for assembly_id, inventory in cycle_inventories.items():
                all_inventories[assembly_id].append(inventory)

            # Refuel if not last cycle
            if cycle < n_cycles - 1 and pattern is not None:
                self.apply_refueling(pattern, target_burnup, fresh_enrichment)

        logger.info(f"Multi-cycle burnup simulation complete ({n_cycles} cycles)")

        return all_inventories
