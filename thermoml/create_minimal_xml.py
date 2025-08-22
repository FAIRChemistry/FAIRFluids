#!/usr/bin/env python3
"""
Create Minimal ThermoML XML

This script creates a minimal but valid DataReport structure that can be written as XML.
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from thermo import DataReport, Version, Citation, Compound, RegNum
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Create a minimal valid DataReport and write it as XML."""
    
    print("=== Creating Minimal ThermoML XML ===\n")
    
    try:
        # Step 1: Create a minimal but valid DataReport
        print("1. Creating minimal DataReport structure...")
        
        # Create minimal version
        version = Version(
            n_version_major=2,
            n_version_minor=0
        )
        
        # Create minimal citation
        citation = Citation(
            e_type="journal",
            e_source_type="Original",
            s_author=["Test Author"],
            s_pub_name="Test Journal",
            yr_pub_yr="2025",
            s_title="Test Title",
            s_doi="10.1234/test.123"
        )
        
        # Create minimal compound
        reg_num = RegNum(
            n_org_num=1
        )
        
        compound = Compound(
            n_pub_chem_id=123,
            reg_num=reg_num,
            s_common_name=["Test Compound"],
            s_formula_molec="H2O",
            s_iupac_name="water"
        )
        
        # Create minimal DataReport
        data_report = DataReport(
            version=version,
            citation=citation,
            compound=[compound],
            pure_or_mixture_data=[],
            reaction_data=[]
        )
        
        print("   ✓ Created minimal DataReport structure")
        print(f"   ✓ Version: {data_report.version.n_version_major}.{data_report.version.n_version_minor}")
        print(f"   ✓ Citation: {data_report.citation.s_title}")
        print(f"   ✓ Compounds: {len(data_report.compound)}")
        
        print()
        
        # Step 2: Write the minimal structure as XML
        print("2. Writing minimal structure as XML...")
        try:
            xml_string = data_report.to_xml(
                indent=2,
                encoding='utf-8'
            )
            
            output_xml = "minimal_thermoml.xml"
            with open(output_xml, 'wb') as f:
                f.write(xml_string)
            
            print(f"   ✓ Successfully wrote minimal XML to {output_xml}")
            print(f"   ✓ XML file size: {len(xml_string)} bytes")
            
            # Step 3: Validate the written XML
            print("\n3. Validating written XML...")
            try:
                from thermoml_mapper import ThermoMLMapper
                mapper = ThermoMLMapper()
                
                # Parse the written XML to validate it
                written_data_report = mapper.parse_xml_file(output_xml)
                print(f"   ✓ Successfully parsed written XML")
                print(f"   ✓ Found {len(written_data_report.compound)} compounds")
                print(f"   ✓ Version: {written_data_report.version.n_version_major}.{written_data_report.version.n_version_minor}")
                
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
            return
        
        print()
        print("=== Minimal XML Creation Complete! ===")
        print(f"Output: {output_xml}")
        print(f"Structure: Version, Citation, and 1 Compound")
        
        # Step 4: Show the XML content
        print("\n4. XML Content Preview:")
        print("-" * 50)
        try:
            with open(output_xml, 'r') as f:
                content = f.read()
                print(content[:500] + "..." if len(content) > 500 else content)
        except Exception as e:
            print(f"Error reading XML file: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

