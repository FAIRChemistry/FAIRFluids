"""
I/O layer: CSV/JSON loading, PubChem, ThermoML conversion (two separate pipelines).

Canonical imports::

    from fairfluids.io import FluidIO, FAIRFluidsCMLParser
    from fairfluids.io.thermoml_to_fairfluids import convert as thermoml_to_ff
    from fairfluids.io.fairfluids_to_thermoml import convert as ff_to_thermoml
"""

from fairfluids.io.fluid_io import FluidIO
from fairfluids.io.pubchem import fetch_compound_from_pubchem
from fairfluids.io.cml_parser import FAIRFluidsCMLParser

__all__ = [
    "FluidIO",
    "fetch_compound_from_pubchem",
    "FAIRFluidsCMLParser",
]
