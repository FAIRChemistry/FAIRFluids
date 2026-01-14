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

from .fluid_io import FluidIO
from .functionalities import (
    FAIRFluidsCMLParser,
    filter_fluid_compounds_by_mole_fractions,
    combine_compounds,
    calculate_ratio_of_solvent,
    cleanup_orphaned_parameters,
    calculate_activationEnergy,
)
from .visualization import filter_fluid_measurements

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
]
