#!/usr/bin/env python3
"""
Example usage of ThermoMLMapper

This script demonstrates how to use the ThermoMLMapper class to work with
ThermoML XML files programmatically.
"""

from thermoml_mapper import ThermoMLMapper
import json

def main():
    """Demonstrate various uses of the ThermoMLMapper."""
    
    # Initialize the mapper
    mapper = ThermoMLMapper()
    
    # Path to your ThermoML XML file
    xml_file = "fairfluids/data/thermoml_xml/spera_et_al_fpe_592_2025_114324.xml"
    
    print("=== ThermoML XML Processing Example ===\n")
    
    try:
        # 1. Get a summary of the file
        print("1. Getting file summary...")
        summary = mapper.get_summary(xml_file)
        print(f"   File: {summary['file_path']}")
        print(f"   Version: {summary['version']}")
        print(f"   Compounds: {summary['compounds']}")
        print(f"   Pure/Mixture Data Sets: {summary['pure_mixture_data_sets']}")
        print(f"   Reaction Data Sets: {summary['reaction_data_sets']}")
        print(f"   Title: {summary['citation']['title']}")
        print(f"   Authors: {', '.join(summary['citation']['authors'])}")
        print(f"   DOI: {summary['citation']['doi']}")
        print()
        
        # 2. Parse the XML file to get the full DataReport model
        print("2. Parsing XML file to DataReport model...")
        data_report = mapper.parse_xml_file(xml_file)
        print(f"   Successfully parsed {xml_file}")
        print(f"   DataReport has {len(data_report.compound)} compounds")
        print(f"   DataReport has {len(data_report.pure_or_mixture_data)} pure/mixture data sets")
        print()
        
        # 3. Access specific compound information
        print("3. Accessing compound information...")
        for i, compound in enumerate(data_report.compound[:3]):  # Show first 3 compounds
            print(f"   Compound {i+1}:")
            print(f"     PubChem ID: {compound.n_pub_chem_id}")
            print(f"     Common Names: {', '.join(compound.s_common_name)}")
            print(f"     Formula: {compound.s_formula_molec}")
            print(f"     IUPAC Name: {compound.s_iupac_name}")
            print()
        
        # 4. Access citation information
        print("4. Accessing citation information...")
        if data_report.citation:
            citation = data_report.citation
            print(f"   Title: {citation.s_title}")
            print(f"   Authors: {', '.join(citation.s_author)}")
            print(f"   Publication: {citation.s_pub_name}")
            print(f"   Year: {citation.yr_pub_yr}")
            print(f"   DOI: {citation.s_doi}")
            print(f"   Abstract: {citation.s_abstract[:100]}...")
            print()
        
        # 5. Convert to JSON (first 1000 characters to avoid overwhelming output)
        print("5. Converting to JSON...")
        json_data = mapper.convert_to_json(xml_file)
        print(f"   JSON length: {len(json_data)} characters")
        print(f"   First 200 characters: {json_data[:200]}...")
        print()
        
        # 6. Validate the file
        print("6. Validating XML file...")
        is_valid = mapper.validate_xml_file(xml_file)
        print(f"   File is valid: {is_valid}")
        print()
        
        # 7. Demonstrate working with the parsed data
        print("7. Working with parsed data...")
        print("   You can now:")
        print("   - Access all compound properties programmatically")
        print("   - Iterate through pure/mixture data sets")
        print("   - Extract specific property values")
        print("   - Convert data to other formats")
        print("   - Perform data analysis and validation")
        print()
        
        # 8. Show how to access pure/mixture data if available
        if data_report.pure_or_mixture_data:
            print("8. Pure/Mixture Data information...")
            for i, data_set in enumerate(data_report.pure_or_mixture_data[:2]):  # Show first 2
                print(f"   Data Set {i+1}:")
                print(f"     Number: {data_set.n_pure_or_mixture_data_number}")
                print(f"     Compiler: {data_set.s_compiler}")
                print(f"     Contributor: {data_set.s_contributor}")
                print(f"     Date Added: {data_set.date_date_added}")
                print(f"     Purpose: {data_set.e_exp_purpose}")
                print()
        
        print("=== Example completed successfully! ===")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
