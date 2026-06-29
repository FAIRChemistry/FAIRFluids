"""PubChem REST helpers for compound metadata (single I/O boundary).

All PubChem network access in the package funnels through this module, so the
retry/backoff policy and the JSON-shape handling live in exactly one place.
Three public helpers are provided:

- :func:`search_cid_by_name` — resolve a compound name to a PubChem CID.
- :func:`fetch_compound_from_pubchem` — fetch metadata for a known CID.
- :func:`fetch_compound_by_name` — convenience wrapper chaining the two.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

_PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound"
_PROPERTY_FIELDS = (
    "IUPACName,MolecularFormula,MolecularWeight,SMILES,InChI,InChIKey,Title"
)
# HTTP statuses worth retrying with exponential backoff (transient/throttling).
_RETRYABLE_STATUSES = {429, 500, 502, 503}


def search_cid_by_name(
    compound_name: str, *, max_retries: int = 3, retry_delay: float = 2.0
) -> Optional[int]:
    """Resolve a PubChem CID from a compound name.

    Args:
        compound_name: Free-text compound name to search for.
        max_retries: Maximum number of attempts on transient failures.
        retry_delay: Base delay (seconds) for exponential backoff.

    Returns:
        The first matching CID, or ``None`` if not found / unresolvable.
    """
    if not compound_name:
        return None

    encoded_name = quote(compound_name)
    search_url = f"{_PUBCHEM_BASE}/name/{encoded_name}/JSON"

    for attempt in range(max_retries):
        try:
            response = requests.get(search_url, timeout=30)
            if response.status_code == 200:
                compounds = response.json().get("PC_Compounds", [])
                if compounds:
                    return compounds[0]["id"]["id"]["cid"]
                return None
            if response.status_code in _RETRYABLE_STATUSES and attempt < max_retries - 1:
                time.sleep(retry_delay * (2**attempt))
                continue
            if response.status_code == 404:
                logger.info("Compound '%s' not found in PubChem", compound_name)
            else:
                logger.warning(
                    "PubChem name search for '%s' failed (status %s)",
                    compound_name,
                    response.status_code,
                )
            return None
        except requests.exceptions.RequestException as exc:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2**attempt))
                continue
            logger.warning(
                "PubChem name search for '%s' errored: %s", compound_name, exc
            )
            return None
    return None


def fetch_compound_from_pubchem(pubchem_id: int) -> Optional[Dict[str, Any]]:
    """Fetch compound metadata from PubChem using a known CID.

    Args:
        pubchem_id: The PubChem CID.

    Returns:
        A dict of FAIRFluids compound fields, or ``None`` if not found.
    """
    try:
        info_url = (
            f"{_PUBCHEM_BASE}/cid/{pubchem_id}/property/{_PROPERTY_FIELDS}/JSON"
        )
        info_response = requests.get(info_url, timeout=10)

        if info_response.status_code == 200:
            data = info_response.json()
            if (
                "PropertyTable" in data
                and "Properties" in data["PropertyTable"]
                and len(data["PropertyTable"]["Properties"]) > 0
            ):
                info_data = data["PropertyTable"]["Properties"][0]

                return {
                    "pubChemID": pubchem_id,
                    "commonName": info_data.get("Title", f"Compound_{pubchem_id}"),
                    "name_IUPAC": info_data.get("IUPACName"),
                    "smiles_code": info_data.get("SMILES"),
                    "molar_weigth": info_data.get("MolecularWeight"),
                    "standard_InChI": info_data.get("InChI"),
                    "standard_InChI_key": info_data.get("InChIKey"),
                    "SELFIE": None,
                    "sigma_profile": None,
                }
    except Exception as exc:  # noqa: BLE001 - network boundary, log and degrade
        logger.warning("Error fetching CID %s from PubChem: %s", pubchem_id, exc)
        return None

    return None


def fetch_compound_by_name(
    compound_name: str, *, max_retries: int = 3, retry_delay: float = 2.0
) -> Optional[Dict[str, Any]]:
    """Fetch compound metadata from PubChem by name (CID lookup + fetch).

    Args:
        compound_name: Free-text compound name to search for.
        max_retries: Maximum number of attempts for the name->CID search.
        retry_delay: Base delay (seconds) for exponential backoff.

    Returns:
        The same metadata dict as :func:`fetch_compound_from_pubchem`, or
        ``None`` if the name cannot be resolved.
    """
    cid = search_cid_by_name(
        compound_name, max_retries=max_retries, retry_delay=retry_delay
    )
    if cid is None:
        return None
    return fetch_compound_from_pubchem(cid)
