"""DOI citation enrichment for the FAIRFluids builder.

Thin canonical-layer seam over :mod:`fairfluids.io.resolve_doi` (mirroring
:mod:`fairfluids.io.canonical.pubchem`). Given a DOI, it fetches bibliographic
metadata and merges it under any values the producer already knows, so
caller-provided fields always stay authoritative and the web lookup only fills
the gaps.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fairfluids.io.resolve_doi import resolve_doi

logger = logging.getLogger(__name__)

# Scalar citation fields the builder can fill from a DOI lookup.
_SCALAR_FIELDS = ("title", "pub_name", "pub_year", "volume", "page", "lit_type", "url")


def enrich_citation_from_doi(
    doi: Optional[str],
    existing: Optional[Dict[str, Any]] = None,
    *,
    fetch: bool = True,
    **resolve_kwargs: Any,
) -> Dict[str, Any]:
    """Resolve ``doi`` to citation fields, keeping ``existing`` values authoritative.

    Args:
        doi: The DOI to resolve (any common form).
        existing: Fields the producer already supplied (e.g. from a template
            citation). Present/non-empty values here are never overwritten.
        fetch: When False, skip the network entirely and return only
            ``existing`` (so callers can disable enrichment with one flag).
        **resolve_kwargs: Forwarded to :func:`resolve_doi` (timeout, providers…).

    Returns:
        A dict with the scalar citation fields plus ``"authors"`` (a list of
        ``{given_name, family_name, orcid}`` dicts from the DOI, only useful when
        the caller has no authors of its own). Empty/partial when the DOI cannot
        be resolved. Never raises — network failures degrade to ``existing``.
    """
    merged: Dict[str, Any] = {k: v for k, v in (existing or {}).items() if v}

    if not fetch or not doi:
        merged.setdefault("authors", [])
        return merged

    meta = resolve_doi(doi, **resolve_kwargs)
    if not meta:
        merged.setdefault("authors", [])
        return merged

    for key in _SCALAR_FIELDS:
        if not merged.get(key) and meta.get(key):
            merged[key] = meta[key]
    # The resolved DOI is authoritative for the ``doi`` field only when the
    # caller left it blank.
    if not merged.get("doi") and meta.get("doi"):
        merged["doi"] = meta["doi"]

    merged["authors"] = meta.get("authors") or []
    logger.debug("DOI enrichment for %s filled: %s", doi, sorted(merged))
    return merged
