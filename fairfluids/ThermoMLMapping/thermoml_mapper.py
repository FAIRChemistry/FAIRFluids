"""
ThermoML to FAIRFluids Mapper

This module contains the main ThermoMLMapper class that converts ThermoML XML data
to FAIRFluids format. It handles the complete conversion process including
compounds, citations, properties, parameters, and measurements.
"""

import xml.etree.ElementTree as ET
import uuid
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

# Import FAIRFluids models
import sys

sys.path.append("/home/sga/Code/FAIRFluids")
from fairfluids.core.fairfluids import (
    FAIRFluidsDocument,
    Version,
    Citation,
    Author,
    Compound,
    Fluid,
    Property,
    Parameter,
    Measurement,
    PropertyValue,
    ParameterValue,
    UnitDefinition,
    BaseUnit,
)

# Import enums from lib since they don't need extension
from fairfluids.core.lib import (
    LitType,
    Method,
    Properties,
    Parameters,
)

from .conversion_utils import (
    ThermoMLPropertyMapper,
    ThermoMLParameterMapper,
    ThermoMLMethodMapper,
    ThermoMLLitTypeMapper,
    extract_text_content,
    extract_numeric_value,
    extract_integer_value,
    clean_doi,
    parse_authors,
    create_unit_definition,
)

# Import the filtering function from functionalities
import sys

sys.path.append("/home/sga/Code/FAIRFluids")
from fairfluids.core.functionalities import filter_fluid_compounds_by_mole_fractions


class ThermoMLMapper:
    """
    Main class for converting ThermoML XML data to FAIRFluids format.
    """

    def __init__(self, source_doi: Optional[str] = None):
        """Initialize the mapper with default settings.

        Args:
            source_doi: Optional DOI to assign to all measurements. If not
                provided, the mapper will try to derive it from the ThermoML
                header citation and use that value for all measurements.
        """
        self.property_mapper = ThermoMLPropertyMapper()
        self.parameter_mapper = ThermoMLParameterMapper()
        self.method_mapper = ThermoMLMethodMapper()
        self.lit_type_mapper = ThermoMLLitTypeMapper()

        # Track IDs for referencing
        self.compound_id_map: Dict[int, str] = {}
        self.property_id_map: Dict[int, str] = {}
        # Separate maps to avoid number collisions between constraints and variables
        self.constraint_id_map: Dict[int, str] = {}
        self.variable_id_map: Dict[int, str] = {}

        # Global DOI to stamp onto all measurements
        # If explicitly provided, use it for all files; otherwise extract per file
        self.explicit_source_doi: Optional[str] = source_doi
        self.source_doi: Optional[str] = source_doi

    def convert_file(self, xml_file_path: Union[str, Path]) -> FAIRFluidsDocument:
        """
        Convert a ThermoML XML file to FAIRFluids format.

        Args:
            xml_file_path: Path to the ThermoML XML file

        Returns:
            FAIRFluidsDocument object
        """
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        return self.convert_xml(root)

    def convert_xml(self, root: ET.Element) -> FAIRFluidsDocument:
        """
        Convert ThermoML XML root element to FAIRFluids format.

        Args:
            root: The root XML element

        Returns:
            FAIRFluidsDocument object
        """
        # Create the main document
        document = FAIRFluidsDocument()

        # Store reference to document for compound lookup
        self.document = document

        # Convert version information
        version_elem = root.find(".//{http://www.iupac.org/namespaces/ThermoML}Version")
        if version_elem is not None:
            document.version = self._convert_version(version_elem)

        # Convert citation information
        citation_elem = root.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}Citation"
        )
        if citation_elem is not None:
            document.citation = self._convert_citation(citation_elem)

        # If no explicit source_doi was provided at initialization, 
        # extract it from the citation for THIS file
        # This ensures each file gets its own DOI, not the DOI from the first file
        if self.explicit_source_doi is None and getattr(document, "citation", None) is not None:
            self.source_doi = getattr(document.citation, "doi", None)

        # Convert compounds
        compound_elems = root.findall(
            ".//{http://www.iupac.org/namespaces/ThermoML}Compound"
        )
        for compound_elem in compound_elems:
            compound = self._convert_compound(compound_elem)
            document.compound.append(compound)

        # Convert fluid data (multiple fluids)
        fluids = self._convert_fluid_data(root)
        for fluid in fluids:
            # Filter compounds to only include those with non-zero mole fractions
            filter_fluid_compounds_by_mole_fractions(fluid)
            document.fluid.append(fluid)

        return document

    def _convert_version(self, version_elem: ET.Element) -> Version:
        """Convert ThermoML Version element to FAIRFluids Version."""
        version = Version()

        major_elem = version_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}nVersionMajor"
        )
        if major_elem is not None:
            version.versionMajor = extract_integer_value(major_elem)

        minor_elem = version_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}nVersionMinor"
        )
        if minor_elem is not None:
            version.versionMinor = extract_integer_value(minor_elem)

        return version

    def _convert_citation(self, citation_elem: ET.Element) -> Citation:
        """Convert ThermoML Citation element to FAIRFluids Citation."""
        citation = Citation()

        # Convert literature type
        lit_type_elem = citation_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}eType"
        )
        if lit_type_elem is not None:
            lit_type_str = extract_text_content(lit_type_elem)
            if lit_type_str:
                mapped_lit_type = self.lit_type_mapper.map_lit_type(lit_type_str)
                if mapped_lit_type and mapped_lit_type in LitType.__members__:
                    citation.litType = LitType[mapped_lit_type]

        # Convert authors
        author_elems = citation_elem.findall(
            ".//{http://www.iupac.org/namespaces/ThermoML}sAuthor"
        )
        for author_elem in author_elems:
            author_text = extract_text_content(author_elem)
            if author_text:
                authors = parse_authors(author_text)
                for author_data in authors:
                    author = Author(**author_data)
                    citation.author.append(author)

        # Convert DOI
        doi_elem = citation_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}sDOI"
        )
        if doi_elem is not None:
            doi_text = extract_text_content(doi_elem)
            if doi_text:
                citation.doi = clean_doi(doi_text)

        # Publication metadata
        pub_name_elem = citation_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}sPubName"
        )
        if pub_name_elem is not None:
            citation.pub_name = extract_text_content(pub_name_elem)

        pub_year_elem = citation_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}yrPubYr"
        )
        if pub_year_elem is not None:
            citation.publication_year = extract_text_content(pub_year_elem)

        title_elem = citation_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}sTitle"
        )
        if title_elem is not None:
            citation.title = extract_text_content(title_elem)

        vol_elem = citation_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}sVol"
        )
        if vol_elem is not None:
            citation.lit_volume_num = extract_text_content(vol_elem)

        page_elem = citation_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}sPage"
        )
        if page_elem is not None:
            citation.page = extract_text_content(page_elem)

        return citation

    def _convert_compound(self, compound_elem: ET.Element) -> Compound:
        """Convert ThermoML Compound element to FAIRFluids Compound."""
        compound = Compound()

        # PubChem ID
        pubchem_elem = compound_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}nPubChemID"
        )
        if pubchem_elem is not None:
            compound.pubChemID = extract_integer_value(pubchem_elem)

        # Names and identifiers
        common_name_elems = compound_elem.findall(
            ".//{http://www.iupac.org/namespaces/ThermoML}sCommonName"
        )
        if common_name_elems:
            compound.commonName = extract_text_content(common_name_elems[0])

        iupac_elem = compound_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}sIUPACName"
        )
        if iupac_elem is not None:
            compound.name_IUPAC = extract_text_content(iupac_elem)

        inchi_elem = compound_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}sStandardInChI"
        )
        if inchi_elem is not None:
            compound.standard_InChI = extract_text_content(inchi_elem)

        inchikey_elem = compound_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}sStandardInChIKey"
        )
        if inchikey_elem is not None:
            compound.standard_InChI_key = extract_text_content(inchikey_elem)

        # Generate consistent compound ID: compound_<common_name> or compound_<pubChemID> or compound_<org_num>
        regnum_elem = compound_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}RegNum"
        )
        if regnum_elem is not None:
            orgnum_elem = regnum_elem.find(
                ".//{http://www.iupac.org/namespaces/ThermoML}nOrgNum"
            )
            if orgnum_elem is not None:
                org_num = extract_integer_value(orgnum_elem)
                if org_num is not None:
                    # Generate consistent compound ID
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
                        compound_id = f"compound_{org_num}"

                    compound.compoundID = compound_id
                    self.compound_id_map[org_num] = compound.compoundID

        return compound

    def _convert_fluid_data(self, root: ET.Element) -> List[Fluid]:
        """Convert ThermoML fluid data to FAIRFluids Fluid list."""
        fluids = []

        # Find all PureOrMixtureData elements
        data_elems = root.findall(
            ".//{http://www.iupac.org/namespaces/ThermoML}PureOrMixtureData"
        )

        if not data_elems:
            return fluids

        # Process each data element as a separate fluid
        for data_elem in data_elems:
            fluid = self._process_data_element(data_elem)
            if fluid:
                fluids.append(fluid)

        return fluids

    def _process_data_element(self, data_elem: ET.Element) -> Optional[Fluid]:
        """Process a single PureOrMixtureData element and return a Fluid."""
        # Generate UUID for fluidID
        fluid_uuid = str(uuid.uuid4())
        fluid = Fluid(fluidID=[fluid_uuid])

        # Extract compounds involved using common names
        components = data_elem.findall(
            ".//{http://www.iupac.org/namespaces/ThermoML}Component"
        )
        for component in components:
            regnum_elem = component.find(
                ".//{http://www.iupac.org/namespaces/ThermoML}RegNum"
            )
            if regnum_elem is not None:
                orgnum_elem = regnum_elem.find(
                    ".//{http://www.iupac.org/namespaces/ThermoML}nOrgNum"
                )
                if orgnum_elem is not None:
                    org_num = extract_integer_value(orgnum_elem)
                    if org_num and org_num in self.compound_id_map:
                        # Get the compound and use its common name
                        compound_id = self.compound_id_map[org_num]
                        # Find the compound in our document to get compound ID
                        for compound in self.document.compound:
                            if compound.compoundID == compound_id:
                                if compound.compoundID not in fluid.compounds:
                                    fluid.compounds.append(compound.compoundID)
                                break

        # Extract properties with method information (include all properties)
        properties = data_elem.findall(
            ".//{http://www.iupac.org/namespaces/ThermoML}Property"
        )
        for prop_elem in properties:
            property_obj = self._convert_property(prop_elem)
            if property_obj:
                fluid.property.append(property_obj)

        # Extract constraints (parameters with fixed values) and collect their values
        constraints = data_elem.findall(
            ".//{http://www.iupac.org/namespaces/ThermoML}Constraint"
        )
        constraint_values: Dict[str, float] = {}
        for constraint_elem in constraints:
            parameter_obj = self._convert_constraint(constraint_elem)
            if parameter_obj:
                fluid.parameter.append(parameter_obj)
            # collect value for later injection into all measurements
            constr_num_elem = constraint_elem.find(
                ".//{http://www.iupac.org/namespaces/ThermoML}nConstraintNumber"
            )
            constr_val_elem = constraint_elem.find(
                ".//{http://www.iupac.org/namespaces/ThermoML}nConstraintValue"
            )
            if constr_num_elem is not None and constr_val_elem is not None:
                constr_num = extract_integer_value(constr_num_elem)
                constr_val = extract_numeric_value(constr_val_elem)
                if constr_num is not None and constr_val is not None:
                    cid = self.constraint_id_map.get(constr_num)
                    if cid:
                        constraint_values[cid] = constr_val

        # Extract variables (parameters with varying values)
        variables = data_elem.findall(
            ".//{http://www.iupac.org/namespaces/ThermoML}Variable"
        )
        for variable_elem in variables:
            parameter_obj = self._convert_variable(variable_elem)
            if parameter_obj:
                fluid.parameter.append(parameter_obj)

        # Extract measurements and add constraint values to each
        measurements = self._extract_measurements(data_elem, constraint_values)
        for measurement in measurements:
            fluid.measurement.append(measurement)

        # Identify solvent compounds from Property elements (if specified)
        solvent_compounds = set()
        properties = data_elem.findall(
            ".//{http://www.iupac.org/namespaces/ThermoML}Property"
        )
        for prop_elem in properties:
            solvent_elems = prop_elem.findall(
                ".//{http://www.iupac.org/namespaces/ThermoML}Solvent"
            )
            for solvent_elem in solvent_elems:
                regnum_elem = solvent_elem.find(
                    ".//{http://www.iupac.org/namespaces/ThermoML}RegNum"
                )
                if regnum_elem is not None:
                    orgnum_elem = regnum_elem.find(
                        ".//{http://www.iupac.org/namespaces/ThermoML}nOrgNum"
                    )
                    if orgnum_elem is not None:
                        org_num = extract_integer_value(orgnum_elem)
                        if org_num and org_num in self.compound_id_map:
                            compound_id = self.compound_id_map[org_num]
                            solvent_compounds.add(compound_id)

        # Store solvent information for use in ratio conversion
        fluid._solvent_compounds = solvent_compounds  # type: ignore

        # Handle implicit mole fractions for components without explicit parameters
        # This is needed when some components have explicit mole fractions but others don't
        # (e.g., in ternary mixtures where one component's mole fraction is implicit)
        self._add_implicit_mole_fractions(fluid)

        return fluid

    def _convert_property(self, prop_elem: ET.Element) -> Optional[Property]:
        """Convert ThermoML Property element to FAIRFluids Property."""
        property_obj = Property()

        # Get property number (used as fallback and for referencing)
        prop_num: Optional[int] = None
        prop_num_elem = prop_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}nPropNumber"
        )
        if prop_num_elem is not None:
            prop_num = extract_integer_value(prop_num_elem)

        # Get property name
        semantic_id: Optional[str] = None
        prop_name_elem = prop_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}ePropName"
        )
        if prop_name_elem is not None:
            prop_name = extract_text_content(prop_name_elem)
            if prop_name:
                mapped_prop = self.property_mapper.map_property(prop_name)
                if mapped_prop and mapped_prop in Properties.__members__:
                    # Use semantic enum value as propertyID
                    semantic_id = mapped_prop
                    property_obj.properties = Properties[mapped_prop]

                # Create unit definition from source prop name
                unit_def = create_unit_definition(
                    prop_name, f"unit_{prop_name.replace(' ', '_')}"
                )
                property_obj.unit = UnitDefinition(**unit_def)

        # Assign propertyID (semantic preferred, fallback to numeric-based)
        if semantic_id is None and prop_num is not None:
            semantic_id = f"property_{prop_num}"
        if semantic_id is None:
            # Ultimate fallback (should not happen normally)
            semantic_id = "property"
        property_obj.propertyID = semantic_id

        # Store mapping for measurement references
        if prop_num is not None:
            self.property_id_map[prop_num] = semantic_id

        return property_obj

    def _convert_constraint(self, constraint_elem: ET.Element) -> Optional[Parameter]:
        """Convert ThermoML Constraint element to FAIRFluids Parameter."""
        parameter_obj = Parameter()

        # Determine associated compound (if any) early for ID construction
        associated_common_name = None
        regnum_elem = constraint_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}RegNum"
        )
        if regnum_elem is not None:
            orgnum_elem = regnum_elem.find(
                ".//{http://www.iupac.org/namespaces/ThermoML}nOrgNum"
            )
            if orgnum_elem is not None:
                org_num = extract_integer_value(orgnum_elem)
                if org_num and org_num in self.compound_id_map:
                    compound_id = self.compound_id_map[org_num]
                    for compound in self.document.compound:
                        if compound.compoundID == compound_id:
                            associated_common_name = compound.commonName
                            if (
                                compound.compoundID
                                not in parameter_obj.associated_compounds
                            ):
                                parameter_obj.associated_compounds.append(
                                    compound.compoundID
                                )
                            break

        # Get constraint number to keep a map for value injection
        constr_num_elem = constraint_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}nConstraintNumber"
        )
        constr_num_val: Optional[int] = None
        if constr_num_elem is not None:
            constr_num_val = extract_integer_value(constr_num_elem)

        # Get constraint type and assign semantic parameter IDs
        constraint_type_elem = constraint_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}ConstraintType"
        )
        if constraint_type_elem is not None:
            # Component composition → Mole fraction
            comp_comp_elem = constraint_type_elem.find(
                ".//{http://www.iupac.org/namespaces/ThermoML}eComponentComposition"
            )
            if comp_comp_elem is not None:
                comp_type = extract_text_content(comp_comp_elem)
                if comp_type:
                    mapped_param = self.parameter_mapper.map_parameter(comp_type)
                    if mapped_param and mapped_param in Parameters.__members__:
                        parameter_obj.parameter = Parameters[mapped_param]
                # Semantic ID for visualization: parameter_mole_fraction_<name>
                if associated_common_name:
                    # Clean the common name to ensure consistency with compound IDs
                    clean_name = (
                        associated_common_name.lower()
                        .replace(" ", "")
                        .replace("-", "")
                        .replace("_", "")
                    )
                    parameter_obj.parameterID = f"parameter_mole_fraction_{clean_name}"
                else:
                    parameter_obj.parameterID = "parameter_mole_fraction"

            # Solvent composition → Mole fraction (same logic as component composition)
            solvent_comp_elem = constraint_type_elem.find(
                ".//{http://www.iupac.org/namespaces/ThermoML}eSolventComposition"
            )
            if solvent_comp_elem is not None:
                solvent_type = extract_text_content(solvent_comp_elem)
                if solvent_type:
                    # Map "Solvent: Mole fraction" to "Mole fraction" via parameter mapper
                    mapped_param = self.parameter_mapper.map_parameter(solvent_type)
                    if mapped_param and mapped_param in Parameters.__members__:
                        parameter_obj.parameter = Parameters[mapped_param]
                # Semantic ID for visualization: parameter_mole_fraction_<name>
                if associated_common_name:
                    # Clean the common name to ensure consistency with compound IDs
                    clean_name = (
                        associated_common_name.lower()
                        .replace(" ", "")
                        .replace("-", "")
                        .replace("_", "")
                    )
                    parameter_obj.parameterID = f"parameter_mole_fraction_{clean_name}"
                else:
                    parameter_obj.parameterID = "parameter_mole_fraction"

            # Pressure constraint
            pressure_elem = constraint_type_elem.find(
                ".//{http://www.iupac.org/namespaces/ThermoML}ePressure"
            )
            if pressure_elem is not None:
                pressure_type = extract_text_content(pressure_elem)
                if pressure_type:
                    mapped_param = self.parameter_mapper.map_parameter(pressure_type)
                    if mapped_param and mapped_param in Parameters.__members__:
                        parameter_obj.parameter = Parameters[mapped_param]
                # Semantic ID for pressure
                parameter_obj.parameterID = "parameter_pressure_kPa"

        # Backfill constraint_id_map for value injection
        if constr_num_val is not None and parameter_obj.parameterID:
            self.constraint_id_map[constr_num_val] = parameter_obj.parameterID

        return parameter_obj

    def _convert_variable(self, variable_elem: ET.Element) -> Optional[Parameter]:
        """Convert ThermoML Variable element to FAIRFluids Parameter."""
        parameter_obj = Parameter()

        # Get variable number (we still keep a map for linking values)
        var_num_elem = variable_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}nVarNumber"
        )
        var_num_val: Optional[int] = None
        if var_num_elem is not None:
            var_num_val = extract_integer_value(var_num_elem)

        # Determine associated compound (if any) early for ID construction
        associated_common_name = None
        regnum_elem = variable_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}RegNum"
        )
        if regnum_elem is not None:
            orgnum_elem = regnum_elem.find(
                ".//{http://www.iupac.org/namespaces/ThermoML}nOrgNum"
            )
            if orgnum_elem is not None:
                org_num = extract_integer_value(orgnum_elem)
                if org_num and org_num in self.compound_id_map:
                    compound_id = self.compound_id_map[org_num]
                    for compound in self.document.compound:
                        if compound.compoundID == compound_id:
                            associated_common_name = compound.commonName
                            if (
                                compound.compoundID
                                not in parameter_obj.associated_compounds
                            ):
                                parameter_obj.associated_compounds.append(
                                    compound.compoundID
                                )
                            break

        # Get variable type
        var_type_elem = variable_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}VariableType"
        )
        if var_type_elem is not None:
            # Temperature
            temp_elem = var_type_elem.find(
                ".//{http://www.iupac.org/namespaces/ThermoML}eTemperature"
            )
            if temp_elem is not None:
                temp_type = extract_text_content(temp_elem)
                if temp_type:
                    mapped_param = self.parameter_mapper.map_parameter(temp_type)
                    if mapped_param and mapped_param in Parameters.__members__:
                        parameter_obj.parameter = Parameters[mapped_param]
                # Semantic ID for visualization
                parameter_obj.parameterID = "parameter_temperature"

            # Pressure
            pressure_elem = var_type_elem.find(
                ".//{http://www.iupac.org/namespaces/ThermoML}ePressure"
            )
            if pressure_elem is not None:
                pressure_type = extract_text_content(pressure_elem)
                if pressure_type:
                    mapped_param = self.parameter_mapper.map_parameter(pressure_type)
                    if mapped_param and mapped_param in Parameters.__members__:
                        parameter_obj.parameter = Parameters[mapped_param]
                # Semantic ID for pressure
                parameter_obj.parameterID = "parameter_pressure_kPa"

            # Component composition (mole fraction, etc.)
            comp_comp_elem = var_type_elem.find(
                ".//{http://www.iupac.org/namespaces/ThermoML}eComponentComposition"
            )
            if comp_comp_elem is not None:
                comp_type = extract_text_content(comp_comp_elem)
                if comp_type:
                    mapped_param = self.parameter_mapper.map_parameter(comp_type)
                    if mapped_param and mapped_param in Parameters.__members__:
                        parameter_obj.parameter = Parameters[mapped_param]

                    # Create semantic ID based on parameter type
                    # For mole fraction, use "parameter_mole_fraction_<name>"
                    # For ratios, use "parameter_<ratio_type>_<name>"
                    if "mole fraction" in mapped_param.lower():
                        if associated_common_name:
                            clean_name = (
                                associated_common_name.lower()
                                .replace(" ", "")
                                .replace("-", "")
                                .replace("_", "")
                            )
                            parameter_obj.parameterID = (
                                f"parameter_mole_fraction_{clean_name}"
                            )
                        else:
                            parameter_obj.parameterID = "parameter_mole_fraction"
                    elif "ratio" in mapped_param.lower():
                        # For ratio parameters, create ID based on ratio type
                        if associated_common_name:
                            clean_name = (
                                associated_common_name.lower()
                                .replace(" ", "")
                                .replace("-", "")
                                .replace("_", "")
                            )
                            # Extract ratio type (e.g., "amount_ratio", "mass_ratio")
                            ratio_type_clean = (
                                mapped_param.lower()
                                .replace(" ", "_")
                                .replace(",", "")
                                .replace("(", "")
                                .replace(")", "")
                            )
                            parameter_obj.parameterID = (
                                f"parameter_{ratio_type_clean}_{clean_name}"
                            )
                        else:
                            ratio_type_clean = (
                                mapped_param.lower()
                                .replace(" ", "_")
                                .replace(",", "")
                                .replace("(", "")
                                .replace(")", "")
                            )
                            parameter_obj.parameterID = f"parameter_{ratio_type_clean}"
                    else:
                        # For other composition types, use generic ID
                        if associated_common_name:
                            clean_name = (
                                associated_common_name.lower()
                                .replace(" ", "")
                                .replace("-", "")
                                .replace("_", "")
                            )
                            param_type_clean = (
                                mapped_param.lower()
                                .replace(" ", "_")
                                .replace(",", "")
                                .replace("(", "")
                                .replace(")", "")
                            )
                            parameter_obj.parameterID = (
                                f"parameter_{param_type_clean}_{clean_name}"
                            )
                        else:
                            param_type_clean = (
                                mapped_param.lower()
                                .replace(" ", "_")
                                .replace(",", "")
                                .replace("(", "")
                                .replace(")", "")
                            )
                            parameter_obj.parameterID = f"parameter_{param_type_clean}"

            # Solvent composition (mole fraction, etc.) - same logic as component composition
            solvent_comp_elem = var_type_elem.find(
                ".//{http://www.iupac.org/namespaces/ThermoML}eSolventComposition"
            )
            if solvent_comp_elem is not None:
                solvent_type = extract_text_content(solvent_comp_elem)
                if solvent_type:
                    # Map "Solvent: Mole fraction" to "Mole fraction" via parameter mapper
                    mapped_param = self.parameter_mapper.map_parameter(solvent_type)
                    if mapped_param and mapped_param in Parameters.__members__:
                        parameter_obj.parameter = Parameters[mapped_param]
                # Semantic ID for visualization: parameter_mole_fraction_<name>
                if associated_common_name:
                    # Clean the common name to ensure consistency with compound IDs
                    clean_name = (
                        associated_common_name.lower()
                        .replace(" ", "")
                        .replace("-", "")
                        .replace("_", "")
                    )
                    parameter_obj.parameterID = f"parameter_mole_fraction_{clean_name}"
                else:
                    parameter_obj.parameterID = "parameter_mole_fraction"

        # Store variable map
        if var_num_val is not None and parameter_obj.parameterID:
            self.variable_id_map[var_num_val] = parameter_obj.parameterID

        return parameter_obj

    def _extract_measurements(
        self, data_elem: ET.Element, constraint_values: Dict[str, float]
    ) -> List[Measurement]:
        """Extract measurements from NumValues elements and inject constraint values."""
        measurements = []

        # Find all NumValues elements
        num_values_elems = data_elem.findall(
            ".//{http://www.iupac.org/namespaces/ThermoML}NumValues"
        )

        for num_values_elem in num_values_elems:
            measurement = Measurement()
            measurement.measurement_id = str(uuid.uuid4())
            # Assign global source DOI if available
            measurement.source_doi = self.source_doi

            # Extract property values
            prop_value_elems = num_values_elem.findall(
                ".//{http://www.iupac.org/namespaces/ThermoML}PropertyValue"
            )
            for prop_value_elem in prop_value_elems:
                prop_value = self._convert_property_value(prop_value_elem)
                if prop_value:
                    measurement.propertyValue.append(prop_value)

            # Extract parameter values (variables)
            var_value_elems = num_values_elem.findall(
                ".//{http://www.iupac.org/namespaces/ThermoML}VariableValue"
            )
            for var_value_elem in var_value_elems:
                param_value = self._convert_variable_value(var_value_elem)
                if param_value:
                    measurement.parameterValue.append(param_value)

            # Inject constraint values into every measurement
            for cid, cval in constraint_values.items():
                pv = ParameterValue()
                pv.parameterID = cid
                pv.paramValue = cval
                measurement.parameterValue.append(pv)

            # Extract method information
            method_info = self._extract_method_info(data_elem)
            if method_info:
                measurement.method = method_info.get("method")
                measurement.method_description = method_info.get("description")

            measurements.append(measurement)

        return measurements

    def _convert_property_value(
        self, prop_value_elem: ET.Element
    ) -> Optional[PropertyValue]:
        """Convert ThermoML PropertyValue element to FAIRFluids PropertyValue."""
        prop_value = PropertyValue()

        # Get property number
        prop_num_elem = prop_value_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}nPropNumber"
        )
        if prop_num_elem is not None:
            prop_num = extract_integer_value(prop_num_elem)
            if prop_num and prop_num in self.property_id_map:
                prop_value.propertyID = self.property_id_map[prop_num]

        # Get property value
        prop_val_elem = prop_value_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}nPropValue"
        )
        if prop_val_elem is not None:
            prop_value.propValue = extract_numeric_value(prop_val_elem)

        # Get uncertainty
        uncertainty_elem = prop_value_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}CombinedUncertainty"
        )
        if uncertainty_elem is not None:
            uncert_elem = uncertainty_elem.find(
                ".//{http://www.iupac.org/namespaces/ThermoML}nCombExpandUncertValue"
            )
            if uncert_elem is not None:
                prop_value.uncertainty = extract_numeric_value(uncert_elem)

        return prop_value

    def _convert_variable_value(
        self, var_value_elem: ET.Element
    ) -> Optional[ParameterValue]:
        """Convert ThermoML VariableValue element to FAIRFluids ParameterValue."""
        param_value = ParameterValue()

        # Get variable number and map via variable map to semantic ID
        var_num_elem = var_value_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}nVarNumber"
        )
        if var_num_elem is not None:
            var_num = extract_integer_value(var_num_elem)
            if var_num and var_num in self.variable_id_map:
                param_value.parameterID = self.variable_id_map[var_num]

        # Get variable value
        var_val_elem = var_value_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}nVarValue"
        )
        if var_val_elem is not None:
            param_value.paramValue = extract_numeric_value(var_val_elem)

        return param_value

    def _extract_method_info(self, data_elem: ET.Element) -> Optional[Dict[str, str]]:
        """Extract method information from the data element."""
        method_info = {}

        # Look for Prediction element
        prediction_elem = data_elem.find(
            ".//{http://www.iupac.org/namespaces/ThermoML}Prediction"
        )
        if prediction_elem is not None:
            pred_type_elem = prediction_elem.find(
                ".//{http://www.iupac.org/namespaces/ThermoML}ePredictionType"
            )
            if pred_type_elem is not None:
                pred_type = extract_text_content(pred_type_elem)
                if pred_type:
                    mapped_method = self.method_mapper.map_method(pred_type)
                    if mapped_method and mapped_method in Method.__members__:
                        method_info["method"] = Method[mapped_method]

            pred_desc_elem = prediction_elem.find(
                ".//{http://www.iupac.org/namespaces/ThermoML}sPredictionMethodDescription"
            )
            if pred_desc_elem is not None:
                method_info["description"] = extract_text_content(pred_desc_elem)

        return method_info if method_info else None

    def _add_implicit_mole_fractions(self, fluid: Fluid) -> None:
        """
        Add implicit mole fraction parameters and values for components that don't have
        explicit mole fraction parameters. This handles cases where:
        1. Some components have explicit mole fractions but others are implicit
        2. Composition is specified as ratios (e.g., "Amount ratio of solute to solvent")
        3. Pure compounds (single component) should have mole fraction = 1.0

        Args:
            fluid: The Fluid object to process
        """
        if not fluid.compounds or not fluid.measurement:
            return

        # Find which compounds have explicit mole fraction parameters or ratio-based composition
        compounds_with_explicit_mf = set()
        compounds_with_ratio_composition = {}  # comp_id -> (param_id, ratio_type)
        mole_fraction_param_ids = {}

        for param in fluid.parameter:
            if (
                hasattr(param, "parameter")
                and param.parameter is not None
                and hasattr(param, "associated_compounds")
                and param.associated_compounds
            ):
                param_name = str(param.parameter)
                if hasattr(param.parameter, "value"):
                    param_name = param.parameter.value

                # Check for mole fraction parameters
                if "mole fraction" in param_name.lower():
                    for comp_id in param.associated_compounds:
                        compounds_with_explicit_mf.add(comp_id)
                        mole_fraction_param_ids[comp_id] = param.parameterID

                # Check for ratio-based composition parameters
                elif any(
                    ratio_term in param_name.lower()
                    for ratio_term in [
                        "amount ratio of solute to solvent",
                        "mass ratio of solute to solvent",
                        "volume ratio of solute to solvent",
                    ]
                ):
                    for comp_id in param.associated_compounds:
                        compounds_with_ratio_composition[comp_id] = (
                            param.parameterID,
                            param_name,
                        )

        # Convert ratio-based composition to mole fractions
        if compounds_with_ratio_composition:
            self._convert_ratios_to_mole_fractions(
                fluid,
                compounds_with_ratio_composition,
                compounds_with_explicit_mf,
                mole_fraction_param_ids,
            )

        # Handle pure compounds (single component) - they should have mole fraction = 1.0
        if len(fluid.compounds) == 1:
            compound_id = fluid.compounds[0]
            if (
                compound_id not in compounds_with_explicit_mf
                and compound_id not in mole_fraction_param_ids
            ):
                # Create mole fraction parameter for pure compound
                compound = None
                for comp in self.document.compound:
                    if comp.compoundID == compound_id:
                        compound = comp
                        break

                if compound and compound.commonName:
                    clean_name = (
                        compound.commonName.lower()
                        .replace(" ", "")
                        .replace("-", "")
                        .replace("_", "")
                    )
                    param_id = f"parameter_mole_fraction_{clean_name}"

                    pure_param = Parameter()
                    pure_param.parameterID = param_id
                    pure_param.parameter = Parameters.MOLE_FRACTION
                    pure_param.associated_compounds = [compound_id]
                    pure_param.unit = UnitDefinition(
                        unitID="unit_1",
                        unitName="1",
                        baseUnit=BaseUnit(kind="dimensionless", exponent=1),
                    )

                    fluid.parameter.append(pure_param)
                    mole_fraction_param_ids[compound_id] = param_id
                    compounds_with_explicit_mf.add(compound_id)

                    # Add mole fraction = 1.0 to all measurements
                    for measurement in fluid.measurement:
                        pure_pv = ParameterValue()
                        pure_pv.parameterID = param_id
                        pure_pv.paramValue = 1.0
                        measurement.parameterValue.append(pure_pv)

            return  # Pure compound handled, no need for implicit calculation

        # Find compounds that are components but don't have explicit mole fraction parameters
        compounds_without_explicit_mf = [
            comp_id
            for comp_id in fluid.compounds
            if comp_id not in compounds_with_explicit_mf
        ]

        if not compounds_without_explicit_mf:
            return

        # Only create implicit parameters if we have at least one explicit mole fraction
        # and multiple components (indicating a mixture where implicit calculation makes sense)
        if len(compounds_with_explicit_mf) == 0 or len(fluid.compounds) < 2:
            return

        # Create implicit mole fraction parameters for compounds without explicit ones
        for compound_id in compounds_without_explicit_mf:
            # Find the compound to get its common name
            compound = None
            for comp in self.document.compound:
                if comp.compoundID == compound_id:
                    compound = comp
                    break

            if compound and compound.commonName:
                # Clean the common name to ensure consistency with compound IDs
                clean_name = (
                    compound.commonName.lower()
                    .replace(" ", "")
                    .replace("-", "")
                    .replace("_", "")
                )
                param_id = f"parameter_mole_fraction_{clean_name}"

                # Create the parameter
                implicit_param = Parameter()
                implicit_param.parameterID = param_id
                implicit_param.parameter = Parameters.MOLE_FRACTION
                implicit_param.associated_compounds = [compound_id]
                # Create a simple unit definition for mole fraction
                implicit_param.unit = UnitDefinition(
                    unitID="unit_1",
                    unitName="1",
                    baseUnit=BaseUnit(kind="dimensionless", exponent=1),
                )

                fluid.parameter.append(implicit_param)
                mole_fraction_param_ids[compound_id] = param_id

        # Calculate implicit mole fraction values for each measurement
        for measurement in fluid.measurement:
            # Sum all explicit mole fractions in this measurement
            sum_explicit_mf = 0.0
            for param_value in measurement.parameterValue:
                if param_value.parameterID in mole_fraction_param_ids.values():
                    if param_value.paramValue is not None:
                        sum_explicit_mf += param_value.paramValue

            # Calculate implicit mole fractions (1 - sum of explicit)
            # Distribute among compounds without explicit mole fractions
            # In most cases, there's only one implicit compound, so it's 1 - sum
            implicit_mf_value = 1.0 - sum_explicit_mf

            # Add implicit mole fraction values for compounds without explicit ones
            for compound_id in compounds_without_explicit_mf:
                if compound_id in mole_fraction_param_ids:
                    param_id = mole_fraction_param_ids[compound_id]

                    # Check if this parameter value already exists (shouldn't, but be safe)
                    exists = any(
                        pv.parameterID == param_id for pv in measurement.parameterValue
                    )

                    if not exists and implicit_mf_value >= 0:
                        implicit_pv = ParameterValue()
                        implicit_pv.parameterID = param_id
                        implicit_pv.paramValue = implicit_mf_value
                        measurement.parameterValue.append(implicit_pv)

    def _convert_ratios_to_mole_fractions(
        self,
        fluid: Fluid,
        compounds_with_ratio_composition: Dict[str, tuple],
        compounds_with_explicit_mf: set,
        mole_fraction_param_ids: Dict[str, str],
    ) -> None:
        """
        Convert ratio-based composition parameters (e.g., "Amount ratio of solute to solvent")
        to mole fraction parameters and values.

        For "Amount ratio of solute to solvent" with ratio r = n_solute/n_solvent:
        - x_solute = r / (r + 1)
        - x_solvent = 1 / (r + 1)

        Args:
            fluid: The Fluid object to process
            compounds_with_ratio_composition: Dict mapping compound_id to (param_id, ratio_type)
            compounds_with_explicit_mf: Set of compounds that already have explicit mole fractions
            mole_fraction_param_ids: Dict mapping compound_id to mole fraction param_id
        """
        # Identify solute and solvent compounds
        # The ratio parameter is associated with the solute
        # We need to find the solvent (other component in the fluid)
        # First, try to get solvent from fluid metadata (if available)
        solvent_compounds = getattr(fluid, "_solvent_compounds", set())

        for solute_id, (
            ratio_param_id,
            ratio_type,
        ) in compounds_with_ratio_composition.items():
            # Find the solvent (other component in the fluid)
            solvent_candidates = [c for c in fluid.compounds if c != solute_id]
            if not solvent_candidates:
                continue

            # Prefer explicitly identified solvents, otherwise use first candidate
            if solvent_compounds:
                # Find intersection of solvent_compounds and solvent_candidates
                explicit_solvents = [
                    c for c in solvent_candidates if c in solvent_compounds
                ]
                if explicit_solvents:
                    solvent_id = explicit_solvents[0]
                else:
                    # If no explicit solvent matches, use first candidate
                    solvent_id = solvent_candidates[0]
            else:
                # For binary mixtures, the solvent is the other component
                # For multi-component, use the first other component as solvent
                solvent_id = solvent_candidates[0]

            if not solvent_id:
                continue

            # Create mole fraction parameters for both solute and solvent if they don't exist
            for comp_id in [solute_id, solvent_id]:
                if comp_id not in mole_fraction_param_ids:
                    compound = None
                    for comp in self.document.compound:
                        if comp.compoundID == comp_id:
                            compound = comp
                            break

                    if compound and compound.commonName:
                        clean_name = (
                            compound.commonName.lower()
                            .replace(" ", "")
                            .replace("-", "")
                            .replace("_", "")
                        )
                        param_id = f"parameter_mole_fraction_{clean_name}"

                        mf_param = Parameter()
                        mf_param.parameterID = param_id
                        mf_param.parameter = Parameters.MOLE_FRACTION
                        mf_param.associated_compounds = [comp_id]
                        mf_param.unit = UnitDefinition(
                            unitID="unit_1",
                            unitName="1",
                            baseUnit=BaseUnit(kind="dimensionless", exponent=1),
                        )

                        fluid.parameter.append(mf_param)
                        mole_fraction_param_ids[comp_id] = param_id
                        compounds_with_explicit_mf.add(comp_id)

            # Convert ratio values to mole fractions for each measurement
            solute_param_id = mole_fraction_param_ids[solute_id]
            solvent_param_id = mole_fraction_param_ids[solvent_id]

            for measurement in fluid.measurement:
                # Find the ratio value for this measurement
                ratio_value = None
                for pv in measurement.parameterValue:
                    if pv.parameterID == ratio_param_id:
                        ratio_value = pv.paramValue
                        break

                if ratio_value is not None and ratio_value >= 0:
                    # Convert ratio to mole fractions
                    # For "Amount ratio of solute to solvent": r = n_solute/n_solvent
                    # x_solute = r / (r + 1), x_solvent = 1 / (r + 1)
                    if "amount ratio" in ratio_type.lower():
                        x_solute = ratio_value / (ratio_value + 1.0)
                        x_solvent = 1.0 / (ratio_value + 1.0)

                        # Add mole fraction values if they don't already exist
                        solute_exists = any(
                            pv.parameterID == solute_param_id
                            for pv in measurement.parameterValue
                        )
                        solvent_exists = any(
                            pv.parameterID == solvent_param_id
                            for pv in measurement.parameterValue
                        )

                        if not solute_exists:
                            solute_pv = ParameterValue()
                            solute_pv.parameterID = solute_param_id
                            solute_pv.paramValue = x_solute
                            measurement.parameterValue.append(solute_pv)

                        if not solvent_exists:
                            solvent_pv = ParameterValue()
                            solvent_pv.parameterID = solvent_param_id
                            solvent_pv.paramValue = x_solvent
                            measurement.parameterValue.append(solvent_pv)
                    else:
                        # For mass/volume ratios, we can't convert without molecular weights/densities
                        # However, we've already created the mole fraction parameters above
                        # The implicit mole fraction calculation will handle creating values
                        # by calculating 1 - sum of explicit mole fractions
                        # Since we don't have explicit mole fractions here, we'll need to
                        # approximate or let the implicit logic handle it
                        # For now, we'll approximate mass ratio as amount ratio (not perfect, but better than nothing)
                        # This is a rough approximation assuming similar molecular weights
                        if "mass ratio" in ratio_type.lower():
                            # Approximate: assume similar molecular weights, so mass ratio ≈ amount ratio
                            x_solute_approx = ratio_value / (ratio_value + 1.0)
                            x_solvent_approx = 1.0 / (ratio_value + 1.0)

                            solute_exists = any(
                                pv.parameterID == solute_param_id
                                for pv in measurement.parameterValue
                            )
                            solvent_exists = any(
                                pv.parameterID == solvent_param_id
                                for pv in measurement.parameterValue
                            )

                            if not solute_exists:
                                solute_pv = ParameterValue()
                                solute_pv.parameterID = solute_param_id
                                solute_pv.paramValue = x_solute_approx
                                measurement.parameterValue.append(solute_pv)

                            if not solvent_exists:
                                solvent_pv = ParameterValue()
                                solvent_pv.parameterID = solvent_param_id
                                solvent_pv.paramValue = x_solvent_approx
                                measurement.parameterValue.append(solvent_pv)
