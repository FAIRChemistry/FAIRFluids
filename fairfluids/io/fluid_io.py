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
import requests
import time
import warnings
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from collections import defaultdict, Counter
from urllib.parse import quote
from fairfluids.io.pubchem import fetch_compound_from_pubchem
from fairfluids.io.thermoml_to_fairfluids.fairfluids_builder import _clean_doi
from fairfluids.io.thermoml_to_fairfluids.id_registry import IDRegistry
from fairfluids.io.thermoml_to_fairfluids.mappers.unit_mapper import UnitMapper
from fairfluids.core.lib import (
    Fluid,
    Property,
    Parameter,
    Measurement,
    Sample,
    PropertyValue,
    ParameterValue,
    Method,
    FAIRFluidsDocument,
    FittedModel,
    Properties,
    Parameters,
    UnitDefinition,
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
        units: Optional[Dict[str, str]] = None,
        uncertainty_units: Optional[Dict[str, str]] = None,
    ) -> List[FAIRFluidsDocument]:
        """
        Backward-compatible entrypoint. Accepts CSV and XLSX paths.
        """
        return self.data_from_spreadsheet(
            spreadsheet_path=csv_path,
            document=document,
            output_dir=output_dir,
            fetch_from_pubchem=fetch_from_pubchem,
            units=units,
            uncertainty_units=uncertainty_units,
        )

    def data_from_spreadsheet(
        self,
        spreadsheet_path: str,
        document: Optional[FAIRFluidsDocument] = None,
        output_dir: Optional[str] = None,
        fetch_from_pubchem: bool = False,
        units: Optional[Dict[str, str]] = None,
        uncertainty_units: Optional[Dict[str, str]] = None,
    ) -> List[FAIRFluidsDocument]:
        """
        Create FAIRFluids documents from CSV file.

        Supports the structured CSV format with:
        - Compound i / Molar Fraction i columns
        - mandatory temperature and pressure columns (+ units)
        - optional multi-property blocks per row (e.g. viscosity_value, density_value)

        Each unique compound combination creates a separate document. Within each document,
        separate fluids are created for each composition group.

        Args:
            csv_path: Path to CSV file
            document: Optional template document (for metadata like citation)
            output_dir: Optional directory to save JSON files
            fetch_from_pubchem: If True, fetch compound information from PubChem
            units: Optional global input units, e.g.
                {"temperature": "C", "pressure": "bar", "viscosity": "cP"}
            uncertainty_units: Optional global uncertainty units per quantity, e.g.
                {"temperature": "K", "pressure": "bar", "viscosity": "cP"}

        Returns:
            List of FAIRFluidsDocument objects (one per compound combination)
        """
        # The workflow is expected to predefine the citation block before
        # feeding data; warn (do not raise) if it is missing.
        if document is None or document.citation is None:
            warnings.warn(
                "No citation defined. Pass a `document` whose `citation` block is "
                "predefined before converting so the FAIRFluids document is fully "
                "attributed.",
                UserWarning,
                stacklevel=2,
            )

        # Read CSV/XLSX rows
        units = self._normalize_global_unit_map(units)
        uncertainty_units = self._normalize_global_unit_map(uncertainty_units)

        input_path = Path(spreadsheet_path)
        rows_data = self._read_tabular_rows(input_path)

        # Group rows by compound combinations
        compound_combinations = defaultdict(list)
        for row in rows_data:
            compounds = self._extract_compounds(row)

            if not compounds:
                continue  # Skip rows with no compounds

            # Create key for grouping (tuple of compound names)
            compound_key = tuple(compounds)
            compound_combinations[compound_key].append(row)

        print(f"Found {len(compound_combinations)} unique compound combinations")

        # Fetch compound data from PubChem if requested
        compound_data_cache = {}
        if fetch_from_pubchem:
            explicit_pubchem_ids: Dict[str, int] = {}
            for compound_key, rows in compound_combinations.items():
                for row in rows:
                    pubchem_ids = self._extract_pubchem_ids(row, len(compound_key))
                    for idx, compound_name in enumerate(compound_key):
                        cid = pubchem_ids[idx]
                        if (
                            cid is not None
                            and compound_name not in explicit_pubchem_ids
                        ):
                            explicit_pubchem_ids[compound_name] = cid

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
                compound_data = None
                explicit_cid = explicit_pubchem_ids.get(compound_name)
                if explicit_cid is not None:
                    compound_data = fetch_compound_from_pubchem(explicit_cid)
                    if compound_data:
                        compound_data["pubChemID"] = explicit_cid
                if compound_data is None:
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

            # One ID registry per document so every generated object receives a
            # canonical ``<type>_<n>`` counter ID, restarting per document.
            registry = IDRegistry()

            # Add compounds to document, assigning counter compound IDs. Compound
            # ordering (index) maps onto the CSV composition components.
            compound_name_to_id = {}
            if fetch_from_pubchem:
                for compound_name in compounds_list:
                    compound_id = registry.new_id("compound")
                    compound_name_to_id[compound_name] = compound_id
                    if compound_name in compound_data_cache:
                        compound_data = compound_data_cache[compound_name].copy()
                        compound_data["compoundID"] = compound_id
                        doc.add_to_compound(**compound_data)
                        print(
                            f"  Added compound: {compound_name} -> {compound_id} "
                            f"(CID: {compound_data.get('pubChemID', 'N/A')})"
                        )
                    else:
                        # Not found on PubChem: record the name, leave metadata empty
                        # (do not fabricate identifiers).
                        doc.add_to_compound(
                            compoundID=compound_id,
                            commonName=compound_name.strip(),
                        )
            else:
                for compound_name in compounds_list:
                    compound_id = registry.new_id("compound")
                    compound_name_to_id[compound_name] = compound_id
                    doc.add_to_compound(
                        compoundID=compound_id,
                        commonName=compound_name.strip(),
                    )

            # Group rows by composition: (molar fractions + storage)
            # Multiple properties can be in the same fluid (as separate measurements)
            composition_groups = defaultdict(list)
            skip_missing_required = 0
            skip_no_property = 0
            skip_missing_mole_fraction = 0
            skip_invalid_mole_fraction_sum = 0
            invalid_mole_fraction_compositions: Counter[Tuple[float, ...]] = Counter()

            for row in rows:
                if not self._has_required_row_parameters(row, units):
                    skip_missing_required += 1
                    continue

                if not self._row_has_any_property_value(row, units):
                    skip_no_property += 1
                    continue

                molar_fractions = self._extract_molar_fractions(
                    row, len(compounds_list)
                )
                if molar_fractions is None:
                    skip_missing_mole_fraction += 1
                    continue
                if not self._is_valid_mole_fraction_sum(molar_fractions):
                    skip_invalid_mole_fraction_sum += 1
                    invalid_mole_fraction_compositions[tuple(molar_fractions)] += 1
                    continue

                # Extract storage condition for grouping
                storage_str = row.get("Storage", "").strip().lower()
                storage_key = (
                    None if storage_str in ["", "nan", "none"] else storage_str
                )

                # property_name is NOT part of the key - multiple properties can be in same fluid
                composition_key = (tuple(molar_fractions), storage_key)
                composition_groups[composition_key].append(row)

            if skip_invalid_mole_fraction_sum > 0:
                composition_details = "; ".join(
                    f"{list(fracs)} (sum={sum(fracs):.6g}, {count} row(s))"
                    for fracs, count in sorted(
                        invalid_mole_fraction_compositions.items(),
                        key=lambda item: (-item[1], item[0]),
                    )
                )
                warnings.warn(
                    f"Skipped {skip_invalid_mole_fraction_sum} row(s) for compound "
                    f"combination {list(compounds_list)!r}: molar fractions must sum to "
                    f"1 (tolerance 1e-8). No fluid is created for these compositions. "
                    f"Invalid value(s): {composition_details}.",
                    UserWarning,
                    stacklevel=2,
                )

            # Map compound names to IDs (always use the mapped IDs)
            fluid_compounds = [
                compound_name_to_id.get(name, name.strip().title())
                for name in compounds_list
            ]

            # Create fluid for each composition (molar fractions + storage)
            # Each fluid can contain multiple properties (as separate measurements)
            for composition_key, composition_rows in composition_groups.items():
                if composition_rows:
                    # New format: (molar_fractions_tuple, storage_key)
                    _, storage_key = composition_key

                    fluid = self._create_fluid_from_rows(
                        fluid_compounds,
                        composition_rows,
                        True,
                        units=units,
                        uncertainty_units=uncertainty_units,
                        registry=registry,
                    )
                    if fluid:
                        doc.fluid.append(fluid)

            if not doc.fluid:
                print(
                    "No fluids created for compound combination "
                    f"{compound_key}. Skipped rows -> "
                    f"missing_required(T): {skip_missing_required}, "
                    f"no_property: {skip_no_property}, "
                    f"missing_mole_fraction: {skip_missing_mole_fraction}, "
                    f"invalid_mole_fraction_sum: {skip_invalid_mole_fraction_sum}"
                )

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

    def create_datasheet(
        self,
        output_path: str,
        file_format: str = "csv",
        properties: Optional[List[str]] = None,
        n_compounds: int = 2,
        parameters: Optional[List[str]] = None,
        n_rows: int = 25,
    ) -> str:
        """
        Create a parser-compatible structured datasheet template.

        The resulting file is compatible with ``data_from_csv`` and includes:
        - dynamic compound columns (Compound i / Molar Fraction i)
        - required base parameters (temperature + pressure)
        - property blocks with value/unit/uncertainty fields
        - optional extra parameter blocks with uncertainty fields

        Args:
            output_path: Full output file path.
            file_format: "csv" or "xlsx".
            properties: Property names (supported: viscosity, density, conductivity).
            n_compounds: Number of compounds/components.
            parameters: Extra parameter names beyond required base parameters.
            n_rows: Number of empty template rows.

        Returns:
            The path to the written datasheet file.
        """
        if n_compounds < 1:
            raise ValueError("n_compounds must be >= 1")

        file_format = file_format.strip().lower()
        if file_format not in {"csv", "xlsx"}:
            raise ValueError("file_format must be either 'csv' or 'xlsx'")

        normalized_properties = self._normalize_property_list(properties)
        normalized_parameters = self._normalize_parameter_list(parameters)

        headers: List[str] = []
        for i in range(1, n_compounds + 1):
            headers.extend([f"Compound {i}", f"pubchemID {i}", f"Molar Fraction {i}"])

        # Required core parameters for parser compatibility
        headers.extend(
            [
                "temperature_value",
                "temperature_unit",
                "temperature_uncertainty",
                "temperature_uncertainty_unit",
                "pressure_value",
                "pressure_unit",
                "pressure_uncertainty",
                "pressure_uncertainty_unit",
            ]
        )

        # Optional parameter extension blocks
        for parameter in normalized_parameters:
            headers.extend(
                [
                    f"{parameter}_value",
                    f"{parameter}_unit",
                    f"{parameter}_uncertainty",
                    f"{parameter}_uncertainty_unit",
                ]
            )

        # Property blocks (multiple properties per row possible)
        for property_name in normalized_properties:
            headers.extend(
                [
                    f"{property_name}_value",
                    f"{property_name}_unit",
                    f"{property_name}_uncertainty",
                    f"{property_name}_uncertainty_unit",
                ]
            )

        headers.extend(["Storage", "Comment", "source_doi"])

        # Empty template rows
        rows = [{header: "" for header in headers} for _ in range(max(1, n_rows))]

        # Add hints in first row to reduce formatting errors
        rows[0]["temperature_unit"] = "K"
        rows[0]["pressure_unit"] = "kPa"
        for property_name in normalized_properties:
            rows[0][f"{property_name}_unit"] = self._default_property_input_unit(
                property_name
            )

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if file_format == "csv":
            with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                writer.writerows(rows)
            return str(output_file)

        # XLSX
        try:
            import pandas as pd
        except ImportError as exc:
            raise ImportError(
                "Creating .xlsx templates requires pandas (and an excel engine like openpyxl). "
                "Use file_format='csv' or install the missing dependency."
            ) from exc

        df = pd.DataFrame(rows, columns=headers)
        try:
            df.to_excel(output_file, index=False)
        except Exception as exc:
            raise RuntimeError(
                "Failed to write xlsx template. Ensure an Excel writer engine is installed "
                "(e.g., openpyxl)."
            ) from exc
        return str(output_file)

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
        units: Optional[Dict[str, str]] = None,
        uncertainty_units: Optional[Dict[str, str]] = None,
        registry: Optional[IDRegistry] = None,
    ) -> Optional[Fluid]:
        """
        Create a Fluid object from rows. Multiple properties can be in the same fluid
        (as separate measurements).

        Args:
            compounds_list: List of compound IDs (counter IDs, in component order).
            rows: List of CSV row dictionaries (can contain multiple property types)
            is_new_format: Kept for compatibility; structured format is assumed.
            units: Optional global input units (used if unit columns are missing).
            uncertainty_units: Optional global uncertainty units.
            registry: Shared per-document ID registry for counter IDs.

        Returns:
            Fluid object or None if no valid data
        """
        if not rows:
            return None
        if registry is None:
            registry = IDRegistry()

        # One shared Property definition per detected type (counter IDs + enums).
        property_objects: Dict[str, Property] = {}
        supported_properties = self._default_supported_property_aliases()
        for property_type in supported_properties:
            if any(
                self._extract_property_si(
                    row, property_type, units=units, uncertainty_units=uncertainty_units
                )
                is not None
                for row in rows
            ):
                property_objects[property_type] = Property(
                    propertyID=registry.new_id("property"),
                    properties=self._map_property_type(property_type),
                    unit=self._make_property_unit(property_type, registry),
                )

        if not property_objects:
            return None

        # Required parameter definitions: temperature (+ optional pressure) + mole fractions.
        temperature_param = Parameter(
            parameterID=registry.new_id("parameter"),
            parameters=Parameters.TEMPERATURE,
            unit=self._make_unit("K", registry),
            associated_compounds=[],
        )
        all_parameters: List[Parameter] = [temperature_param]

        pressure_param: Optional[Parameter] = None
        has_any_pressure = any(
            self._extract_pressure_kpa(row, units) is not None for row in rows
        )
        if has_any_pressure:
            pressure_param = Parameter(
                parameterID=registry.new_id("parameter"),
                parameters=Parameters.PRESSURE,
                unit=self._make_unit("kPa", registry),
                associated_compounds=[],
            )
            all_parameters.append(pressure_param)

        # Mole fraction parameters (one per compound), keyed by component index.
        mole_fraction_params: Dict[int, Parameter] = {}
        for i, compound_id in enumerate(compounds_list):
            param = Parameter(
                parameterID=registry.new_id("parameter"),
                parameters=Parameters.MOLE_FRACTION,
                unit=self._dimensionless(),
                associated_compounds=[compound_id],
            )
            mole_fraction_params[i] = param
            all_parameters.append(param)

        fluid = Fluid(
            fluidID=[registry.new_id("fluid")],
            compounds=compounds_list,
            property=list(property_objects.values()),
            parameter=all_parameters,
            sample=Sample(
                sample_id=registry.new_id("sample"),
                associated_compounds=compounds_list,
                measurement=[],
            ),
        )

        for row in rows:
            temperature_value = self._extract_temperature_kelvin(row, units)
            pressure_value = self._extract_pressure_kpa(row, units)
            mole_fractions = self._extract_molar_fractions(row, len(compounds_list))

            if (
                temperature_value is None
                or mole_fractions is None
                or not self._is_valid_mole_fraction_sum(mole_fractions)
            ):
                continue

            property_values: List[PropertyValue] = []
            for property_type, property_obj in property_objects.items():
                prop_payload = self._extract_property_si(
                    row,
                    property_type,
                    units=units,
                    uncertainty_units=uncertainty_units,
                )
                if prop_payload is None:
                    continue
                property_values.append(
                    PropertyValue(
                        properties=property_obj.properties,
                        propertyID=property_obj.propertyID,
                        propValue=prop_payload["value"],
                        uncertainty=prop_payload["uncertainty"],
                    )
                )

            if not property_values:
                continue

            parameter_values = [
                ParameterValue(
                    parameters=temperature_param.parameters,
                    parameterID=temperature_param.parameterID,
                    paramValue=temperature_value,
                    uncertainty=None,
                ),
            ]
            if pressure_value is not None and pressure_param is not None:
                parameter_values.append(
                    ParameterValue(
                        parameters=pressure_param.parameters,
                        parameterID=pressure_param.parameterID,
                        paramValue=pressure_value,
                        uncertainty=None,
                    )
                )

            for i in range(len(compounds_list)):
                param = mole_fraction_params[i]
                parameter_values.append(
                    ParameterValue(
                        parameters=param.parameters,
                        parameterID=param.parameterID,
                        paramValue=mole_fractions[i],
                        uncertainty=None,
                    )
                )

            doi = (
                row.get("source_doi", "").strip()
                or row.get("Reference (DOI)", "").strip()
            )
            doi = _clean_doi(doi) or None

            comment = row.get("Comment", "").strip()
            method_description = "Experimental measurement"
            if comment:
                method_description += f" (Comment: {comment})"

            measurement = Measurement(
                measurement_id=registry.new_id("measurement"),
                source_doi=doi,
                propertyValue=property_values,
                parameterValue=parameter_values,
                method=Method.MEASURED,
                method_description=method_description,
            )
            fluid.sample.measurement.append(measurement)

        return fluid if fluid.sample and fluid.sample.measurement else None

    def _map_property_type(self, property_type: str) -> Properties:
        """Map property type string to Properties enum."""
        _, enum_prop = self._resolve_property_alias_and_enum(property_type)
        return enum_prop

    def _normalize_property_list(self, properties: Optional[List[str]]) -> List[str]:
        supported = self._default_supported_property_aliases()
        if not properties:
            return list(supported)
        normalized = []
        for prop in properties:
            alias, _ = self._resolve_property_alias_and_enum(prop)
            if alias not in supported:
                raise ValueError(
                    f"Unsupported property '{prop}'. Supported aliases: {sorted(supported)}"
                )
            if alias not in normalized:
                normalized.append(alias)
        return normalized

    def _normalize_parameter_list(self, parameters: Optional[List[str]]) -> List[str]:
        if not parameters:
            return []
        reserved = {"temperature", "pressure", "molar_fraction"}
        normalized = []
        for parameter in parameters:
            key = str(parameter).strip()
            if not key:
                continue
            enum_parameter = self._resolve_parameter_enum(key)
            canonical = enum_parameter.name.lower()
            if canonical == "mole_fraction":
                canonical = "molar_fraction"
            if canonical in reserved:
                # Core parameters are already included in the template
                continue
            if canonical not in normalized:
                normalized.append(canonical)
        return normalized

    def _default_property_input_unit(self, property_name: str) -> str:
        defaults = {
            "viscosity": "cP",
            "density": "g/cm3",
            "conductivity": "mS/cm",
        }
        return defaults.get(property_name, "")

    def _make_property_unit(
        self, property_type: str, registry: IDRegistry
    ) -> UnitDefinition:
        """Build a fully-specified canonical-SI unit for a property type."""
        unit_str_map = {
            "viscosity": "Pa*s",
            "density": "kg/m3",
            "conductivity": "S/m",
        }
        unit_str = unit_str_map[property_type]
        return UnitMapper.from_unit_string(
            unit_str, unit_id=registry.new_id("unit")
        )

    def _dimensionless(self) -> UnitDefinition:
        """Return the single canonical dimensionless unit."""
        return UnitMapper.dimensionless()

    def _parse_float(self, raw_value: Any) -> Optional[float]:
        if raw_value is None:
            return None
        value_str = str(raw_value).strip()
        if value_str.lower() in {"", "nan", "none"}:
            return None
        try:
            return float(value_str.replace(",", "."))
        except (ValueError, TypeError):
            return None

    def _normalize_global_unit_map(
        self, unit_map: Optional[Dict[str, str]]
    ) -> Dict[str, str]:
        if not unit_map:
            return {}
        return {str(k).strip().lower(): str(v).strip() for k, v in unit_map.items()}

    def _read_tabular_rows(self, input_path: Path) -> List[Dict[str, str]]:
        """
        Read structured tabular input from CSV or XLSX and return rows as dictionaries.
        """
        suffix = input_path.suffix.lower()
        if suffix in {".xlsx", ".xls"}:
            try:
                import pandas as pd
            except ImportError as exc:
                raise ImportError(
                    "Reading Excel files requires pandas (and an engine like openpyxl)."
                ) from exc

            df = pd.read_excel(input_path)
            df = df.where(pd.notna(df), "")
            return [
                {str(col): str(val).strip() for col, val in row.items()}
                for row in df.to_dict(orient="records")
            ]

        # Default: CSV parsing with automatic delimiter detection
        delimiter = ";"
        with open(input_path, newline="", encoding="utf-8") as csvfile:
            sample = csvfile.read(1024)
            csvfile.seek(0)
            if sample.count(";") > sample.count(","):
                delimiter = ";"
            else:
                delimiter = ","

            reader = csv.DictReader(csvfile, delimiter=delimiter)
            return [
                {
                    str(k): (str(v).strip() if v is not None else "")
                    for k, v in row.items()
                }
                for row in reader
            ]

    def _normalize_unit(self, unit: Any) -> str:
        if unit is None:
            return ""
        normalized = str(unit).strip().replace("·", "*").lower()
        # Accept common spreadsheet/SI spellings (e.g. template hint "Pa.s")
        unit_aliases = {
            "pa.s": "pa*s",
            "pa s": "pa*s",
            "pas": "pa*s",
            "mpa.s": "mpa*s",
            "mpa s": "mpa*s",
        }
        return unit_aliases.get(normalized, normalized)

    def _convert_temperature_to_kelvin(
        self, value: float, unit: str
    ) -> Optional[float]:
        if unit == "k":
            return value
        if unit in {"c", "°c", "degc", "celsius"}:
            return value + 273.15
        return None

    def _convert_pressure_to_kpa(self, value: float, unit: str) -> Optional[float]:
        factors = {
            "pa": 1e-3,
            "kpa": 1.0,
            "mpa": 1e3,
            "bar": 1e2,
        }
        factor = factors.get(unit)
        return None if factor is None else value * factor

    def _convert_property_to_si(
        self, property_type: str, value: float, unit: str
    ) -> Optional[float]:
        if property_type == "viscosity":
            factors = {"pa*s": 1.0, "mpa*s": 1e-3, "cp": 1e-3}
        elif property_type == "density":
            factors = {"kg/m3": 1.0, "g/cm3": 1e3}
        elif property_type == "conductivity":
            factors = {"s/m": 1.0, "ms/cm": 0.1}
        else:
            return None
        factor = factors.get(unit)
        return None if factor is None else value * factor

    def _extract_compounds(self, row: Dict[str, str]) -> List[str]:
        indexed = []
        for key, value in row.items():
            if not key.lower().startswith("compound "):
                continue
            suffix = key.split(" ", 1)[-1].strip()
            if not suffix.isdigit():
                continue
            parsed = str(value).strip()
            if parsed:
                indexed.append((int(suffix), parsed))
        return [name for _, name in sorted(indexed, key=lambda x: x[0])]

    def _extract_molar_fractions(
        self, row: Dict[str, str], n_components: int
    ) -> Optional[List[float]]:
        molar_fractions: List[float] = []
        for i in range(1, n_components + 1):
            value = self._parse_float(row.get(f"Molar Fraction {i}"))
            if value is None:
                return None
            molar_fractions.append(value)
        return molar_fractions

    def _extract_pubchem_ids(
        self, row: Dict[str, str], n_components: int
    ) -> List[Optional[int]]:
        pubchem_ids: List[Optional[int]] = []
        for i in range(1, n_components + 1):
            cid_raw = row.get(f"pubchemID {i}", row.get(f"pubchemID_{i}", ""))
            cid_val = self._parse_float(cid_raw)
            pubchem_ids.append(int(cid_val) if cid_val is not None else None)
        return pubchem_ids

    def _is_valid_mole_fraction_sum(self, molar_fractions: List[float]) -> bool:
        return abs(sum(molar_fractions) - 1.0) <= 1e-8

    def _extract_temperature_kelvin(
        self, row: Dict[str, str], units: Optional[Dict[str, str]] = None
    ) -> Optional[float]:
        value = self._parse_float(row.get("temperature_value"))
        unit = self._normalize_unit(row.get("temperature_unit"))
        if not unit and units:
            unit = self._normalize_unit(units.get("temperature"))
        if value is None or not unit:
            return None
        return self._convert_temperature_to_kelvin(value, unit)

    def _extract_pressure_kpa(
        self, row: Dict[str, str], units: Optional[Dict[str, str]] = None
    ) -> Optional[float]:
        value = self._parse_float(row.get("pressure_value"))
        unit = self._normalize_unit(row.get("pressure_unit"))
        if not unit and units:
            unit = self._normalize_unit(units.get("pressure"))
        if value is None or not unit:
            return None
        return self._convert_pressure_to_kpa(value, unit)

    def _extract_property_si(
        self,
        row: Dict[str, str],
        property_type: str,
        units: Optional[Dict[str, str]] = None,
        uncertainty_units: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, Optional[float]]]:
        value = self._parse_float(row.get(f"{property_type}_value"))
        unit = self._normalize_unit(row.get(f"{property_type}_unit"))
        if not unit and units:
            unit = self._normalize_unit(units.get(property_type))
        if value is None or not unit:
            return None

        value_si = self._convert_property_to_si(property_type, value, unit)
        if value_si is None:
            return None

        uncertainty = None
        uncertainty_raw = self._parse_float(row.get(f"{property_type}_uncertainty"))
        uncertainty_unit = self._normalize_unit(
            row.get(f"{property_type}_uncertainty_unit")
        )
        if not uncertainty_unit and uncertainty_units:
            uncertainty_unit = self._normalize_unit(
                uncertainty_units.get(property_type)
            )
        if uncertainty_raw is not None:
            if not uncertainty_unit:
                uncertainty_unit = unit
            uncertainty = self._convert_property_to_si(
                property_type, uncertainty_raw, uncertainty_unit
            )
            if uncertainty is None:
                return None

        return {"value": value_si, "uncertainty": uncertainty}

    def _row_has_any_property_value(
        self, row: Dict[str, str], units: Optional[Dict[str, str]] = None
    ) -> bool:
        return any(
            self._extract_property_si(row, property_type, units=units) is not None
            for property_type in self._default_supported_property_aliases()
        )

    def _has_required_row_parameters(
        self, row: Dict[str, str], units: Optional[Dict[str, str]] = None
    ) -> bool:
        return self._extract_temperature_kelvin(row, units) is not None

    def _map_parameter_type(self, parameter_type: str) -> Parameters:
        """Map parameter type string to Parameters enum."""
        return self._resolve_parameter_enum(parameter_type)

    def _default_supported_property_aliases(self) -> Tuple[str, ...]:
        return ("viscosity", "density", "conductivity")

    def get_parsable_property_keywords(self) -> Dict[str, str]:
        """
        Return user-facing property keywords mapped to Properties enum names.

        Returns:
            Dict[keyword, enum_name]
        """
        keyword_map = {
            "viscosity": Properties.VISCOSITY.name,
            "density": Properties.DENSITY.name,
            "conductivity": Properties.ELECTRICAL_CONDUCTIVITY.name,
            "electrical_conductivity": Properties.ELECTRICAL_CONDUCTIVITY.name,
            "thermal_conductivity": Properties.THERMAL_CONDUCTIVITY.name,
        }
        return keyword_map

    def get_parsable_parameter_keywords(self) -> Dict[str, str]:
        """
        Return user-facing parameter keywords mapped to Parameters enum names.

        Returns:
            Dict[keyword, enum_name]
        """
        keyword_map = {
            "temperature": Parameters.TEMPERATURE.name,
            "pressure": Parameters.PRESSURE.name,
            "mole_fraction": Parameters.MOLE_FRACTION.name,
            "molar_fraction": Parameters.MOLE_FRACTION.name,
            "time": Parameters.TIME.name,
        }
        return keyword_map

    def get_all_property_enum_keywords(self) -> Dict[str, str]:
        """
        Return all Properties enum options as {enum_name_lower: enum_value}.
        """
        return {member.name.lower(): member.value for member in Properties}

    def get_all_parameter_enum_keywords(self) -> Dict[str, str]:
        """
        Return all Parameters enum options as {enum_name_lower: enum_value}.
        """
        return {member.name.lower(): member.value for member in Parameters}

    def _resolve_property_alias_and_enum(
        self, property_name: str
    ) -> Tuple[str, Properties]:
        alias_to_enum = {
            "viscosity": Properties.VISCOSITY,
            "density": Properties.DENSITY,
            "conductivity": Properties.ELECTRICAL_CONDUCTIVITY,
            "electrical_conductivity": Properties.ELECTRICAL_CONDUCTIVITY,
            "thermal_conductivity": Properties.THERMAL_CONDUCTIVITY,
        }
        key = str(property_name).strip().lower().replace(" ", "_")
        if key in alias_to_enum:
            alias = "conductivity" if "conductivity" in key else key
            return alias, alias_to_enum[key]

        for enum_member in Properties:
            if key in {
                enum_member.name.lower(),
                enum_member.value.lower().replace(" ", "_"),
            }:
                if enum_member == Properties.VISCOSITY:
                    return "viscosity", enum_member
                if enum_member == Properties.DENSITY:
                    return "density", enum_member
                if enum_member in {
                    Properties.ELECTRICAL_CONDUCTIVITY,
                    Properties.THERMAL_CONDUCTIVITY,
                }:
                    return "conductivity", enum_member
                break

        raise ValueError(f"Unsupported property enum/alignment for '{property_name}'")

    def _resolve_parameter_enum(self, parameter_name: str) -> Parameters:
        key = str(parameter_name).strip().lower().replace(" ", "_")
        alias_to_enum = {
            "temperature": Parameters.TEMPERATURE,
            "pressure": Parameters.PRESSURE,
            "mole_fraction": Parameters.MOLE_FRACTION,
            "molar_fraction": Parameters.MOLE_FRACTION,
            "time": Parameters.TIME,
        }
        if key in alias_to_enum:
            return alias_to_enum[key]

        for enum_member in Parameters:
            enum_name = enum_member.name.lower()
            enum_value = enum_member.value.lower().replace(" ", "_")
            if key in {enum_name, enum_value}:
                return enum_member

        raise ValueError(
            f"Unsupported parameter '{parameter_name}'. Provide a Parameters enum name/value."
        )

    def _make_unit(self, unit_str: str, registry: IDRegistry) -> UnitDefinition:
        """Build a fully-specified canonical-SI unit for a parameter."""
        return UnitMapper.from_unit_string(
            unit_str, unit_id=registry.new_id("unit")
        )


# ``FluidIO`` subclasses ``Fluid``, whose ``fitted_model`` field forward-references
# ``FittedModel``. Rebuild the model here so the reference resolves in this module's
# namespace (``FittedModel`` is imported above) rather than failing lazily on first
# instantiation.
FluidIO.model_rebuild()


def from_csv(
    csv_path: str,
    *,
    document: Optional[FAIRFluidsDocument] = None,
    units: Optional[Dict[str, str]] = None,
    uncertainty_units: Optional[Dict[str, str]] = None,
    fetch_from_pubchem: bool = False,
    output_dir: Optional[str] = None,
) -> List[FAIRFluidsDocument]:
    """Convert a structured CSV/XLSX file into FAIRFluids documents.

    One document is produced per unique compound combination found in the file.
    The workflow should predefine ``document.citation`` (and, ideally, the
    compound block) before converting; a :class:`UserWarning` is emitted if the
    citation is missing.

    Args:
        csv_path: Path to the CSV or XLSX file.
        document: Optional template document supplying metadata (citation/version).
        units: Optional input units per quantity (e.g. ``{"pressure": "bar"}``);
            values are converted to canonical SI before storing.
        uncertainty_units: Optional input units for the uncertainty columns.
        fetch_from_pubchem: If True, enrich compounds with PubChem metadata.
        output_dir: Optional directory to additionally write JSON files into.

    Returns:
        A list of :class:`FAIRFluidsDocument` objects.
    """
    return FluidIO().data_from_spreadsheet(
        spreadsheet_path=csv_path,
        document=document,
        output_dir=output_dir,
        fetch_from_pubchem=fetch_from_pubchem,
        units=units,
        uncertainty_units=uncertainty_units,
    )
