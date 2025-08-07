"""
Core functionality for FAIRFluids package.

This module contains the main data models and utilities for working with
FAIR fluid data documents.
"""

from .lib import (
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
    LitType
)

from .fluid_io import FluidIO
from .functionalities import FAIRFluidsCMLParser

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
    "FAIRFluidsCMLParser"
]
