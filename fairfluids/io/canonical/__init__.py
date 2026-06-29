"""
Shared canonical pipeline core (source-format neutral).

This package holds the machinery every inbound converter (CSV, CML, ThermoML)
depends on, decoupled from any single source format:

    producer -> Canonical models -> build_fairfluids() -> FAIRFluidsDocument dict

Modules
-------
- ``canonical_model``    neutral ``Canonical*`` / ``Raw*`` Pydantic models
- ``fairfluids_builder`` ``build_fairfluids()``: Canonical -> FAIRFluids dict
- ``id_registry``        per-prefix ``"<type>_<n>"`` ID allocator
- ``composition``        mole-fraction inference / completion + molar masses
- ``pubchem``            ``enrich_compound_from_pubchem`` wrapper
- ``mappers``            property / parameter / unit controlled-vocab mappers

A *producer* (e.g. :class:`~fairfluids.io.fluid_io.FluidIO`,
:class:`~fairfluids.io.cml_parser.FAIRFluidsCMLParser`, or the ThermoML
converter) only needs to emit ``Canonical*`` models; ``build_fairfluids`` does
the rest.
"""

from __future__ import annotations

from .canonical_model import (
    CanonicalCitation,
    CanonicalCompound,
    CanonicalDataset,
    CanonicalDocument,
    CanonicalParameter,
    CanonicalProperty,
    CanonicalRow,
    CanonicalSourceCompound,
)
from .fairfluids_builder import build_fairfluids

__all__ = [
    "CanonicalCitation",
    "CanonicalCompound",
    "CanonicalDataset",
    "CanonicalDocument",
    "CanonicalParameter",
    "CanonicalProperty",
    "CanonicalRow",
    "CanonicalSourceCompound",
    "build_fairfluids",
]
