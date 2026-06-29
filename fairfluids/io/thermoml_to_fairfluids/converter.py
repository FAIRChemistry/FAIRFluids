"""
Converter orchestration.

Single entry point that chains the three layers:
  XML file → RawThermoML → List[CanonicalDataset] → FAIRFluids JSON dict
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fairfluids.io.canonical.fairfluids_builder import build_fairfluids

from .canonical_builder import build_canonical
from .parser import parse


def convert(xml_file: str | Path, fetch_from_pubchem: bool = True) -> Dict[str, Any]:
    """Convert a ThermoML XML file into a FAIRFluids JSON dict.

    Args:
        xml_file: Path to the ThermoML XML file.
        fetch_from_pubchem: If True (default), enrich compounds with PubChem metadata.

    Returns:
        A dict conforming to the ``FAIRFluidsDocument`` schema.
    """
    raw = parse(xml_file)
    document = build_canonical(raw)
    return build_fairfluids(
        document,
        fetch_from_pubchem=fetch_from_pubchem,
    )
