"""DOI -> citation-metadata resolution (single network I/O boundary).

All DOI-based bibliographic lookups in the package funnel through this module,
so the provider order, retry/backoff policy and JSON-shape handling live in
exactly one place (mirroring :mod:`fairfluids.io.pubchem`).

Three public metadata providers are queried, in order, until the citation is
sufficiently complete:

- **Crossref** (``api.crossref.org``) — richest structured metadata, gives
  given/family author names, container title, volume and page directly.
- **OpenAlex** (``api.openalex.org``) — good coverage incl. ORCID iDs.
- **Semantic Scholar** (``api.semanticscholar.org``) — final fallback.

The single public helper is :func:`resolve_doi`, which returns a normalised
dict (or ``None`` when nothing could be resolved / the network is unavailable)::

    {
        "doi": "10.1016/j.jct.2014.06.031",
        "title": "…",
        "authors": [{"given_name": "…", "family_name": "…", "orcid": "…"}],
        "pub_name": "The Journal of Chemical Thermodynamics",
        "pub_year": "2014",
        "volume": "78",
        "page": "24-32",
        "lit_type": "journal",   # a key understood by the builder's LitType map
        "url": "https://doi.org/…",
    }

Every network access degrades gracefully: on timeout, HTTP error or malformed
payload the provider is skipped (a debug/warning log is emitted) so that offline
conversion still succeeds — just without the citation enrichment.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

# Contact string sent to Crossref/OpenAlex to join their "polite pool" (faster,
# more reliable than anonymous access). A generic project contact is fine.
_CONTACT_EMAIL = "contact@fairchemistry.org"
_USER_AGENT = (
    f"FAIRFluids/0.1 (https://github.com/FAIRChemistry/FAIRFluids; "
    f"mailto:{_CONTACT_EMAIL})"
)

_CROSSREF_BASE = "https://api.crossref.org/works"
_OPENALEX_BASE = "https://api.openalex.org/works"
_SEMANTIC_SCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1/paper"

# HTTP statuses worth retrying with exponential backoff (transient/throttling).
_RETRYABLE_STATUSES = {429, 500, 502, 503, 504}

# The normalised citation fields the builder consumes.
_CITATION_FIELDS = (
    "title",
    "pub_name",
    "pub_year",
    "volume",
    "page",
    "lit_type",
    "url",
)

DEFAULT_PROVIDERS: tuple[str, ...] = ("crossref", "openalex", "semantic_scholar")


# ---------------------------------------------------------------------------
# DOI normalisation
# ---------------------------------------------------------------------------


def _bare_doi(doi: Optional[str]) -> Optional[str]:
    """Strip URL prefixes / ``doi:`` scheme, returning the bare ``10.x/...`` DOI."""
    if not doi:
        return None
    doi = doi.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/",
                   "http://dx.doi.org/", "doi:", "DOI:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
            break
    doi = doi.strip()
    return doi or None


# ---------------------------------------------------------------------------
# Literature-type mapping (provider vocab -> builder LitType-map keys)
# ---------------------------------------------------------------------------

# Values here are keys understood by ``fairfluids_builder._LIT_TYPE_MAP``.
_TYPE_MAP: Dict[str, str] = {
    # Crossref ``type``
    "journal-article": "journal",
    "journal": "journal",
    "book": "book",
    "book-chapter": "book",
    "monograph": "book",
    "reference-book": "book",
    "proceedings-article": "conference proceedings",
    "proceedings": "conference proceedings",
    "dissertation": "thesis",
    "report": "report",
    "report-component": "report",
    "posted-content": "unspecified",
    "peer-review": "unspecified",
    # OpenAlex ``type`` (superset)
    "article": "journal",
    "preprint": "unspecified",
    "dataset": "unspecified",
    "book-series": "book",
    "proceedings-series": "conference proceedings",
    "reference-entry": "book",
}


def _map_type(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    return _TYPE_MAP.get(raw.strip().lower())


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _split_full_name(name: Optional[str]) -> Dict[str, Optional[str]]:
    """Split a free-text ``"Given Middle Family"`` into given/family parts.

    Providers that expose only a single display name (OpenAlex, Semantic
    Scholar) get a best-effort split: the last whitespace-delimited token is the
    family name, the remainder is the given name.
    """
    if not name:
        return {"given_name": None, "family_name": None}
    parts = name.strip().split()
    if len(parts) == 1:
        return {"given_name": None, "family_name": parts[0]}
    return {"given_name": " ".join(parts[:-1]), "family_name": parts[-1]}


def _clean_orcid(orcid: Optional[str]) -> Optional[str]:
    """Reduce an ORCID URL/iD to the bare ``0000-0002-1825-0097`` form."""
    if not orcid:
        return None
    orcid = orcid.strip()
    marker = "orcid.org/"
    if marker in orcid:
        orcid = orcid.split(marker, 1)[-1]
    return orcid or None


def _first(seq: Any) -> Optional[Any]:
    if isinstance(seq, (list, tuple)) and seq:
        return seq[0]
    return None


def _get(
    url: str,
    *,
    params: Optional[Dict[str, str]] = None,
    timeout: float,
    max_retries: int,
    retry_delay: float,
) -> Optional[Dict[str, Any]]:
    """GET ``url`` and return parsed JSON, retrying transient failures.

    Returns ``None`` (never raises) on 404, other client errors, exhausted
    retries or malformed JSON — the caller treats that as "provider had nothing".
    """
    headers = {"User-Agent": _USER_AGENT, "Accept": "application/json"}
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url, params=params, headers=headers, timeout=timeout
            )
            if response.status_code == 200:
                return response.json()
            if (
                response.status_code in _RETRYABLE_STATUSES
                and attempt < max_retries - 1
            ):
                time.sleep(retry_delay * (2**attempt))
                continue
            if response.status_code == 404:
                logger.debug("DOI lookup 404 at %s", url)
            else:
                logger.warning(
                    "DOI lookup failed (status %s) at %s", response.status_code, url
                )
            return None
        except (requests.exceptions.RequestException, ValueError) as exc:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2**attempt))
                continue
            logger.warning("DOI lookup errored at %s: %s", url, exc)
            return None
    return None


# ---------------------------------------------------------------------------
# Providers — each returns a normalised dict or ``None``
# ---------------------------------------------------------------------------


def _from_crossref(doi: str, **kw: Any) -> Optional[Dict[str, Any]]:
    payload = _get(
        f"{_CROSSREF_BASE}/{quote(doi)}",
        params={"mailto": _CONTACT_EMAIL},
        **kw,
    )
    if not payload:
        return None
    msg = payload.get("message")
    if not isinstance(msg, dict):
        return None

    authors: List[Dict[str, Optional[str]]] = []
    for a in msg.get("author", []) or []:
        family = (a.get("family") or "").strip() or None
        given = (a.get("given") or "").strip() or None
        if not family and not given:
            # Organisation-style author (only ``name``).
            family = (a.get("name") or "").strip() or None
        if family or given:
            authors.append(
                {
                    "given_name": given,
                    "family_name": family,
                    "orcid": _clean_orcid(a.get("ORCID")),
                }
            )

    issued = (msg.get("issued") or {}).get("date-parts") or []
    year = None
    if issued and isinstance(issued[0], list) and issued[0]:
        year = str(issued[0][0])

    return {
        "doi": (msg.get("DOI") or doi).lower(),
        "title": _first(msg.get("title")),
        "authors": authors,
        "pub_name": _first(msg.get("container-title")),
        "pub_year": year,
        "volume": msg.get("volume"),
        "page": msg.get("page"),
        "lit_type": _map_type(msg.get("type")),
        "url": msg.get("URL") or f"https://doi.org/{doi}",
    }


def _from_openalex(doi: str, **kw: Any) -> Optional[Dict[str, Any]]:
    payload = _get(
        f"{_OPENALEX_BASE}/https://doi.org/{quote(doi)}",
        params={"mailto": _CONTACT_EMAIL},
        **kw,
    )
    if not payload or not isinstance(payload, dict):
        return None

    authors: List[Dict[str, Optional[str]]] = []
    for ship in payload.get("authorships", []) or []:
        author = ship.get("author") or {}
        parts = _split_full_name(author.get("display_name"))
        if parts["given_name"] or parts["family_name"]:
            authors.append(
                {
                    "given_name": parts["given_name"],
                    "family_name": parts["family_name"],
                    "orcid": _clean_orcid(author.get("orcid")),
                }
            )

    biblio = payload.get("biblio") or {}
    first_page = biblio.get("first_page")
    last_page = biblio.get("last_page")
    page = None
    if first_page and last_page:
        page = f"{first_page}-{last_page}"
    elif first_page:
        page = str(first_page)

    source = (payload.get("primary_location") or {}).get("source") or {}
    year = payload.get("publication_year")

    return {
        "doi": (_bare_doi(payload.get("doi")) or doi).lower(),
        "title": payload.get("title") or payload.get("display_name"),
        "authors": authors,
        "pub_name": source.get("display_name"),
        "pub_year": str(year) if year else None,
        "volume": biblio.get("volume"),
        "page": page,
        "lit_type": _map_type(payload.get("type")),
        "url": payload.get("doi") or f"https://doi.org/{doi}",
    }


def _from_semantic_scholar(doi: str, **kw: Any) -> Optional[Dict[str, Any]]:
    fields = "title,year,venue,authors,externalIds,publicationTypes"
    payload = _get(
        f"{_SEMANTIC_SCHOLAR_BASE}/DOI:{quote(doi)}",
        params={"fields": fields},
        **kw,
    )
    if not payload or not isinstance(payload, dict):
        return None

    authors: List[Dict[str, Optional[str]]] = []
    for a in payload.get("authors", []) or []:
        parts = _split_full_name(a.get("name"))
        if parts["given_name"] or parts["family_name"]:
            authors.append(
                {
                    "given_name": parts["given_name"],
                    "family_name": parts["family_name"],
                    "orcid": None,
                }
            )

    pub_types = payload.get("publicationTypes") or []
    lit_type = "journal" if "JournalArticle" in pub_types else None
    year = payload.get("year")

    return {
        "doi": doi.lower(),
        "title": payload.get("title"),
        "authors": authors,
        "pub_name": payload.get("venue"),
        "pub_year": str(year) if year else None,
        "volume": None,
        "page": None,
        "lit_type": lit_type,
        "url": f"https://doi.org/{doi}",
    }


_PROVIDER_FUNCS = {
    "crossref": _from_crossref,
    "openalex": _from_openalex,
    "semantic_scholar": _from_semantic_scholar,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _merge(base: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
    """Fill fields missing from ``base`` with values from ``extra`` (base wins)."""
    for key in _CITATION_FIELDS:
        if not base.get(key) and extra.get(key):
            base[key] = extra[key]
    if not base.get("authors") and extra.get("authors"):
        base["authors"] = extra["authors"]
    if not base.get("doi") and extra.get("doi"):
        base["doi"] = extra["doi"]
    return base


def _is_complete(meta: Dict[str, Any]) -> bool:
    """True when the core citation fields are all present (short-circuit merge)."""
    return bool(
        meta.get("title")
        and meta.get("authors")
        and meta.get("pub_name")
        and meta.get("pub_year")
    )


def resolve_doi(
    doi: str,
    *,
    providers: Sequence[str] = DEFAULT_PROVIDERS,
    timeout: float = 15.0,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> Optional[Dict[str, Any]]:
    """Resolve a DOI to normalised citation metadata.

    Providers are queried in ``providers`` order; each fills any fields the
    previous ones left blank, and the loop stops early once the core fields
    (title, authors, journal, year) are all present.

    Args:
        doi: A DOI in any common form (bare, ``doi:``, or a ``doi.org`` URL).
        providers: Provider keys to try, in order. Defaults to Crossref,
            OpenAlex, Semantic Scholar.
        timeout: Per-request timeout in seconds.
        max_retries: Attempts per request on transient failures.
        retry_delay: Base delay (seconds) for exponential backoff.

    Returns:
        A normalised citation dict, or ``None`` if the DOI is empty or no
        provider returned anything (e.g. offline / unknown DOI).
    """
    bare = _bare_doi(doi)
    if not bare:
        return None

    request_kw = dict(
        timeout=timeout, max_retries=max_retries, retry_delay=retry_delay
    )
    merged: Dict[str, Any] = {}
    for name in providers:
        func = _PROVIDER_FUNCS.get(name)
        if func is None:
            logger.warning("Unknown DOI provider %r; skipping.", name)
            continue
        try:
            result = func(bare, **request_kw)
        except Exception as exc:  # noqa: BLE001 - network boundary, log & degrade
            logger.warning("DOI provider %r errored for %s: %s", name, bare, exc)
            result = None
        if not result:
            continue
        merged = _merge(merged, result) if merged else result
        if _is_complete(merged):
            break

    if not merged or not merged.get("title"):
        logger.info("No citation metadata resolved for DOI %s", bare)
        return None

    merged.setdefault("doi", bare)
    merged.setdefault("url", f"https://doi.org/{bare}")
    merged.setdefault("authors", [])
    return merged
