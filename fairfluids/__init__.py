"""
FAIRFluids - A framework for creating FAIR fluid data documents.

This package provides tools for creating, parsing, and manipulating
FAIR-compliant fluid property data with standardized metadata.
"""

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

from .core.fluid_io import FluidIO
from .core.functionalities import (
    FAIRFluidsCMLParser,
    filter_fluid_compounds_by_mole_fractions,
    combine_compounds,
    calculate_ratio_of_solvent,
    cleanup_orphaned_parameters,
    calculate_activationEnergy,
)
from .core.visualization import filter_fluid_measurements
from .core.plot_utils import save_plot_as_svg, reset_plot_counter

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
    "filter_fluid_measurements",
    "filter_fluid_compounds_by_mole_fractions",
    "combine_compounds",
    "calculate_ratio_of_solvent",
    "cleanup_orphaned_parameters",
    "calculate_activationEnergy",
    "save_plot_as_svg",
    "reset_plot_counter",
]
