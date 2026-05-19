"""PubChem REST helpers for compound metadata (I/O boundary)."""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests


def fetch_compound_from_pubchem(pubchem_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch compound information from PubChem using the pubChemID.

    Args:
        pubchem_id: The PubChem CID

    Returns:
        Dictionary with compound information or None if not found
    """
    try:
        info_url = (
            f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{pubchem_id}/"
            "property/IUPACName,MolecularFormula,MolecularWeight,SMILES,InChI,InChIKey,Title/JSON"
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
    except Exception as e:
        print(f"Error fetching compound from PubChem: {e}")
        return None

    return None
