#!/usr/bin/env python3
"""
Test script for the BAML parser functionality.
This script demonstrates how to use the ModelMarkdownParser to convert
FAIRFluids model.md to BAML format.
"""

import sys
import os

# Add the parent directory to the path so we can import the parser
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'jinja'))

from parser import ModelMarkdownParser, generate_baml_from_markdown
from FAIRFluids.core.functionalities import FAIRFluidsCMLParser

# Define the compounds for ChCl/Urea/Water system
compounds = [
    {"commonName": "ChCl", "compoundID": "1"},
    {"commonName": "Urea", "compoundID": "2"},
    {"commonName": "Water", "compoundID": "3"}
]

# Path to the test CML file
cml_path = "FAIRFluids/data/cml_xml/ChCl_urea.xml"

# Parse the CML file
parser = FAIRFluidsCMLParser(cml_path, compounds=compounds)
doc = parser.parse()

# Print summary
print("Number of compounds:", len(doc.compound))
print("Number of fluids:", len(doc.fluid))
if doc.fluid:
    print("First fluid compounds:", doc.fluid[0].compounds)
    print("First fluid parameters:", [p.parameterID for p in doc.fluid[0].parameter])
    if doc.fluid[0].measurement:
        m = doc.fluid[0].measurement[0]
        print("First measurement property values:", [(pv.propertyID, pv.propValue) for pv in m.propertyValue])
        print("First measurement parameter values:", [(pv.parameterID, pv.paramValue) for pv in m.parameterValue])


def test_parser():
    """Test the BAML parser functionality"""
    print("Testing FAIRFluids BAML Parser")
    print("=" * 40)
    
    # Test parsing the model.md file
    markdown_file = "FAIRFluids/specifications/model.md"
    template_file = "jinja/md_to_baml.j2"
    output_file = "test_output.baml"
    
    if not os.path.exists(markdown_file):
        print(f"Error: {markdown_file} not found!")
        return False
    
    if not os.path.exists(template_file):
        print(f"Error: {template_file} not found!")
        return False
    
    try:
        # Generate BAML from markdown
        generate_baml_from_markdown(markdown_file, template_file, output_file)
        
        # Read and display the generated BAML
        with open(output_file, 'r') as f:
            baml_content = f.read()
        
        print(f"\nGenerated BAML file: {output_file}")
        print(f"File size: {len(baml_content)} characters")
        
        # Show first few lines
        lines = baml_content.split('\n')
        print("\nFirst 20 lines of generated BAML:")
        print("-" * 40)
        for i, line in enumerate(lines[:20]):
            print(f"{i+1:2d}: {line}")
        
        if len(lines) > 20:
            print(f"... and {len(lines) - 20} more lines")
        
        print("\n✅ BAML parser test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during BAML generation: {e}")
        return False

def test_parser_directly():
    """Test the parser directly without template generation"""
    print("\nTesting Parser Directly")
    print("=" * 30)
    
    markdown_file = "FAIRFluids/specifications/model.md"
    
    try:
        # Create parser instance
        parser = ModelMarkdownParser(markdown_file)
        
        # Parse the markdown
        parsed_data = parser.parse()
        
        print(f"Parsed {len(parsed_data['classes'])} classes:")
        for cls in parsed_data['classes']:
            print(f"  - {cls['name']} ({len(cls['fields'])} fields)")
        
        print(f"\nParsed {len(parsed_data['enums'])} enums:")
        for enum in parsed_data['enums']:
            print(f"  - {enum['name']} ({len(enum['enum_values'])} values)")
        
        # Show details of first class
        if parsed_data['classes']:
            first_class = parsed_data['classes'][0]
            print(f"\nFirst class details - {first_class['name']}:")
            for field in first_class['fields']:
                print(f"  - {field['name']}: {field['type']}")
                if field['description']:
                    print(f"    Description: {field['description']}")
        
        print("\n✅ Direct parser test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during direct parsing: {e}")
        return False

if __name__ == "__main__":
    print("FAIRFluids BAML Parser Test Suite")
    print("=" * 50)
    
    # Run tests
    test1_success = test_parser()
    test2_success = test_parser_directly()
    
    if test1_success and test2_success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1) 