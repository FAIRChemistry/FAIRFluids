"""
fluid_io.py

Utilities for loading tabular (CSV) fluid-property data into FAIRFluids
documents via the shared canonical pipeline (producer -> Canonical models ->
build_fairfluids -> FAIRFluidsDocument).

CSV rows are grouped by ``source_doi`` into one FAIRFluidsDocument per DOI,
then split into fluids by composition.

Usage:
    from fairfluids.io.fluid_io import FluidIO
    from fairfluids.core.lib import FAIRFluidsDocument

    # Returns a list of FAIRFluidsDocument, one per source DOI:
    docs = FluidIO().data_from_csv('path/to/data.csv')

    # Or seed citation/version metadata from a template document:
    doc = FAIRFluidsDocument()
    docs = FluidIO().data_from_csv('path/to/data.csv', document=doc)
"""

import csv
import warnings
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from collections import defaultdict, Counter
from fairfluids.io.canonical.fairfluids_builder import (
    _clean_doi,
    build_fairfluids,
    canonical_citation_from_citation,
)
from fairfluids.io.canonical.canonical_model import (
    CanonicalCitation,
    CanonicalCompound,
    CanonicalDataset,
    CanonicalDocument,
    CanonicalParameter,
    CanonicalProperty,
    CanonicalRow,
    CanonicalSourceCompound,
)
from fairfluids.core.lib import (
    Method,
    FAIRFluidsDocument,
    Properties,
    Parameters,
    Version,
)


class FluidIO:
    """
    Converter that loads fluid data from a structured CSV/XLSX file and emits
    :class:`FAIRFluidsDocument` objects via the shared canonical builder.
    """

    def data_from_csv(
        self,
        csv_path: str,
        document: Optional[FAIRFluidsDocument] = None,
        output_dir: Optional[str] = None,
        fetch_from_pubchem: bool = False,
        fetch_from_doi: bool = True,
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
            fetch_from_doi=fetch_from_doi,
            units=units,
            uncertainty_units=uncertainty_units,
        )

    def data_from_spreadsheet(
        self,
        spreadsheet_path: str,
        document: Optional[FAIRFluidsDocument] = None,
        output_dir: Optional[str] = None,
        fetch_from_pubchem: bool = False,
        fetch_from_doi: bool = True,
        units: Optional[Dict[str, str]] = None,
        uncertainty_units: Optional[Dict[str, str]] = None,
    ) -> List[FAIRFluidsDocument]:
        """
        Create FAIRFluids documents from a structured CSV/XLSX file.

        Supports the structured format with:
        - Compound i / Molar Fraction i columns
        - mandatory temperature and pressure columns (+ units)
        - optional multi-property blocks per row (e.g. viscosity_value, density_value)

        Grouping:
        - One :class:`FAIRFluidsDocument` is produced **per source DOI**
          (``source_doi`` / ``Reference (DOI)`` column).
        - Within a document, one fluid is created per **composition group**
          (compound set + molar fractions + storage). A single DOI may contain
          several compound sets; these become several fluids and the document's
          compound list is the union across them.
        - Rows without a DOI are kept but grouped into a single document and a
          ``UserWarning`` is emitted; attribute them by predefining the
          ``document`` citation block.

        Args:
            spreadsheet_path: Path to the CSV or XLSX file.
            document: Optional template document (for metadata like citation).
            output_dir: Optional directory to save JSON files.
            fetch_from_pubchem: If True, fetch compound information from PubChem.
            fetch_from_doi: If True (default), resolve each document's citation
                block online from its ``source_doi`` (Crossref / OpenAlex /
                Semantic Scholar), filling fields the template citation omits.
                Network failures degrade gracefully to the template values.
            units: Optional global input units, e.g.
                {"temperature": "C", "pressure": "bar", "viscosity": "cP"}
            uncertainty_units: Optional global uncertainty units per quantity, e.g.
                {"temperature": "K", "pressure": "bar", "viscosity": "cP"}

        Returns:
            List of FAIRFluidsDocument objects (one per source DOI).
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

        # Warn about rows lacking a source DOI (they collapse into one document
        # attributed only by the predefined citation).
        rows_without_doi = sum(
            1
            for row in rows_data
            if self._extract_compounds(row) and self._extract_row_doi(row) is None
        )
        if rows_without_doi:
            warnings.warn(
                f"{rows_without_doi} row(s) have no source DOI; they are grouped "
                "into a single document attributed only by the predefined citation "
                "(if any). Provide a `source_doi` (or `Reference (DOI)`) per row to "
                "split data by publication.",
                UserWarning,
                stacklevel=2,
            )

        # Route B: turn the rows into one neutral CanonicalDocument per DOI,
        # then let the shared FAIRFluids builder produce each document.
        canonical_pairs = self._csv_to_canonical_documents(
            rows_data, units=units, uncertainty_units=uncertainty_units
        )
        print(f"Found {len(canonical_pairs)} source DOI group(s)")

        # Flatten the template citation once so every per-DOI document runs the
        # same builder path: template fields stay authoritative, the per-document
        # ``source_doi`` attributes the citation, and (when enabled) the DOI
        # lookup fills any remaining gaps.
        template_citation = (
            canonical_citation_from_citation(document.citation)
            if (document is not None and document.citation)
            else None
        )

        documents: List[FAIRFluidsDocument] = []
        for doi, canonical_document in canonical_pairs:
            if template_citation is not None:
                canonical_document.citation = template_citation
            doc_dict = build_fairfluids(
                canonical_document,
                fetch_from_pubchem=fetch_from_pubchem,
                fetch_from_doi=fetch_from_doi,
            )
            doc = FAIRFluidsDocument.model_validate(doc_dict)

            # Document-level version mirrors the template (the canonical builder
            # leaves version to the producer): default to 1.0 otherwise. The
            # citation is now built + DOI-enriched per document by the builder,
            # so it is no longer overwritten with the shared template here.
            doc.version = (
                document.version
                if (document is not None and document.version)
                else Version(versionMajor=1, versionMinor=0)
            )

            if not doc.fluid:
                print(f"No fluids created for DOI {doi!r}.")

            documents.append(doc)

            # Save to JSON if output_dir is specified
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                filepath = output_path / f"{self._sanitize_doi_for_filename(doi)}.json"
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(doc.model_dump_json(indent=2))
                print(f"Saved document to: {filepath}")

        return documents


    def _extract_row_doi(self, row: Dict[str, str]) -> Optional[str]:
        """Return the cleaned bare DOI for a row, or ``None`` if absent."""
        raw = (
            row.get("source_doi", "").strip()
            or row.get("Reference (DOI)", "").strip()
        )
        return _clean_doi(raw) or None

    def _unique_compounds_in_order(
        self, rows: List[Dict[str, str]]
    ) -> List[str]:
        """Collect every compound name across ``rows`` in first-seen order."""
        seen: List[str] = []
        for row in rows:
            for name in self._extract_compounds(row):
                if name not in seen:
                    seen.append(name)
        return seen

    def _sanitize_doi_for_filename(self, doi: Optional[str]) -> str:
        """Turn a DOI (or ``None``) into a filesystem-safe filename stem."""
        if not doi:
            return "no_doi"
        safe = doi.replace("/", "_").replace(":", "_").replace(" ", "_")
        return safe.replace("\\", "_")

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

    # ------------------------------------------------------------------
    # Canonical producer (Route B): CSV/XLSX rows -> CanonicalDocument(s)
    # ------------------------------------------------------------------

    # Canonical-SI unit strings per supported property type (mirrors the
    # controlled vocabulary the shared FAIRFluids builder expects).
    _PROPERTY_SI_UNIT: Dict[str, str] = {
        "viscosity": "Pa*s",
        "density": "kg/m3",
        "conductivity": "S/m",
    }

    def _csv_to_canonical_documents(
        self,
        rows_data: List[Dict[str, str]],
        *,
        units: Optional[Dict[str, str]] = None,
        uncertainty_units: Optional[Dict[str, str]] = None,
    ) -> List[Tuple[Optional[str], CanonicalDocument]]:
        """Group CSV/XLSX rows into one neutral :class:`CanonicalDocument` per DOI.

        Route B: composition is fully specified (exact mole fractions), the
        controlled-vocab member and canonical unit are pre-resolved, and each
        measurement carries its method explicitly. ``complete_composition`` is
        therefore ``False`` and ``source_doi`` is the per-document DOI.

        Returns a list of ``(doi, document)`` pairs preserving first-seen DOI
        order so the caller can attribute / name outputs per group.
        """
        # One document per source DOI (rows without a DOI share the ``None`` key).
        doi_groups: "defaultdict[Optional[str], List[Dict[str, str]]]" = defaultdict(
            list
        )
        for row in rows_data:
            if not self._extract_compounds(row):
                continue  # Skip rows with no compounds
            doi_groups[self._extract_row_doi(row)].append(row)

        documents: List[Tuple[Optional[str], CanonicalDocument]] = []
        for doi, rows in doi_groups.items():
            # Document compounds = union of every compound under this DOI in
            # first-seen order; the index is the document-global component key.
            names = self._unique_compounds_in_order(rows)
            name_to_key = {name: idx for idx, name in enumerate(names)}
            # Explicit ``pubchemID i`` columns (first-seen per name) so the
            # builder's PubChem enrichment can use them directly.
            explicit_cid: Dict[str, int] = {}
            for row in rows:
                row_compounds = self._extract_compounds(row)
                pubchem_ids = self._extract_pubchem_ids(row, len(row_compounds))
                for name, cid in zip(row_compounds, pubchem_ids):
                    if cid is not None and name not in explicit_cid:
                        explicit_cid[name] = cid
            source_compounds = [
                CanonicalSourceCompound(
                    component_key=idx,
                    common_name=name.strip(),
                    pubchem_cid=explicit_cid.get(name),
                )
                for idx, name in enumerate(names)
            ]

            # Group rows into fluids/datasets by composition
            # (compound set + molar fractions + storage).
            composition_groups: "defaultdict[Tuple[Tuple[str, ...], Tuple[float, ...], Optional[str]], List[Dict[str, str]]]" = defaultdict(
                list
            )
            skip_invalid_mole_fraction_sum = 0
            invalid_mole_fraction_compositions: Counter[Tuple[float, ...]] = Counter()
            for row in rows:
                row_compounds = self._extract_compounds(row)
                if not self._has_required_row_parameters(row, units):
                    continue
                if not self._row_has_any_property_value(row, units):
                    continue
                molar_fractions = self._extract_molar_fractions(
                    row, len(row_compounds)
                )
                if molar_fractions is None:
                    continue
                if not self._is_valid_mole_fraction_sum(molar_fractions):
                    skip_invalid_mole_fraction_sum += 1
                    invalid_mole_fraction_compositions[tuple(molar_fractions)] += 1
                    continue
                storage_str = row.get("Storage", "").strip().lower()
                storage_key = (
                    None if storage_str in ["", "nan", "none"] else storage_str
                )
                composition_groups[
                    (tuple(row_compounds), tuple(molar_fractions), storage_key)
                ].append(row)

            if skip_invalid_mole_fraction_sum > 0:
                composition_details = "; ".join(
                    f"{list(fracs)} (sum={sum(fracs):.6g}, {count} row(s))"
                    for fracs, count in sorted(
                        invalid_mole_fraction_compositions.items(),
                        key=lambda item: (-item[1], item[0]),
                    )
                )
                warnings.warn(
                    f"Skipped {skip_invalid_mole_fraction_sum} row(s) for DOI "
                    f"{doi!r}: molar fractions must sum to 1 (tolerance 1e-8). "
                    f"No fluid is created for these compositions. "
                    f"Invalid value(s): {composition_details}.",
                    UserWarning,
                    stacklevel=2,
                )

            datasets: List[CanonicalDataset] = []
            for index, (
                (row_compounds, _fracs, _storage),
                group_rows,
            ) in enumerate(composition_groups.items()):
                if not group_rows:
                    continue
                datasets.append(
                    self._csv_composition_to_dataset(
                        index,
                        list(row_compounds),
                        name_to_key,
                        group_rows,
                        units=units,
                        uncertainty_units=uncertainty_units,
                    )
                )

            documents.append(
                (
                    doi,
                    CanonicalDocument(
                        citation=CanonicalCitation(),
                        compounds=source_compounds,
                        datasets=datasets,
                        complete_composition=False,
                        source_doi=doi,
                    ),
                )
            )

        return documents

    def _csv_composition_to_dataset(
        self,
        index: int,
        row_compounds: List[str],
        name_to_key: Dict[str, int],
        group_rows: List[Dict[str, str]],
        *,
        units: Optional[Dict[str, str]] = None,
        uncertainty_units: Optional[Dict[str, str]] = None,
    ) -> CanonicalDataset:
        """Turn one composition group into a canonical dataset (fluid)."""
        # Properties present in any row, in canonical supported order so the
        # builder reproduces stable ``property_<n>`` IDs.
        present_props: List[str] = []
        for property_type in self._default_supported_property_aliases():
            if any(
                self._extract_property_si(
                    row, property_type, units=units, uncertainty_units=uncertainty_units
                )
                is not None
                for row in group_rows
            ):
                present_props.append(property_type)

        properties: Dict[str, CanonicalProperty] = {}
        prop_canon_id: Dict[str, str] = {}
        for property_type in present_props:
            canon_id = f"prop_{property_type}"
            prop_canon_id[property_type] = canon_id
            properties[canon_id] = CanonicalProperty(
                prop_id=canon_id,
                source_term=property_type,
                resolved_property=self._map_property_type(property_type),
                canonical_unit=self._PROPERTY_SI_UNIT[property_type],
            )

        # Parameters: temperature, optional pressure, then a mole fraction per
        # compound (insertion order = builder allocation order).
        parameters: Dict[str, CanonicalParameter] = {
            "param_temperature": CanonicalParameter(
                param_id="param_temperature",
                source_term="temperature",
                resolved_parameter=Parameters.TEMPERATURE,
                canonical_unit="K",
            )
        }
        has_pressure = any(
            self._extract_pressure_kpa(row, units) is not None for row in group_rows
        )
        if has_pressure:
            parameters["param_pressure"] = CanonicalParameter(
                param_id="param_pressure",
                source_term="pressure",
                resolved_parameter=Parameters.PRESSURE,
                canonical_unit="kPa",
            )
        molefrac_canon_id: Dict[int, str] = {}
        for position, name in enumerate(row_compounds):
            key = name_to_key[name]
            canon_id = f"param_x_{key}"
            molefrac_canon_id[position] = canon_id
            parameters[canon_id] = CanonicalParameter(
                param_id=canon_id,
                source_term="mole fraction",
                resolved_parameter=Parameters.MOLE_FRACTION,
                canonical_unit="dimensionless",
                component_ref=key,
            )

        rows_out: List[CanonicalRow] = []
        for row in group_rows:
            temperature = self._extract_temperature_kelvin(row, units)
            pressure = self._extract_pressure_kpa(row, units)
            molar_fractions = self._extract_molar_fractions(
                row, len(row_compounds)
            )

            property_values: Dict[str, float] = {}
            uncertainties: Dict[str, float] = {}
            for property_type in present_props:
                payload = self._extract_property_si(
                    row,
                    property_type,
                    units=units,
                    uncertainty_units=uncertainty_units,
                )
                if payload is None:
                    continue
                canon_id = prop_canon_id[property_type]
                property_values[canon_id] = payload["value"]
                if payload["uncertainty"] is not None:
                    uncertainties[f"{canon_id}_unc"] = payload["uncertainty"]

            parameter_values: Dict[str, float] = {"param_temperature": temperature}
            if has_pressure and pressure is not None:
                parameter_values["param_pressure"] = pressure
            for position in range(len(row_compounds)):
                parameter_values[molefrac_canon_id[position]] = molar_fractions[
                    position
                ]

            comment = row.get("Comment", "").strip()
            method_description = "Experimental measurement"
            if comment:
                method_description += f" (Comment: {comment})"

            rows_out.append(
                CanonicalRow(
                    parameter_values=parameter_values,
                    property_values=property_values,
                    uncertainties=uncertainties,
                    method=Method.MEASURED,
                    method_description=method_description,
                )
            )

        return CanonicalDataset(
            index=index,
            compounds=[
                CanonicalCompound(
                    component_key=name_to_key[name], compound_id=""
                )
                for name in row_compounds
            ],
            properties=properties,
            parameters=parameters,
            rows=rows_out,
        )

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

    One :class:`FAIRFluidsDocument` is produced **per source DOI**; within a
    document each composition group becomes a fluid. The optional ``document``
    template supplies citation/version metadata (CSV rows carry no citation
    block); a :class:`UserWarning` is emitted if no citation is provided.

    Args:
        csv_path: Path to the CSV or XLSX file.
        document: Optional template document supplying citation/version metadata.
        units: Optional input units per quantity (e.g. ``{"pressure": "bar"}``);
            values are converted to canonical SI before storing.
        uncertainty_units: Optional input units for the uncertainty columns.
        fetch_from_pubchem: If True, enrich compounds with PubChem metadata.
        output_dir: Optional directory to additionally write JSON files into.

    Returns:
        A list of :class:`FAIRFluidsDocument` (one per source DOI); the list
        return type matches :func:`from_cml` and :func:`from_thermoml`.
    """
    return FluidIO().data_from_spreadsheet(
        spreadsheet_path=csv_path,
        document=document,
        output_dir=output_dir,
        fetch_from_pubchem=fetch_from_pubchem,
        units=units,
        uncertainty_units=uncertainty_units,
    )
