"""
fluid_io.py

Extends the Fluid class with input utilities for loading data from CSV files.

Example CSV format:

# compounds,propertyID,propertyType,parameterID,parameterType,parameterValue,propertyValue,uncertainty,method,method_description
# H2O_001;urea_001,viscosity,viscosity,temp,Temperature, K,298.15,1.23,0.01,measuredRotational viscometer
# H2O_001;urea_001,viscosity,viscosity,temp,Temperature, K,303.15,1.10,0.01,measuredRotational viscometer

Usage:
    from FAIRFluids.core.fluid_io import FluidIO
    from FAIRFluids.core.lib import FAIRFluidsDocument
    fluid = FluidIO()
    fluid.data_from_csv('path/to/data.csv')
    doc = FAIRFluidsDocument()
    doc.fluid.append(fluid)

    # Or with a document (creates multiple fluids grouped by composition and property):
    doc = FAIRFluidsDocument()
    fluid_io = FluidIO()
    fluid_io.data_from_csv('path/to/data.csv', document=doc)
"""

import csv
import json
import uuid
import requests
import time
import random
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from collections import defaultdict, Counter
from urllib.parse import quote
from .lib import (
    Fluid,
    Property,
    Parameter,
    Measurement,
    PropertyValue,
    ParameterValue,
    Method,
    FAIRFluidsDocument,
    Properties,
    Parameters,
    UnitDefinition,
    BaseUnit,
    Version,
    Storage,
    StorageCondition,
)
from .functionalities import fetch_compound_from_pubchem


class FluidIO(Fluid):
    """
    Extends Fluid with input utility to load data from a CSV file.
    """

    def data_from_csv(
        self,
        csv_path: str,
        document: Optional[FAIRFluidsDocument] = None,
        output_dir: Optional[str] = None,
        fetch_from_pubchem: bool = False,
    ) -> List[FAIRFluidsDocument]:
        """
        Create FAIRFluids documents from CSV file.

        Supports two CSV formats:
        1. Old format: Component#1, Component#2, Component#3, Viscosity, cP, Density, g/cm^3, etc.
        2. New format: Compound 1, Compound 2, Compound 3, Molar Fraction 1-3, Property, Property Name, etc.

        Each unique compound combination creates a separate document. Within each document,
        separate fluids are created for each property type (viscosity, polarity, etc.).

        Args:
            csv_path: Path to CSV file
            document: Optional template document (for metadata like citation)
            output_dir: Optional directory to save JSON files
            fetch_from_pubchem: If True, fetch compound information from PubChem

        Returns:
            List of FAIRFluidsDocument objects (one per compound combination)
        """
        # Detect delimiter (semicolon or comma)
        delimiter = ";"
        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            sample = csvfile.read(1024)
            csvfile.seek(0)
            if sample.count(";") > sample.count(","):
                delimiter = ";"
            else:
                delimiter = ","

        # Read CSV and group by compound combinations
        compound_combinations = defaultdict(list)

        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            for row in reader:
                # Try new format first (Compound 1, Compound 2, Compound 3)
                compounds = []
                for i in [1, 2, 3]:
                    comp_col = f"Compound {i}"
                    comp_value = row.get(comp_col, "").strip()
                    if comp_value:
                        compounds.append(comp_value)

                # If new format didn't work, try old format (Component#1, Component#2, Component#3)
                if not compounds:
                    for i in [1, 2, 3]:
                        comp_col = f"Component#{i}"
                        comp_value = row.get(comp_col, "").strip()
                        if comp_value:
                            compounds.append(comp_value)

                if not compounds:
                    continue  # Skip rows with no compounds

                # Create key for grouping (tuple of compound names)
                compound_key = tuple(compounds)
                compound_combinations[compound_key].append(row)

        print(f"Found {len(compound_combinations)} unique compound combinations")

        # Fetch compound data from PubChem if requested
        compound_data_cache = {}
        if fetch_from_pubchem:
            # Collect all unique compounds
            all_unique_compounds = set()
            for compounds_list in compound_combinations.keys():
                for comp in compounds_list:
                    if comp:
                        all_unique_compounds.add(comp)

            print(
                f"\nFetching compound information from PubChem for {len(all_unique_compounds)} unique compounds..."
            )

            # Fetch compound data from PubChem with rate limiting
            # Add a small delay between requests to avoid overwhelming PubChem API
            for idx, compound_name in enumerate(all_unique_compounds):
                compound_data = self._fetch_compound_by_name(compound_name)
                if compound_data:
                    compound_data_cache[compound_name] = compound_data

                # Rate limiting: wait 0.5 seconds between requests to avoid API throttling
                # Skip delay for the last item
                if idx < len(all_unique_compounds) - 1:
                    time.sleep(0.5)

            print(f"\nFetched data for {len(compound_data_cache)} compounds\n")

        documents = []

        # Create a document for each compound combination
        for compound_key, rows in compound_combinations.items():
            compounds_list = list(compound_key)

            # Always create new document for this compound combination
            # (each combination gets its own JSON file)
            doc = FAIRFluidsDocument(version=Version(versionMajor=1, versionMinor=0))

            # If a document template was provided, copy its metadata (but not fluids/compounds)
            if document is not None:
                if document.version:
                    doc.version = document.version
                if document.citation:
                    doc.citation = document.citation

            # Add compounds to document
            # Also map compound names to compound IDs for use in fluids
            compound_name_to_id = {}
            if fetch_from_pubchem:
                for compound_name in compounds_list:
                    if compound_name in compound_data_cache:
                        compound_data = compound_data_cache[compound_name].copy()
                        # Use commonName from PubChem as compoundID, formatted nicely
                        # If commonName is not available, use a cleaned version of the original name
                        if compound_data.get("commonName"):
                            # Use commonName as compoundID (title case for readability)
                            compound_id = compound_data["commonName"].title()
                            compound_data["compoundID"] = compound_id
                        else:
                            # Fallback to original name, cleaned up
                            compound_id = compound_name.strip().title()
                            compound_data["compoundID"] = compound_id
                        compound_name_to_id[compound_name] = compound_id
                        doc.add_to_compound(**compound_data)
                        print(
                            f"  Added compound: {compound_name} -> {compound_id} (CID: {compound_data.get('pubChemID', 'N/A')})"
                        )
                    else:
                        # If not in cache, use the name as-is (title case)
                        compound_id = compound_name.strip().title()
                        compound_name_to_id[compound_name] = compound_id
                        # Add basic compound entry with random pubChemID
                        doc.add_to_compound(
                            compoundID=compound_id,
                            pubChemID=random.randint(999999999999, 9999999999999),
                            commonName=compound_id,
                            SELFIE=None,
                            name_IUPAC=None,
                            standard_InChI=None,
                            standard_InChI_key=None,
                            molar_weigth=None,
                            smiles_code=None,
                            sigma_profile=None,
                        )
            else:
                # If not fetching from PubChem, use compound names as IDs (title case)
                for compound_name in compounds_list:
                    compound_id = compound_name.strip().title()
                    compound_name_to_id[compound_name] = compound_id
                    # Add basic compound entry with random pubChemID
                    doc.add_to_compound(
                        compoundID=compound_id,
                        pubChemID=random.randint(999999999999, 9999999999999),
                        commonName=compound_id,
                        SELFIE=None,
                        name_IUPAC=None,
                        standard_InChI=None,
                        standard_InChI_key=None,
                        molar_weigth=None,
                        smiles_code=None,
                        sigma_profile=None,
                    )

            # Group rows by composition (compounds + molar fractions + storage)
            # Multiple properties can be in the same fluid (as separate measurements)
            # Check if this is new format (has "Property Name" column) or old format
            first_row = rows[0] if rows else {}
            is_new_format = "Property Name" in first_row or "Property" in first_row

            # Group by composition: (molar fractions + storage) - NOT by property name
            composition_groups = defaultdict(list)

            if is_new_format:
                # New format: group by Molar Fractions + Storage (all properties in same fluid)
                for row in rows:
                    property_val = row.get("Property", "").strip()

                    # Skip rows with invalid property values
                    if not property_val or property_val.lower() in [
                        "",
                        "nan",
                        "none",
                        "crystallized",
                    ]:
                        continue

                    # Try to convert to float (handle comma as decimal separator)
                    try:
                        prop_val_float = float(property_val.replace(",", "."))
                    except (ValueError, TypeError):
                        continue

                    # Extract molar fractions for composition key
                    molar_fractions = []
                    for i in range(1, len(compounds_list) + 1):
                        x_col = f"Molar Fraction {i}"
                        x_str = row.get(x_col, "").strip()
                        if x_str and x_str.lower() not in ["", "nan", "none"]:
                            try:
                                molar_fractions.append(float(x_str.replace(",", ".")))
                            except (ValueError, TypeError):
                                molar_fractions.append(None)
                        else:
                            molar_fractions.append(None)

                    # Extract storage condition for grouping
                    # "none" means no storage condition (None), others are normalized
                    storage_str = row.get("Storage", "").strip().lower()
                    if storage_str in ["", "nan", "none"]:
                        storage_key = None  # No storage condition
                    else:
                        storage_key = (
                            storage_str  # Use storage condition as part of key
                        )

                    # Create composition key: (tuple of molar fractions, storage_key)
                    # Note: property_name is NOT part of the key - multiple properties can be in same fluid
                    composition_key = (
                        tuple(molar_fractions),
                        storage_key,
                    )
                    composition_groups[composition_key].append(row)
            else:
                # Old format: group by Molar Fractions only (multiple properties can be in same fluid)
                for row in rows:
                    # Check if row has any valid property value
                    has_valid_property = False
                    viscosity_val = row.get("Viscosity, cP", "").strip()
                    density_val = row.get("Density, g/cm^3", "").strip()

                    if viscosity_val and viscosity_val.lower() not in [
                        "",
                        "nan",
                        "none",
                    ]:
                        try:
                            float(viscosity_val.replace(",", "."))
                            has_valid_property = True
                        except (ValueError, TypeError):
                            pass

                    if (
                        not has_valid_property
                        and density_val
                        and density_val.lower()
                        not in [
                            "",
                            "nan",
                            "none",
                        ]
                    ):
                        try:
                            float(density_val.replace(",", "."))
                            has_valid_property = True
                        except (ValueError, TypeError):
                            pass

                    if not has_valid_property:
                        continue

                    # Extract molar fractions for composition key
                    molar_fractions = []
                    for i in range(1, len(compounds_list) + 1):
                        x_col = f"X#{i} (molar fraction)"
                        x_str = row.get(x_col, "").strip()
                        if x_str and x_str.lower() not in ["", "nan", "none"]:
                            try:
                                molar_fractions.append(float(x_str.replace(",", ".")))
                            except (ValueError, TypeError):
                                molar_fractions.append(None)
                        else:
                            molar_fractions.append(None)

                    # Create composition key: (tuple of molar fractions)
                    # Note: property type is NOT part of the key - multiple properties can be in same fluid
                    composition_key = tuple(molar_fractions)
                    composition_groups[composition_key].append(row)

            # Map compound names to IDs (always use the mapped IDs)
            fluid_compounds = [
                compound_name_to_id.get(name, name.strip().title())
                for name in compounds_list
            ]

            # Create fluid for each composition (molar fractions + storage)
            # Each fluid can contain multiple properties (as separate measurements)
            for composition_key, composition_rows in composition_groups.items():
                if composition_rows:
                    if is_new_format:
                        # New format: (molar_fractions_tuple, storage_key)
                        _, storage_key = composition_key
                    else:
                        # Old format: (molar_fractions_tuple)
                        storage_key = None  # Old format doesn't have storage

                    fluid = self._create_fluid_from_rows(
                        fluid_compounds,
                        composition_rows,
                        is_new_format,
                        storage_key=storage_key,  # Pass storage key to fluid creation
                    )
                    if fluid:
                        doc.fluid.append(fluid)

            documents.append(doc)

            # Save to JSON if output_dir is specified
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)

                # Create filename from compound names
                compound_names = "_".join(
                    [
                        c.replace(" ", "_").replace(",", "").replace(";", "_")[:20]
                        for c in compounds_list
                    ]
                )
                filename = f"{compound_names}.json"
                filepath = output_path / filename

                with open(filepath, "w", encoding="utf-8") as f:
                    json_str = doc.model_dump_json(indent=2)
                    f.write(json_str)

                print(f"Saved document to: {filepath}")

        return documents

    def _fetch_compound_by_name(
        self, compound_name: str, max_retries: int = 3, retry_delay: float = 2.0
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch compound information from PubChem by searching with compound name.
        Includes retry logic for handling timeouts and 503 errors.

        Args:
            compound_name: Name of the compound to search for
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 2.0)

        Returns:
            Dictionary with compound information or None if not found
        """
        # URL-encode the compound name to handle special characters safely
        encoded_name = quote(compound_name)
        search_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_name}/JSON"

        # Retry logic for search request
        for attempt in range(max_retries):
            try:
                # Increased timeout and retry for 503 errors
                search_response = requests.get(
                    search_url, timeout=30
                )  # Increased from 10 to 30 seconds

                if search_response.status_code == 200:
                    search_data = search_response.json()

                    # Extract CID from the response
                    if (
                        "PC_Compounds" in search_data
                        and len(search_data["PC_Compounds"]) > 0
                    ):
                        cid = search_data["PC_Compounds"][0]["id"]["id"]["cid"]

                        # Use the existing fetch_compound_from_pubchem function
                        # Retry logic for fetching compound data
                        for info_attempt in range(max_retries):
                            try:
                                compound_data = fetch_compound_from_pubchem(cid)

                                if compound_data:
                                    # Generate compound ID from cleaned name
                                    clean_name = (
                                        compound_name.lower()
                                        .replace(" ", "")
                                        .replace("-", "")
                                        .replace("_", "")
                                        .replace(",", "")
                                        .replace(";", "")
                                    )
                                    compound_id = f"compound_{clean_name}"

                                    # Update compound_data with compoundID
                                    compound_data["compoundID"] = compound_id

                                    # Ensure sigma_profile is set (not sigman_profile)
                                    if "sigman_profile" in compound_data:
                                        compound_data["sigma_profile"] = (
                                            compound_data.pop("sigman_profile")
                                        )
                                    elif "sigma_profile" not in compound_data:
                                        compound_data["sigma_profile"] = None

                                    # Ensure SELFIE is set
                                    if "SELFIE" not in compound_data:
                                        compound_data["SELFIE"] = None

                                    return compound_data
                                else:
                                    # If fetch failed, retry
                                    if info_attempt < max_retries - 1:
                                        time.sleep(retry_delay * (info_attempt + 1))
                                        continue
                                    else:
                                        print(
                                            f"Warning: Failed to fetch compound data for '{compound_name}' (CID: {cid}) after {max_retries} attempts"
                                        )
                                        return None

                            except Exception as e:
                                if info_attempt < max_retries - 1:
                                    print(
                                        f"Error fetching compound data for '{compound_name}' (CID: {cid}), retrying ({info_attempt + 1}/{max_retries})...: {e}"
                                    )
                                    time.sleep(retry_delay * (info_attempt + 1))
                                    continue
                                else:
                                    print(
                                        f"Error fetching compound data for '{compound_name}' from PubChem: {e}"
                                    )
                                    return None

                        return None  # If all info attempts failed

                elif search_response.status_code == 404:
                    print(f"Warning: Compound '{compound_name}' not found in PubChem")
                    return None
                elif search_response.status_code == 503:
                    # Service unavailable - retry with exponential backoff
                    if attempt < max_retries - 1:
                        delay = retry_delay * (2**attempt)  # Exponential backoff
                        print(
                            f"PubChem service unavailable (503) for '{compound_name}', retrying in {delay:.1f}s ({attempt + 1}/{max_retries})..."
                        )
                        time.sleep(delay)
                        continue
                    else:
                        print(
                            f"Warning: PubChem search failed for '{compound_name}' after {max_retries} attempts (status: 503)"
                        )
                        return None
                else:
                    print(
                        f"Warning: PubChem search failed for '{compound_name}' (status: {search_response.status_code})"
                    )
                    return None

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    delay = retry_delay * (2**attempt)  # Exponential backoff
                    print(
                        f"Timeout fetching '{compound_name}', retrying in {delay:.1f}s ({attempt + 1}/{max_retries})..."
                    )
                    time.sleep(delay)
                    continue
                else:
                    print(
                        f"Error: Timeout fetching compound '{compound_name}' from PubChem after {max_retries} attempts"
                    )
                    return None
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    delay = retry_delay * (2**attempt)
                    print(
                        f"Request error for '{compound_name}', retrying in {delay:.1f}s ({attempt + 1}/{max_retries})...: {e}"
                    )
                    time.sleep(delay)
                    continue
                else:
                    print(
                        f"Error fetching compound '{compound_name}' from PubChem: {e}"
                    )
                    return None
            except Exception as e:
                print(
                    f"Unexpected error fetching compound '{compound_name}' from PubChem: {e}"
                )
                return None

        return None

    def _create_fluid_from_rows(
        self,
        compounds_list: List[str],
        rows: List[Dict[str, str]],
        is_new_format: bool = False,
        storage_key: Optional[str] = None,
    ) -> Optional[Fluid]:
        """
        Create a Fluid object from rows. Multiple properties can be in the same fluid
        (as separate measurements).

        Args:
            compounds_list: List of compound names
            rows: List of CSV row dictionaries (can contain multiple property types)
            is_new_format: If True, use new CSV format (with Property Name, Time parameter, etc.)
            storage_key: Storage condition key (for new format). None means no storage condition.

        Returns:
            Fluid object or None if no valid data
        """
        if not rows:
            return None

        # Collect all unique properties from rows
        property_objects = {}
        property_columns = {}

        if is_new_format:
            # New format: collect all Property Names
            for row in rows:
                property_name = row.get("Property Name", "").strip()
                property_val = row.get("Property", "").strip()

                # Skip rows with invalid property values
                if not property_val or property_val.lower() in [
                    "",
                    "nan",
                    "none",
                    "crystallized",
                ]:
                    continue

                # Try to convert to float
                try:
                    float(property_val.replace(",", "."))
                except (ValueError, TypeError):
                    continue

                if property_name and property_name.lower() not in property_objects:
                    property_type = property_name.lower()
                    property_id = property_type
                    property_obj = Property(
                        propertyID=property_id,
                        properties=self._map_property_type(property_type),
                    )

                    # Set unit based on property type
                    if property_type == "viscosity":
                        property_obj.unit = UnitDefinition(
                            unitID="mPa·s",
                            name="milliPascal second",
                            base_units=[],
                        )
                    elif property_type == "kinematic_viscosity":
                        property_obj.unit = UnitDefinition(
                            unitID="m2/s",
                            name="square meter per second",
                            base_units=[],
                        )
                    elif property_type == "density":
                        property_obj.unit = UnitDefinition(
                            unitID="kg/m3",
                            name="kilogram per cubic meter",
                            base_units=[],
                        )
                    elif property_type == "polarity":
                        property_obj.unit = UnitDefinition(
                            unitID="1",
                            name="dimensionless",
                            base_units=[],
                        )

                    property_objects[property_type] = property_obj
                    property_columns[property_type] = "Property"
        else:
            # Old format: check for Viscosity and Density columns
            for row in rows:
                # Check for viscosity
                viscosity_val = row.get("Viscosity, cP", "").strip()
                if viscosity_val and viscosity_val.lower() not in ["", "nan", "none"]:
                    try:
                        float(viscosity_val.replace(",", "."))
                        if "viscosity" not in property_objects:
                            property_obj = Property(
                                propertyID="viscosity",
                                properties=Properties.VISCOSITY,
                            )
                            property_obj.unit = UnitDefinition(
                                unitID="mPa·s",
                                name="milliPascal second",
                                base_units=[],
                            )
                            property_objects["viscosity"] = property_obj
                            property_columns["viscosity"] = "Viscosity, cP"
                    except (ValueError, TypeError):
                        pass

                # Check for density
                density_val = row.get("Density, g/cm^3", "").strip()
                if density_val and density_val.lower() not in ["", "nan", "none"]:
                    try:
                        float(density_val.replace(",", "."))
                        if "density" not in property_objects:
                            property_obj = Property(
                                propertyID="density",
                                properties=Properties.DENSITY,
                            )
                            property_obj.unit = UnitDefinition(
                                unitID="kg/m3",
                                name="kilogram per cubic meter",
                                base_units=[],
                            )
                            property_objects["density"] = property_obj
                            property_columns["density"] = "Density, g/cm^3"
                    except (ValueError, TypeError):
                        pass

        if not property_objects:
            return None

        # Create parameter definitions
        all_parameters = []

        if is_new_format:
            # New format: Time parameter instead of Temperature
            time_param = Parameter(
                parameterID="parameter_time",
                parameter=Parameters.TIME,
                unit=self._make_unit("days"),  # Time in days
                associated_compounds=[],
            )
            all_parameters.append(time_param)
        else:
            # Old format: Temperature parameter
            temp_param = Parameter(
                parameterID="parameter_temperature",
                parameter=Parameters.TEMPERATURE,
                unit=self._make_unit("K"),
                associated_compounds=[],
            )
            all_parameters.append(temp_param)

        # Mole fraction parameters (one per compound)
        mole_fraction_params = []
        for i, compound_name in enumerate(compounds_list):
            # Clean compound name for parameter ID
            clean_name = (
                compound_name.lower()
                .replace(" ", "")
                .replace("-", "")
                .replace("_", "")
                .replace(",", "")
                .replace(";", "")
            )
            param_id = f"parameter_mole_fraction_{clean_name}"

            # Use actual compound ID (from compounds_list, which already has the correct IDs)
            compound_id = (
                compound_name  # This is already the compound ID from fluid_compounds
            )

            mole_fraction_param = Parameter(
                parameterID=param_id,
                parameter=Parameters.MOLE_FRACTION,
                unit=self._make_unit("1"),
                associated_compounds=[compound_id],
            )
            mole_fraction_params.append(mole_fraction_param)

        # Combine all parameters
        all_parameters.extend(mole_fraction_params)

        # Generate UUID for fluidID
        fluid_uuid = str(uuid.uuid4())

        # Set storage condition for fluid level from storage_key
        # All rows in this group have the same storage condition (since it's part of the key)
        fluid_storage = None
        if is_new_format and storage_key:
            storage_condition = self._map_storage_condition(storage_key)
            if storage_condition:
                fluid_storage = Storage(storage_condition=storage_condition)

        # Create fluid with UUID as fluidID and all properties
        fluid = Fluid(
            fluidID=[fluid_uuid],
            compounds=compounds_list,
            property=list(property_objects.values()),  # All properties in this fluid
            parameter=all_parameters,
            measurement=[],
            storage=fluid_storage,
        )

        # Create measurements from rows
        # Each row becomes a measurement with the appropriate property value
        for row_idx, row in enumerate(rows):
            # Determine which property this row belongs to
            property_type = None
            property_column = None

            if is_new_format:
                property_name = row.get("Property Name", "").strip()
                if property_name:
                    property_type = property_name.lower()
                    property_column = property_columns.get(property_type)
            else:
                # Old format: check which property column has a value
                viscosity_val = row.get("Viscosity, cP", "").strip()
                density_val = row.get("Density, g/cm^3", "").strip()

                if viscosity_val and viscosity_val.lower() not in ["", "nan", "none"]:
                    try:
                        float(viscosity_val.replace(",", "."))
                        property_type = "viscosity"
                        property_column = "Viscosity, cP"
                    except (ValueError, TypeError):
                        pass

                if (
                    not property_type
                    and density_val
                    and density_val.lower()
                    not in [
                        "",
                        "nan",
                        "none",
                    ]
                ):
                    try:
                        float(density_val.replace(",", "."))
                        property_type = "density"
                        property_column = "Density, g/cm^3"
                    except (ValueError, TypeError):
                        pass

            if not property_type or not property_column:
                continue

            # Extract property value (handle comma as decimal separator)
            prop_value_str = row.get(property_column, "").strip()
            if not prop_value_str or prop_value_str.lower() in [
                "",
                "nan",
                "none",
                "crystallized",
            ]:
                continue

            try:
                prop_value = float(prop_value_str.replace(",", "."))
            except (ValueError, TypeError):
                continue

            # Extract uncertainty (Standard Deviation Viscosity or similar)
            uncertainty = None
            if is_new_format:
                uncertainty_str = row.get("Standard Deviation Viscosity", "").strip()
                if uncertainty_str and uncertainty_str.lower() not in [
                    "",
                    "nan",
                    "none",
                ]:
                    try:
                        uncertainty = float(uncertainty_str.replace(",", "."))
                    except (ValueError, TypeError):
                        pass

            # Extract temperature or time parameter
            temperature = None
            time_value = None
            if is_new_format:
                # New format: Parameter column contains the time value (in days)
                # Type column indicates it's "Time"
                time_str = row.get("Parameter", "").strip()
                param_type = row.get("Type", "").strip()
                if (
                    time_str
                    and time_str.lower() not in ["", "nan", "none"]
                    and param_type.lower() == "time"
                ):
                    try:
                        time_value = float(time_str.replace(",", "."))
                    except (ValueError, TypeError):
                        pass
            else:
                # Old format: Temperature
                temp_str = row.get("Temperature, K", "").strip()
                if temp_str and temp_str.lower() not in ["", "nan", "none"]:
                    try:
                        temperature = float(temp_str.replace(",", "."))
                    except (ValueError, TypeError):
                        pass

            # Extract mole fractions
            mole_fractions = {}
            if is_new_format:
                # New format: Molar Fraction 1, Molar Fraction 2, Molar Fraction 3
                for i in range(1, len(compounds_list) + 1):
                    x_col = f"Molar Fraction {i}"
                    x_str = row.get(x_col, "").strip()
                    if x_str and x_str.lower() not in ["", "nan", "none"]:
                        try:
                            mole_fractions[i] = float(x_str.replace(",", "."))
                        except (ValueError, TypeError):
                            pass
            else:
                # Old format: X#1 (molar fraction), etc.
                for i in range(1, len(compounds_list) + 1):
                    x_col = f"X#{i} (molar fraction)"
                    x_str = row.get(x_col, "").strip()
                    if x_str and x_str.lower() not in ["", "nan", "none"]:
                        try:
                            mole_fractions[i] = float(x_str.replace(",", "."))
                        except (ValueError, TypeError):
                            pass

            # Extract DOI (not in new format, but check anyway)
            doi = row.get("Reference (DOI)", "").strip()
            if not doi or doi.lower() in ["", "nan", "none"]:
                doi = None

            # Extract Storage information (new format)
            # Since storage is now part of the grouping key, all rows in this fluid have the same storage
            # So we only need to add comment to method_description
            storage_info = None
            if is_new_format:
                comment = row.get("Comment", "").strip()
                if comment:
                    storage_info = f"Comment: {comment}"

            # Create parameter values
            parameter_values = []

            # Temperature or Time parameter value
            if is_new_format and time_value is not None:
                parameter_values.append(
                    ParameterValue(
                        parameterID="parameter_time",
                        paramValue=time_value,
                        uncertainty=None,
                    )
                )
            elif not is_new_format and temperature is not None:
                parameter_values.append(
                    ParameterValue(
                        parameterID="parameter_temperature",
                        paramValue=temperature,
                        uncertainty=None,
                    )
                )

            # Mole fraction parameter values
            for i, compound_name in enumerate(compounds_list):
                comp_idx = i + 1
                if comp_idx in mole_fractions:
                    clean_name = (
                        compound_name.lower()
                        .replace(" ", "")
                        .replace("-", "")
                        .replace("_", "")
                        .replace(",", "")
                        .replace(";", "")
                    )
                    param_id = f"parameter_mole_fraction_{clean_name}"
                    parameter_values.append(
                        ParameterValue(
                            parameterID=param_id,
                            paramValue=mole_fractions[comp_idx],
                            uncertainty=None,
                        )
                    )

            # Create property value with uncertainty
            property_value = PropertyValue(
                propertyID=property_type,
                propValue=prop_value,
                uncertainty=uncertainty,
            )

            # Create method description
            method_description = "Experimental measurement"
            if storage_info:
                method_description += f" ({storage_info})"

            # Create measurement with UUID
            measurement = Measurement(
                measurement_id=f"meas_{property_type}_{uuid.uuid4()}",
                source_doi=doi,
                propertyValue=[property_value],
                parameterValue=parameter_values,
                method=Method.MEASURED,
                method_description=method_description,
            )

            fluid.measurement.append(measurement)

        return fluid if fluid.measurement else None

    def _map_property_type(self, property_type: str) -> Properties:
        """Map property type string to Properties enum."""
        prop_map = {
            "viscosity": Properties.VISCOSITY,
            "kinematic_viscosity": Properties.KINEMATIC_VISCOSITY,
            "density": Properties.DENSITY,
            "thermal_conductivity": Properties.THERMAL_CONDUCTIVITY,
            "polarity": Properties.POLARITY,
        }
        return prop_map.get(property_type.lower(), Properties.VISCOSITY)

    def _map_parameter_type(self, parameter_type: str) -> Parameters:
        """Map parameter type string to Parameters enum."""
        param_map = {
            "temperature": Parameters.TEMPERATURE,
            "time": Parameters.TIME,
            "mole_fraction": Parameters.MOLE_FRACTION,
            "pressure": Parameters.PRESSURE,
        }
        return param_map.get(parameter_type.lower(), Parameters.TEMPERATURE)

    def _map_storage_condition(self, storage_str: str) -> Optional[StorageCondition]:
        """Map storage condition string from CSV to StorageCondition enum.

        Args:
            storage_str: Storage condition string from CSV (e.g., "closed", "fridge", "open", "none")

        Returns:
            StorageCondition enum value or None if not mappable
        """
        storage_lower = storage_str.lower().strip()
        storage_map = {
            "closed": StorageCondition.CLOSED,
            "fridge": StorageCondition.FRIDGE,
            "open": StorageCondition.OPEN,
            "fresh": StorageCondition.FRESH,
            "none": None,  # "none" means no specific storage condition
        }
        return storage_map.get(storage_lower)

    def _make_unit(self, unit_str: str) -> UnitDefinition:
        """Create a UnitDefinition from a unit string for parameters.
        Parameters use units with base_units that have kind=null, exponent=null."""
        # Map common unit strings to unit definitions matching example structure
        unit_map = {
            "K": UnitDefinition(
                unitID="K",
                name="kelvin",
                base_units=[
                    BaseUnit(
                        kind=None,
                        exponent=None,
                        multiplier=1.0,
                        scale=0.0,
                    )
                ],
            ),
            "1": UnitDefinition(
                unitID="1",
                name="dimensionless",
                base_units=[
                    BaseUnit(
                        kind=None,
                        exponent=None,
                        multiplier=1.0,
                        scale=0.0,
                    )
                ],
            ),
            "days": UnitDefinition(
                unitID="days",
                name="days",
                base_units=[
                    BaseUnit(
                        kind=None,
                        exponent=None,
                        multiplier=1.0,
                        scale=0.0,
                    )
                ],
            ),
        }

        if unit_str in unit_map:
            return unit_map[unit_str]

        # Default unit definition for parameters
        return UnitDefinition(
            unitID=unit_str,
            name=unit_str,
            base_units=[
                BaseUnit(
                    kind=None,
                    exponent=None,
                    multiplier=1.0,
                    scale=0.0,
                )
            ],
        )
