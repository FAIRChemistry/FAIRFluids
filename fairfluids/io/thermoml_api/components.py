"""Resolve component common names to InChIKeys via PubChem."""

from __future__ import annotations

from dataclasses import dataclass

from fairfluids.io.pubchem import fetch_compound_from_pubchem
from fairfluids.io.thermoml_to_fairfluids.pubchem import _search_cid_by_name


@dataclass(frozen=True)
class ResolvedComponent:
    common_name: str
    inchikey: str | None = None
    pubchem_cid: int | None = None
    lookup_error: str | None = None

    @property
    def has_inchikey(self) -> bool:
        return bool(self.inchikey)


def resolve_component(common_name: str) -> ResolvedComponent:
    """Resolve a single common name to an InChIKey using PubChem."""
    name = common_name.strip()
    if not name:
        return ResolvedComponent(common_name=common_name, lookup_error="empty name")

    cid = _search_cid_by_name(name)
    if cid is None:
        return ResolvedComponent(
            common_name=name,
            lookup_error=f"PubChem CID not found for '{name}'",
        )

    fetched = fetch_compound_from_pubchem(cid)
    if not fetched:
        return ResolvedComponent(
            common_name=name,
            pubchem_cid=cid,
            lookup_error=f"PubChem property fetch failed for CID {cid}",
        )

    inchikey = fetched.get("standard_InChI_key")
    if not inchikey:
        return ResolvedComponent(
            common_name=name,
            pubchem_cid=cid,
            lookup_error=f"No InChIKey returned for CID {cid}",
        )

    return ResolvedComponent(
        common_name=name,
        inchikey=inchikey,
        pubchem_cid=cid,
    )


def resolve_components(common_names: list[str]) -> list[ResolvedComponent]:
    """Resolve each non-empty common name via PubChem."""
    return [resolve_component(name) for name in common_names if name.strip()]
