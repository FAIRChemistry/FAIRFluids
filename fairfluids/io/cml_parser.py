"""CML file parsing into FAIRFluids documents."""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from fairfluids.core.lib import (
    BaseUnit,
    FAIRFluidsDocument,
    Measurement,
    Method,
    Parameter,
    ParameterValue,
    Properties,
    Parameters,
    Property,
    PropertyValue,
    Sample,
    UnitDefinition,
)
from fairfluids.io.pubchem import fetch_compound_from_pubchem
from fairfluids.operations.sample_utils import _ensure_fluid_sample


class FAIRFluidsCMLParser:
    """
    Robust parser for CML files to populate the FAIRFluids data model.
    """

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
        self.compound_name_to_id = {}
        self._parse_cml_root()

    def _parse_cml_root(self):
        try:
            self.root = ET.parse(self.cml_path).getroot()
        except Exception as e:
            raise RuntimeError(f"Failed to parse CML file: {e}")

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

    def _convert_viscosity_to_pas(self, viscosity_value: float) -> float:
        """
        Convert viscosity from CML input unit to Pa·s.

        Supported units:
        - cP / centipoise
        - mPa·s / mPas
        - Pa·s / Pas
        """
        unit_normalized = (
            self.viscosity_input_unit.lower()
            .replace("·", "")
            .replace(" ", "")
            .replace("sec", "s")
        )
        if unit_normalized in {"cp", "centipoise", "mpas", "mpas"}:
            return viscosity_value / 1000.0
        if unit_normalized in {"pas", "pa*s"}:
            return viscosity_value
        raise ValueError(
            f"Unsupported viscosity_input_unit='{self.viscosity_input_unit}'. "
            "Use 'cP', 'mPa·s', or 'Pa·s'."
        )

    def populate_compounds(self):
        """
        Populate compounds in the document. If compounds are provided, use them; otherwise, try to extract from CML.
        Also builds a mapping from index to compoundID for later use. If the document already has compounds, do not add duplicates.
        Additionally, builds a list of common names (lowercase, fallback to index) for use in parameterID generation.
        """
        self.index_to_compoundID = {}
        self.compound_common_names = []
        compound_counter = 1

        # If the document already has compounds, use them
        if getattr(self.document, "compound", None) and len(self.document.compound) > 0:
            for i, compound in enumerate(self.document.compound):
                if compound.commonName:
                    self.compound_name_to_id[compound.commonName] = i
                    self.compound_common_names.append(compound.commonName.lower())
                else:
                    self.compound_common_names.append(str(i))

                # Generate consistent compound ID: compound_<common_name> or compound_<pubChemID> or compound_<number>
                if compound.compoundID is not None:
                    self.index_to_compoundID[i] = str(compound.compoundID)
                else:
                    # Generate new consistent ID
                    if compound.commonName:
                        # Clean the common name to ensure consistency with parameter IDs
                        clean_name = (
                            compound.commonName.lower()
                            .replace(" ", "")
                            .replace("-", "")
                            .replace("_", "")
                        )
                        compound_id = f"compound_{clean_name}"
                    elif compound.pubChemID is not None:
                        compound_id = f"compound_{compound.pubChemID}"
                    else:
                        compound_id = f"compound_{compound_counter}"
                        compound_counter += 1

                    # Update the compound's ID
                    compound.compoundID = compound_id
                    self.index_to_compoundID[i] = compound_id
        else:
            for i, comp in enumerate(self.compounds):
                # Check if compound has pubChemID and fetch data from PubChem if available
                pubchem_id = comp.get("pubChemID")
                if pubchem_id is not None:
                    # Ensure pubchem_id is an integer
                    try:
                        pubchem_id = int(pubchem_id)
                    except (ValueError, TypeError):
                        print(
                            f"Warning: Invalid pubChemID format: {pubchem_id}, skipping PubChem fetch"
                        )
                        pubchem_id = None

                    if pubchem_id is not None:
                        print(
                            f"Fetching compound data from PubChem for CID {pubchem_id}..."
                        )
                        fetched_data = fetch_compound_from_pubchem(pubchem_id)
                        if fetched_data is not None:
                            # Merge fetched data with provided data, preferring fetched data
                            # but keeping any additional fields from provided data
                            merged_data = comp.copy()
                            merged_data.update(fetched_data)
                            # Ensure pubChemID is preserved
                            merged_data["pubChemID"] = pubchem_id
                            comp = merged_data
                            print(
                                f"Successfully fetched and merged data for CID {pubchem_id}"
                            )
                        else:
                            print(
                                f"Warning: Failed to fetch data from PubChem for CID {pubchem_id}, using provided data"
                            )

                compound = self.document.add_to_compound(**comp)
                if compound.commonName:
                    self.compound_name_to_id[compound.commonName] = i
                    self.compound_common_names.append(compound.commonName.lower())
                else:
                    self.compound_common_names.append(str(i))

                # Generate consistent compound ID: compound_<common_name> or compound_<pubChemID> or compound_<number>
                if compound.compoundID is not None:
                    self.index_to_compoundID[i] = str(compound.compoundID)
                else:
                    # Generate new consistent ID
                    if compound.commonName:
                        # Clean the common name to ensure consistency with parameter IDs
                        clean_name = (
                            compound.commonName.lower()
                            .replace(" ", "")
                            .replace("-", "")
                            .replace("_", "")
                        )
                        compound_id = f"compound_{clean_name}"
                    elif compound.pubChemID is not None:
                        compound_id = f"compound_{compound.pubChemID}"
                    else:
                        compound_id = f"compound_{compound_counter}"
                        compound_counter += 1

                    # Update the compound's ID
                    compound.compoundID = compound_id
                    self.index_to_compoundID[i] = compound_id

    def _extract_experiments(self) -> List[ET.Element]:
        return self.root.findall(f".//{self.ns}module[@dictRef='des:experiment']")

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
        """
        Extract both experiment and simulation modules, returning a list of (element, method_type) tuples.
        """
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

    def _make_unit(self, name: str) -> UnitDefinition:
        if name == "K":
            return UnitDefinition(
                unitID="K",
                name="kelvin",
                base_units=[
                    BaseUnit(
                        kind="temperature",
                        exponent=1,
                        multiplier=1.0,
                        scale=0.0,
                    )
                ],
            )
        if name == "Pa·s":
            return UnitDefinition(
                unitID="Pa·s",
                name="Pascal second",
                base_units=[
                    BaseUnit(kind="pressure", exponent=1, multiplier=1.0, scale=0.0),
                    BaseUnit(kind="time", exponent=1, multiplier=1.0, scale=0.0),
                ],
            )
        if name == "mPa·s":
            return UnitDefinition(
                unitID="mPa·s",
                name="milliPascal second",
                base_units=[
                    BaseUnit(kind="pressure", exponent=1, multiplier=1.0, scale=-3.0),
                    BaseUnit(kind="time", exponent=1, multiplier=1.0, scale=0.0),
                ],
            )
        if name == "m2/s":
            return UnitDefinition(
                unitID="m2/s",
                name="square meter per second",
                base_units=[
                    BaseUnit(kind="length", exponent=2, multiplier=1.0, scale=0.0),
                    BaseUnit(kind="time", exponent=-1, multiplier=1.0, scale=0.0),
                ],
            )
        if name == "1":
            return UnitDefinition(
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
            )
        return UnitDefinition(unitID=name, name=name, base_units=[])

    def _make_property(self, exp_id: str, property_type: str = "viscosity") -> Property:
        # Extend for other property types as needed
        if property_type == "viscosity":
            return Property(
                propertyID="viscosity",
                properties=Properties.VISCOSITY,
                unit=self._make_unit("Pa·s"),
            )
        if property_type == "kinematic_viscosity":
            return Property(
                propertyID="kinematic_viscosity",
                properties=Properties.KINEMATIC_VISCOSITY,
                unit=self._make_unit("m2/s"),
            )
        if property_type == "conductivity":
            return Property(
                propertyID="conductivity",
                properties=Properties.THERMAL_CONDUCTIVITY,
                unit=self._make_unit("S/m"),
            )
        if property_type == "density":
            return Property(
                propertyID="density",
                properties=Properties.DENSITY,
                unit=self._make_unit("kg/m3"),
            )
        # Add more property types as needed
        raise NotImplementedError(f"Property type {property_type} not implemented.")

    def _make_parameter(
        self, name: str, value: str, idx: int, compound_index: Optional[int] = None
    ) -> Parameter:
        if name == "temperature":
            return Parameter(
                parameterID="parameter_temperature",
                parameters=Parameters.TEMPERATURE,
                unit=self._make_unit("K"),
                associated_compounds=[],
            )
        if name == "mole_fraction_of_water":
            compound_id = (
                self.index_to_compoundID.get(compound_index, str(compound_index))
                if compound_index is not None
                else None
            )
            return Parameter(
                parameterID="parameter_mole_fraction_water",
                parameters=Parameters.MOLE_FRACTION,
                unit=self._make_unit("1"),
                associated_compounds=[compound_id] if compound_id else [],
            )
        if name == "molar_ratio_of_DES":
            compound_id = (
                self.index_to_compoundID.get(compound_index, str(compound_index))
                if compound_index is not None
                else None
            )
            return Parameter(
                parameterID="parameter_molar_ratio_des",
                parameters=Parameters.AMOUNT_RATIO_OF_SOLUTE_TO_SOLVENT,
                unit=self._make_unit("1"),
                associated_compounds=[compound_id] if compound_id else [],
            )
        # Add more parameter types as needed
        compound_id = (
            self.index_to_compoundID.get(compound_index, str(compound_index))
            if compound_index is not None
            else None
        )
        return Parameter(
            parameterID=f"parameter_{name}_{idx}",
            parameters=None,
            unit=self._make_unit("1"),
            associated_compounds=[compound_id] if compound_id else [],
        )

    def _make_property_value(
        self, property_type: str, value: str, uncertainty: Optional[str]
    ) -> PropertyValue:
        safe_uncertainty = self._safe_float(uncertainty)
        return PropertyValue(
            propertyID=property_type,
            propValue=float(value),
            uncertainty=safe_uncertainty,
        )

    def _extract_uncertainty(
        self, props: Dict[str, str], property_name: str, property_value: float
    ) -> Optional[float]:
        """
        Extract uncertainty for a property from common CML key variants.

        Supports absolute uncertainty keys (e.g. error_viscosity) and relative forms
        (e.g. relative_error_viscosity / rel_error_viscosity) including percentage
        strings such as "0.5%".
        """
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

    def _make_parameter_value(self, param: Parameter, value: str) -> ParameterValue:
        return ParameterValue(
            parameterID=param.parameterID, paramValue=float(value), uncertainty=None
        )

    def _calculate_mole_fractions(self, molar_ratio: float, water_fraction: float):
        """
        Calculate mole fractions for all three components based on DES molar ratio and water fraction.
        Returns (x1, x2, x3) for component 1, 2, and water.
        Ensures fractions sum to exactly 1.0 by normalizing to eliminate floating point imprecision.
        """
        r = self._safe_float(molar_ratio)
        w = self._safe_float(water_fraction)
        if r is None or w is None:
            raise ValueError(
                f"Cannot calculate mole fractions from invalid inputs r={molar_ratio}, w={water_fraction}"
            )
        if r < 0:
            raise ValueError(f"Molar ratio must be >= 0, got {r}")
        if not 0.0 <= w <= 1.0:
            raise ValueError(f"Water mole fraction must be in [0, 1], got {w}")
        x3 = w
        x1 = (r * (1 - x3)) / (r + 1)
        x2 = (1 - x3) - x1

        # Normalize to ensure exact sum of 1.0 and eliminate floating point imprecision
        total = x1 + x2 + x3
        x1_normalized = x1 / total
        x2_normalized = x2 / total
        x3_normalized = x3 / total

        # Round to a reasonable precision to avoid floating point artifacts
        # Using 12 decimal places should be sufficient for most applications
        precision = 12
        x1_final = round(x1_normalized, precision)
        x2_final = round(x2_normalized, precision)
        x3_final = round(x3_normalized, precision)

        # Verify the sum is exactly 1.0 (within floating point precision)
        sum_check = x1_final + x2_final + x3_final
        if abs(sum_check - 1.0) > 1e-10:
            # If rounding caused issues, adjust the largest component
            diff = 1.0 - sum_check
            if abs(x3_final) >= abs(x2_final) and abs(x3_final) >= abs(x1_final):
                x3_final += diff
            elif abs(x2_final) >= abs(x1_final):
                x2_final += diff
            else:
                x1_final += diff

        return x1_final, x2_final, x3_final

    def populate_fluids_and_measurements(self):
        """
        Populate multiple fluids based on unique compositions from CML experiments and simulations.
        Each unique composition gets its own fluid block with only the compounds present in that composition.
        """
        measurement_modules = self._extract_measurement_modules()

        # Scan all modules to find all unique property types
        property_types = set()
        for exp, _ in measurement_modules:
            props = self._extract_properties(exp)
            if "value_viscosity" in props:
                property_types.add("viscosity")
            if "value_conductivity" in props:
                property_types.add("conductivity")
            if "value_density" in props:
                property_types.add("density")

        # Build property objects for all found types
        property_objs = [
            self._make_property(pt, property_type=pt) for pt in property_types
        ]

        # Group measurements by composition (unique mole fraction combinations)
        composition_groups = {}

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

            # Create composition key (rounded to 3 decimal places to group similar compositions)
            composition_key = (round(x1, 3), round(x2, 3), round(x3, 3))

            if composition_key not in composition_groups:
                composition_groups[composition_key] = []

            composition_groups[composition_key].append(
                (exp, method_type, props, params)
            )

        print(f"Found {len(composition_groups)} unique compositions")

        # Create a separate fluid for each unique composition
        for composition_key, measurements in composition_groups.items():
            x1, x2, x3 = composition_key

            # Determine which compounds are present (non-zero mole fractions)
            present_compounds = []
            present_compound_indices = []

            for i, mole_frac in enumerate([x1, x2, x3]):
                if mole_frac > 0:  # Only include compounds with non-zero mole fractions
                    compound_id = self.index_to_compoundID.get(i, str(i))
                    present_compounds.append(compound_id)
                    present_compound_indices.append(i)

            print(f"Composition {composition_key}: compounds {present_compounds}")

            # Create parameters only for present compounds
            parameters = []

            # Add mole fraction parameters for present compounds
            for i in present_compound_indices:
                compound_id = self.index_to_compoundID.get(i, str(i))
                if i < len(self.compound_common_names):
                    common_name = self.compound_common_names[i]
                else:
                    common_name = str(i)

                # Clean the common name to ensure consistency with compound IDs
                clean_name = (
                    common_name.lower()
                    .replace(" ", "")
                    .replace("-", "")
                    .replace("_", "")
                )

                param = Parameter(
                    parameterID=f"parameter_mole_fraction_{clean_name}",
                    parameters=Parameters.MOLE_FRACTION,
                    unit=self._make_unit("1"),
                    associated_compounds=[compound_id],
                )
                parameters.append(param)

            # Add temperature parameter (always present)
            temp_param = self._make_parameter(
                "temperature", "298.15", len(parameters) + 1
            )
            parameters.append(temp_param)

            # Create the fluid for this composition
            sample = Sample(
                sample_id=f"sample_{uuid.uuid4()}",
                associated_compounds=present_compounds,
                measurement=[],
            )
            fluid = self.document.add_to_fluid(
                compounds=present_compounds,
                property=property_objs,
                parameter=parameters,
                sample=sample,
            )

            # Add all measurements for this composition
            for exp, method_type, props, params in measurements:
                doi = props.get(
                    "DOI"
                )  # Use None if DOI is missing (consistent with Optional[str] type)
                temperature = self._safe_float(params.get("temperature"))
                mole_fraction_water = self._safe_float(
                    params.get("mole_fraction_of_water")
                )
                molar_ratio_des = self._safe_float(params.get("molar_ratio_of_DES"))

                parameter_values = []

                # Add mole fraction parameter values for present compounds
                if molar_ratio_des is not None and mole_fraction_water is not None:
                    calc_x1, calc_x2, calc_x3 = self._calculate_mole_fractions(
                        molar_ratio_des, mole_fraction_water
                    )
                    mole_fracs = [calc_x1, calc_x2, calc_x3]

                    for i in present_compound_indices:
                        if i < len(self.compound_common_names):
                            common_name = self.compound_common_names[i]
                        else:
                            common_name = str(i)

                        clean_name = (
                            common_name.lower()
                            .replace(" ", "")
                            .replace("-", "")
                            .replace("_", "")
                        )

                        param_id = f"parameter_mole_fraction_{clean_name}"
                        param = next(
                            (p for p in parameters if p.parameterID == param_id),
                            None,
                        )
                        if param:
                            parameter_values.append(
                                self._make_parameter_value(param, str(mole_fracs[i]))
                            )

                # Add temperature parameter value
                if temperature is not None:
                    temp_param = next(
                        (
                            p
                            for p in parameters
                            if p.parameterID == "parameter_temperature"
                        ),
                        None,
                    )
                    if temp_param:
                        parameter_values.append(
                            self._make_parameter_value(temp_param, str(temperature))
                        )

                # Collect property values for all present property types
                property_values = []
                if "value_viscosity" in props:
                    # CML viscosity is typically reported in cP (== mPa·s); we store Pa·s.
                    # Both the value and the uncertainty need to be converted using the same scaling factor
                    viscosity_value = self._safe_float(props.get("value_viscosity"))
                    if viscosity_value is not None:
                        viscosity_value_pas = self._convert_viscosity_to_pas(
                            viscosity_value
                        )
                        viscosity_uncertainty = self._extract_uncertainty(
                            props, "viscosity", viscosity_value
                        )
                        viscosity_uncertainty_pas = None
                        if viscosity_uncertainty is not None:
                            # Apply the same conversion to the uncertainty as to the value
                            viscosity_uncertainty_pas = self._convert_viscosity_to_pas(
                                viscosity_uncertainty
                            )
                        property_values.append(
                            PropertyValue(
                                propertyID="viscosity",
                                propValue=viscosity_value_pas,
                                uncertainty=viscosity_uncertainty_pas,
                            )
                        )
                if "value_conductivity" in props:
                    conductivity_value = self._safe_float(
                        props.get("value_conductivity")
                    )
                    if conductivity_value is not None:
                        conductivity_uncertainty = self._extract_uncertainty(
                            props, "conductivity", conductivity_value
                        )
                        property_values.append(
                            self._make_property_value(
                                "conductivity",
                                str(conductivity_value),
                                (
                                    str(conductivity_uncertainty)
                                    if conductivity_uncertainty is not None
                                    else None
                                ),
                            )
                        )
                if "value_density" in props:
                    density_value = self._safe_float(props.get("value_density"))
                    if density_value is not None:
                        density_uncertainty = self._extract_uncertainty(
                            props, "density", density_value
                        )
                        property_values.append(
                            self._make_property_value(
                                "density",
                                str(density_value),
                                (
                                    str(density_uncertainty)
                                    if density_uncertainty is not None
                                    else None
                                ),
                            )
                        )

                # Set method based on method_type
                if method_type == "EXPERIMENTAL":
                    method = Method.MEASURED
                    method_description = "Experimental measurement"
                else:
                    method = Method.SIMULATED
                    method_description = "Simulation measurement"

                _ensure_fluid_sample(fluid).measurement.append(
                    Measurement(
                        measurement_id=str(uuid.uuid4()),
                        source_doi=doi,
                        propertyValue=property_values,
                        parameterValue=parameter_values,
                        method=method,
                        method_description=method_description,
                    )
                )

    def parse(self) -> FAIRFluidsDocument:
        self.populate_compounds()
        self.populate_fluids_and_measurements()
        return self.document


__all__ = ["FAIRFluidsCMLParser"]
