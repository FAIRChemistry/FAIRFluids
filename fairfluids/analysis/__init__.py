"""
Analysis: Arrhenius/VFT fits, activation energy, measurement tables.

Bayesian workflows live in ``fairfluids.analysis.bayesian`` (optional dependencies).
Implementations currently live in ``fairfluids.core.functionalities`` and are
re-exported here as the canonical analysis API surface.
"""

from fairfluids.core.functionalities import (
    calculate_activationEnergy,
    extract_property_dataframe,
    fit_arrhenius,
    fit_extended_arrhenius,
    fit_vft,
    group_and_filter_measurements,
)

__all__ = [
    "calculate_activationEnergy",
    "extract_property_dataframe",
    "fit_arrhenius",
    "fit_extended_arrhenius",
    "fit_vft",
    "group_and_filter_measurements",
]
