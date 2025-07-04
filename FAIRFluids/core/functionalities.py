from typing import Optional, List, Dict, Any

import xml.etree.ElementTree as ET
from FAIRFluids.core.lib import (
    FAIRFluidsDocument, Version, Citation, Author, Compound, 
    Fluid, Property, Property_Group, Variable, Constraint, 
    NumValue, PropertyValue, VariableValue, ConstraintVariableType,
    eTemperature, ePressure, eComponentComposition, C_id
)

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
                    fluid.property.property_group and
                    fluid.property.property_group.property_name == "Dynamic viscosity, mPa·s"):
                continue
                
            # Extract values
            viscosity = fluid.num_value.propertyValue.propValue
            temperature = (fluid.num_value.variableValue.varValue 
                         if fluid.num_value and fluid.num_value.variableValue 
                         else None)
            
            # Get mole fraction from constraints with compound identifiers
            mole_fractions = []
            compound_identifiers = []
            if fluid.constraint:
                for constraint in fluid.constraint:
                    if (constraint.constraint_type and 
                        constraint.constraint_type.e_component_composition == eComponentComposition.MOLE_FRACTION):
                        mole_fractions.append(constraint.constraint_value)
                        # Get compound identifier if available
                        compound_id = (constraint.compound_identifier.c_id 
                                     if constraint.compound_identifier else None)
                        compound_identifiers.append(compound_id)
                         
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

    def _create_pressure_constraint(self, param_value: str, constraint_number: int) -> Constraint:
        """Create pressure constraint"""
        return Constraint(
            constraint_type=ConstraintVariableType(e_Pressure="Pressure, kPa"),
            constraint_digits=3,
            constraint_value=float(param_value),
            constraint_number=constraint_number
        )

    def _create_temperature_variable(self, param_value: str, var_number: int) -> Variable:
        """Create temperature variable"""
        return Variable(
            variableID=f"temp_var_{var_number}",
            variableType=ConstraintVariableType(e_temperature=eTemperature.TEMPERATURE_K),
            variableName="Temperature"
        )

    def _create_mole_fraction_constraint(self, param_value: str, constraint_number: int, compound_identifier: Optional[str] = None) -> Constraint:
        """Create mole fraction constraint with optional compound identifier"""
        constraint_params = {
            "constraint_type": ConstraintVariableType(
                e_component_composition=eComponentComposition.MOLE_FRACTION
            ),
            "constraint_digits": 3,
            "constraint_value": float(param_value),
            "constraint_number": constraint_number
        }
        
        # Add compound identifier if provided
        if compound_identifier:
            constraint_params["compound_identifier"] = C_id(c_id=compound_identifier)
            
        return Constraint(**constraint_params)

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

    def _create_variables(self, exp: Dict[str, str]) -> List[Variable]:
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

    def _create_constraints(self, exp: Dict[str, str]) -> List[Constraint]:
        """Create constraints from experiment parameters"""
        constraints = []
        constraint_count = 1
        
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
            
            # Create constraints for each component
            for component_name, fraction in component_fractions.items():
                c_id = component_to_cid.get(component_name)
                constraints.append(self._create_mole_fraction_constraint(str(fraction), constraint_count, c_id))
                constraint_count += 1
        else:
            # Fallback to original logic if we don't have both parameters
            # This handles cases where we only have individual mole fractions
            if 'mole_fraction_of_water' in exp:
                c_id = compound_name_to_cid.get('Water')
                constraints.append(self._create_mole_fraction_constraint(exp['mole_fraction_of_water'], constraint_count, c_id))
                constraint_count += 1
                
            if 'molar_ratio_of_DES' in exp:
                # For molar ratio, we need to determine which component it refers to
                # This could be the first non-water component
                non_water_compounds = [name for name in compound_name_to_cid.keys() if name.lower() != 'water']
                c_id = compound_name_to_cid.get(non_water_compounds[0]) if non_water_compounds else None
                constraints.append(self._create_mole_fraction_constraint(exp['molar_ratio_of_DES'], constraint_count, c_id))
                constraint_count += 1
                
        if 'pressure' in exp:
            constraints.append(self._create_pressure_constraint(exp['pressure'], constraint_count))
            
        return constraints

    def _create_property(self, exp_id: str) -> Property:
        """Create property from experiment ID"""
        return Property(
            propertyID=f"viscosity_{exp_id}",
            property_group=Property_Group(
                group="TransportProp",
                method="experimental",
                property_name="Dynamic viscosity, mPa·s"
            )
        )
        
    def _add_fluid_data(self, doi: str, exp: Dict[str, str], variables: List[Variable], 
                        constraints: List[Constraint]) -> None:
        """Add fluid data to document"""
        viscosity_value = exp.get('value_viscosity') or exp.get('c', 0)
        temperature_value = exp.get('temperature', 0)
        exp_id = exp.get('ID', '001')
        
        self.add_to_fluid(
            source_doi=doi,
            property=self._create_property(exp_id),
            variable=variables[0] if variables else None,
            constraint=constraints,
            num_value=NumValue(
                propertyValue=PropertyValue(
                    propDigits=4,
                    propNumber=f"prop_{exp_id}",
                    propValue=float(viscosity_value),
                    uncertainty=float(exp.get('error_viscosity', 0)) if exp.get('error_viscosity') != 'NG' else 0
                ),
                variableValue=VariableValue(
                    varDigits=2,
                    varNumber=f"var_{exp_id}",
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
                constraints = self._create_constraints(exp)
                self._add_fluid_data(doi, exp, variables, constraints)
        
        return self