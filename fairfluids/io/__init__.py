"""
I/O layer: CSV/JSON loading, PubChem, ThermoML conversion (two separate pipelines).

Canonical imports::

    from fairfluids.io import FluidIO, FAIRFluidsCMLParser
    from fairfluids.io.thermoml_to_fairfluids import convert as thermoml_to_ff
    from fairfluids.io.fairfluids_to_thermoml import convert as ff_to_thermoml
"""

from pathlib import Path
from typing import Union

from fairfluids.core.lib import FAIRFluidsDocument
from fairfluids.io.fluid_io import FluidIO, from_csv
from fairfluids.io.pubchem import fetch_compound_from_pubchem
from fairfluids.io.cml_parser import FAIRFluidsCMLParser, from_cml


def from_thermoml(
    xml_path: Union[str, Path],
    *,
    fetch_from_pubchem: bool = True,
) -> FAIRFluidsDocument:
    """Convert a ThermoML XML file into a :class:`FAIRFluidsDocument`.

    The ThermoML converter derives citation and compound metadata directly from
    the source file, so no template document is required.

    Args:
        xml_path: Path to the ThermoML XML file.
        fetch_from_pubchem: If True (default), enrich compounds with PubChem metadata.

    Returns:
        A :class:`FAIRFluidsDocument`.
    """
    from fairfluids.io.thermoml_to_fairfluids.converter import convert

    document_dict = convert(xml_path, fetch_from_pubchem=fetch_from_pubchem)
    return FAIRFluidsDocument.model_validate(document_dict)


__all__ = [
    "FluidIO",
    "fetch_compound_from_pubchem",
    "FAIRFluidsCMLParser",
    "from_cml",
    "from_csv",
    "from_thermoml",
]
