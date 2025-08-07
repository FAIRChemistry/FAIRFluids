# Import the FAIRFluids models
import sys
sys.path.append('/home/sga/Code/FAIRFluids')

from FAIRFluids.core.lib import (
    FAIRFluidsDocument, Version, Citation, Author, Compound, 
    Fluid, Property, PropertyValue, Parameter, ParameterValue, Measurement,
    UnitDefinition, BaseUnit, Method, Properties, Parameters
)
from typing import Optional, List, Dict, Any
import xml.etree.ElementTree as ET

class FAIRFluidsCMLParser:
    """
    Robust parser for CML files to populate the FAIRFluids data model.
    """
    def __init__(self, cml_path: str, compounds: Optional[List[Dict[str, Any]]] = None, document: Optional[FAIRFluidsDocument] = None):
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
        # If the document already has compounds, use them
        if getattr(self.document, 'compound', None) and len(self.document.compound) > 0:
            for i, compound in enumerate(self.document.compound):
                if compound.commonName:
                    self.compound_name_to_id[compound.commonName] = i
                    self.compound_common_names.append(compound.commonName.lower())
                else:
                    self.compound_common_names.append(str(i))
                if compound.compoundID is not None:
                    self.index_to_compoundID[i] = str(compound.compoundID)
                else:
                    self.index_to_compoundID[i] = str(i)
        else:
            for i, comp in enumerate(self.compounds):
                compound = self.document.add_to_compound(**comp)
                if compound.commonName:
                    self.compound_name_to_id[compound.commonName] = i
                    self.compound_common_names.append(compound.commonName.lower())
                else:
                    self.compound_common_names.append(str(i))
                # Map index to compoundID (as string)
                if compound.compoundID is not None:
                    self.index_to_compoundID[i] = str(compound.compoundID)
                else:
                    self.index_to_compoundID[i] = str(i)

    def _extract_experiments(self) -> List[ET.Element]:
        return self.root.findall(".//{http://www.xml-cml.org/schema}module[@dictRef='des:experiment']")
        
    def _extract_properties(self, experiment: ET.Element) -> Dict[str, str]:
        properties = {}
        property_list = experiment.find(".//{http://www.xml-cml.org/schema}propertyList")
        if property_list is not None:
            for prop in property_list:
                dict_ref = prop.get('dictRef')
                if dict_ref:
                    prop_type = dict_ref.split(':')[-1]
                    scalar = prop.find(".//{http://www.xml-cml.org/schema}scalar")
                    if scalar is not None:
                        properties[prop_type] = scalar.text
        return properties

    def _extract_parameters(self, experiment: ET.Element) -> Dict[str, str]:
        parameters = {}
        param_list = experiment.find(".//{http://www.xml-cml.org/schema}parameterList")
        if param_list is not None:
            for param in param_list:
                dict_ref = param.get('dictRef')
                if dict_ref:
                    param_type = dict_ref.split(':')[-1]
                    scalar = param.find(".//{http://www.xml-cml.org/schema}scalar")
                    if scalar is not None:
                        parameters[param_type] = scalar.text
        return parameters

    def _extract_measurement_modules(self) -> List[tuple]:
        """
        Extract both experiment and simulation modules, returning a list of (element, method_type) tuples.
        """
        ns = '{http://www.xml-cml.org/schema}'
        experiments = [(el, 'EXPERIMENTAL') for el in self.root.findall(f".//{ns}module[@dictRef='des:experiment']")]
        simulations = [(el, 'SIMULATION') for el in self.root.findall(f".//{ns}module[@dictRef='des:simulation']")]
        return experiments + simulations

    def _make_unit(self, name: str) -> UnitDefinition:
        if name == "K":
            return UnitDefinition(unitID="K", name="kelvin", base_units=[BaseUnit(symbol="K", power=1, multiplier=1.0, scale=0.0)])
        if name == "mPa·s":
            return UnitDefinition(unitID="mPa·s", name="milliPascal second", base_units=[])
        if name == "1":
            return UnitDefinition(unitID="1", name="dimensionless", base_units=[BaseUnit(symbol="1", power=1, multiplier=1.0, scale=0.0)])
        return UnitDefinition(unitID=name, name=name, base_units=[])

    def _make_property(self, exp_id: str, property_type: str = "viscosity") -> Property:
        # Extend for other property types as needed
        if property_type == "viscosity":
            return Property(
                propertyID="viscosity",
                properties=Properties.VISCOSITY,
                unit=self._make_unit("mPa·s")
            )
        if property_type == "conductivity":
            return Property(
                propertyID="conductivity",
                properties=Properties.THERMAL_CONDUCTIVITY,
                unit=self._make_unit("S/m")
            )
        if property_type == "density":
            return Property(
                propertyID="density",
                properties=Properties.DENSITY,
                unit=self._make_unit("kg/m3")
            )
        # Add more property types as needed
        raise NotImplementedError(f"Property type {property_type} not implemented.")

    def _make_parameter(self, name: str, value: str, idx: int, compound_index: Optional[int] = None) -> Parameter:
        if name == "temperature":
            return Parameter(
                parameterID=f"T_{idx}",
                parameter=Parameters.TEMPERATURE_K,
                unit=self._make_unit("K"),
                associated_compound=None
            )
        if name == "mole_fraction_of_water":
            return Parameter(
                parameterID=f"x_water_{idx}",
                parameter=Parameters.MOLE_FRACTION,
                unit=self._make_unit("1"),
                associated_compound=str(compound_index) if compound_index is not None else None
            )
        if name == "molar_ratio_of_DES":
            return Parameter(
                parameterID=f"r_DES_{idx}",
                parameter=Parameters.AMOUNT_RATIO_OF_SOLUTE_TO_SOLVENT,
                unit=self._make_unit("1"),
                associated_compound=str(compound_index) if compound_index is not None else None
            )
        # Add more parameter types as needed
        return Parameter(
            parameterID=f"param_{name}_{idx}",
            parameter=None,
            unit=self._make_unit("1"),
            associated_compound=str(compound_index) if compound_index is not None else None
        )

    def _make_property_value(self, property_type: str, value: str, uncertainty: Optional[str]) -> PropertyValue:
        return PropertyValue(
            propertyID=property_type,
            propValue=float(value),
            uncertainty=None if uncertainty in (None, "NG") else float(uncertainty)
        )

    def _make_parameter_value(self, param: Parameter, value: str) -> ParameterValue:
        return ParameterValue(
            parameterID=param.parameterID,
            paramValue=float(value),
            uncertainty=None
        )

    def _calculate_mole_fractions(self, molar_ratio: float, water_fraction: float):
        """
        Calculate mole fractions for all three components based on DES molar ratio and water fraction.
        Returns (x1, x2, x3) for component 1, 2, and water.
        """
        r = molar_ratio
        w = water_fraction
        x3 = w
        x1 = (r * (1 - x3)) / (r + 1)
        x2 = (1 - x3) - x1
        return x1, x2, x3

    def populate_fluids_and_measurements(self):
        """
        Populate a single fluid and add all measurements from CML experiments and simulations to it.
        Now supports viscosity, conductivity, and density as possible properties.
        """
        measurement_modules = self._extract_measurement_modules()
        fluid_compounds = [self.index_to_compoundID.get(i, str(i)) for i in range(len(self.compound_common_names))]
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
        property_objs = [self._make_property(pt, property_type=pt) for pt in property_types]
        # Build parameter template as before (from first module)
        first_exp = measurement_modules[0][0] if measurement_modules else None
        parameters_template = []
        if first_exp is not None:
            props = self._extract_properties(first_exp)
            params = self._extract_parameters(first_exp)
            exp_id = props.get("ID", "unknown")
            temperature = params.get("temperature")
            mole_fraction_water = params.get("mole_fraction_of_water")
            molar_ratio_des = params.get("molar_ratio_of_DES")
            idx = 1
            if molar_ratio_des is not None and mole_fraction_water is not None:
                r = float(molar_ratio_des)
                w = float(mole_fraction_water)
                x1, x2, x3 = self._calculate_mole_fractions(r, w)
                mole_fracs = [x1, x2, x3]
                for i, x in enumerate(mole_fracs):
                    compound_id = self.index_to_compoundID.get(i, str(i))
                    # Use precomputed common name list
                    if i < len(self.compound_common_names):
                        common_name = self.compound_common_names[i]
                    else:
                        common_name = str(i)
                    param = Parameter(
                        parameterID=f"x_{common_name}",
                        parameter=Parameters.MOLE_FRACTION,
                        unit=self._make_unit("1"),
                        associated_compound=compound_id
                    )
                    parameters_template.append(param)
                    idx += 1
            if temperature is not None:
                param = self._make_parameter("temperature", temperature, idx)
                parameters_template.append(param)
        # Create the single fluid
        fluid = self.document.add_to_fluid(
            compounds=fluid_compounds,
            property=property_objs,
            parameter=parameters_template,
            measurement=[]
        )
        # Add all measurements
        for exp, method_type in measurement_modules:
            props = self._extract_properties(exp)
            params = self._extract_parameters(exp)
            exp_id = props.get("ID", "unknown")
            doi = props.get("DOI", "unknown")
            temperature = params.get("temperature")
            mole_fraction_water = params.get("mole_fraction_of_water")
            molar_ratio_des = params.get("molar_ratio_of_DES")
            parameter_values = []
            idx = 1
            if molar_ratio_des is not None and mole_fraction_water is not None:
                r = float(molar_ratio_des)
                w = float(mole_fraction_water)
                x1, x2, x3 = self._calculate_mole_fractions(r, w)
                mole_fracs = [x1, x2, x3]
                for i, x in enumerate(mole_fracs):
                    if i < len(self.compound_common_names):
                        common_name = self.compound_common_names[i]
                    else:
                        common_name = str(i)
                    param_id = f"x_{common_name}"
                    param = next((p for p in parameters_template if p.parameterID == param_id), None)
                    if param:
                        parameter_values.append(self._make_parameter_value(param, str(x)))
                    idx += 1
            if temperature is not None:
                param = next((p for p in parameters_template if p.parameterID.startswith("T_")), None)
                if param:
                    parameter_values.append(self._make_parameter_value(param, temperature))
            # Collect property values for all present property types
            property_values = []
            if "value_viscosity" in props:
                property_values.append(self._make_property_value("viscosity", props["value_viscosity"], props.get("error_viscosity")))
            if "value_conductivity" in props:
                property_values.append(self._make_property_value("conductivity", props["value_conductivity"], props.get("error_conductivity")))
            if "value_density" in props:
                property_values.append(self._make_property_value("density", props["value_density"], props.get("error_density")))
            # Set method
            if method_type == 'EXPERIMENTAL':
                method = Method.EXPERIMENTAL if hasattr(Method, 'EXPERIMENTAL') else Method.MEASURED
            else:
                method = Method.SIMULATION if hasattr(Method, 'SIMULATION') else Method.SIMULATED
            fluid.add_to_measurement(
                measurement_id=f"meas_{exp_id}",
                source_doi=doi,
                propertyValue=property_values,
                parameterValue=parameter_values,
                simulated=method,
                method_description="Experimental measurement" if method_type == 'EXPERIMENTAL' else "Simulation measurement"
            )

    def parse(self) -> FAIRFluidsDocument:
        self.populate_compounds()
        self.populate_fluids_and_measurements()
        return self.document

# Example usage:
# parser = FAIRFluidsCMLParser("/path/to/file.xml", compounds=[{"commonName": "Water", ...}, ...])
# doc = parser.parse()