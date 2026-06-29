"""
FAIRFluids - A framework for creating FAIR fluid data documents.

This package provides tools for creating, parsing, and manipulating
FAIR-compliant fluid property data with standardized metadata.
"""

from pathlib import Path

__version__ = "0.1.0"
__author__ = "FAIRChemistry Team"
__email__ = "contact@fairchemistry.org"

# Import main classes for easy access
from .core.lib import (
    FAIRFluidsDocument,
    Version,
    Citation,
    Author,
    Compound,
    Fluid,
    Property,
    PropertyValue,
    Parameter,
    ParameterValue,
    Measurement,
    UnitDefinition,
    BaseUnit,
    Method,
    Properties,
    Parameters,
    LitType,
)

from .io import FluidIO, FAIRFluidsCMLParser, from_cml, from_csv, from_thermoml
from .core.functionalities import filter_fluid_compounds_by_mole_fractions
from .operations import (
    combine_compounds,
    calculate_ratio_of_solvent,
    cleanup_orphaned_parameters,
)
from .core.visualization import filter_fluid_measurements
from .core.plot_utils import save_plot_as_svg, reset_plot_counter


def _save_to_json_compat(self: "FAIRFluidsDocument", filename: str = "fairfluids_document.json") -> None:
    """Backward-compatible helper kept for older notebooks/scripts."""
    out = Path(filename)
    out.write_text(self.model_dump_json(indent=4), encoding="utf-8")


# Older workflows call `doc.save_to_json(...)`; reattach this helper method.
if not hasattr(FAIRFluidsDocument, "save_to_json"):
    FAIRFluidsDocument.save_to_json = _save_to_json_compat  # type: ignore[attr-defined]

# Convenience imports
__all__ = [
    "FAIRFluidsDocument",
    "Version",
    "Citation",
    "Author",
    "Compound",
    "Fluid",
    "Property",
    "PropertyValue",
    "Parameter",
    "ParameterValue",
    "Measurement",
    "UnitDefinition",
    "BaseUnit",
    "Method",
    "Properties",
    "Parameters",
    "LitType",
    "FluidIO",
    "FAIRFluidsCMLParser",
    "from_cml",
    "from_csv",
    "from_thermoml",
    "filter_fluid_measurements",
    "filter_fluid_compounds_by_mole_fractions",
    "combine_compounds",
    "calculate_ratio_of_solvent",
    "cleanup_orphaned_parameters",
    "save_plot_as_svg",
    "reset_plot_counter",
]
