#!/usr/bin/env python3
"""
Simple ThermoML XML Validation and Writing Script

This script provides a simpler approach to validate and write ThermoML XML files.
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
    """Main function for simple validation and XML writing."""
    
    # Initialize mapper
    mapper = ThermoMLMapper()
    
    # Path to the original XML file
    original_xml = "../fairfluids/data/thermoml_xml/spera_et_al_fpe_592_2025_114324.xml"
    output_xml = "rewritten_thermoml.xml"
    
    print("=== Simple ThermoML XML Validation and Writing ===\n")
    
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
        
        # Step 2: Get a summary of the data
        print("2. Getting data summary...")
        summary = mapper.get_summary(original_xml)
        print(f"   ✓ Version: {summary['version']}")
        print(f"   ✓ Title: {summary['citation']['title']}")
        print(f"   ✓ Authors: {', '.join(summary['citation']['authors'])}")
        print(f"   ✓ DOI: {summary['citation']['doi']}")
        print(f"   ✓ Compounds: {summary['compounds']}")
        print(f"   ✓ Data Sets: {summary['pure_mixture_data_sets']}")
        
        print()
        
        # Step 3: Convert to JSON first (this works reliably)
        print("3. Converting to JSON...")
        try:
            json_data = mapper.convert_to_json(original_xml, "thermoml_data.json")
            print(f"   ✓ Successfully converted to JSON")
            print(f"   ✓ JSON file size: {len(json_data)} characters")
        except Exception as e:
            print(f"   ✗ Error converting to JSON: {e}")
            return
        
        print()
        
        # Step 4: Try to write XML with error handling
        print("4. Attempting to write XML...")
        try:
            # Try to write XML using the to_xml method
            xml_string = data_report.to_xml(
                indent=2,
                encoding='utf-8'
            )
            
            # Write to file
            with open(output_xml, 'wb') as f:
                f.write(xml_string)
            
            print(f"   ✓ Successfully wrote XML to {output_xml}")
            print(f"   ✓ XML file size: {len(xml_string)} bytes")
            
            # Step 5: Validate the written XML
            print("\n5. Validating written XML...")
            try:
                # Parse the written XML to validate it
                written_data_report = mapper.parse_xml_file(output_xml)
                print(f"   ✓ Successfully parsed written XML")
                print(f"   ✓ Found {len(written_data_report.compound)} compounds")
                print(f"   ✓ Found {len(written_data_report.pure_or_mixture_data)} pure/mixture data sets")
                
                # Validate the written XML
                is_written_valid = mapper.validate_xml_file(output_xml)
                if is_written_valid:
                    print("   ✓ Written XML is valid")
                else:
                    print("   ✗ Written XML has validation errors")
                    
            except Exception as e:
                print(f"   ✗ Error validating written XML: {e}")
                
        except Exception as e:
            print(f"   ✗ Error writing XML: {e}")
            print("   Note: This is likely due to some nested models not being fully initialized.")
            print("   The JSON conversion worked successfully, indicating the data is valid.")
            print("   You can use the JSON file for further processing.")
        
        print()
        print("=== Validation Complete! ===")
        print(f"Original XML: {original_xml}")
        print(f"JSON Output: thermoml_data.json")
        if os.path.exists(output_xml):
            print(f"XML Output: {output_xml}")
        print(f"Original XML is valid and contains {summary['compounds']} compounds.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

