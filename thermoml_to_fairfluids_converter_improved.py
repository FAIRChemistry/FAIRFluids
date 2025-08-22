#!/usr/bin/env python3
"""
Improved ThermoML to FAIRFluids Converter

This script demonstrates how to read a ThermoML XML file and convert it to the FAIRFluids format
with proper property extraction and simulation method details.

Usage:
    python thermoml_to_fairfluids_converter_improved.py <thermoml_file.xml>

Example:
    python thermoml_to_fairfluids_converter_improved.py fairfluids/data/thermoml_xml/spera_et_al_fpe_592_2025_114324.xml
"""

import sys
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Import FAIRFluids models
try:
    from fairfluids.core.lib import (
        FAIRFluidsDocument, Version, Citation, Author, Compound, 
        Fluid, Property, Parameter, Measurement, PropertyValue, 
        ParameterValue, UnitDefinition, BaseUnit, Properties, Parameters, Method, LitType
    )
except ImportError:
    print("Warning: FAIRFluids models not available. Install the package first.")
    print("Creating mock classes for demonstration...")
    
    # Mock classes for demonstration
    class MockClass:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    FAIRFluidsDocument = MockClass
    Version = MockClass
    Citation = MockClass
    Author = MockClass
    Compound = MockClass
    Fluid = MockClass
    Property = MockClass
    Parameter = MockClass
    Measurement = MockClass
    PropertyValue = MockClass
    ParameterValue = MockClass
    UnitDefinition = MockClass
    BaseUnit = MockClass
    
    class Properties:
        DENSITY = "density"
        VISCOSITY = "viscosity"
        SPECIFIC_HEAT_CAPACITY = "specificHeatCapacity"
        BOILING_POINT = "boilingPoint"
        MELTING_POINT = "meltingPoint"
        THERMAL_CONDUCTIVITY = "thermalConductivity"
        VAPOR_PRESSURE = "vaporPressure"
        COMPRESSIBILITY = "Compressibility"
        PH = "pH"
        POLARITY = "polarity"
    
    class Parameters:
        TEMPERATURE_K = "Temperature, K"
        PRESSURE_KPA = "Pressure, kPa"
        MOLE_FRACTION = "Mole fraction"
        MASS_FRACTION = "Mass fraction"
        MOLALITY_MOLKG = "Molality, mol/kg"
        MASS_DENSITY_KGM3 = "Mass density, kg/m3"
        MOLAR_VOLUME_M3MOL = "Molar volume, m3/mol"
    
    class Method:
        SIMULATED = "simulated"
        MEASURED = "measured"
        CALCULATED = "calculated"
        LITERATURE = "literature"
    
    class LitType:
        JOURNAL = "journal"
        BOOK = "book"
        THESIS = "thesis"
        REPORT = "report"
        PATENT = "patent"
        CONFERENCEPROCEEDINGS = "conferenceProceedings"
        UNSPECIFIED = "unspecified"


class ImprovedThermoMLConverter:
    """Improved converter from ThermoML XML to FAIRFluids format."""
    
    def __init__(self):
        self.namespace = {'thermoml': 'http://www.iupac.org/namespaces/ThermoML'}
        self.compound_map = {}  # Maps ThermoML comp_index to FAIRFluids compoundID
        self.property_map = {}  # Maps ThermoML prop_number to FAIRFluids propertyID
        self.variable_map = {}  # Maps ThermoML var_number to FAIRFluids parameterID
        self.property_definitions = {}  # Stores property definitions by prop_number
        self.unique_property_counter = 1  # Counter for generating unique property IDs
        self.unique_parameter_counter = 1  # Counter for generating unique parameter IDs
        
    def parse_thermoml_file(self, file_path: str) -> FAIRFluidsDocument:
        """Parse a ThermoML XML file and convert it to FAIRFluids format."""
        
        print(f"Parsing ThermoML file: {file_path}")
        
        # Parse XML
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Create FAIRFluids document
        fairfluids_doc = FAIRFluidsDocument()
        
        # Convert version
        fairfluids_doc.version = self._convert_version(root)
        
        # Convert citation
        fairfluids_doc.citation = self._convert_citation(root)
        
        # Convert compounds
        fairfluids_doc.compound = self._convert_compounds(root)
        
        # Extract property definitions first
        self._extract_property_definitions(root)
        
        # Create a global property mapping that combines property number with fluid context
        self._create_global_property_mapping(root)
        
        # Convert fluid data
        fairfluids_doc.fluid = self._convert_fluid_data(root)
        
        return fairfluids_doc
    
    def _convert_version(self, root: ET.Element) -> Version:
        """Convert ThermoML version to FAIRFluids version."""
        version_elem = root.find('.//thermoml:Version', self.namespace)
        if version_elem is not None:
            major = version_elem.find('thermoml:nVersionMajor', self.namespace)
            minor = version_elem.find('thermoml:nVersionMinor', self.namespace)
            
            return Version(
                versionMajor=int(major.text) if major is not None else None,
                versionMinor=int(minor.text) if minor is not None else None
            )
        return None
    
    def _convert_citation(self, root: ET.Element) -> Citation:
        """Convert ThermoML citation to FAIRFluids citation."""
        citation_elem = root.find('.//thermoml:Citation', self.namespace)
        if citation_elem is None:
            return None
        
        # Extract basic citation information
        pub_type = citation_elem.find('thermoml:eType', self.namespace)
        authors = citation_elem.findall('thermoml:sAuthor', self.namespace)
        title = citation_elem.find('thermoml:sTitle', self.namespace)
        journal = citation_elem.find('thermoml:sPubName', self.namespace)
        volume = citation_elem.find('thermoml:sVol', self.namespace)
        pages = citation_elem.find('thermoml:sPage', self.namespace)
        year = citation_elem.find('thermoml:yrPubYr', self.namespace)
        doi = citation_elem.find('thermoml:sDOI', self.namespace)
        
        # Convert publication type
        lit_type = self._map_publication_type(pub_type.text if pub_type is not None else None)
        
        # Convert authors
        author_list = []
        for author_elem in authors:
            if author_elem.text:
                # Split author name into given and family names
                name_parts = author_elem.text.split(', ')
                if len(name_parts) >= 2:
                    family_name = name_parts[0]
                    given_name = ', '.join(name_parts[1:])
                else:
                    family_name = author_elem.text
                    given_name = None
                
                author_list.append(Author(
                    family_name=family_name,
                    given_name=given_name
                ))
        
        return Citation(
            litType=lit_type,
            author=author_list,
            title=title.text if title is not None else None,
            pub_name=journal.text if journal is not None else None,
            lit_volume_num=volume.text if volume is not None else None,
            page=pages.text if pages is not None else None,
            publication_year=year.text if year is not None else None,
            doi=doi.text if doi is not None else None
        )
    
    def _map_publication_type(self, thermoml_type: str) -> Optional[LitType]:
        """Map ThermoML publication type to FAIRFluids LitType."""
        if not thermoml_type:
            return None
        
        type_mapping = {
            'journal': LitType.JOURNAL,
            'book': LitType.BOOK,
            'thesis': LitType.THESIS,
            'report': LitType.REPORT,
            'patent': LitType.PATENT,
            'conferenceProceedings': LitType.CONFERENCEPROCEEDINGS
        }
        
        return type_mapping.get(thermoml_type.lower(), LitType.UNSPECIFIED)
    
    def _convert_compounds(self, root: ET.Element) -> List[Compound]:
        """Convert ThermoML compounds to FAIRFluids compounds."""
        compounds = []
        compound_elems = root.findall('.//thermoml:Compound', self.namespace)
        
        for i, compound_elem in enumerate(compound_elems):
            # Extract compound information
            comp_index = compound_elem.find('thermoml:nCompIndex', self.namespace)
            pubchem_id = compound_elem.find('thermoml:nPubChemID', self.namespace)
            common_names = compound_elem.findall('thermoml:sCommonName', self.namespace)
            iupac_name = compound_elem.find('thermoml:sIUPACName', self.namespace)
            inchi = compound_elem.find('thermoml:sStandardInChI', self.namespace)
            inchikey = compound_elem.find('thermoml:sStandardInChIKey', self.namespace)
            smiles = compound_elem.findall('thermoml:sSMILES', self.namespace)
            
            # Create compound ID - use descriptive name if available
            if common_names and common_names[0].text:
                compound_id = common_names[0].text
            else:
                compound_id = f"compound_{i+1}"
            
            # Map both comp_index and org_num to the compound ID
            if comp_index is not None:
                self.compound_map[comp_index.text] = compound_id
            
            # Also map the org_num from RegNum if available
            reg_num = compound_elem.find('.//thermoml:RegNum//thermoml:nOrgNum', self.namespace)
            if reg_num is not None:
                self.compound_map[reg_num.text] = compound_id
            
            # Extract primary common name
            primary_name = common_names[0].text if common_names else None
            
            # Convert SELFIE if available (use first SMILES as approximation)
            selfie = smiles[0].text if smiles else None
            
            compound = Compound(
                compoundID=compound_id,
                pubChemID=int(pubchem_id.text) if pubchem_id is not None else None,
                commonName=primary_name,
                SELFIE=selfie,
                name_IUPAC=iupac_name.text if iupac_name is not None else None,
                standard_InChI=inchi.text if inchi is not None else None,
                standard_InChI_key=inchikey.text if inchikey is not None else None
            )
            
            compounds.append(compound)
        
        return compounds
    
    def _create_global_property_mapping(self, root: ET.Element):
        """Create a global property mapping that combines property number with fluid context."""
        print("Creating global property mapping...")
        
        # Find all PureOrMixtureData elements
        data_elems = root.findall('.//thermoml:PureOrMixtureData', self.namespace)
        
        for fluid_index, data_elem in enumerate(data_elems):
            # Find properties in this fluid
            property_elems = data_elem.findall('.//thermoml:Property', self.namespace)
            
            for prop_elem in property_elems:
                prop_number = prop_elem.find('thermoml:nPropNumber', self.namespace)
                if prop_number is None:
                    continue
                
                prop_num = prop_number.text
                
                # Extract property information directly from this Property element
                prop_method_id = None
                for child in prop_elem.iter():
                    if child.tag.endswith('Property-MethodID'):
                        prop_method_id = child
                        break
                
                if prop_method_id is not None:
                    # Extract property name and type directly
                    prop_name, prop_type, method_details = self._extract_property_details(prop_method_id)
                    
                    # Create unique property ID based on name and type
                    if prop_name != "Unknown":
                        property_id = f"{prop_type}_{self.unique_property_counter}"
                        self.unique_property_counter += 1
                        
                        print(f"  Fluid {fluid_index+1}, Property {prop_num}: {prop_name} -> {property_id}")
                    else:
                        property_id = f"unknown_property_{self.unique_property_counter}"
                        self.unique_property_counter += 1
                        print(f"  Fluid {fluid_index+1}, Property {prop_num}: Unknown -> {property_id}")
                else:
                    property_id = f"unknown_property_{self.unique_property_counter}"
                    self.unique_property_counter += 1
                    print(f"  Fluid {fluid_index+1}, Property {prop_num}: No Property-MethodID -> {property_id}")
                
                # Create a unique key combining fluid index and property number
                unique_key = f"{fluid_index}_{prop_num}"
                
                # Store the mapping
                self.property_map[unique_key] = property_id
    
    def _extract_property_definitions(self, root: ET.Element):
        """Extract property definitions from Property-MethodID blocks."""
        print("Extracting property definitions...")
        
        # Find all Property elements
        property_elems = root.findall('.//thermoml:Property', self.namespace)
        
        for prop_elem in property_elems:
            prop_number = prop_elem.find('thermoml:nPropNumber', self.namespace)
            if prop_number is None:
                continue
            
            prop_num = prop_number.text
            
            # Extract property information from Property-MethodID (handle hyphen in tag name)
            prop_method_id = None
            for child in prop_elem.iter():
                if child.tag.endswith('Property-MethodID'):
                    prop_method_id = child
                    break
            if prop_method_id is None:
                continue
            
            # Extract property name and type
            prop_name, prop_type, method_details = self._extract_property_details(prop_method_id)
            
            # Store property definition
            self.property_definitions[prop_num] = {
                'name': prop_name,
                'type': prop_type,
                'method_details': method_details
            }
            
            print(f"  Property {prop_num}: {prop_name} ({prop_type})")
    
    def _extract_property_details(self, prop_method_id: ET.Element) -> Tuple[str, str, str]:
        """Extract property name, type, and method details from Property-MethodID."""
        prop_name = "Unknown"
        prop_type = "Unknown"
        method_details = ""
        
        # Look for property name in various property groups (handle hyphen in tag names)
        prop_name = "Unknown"
        prop_type = "Unknown"
        
        # Search for property groups and names
        for child in prop_method_id.iter():
            if child.tag.endswith('VolumetricProp'):
                prop_type = 'volumetric'
                # Look for property name within this group
                for subchild in child.iter():
                    if subchild.tag.endswith('ePropName'):
                        prop_name = subchild.text
                        break
                break
            elif child.tag.endswith('TransportProp'):
                prop_type = 'transport'
                for subchild in child.iter():
                    if subchild.tag.endswith('ePropName'):
                        prop_name = subchild.text
                        break
                break
            elif child.tag.endswith('HeatCapacityAndDerivedProp'):
                prop_type = 'thermodynamic'
                for subchild in child.iter():
                    if subchild.tag.endswith('ePropName'):
                        prop_name = subchild.text
                        break
                break
            elif child.tag.endswith('PhaseTransition'):
                prop_type = 'phase_transition'
                for subchild in child.iter():
                    if subchild.tag.endswith('ePropName'):
                        prop_name = subchild.text
                        break
                break
            elif child.tag.endswith('ActivityFugacityOsmoticProp'):
                prop_type = 'other'
                for subchild in child.iter():
                    if subchild.tag.endswith('ePropName'):
                        prop_name = subchild.text
                        break
                break
            elif child.tag.endswith('BioProperties'):
                prop_type = 'other'
                for subchild in child.iter():
                    if subchild.tag.endswith('ePropName'):
                        prop_name = subchild.text
                        break
                break
        
        # Extract method details
        prediction = None
        pred_type = None
        pred_desc = None
        
        for child in prop_method_id.iter():
            if child.tag.endswith('Prediction'):
                prediction = child
                # Look for prediction type and description
                for subchild in child.iter():
                    if subchild.tag.endswith('ePredictionType'):
                        pred_type = subchild
                    elif subchild.tag.endswith('sPredictionMethodDescription'):
                        pred_desc = subchild
                break
            
            if pred_type is not None and pred_desc is not None:
                method_details = f"{pred_type.text}: {pred_desc.text}"
        
        return prop_name, prop_type, method_details
    
    def _convert_fluid_data(self, root: ET.Element) -> List[Fluid]:
        """Convert ThermoML fluid data to FAIRFluids format."""
        fluids = []
        
        # Find all PureOrMixtureData elements
        data_elems = root.findall('.//thermoml:PureOrMixtureData', self.namespace)
        
        for i, data_elem in enumerate(data_elems):
            # Extract compounds for this fluid
            compounds = self._extract_components(data_elem)
            
            # Extract properties for this fluid
            properties = self._extract_properties(data_elem, i)
            
            # Extract parameters for this fluid
            parameters = self._extract_parameters(data_elem)
            
            # Extract measurements for this fluid, passing parameters for composition consistency
            measurements = self._extract_measurements(data_elem, i, parameters)
            
            # Create fluid object
            fluid = Fluid(
                compounds=compounds,
                property=properties,
                parameter=parameters,
                measurement=measurements
            )
            
            fluids.append(fluid)
        
        return fluids
    
    def _extract_components(self, data_elem: ET.Element) -> List[str]:
        """Extract component references from PureOrMixtureData."""
        components = []
        component_elems = data_elem.findall('.//thermoml:Component', self.namespace)
        
        for comp_elem in component_elems:
            reg_num = comp_elem.find('.//thermoml:RegNum//thermoml:nOrgNum', self.namespace)
            if reg_num is not None:
                if reg_num.text in self.compound_map:
                    components.append(self.compound_map[reg_num.text])
                else:
                    print(f"Warning: Component with org_num {reg_num.text} not found in compound map")
        
        return components
    
    def _extract_properties(self, data_elem: ET.Element, fluid_index: int) -> List[Property]:
        """Extract properties from PureOrMixtureData."""
        properties = []
        property_elems = data_elem.findall('.//thermoml:Property', self.namespace)
        
        for i, prop_elem in enumerate(property_elems):
            prop_number = prop_elem.find('thermoml:nPropNumber', self.namespace)
            
            if prop_number is None:
                continue
            
            prop_num = prop_number.text
            
            # Create unique key combining fluid index and property number
            unique_key = f"{fluid_index}_{prop_num}"
            
            # Get property definition from our stored definitions
            if prop_num in self.property_definitions:
                prop_def = self.property_definitions[prop_num]
                property_type = self._map_property_type(prop_def['name'])
            else:
                property_type = None
            
            # Get property ID from our global mapping
            property_id = self.property_map.get(unique_key, f"unknown_property_{i+1}")
            
            # Also get the property type and unit from the global mapping context
            prop_name = "Unknown"
            if unique_key in self.property_map:
                # Extract property information directly to get the type
                prop_method_id = None
                for child in prop_elem.iter():
                    if child.tag.endswith('Property-MethodID'):
                        prop_method_id = child
                        break
                
                if prop_method_id is not None:
                    prop_name, prop_type, method_details = self._extract_property_details(prop_method_id)
                    property_type = self._map_property_type(prop_name)
            
            # Create unit definition for this property
            unit_definition = self._create_unit_definition(prop_name)
            
            # Create property object with proper unit
            property_obj = Property(
                propertyID=property_id,
                properties=property_type,
                unit=unit_definition
            )
            
            properties.append(property_obj)
        
        return properties
    
    def _create_unit_definition(self, prop_name: str) -> UnitDefinition:
        """Create a UnitDefinition based on the property name."""
        
        # Map property names to unit information
        unit_mappings = {
            'mass density': {'unitID': 'kg_m3', 'name': 'kilogram per cubic meter'},
            'molar enthalpy': {'unitID': 'kJ_mol', 'name': 'kilojoule per mole'},
            'viscosity': {'unitID': 'Pa_s', 'name': 'pascal second'},
            'isobaric coefficient of expansion': {'unitID': 'K-1', 'name': 'per kelvin'},
            'excess molar volume': {'unitID': 'm3_mol', 'name': 'cubic meter per mole'},
            'self diffusion coefficient': {'unitID': 'm2_s', 'name': 'square meter per second'},
        }
        
        # Find matching unit
        prop_name_lower = prop_name.lower()
        for key, unit_info in unit_mappings.items():
            if key in prop_name_lower:
                return UnitDefinition(
                    unitID=unit_info['unitID'],
                    name=unit_info['name']
                )
        
        # Default unit if no match found
        return UnitDefinition(
            unitID='dimensionless',
            name='dimensionless'
        )

    def _map_property_type(self, prop_name: str) -> Optional[Properties]:
        """Map ThermoML property name to FAIRFluids property type."""
        if not prop_name:
            return None
        
        prop_name_lower = prop_name.lower()
        
        if 'density' in prop_name_lower:
            return Properties.DENSITY
        elif 'viscosity' in prop_name_lower:
            return Properties.VISCOSITY
        elif 'heat capacity' in prop_name_lower or 'enthalpy' in prop_name_lower:
            return Properties.SPECIFIC_HEAT_CAPACITY
        elif 'boiling' in prop_name_lower:
            return Properties.BOILING_POINT
        elif 'melting' in prop_name_lower:
            return Properties.MELTING_POINT
        elif 'thermal conductivity' in prop_name_lower:
            return Properties.THERMAL_CONDUCTIVITY
        elif 'vapor pressure' in prop_name_lower:
            return Properties.VAPOR_PRESSURE
        elif 'compressibility' in prop_name_lower or 'expansion' in prop_name_lower:
            return Properties.COMPRESSIBILITY
        elif 'volume' in prop_name_lower and 'excess' in prop_name_lower:
            return Properties.COMPRESSIBILITY  # Closest match for excess molar volume
        elif 'diffusion' in prop_name_lower:
            return Properties.VISCOSITY  # Closest match for transport properties
        else:
            return None
    
    def _extract_parameters(self, data_elem: ET.Element) -> List[Parameter]:
        """Extract parameters from constraints and variables."""
        parameters = []
        
        # Extract constraints
        constraint_elems = data_elem.findall('.//thermoml:Constraint', self.namespace)
        for i, constr_elem in enumerate(constraint_elems):
            param = self._convert_constraint_to_parameter(constr_elem, i)
            if param:
                parameters.append(param)
        
        # Extract variables
        variable_elems = data_elem.findall('.//thermoml:Variable', self.namespace)
        for i, var_elem in enumerate(variable_elems):
            param = self._convert_variable_to_parameter(var_elem, i)
            if param:
                parameters.append(param)
        
        return parameters
    
    def _convert_constraint_to_parameter(self, constr_elem: ET.Element, index: int) -> Optional[Parameter]:
        """Convert a ThermoML constraint to a FAIRFluids parameter."""
        constraint_type = constr_elem.find('.//thermoml:ConstraintType', self.namespace)
        if constraint_type is None:
            return None
        
        # Extract constraint type
        comp_comp = constraint_type.find('thermoml:eComponentComposition', self.namespace)
        pressure = constraint_type.find('thermoml:ePressure', self.namespace)
        
        if comp_comp is not None:
            param_type = Parameters.MOLE_FRACTION
            # Create unique ID that includes the compound and composition value
            reg_num = constr_elem.find('.//thermoml:RegNum//thermoml:nOrgNum', self.namespace)
            compound_id = self.compound_map.get(reg_num.text) if reg_num is not None else None
            
            # Get the actual composition value
            constr_value = constr_elem.find('thermoml:nConstraintValue', self.namespace)
            composition_value = float(constr_value.text) if constr_value is not None else 0.0
            
            if compound_id and composition_value is not None:
                param_id = f"composition_{compound_id}_{composition_value}"
            else:
                param_id = f"composition_{self.unique_parameter_counter}"
                self.unique_parameter_counter += 1
        elif pressure is not None:
            param_type = Parameters.PRESSURE_KPA
            param_id = f"pressure_{self.unique_parameter_counter}"
            self.unique_parameter_counter += 1
        else:
            return None
        
        # Extract associated compound
        reg_num = constr_elem.find('.//thermoml:RegNum//thermoml:nOrgNum', self.namespace)
        associated_compound = self.compound_map.get(reg_num.text) if reg_num is not None else None
        
        # Create parameter object without null unit field
        param_obj = Parameter(
            parameterID=param_id,
            parameter=param_type
        )
        
        # Only set associated_compound if it's not None
        if associated_compound:
            param_obj.associated_compound = associated_compound
        
        return param_obj
    
    def _convert_variable_to_parameter(self, var_elem: ET.Element, index: int) -> Optional[Parameter]:
        """Convert a ThermoML variable to a FAIRFluids parameter."""
        var_number = var_elem.find('thermoml:nVarNumber', self.namespace)
        var_type = var_elem.find('.//thermoml:VariableType', self.namespace)
        
        if var_type is None:
            return None
        
        # Extract variable type
        temperature = var_type.find('thermoml:eTemperature', self.namespace)
        
        if temperature is not None:
            param_type = Parameters.TEMPERATURE_K
            param_id = f"temperature_{self.unique_parameter_counter}"
            self.unique_parameter_counter += 1
        else:
            return None
        
        # Store mapping
        if var_number is not None:
            self.variable_map[var_number.text] = param_id
        
        return Parameter(
            parameterID=param_id,
            parameter=param_type
        )
    
    def _extract_measurements(self, data_elem: ET.Element, fluid_index: int, parameters: List[Parameter]) -> List[Measurement]:
        """Extract measurements from NumValues."""
        measurements = []
        num_values_elems = data_elem.findall('.//thermoml:NumValues', self.namespace)
        
        # Extract composition values from parameters for consistency
        composition_values = []
        for param in parameters:
            if param.parameter == Parameters.MOLE_FRACTION:
                # Find the corresponding constraint to get the actual value
                constraint_elems = data_elem.findall('.//thermoml:Constraint', self.namespace)
                for constr_elem in constraint_elems:
                    constr_type = constr_elem.find('.//thermoml:ConstraintType', self.namespace)
                    if constr_type is not None:
                        comp_comp = constr_type.find('thermoml:eComponentComposition', self.namespace)
                        if comp_comp is not None:
                            # Get the compound reference
                            reg_num = constr_elem.find('.//thermoml:RegNum//thermoml:nOrgNum', self.namespace)
                            compound_id = self.compound_map.get(reg_num.text) if reg_num is not None else None
                            
                            # Get the composition value
                            constr_value = constr_elem.find('thermoml:nConstraintValue', self.namespace)
                            composition_value = float(constr_value.text) if constr_value is not None else None
                            
                            # Check if this constraint matches the parameter
                            if compound_id and composition_value is not None:
                                expected_param_id = f"composition_{compound_id}_{composition_value}"
                                if param.parameterID == expected_param_id:
                                    composition_values.append(ParameterValue(
                                        parameterID=param.parameterID,
                                        paramValue=composition_value
                                    ))
                                    break
        
        for i, num_val_elem in enumerate(num_values_elems):
            # Extract property values
            property_values = self._extract_property_values(num_val_elem, fluid_index)
            
            # Extract variable values (temperature, pressure)
            parameter_values = self._extract_parameter_values(num_val_elem)
            
            # Combine all parameter values
            all_parameter_values = parameter_values + composition_values
            
            # Get method information from property definitions
            method_info = self._get_method_info(data_elem)
            
            # Create measurement
            measurement = Measurement(
                measurement_id=f"meas_{fluid_index+1}_{i+1}",
                propertyValue=property_values,
                parameterValue=all_parameter_values,
                method=method_info['method'],
                method_description=method_info['description']
            )
            
            measurements.append(measurement)
        
        return measurements
    
    def _get_method_info(self, data_elem: ET.Element) -> Dict[str, str]:
        """Get method information from property definitions."""
        # Look for properties in this data element
        property_elems = data_elem.findall('.//thermoml:Property', self.namespace)
        
        for prop_elem in property_elems:
            prop_number = prop_elem.find('thermoml:nPropNumber', self.namespace)
            if prop_number is not None and prop_number.text in self.property_definitions:
                prop_def = self.property_definitions[prop_number.text]
                if 'method_details' in prop_def and prop_def['method_details']:
                    return {
                        'method': Method.SIMULATED,
                        'description': prop_def['method_details']
                    }
        
        # Default method info
        return {
            'method': Method.SIMULATED,
            'description': "Molecular dynamics simulation in NPT ensemble"
        }
    
    def _extract_property_values(self, num_val_elem: ET.Element, fluid_index: int) -> List[PropertyValue]:
        """Extract property values from NumValues."""
        property_values = []
        prop_val_elems = num_val_elem.findall('.//thermoml:PropertyValue', self.namespace)
        
        for prop_val_elem in prop_val_elems:
            prop_number = prop_val_elem.find('thermoml:nPropNumber', self.namespace)
            prop_value = prop_val_elem.find('thermoml:nPropValue', self.namespace)
            uncertainty = prop_val_elem.find('.//thermoml:CombinedUncertainty//thermoml:nCombExpandUncertValue', self.namespace)
            
            if prop_number is not None:
                # Create unique key combining fluid index and property number
                unique_key = f"{fluid_index}_{prop_number.text}"
                property_id = self.property_map.get(unique_key, f"unknown_property_{prop_number.text}")
                
                property_value = PropertyValue(
                    propertyID=property_id,
                    propValue=float(prop_value.text) if prop_value is not None else None,
                    uncertainty=float(uncertainty.text) if uncertainty is not None else None
                )
                property_values.append(property_value)
        
        return property_values
    
    def _extract_parameter_values(self, num_val_elem: ET.Element) -> List[ParameterValue]:
        """Extract parameter values from NumValues."""
        parameter_values = []
        var_val_elems = num_val_elem.findall('.//thermoml:VariableValue', self.namespace)
        
        for var_val_elem in var_val_elems:
            var_number = var_val_elem.find('thermoml:nVarNumber', self.namespace)
            var_value = var_val_elem.find('thermoml:nVarValue', self.namespace)
            
            if var_number is not None and var_number.text in self.variable_map:
                parameter_value = ParameterValue(
                    parameterID=self.variable_map[var_number.text],
                    paramValue=float(var_value.text) if var_value is not None else None
                )
                parameter_values.append(parameter_value)
        
        return parameter_values

    def _extract_composition_values(self, fluid_elem: ET.Element) -> List[ParameterValue]:
        """Extract composition values from Constraints."""
        composition_values = []
        
        # Find all composition constraints - use the same logic as parameter extraction
        constraint_elems = fluid_elem.findall('.//thermoml:Constraint', self.namespace)
        
        for constr_elem in constraint_elems:
            constr_type = constr_elem.find('.//thermoml:ConstraintType', self.namespace)
            
            if constr_type is not None:
                # Check if it's a composition constraint
                comp_comp = constr_type.find('thermoml:eComponentComposition', self.namespace)
                
                if comp_comp is not None:
                    # Get the compound reference
                    reg_num = constr_elem.find('.//thermoml:RegNum//thermoml:nOrgNum', self.namespace)
                    compound_id = self.compound_map.get(reg_num.text) if reg_num is not None else None
                    
                    # Get the composition value
                    constr_value = constr_elem.find('thermoml:nConstraintValue', self.namespace)
                    composition_value = float(constr_value.text) if constr_value is not None else None
                    
                    if compound_id and composition_value is not None:
                        # Use the same parameter ID format as defined in the header
                        # This must match the IDs created in _convert_constraint_to_parameter
                        param_id = f"composition_{compound_id}_{composition_value}"
                        
                        composition_values.append(ParameterValue(
                            parameterID=param_id,
                            paramValue=composition_value
                        ))
        
        return composition_values


def main():
    """Main function to run the converter."""
    if len(sys.argv) != 2:
        print("Usage: python thermoml_to_fairfluids_converter_improved.py <thermoml_file.xml>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"Error: File {file_path} not found.")
        sys.exit(1)
    
    try:
        # Create converter and parse file
        converter = ImprovedThermoMLConverter()
        fairfluids_doc = converter.parse_thermoml_file(file_path)
        
        # Print summary
        print("\n" + "="*60)
        print("CONVERSION SUMMARY")
        print("="*60)
        print(f"Version: {fairfluids_doc.version.versionMajor}.{fairfluids_doc.version.versionMinor}")
        print(f"Citation: {fairfluids_doc.citation.title if fairfluids_doc.citation else 'None'}")
        print(f"Compounds: {len(fairfluids_doc.compound)}")
        print(f"Fluids: {len(fairfluids_doc.fluid)}")
        
        # Print compound details
        print("\nCompounds:")
        for compound in fairfluids_doc.compound:
            print(f"  - {compound.compoundID}: {compound.commonName}")
        
        # Print fluid details
        print("\nFluids:")
        for i, fluid in enumerate(fairfluids_doc.fluid):
            print(f"  - Fluid {i+1}: {len(fluid.compounds)} components, {len(fluid.measurement)} measurements")
        
        # Save to JSON
        try:
            output_file = Path(file_path).stem + "_improved_converted.json"
            with open(output_file, 'w') as f:
                import json
                
                # Custom JSON encoder to handle enums and other non-serializable objects
                class CustomJSONEncoder(json.JSONEncoder):
                    def default(self, obj):
                        if hasattr(obj, 'value'):  # Handle enums
                            return obj.value
                        if hasattr(obj, 'model_dump'):  # Handle Pydantic models
                            return obj.model_dump()
                        return str(obj)
                
                # Convert to dict first, then serialize
                if hasattr(fairfluids_doc, 'model_dump'):
                    data_dict = fairfluids_doc.model_dump(exclude_none=True)  # Exclude None values
                else:
                    # For mock classes, create a simple dict
                    data_dict = {}
                    for attr in dir(fairfluids_doc):
                        if not attr.startswith('_'):
                            value = getattr(fairfluids_doc, attr)
                            if not callable(value) and value is not None:  # Exclude None values
                                data_dict[attr] = value
                
                json.dump(data_dict, f, indent=2, cls=CustomJSONEncoder)
            print(f"\nConverted data saved to: {output_file}")
        except Exception as e:
            print(f"\nCould not save JSON file: {e}")
            print("This might be due to non-serializable objects in the data structure.")
        
        print("\nConversion completed successfully!")
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
