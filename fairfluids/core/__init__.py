"""
Core functionality for FAIRFluids package.

This module contains the main data models and utilities for working with
FAIR fluid data documents.
"""

from .fairfluids import (
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
)

# Import enums and other utilities from lib since they don't need extension
from .lib import (
    Method,
    Properties,
    Parameters,
    LitType,
)

from fairfluids.io import FluidIO, FAIRFluidsCMLParser
from fairfluids.operations import (
    calculate_ratio_of_solvent,
    cleanup_orphaned_parameters,
    combine_compounds,
)
from .functionalities import filter_fluid_compounds_by_mole_fractions
from .visualization import filter_fluid_measurements
from .plot_utils import save_plot_as_svg, reset_plot_counter

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
    "save_plot_as_svg",
    "reset_plot_counter",
]
