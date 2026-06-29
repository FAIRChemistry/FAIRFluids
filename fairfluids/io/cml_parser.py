"""CML file parsing into FAIRFluids documents."""

from __future__ import annotations

import warnings
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from fairfluids.core.lib import (
    FAIRFluidsDocument,
    Measurement,
    Method,
    Parameter,
    ParameterValue,
    Parameters,
    Properties,
    Property,
    PropertyValue,
    Sample,
)
from fairfluids.io.pubchem import fetch_compound_from_pubchem
from fairfluids.io.thermoml_to_fairfluids.fairfluids_builder import _clean_doi
from fairfluids.io.thermoml_to_fairfluids.id_registry import IDRegistry
from fairfluids.io.thermoml_to_fairfluids.mappers.unit_mapper import UnitMapper
from fairfluids.operations.sample_utils import _ensure_fluid_sample


class FAIRFluidsCMLParser:
    """
    Robust parser for CML files to populate the FAIRFluids data model.

    Identifiers for every generated object (property, parameter, measurement,
    sample, fluid, unit) follow the canonical ``<type>_<n>`` counter scheme via
    a single :class:`IDRegistry`. Compound IDs are owned by the workflow: if a
    supplied compound dict carries ``compoundID`` it is respected, otherwise a
    counter ID is assigned. The citation and compound blocks are expected to be
    predefined by the workflow before feeding data; if they are missing a
    ``UserWarning`` is emitted (the parse still proceeds).
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
        self.registry = IDRegistry()
        if document is not None:
            self.document = document
        else:
            self.document = FAIRFluidsDocument()
        self.index_to_compoundID: Dict[int, str] = {}
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
    # Units
    # ------------------------------------------------------------------
    def _unit(self, unit_str: str):
        """Build a fully-specified ``UnitDefinition`` with a counter unit ID."""
        return UnitMapper.from_unit_string(
            unit_str, unit_id=self.registry.new_id("unit")
        )

    @staticmethod
    def _dimensionless():
        return UnitMapper.dimensionless()

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
    # Compounds
    # ------------------------------------------------------------------
    def populate_compounds(self):
        """Populate compounds and build ``index_to_compoundID``.

        Compound IDs are workflow-owned: a provided ``compoundID`` is kept,
        otherwise a ``compound_<n>`` counter ID is assigned. Compound ordering
        (index) maps onto the CML composition components x1, x2, x3.
        """
        self.index_to_compoundID = {}

        existing = getattr(self.document, "compound", None)
        if existing:
            for i, compound in enumerate(existing):
                if compound.compoundID is None:
                    compound.compoundID = self.registry.new_id("compound")
                self.index_to_compoundID[i] = str(compound.compoundID)
            return

        for i, comp in enumerate(self.compounds):
            comp = dict(comp)
            pubchem_id = comp.get("pubChemID")
            if pubchem_id is not None:
                try:
                    pubchem_id = int(pubchem_id)
                except (ValueError, TypeError):
                    print(
                        f"Warning: Invalid pubChemID format: {pubchem_id}, "
                        "skipping PubChem fetch"
                    )
                    pubchem_id = None

                if pubchem_id is not None:
                    print(f"Fetching compound data from PubChem for CID {pubchem_id}...")
                    fetched_data = fetch_compound_from_pubchem(pubchem_id)
                    if fetched_data is not None:
                        merged = comp.copy()
                        merged.update(fetched_data)
                        merged["pubChemID"] = pubchem_id
                        comp = merged
                        print(f"Successfully fetched and merged data for CID {pubchem_id}")
                    else:
                        print(
                            f"Warning: Failed to fetch data from PubChem for CID "
                            f"{pubchem_id}, using provided data"
                        )

            compound = self.document.add_to_compound(**comp)
            if compound.compoundID is None:
                compound.compoundID = self.registry.new_id("compound")
            self.index_to_compoundID[i] = str(compound.compoundID)

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

    # ------------------------------------------------------------------
    # Model object builders (counter IDs + controlled vocab enums)
    # ------------------------------------------------------------------
    def _make_property(self, property_type: str) -> Property:
        if property_type not in self._PROPERTY_SPEC:
            raise NotImplementedError(
                f"Property type {property_type} not implemented."
            )
        enum_member, unit_str = self._PROPERTY_SPEC[property_type]
        return Property(
            propertyID=self.registry.new_id("property"),
            properties=enum_member,
            unit=self._unit(unit_str),
        )

    def _make_property_value(
        self, prop: Property, value: float, uncertainty: Optional[float]
    ) -> PropertyValue:
        return PropertyValue(
            propertyID=prop.propertyID,
            properties=prop.properties,
            propValue=float(value),
            uncertainty=(float(uncertainty) if uncertainty is not None else None),
        )

    def _make_parameter_value(
        self, param: Parameter, value: float
    ) -> ParameterValue:
        return ParameterValue(
            parameterID=param.parameterID,
            parameters=param.parameters,
            paramValue=float(value),
            uncertainty=None,
        )

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
    # Fluids & measurements
    # ------------------------------------------------------------------
    def populate_fluids_and_measurements(self):
        """Populate one fluid per unique composition, with its measurements."""
        measurement_modules = self._extract_measurement_modules()

        # Discover all property types present across modules (stable order).
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

        # One shared Property definition per type (counter IDs + enums).
        property_objs: Dict[str, Property] = {
            pt: self._make_property(pt) for pt in property_types
        }

        # Group measurements by composition (rounded to 3 d.p.).
        composition_groups: Dict[tuple, list] = {}
        for exp, method_type in measurement_modules:
            props = self._extract_properties(exp)
            params = self._extract_parameters(exp)

            mole_fraction_water = self._safe_float(params.get("mole_fraction_of_water"))
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

        print(f"Found {len(composition_groups)} unique compositions")

        for composition_key, measurements in composition_groups.items():
            x1, x2, x3 = composition_key

            present_indices = [
                i for i, mole_frac in enumerate([x1, x2, x3]) if mole_frac > 0
            ]
            present_compounds = [
                self.index_to_compoundID[i]
                for i in present_indices
                if i in self.index_to_compoundID
            ]

            print(f"Composition {composition_key}: compounds {present_compounds}")

            # Mole-fraction parameters for each present compound + temperature.
            parameters: List[Parameter] = []
            mole_frac_param_by_index: Dict[int, Parameter] = {}
            for i in present_indices:
                if i not in self.index_to_compoundID:
                    continue
                param = Parameter(
                    parameterID=self.registry.new_id("parameter"),
                    parameters=Parameters.MOLE_FRACTION,
                    unit=self._dimensionless(),
                    associated_compounds=[self.index_to_compoundID[i]],
                )
                parameters.append(param)
                mole_frac_param_by_index[i] = param

            temp_param = Parameter(
                parameterID=self.registry.new_id("parameter"),
                parameters=Parameters.TEMPERATURE,
                unit=self._unit("K"),
                associated_compounds=[],
            )
            parameters.append(temp_param)

            sample = Sample(
                sample_id=self.registry.new_id("sample"),
                associated_compounds=present_compounds,
                measurement=[],
            )
            fluid = self.document.add_to_fluid(
                fluidID=[self.registry.new_id("fluid")],
                compounds=present_compounds,
                property=list(property_objs.values()),
                parameter=parameters,
                sample=sample,
            )

            for exp, method_type, props, params in measurements:
                doi = _clean_doi(props.get("DOI")) or None
                temperature = self._safe_float(params.get("temperature"))
                mole_fraction_water = self._safe_float(
                    params.get("mole_fraction_of_water")
                )
                molar_ratio_des = self._safe_float(params.get("molar_ratio_of_DES"))

                parameter_values: List[ParameterValue] = []
                if molar_ratio_des is not None and mole_fraction_water is not None:
                    calc = self._calculate_mole_fractions(
                        molar_ratio_des, mole_fraction_water
                    )
                    for i, param in mole_frac_param_by_index.items():
                        parameter_values.append(
                            self._make_parameter_value(param, calc[i])
                        )

                if temperature is not None:
                    parameter_values.append(
                        self._make_parameter_value(temp_param, temperature)
                    )

                property_values: List[PropertyValue] = []
                if "viscosity" in property_objs and "value_viscosity" in props:
                    viscosity_value = self._safe_float(props.get("value_viscosity"))
                    if viscosity_value is not None:
                        viscosity_value_pas = self._convert_viscosity_to_pas(
                            viscosity_value
                        )
                        viscosity_uncertainty = self._extract_uncertainty(
                            props, "viscosity", viscosity_value
                        )
                        viscosity_uncertainty_pas = (
                            self._convert_viscosity_to_pas(viscosity_uncertainty)
                            if viscosity_uncertainty is not None
                            else None
                        )
                        property_values.append(
                            self._make_property_value(
                                property_objs["viscosity"],
                                viscosity_value_pas,
                                viscosity_uncertainty_pas,
                            )
                        )
                if "conductivity" in property_objs and "value_conductivity" in props:
                    conductivity_value = self._safe_float(
                        props.get("value_conductivity")
                    )
                    if conductivity_value is not None:
                        conductivity_uncertainty = self._extract_uncertainty(
                            props, "conductivity", conductivity_value
                        )
                        property_values.append(
                            self._make_property_value(
                                property_objs["conductivity"],
                                conductivity_value,
                                conductivity_uncertainty,
                            )
                        )
                if "density" in property_objs and "value_density" in props:
                    density_value = self._safe_float(props.get("value_density"))
                    if density_value is not None:
                        density_value_kg_m3 = self._convert_density_to_kg_m3(
                            density_value
                        )
                        density_uncertainty = self._extract_uncertainty(
                            props, "density", density_value
                        )
                        density_uncertainty_kg_m3 = (
                            self._convert_density_to_kg_m3(density_uncertainty)
                            if density_uncertainty is not None
                            else None
                        )
                        property_values.append(
                            self._make_property_value(
                                property_objs["density"],
                                density_value_kg_m3,
                                density_uncertainty_kg_m3,
                            )
                        )

                if method_type == "EXPERIMENTAL":
                    method = Method.MEASURED
                    method_description = "Experimental measurement"
                else:
                    method = Method.SIMULATED
                    method_description = "Simulation measurement"

                _ensure_fluid_sample(fluid).measurement.append(
                    Measurement(
                        measurement_id=self.registry.new_id("measurement"),
                        source_doi=doi,
                        propertyValue=property_values,
                        parameterValue=parameter_values,
                        method=method,
                        method_description=method_description,
                    )
                )

    def parse(self) -> FAIRFluidsDocument:
        self._warn_if_blocks_undefined()
        self.populate_compounds()
        self.populate_fluids_and_measurements()
        return self.document


def from_cml(
    cml_path: str,
    *,
    document: FAIRFluidsDocument,
    compounds: Optional[List[Dict[str, Any]]] = None,
    viscosity_input_unit: str = "cP",
) -> FAIRFluidsDocument:
    """Convert a CML file into a :class:`FAIRFluidsDocument`.

    The ``document`` should already carry the workflow-defined citation and
    (optionally) compound blocks. Compounds may alternatively be supplied via
    ``compounds``. A ``UserWarning`` is emitted if neither citation nor
    compounds are defined.
    """
    parser = FAIRFluidsCMLParser(
        cml_path,
        compounds=compounds,
        document=document,
        viscosity_input_unit=viscosity_input_unit,
    )
    return parser.parse()


__all__ = ["FAIRFluidsCMLParser", "from_cml"]
