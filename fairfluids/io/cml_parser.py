"""CML file parsing into FAIRFluids documents."""

from __future__ import annotations

import warnings
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from fairfluids.core.lib import (
    FAIRFluidsDocument,
    Method,
    Parameters,
    Properties,
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
from fairfluids.io.canonical.fairfluids_builder import build_fairfluids


class FAIRFluidsCMLParser:
    """
    Robust parser for CML files to populate the FAIRFluids data model.

    Parsing produces a neutral :class:`CanonicalDocument` (Route B: resolved
    controlled-vocab members, canonical units, fully-specified composition and
    per-measurement method); the shared FAIRFluids builder then assigns all
    object identifiers via its own ``<type>_<n>`` counter scheme. The citation
    and compound blocks are expected to be predefined by the workflow before
    feeding data; if they are missing a ``UserWarning`` is emitted (the parse
    still proceeds).
    """

    # property_type -> (controlled-vocab enum, canonical unit string)
    _PROPERTY_SPEC: Dict[str, tuple] = {
        "viscosity": (Properties.VISCOSITY, "Pa*s"),
        "kinematic_viscosity": (Properties.KINEMATIC_VISCOSITY, "m2/s"),
        "conductivity": (Properties.ELECTRICAL_CONDUCTIVITY, "S/m"),
        "density": (Properties.DENSITY, "kg/m3"),
    }

    def __init__(
        self,
        cml_path: str,
        compounds: Optional[List[Dict[str, Any]]] = None,
        document: Optional[FAIRFluidsDocument] = None,
        viscosity_input_unit: str = "cP",
    ):
        self.cml_path = cml_path
        self.compounds = compounds or []
        self.ns = "{http://www.xml-cml.org/schema}"
        self.viscosity_input_unit = (viscosity_input_unit or "cP").strip()
        if document is not None:
            self.document = document
        else:
            self.document = FAIRFluidsDocument()
        self._parse_cml_root()

    def _parse_cml_root(self):
        try:
            self.root = ET.parse(self.cml_path).getroot()
        except Exception as e:
            raise RuntimeError(f"Failed to parse CML file: {e}")

    def _warn_if_blocks_undefined(self) -> None:
        """Emit a ``UserWarning`` when the workflow has not predefined the
        citation or compound blocks (they must be set before feeding data)."""
        if self.document.citation is None:
            warnings.warn(
                "No citation defined on the document. Define `document.citation` "
                "before converting so the FAIRFluids document is fully attributed.",
                UserWarning,
                stacklevel=3,
            )
        has_compounds = bool(self.compounds) or bool(
            getattr(self.document, "compound", None)
        )
        if not has_compounds:
            warnings.warn(
                "No compounds defined. Provide `compounds=` or predefine "
                "`document.compound` before converting; compound references "
                "will otherwise be missing.",
                UserWarning,
                stacklevel=3,
            )

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            if value == "" or value.upper() == "NG":
                return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _extract_scalar_text(self, element: ET.Element) -> Optional[str]:
        scalar = element.find(f".//{self.ns}scalar")
        if scalar is None or scalar.text is None:
            return None
        value = scalar.text.strip()
        return value if value else None

    # ------------------------------------------------------------------
    # Unit conversions (input -> canonical SI)
    # ------------------------------------------------------------------
    def _convert_viscosity_to_pas(self, viscosity_value: float) -> float:
        """Convert viscosity from the configured CML input unit to Pa*s."""
        unit_normalized = (
            self.viscosity_input_unit.lower()
            .replace("·", "")
            .replace(" ", "")
            .replace("sec", "s")
        )
        if unit_normalized in {"cp", "centipoise", "mpas"}:
            return viscosity_value / 1000.0
        if unit_normalized in {"pas", "pa*s"}:
            return viscosity_value
        raise ValueError(
            f"Unsupported viscosity_input_unit='{self.viscosity_input_unit}'. "
            "Use 'cP', 'mPa·s', or 'Pa·s'."
        )

    @staticmethod
    def _convert_density_to_kg_m3(density_value: float) -> float:
        """Convert density to kg/m³ (values < 100 are assumed g/cm³)."""
        if 0 < density_value < 100.0:
            return density_value * 1000.0
        return density_value

    # ------------------------------------------------------------------
    # CML extraction
    # ------------------------------------------------------------------
    def _extract_properties(self, experiment: ET.Element) -> Dict[str, str]:
        properties = {}
        property_list = experiment.find(f".//{self.ns}propertyList")
        if property_list is not None:
            for prop in property_list:
                dict_ref = prop.get("dictRef")
                if dict_ref:
                    prop_type = dict_ref.split(":")[-1]
                    scalar_text = self._extract_scalar_text(prop)
                    if scalar_text is not None:
                        properties[prop_type] = scalar_text
        return properties

    def _extract_parameters(self, experiment: ET.Element) -> Dict[str, str]:
        parameters = {}
        param_list = experiment.find(f".//{self.ns}parameterList")
        if param_list is not None:
            for param in param_list:
                dict_ref = param.get("dictRef")
                if dict_ref:
                    param_type = dict_ref.split(":")[-1]
                    scalar_text = self._extract_scalar_text(param)
                    if scalar_text is not None:
                        parameters[param_type] = scalar_text
        return parameters

    def _extract_measurement_modules(self) -> List[tuple]:
        """Return (element, method_type) for experiment + simulation modules."""
        experiments = [
            (el, "EXPERIMENTAL")
            for el in self.root.findall(
                f".//{self.ns}module[@dictRef='des:experiment']"
            )
        ]
        simulations = [
            (el, "SIMULATION")
            for el in self.root.findall(
                f".//{self.ns}module[@dictRef='des:simulation']"
            )
        ]
        return experiments + simulations

    def _extract_uncertainty(
        self, props: Dict[str, str], property_name: str, property_value: float
    ) -> Optional[float]:
        """Extract absolute or relative uncertainty for a property."""
        if property_value is None:
            return None

        absolute_keys = [
            f"error_{property_name}",
            f"uncertainty_{property_name}",
            f"std_{property_name}",
            f"sigma_{property_name}",
        ]
        for key in absolute_keys:
            uncertainty_value = self._safe_float(props.get(key))
            if uncertainty_value is not None:
                return uncertainty_value

        relative_keys = [
            f"relative_error_{property_name}",
            f"rel_error_{property_name}",
            f"relative_uncertainty_{property_name}",
        ]
        for key in relative_keys:
            raw_relative = props.get(key)
            if raw_relative is None:
                continue
            raw_relative = str(raw_relative).strip()
            if raw_relative == "":
                continue

            is_percent = raw_relative.endswith("%")
            if is_percent:
                raw_relative = raw_relative[:-1].strip()

            relative_value = self._safe_float(raw_relative)
            if relative_value is None:
                continue

            if is_percent:
                relative_value = relative_value / 100.0

            return abs(property_value) * relative_value

        return None

    def _calculate_mole_fractions(self, molar_ratio: float, water_fraction: float):
        """Compute (x1, x2, x3) for DES component 1, component 2, and water."""
        r = self._safe_float(molar_ratio)
        w = self._safe_float(water_fraction)
        if r is None or w is None:
            raise ValueError(
                f"Cannot calculate mole fractions from invalid inputs "
                f"r={molar_ratio}, w={water_fraction}"
            )
        if r < 0:
            raise ValueError(f"Molar ratio must be >= 0, got {r}")
        if not 0.0 <= w <= 1.0:
            raise ValueError(f"Water mole fraction must be in [0, 1], got {w}")
        x3 = w
        x1 = (r * (1 - x3)) / (r + 1)
        x2 = (1 - x3) - x1

        total = x1 + x2 + x3
        x1_n = x1 / total
        x2_n = x2 / total
        x3_n = x3 / total

        precision = 12
        x1_final = round(x1_n, precision)
        x2_final = round(x2_n, precision)
        x3_final = round(x3_n, precision)

        sum_check = x1_final + x2_final + x3_final
        if abs(sum_check - 1.0) > 1e-10:
            diff = 1.0 - sum_check
            if abs(x3_final) >= abs(x2_final) and abs(x3_final) >= abs(x1_final):
                x3_final += diff
            elif abs(x2_final) >= abs(x1_final):
                x2_final += diff
            else:
                x1_final += diff

        return x1_final, x2_final, x3_final

    # ------------------------------------------------------------------
    # Canonical producer (Layer 2) — emits a neutral CanonicalDocument that
    # the shared FAIRFluids builder consumes. CML already knows the exact
    # controlled-vocab member, canonical unit, fully-specified composition and
    # per-measurement method, so it populates the Route-B "resolved" fields and
    # sets ``complete_composition=False`` to bypass the inference machinery.
    # ------------------------------------------------------------------
    def _canonical_citation(self) -> CanonicalCitation:
        cit = getattr(self.document, "citation", None)
        if cit is None:
            return CanonicalCitation()
        authors: List[str] = []
        for a in (cit.author or []):
            fam = (a.family_name or "").strip()
            giv = (a.given_name or "").strip()
            if fam and giv:
                authors.append(f"{fam}, {giv}")
            elif fam or giv:
                authors.append(fam or giv)
        return CanonicalCitation(
            title=cit.title,
            doi=cit.doi,
            pub_name=cit.pub_name,
            pub_year=cit.publication_year,
            volume=cit.lit_volume_num,
            page=cit.page,
            lit_type=(cit.litType.value if cit.litType is not None else None),
            authors=authors,
        )

    def _canonical_source_compounds(self) -> List[CanonicalSourceCompound]:
        existing = getattr(self.document, "compound", None)
        if existing:
            return [
                CanonicalSourceCompound(
                    component_key=i,
                    common_name=c.commonName,
                    pubchem_cid=c.pubChemID,
                    standard_inchi=c.standard_InChI,
                    standard_inchi_key=c.standard_InChI_key,
                )
                for i, c in enumerate(existing)
            ]
        result: List[CanonicalSourceCompound] = []
        for i, comp in enumerate(self.compounds):
            cid = comp.get("pubChemID")
            try:
                cid = int(cid) if cid is not None else None
            except (TypeError, ValueError):
                cid = None
            result.append(
                CanonicalSourceCompound(
                    component_key=i,
                    common_name=comp.get("commonName"),
                    pubchem_cid=cid,
                    standard_inchi=comp.get("standard_InChI"),
                    standard_inchi_key=comp.get("standard_InChI_key"),
                )
            )
        return result

    def to_canonical_document(self) -> CanonicalDocument:
        """Parse the CML file into a neutral :class:`CanonicalDocument`."""
        source_compounds = self._canonical_source_compounds()
        n_compounds = len(source_compounds)

        measurement_modules = self._extract_measurement_modules()

        # Discover property types present across modules (stable order).
        property_types: List[str] = []
        value_key_to_type = {
            "value_viscosity": "viscosity",
            "value_conductivity": "conductivity",
            "value_density": "density",
        }
        for exp, _ in measurement_modules:
            props = self._extract_properties(exp)
            for key, ptype in value_key_to_type.items():
                if key in props and ptype not in property_types:
                    property_types.append(ptype)

        # Group measurements by composition (rounded to 3 d.p.).
        composition_groups: Dict[tuple, list] = {}
        for exp, method_type in measurement_modules:
            props = self._extract_properties(exp)
            params = self._extract_parameters(exp)
            mole_fraction_water = self._safe_float(
                params.get("mole_fraction_of_water")
            )
            molar_ratio_des = self._safe_float(params.get("molar_ratio_of_DES"))
            if mole_fraction_water is None or molar_ratio_des is None:
                continue
            try:
                x1, x2, x3 = self._calculate_mole_fractions(
                    molar_ratio_des, mole_fraction_water
                )
            except ValueError:
                continue
            composition_key = (round(x1, 3), round(x2, 3), round(x3, 3))
            composition_groups.setdefault(composition_key, []).append(
                (exp, method_type, props, params)
            )

        datasets: List[CanonicalDataset] = []
        for di, (composition_key, measurements) in enumerate(
            composition_groups.items(), start=1
        ):
            present_indices = [
                i
                for i, mf in enumerate(composition_key)
                if mf > 0 and i < n_compounds
            ]

            cds_compounds = [
                CanonicalCompound(component_key=i, compound_id=f"compound_{i}")
                for i in present_indices
            ]

            properties: Dict[str, CanonicalProperty] = {}
            prop_id_by_type: Dict[str, str] = {}
            for pt in property_types:
                enum_member, unit_str = self._PROPERTY_SPEC[pt]
                pid = f"prop_{pt}"
                properties[pid] = CanonicalProperty(
                    prop_id=pid,
                    source_term=pt,
                    resolved_property=enum_member,
                    canonical_unit=unit_str,
                )
                prop_id_by_type[pt] = pid

            parameters: Dict[str, CanonicalParameter] = {}
            mf_param_id_by_index: Dict[int, str] = {}
            for i in present_indices:
                pid = f"param_molefrac_{i}"
                parameters[pid] = CanonicalParameter(
                    param_id=pid,
                    source_term="mole fraction",
                    resolved_parameter=Parameters.MOLE_FRACTION,
                    canonical_unit="dimensionless",
                    component_ref=i,
                )
                mf_param_id_by_index[i] = pid
            temp_pid = "param_temperature"
            parameters[temp_pid] = CanonicalParameter(
                param_id=temp_pid,
                source_term="temperature",
                resolved_parameter=Parameters.TEMPERATURE,
                canonical_unit="K",
            )

            rows: List[CanonicalRow] = []
            for exp, method_type, props, params in measurements:
                temperature = self._safe_float(params.get("temperature"))
                mole_fraction_water = self._safe_float(
                    params.get("mole_fraction_of_water")
                )
                molar_ratio_des = self._safe_float(
                    params.get("molar_ratio_of_DES")
                )

                row = CanonicalRow()
                if molar_ratio_des is not None and mole_fraction_water is not None:
                    calc = self._calculate_mole_fractions(
                        molar_ratio_des, mole_fraction_water
                    )
                    for i, pid in mf_param_id_by_index.items():
                        row.parameter_values[pid] = calc[i]
                if temperature is not None:
                    row.parameter_values[temp_pid] = temperature

                if "viscosity" in prop_id_by_type and "value_viscosity" in props:
                    v = self._safe_float(props.get("value_viscosity"))
                    if v is not None:
                        pid = prop_id_by_type["viscosity"]
                        row.property_values[pid] = self._convert_viscosity_to_pas(v)
                        unc = self._extract_uncertainty(props, "viscosity", v)
                        if unc is not None:
                            row.uncertainties[f"{pid}_unc"] = (
                                self._convert_viscosity_to_pas(unc)
                            )
                if (
                    "conductivity" in prop_id_by_type
                    and "value_conductivity" in props
                ):
                    c = self._safe_float(props.get("value_conductivity"))
                    if c is not None:
                        pid = prop_id_by_type["conductivity"]
                        row.property_values[pid] = c
                        unc = self._extract_uncertainty(props, "conductivity", c)
                        if unc is not None:
                            row.uncertainties[f"{pid}_unc"] = unc
                if "density" in prop_id_by_type and "value_density" in props:
                    d = self._safe_float(props.get("value_density"))
                    if d is not None:
                        pid = prop_id_by_type["density"]
                        row.property_values[pid] = self._convert_density_to_kg_m3(d)
                        unc = self._extract_uncertainty(props, "density", d)
                        if unc is not None:
                            row.uncertainties[f"{pid}_unc"] = (
                                self._convert_density_to_kg_m3(unc)
                            )

                if method_type == "EXPERIMENTAL":
                    row.method = Method.MEASURED
                    row.method_description = "Experimental measurement"
                else:
                    row.method = Method.SIMULATED
                    row.method_description = "Simulation measurement"

                rows.append(row)

            datasets.append(
                CanonicalDataset(
                    index=di,
                    compounds=cds_compounds,
                    properties=properties,
                    parameters=parameters,
                    rows=rows,
                )
            )

        return CanonicalDocument(
            citation=self._canonical_citation(),
            compounds=source_compounds,
            datasets=datasets,
            complete_composition=False,
        )

    def parse(self, fetch_from_pubchem: bool = True) -> FAIRFluidsDocument:
        self._warn_if_blocks_undefined()
        canonical = self.to_canonical_document()
        doc_dict = build_fairfluids(canonical, fetch_from_pubchem=fetch_from_pubchem)
        self.document = FAIRFluidsDocument.model_validate(doc_dict)
        return self.document


def from_cml(
    cml_path: str,
    *,
    document: Optional[FAIRFluidsDocument] = None,
    compounds: Optional[List[Dict[str, Any]]] = None,
    viscosity_input_unit: str = "cP",
    fetch_from_pubchem: bool = True,
) -> List[FAIRFluidsDocument]:
    """Convert a CML file into FAIRFluids documents.

    The optional ``document`` template should carry the workflow-defined
    citation and (optionally) compound blocks; CML files do not embed a
    citation, so this template supplies the document's attribution. Compounds
    may alternatively be supplied via ``compounds``. A ``UserWarning`` is
    emitted if neither citation nor compounds are defined.

    CML parsing emits a neutral :class:`CanonicalDocument` (Route B: resolved
    controlled-vocab members, canonical units, fully-specified composition and
    per-measurement method) which the shared FAIRFluids builder turns into the
    final document.

    Returns:
        A list of :class:`FAIRFluidsDocument`. A CML file maps to a single
        document, so the list always has exactly one element; the list return
        type matches :func:`from_csv` and :func:`from_thermoml`.
    """
    parser = FAIRFluidsCMLParser(
        cml_path,
        compounds=compounds,
        document=document,
        viscosity_input_unit=viscosity_input_unit,
    )
    return [parser.parse(fetch_from_pubchem=fetch_from_pubchem)]


__all__ = ["FAIRFluidsCMLParser", "from_cml"]
