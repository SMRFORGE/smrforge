"""
SMRForge Pro - AI/surrogate, BYOS, Serpent/OpenMC converters, validation reports, ML export.

Pro extends Community with full implementations of:
- smrforge_pro.converters: OpenMCConverter, SerpentConverter, MCNPConverter
- smrforge_pro.visualization: visualize_openmc_tallies (OpenMC mesh tally viz)
- load_surrogate_from_path (ONNX, TorchScript, sklearn pickle)
- fit_surrogate, surrogate_from_sweep_results (RBF/linear)
- SurrogateValidationReport, generate_validation_report
- record_ai_model, export_ml_dataset
- SweepConfig.surrogate_path, --surrogate CLI
"""

__version__ = "0.1.0"
