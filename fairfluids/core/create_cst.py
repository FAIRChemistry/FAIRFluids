"""
Creates a Chemical Sample Table (CST) from FAIRFluids JSON files.

This function extracts IUPAC names and CAS Registry Numbers from compounds
and fetches missing data from PubChem.
"""

import json
import requests
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import pandas as pd


def fetch_cas_from_pubchem(pubchem_id: int) -> Optional[str]:
    """
    Fetches CAS Registry Number from PubChem for a given PubChem CID.

    Args:
        pubchem_id: The PubChem CID

    Returns:
        CAS Registry Number as string or None if not found
    """
    try:
        # PubChem API for Registry Numbers (CAS is one of the Registry Numbers)
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{pubchem_id}/synonyms/JSON"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if "InformationList" in data and "Information" in data["InformationList"]:
                info_list = data["InformationList"]["Information"]
                if len(info_list) > 0 and "Synonym" in info_list[0]:
                    synonyms = info_list[0]["Synonym"]
                    # CAS Registry Numbers typically have the format: XXXXX-XX-X
                    # Search for entries matching this format
                    for synonym in synonyms:
                        if isinstance(synonym, str) and "-" in synonym:
                            parts = synonym.split("-")
                            # CAS numbers typically have 3 parts: XXXXX-XX-X
                            if len(parts) == 3:
                                try:
                                    # Check if all parts are numeric (except possibly leading zeros)
                                    int(parts[0])
                                    int(parts[1])
                                    int(parts[2])
                                    # If all parts are numeric, it's likely a CAS number
                                    if (
                                        len(parts[0]) >= 2
                                        and len(parts[1]) == 2
                                        and len(parts[2]) == 1
                                    ):
                                        return synonym
                                except ValueError:
                                    continue

        # Alternative: Try directly via Property API
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{pubchem_id}/property/RegistryNumber/JSON"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if "PropertyTable" in data and "Properties" in data["PropertyTable"]:
                props = data["PropertyTable"]["Properties"]
                if len(props) > 0 and "RegistryNumber" in props[0]:
                    registry_numbers = props[0]["RegistryNumber"]
                    if isinstance(registry_numbers, list) and len(registry_numbers) > 0:
                        # CAS numbers typically start with a number
                        for reg_num in registry_numbers:
                            if isinstance(reg_num, str) and "-" in reg_num:
                                parts = reg_num.split("-")
                                if len(parts) == 3:
                                    try:
                                        int(parts[0])
                                        int(parts[1])
                                        int(parts[2])
                                        return reg_num
                                    except ValueError:
                                        continue
                    elif isinstance(registry_numbers, str):
                        return registry_numbers
    except Exception as e:
        print(f"Error fetching CAS number from PubChem for CID {pubchem_id}: {e}")

    return None


def fetch_iupac_and_cas_from_pubchem(pubchem_id: int) -> Dict[str, Optional[str]]:
    """
    Fetches IUPAC name and CAS Registry Number from PubChem for a given PubChem CID.

    Args:
        pubchem_id: The PubChem CID

    Returns:
        Dictionary with 'name_IUPAC' and 'cas_registry_number' or None values
    """
    result = {"name_IUPAC": None, "cas_registry_number": None}

    try:
        # Fetch IUPAC name and other properties
        info_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{pubchem_id}/property/IUPACName/JSON"
        info_response = requests.get(info_url, timeout=10)

        if info_response.status_code == 200:
            data = info_response.json()
            if (
                "PropertyTable" in data
                and "Properties" in data["PropertyTable"]
                and len(data["PropertyTable"]["Properties"]) > 0
            ):
                info_data = data["PropertyTable"]["Properties"][0]
                result["name_IUPAC"] = info_data.get("IUPACName")

        # Fetch CAS Registry Number
        cas_number = fetch_cas_from_pubchem(pubchem_id)
        result["cas_registry_number"] = cas_number

    except Exception as e:
        print(f"Error fetching PubChem data for CID {pubchem_id}: {e}")

    return result


def create_cst(
    json_files: Union[str, Path, List[Union[str, Path]]],
    output_path: Union[str, Path],
    include_additional_fields: bool = False,
) -> pd.DataFrame:
    """
    Creates a Chemical Sample Table (CST) from one or more FAIRFluids JSON files.

    The function extracts IUPAC names and CAS Registry Numbers from compounds
    and fetches missing data from PubChem.

    Args:
        json_files: Path to a JSON file or list of paths to JSON files
        output_path: Path for the output XLSX file
        include_additional_fields: If True, additional fields like commonName and pubChemID are added

    Returns:
        pandas.DataFrame with the extracted data

    Example:
        >>> df = create_cst(
        ...     ["file1.json", "file2.json"],
        ...     "chemical_sample_table.xlsx"
        ... )
    """
    # Normalize input to list
    if isinstance(json_files, (str, Path)):
        json_files = [json_files]

    # Collect all unique compounds
    compounds_dict = {}  # Use compoundID as key to avoid duplicates

    for json_file in json_files:
        json_path = Path(json_file)
        if not json_path.exists():
            print(f"Warning: File {json_path} does not exist, skipping...")
            continue

        print(f"Loading {json_path}...")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract compounds
        if "compound" not in data:
            print(f"Warning: No 'compound' block found in {json_path}")
            continue

        for compound in data["compound"]:
            compound_id = compound.get("compoundID")
            if not compound_id:
                print(f"Warning: Compound without compoundID found, skipping...")
                continue

            # If compound already exists, skip (or update if necessary)
            if compound_id not in compounds_dict:
                compounds_dict[compound_id] = {
                    "compoundID": compound_id,
                    "name_IUPAC": compound.get("name_IUPAC"),
                    "cas_registry_number": compound.get(
                        "cas_registry_number"
                    ),  # If already present
                    "commonName": compound.get("commonName"),
                    "pubChemID": compound.get("pubChemID"),
                }

    # Process each compound and fetch missing data from PubChem
    compounds_list = []
    for compound_id, compound_data in compounds_dict.items():
        pubchem_id = compound_data.get("pubChemID")
        iupac_name = compound_data.get("name_IUPAC")
        cas_number = compound_data.get("cas_registry_number")

        # If PubChem ID is present and data is missing, fetch it from PubChem
        if pubchem_id is not None:
            try:
                pubchem_id = int(pubchem_id)
            except (ValueError, TypeError):
                print(f"Warning: Invalid pubChemID for {compound_id}: {pubchem_id}")
                pubchem_id = None

        if pubchem_id is not None and (iupac_name is None or cas_number is None):
            print(
                f"Fetching missing data from PubChem for {compound_id} (CID: {pubchem_id})..."
            )
            pubchem_data = fetch_iupac_and_cas_from_pubchem(pubchem_id)

            if iupac_name is None:
                iupac_name = pubchem_data.get("name_IUPAC")
            if cas_number is None:
                cas_number = pubchem_data.get("cas_registry_number")

        # Create entry for DataFrame
        entry = {
            "IUPAC Name": iupac_name,
            "CAS Registry Number": cas_number,
        }

        if include_additional_fields:
            entry["Compound ID"] = compound_id
            entry["Common Name"] = compound_data.get("commonName")
            entry["PubChem ID"] = compound_data.get("pubChemID")

        compounds_list.append(entry)

    # Create DataFrame
    df = pd.DataFrame(compounds_list)

    # Sort by IUPAC Name (if present)
    if "IUPAC Name" in df.columns:
        df = df.sort_values("IUPAC Name", na_position="last")

    # Save as XLSX
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        df.to_excel(output_path, index=False, engine="openpyxl")
        print(f"\n✓ Chemical Sample Table successfully created: {output_path}")
        print(f"  Number of compounds: {len(df)}")
        print(f"  Compounds with IUPAC Name: {df['IUPAC Name'].notna().sum()}")
        print(
            f"  Compounds with CAS Registry Number: {df['CAS Registry Number'].notna().sum()}"
        )
    except ImportError:
        print(
            "\nError: openpyxl is not installed. Please install it with: pip install openpyxl"
        )
        raise
    except Exception as e:
        print(f"\nError saving XLSX file: {e}")
        raise

    return df
