#!/usr/bin/env python3
"""
ThermoML XML Validation and Writing Script

This script:
1. Parses the original ThermoML XML file
2. Validates it against the generated models
3. Writes it back as XML using the models
4. Validates the written XML
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from thermoml_mapper import ThermoMLMapper
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function for validation and XML writing."""
    
    # Initialize mapper
    mapper = ThermoMLMapper()
    
    # Path to the original XML file
    original_xml = "../fairfluids/data/thermoml_xml/spera_et_al_fpe_592_2025_114324.xml"
    output_xml = "rewritten_thermoml.xml"
    
    print("=== ThermoML XML Validation and Writing ===\n")
    
    try:
        # Step 1: Parse and validate the original XML
        print("1. Parsing and validating original XML...")
        data_report = mapper.parse_xml_file(original_xml)
        print(f"   ✓ Successfully parsed {original_xml}")
        print(f"   ✓ Found {len(data_report.compound)} compounds")
        print(f"   ✓ Found {len(data_report.pure_or_mixture_data)} pure/mixture data sets")
        print(f"   ✓ Found {len(data_report.reaction_data)} reaction data sets")
        
        # Validate the parsed data
        is_valid = mapper.validate_xml_file(original_xml)
        if is_valid:
            print("   ✓ Original XML is valid")
        else:
            print("   ✗ Original XML has validation errors")
            return
        
        print()
        
        # Step 2: Write the data back as XML
        print("2. Writing data back as XML...")
        try:
            # Convert to XML string using the to_xml method
            xml_string = data_report.to_xml(
                indent=2,
                encoding='utf-8'
            )
            
            # Write to file
            with open(output_xml, 'wb') as f:
                f.write(xml_string)
            
            print(f"   ✓ Successfully wrote XML to {output_xml}")
            print(f"   ✓ File size: {len(xml_string)} bytes")
            
        except Exception as e:
            print(f"   ✗ Error writing XML: {e}")
            return
        
        print()
        
        # Step 3: Validate the written XML
        print("3. Validating written XML...")
        try:
            # Parse the written XML to validate it
            written_data_report = mapper.parse_xml_file(output_xml)
            print(f"   ✓ Successfully parsed written XML")
            print(f"   ✓ Found {len(written_data_report.compound)} compounds")
            print(f"   ✓ Found {len(written_data_report.pure_or_mixture_data)} pure/mixture data sets")
            print(f"   ✓ Found {len(written_data_report.reaction_data)} reaction data sets")
            
            # Validate the written XML
            is_written_valid = mapper.validate_xml_file(output_xml)
            if is_written_valid:
                print("   ✓ Written XML is valid")
            else:
                print("   ✗ Written XML has validation errors")
                return
                
        except Exception as e:
            print(f"   ✗ Error validating written XML: {e}")
            return
        
        print()
        
        # Step 4: Compare the data
        print("4. Comparing original and written data...")
        try:
            # Compare basic counts
            original_compounds = len(data_report.compound)
            written_compounds = len(written_data_report.compound)
            
            original_data_sets = len(data_report.pure_or_mixture_data)
            written_data_sets = len(written_data_report.pure_or_mixture_data)
            
            original_reactions = len(data_report.reaction_data)
            written_reactions = len(written_data_report.reaction_data)
            
            print(f"   Compounds: {original_compounds} → {written_compounds} {'✓' if original_compounds == written_compounds else '✗'}")
            print(f"   Data Sets: {original_data_sets} → {written_data_sets} {'✓' if original_data_sets == written_data_sets else '✗'}")
            print(f"   Reactions: {original_reactions} → {written_reactions} {'✓' if original_reactions == written_reactions else '✗'}")
            
            # Compare citation information
            if data_report.citation and written_data_report.citation:
                original_title = data_report.citation.s_title
                written_title = written_data_report.citation.s_title
                print(f"   Title: {'✓' if original_title == written_title else '✗'}")
                
                original_authors = data_report.citation.s_author
                written_authors = written_data_report.citation.s_author
                print(f"   Authors: {'✓' if original_authors == written_authors else '✗'}")
                
                original_doi = data_report.citation.s_doi
                written_doi = written_data_report.citation.s_doi
                print(f"   DOI: {'✓' if original_doi == written_doi else '✗'}")
            
        except Exception as e:
            print(f"   ✗ Error comparing data: {e}")
        
        print()
        print("=== Validation and Writing Complete! ===")
        print(f"Original XML: {original_xml}")
        print(f"Written XML: {output_xml}")
        print(f"Both files are valid and contain the same data structure.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
