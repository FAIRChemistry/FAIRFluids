# Import the FAIRFluids models
from .lib import (
    FAIRFluidsDocument,
    Version,
    Citation,
    Author,
    Compound,
    Fluid,
    Property,
    PropertyValue,
    Parameter,
    ParameterValue,
    Measurement,
    UnitDefinition,
    BaseUnit,
    Method,
    Properties,
    Parameters,
)
from typing import Optional, List, Dict, Any, Tuple, Union
import xml.etree.ElementTree as ET
import requests
import numpy as np
import uuid
from collections import defaultdict
import pandas as pd


def _is_compositional_parameter(param_name_lower: str) -> bool:
    """
    Check if a parameter name represents a compositional parameter.

    Args:
        param_name_lower: Lowercase parameter name

    Returns:
        True if the parameter is compositional, False otherwise
    """
    compositional_keywords = [
        "mole fraction",
        "mass fraction",
        "volume fraction",
        "molality",
        "molarity",
        "amount concentration",
        "amount ratio",
        "mass ratio",
        "volume ratio",
        "ratio of amount",
        "ratio of mass",
        "ratio of component",
        "amount density",
        "amount of solute",
        "mass of solute",
        "volume of solute",
        "solute to solvent",
        "solute to solution",
        "component to other component",
        "component to mass",
        "component mass to volume",
    ]

    return any(keyword in param_name_lower for keyword in compositional_keywords)


def filter_fluid_compounds_by_mole_fractions(fluid):
    """
    Filter compounds and their parameters from a fluid if they have zero mole fractions
    in ALL measurements AND no other compositional parameters are present.

    This function:
    1. Checks each compound's compositional parameters (mole fraction, mass fraction,
       molality, volume fraction, ratios, etc.) across all measurements
    2. Removes compounds that have 0.0 mole fractions in ALL measurements AND no other
       compositional parameters present
    3. Removes associated parameter definitions
    4. Removes parameter values from all measurements

    Args:
        fluid: A Fluid object with measurements

    Returns:
        The fluid object with filtered compounds and parameters
    """
    if not fluid.measurement:
        return fluid

    print(
        f"=== Filtering Fluid with {len(fluid.compounds)} compounds and {len(fluid.measurement)} measurements ==="
    )

    # Track which compounds should be kept (non-zero mole fractions OR other compositional params present)
    compounds_to_keep = set()

    # Build a quick lookup for parameter definitions by ID once
    parameter_lookup = {
        param.parameterID: param
        for param in fluid.parameter
        if getattr(param, "parameterID", None)
    }

    # Check each compound's compositional parameters across all measurements
    for compound_id in fluid.compounds:
        has_non_zero_mole_fraction = False
        has_compositional_signal = False  # any compositional parameter present
        compositional_param_types = []  # track which types we found

        # Check all measurements for this compound
        for measurement in fluid.measurement:
            for param_value in measurement.parameterValue:
                # Find the parameter definition for this parameter value
                param_def = parameter_lookup.get(param_value.parameterID)

                # Check if this is a compositional parameter for this compound
                if (
                    param_def
                    and compound_id in param_def.associated_compounds
                    and hasattr(param_def, "parameter")
                    and param_def.parameter is not None
                ):

                    # Normalize parameter name
                    param_name = str(param_def.parameter)
                    if hasattr(param_def.parameter, "value"):
                        param_name = param_def.parameter.value
                    param_name_lower = param_name.lower()

                    # Check if this is any compositional parameter
                    if _is_compositional_parameter(param_name_lower):
                        has_compositional_signal = True

                        # Track the type for reporting
                        if "mole fraction" in param_name_lower:
                            compositional_param_types.append("mole fraction")
                        elif "mass fraction" in param_name_lower:
                            compositional_param_types.append("mass fraction")
                        elif "molality" in param_name_lower:
                            compositional_param_types.append("molality")
                        elif "volume fraction" in param_name_lower:
                            compositional_param_types.append("volume fraction")
                        elif "ratio" in param_name_lower:
                            compositional_param_types.append("ratio")
                        elif (
                            "molarity" in param_name_lower
                            or "amount concentration" in param_name_lower
                        ):
                            compositional_param_types.append("molarity/concentration")
                        else:
                            compositional_param_types.append("compositional")

                        # Check for non-zero mole fraction specifically
                        if "mole fraction" in param_name_lower:
                            if (
                                param_value.paramValue is not None
                                and param_value.paramValue > 0
                            ):
                                has_non_zero_mole_fraction = True
                                break
                        # For other compositional parameters, just note their presence
                        # (we don't break to continue looking for mole fractions)

            if has_non_zero_mole_fraction:
                break

        if has_non_zero_mole_fraction or has_compositional_signal:
            compounds_to_keep.add(compound_id)
            # Create descriptive reason
            if has_non_zero_mole_fraction:
                reason = "non-zero mole fractions"
            else:
                unique_types = list(set(compositional_param_types))
                if len(unique_types) == 1:
                    reason = f"composition parameter present ({unique_types[0]})"
                else:
                    reason = f"composition parameters present ({', '.join(unique_types[:3])}{'...' if len(unique_types) > 3 else ''})"
            print(f"✅ Keeping compound: {compound_id} ({reason})")
        else:
            print(
                f"❌ Removing compound: {compound_id} (no compositional parameters in measurements)"
            )

    # Update compounds list
    original_compounds = fluid.compounds.copy()
    fluid.compounds = [comp for comp in original_compounds if comp in compounds_to_keep]

    # Remove parameter definitions for compounds that are not kept
    original_parameters = fluid.parameter.copy()
    fluid.parameter = [
        param
        for param in original_parameters
        if (
            not hasattr(param, "associated_compounds")
            or not param.associated_compounds
            or any(comp in compounds_to_keep for comp in param.associated_compounds)
        )
    ]

    # Remove parameter values from measurements for compounds that are not kept
    for measurement in fluid.measurement:
        original_param_values = measurement.parameterValue.copy()
        measurement.parameterValue = []

        for pv in original_param_values:
            # Find the parameter definition for this parameter value
            param_def = None
            for param in fluid.parameter:
                if param.parameterID == pv.parameterID:
                    param_def = param
                    break

            # Keep the parameter value if:
            # 1. It's not associated with any compound (like temperature)
            # 2. It's associated with a compound that we're keeping
            if (
                not param_def
                or not hasattr(param_def, "associated_compounds")
                or not param_def.associated_compounds
                or any(
                    comp in compounds_to_keep for comp in param_def.associated_compounds
                )
            ):
                measurement.parameterValue.append(pv)

    print(
        f"Final result: {len(fluid.compounds)} compounds, {len(fluid.parameter)} parameters"
    )
    return fluid


class FAIRFluidsCMLParser:
    """
    Robust parser for CML files to populate the FAIRFluids data model.
    """

    def __init__(
        self,
        cml_path: str,
        compounds: Optional[List[Dict[str, Any]]] = None,
        document: Optional[FAIRFluidsDocument] = None,
    ):
        self.cml_path = cml_path
        self.compounds = compounds or []
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
        return self.root.findall(
            ".//{http://www.xml-cml.org/schema}module[@dictRef='des:experiment']"
        )

    def _extract_properties(self, experiment: ET.Element) -> Dict[str, str]:
        properties = {}
        property_list = experiment.find(
            ".//{http://www.xml-cml.org/schema}propertyList"
        )
        if property_list is not None:
            for prop in property_list:
                dict_ref = prop.get("dictRef")
                if dict_ref:
                    prop_type = dict_ref.split(":")[-1]
                    scalar = prop.find(".//{http://www.xml-cml.org/schema}scalar")
                    if scalar is not None:
                        properties[prop_type] = scalar.text
        return properties

    def _extract_parameters(self, experiment: ET.Element) -> Dict[str, str]:
        parameters = {}
        param_list = experiment.find(".//{http://www.xml-cml.org/schema}parameterList")
        if param_list is not None:
            for param in param_list:
                dict_ref = param.get("dictRef")
                if dict_ref:
                    param_type = dict_ref.split(":")[-1]
                    scalar = param.find(".//{http://www.xml-cml.org/schema}scalar")
                    if scalar is not None:
                        parameters[param_type] = scalar.text
        return parameters

    def _extract_measurement_modules(self) -> List[tuple]:
        """
        Extract both experiment and simulation modules, returning a list of (element, method_type) tuples.
        """
        ns = "{http://www.xml-cml.org/schema}"
        experiments = [
            (el, "EXPERIMENTAL")
            for el in self.root.findall(f".//{ns}module[@dictRef='des:experiment']")
        ]
        simulations = [
            (el, "SIMULATION")
            for el in self.root.findall(f".//{ns}module[@dictRef='des:simulation']")
        ]
        return experiments + simulations

    def _make_unit(self, name: str) -> UnitDefinition:
        if name == "K":
            return UnitDefinition(
                unitID="K",
                name="kelvin",
                base_units=[BaseUnit(symbol="K", power=1, multiplier=1.0, scale=0.0)],
            )
        if name == "Pa·s":
            return UnitDefinition(unitID="Pa·s", name="Pascal second", base_units=[])
        if name == "mPa·s":
            return UnitDefinition(
                unitID="mPa·s", name="milliPascal second", base_units=[]
            )
        if name == "m2/s":
            return UnitDefinition(
                unitID="m2/s",
                name="square meter per second",
                base_units=[
                    BaseUnit(symbol="m2/s", power=1, multiplier=1.0, scale=0.0)
                ],
            )
        if name == "1":
            return UnitDefinition(
                unitID="1",
                name="dimensionless",
                base_units=[BaseUnit(symbol="1", power=1, multiplier=1.0, scale=0.0)],
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
                parameter=Parameters.TEMPERATURE,
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
                parameter=Parameters.MOLE_FRACTION,
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
                parameter=Parameters.AMOUNT_RATIO_OF_SOLUTE_TO_SOLVENT,
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
            parameter=None,
            unit=self._make_unit("1"),
            associated_compounds=[compound_id] if compound_id else [],
        )

    def _make_property_value(
        self, property_type: str, value: str, uncertainty: Optional[str]
    ) -> PropertyValue:
        return PropertyValue(
            propertyID=property_type,
            propValue=float(value),
            uncertainty=None if uncertainty in (None, "NG") else float(uncertainty),
        )

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
        r = molar_ratio
        w = water_fraction
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

            mole_fraction_water = params.get("mole_fraction_of_water")
            molar_ratio_des = params.get("molar_ratio_of_DES")

            if molar_ratio_des is not None and mole_fraction_water is not None:
                r = float(molar_ratio_des)
                w = float(mole_fraction_water)
                x1, x2, x3 = self._calculate_mole_fractions(r, w)

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
                    parameter=Parameters.MOLE_FRACTION,
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
            fluid = self.document.add_to_fluid(
                compounds=present_compounds,
                property=property_objs,
                parameter=parameters,
                measurement=[],
            )

            # Add all measurements for this composition
            for exp, method_type, props, params in measurements:
                exp_id = props.get("ID", "unknown")
                doi = props.get(
                    "DOI"
                )  # Use None if DOI is missing (consistent with Optional[str] type)
                temperature = params.get("temperature")
                mole_fraction_water = params.get("mole_fraction_of_water")
                molar_ratio_des = params.get("molar_ratio_of_DES")

                parameter_values = []

                # Add mole fraction parameter values for present compounds
                if molar_ratio_des is not None and mole_fraction_water is not None:
                    r = float(molar_ratio_des)
                    w = float(mole_fraction_water)
                    calc_x1, calc_x2, calc_x3 = self._calculate_mole_fractions(r, w)
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
                            self._make_parameter_value(temp_param, temperature)
                        )

                # Collect property values for all present property types
                property_values = []
                if "value_viscosity" in props:
                    # Convert from mPa·s to Pa·s (divide by 1000)
                    viscosity_value_pas = float(props["value_viscosity"]) / 1000.0
                    viscosity_uncertainty_pas = None
                    if props.get("error_viscosity") not in (None, "NG"):
                        viscosity_uncertainty_pas = (
                            float(props.get("error_viscosity")) / 1000.0
                        )
                    property_values.append(
                        PropertyValue(
                            propertyID="viscosity",
                            propValue=viscosity_value_pas,
                            uncertainty=viscosity_uncertainty_pas,
                        )
                    )
                if "value_conductivity" in props:
                    property_values.append(
                        self._make_property_value(
                            "conductivity",
                            props["value_conductivity"],
                            props.get("error_conductivity"),
                        )
                    )
                if "value_density" in props:
                    property_values.append(
                        self._make_property_value(
                            "density",
                            props["value_density"],
                            props.get("error_density"),
                        )
                    )

                # Set method based on method_type
                if method_type == "EXPERIMENTAL":
                    method = Method.MEASURED
                    method_description = "Experimental measurement"
                else:
                    method = Method.SIMULATED
                    method_description = "Simulation measurement"

                fluid.add_to_measurement(
                    measurement_id=str(uuid.uuid4()),
                    source_doi=doi,
                    propertyValue=property_values,
                    parameterValue=parameter_values,
                    method=method,
                    method_description=method_description,
                )

    def parse(self) -> FAIRFluidsDocument:
        self.populate_compounds()
        self.populate_fluids_and_measurements()
        return self.document


def fetch_compound_from_pubchem(pubchem_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch compound information from PubChem using the pubChemID.

    Args:
        pubchem_id: The PubChem CID

    Returns:
        Dictionary with compound information or None if not found
    """
    try:
        # Get detailed compound info using the CID
        # Note: PubChem returns 'SMILES' not 'CanonicalSMILES', and 'IsomericSMILES' may not be available
        info_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{pubchem_id}/property/IUPACName,MolecularFormula,MolecularWeight,SMILES,InChI,InChIKey,Title/JSON"
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
                    "smiles_code": info_data.get(
                        "SMILES"
                    ),  # PubChem returns 'SMILES' not 'CanonicalSMILES'
                    "molar_weigth": info_data.get("MolecularWeight"),
                    "standard_InChI": info_data.get("InChI"),
                    "standard_InChI_key": info_data.get("InChIKey"),
                    "SELFIE": None,
                    "sigman_profile": None,
                }
    except Exception as e:
        print(f"Error fetching compound from PubChem: {e}")
        return None

    return None


def combine_compounds(
    document: FAIRFluidsDocument,
    old_molecules: List[int],
    new_molecule: int,
) -> FAIRFluidsDocument:
    """
    Combine separate compounds (e.g., choline chloride ions) into a single compound.

    This function:
    1. Fetches information for the new combined molecule from PubChem
    2. Removes the old compounds from the document
    3. Adds the new compound to the document
    4. Updates all fluid references to use the new compound
    5. Merges parameter values (e.g., mole fractions) for the old compounds
    6. Removes old parameter definitions

    Args:
        document: The FAIRFluidsDocument to modify
        old_molecules: List of pubChemIDs for the old compounds to be combined
        new_molecule: The pubChemID for the new combined compound

    Returns:
        The modified FAIRFluidsDocument
    """
    print(f"=== Combining Compounds ===")
    print(f"Old molecules (pubChemIDs): {old_molecules}")
    print(f"New molecule (pubChemID): {new_molecule}")

    # Fetch compound data from PubChem
    new_compound_data = fetch_compound_from_pubchem(new_molecule)
    if new_compound_data is None:
        raise ValueError(
            f"Could not fetch compound data from PubChem for CID {new_molecule}"
        )

    # Find old compounds to remove
    old_compound_ids = []
    old_compound_indices = []
    for i, compound in enumerate(document.compound):
        if compound.pubChemID in old_molecules:
            old_compound_ids.append(compound.compoundID)
            old_compound_indices.append(i)
            print(
                f"Found old compound to remove: {compound.compoundID} (pubChemID: {compound.pubChemID})"
            )

    if len(old_compound_ids) == 0:
        print("Warning: No old compounds found to remove")
        return document

    # Create new compound
    # Clean the common name to generate a consistent compoundID
    clean_name = (
        new_compound_data["commonName"]
        .lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
        .replace(".", "")
    )
    new_compound_id = f"compound_{clean_name}"

    new_compound = document.add_to_compound(
        compoundID=new_compound_id, **new_compound_data
    )

    print(f"Created new compound: {new_compound.compoundID}")

    # Remove old compounds
    for idx in sorted(old_compound_indices, reverse=True):
        del document.compound[idx]

    # For each fluid, update compounds list and parameter values
    for fluid in document.fluid:
        # Update compounds list
        compounds_list = list(fluid.compounds)
        updated_compounds = []
        old_compound_present = False

        for comp_id in compounds_list:
            if comp_id in old_compound_ids:
                old_compound_present = True
            else:
                updated_compounds.append(comp_id)

        # If any old compounds were in the fluid, replace with new compound
        if old_compound_present:
            updated_compounds.append(new_compound_id)
            fluid.compounds = updated_compounds
            print(f"Updated fluid compounds: {fluid.compounds}")

        # Find parameters associated with old compounds
        old_param_ids = []
        for param in fluid.parameter:
            if any(comp in old_compound_ids for comp in param.associated_compounds):
                old_param_ids.append(param.parameterID)

        # Remove old parameter definitions
        fluid.parameter = [
            p for p in fluid.parameter if p.parameterID not in old_param_ids
        ]

        # Add new parameter for the combined compound
        # Check if we need to add a mole fraction parameter
        if old_param_ids:  # If there were old parameters, add new one
            # Get the common name for parameter ID generation
            clean_param_name = (
                new_compound_data["commonName"]
                .lower()
                .replace(" ", "")
                .replace("-", "")
                .replace("_", "")
                .replace(".", "")
            )

            new_param_id = f"parameter_mole_fraction_{clean_param_name}"

            # Check if this parameter already exists
            param_exists = any(p.parameterID == new_param_id for p in fluid.parameter)

            if not param_exists:
                new_param = Parameter(
                    parameterID=new_param_id,
                    parameter=Parameters.MOLE_FRACTION,
                    unit=UnitDefinition(
                        unitID="1",
                        name="dimensionless",
                        base_units=[
                            BaseUnit(symbol="1", power=1, multiplier=1.0, scale=0.0)
                        ],
                    ),
                    associated_compounds=[new_compound_id],
                )
                fluid.parameter.append(new_param)
                print(f"Added new parameter: {new_param_id}")

        # Update measurements
        for measurement in fluid.measurement:
            # Find parameter values for old compounds
            old_param_values = {}
            param_values_to_keep = []

            # Get the common name for the new parameter ID
            clean_param_name = (
                new_compound_data["commonName"]
                .lower()
                .replace(" ", "")
                .replace("-", "")
                .replace("_", "")
                .replace(".", "")
            )
            new_param_id = f"parameter_mole_fraction_{clean_param_name}"

            combined_value = 0.0
            has_old_values = False

            for pv in measurement.parameterValue:
                if pv.parameterID in old_param_ids:
                    combined_value += pv.paramValue or 0.0
                    has_old_values = True
                else:
                    param_values_to_keep.append(pv)

            # If we found old parameter values, add the combined one
            if has_old_values:
                # Find the parameter definition for the new parameter
                new_param = next(
                    (p for p in fluid.parameter if p.parameterID == new_param_id), None
                )

                if new_param:
                    new_param_value = ParameterValue(
                        parameterID=new_param_id,
                        paramValue=combined_value,
                        uncertainty=None,
                    )
                    param_values_to_keep.append(new_param_value)
                    print(
                        f"Combined mole fractions: {old_param_ids} -> {combined_value}"
                    )

            measurement.parameterValue = param_values_to_keep

    print("=== Compound Combination Complete ===")
    return document


def calculate_ratio_of_solvent(
    doc: FAIRFluidsDocument,
    parameter_id_1: str,
    parameter_id_2: str,
    name: str,
    compound_id_1: Optional[str] = None,
    compound_id_2: Optional[str] = None,
    precision: Optional[int] = None,
) -> FAIRFluidsDocument:
    """
    Calculate and add solvent ratio parameter for binary solvents.

    This function adds a new parameter representing the ratio of two components in a binary solvent
    (e.g., glycerol/choline chloride ratio in glyceline). For each measurement, it calculates the
    ratio from existing mole fraction parameters and adds it as a new parameterValue.

    Args:
        doc: The FAIRFluidsDocument to modify
        parameter_id_1: Parameter ID for the first component (e.g., "parameter_mole_fraction_glycerol")
        parameter_id_2: Parameter ID for the second component (e.g., "parameter_mole_fraction_cholinechloride")
        name: Name for the new ratio parameter (e.g., "glyceline")
        compound_id_1: Compound ID for the first component (optional)
        compound_id_2: Compound ID for the second component (optional)
        precision: Number of decimal places to round the ratio to (optional). If None, no rounding is applied.

    Returns:
        The modified FAIRFluidsDocument

    Example:
        doc = calculate_ratio_of_solvent(
            doc=fairfluids_document,
            parameter_id_1="parameter_mole_fraction_glycerol",
            parameter_id_2="parameter_mole_fraction_cholinechloride",
            name="glyceline",
            compound_id_1="compound_glycerol",
            compound_id_2="compound_cholinechloride",
            precision=2  # Round to 2 decimal places
        )
    """
    print(f"=== Calculating Solvent Ratio: {name} ===")
    print(f"Component 1: {parameter_id_1}")
    print(f"Component 2: {parameter_id_2}")
    print(f"Processing {len(doc.fluid)} fluids")

    # Create parameter ID for the new ratio parameter
    new_param_id = f"parameter_solvent_ratio_{name}"

    # Create associated_compounds list
    associated_compounds_list = []
    if compound_id_1:
        associated_compounds_list.append(compound_id_1)
    if compound_id_2:
        associated_compounds_list.append(compound_id_2)

    # Process each fluid in the document
    for fluid_idx, fluid in enumerate(doc.fluid):
        print(f"\n--- Processing Fluid {fluid_idx + 1} ---")

        # Check if both required compounds are present in the fluid
        compounds_in_fluid = set(fluid.compounds)

        # Determine if we should process this fluid
        should_process = True
        if compound_id_1 and compound_id_1 not in compounds_in_fluid:
            print(
                f"Skipping fluid {fluid_idx + 1}: {compound_id_1} not in compounds list"
            )
            should_process = False
        if compound_id_2 and compound_id_2 not in compounds_in_fluid:
            print(
                f"Skipping fluid {fluid_idx + 1}: {compound_id_2} not in compounds list"
            )
            should_process = False

        if not should_process:
            continue

        # Check if parameter already exists in this fluid
        param_exists = any(p.parameterID == new_param_id for p in fluid.parameter)

        if not param_exists:
            # Create new parameter with associated_compounds
            new_param = Parameter(
                parameterID=new_param_id,
                parameter=Parameters.SOLVENT_AMOUNT_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT,
                unit=UnitDefinition(
                    unitID="1",
                    name="dimensionless",
                    base_units=[
                        BaseUnit(symbol="1", power=1, multiplier=1.0, scale=0.0)
                    ],
                ),
                associated_compounds=associated_compounds_list,
            )
            fluid.parameter.append(new_param)
            print(f"Added new parameter: {new_param_id}")
            print(f"Associated compounds: {associated_compounds_list}")
        else:
            print(f"Parameter {new_param_id} already exists, skipping creation")

        # Calculate ratios for each measurement in this fluid
        for measurement in fluid.measurement:
            # Find parameter values for both components
            value_1 = None
            value_2 = None

            for pv in measurement.parameterValue:
                if pv.parameterID == parameter_id_1:
                    value_1 = pv.paramValue
                elif pv.parameterID == parameter_id_2:
                    value_2 = pv.paramValue

            # Calculate ratio if both values exist
            if value_1 is not None and value_2 is not None:
                # Avoid division by zero
                if value_2 != 0:
                    ratio = value_1 / value_2

                    # Round to specified precision if provided
                    if precision is not None:
                        ratio = round(ratio, precision)
                else:
                    ratio = float("inf") if value_1 > 0 else 0.0

                print(
                    f"Measurement {measurement.measurement_id}: ratio = {value_1} / {value_2} = {ratio}"
                )

                # Check if parameter value already exists for this measurement
                existing_pv = next(
                    (
                        pv
                        for pv in measurement.parameterValue
                        if pv.parameterID == new_param_id
                    ),
                    None,
                )

                if not existing_pv:
                    # Add new parameter value
                    new_param_value = ParameterValue(
                        parameterID=new_param_id,
                        paramValue=ratio,
                        uncertainty=None,
                    )
                    measurement.parameterValue.append(new_param_value)
                    print(
                        f"Added ratio value {ratio} to measurement {measurement.measurement_id}"
                    )
                else:
                    # Update existing value
                    existing_pv.paramValue = ratio
                    print(
                        f"Updated ratio value to {ratio} for measurement {measurement.measurement_id}"
                    )
            else:
                if value_1 is None:
                    print(
                        f"Warning: {parameter_id_1} not found in measurement {measurement.measurement_id}"
                    )
                if value_2 is None:
                    print(
                        f"Warning: {parameter_id_2} not found in measurement {measurement.measurement_id}"
                    )

    print("=== Solvent Ratio Calculation Complete ===")
    return doc


def cleanup_orphaned_parameters(doc: FAIRFluidsDocument) -> FAIRFluidsDocument:
    """
    Remove parameters from fluids where the associated compounds are not in the fluid's compounds list.

    This function is useful for cleaning up parameters that were incorrectly added to fluids.
    For example, if a fluid only has water but has a glyceline ratio parameter, this will remove it.

    Args:
        doc: The FAIRFluidsDocument to clean up

    Returns:
        The cleaned FAIRFluidsDocument

    Example:
        doc = cleanup_orphaned_parameters(doc)
    """
    print("=== Cleaning up orphaned parameters ===")

    total_removed = 0

    for fluid_idx, fluid in enumerate(doc.fluid):
        compounds_in_fluid = set(fluid.compounds)
        params_to_remove = []
        param_ids_to_remove = set()

        for param in fluid.parameter:
            # Check if this parameter has associated compounds
            if hasattr(param, "associated_compounds") and param.associated_compounds:
                # Check if ALL associated compounds are in the fluid's compounds list
                compounds_exist = all(
                    comp in compounds_in_fluid for comp in param.associated_compounds
                )

                if not compounds_exist:
                    params_to_remove.append(param)
                    param_ids_to_remove.add(param.parameterID)
                    print(
                        f"Fluid {fluid_idx + 1}: Removing parameter {param.parameterID}"
                    )
                    print(f"  Associated compounds: {param.associated_compounds}")
                    print(f"  Fluid compounds: {list(compounds_in_fluid)}")

        if params_to_remove:
            # Remove from parameter list
            fluid.parameter = [
                p for p in fluid.parameter if p.parameterID not in param_ids_to_remove
            ]

            # Remove from measurements
            for measurement in fluid.measurement:
                measurement.parameterValue = [
                    pv
                    for pv in measurement.parameterValue
                    if pv.parameterID not in param_ids_to_remove
                ]

            total_removed += len(params_to_remove)

    print(f"=== Cleanup complete: removed {total_removed} orphaned parameters ===")
    return doc


def calculate_activationEnergy(
    doc: FAIRFluidsDocument,
    per_source: bool = False,
    solvent_ratio_value: Optional[float] = None,
    return_dataframe: bool = False,
) -> Union[Dict[str, Dict[str, Any]], pd.DataFrame]:
    """
    Calculate activation energy for viscosity using the Arrhenius equation.

    The Arrhenius equation for viscosity is: η = η₀ * exp(Ea/(R*T))
    Taking natural logarithm: ln(η) = ln(η₀) + (Ea/R) * (1/T)

    Linear regression of ln(η) vs 1/T gives: slope = Ea/R
    Therefore: Ea = slope * R, where R = 8.314 J/(mol·K)

    Args:
        doc: The FAIRFluidsDocument containing fluids and measurements
        per_source: If True, group by fluid AND source_doi (separate calculation for each fluid-DOI combination).
                   If False, group by fluid only (use all measurements from each fluid regardless of DOI).
                   Each fluid already represents a unique composition based on mole fractions.
        solvent_ratio_value: Optional filter value. If provided, only processes fluids and measurements where
                           the "Solvent: Amount ratio of component to other component of binary solvent"
                           parameter equals this value (within floating point tolerance). This filters the data
                           before calculating activation energy.
        return_dataframe: If True, returns a pandas DataFrame instead of a dictionary. The DataFrame will have
                         columns: Group ID, Compounds, Water Fraction, Mole Fractions, Activation Energy (J/mol),
                         Activation Energy (kJ/mol), η₀ (mPa·s), R², N points, Source DOI(s).

    Returns:
        If return_dataframe=False (default): Dictionary with keys being group identifiers (fluid index like "fluid_0"
        or fluid-DOI combination) and values containing:
        - 'activation_energy': Activation energy in J/mol
        - 'eta0': Pre-exponential factor (η₀) in mPa·s
        - 'r_squared': R² value of the fit
        - 'n_points': Number of data points used
        - 'temperatures': List of temperatures used (K)
        - 'viscosities': List of viscosities used (mPa·s)
        - 'source_doi': Source DOI for this group
        - 'compounds': List of compound IDs
        - 'mole_fractions': Dictionary of all mole fractions (backward compatibility)
        - 'water_fraction': Water mole fraction (if available)
        - 'mole_fraction_<compound_name>': Individual mole fraction columns for each compound
          (e.g., 'mole_fraction_water', 'mole_fraction_glycerol', 'mole_fraction_cholinechloride')

        If return_dataframe=True: pandas DataFrame with columns:
        - 'Group ID': Group identifier (fluid index or fluid-DOI combination)
        - 'Compounds': Comma-separated string of compound IDs
        - 'Water Fraction': Water mole fraction (NaN if not available)
        - 'Mole Fractions': Formatted string of all mole fractions (e.g., "compound1: 0.3333, compound2: 0.6667")
        - 'Activation Energy (J/mol)': Activation energy in J/mol
        - 'Activation Energy (kJ/mol)': Activation energy in kJ/mol
        - 'η₀ (mPa·s)': Pre-exponential factor
        - 'R²': R² value of the fit
        - 'N points': Number of data points used
        - 'Source DOI(s)': Source DOI string (or "mixed" if multiple sources)

    Example:
        # Return dictionary
        results = calculate_activationEnergy(doc, per_source=False)
        for group_id, result in results.items():
            print(f"{group_id}: Ea = {result['activation_energy']:.2f} J/mol")

        # Return DataFrame
        df = calculate_activationEnergy(doc, per_source=False, return_dataframe=True)
        print(df)

        # Filter by solvent ratio = 2.0 and return DataFrame
        df = calculate_activationEnergy(doc, per_source=False, solvent_ratio_value=2.0, return_dataframe=True)
    """
    R = 8.314  # Gas constant in J/(mol·K)

    # Print filter information if filtering is active
    if solvent_ratio_value is not None:
        print(f"=== Filtering by solvent ratio = {solvent_ratio_value} ===")

    # Group measurements by fluid or source_doi
    grouped_data = defaultdict(
        lambda: {
            "temperatures": [],
            "viscosities": [],
            "source_dois": set(),
            "compounds": None,
            "mole_fractions": {},  # Store mole fractions for each compound
        }
    )

    for fluid_idx, fluid in enumerate(doc.fluid):
        # Build parameter lookup
        parameter_lookup = {}
        for param in fluid.parameter:
            if param.parameterID:
                parameter_lookup[param.parameterID] = param

        # Build property lookup
        property_lookup = {}
        for prop in fluid.property:
            if prop.propertyID:
                property_lookup[prop.propertyID] = prop

        # If filtering by solvent ratio, find parameter IDs that match the filter
        solvent_ratio_param_ids = []
        if solvent_ratio_value is not None:
            target_param_type = (
                Parameters.SOLVENT_AMOUNT_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT
            )
            for param in fluid.parameter:
                if param.parameter and param.parameter == target_param_type:
                    solvent_ratio_param_ids.append(param.parameterID)

            if not solvent_ratio_param_ids:
                # Skip this fluid if filtering is requested but no matching parameter found
                print(
                    f"Fluid {fluid_idx}: Skipping - no solvent ratio parameter found (filtering by ratio={solvent_ratio_value})"
                )
                continue

        # Helper function to check if measurement matches solvent ratio filter
        def matches_solvent_ratio_filter(measurement):
            if solvent_ratio_value is None:
                return True  # No filter, accept all measurements

            # Check if measurement has a parameterValue matching the filter
            for param_val in measurement.parameterValue:
                if param_val.parameterID in solvent_ratio_param_ids:
                    # Use small tolerance for floating point comparison
                    if param_val.paramValue is not None:
                        if abs(param_val.paramValue - solvent_ratio_value) < 1e-6:
                            return True
            return False

        # Use fluid index as base group identifier
        # Each fluid already represents a unique composition (based on mole fractions)
        base_group_id = f"fluid_{fluid_idx}"

        if per_source:
            # Group by fluid AND source_doi
            # Process measurements and group by source_doi within this fluid
            for measurement in fluid.measurement:
                # Apply solvent ratio filter if specified
                if not matches_solvent_ratio_filter(measurement):
                    continue

                source_doi = measurement.source_doi or "unknown_doi"

                # Create group ID combining fluid index and source_doi
                group_id = f"{base_group_id}_doi_{source_doi}"

                # Extract temperature and viscosity
                temperature = None
                viscosity = None

                for param_val in measurement.parameterValue:
                    param_def = parameter_lookup.get(param_val.parameterID)
                    if param_def and param_def.parameter:
                        param_name = str(
                            param_def.parameter.value
                            if hasattr(param_def.parameter, "value")
                            else param_def.parameter
                        )
                        if (
                            "temperature" in param_name.lower()
                            and param_val.paramValue is not None
                        ):
                            temperature = param_val.paramValue

                for prop_val in measurement.propertyValue:
                    prop_def = property_lookup.get(prop_val.propertyID)
                    if prop_def and prop_def.properties:
                        prop_name = str(
                            prop_def.properties.value
                            if hasattr(prop_def.properties, "value")
                            else prop_def.properties
                        )
                        if (
                            "viscosity" in prop_name.lower()
                            and prop_val.propValue is not None
                            and prop_val.propValue > 0
                        ):
                            viscosity = prop_val.propValue

                if temperature is not None and viscosity is not None:
                    grouped_data[group_id]["temperatures"].append(temperature)
                    grouped_data[group_id]["viscosities"].append(viscosity)
                    grouped_data[group_id]["source_dois"].add(source_doi)
                    if grouped_data[group_id]["compounds"] is None:
                        grouped_data[group_id]["compounds"] = fluid.compounds

                    # Extract mole fractions from this measurement (use first measurement to get composition)
                    if not grouped_data[group_id]["mole_fractions"]:
                        for param_val in measurement.parameterValue:
                            param_def = parameter_lookup.get(param_val.parameterID)
                            if param_def and param_def.parameter:
                                param_name = str(
                                    param_def.parameter.value
                                    if hasattr(param_def.parameter, "value")
                                    else param_def.parameter
                                )
                                if (
                                    "mole fraction" in param_name.lower()
                                    and param_val.paramValue is not None
                                ):
                                    # Extract compound name from parameterID
                                    param_id = param_val.parameterID
                                    # Parameter IDs are like "parameter_mole_fraction_water"
                                    # Extract the compound name
                                    if "mole_fraction_" in param_id:
                                        comp_name = param_id.split("mole_fraction_")[-1]
                                        grouped_data[group_id]["mole_fractions"][
                                            comp_name
                                        ] = param_val.paramValue
        else:
            # Group by fluid only (use all measurements from this fluid regardless of source_doi)
            group_id = base_group_id

            for measurement in fluid.measurement:
                # Apply solvent ratio filter if specified
                if not matches_solvent_ratio_filter(measurement):
                    continue

                # Extract temperature and viscosity
                temperature = None
                viscosity = None

                for param_val in measurement.parameterValue:
                    param_def = parameter_lookup.get(param_val.parameterID)
                    if param_def and param_def.parameter:
                        param_name = str(
                            param_def.parameter.value
                            if hasattr(param_def.parameter, "value")
                            else param_def.parameter
                        )
                        if (
                            "temperature" in param_name.lower()
                            and param_val.paramValue is not None
                        ):
                            temperature = param_val.paramValue

                for prop_val in measurement.propertyValue:
                    prop_def = property_lookup.get(prop_val.propertyID)
                    if prop_def and prop_def.properties:
                        prop_name = str(
                            prop_def.properties.value
                            if hasattr(prop_def.properties, "value")
                            else prop_def.properties
                        )
                        if (
                            "viscosity" in prop_name.lower()
                            and prop_val.propValue is not None
                            and prop_val.propValue > 0
                        ):
                            viscosity = prop_val.propValue

                if temperature is not None and viscosity is not None:
                    grouped_data[group_id]["temperatures"].append(temperature)
                    grouped_data[group_id]["viscosities"].append(viscosity)
                    grouped_data[group_id]["source_dois"].add(measurement.source_doi)
                    if grouped_data[group_id]["compounds"] is None:
                        grouped_data[group_id]["compounds"] = fluid.compounds

                    # Extract mole fractions from this measurement (use first measurement to get composition)
                    if not grouped_data[group_id]["mole_fractions"]:
                        for param_val in measurement.parameterValue:
                            param_def = parameter_lookup.get(param_val.parameterID)
                            if param_def and param_def.parameter:
                                param_name = str(
                                    param_def.parameter.value
                                    if hasattr(param_def.parameter, "value")
                                    else param_def.parameter
                                )
                                if (
                                    "mole fraction" in param_name.lower()
                                    and param_val.paramValue is not None
                                ):
                                    # Extract compound name from parameterID
                                    param_id = param_val.parameterID
                                    # Parameter IDs are like "parameter_mole_fraction_water"
                                    # Extract the compound name
                                    if "mole_fraction_" in param_id:
                                        comp_name = param_id.split("mole_fraction_")[-1]
                                        grouped_data[group_id]["mole_fractions"][
                                            comp_name
                                        ] = param_val.paramValue

    # Calculate activation energy for each group
    results = {}

    for group_id, data in grouped_data.items():
        temperatures = np.array(data["temperatures"])
        viscosities = np.array(data["viscosities"])

        # Need at least 2 points for linear regression
        if len(temperatures) < 2:
            print(
                f"Warning: {group_id} has only {len(temperatures)} data point(s), skipping"
            )
            continue

        # Remove any invalid values
        valid_mask = (temperatures > 0) & (viscosities > 0)
        temperatures = temperatures[valid_mask]
        viscosities = viscosities[valid_mask]

        if len(temperatures) < 2:
            print(f"Warning: {group_id} has fewer than 2 valid data points, skipping")
            continue

        # Fit Arrhenius equation: ln(η) = ln(η₀) + (Ea/R) * (1/T)
        x = 1.0 / temperatures  # 1/T
        y = np.log(viscosities)  # ln(η)

        # Linear regression
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]  # Ea/R
        intercept = coeffs[1]  # ln(η₀)

        # Calculate R²
        y_pred = np.polyval(coeffs, x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Calculate activation energy
        activation_energy = slope * R  # J/mol
        eta0 = np.exp(intercept)  # mPa·s

        # Extract source_doi - for per_source=True, each group has single DOI
        # for per_source=False, may have multiple DOIs (set to None to indicate mixed)
        source_doi_result = None
        if per_source:
            # For per_source=True, each group should have exactly one DOI
            source_dois_list = list(data["source_dois"])
            source_doi_result = (
                source_dois_list[0] if len(source_dois_list) == 1 else None
            )
        else:
            # For per_source=False, set to None to indicate measurements may come from multiple sources
            source_doi_result = None

        # Extract water mole fraction (check various possible names)
        water_fraction = None
        mole_fractions_dict = data.get("mole_fractions", {})
        # Try various key formats that might represent water
        for key in mole_fractions_dict.keys():
            key_lower = key.lower()
            if "water" in key_lower:
                water_fraction = mole_fractions_dict[key]
                break

        # Extract individual mole fractions as separate columns
        # Create a dictionary with individual mole fraction columns
        mole_fraction_columns = {}
        for key, value in mole_fractions_dict.items():
            # Create column name: mole_fraction_<compound_name>
            column_name = f"mole_fraction_{key}"
            mole_fraction_columns[column_name] = value

        # Build results dictionary
        result_dict = {
            "activation_energy": activation_energy,
            "eta0": eta0,
            "r_squared": r_squared,
            "n_points": len(temperatures),
            "temperatures": temperatures.tolist(),
            "viscosities": viscosities.tolist(),
            "source_doi": source_doi_result,
            "compounds": data["compounds"],
            "mole_fractions": mole_fractions_dict,  # Keep original dict for backward compatibility
            "water_fraction": water_fraction,
        }

        # Add individual mole fraction columns
        result_dict.update(mole_fraction_columns)

        results[group_id] = result_dict

    # Convert to DataFrame if requested
    if return_dataframe:
        df_data = []
        for group_id, result in results.items():
            # Format compounds as comma-separated string
            compounds_str = (
                ", ".join(result["compounds"]) if result["compounds"] else "unknown"
            )

            # Format mole fractions as string (e.g., "compound1: 0.3333, compound2: 0.6667")
            mole_fractions_dict = result.get("mole_fractions", {})
            mole_fractions_str = ", ".join(
                [f"{k}: {v:.4f}" for k, v in mole_fractions_dict.items()]
            )
            if not mole_fractions_str:
                mole_fractions_str = "N/A"

            # Format source DOI(s)
            source_doi = result.get("source_doi")
            if source_doi:
                source_doi_str = source_doi
            else:
                # For per_source=False, may have multiple DOIs
                source_doi_str = "mixed"

            df_data.append(
                {
                    "Group ID": group_id,
                    "Compounds": compounds_str,
                    "Water Fraction": result.get("water_fraction"),
                    "Mole Fractions": mole_fractions_str,
                    "Activation Energy (J/mol)": result["activation_energy"],
                    "Activation Energy (kJ/mol)": result["activation_energy"] / 1000,
                    "η₀ (mPa·s)": result["eta0"],
                    "R²": result["r_squared"],
                    "N points": result["n_points"],
                    "Source DOI(s)": source_doi_str,
                }
            )

        df = pd.DataFrame(df_data)
        return df

    return results


# Example usage:
# parser = FAIRFluidsCMLParser("/path/to/file.xml", compounds=[{"commonName": "Water", ...}, ...])
# doc = parser.parse()
#
# Example of combine_compounds:
# from fairfluids import FAIRFluidsDocument, FluidIO, combine_compounds
#
# # Load document from JSON
# io = FluidIO()
# doc = io.load_json("path/to/document.json")
#
# # Combine choline (pubChemID: 305) and chloride (pubChemID: 312) into choline chloride (pubChemID: 6209)
# doc = combine_compounds(doc, old_molecules=[305, 312], new_molecule=6209)
#
# # Save the modified document
# io.save_json(doc, "path/to/modified_document.json")
#
# Example of calculate_ratio_of_solvent:
# from fairfluids import FAIRFluidsDocument, calculate_ratio_of_solvent
#
# # Calculate glycerol/choline chloride ratio (glyceline) for the whole document
# # Use precision=2 to round ratios to 2 decimal places (e.g., ensures 2.0 instead of 2.0075...)
# doc = calculate_ratio_of_solvent(
#     doc=fairfluids_document,
#     parameter_id_1="parameter_mole_fraction_glycerol",
#     parameter_id_2="parameter_mole_fraction_cholinechloride",
#     name="glyceline",
#     compound_id_1="compound_glycerol",
#     compound_id_2="compound_cholinechloride",
#     precision=2  # Round to 2 decimal places
# )
#
# # Clean up any orphaned parameters (remove parameters where associated compounds aren't in the fluid)
# doc = cleanup_orphaned_parameters(doc)
