from typing import Optional, List, Dict, Any

import xml.etree.ElementTree as ET
from FAIRFluids.core.lib import *

class myFAIRFluidsDocument(FAIRFluidsDocument):
    """
    Extension of FAIRFluidsDocument with additional functionality for handling viscosity data
    and CML file parsing.
    """
    
    def show_mole_fractions(self) -> None:
        """
        Display the unique mole fraction combinations present in the viscosity data.
        """
        viscosity_data = self.get_viscosity_data()
        
        print("Available mole fraction combinations:")
        
        # Get compound names from first data point
        compounds = viscosity_data[0]['compound_identifiers']
        print(f"\nFormat: {' | '.join(compounds)}")
        print("-" * (len(compounds) * 15))
        
        # Create set of unique mole fraction combinations
        unique_fractions = set()
        for data in viscosity_data:
            # Round to 6 decimal places to avoid floating point comparison issues
            fractions = tuple(round(x, 6) for x in data['mole_fractions'])
            unique_fractions.add(fractions)
        
        # Sort by first component content (first value in tuple)
        for fractions in sorted(unique_fractions):
            print(f"{fractions[0]:.6f} | {fractions[1]:.6f} | {fractions[2]:.6f}")
        
        print(f"\nTotal unique compositions: {len(unique_fractions)}")

    def get_viscosity_data(self) -> List[Dict[str, Any]]:
        """
        Extract viscosity values and corresponding temperatures and mole fractions from fluids.
        
        Returns:
            List of dictionaries containing temperature, mole fractions and viscosity values
        """
        results = []
        if not hasattr(self, 'fluid') or not self.fluid:
            return results
            
        for fluid in self.fluid:
            # Skip if not a viscosity property
            if not (fluid.property and 
                    fluid.property.property_information and
                    fluid.property.property_information.property_name == "Dynamic viscosity, mPa·s"):
                continue
                
            # Extract values
            viscosity = fluid.num_value.propertyValue.propValue
            temperature = (fluid.num_value.parameterValue.varValue 
                         if fluid.num_value and fluid.num_value.parameterValue 
                         else None)
            
            # Get mole fraction from parameters - extract from varNumber field where we stored them
            mole_fractions = []
            compound_identifiers = []
            
            if fluid.num_value and fluid.num_value.parameterValue and fluid.num_value.parameterValue.varNumber:
                var_number = fluid.num_value.parameterValue.varNumber
                # Check if varNumber contains mole fraction data (format: var_ID_mf1,mf2,mf3)
                if "_" in var_number and "," in var_number:
                    try:
                        # Extract mole fraction values from varNumber
                        mole_fraction_part = var_number.split("_", 2)[2]  # Get part after var_ID_
                        mole_fraction_values = [float(x) for x in mole_fraction_part.split(",")]
                        mole_fractions = mole_fraction_values
                        
                        # Get compound identifiers from the fluid's compounds
                        if hasattr(self, 'compound') and self.compound:
                            compound_identifiers = [comp.compound_identifier.c_id for comp in self.compound if comp.compound_identifier]
                    except (ValueError, IndexError):
                        # If parsing fails, return empty lists
                        pass
                         
            results.append({
                'temperature': temperature,
                'mole_fractions': mole_fractions,
                'compound_identifiers': compound_identifiers,
                'viscosity': viscosity
            })
            
        return results

    def sum_num_values(self) -> float:
        """
        Sum all numerical property values across all fluids and store in compound 1's SELFIES field.
        
        Returns:
            Total sum of property values
        """
        total = 0.0
        if hasattr(self, 'fluid') and self.fluid:
            total = sum(fluid.num_value.propertyValue.propValue 
                       for fluid in self.fluid 
                       if fluid.num_value and fluid.num_value.propertyValue)
        
        self.add_selfies_to_compound(0, str(total))
        return total

    def add_selfies_to_compound(self, compound_id: int, selfies_string: str) -> None:
        """Add SELFIES string to specified compound"""
        if hasattr(self, 'compound') and self.compound and len(self.compound) > 0:
            self.compound[compound_id].SELFIE = selfies_string
            
    def _parse_cml_file(self, path_to_cml: str) -> ET.Element:
        """Parse CML file and return root element"""
        return ET.parse(path_to_cml).getroot()
        
    def _extract_properties(self, experiment: ET.Element) -> Dict[str, str]:
        """Extract properties from experiment module"""
        properties = {}
        property_list = experiment.find(".//{http://www.xml-cml.org/schema}propertyList")
        if property_list is not None:
            for prop in property_list:
                dict_ref = prop.get('dictRef')
                if dict_ref:
                    prop_type = dict_ref.split(':')[1] if ':' in dict_ref else dict_ref
                    scalar = prop.find(".//{http://www.xml-cml.org/schema}scalar")
                    if scalar is not None:
                        properties[prop_type] = scalar.text
        return properties
        
    def _extract_parameters(self, experiment: ET.Element) -> Dict[str, str]:
        """Extract parameters from experiment module"""
        parameters = {}
        param_list = experiment.find(".//{http://www.xml-cml.org/schema}parameterList")
        if param_list is not None:
            for param in param_list:
                dict_ref = param.get('dictRef')
                if dict_ref:
                    param_type = dict_ref.split(':')[1] if ':' in dict_ref else dict_ref
                    scalar = param.find(".//{http://www.xml-cml.org/schema}scalar")
                    if scalar is not None:
                        parameters[param_type] = scalar.text
        return parameters

    def _create_pressure_parameter(self, param_value: str, param_number: int) -> Parameter:
        """Create pressure parameter"""
        return Parameter(
            parameterID=f"pressure_param_{param_number}",
            parameterType=ParameterType(e_pressure=ePressure.PRESSURE_KPA),
            componentID=None
        )

    def _create_temperature_variable(self, param_value: str, var_number: int) -> Parameter:
        """Create temperature parameter"""
        return Parameter(
            parameterID=f"temp_var_{var_number}",
            parameterType=ParameterType(e_temperature=eTemperature.TEMPERATURE_K),
            componentID=None
        )

    def _create_mole_fraction_parameter(self, param_value: str, param_number: int, compound_identifier: Optional[str] = None) -> Parameter:
        """Create mole fraction parameter with optional compound identifier"""
        param_params = {
            "parameterID": f"mole_fraction_param_{param_number}",
            "parameterType": ParameterType(e_component_composition=eComponentComposition.MOLE_FRACTION),
            "componentID": None
        }
        
        return Parameter(**param_params)

    def _calculate_component_mole_fractions(self, molar_ratio_des: float, mole_fraction_water: float) -> Dict[str, float]:
        """
        Calculate individual component mole fractions from molar ratio and water fraction.
        
        Args:
            molar_ratio_des: Molar ratio of DES (component 1 to component 2 ratio)
            mole_fraction_water: Mole fraction of water
            
        Returns:
            Dictionary with mole fractions for each component
        """
        w = mole_fraction_water
        r = molar_ratio_des
        
        # Calculate the remaining mole fractions
        molar_constraint_water = w
        molar_constraint_component_1 = (r * (1 - molar_constraint_water)) / (r + 1)
        molar_constraint_component_2 = (1 - molar_constraint_water) - molar_constraint_component_1
        
        return {
            'water': molar_constraint_water,
            'component_1': molar_constraint_component_1,
            'component_2': molar_constraint_component_2
        }

    def _create_variables(self, exp: Dict[str, str]) -> List[Parameter]:
        """Create variables from experiment parameters"""
        variables = []
        if 'temperature' in exp:
            variables.append(self._create_temperature_variable(exp['temperature'], 1))
        return variables

    def _auto_map_components_to_compounds(self, component_fractions: Dict[str, float], compound_name_to_cid: Dict[str, str]) -> Dict[str, str]:
        """
        Automatically map calculated component fractions to available compounds.
        
        Args:
            component_fractions: Dictionary of calculated component fractions
            compound_name_to_cid: Mapping from compound names to their c_ids
            
        Returns:
            Dictionary mapping component names to c_ids
        """
        available_compounds = list(compound_name_to_cid.keys())
        component_to_cid = {}
        
        # Strategy 1: Try exact name matching first
        for component_name in component_fractions.keys():
            if component_name in compound_name_to_cid:
                component_to_cid[component_name] = compound_name_to_cid[component_name]
        
        # Strategy 2: Handle common component naming patterns
        for component_name in component_fractions.keys():
            if component_name not in component_to_cid:
                if component_name == 'water':
                    # Look for water-like compounds
                    water_candidates = [name for name in available_compounds 
                                      if name.lower() in ['water', 'h2o', 'oxidane']]
                    if water_candidates:
                        component_to_cid[component_name] = compound_name_to_cid[water_candidates[0]]
                
                elif component_name.startswith('component_'):
                    # Handle generic component names (component_1, component_2, etc.)
                    try:
                        component_num = int(component_name.split('_')[1])
                        if component_num < len(available_compounds):
                            component_to_cid[component_name] = compound_name_to_cid[available_compounds[component_num]]
                    except (ValueError, IndexError):
                        pass
        
        # Strategy 3: Index-based fallback for unmapped components
        unmapped_components = [name for name in component_fractions.keys() if name not in component_to_cid]
        unused_compounds = [name for name in available_compounds 
                          if name not in component_to_cid.values()]
        
        for i, component_name in enumerate(unmapped_components):
            if i < len(unused_compounds):
                component_to_cid[component_name] = compound_name_to_cid[unused_compounds[i]]
        
        return component_to_cid

    def _create_parameters(self, exp: Dict[str, str]) -> List[Parameter]:
        """Create parameters from experiment parameters"""
        parameters = []
        param_count = 1
        
        # Build a mapping from commonName to c_id for all compounds in the document
        compound_name_to_cid = {}
        if hasattr(self, 'compound') and self.compound:
            for comp in self.compound:
                if comp.commonName and comp.compound_identifier and comp.compound_identifier.c_id:
                    compound_name_to_cid[comp.commonName] = comp.compound_identifier.c_id
        
        # Check if we have both molar ratio and water fraction to calculate component mole fractions
        if 'molar_ratio_of_DES' in exp and 'mole_fraction_of_water' in exp:
            molar_ratio = float(exp['molar_ratio_of_DES'])
            water_fraction = float(exp['mole_fraction_of_water'])
            
            # Calculate individual component mole fractions
            component_fractions = self._calculate_component_mole_fractions(molar_ratio, water_fraction)
            
            # Automatically map components to compounds
            component_to_cid = self._auto_map_components_to_compounds(component_fractions, compound_name_to_cid)
            
            # Create parameters for each component
            for component_name, fraction in component_fractions.items():
                c_id = component_to_cid.get(component_name)
                parameters.append(self._create_mole_fraction_parameter(str(fraction), param_count, c_id))
                param_count += 1
        else:
            # Fallback to original logic if we don't have both parameters
            # This handles cases where we only have individual mole fractions
            if 'mole_fraction_of_water' in exp:
                c_id = compound_name_to_cid.get('Water')
                parameters.append(self._create_mole_fraction_parameter(exp['mole_fraction_of_water'], param_count, c_id))
                param_count += 1
                
            if 'molar_ratio_of_DES' in exp:
                # For molar ratio, we need to determine which component it refers to
                # This could be the first non-water component
                non_water_compounds = [name for name in compound_name_to_cid.keys() if name.lower() != 'water']
                c_id = compound_name_to_cid.get(non_water_compounds[0]) if non_water_compounds else None
                parameters.append(self._create_mole_fraction_parameter(exp['molar_ratio_of_DES'], param_count, c_id))
                param_count += 1
                
        if 'pressure' in exp:
            parameters.append(self._create_pressure_parameter(exp['pressure'], param_count))
            
        return parameters

    def _create_property(self, exp_id: str) -> Property:
        """Create property from experiment ID"""
        return Property(
            propertyID=f"viscosity_{exp_id}",
            property_information=Property_Information(
                group="TransportProp",
                method="experimental",
                property_name="Dynamic viscosity, mPa·s"
            )
        )
        
    def _add_fluid_data(self, doi: str, exp: Dict[str, str], variables: List[Parameter], 
                        parameters: List[Parameter]) -> None:
        """Add fluid data to document"""
        viscosity_value = exp.get('value_viscosity') or exp.get('c', 0)
        temperature_value = exp.get('temperature', 0)
        exp_id = exp.get('ID', '001')
        
        # Extract mole fraction values for storage
        mole_fraction_values = []
        if 'molar_ratio_of_DES' in exp and 'mole_fraction_of_water' in exp:
            molar_ratio = float(exp['molar_ratio_of_DES'])
            water_fraction = float(exp['mole_fraction_of_water'])
            component_fractions = self._calculate_component_mole_fractions(molar_ratio, water_fraction)
            mole_fraction_values = list(component_fractions.values())
        elif 'mole_fraction_of_water' in exp:
            mole_fraction_values = [float(exp['mole_fraction_of_water'])]
        
        # Store mole fraction values in the parameterValue if available
        # For now, we'll store them as a comma-separated string in the varNumber field
        mole_fraction_str = ",".join(map(str, mole_fraction_values)) if mole_fraction_values else ""
        
        self.add_to_fluid(
            source_doi=doi,
            property=self._create_property(exp_id),
            parameter=parameters,
            num_value=NumValue(
                propertyValue=PropertyValue(
                    propDigits=4,
                    propNumber=f"prop_{exp_id}",
                    propValue=float(viscosity_value),
                    uncertainty=float(exp.get('error_viscosity', 0)) if exp.get('error_viscosity') != 'NG' else 0
                ),
                parameterValue=ParameterValue(
                    varDigits=2,
                    varNumber=f"var_{exp_id}_{mole_fraction_str}" if mole_fraction_str else f"var_{exp_id}",
                    varValue=float(temperature_value)
                )
            )
        )

    def get_data_from_cml(self, path_to_cml: str) -> 'myFAIRFluidsDocument':
        """
        Create FAIRFluids document from CML file.
        
        Args:
            path_to_cml: Path to the CML file to parse
            
        Returns:
            Self for method chaining
        """
        root = self._parse_cml_file(path_to_cml)
        doi_properties: Dict[str, List[Dict[str, str]]] = {}

        # Find and process all experiment modules
        for experiment in root.findall(".//{http://www.xml-cml.org/schema}module[@dictRef='des:experiment']"):
            properties = self._extract_properties(experiment)
            parameters = self._extract_parameters(experiment)

            if doi := properties.get('DOI'):
                if doi not in doi_properties:
                    doi_properties[doi] = []
                doi_properties[doi].append({**properties, **parameters})

        # Create fluids from collected data
        for doi, experiments in doi_properties.items():
            for exp in experiments:
                variables = self._create_variables(exp)
                parameters = self._create_parameters(exp)
                self._add_fluid_data(doi, exp, variables, parameters)
        
        return self