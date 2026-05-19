"""
PubChem enrichment helpers for ThermoML -> FAIRFluids conversion.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import quote

import requests

from fairfluids.io.pubchem import fetch_compound_from_pubchem

logger = logging.getLogger(__name__)


def _search_cid_by_name(
    compound_name: str, max_retries: int = 3, retry_delay: float = 2.0
) -> Optional[int]:
    """
    Resolve a PubChem CID from a compound name.
    """
    encoded_name = quote(compound_name)
    search_url = (
        f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_name}/JSON"
    )

    for attempt in range(max_retries):
        try:
            response = requests.get(search_url, timeout=30)
            if response.status_code == 200:
                payload = response.json()
                compounds = payload.get("PC_Compounds", [])
                if compounds:
                    return compounds[0]["id"]["id"]["cid"]
                return None
            if response.status_code in {429, 502, 503} and attempt < max_retries - 1:
                time.sleep(retry_delay * (2**attempt))
                continue
            if response.status_code in {400, 404}:
                return None
            return None
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2**attempt))
                continue
            return None
    return None


def enrich_compound_from_pubchem(
    common_name: Optional[str],
    pubchem_cid: Optional[int],
    standard_inchi: Optional[str],
    standard_inchi_key: Optional[str],
) -> Dict[str, Any]:
    """
    Build partial FAIRFluids compound fields from PubChem.

    Returns an empty dict when enrichment is not possible.
    """
    cid = pubchem_cid
    if cid is None:
        if not common_name:
            return {}
        cid = _search_cid_by_name(common_name)
        if cid is None:
            return {}

    fetched = fetch_compound_from_pubchem(cid)
    if not fetched:
        return {}

    # Keep ThermoML identifiers authoritative if already present.
    merged_inchi = standard_inchi or fetched.get("standard_InChI")
    merged_inchi_key = standard_inchi_key or fetched.get("standard_InChI_key")

    logger.debug("PubChem enrichment succeeded for '%s' (CID %s)", common_name, cid)
    return {
        "pubChemID": fetched.get("pubChemID"),
        "commonName": fetched.get("commonName") or common_name,
        "name_IUPAC": fetched.get("name_IUPAC"),
        "smiles_code": fetched.get("smiles_code"),
        "molar_weigth": fetched.get("molar_weigth"),
        "standard_InChI": merged_inchi,
        "standard_InChI_key": merged_inchi_key,
    }
