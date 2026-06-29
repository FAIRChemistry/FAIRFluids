"""ThermoML Cordra API search client."""

from __future__ import annotations

import json
import time
from typing import Any

import requests

API_BASE = "https://trc.nist.gov/ThermoML-API/objects"
XML_BASE = "https://trc.nist.gov/ThermoML"

REQUEST_CONTEXT: dict[str, bool] = {
    "Compound": True,
    "PureOrMixtureData": True,
    "data_summary": True,
}

DEFAULT_PAGE_SIZE = 100
DEFAULT_DELAY_SEC = 0.1
DEFAULT_TIMEOUT = 60
USER_AGENT = "fairfluids-thermoml-fetcher/0.1"


def _get(obj: dict[str, Any], key: str) -> Any:
    return obj.get(key) or obj.get("content", {}).get(key)


def compounds_of(obj: dict[str, Any]) -> list[dict[str, Any]]:
    return _get(obj, "Compound") or []


def poms_of(obj: dict[str, Any]) -> list[dict[str, Any]]:
    return _get(obj, "PureOrMixtureData") or []


def doi_of(obj: dict[str, Any]) -> str:
    raw = obj.get("id") or obj.get("@id") or _get(obj, "id") or ""
    return str(raw).split("trc.thermoml/", 1)[-1]


def _quote_lucene_term(name: str) -> str:
    stripped = name.strip()
    if not stripped:
        return stripped
    if " " in stripped:
        escaped = stripped.replace('"', '\\"')
        return f'"{escaped}"'
    return stripped


def build_lucene_query(components: list[str]) -> str:
    """Build a Cordra Lucene query requiring all component common names."""
    names = [c.strip() for c in components if c.strip()]
    if not names:
        raise ValueError("At least one component common name is required")
    clauses = [f"/Compound/_/sCommonName/_:{_quote_lucene_term(name)}" for name in names]
    return "type:TRCTml4 AND " + " AND ".join(clauses)


def search_all(
    query: str,
    *,
    page_size: int = DEFAULT_PAGE_SIZE,
    delay_sec: float = DEFAULT_DELAY_SEC,
    timeout: int = DEFAULT_TIMEOUT,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """Page through ThermoML API hits until exhausted."""
    sess = session or requests.Session()
    sess.headers.setdefault("User-Agent", USER_AGENT)

    hits: list[dict[str, Any]] = []
    page = 0
    request_context = json.dumps(REQUEST_CONTEXT)

    while True:
        params = {
            "query": query,
            "pageNum": page,
            "pageSize": page_size,
            "requestContext": request_context,
        }
        response = sess.get(API_BASE, params=params, timeout=timeout)
        response.raise_for_status()
        body = response.json()

        results = body.get("results") or []
        if not results:
            break
        hits.extend(results)

        total = body.get("size")
        if total is not None and len(hits) >= total:
            break
        if len(results) < page_size:
            break

        page += 1
        time.sleep(delay_sec)

    return hits
