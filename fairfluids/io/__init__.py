"""
FAIRFluids I/O layer.

Three inbound converters (CSV, CML, ThermoML) now share **one** canonical
pipeline; a separate outbound converter exports back to ThermoML.

Unified inbound contract -- every converter takes a source path plus an optional
``document=`` metadata template and returns ``List[FAIRFluidsDocument]`` (one
document per source DOI; CML and ThermoML carry a single citation, so they
return a one-element list)::

    from fairfluids.io import from_csv, from_cml, from_thermoml

    docs = from_csv("data.csv", document=template)        # -> N documents (per DOI)
    docs = from_cml("run.cml", document=template)         # -> [doc]
    docs = from_thermoml("paper.xml")                     # -> [doc]

The shared pipeline is::

    producer -> Canonical models -> build_fairfluids() -> FAIRFluidsDocument

Each converter is just a *producer* that emits neutral ``Canonical*`` models;
``build_fairfluids`` assigns all object IDs and builds the final document.

Folder map
----------
::

    io/
    |-- __init__.py            this file: from_thermoml() + re-exports
    |-- fluid_io.py            CSV/XLSX producer  (FluidIO, from_csv)
    |-- cml_parser.py          CML producer       (FAIRFluidsCMLParser, from_cml)
    |-- pubchem.py             raw PubChem fetch  (fetch_compound_from_pubchem)
    |
    |-- canonical/                SHARED, source-format-neutral pipeline core
    |   |-- canonical_model.py    neutral Canonical* / Raw* models
    |   |-- fairfluids_builder.py build_fairfluids(): Canonical -> FAIRFluids dict
    |   |-- id_registry.py        per-prefix "<type>_<n>" ID allocator
    |   |-- composition.py        mole-fraction inference / completion
    |   |-- pubchem.py            enrich_compound_from_pubchem wrapper
    |   `-- mappers/              property / parameter / unit vocab mappers
    |
    |-- thermoml_to_fairfluids/   INBOUND producer: ThermoML XML -> Canonical
    |   |-- converter.py          orchestration: XML -> canonical -> dict
    |   |-- parser.py             ThermoML XML -> Raw* models
    |   `-- canonical_builder.py  Raw* -> Canonical* (ThermoML-specific)
    |
    |-- fairfluids_to_thermoml/   OUTBOUND: FAIRFluidsDocument -> ThermoML XML
    |   `-- converter.py          convert() entry point
    |
    `-- thermoml_api/             ThermoML web-archive download/query helpers

The three inbound producers (``fluid_io``, ``cml_parser``,
``thermoml_to_fairfluids``) all depend on ``canonical/`` and nothing in
``canonical/`` depends back on them -- the shared/specific split is explicit in
the folder layout.

Lower-level entry points (used internally / by the CLI)::

    from fairfluids.io.thermoml_to_fairfluids import convert as thermoml_to_ff
    from fairfluids.io.fairfluids_to_thermoml import convert as ff_to_thermoml
"""

from pathlib import Path
from typing import List, Optional, Union

from fairfluids.core.lib import FAIRFluidsDocument
from fairfluids.io.fluid_io import FluidIO, from_csv
from fairfluids.io.pubchem import fetch_compound_from_pubchem
from fairfluids.io.cml_parser import FAIRFluidsCMLParser, from_cml


def from_thermoml(
    xml_path: Union[str, Path],
    *,
    document: Optional[FAIRFluidsDocument] = None,
    fetch_from_pubchem: bool = True,
) -> List[FAIRFluidsDocument]:
    """Convert a ThermoML XML file into FAIRFluids documents.

    The ThermoML converter derives citation and compound metadata directly from
    the source file, so a template ``document`` is not required. When provided,
    the template only *fills gaps*: its citation/version are applied solely
    where the source file did not supply them — the file's own metadata always
    wins. This keeps ``document=`` semantics consistent with :func:`from_csv`
    and :func:`from_cml` (an optional metadata template) without overriding the
    self-describing ThermoML source.

    Args:
        xml_path: Path to the ThermoML XML file.
        document: Optional template document supplying citation/version metadata
            used only to fill gaps the source file leaves empty.
        fetch_from_pubchem: If True (default), enrich compounds with PubChem metadata.

    Returns:
        A list of :class:`FAIRFluidsDocument`. A ThermoML file carries a single
        citation, so the list always has exactly one element; the list return
        type matches :func:`from_csv` and :func:`from_cml`.
    """
    from fairfluids.io.thermoml_to_fairfluids.converter import convert

    document_dict = convert(xml_path, fetch_from_pubchem=fetch_from_pubchem)
    doc = FAIRFluidsDocument.model_validate(document_dict)

    # Optional template: fill only what the source did not provide. ThermoML is
    # self-describing, so in practice these rarely trigger — but accepting the
    # template keeps the contract uniform across all three converters.
    if document is not None:
        if not doc.citation and document.citation:
            doc.citation = document.citation
        if not doc.version and document.version:
            doc.version = document.version

    return [doc]


__all__ = [
    "FluidIO",
    "fetch_compound_from_pubchem",
    "FAIRFluidsCMLParser",
    "from_cml",
    "from_csv",
    "from_thermoml",
]
