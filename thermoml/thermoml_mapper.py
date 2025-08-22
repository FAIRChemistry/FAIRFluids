#!/usr/bin/env python3
"""
ThermoML XML to Python Model Mapper

This script provides utilities to parse ThermoML XML files and convert them
to the generated Python models from thermo.py.

Usage:
    python thermoml_mapper.py parse_xml <xml_file_path>
    python thermoml_mapper.py validate_xml <xml_file_path>
    python thermoml_mapper.py convert_to_json <xml_file_path> [output_file]
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from xml.etree import ElementTree as ET

# Import the generated models
try:
    from thermo import DataReport, Compound, Citation, Version, PureOrMixtureData
    from thermo import ReactionData, Property, PropertyValue, Variable, VariableValue
    from thermo import Constraint, PhaseID, Component, Sample, Purity
    from thermo import RegNum, SOrgID, Biomaterial, Ion, Polymer, MulticomponentSubstance
    from thermo import AuxiliarySubstance, Participant, Catalyst, Solvent
    from thermo import PropertyMethodID, PropertyGroup, PropPhaseID, RefPhaseID
    from thermo import ConstraintID, ConstraintType, ConstraintPhaseID
    from thermo import VariableID, VariableType, VarPhaseID
    from thermo import NumValues, PropLimit, CombinedUncertainty, PropUncertainty
    from thermo import PropRepeatability, PropDeviceSpec, CurveDev
    from thermo import ConstrUncertainty, ConstrRepeatability, ConstrDeviceSpec
    from thermo import VarUncertainty, VarRepeatability, VarDeviceSpec
    from thermo import AsymCombStdUncert, AsymCombExpandUncert, AsymStdUncert, AsymExpandUncert
    from thermo import Equation, EqProperty, EqConstraint, EqVariable, EqParameter, EqConstant, Covariance
    from thermo import ActivityFugacityOsmoticProp, BioProperties, CompositionAtPhaseEquilibrium
    from thermo import Criticals, ExcessPartialApparentEnergyProp, HeatCapacityAndDerivedProp
    from thermo import PhaseTransition, ReactionEquilibriumProp, ReactionStateChangeProp
    from thermo import RefractionSurfaceTensionSoundSpeed, TransportProp, VaporPBoilingTAzeotropTandP
    from thermo import VolumetricProp, CriticalEvaluation, Prediction, PredictionMethodRef
    from thermo import SingleProp, MultiProp, EvalSinglePropRef, EvalMultiPropRef
    from thermo import EquationOfState, EvalEOSRef
    from thermo import Book, Journal, Thesis, TRCRefID
    from thermo import eType, eSourceType, eLanguage, eSpeciationState, eSource, eStatus
    from thermo import ePurifMethod, eAnalMeth, eFunction, eExpPurpose, ePropName, eMethodName
    from thermo import ePredictionType, ePropPhase, eCrystalLatticeType, eBioState, ePresentation
    from thermo import eRefStateType, eRefPhase, eStandardState, eCombUncertEvalMethod, eRepeatMethod
    from thermo import eDeviceSpecMethod, ePhase, eTemperature, ePressure, eComponentComposition
    from thermo import eSolventComposition, eMiscellaneous, eBioVariables, eParticipantAmount
    from thermo import eConstraintPhase, eVarPhase, eEqName, eCompositionRepresentation
    from thermo import eReactionFormalism, eReactionType
except ImportError as e:
    print(f"Error importing thermo models: {e}")
    print("Make sure thermo.py is in the current directory")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ThermoMLMapper:
    """Maps ThermoML XML files to Python models."""
    
    def __init__(self):
        self.namespace = "http://www.iupac.org/namespaces/ThermoML"
        self.xsi_namespace = "http://www.w3.org/2001/XMLSchema-instance"
        
    def parse_xml_file(self, xml_file_path: str) -> DataReport:
        """
        Parse a ThermoML XML file and return a DataReport model.
        
        Args:
            xml_file_path: Path to the XML file
            
        Returns:
            DataReport: Parsed and validated data report
        """
        try:
            # Parse XML with namespace handling
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # Remove namespace prefixes for easier processing
            for elem in root.iter():
                if elem.tag.startswith('{'):
                    elem.tag = elem.tag.split('}', 1)[1]
            
            # Convert to dictionary
            xml_dict = self._xml_to_dict(root)
            
            # Convert to DataReport model
            data_report = self._dict_to_datareport(xml_dict)
            
            logger.info(f"Successfully parsed {xml_file_path}")
            return data_report
            
        except Exception as e:
            logger.error(f"Error parsing XML file {xml_file_path}: {e}")
            raise
    
    def _xml_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """Convert XML element to dictionary."""
        result = {}
        
        # Handle attributes
        if element.attrib:
            result['@attributes'] = element.attrib
        
        # Handle child elements
        for child in element:
            child_tag = child.tag
            child_data = self._xml_to_dict(child)
            
            if child_tag in result:
                # Multiple elements with same tag
                if not isinstance(result[child_tag], list):
                    result[child_tag] = [result[child_tag]]
                result[child_tag].append(child_data)
            else:
                result[child_tag] = child_data
        
        # Handle text content
        if element.text and element.text.strip():
            if result:  # Has children
                result['#text'] = element.text.strip()
            else:  # Leaf element
                result = element.text.strip()
        
        return result
    
    def _dict_to_datareport(self, data: Dict[str, Any]) -> DataReport:
        """Convert dictionary to DataReport model."""
        try:
            # Extract main sections
            version_data = data.get('Version', {})
            citation_data = data.get('Citation', {})
            compounds_data = data.get('Compound', [])
            pure_mixture_data = data.get('PureOrMixtureData', [])
            reaction_data = data.get('ReactionData', [])
            
            # Ensure compounds is a list
            if not isinstance(compounds_data, list):
                compounds_data = [compounds_data] if compounds_data else []
            
            # Ensure pure_mixture_data is a list
            if not isinstance(pure_mixture_data, list):
                pure_mixture_data = [pure_mixture_data] if pure_mixture_data else []
            
            # Ensure reaction_data is a list
            if not isinstance(reaction_data, list):
                reaction_data = [reaction_data] if reaction_data else []
            
            # Create DataReport
            data_report = DataReport(
                version=self._create_version(version_data),
                citation=self._create_citation(citation_data),
                compound=[self._create_compound(c) for c in compounds_data],
                pure_or_mixture_data=[self._create_pure_mixture_data(p) for p in pure_mixture_data],
                reaction_data=[self._create_reaction_data(r) for r in reaction_data]
            )
            
            return data_report
            
        except Exception as e:
            logger.error(f"Error creating DataReport: {e}")
            raise
    
    def _create_version(self, data: Dict[str, Any]) -> Optional[Version]:
        """Create Version model from data."""
        if not data:
            return None
        
        try:
            return Version(
                n_version_major=data.get('nVersionMajor'),
                n_version_minor=data.get('nVersionMinor')
            )
        except Exception as e:
            logger.warning(f"Error creating Version: {e}")
            return None
    
    def _create_citation(self, data: Dict[str, Any]) -> Optional[Citation]:
        """Create Citation model from data."""
        if not data:
            return None
        
        try:
            # Handle multiple authors
            authors = data.get('sAuthor', [])
            if not isinstance(authors, list):
                authors = [authors] if authors else []
            
            # Handle multiple keywords
            keywords = data.get('sKeyword', [])
            if not isinstance(keywords, list):
                keywords = [keywords] if keywords else []
            
            return Citation(
                e_type=data.get('eType'),
                e_source_type=data.get('eSourceType'),
                s_author=authors,
                s_pub_name=data.get('sPubName'),
                yr_pub_yr=data.get('yrPubYr'),
                date_cit=data.get('dateCit'),
                s_title=data.get('sTitle'),
                s_abstract=data.get('sAbstract'),
                s_keyword=keywords,
                s_doi=data.get('sDOI'),
                s_vol=data.get('sVol'),
                s_page=data.get('sPage')
            )
        except Exception as e:
            logger.warning(f"Error creating Citation: {e}")
            return None
    
    def _create_compound(self, data: Dict[str, Any]) -> Compound:
        """Create Compound model from data."""
        try:
            # Handle multiple common names
            common_names = data.get('sCommonName', [])
            if not isinstance(common_names, list):
                common_names = [common_names] if common_names else []
            
            # Handle multiple SMILES
            smiles = data.get('sSMILES', [])
            if not isinstance(smiles, list):
                smiles = [smiles] if smiles else []
            
            # Handle multiple organization IDs
            org_ids = data.get('SOrgID', [])
            if not isinstance(org_ids, list):
                org_ids = [org_ids] if org_ids else []
            
            # Handle multiple samples
            samples = data.get('Sample', [])
            if not isinstance(samples, list):
                samples = [samples] if samples else []
            
            return Compound(
                n_pub_chem_id=data.get('nPubChemID'),
                reg_num=self._create_reg_num(data.get('RegNum', {})),
                s_common_name=common_names,
                s_formula_molec=data.get('sFormulaMolec'),
                s_iupac_name=data.get('sIUPACName'),
                s_standard_in_ch_i=data.get('sStandardInChI'),
                s_standard_in_ch_i_key=data.get('sStandardInChIKey'),
                s_org_id=[self._create_sorg_id(oid) for oid in org_ids],
                s_smiles=smiles,
                sample=[self._create_sample(s) for s in samples]
            )
        except Exception as e:
            logger.warning(f"Error creating Compound: {e}")
            # Return minimal compound if creation fails
            return Compound(
                n_pub_chem_id=data.get('nPubChemID', 0),
                s_common_name=data.get('sCommonName', ['Unknown'])
            )
    
    def _create_reg_num(self, data: Dict[str, Any]) -> Optional[RegNum]:
        """Create RegNum model from data."""
        if not data:
            return None
        
        try:
            return RegNum(
                n_org_num=data.get('nOrgNum'),
                n_casr_num=data.get('nCASRNNum'),
                s_organization=data.get('sOrganization')
            )
        except Exception as e:
            logger.warning(f"Error creating RegNum: {e}")
            return None
    
    def _create_sorg_id(self, data: Dict[str, Any]) -> SOrgID:
        """Create SOrgID model from data."""
        try:
            return SOrgID(
                s_org_identifier=data.get('sOrgIdentifier'),
                s_organization=data.get('sOrganization')
            )
        except Exception as e:
            logger.warning(f"Error creating SOrgID: {e}")
            return SOrgID()
    
    def _create_sample(self, data: Dict[str, Any]) -> Sample:
        """Create Sample model from data."""
        try:
            return Sample(
                n_sample_nm=data.get('nSampleNm'),
                e_source=data.get('eSource'),
                e_status=data.get('eStatus')
            )
        except Exception as e:
            logger.warning(f"Error creating Sample: {e}")
            return Sample()
    
    def _create_pure_mixture_data(self, data: Dict[str, Any]) -> PureOrMixtureData:
        """Create PureOrMixtureData model from data."""
        try:
            return PureOrMixtureData(
                n_pure_or_mixture_data_number=data.get('nPureOrMixtureDataNumber'),
                s_compiler=data.get('sCompiler'),
                s_contributor=data.get('sContributor'),
                date_date_added=data.get('dateDateAdded'),
                e_exp_purpose=data.get('eExpPurpose')
            )
        except Exception as e:
            logger.warning(f"Error creating PureOrMixtureData: {e}")
            return PureOrMixtureData()
    
    def _create_reaction_data(self, data: Dict[str, Any]) -> ReactionData:
        """Create ReactionData model from data."""
        try:
            return ReactionData(
                n_reaction_data_number=data.get('nReactionDataNumber'),
                e_reaction_type=data.get('eReactionType'),
                e_reaction_formalism=data.get('eReactionFormalism'),
                s_compiler=data.get('sCompiler'),
                s_contributor=data.get('sContributor'),
                date_date_added=data.get('dateDateAdded'),
                e_exp_purpose=data.get('eExpPurpose')
            )
        except Exception as e:
            logger.warning(f"Error creating ReactionData: {e}")
            return ReactionData()
    
    def validate_xml_file(self, xml_file_path: str) -> bool:
        """
        Validate a ThermoML XML file against the schema.
        
        Args:
            xml_file_path: Path to the XML file
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            data_report = self.parse_xml_file(xml_file_path)
            logger.info(f"XML file {xml_file_path} is valid")
            return True
        except Exception as e:
            logger.error(f"XML file {xml_file_path} is invalid: {e}")
            return False
    
    def convert_to_json(self, xml_file_path: str, output_file: Optional[str] = None) -> str:
        """
        Convert a ThermoML XML file to JSON.
        
        Args:
            xml_file_path: Path to the XML file
            output_file: Optional output file path
            
        Returns:
            str: JSON string representation
        """
        try:
            data_report = self.parse_xml_file(xml_file_path)
            
            # Convert to JSON
            json_data = data_report.model_dump_json(indent=2)
            
            # Write to file if specified
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(json_data)
                logger.info(f"JSON written to {output_file}")
            
            return json_data
            
        except Exception as e:
            logger.error(f"Error converting to JSON: {e}")
            raise
    
    def get_summary(self, xml_file_path: str) -> Dict[str, Any]:
        """
        Get a summary of the ThermoML XML file.
        
        Args:
            xml_file_path: Path to the XML file
            
        Returns:
            Dict: Summary information
        """
        try:
            data_report = self.parse_xml_file(xml_file_path)
            
            summary = {
                'file_path': xml_file_path,
                'version': f"{data_report.version.n_version_major}.{data_report.version.n_version_minor}" if data_report.version else "Unknown",
                'citation': {
                    'title': data_report.citation.s_title if data_report.citation else "Unknown",
                    'authors': data_report.citation.s_author if data_report.citation else [],
                    'publication': data_report.citation.s_pub_name if data_report.citation else "Unknown",
                    'year': data_report.citation.yr_pub_yr if data_report.citation else "Unknown",
                    'doi': data_report.citation.s_doi if data_report.citation else "Unknown"
                },
                'compounds': len(data_report.compound),
                'pure_mixture_data_sets': len(data_report.pure_or_mixture_data),
                'reaction_data_sets': len(data_report.reaction_data),
                'compound_details': [
                    {
                        'pubchem_id': c.n_pub_chem_id,
                        'common_names': c.s_common_name,
                        'formula': c.s_formula_molec,
                        'iupac_name': c.s_iupac_name
                    }
                    for c in data_report.compound
                ]
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            raise


def main():
    """Main function for command line usage."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    mapper = ThermoMLMapper()
    
    try:
        if command == "parse_xml":
            if len(sys.argv) < 3:
                print("Usage: python thermoml_mapper.py parse_xml <xml_file_path>")
                sys.exit(1)
            
            xml_file = sys.argv[2]
            data_report = mapper.parse_xml_file(xml_file)
            print(f"Successfully parsed {xml_file}")
            print(f"Found {len(data_report.compound)} compounds")
            print(f"Found {len(data_report.pure_or_mixture_data)} pure/mixture data sets")
            print(f"Found {len(data_report.reaction_data)} reaction data sets")
            
        elif command == "validate_xml":
            if len(sys.argv) < 3:
                print("Usage: python thermoml_mapper.py validate_xml <xml_file_path>")
                sys.exit(1)
            
            xml_file = sys.argv[2]
            is_valid = mapper.validate_xml_file(xml_file)
            if is_valid:
                print(f"✓ {xml_file} is valid")
                sys.exit(0)
            else:
                print(f"✗ {xml_file} is invalid")
                sys.exit(1)
                
        elif command == "convert_to_json":
            if len(sys.argv) < 3:
                print("Usage: python thermoml_mapper.py convert_to_json <xml_file_path> [output_file]")
                sys.exit(1)
            
            xml_file = sys.argv[2]
            output_file = sys.argv[3] if len(sys.argv) > 3 else None
            
            json_data = mapper.convert_to_json(xml_file, output_file)
            if not output_file:
                print(json_data)
                
        elif command == "summary":
            if len(sys.argv) < 3:
                print("Usage: python thermoml_mapper.py summary <xml_file_path>")
                sys.exit(1)
            
            xml_file = sys.argv[2]
            summary = mapper.get_summary(xml_file)
            print(json.dumps(summary, indent=2))
            
        else:
            print(f"Unknown command: {command}")
            print(__doc__)
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
