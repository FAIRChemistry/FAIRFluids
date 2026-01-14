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
from collections import defaultdict
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
)


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
        Create FAIRFluids documents from CSV file in joined_viscosity_density.csv format.

        Each unique compound combination (Component#1, Component#2, Component#3) creates
        a separate document. Within each document, separate fluids are created for viscosity
        and density (each fluid has only one property).

        Args:
            csv_path: Path to CSV file
            document: Optional template document (for metadata like citation)
            output_dir: Optional directory to save JSON files
            fetch_from_pubchem: If True, fetch compound information from PubChem

        Returns:
            List of FAIRFluidsDocument objects (one per compound combination)
        """
        # Read CSV and group by compound combinations
        compound_combinations = defaultdict(list)

        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Extract compounds (Component#1, Component#2, Component#3)
                compounds = []
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

            # Group rows by property (viscosity and density)
            viscosity_rows = []
            density_rows = []

            for row in rows:
                # Check if viscosity data exists
                viscosity_val = row.get("Viscosity, cP", "").strip()
                if viscosity_val and viscosity_val.lower() not in ["", "nan", "none"]:
                    try:
                        float(viscosity_val)
                        viscosity_rows.append(row)
                    except (ValueError, TypeError):
                        pass

                # Check if density data exists
                density_val = row.get("Density, g/cm^3", "").strip()
                if density_val and density_val.lower() not in ["", "nan", "none"]:
                    try:
                        float(density_val)
                        density_rows.append(row)
                    except (ValueError, TypeError):
                        pass

            # Map compound names to IDs (always use the mapped IDs)
            fluid_compounds = [
                compound_name_to_id.get(name, name.strip().title())
                for name in compounds_list
            ]

            # Create fluid for viscosity
            if viscosity_rows:
                viscosity_fluid = self._create_fluid_from_rows(
                    fluid_compounds, viscosity_rows, "viscosity", "Viscosity, cP"
                )
                if viscosity_fluid:
                    doc.fluid.append(viscosity_fluid)

            # Create fluid for density
            if density_rows:
                density_fluid = self._create_fluid_from_rows(
                    fluid_compounds, density_rows, "density", "Density, g/cm^3"
                )
                if density_fluid:
                    doc.fluid.append(density_fluid)

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

                        # Now fetch detailed information using the CID
                        # Note: PubChem returns 'SMILES' not 'CanonicalSMILES', and 'IsomericSMILES' may not be available
                        info_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/IUPACName,MolecularFormula,MolecularWeight,SMILES,InChI,InChIKey,Title/JSON"

                        # Retry logic for info request
                        for info_attempt in range(max_retries):
                            try:
                                info_response = requests.get(info_url, timeout=30)

                                if info_response.status_code == 200:
                                    info_data = info_response.json()
                                    if (
                                        "PropertyTable" in info_data
                                        and "Properties" in info_data["PropertyTable"]
                                        and len(
                                            info_data["PropertyTable"]["Properties"]
                                        )
                                        > 0
                                    ):
                                        prop_data = info_data["PropertyTable"][
                                            "Properties"
                                        ][0]

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

                                        return {
                                            "compoundID": compound_id,
                                            "pubChemID": cid,
                                            "commonName": prop_data.get(
                                                "Title", compound_name
                                            ),
                                            "name_IUPAC": prop_data.get("IUPACName"),
                                            "smiles_code": prop_data.get(
                                                "SMILES"
                                            ),  # PubChem returns 'SMILES' not 'CanonicalSMILES'
                                            "molar_weigth": prop_data.get(
                                                "MolecularWeight"
                                            ),
                                            "standard_InChI": prop_data.get("InChI"),
                                            "standard_InChI_key": prop_data.get(
                                                "InChIKey"
                                            ),
                                            "SELFIE": None,
                                            "sigma_profile": None,
                                        }
                                elif info_response.status_code == 503:
                                    # Service unavailable - retry with delay
                                    if info_attempt < max_retries - 1:
                                        time.sleep(retry_delay * (info_attempt + 1))
                                        continue
                                    else:
                                        print(
                                            f"Warning: PubChem info request failed for '{compound_name}' after {max_retries} attempts (status: 503)"
                                        )
                                        return None
                                else:
                                    # Other error - don't retry
                                    print(
                                        f"Warning: PubChem info request failed for '{compound_name}' (status: {info_response.status_code})"
                                    )
                                    return None

                            except requests.exceptions.Timeout:
                                if info_attempt < max_retries - 1:
                                    print(
                                        f"Timeout fetching info for '{compound_name}', retrying ({info_attempt + 1}/{max_retries})..."
                                    )
                                    time.sleep(retry_delay * (info_attempt + 1))
                                    continue
                                else:
                                    print(
                                        f"Error: Timeout fetching compound info for '{compound_name}' after {max_retries} attempts"
                                    )
                                    return None
                            except requests.exceptions.RequestException as e:
                                if info_attempt < max_retries - 1:
                                    print(
                                        f"Request error for '{compound_name}', retrying ({info_attempt + 1}/{max_retries})...: {e}"
                                    )
                                    time.sleep(retry_delay * (info_attempt + 1))
                                    continue
                                else:
                                    print(
                                        f"Error fetching compound info for '{compound_name}' from PubChem: {e}"
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
        property_type: str,
        property_column: str,
    ) -> Optional[Fluid]:
        """
        Create a Fluid object from rows with a specific property type.

        Args:
            compounds_list: List of compound names
            rows: List of CSV row dictionaries
            property_type: Property type ("viscosity" or "density")
            property_column: Column name for property value ("Viscosity, cP" or "Density, g/cm^3")

        Returns:
            Fluid object or None if no valid data
        """
        if not rows:
            return None

        # Create property object
        property_id = property_type
        property_obj = Property(
            propertyID=property_id,
            properties=self._map_property_type(property_type),
        )

        # Set unit based on property type
        # Properties use simple units with empty base_units
        if property_type.lower() == "viscosity":
            property_obj.unit = UnitDefinition(
                unitID="mPa·s",
                name="milliPascal second",
                base_units=[],
            )
        elif property_type.lower() == "kinematic_viscosity":
            property_obj.unit = UnitDefinition(
                unitID="m2/s",
                name="square meter per second",
                base_units=[],
            )
        elif property_type.lower() == "density":
            property_obj.unit = UnitDefinition(
                unitID="kg/m3",
                name="kilogram per cubic meter",
                base_units=[],
            )

        # Create parameter definitions
        # Temperature parameter (always present)
        temp_param = Parameter(
            parameterID="parameter_temperature",
            parameter=Parameters.TEMPERATURE,
            unit=self._make_unit("K"),
            associated_compounds=[],
        )

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
        all_parameters = [temp_param] + mole_fraction_params

        # Generate UUID for fluidID
        fluid_uuid = str(uuid.uuid4())

        # Create fluid with UUID as fluidID
        fluid = Fluid(
            fluidID=[fluid_uuid],
            compounds=compounds_list,
            property=[property_obj],
            parameter=all_parameters,
            measurement=[],
        )

        # Create measurements from rows
        for row_idx, row in enumerate(rows):
            # Extract property value
            prop_value_str = row.get(property_column, "").strip()
            if not prop_value_str or prop_value_str.lower() in ["", "nan", "none"]:
                continue

            try:
                prop_value = float(prop_value_str)
            except (ValueError, TypeError):
                continue

            # Extract temperature
            temp_str = row.get("Temperature, K", "").strip()
            temperature = None
            if temp_str and temp_str.lower() not in ["", "nan", "none"]:
                try:
                    temperature = float(temp_str)
                except (ValueError, TypeError):
                    pass

            # Extract mole fractions
            mole_fractions = {}
            for i in range(1, len(compounds_list) + 1):
                x_col = f"X#{i} (molar fraction)"
                x_str = row.get(x_col, "").strip()
                if x_str and x_str.lower() not in ["", "nan", "none"]:
                    try:
                        mole_fractions[i] = float(x_str)
                    except (ValueError, TypeError):
                        pass

            # Extract DOI
            doi = row.get("Reference (DOI)", "").strip()
            if not doi or doi.lower() in ["", "nan", "none"]:
                doi = None

            # Create parameter values
            parameter_values = []

            # Temperature parameter value
            if temperature is not None:
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

            # Create property value
            property_value = PropertyValue(
                propertyID=property_id,
                propValue=prop_value,
                uncertainty=None,
            )

            # Create measurement with UUID
            measurement = Measurement(
                measurement_id=f"meas_{property_id}_{uuid.uuid4()}",
                source_doi=doi,
                propertyValue=[property_value],
                parameterValue=parameter_values,
                method=Method.MEASURED,
                method_description="Experimental measurement",
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
        }
        return prop_map.get(property_type.lower(), Properties.VISCOSITY)

    def _map_parameter_type(self, parameter_type: str) -> Parameters:
        """Map parameter type string to Parameters enum."""
        param_map = {
            "temperature": Parameters.TEMPERATURE,
            "mole_fraction": Parameters.MOLE_FRACTION,
            "pressure": Parameters.PRESSURE,
        }
        return param_map.get(parameter_type.lower(), Parameters.TEMPERATURE)

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
