"""
PubChem enrichment helpers for ThermoML -> FAIRFluids conversion.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fairfluids.io.pubchem import fetch_compound_from_pubchem, search_cid_by_name

logger = logging.getLogger(__name__)


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
        cid = search_cid_by_name(common_name)
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
