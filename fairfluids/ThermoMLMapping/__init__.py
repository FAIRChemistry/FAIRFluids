"""
ThermoML to FAIRFluids Mapping Module

This module provides functionality to convert ThermoML XML data to FAIRFluids format.
It includes mapping classes and functions for compounds, citations, properties, parameters, and measurements.
"""

from .thermoml_mapper import ThermoMLMapper
from .conversion_utils import *

__all__ = ["ThermoMLMapper"]
