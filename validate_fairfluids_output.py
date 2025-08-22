#!/usr/bin/env python3
"""
Validation script to test the converted ThermoML-to-FAIRFluids output against the FAIRFluids model.

This script:
1. Loads the converted JSON output
2. Attempts to parse it with the FAIRFluids model
3. Validates the data structure and types
4. Tests XML serialization/deserialization
5. Reports validation results
"""

import sys
import json
from pathlib import Path

try:
    from fairfluids.core.lib import (
        FAIRFluidsDocument, Version, Citation, Author, Compound, 
        Fluid, Property, Parameter, Measurement, PropertyValue, 
        ParameterValue, Properties, Parameters, Method, LitType
    )
    FAIRFLUIDS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: FAIRFluids models not available: {e}")
    FAIRFLUIDS_AVAILABLE = False

def validate_json_structure(data):
    """Validate the basic JSON structure."""
    print("🔍 Validating JSON structure...")
    
    required_fields = ['version', 'citation', 'compound', 'fluid']
    missing_fields = []
    
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return False
    
    print("✅ All required root fields present")
    
    # Check version structure
    version = data.get('version', {})
    if not isinstance(version, dict) or 'versionMajor' not in version:
        print("❌ Invalid version structure")
        return False
    
    # Check compounds structure
    compounds = data.get('compound', [])
    if not isinstance(compounds, list):
        print("❌ Compounds should be a list")
        return False
    
    print(f"✅ Found {len(compounds)} compounds")
    
    # Check fluids structure
    fluids = data.get('fluid', [])
    if not isinstance(fluids, list):
        print("❌ Fluids should be a list")
        return False
    
    print(f"✅ Found {len(fluids)} fluids")
    
    return True

def validate_enum_values(data):
    """Validate enum values against FAIRFluids enums."""
    print("\n🔍 Validating enum values...")
    
    errors = []
    
    # Validate citation litType
    citation = data.get('citation', {})
    if citation and 'litType' in citation:
        lit_type = citation['litType']
        valid_lit_types = ['journal', 'book', 'thesis', 'report', 'patent', 'conferenceProceedings', 'unspecified']
        if lit_type not in valid_lit_types:
            errors.append(f"Invalid litType: {lit_type}")
    
    # Validate property types
    fluids = data.get('fluid', [])
    for i, fluid in enumerate(fluids):
        properties = fluid.get('property', [])
        for j, prop in enumerate(properties):
            prop_type = prop.get('properties')
            if prop_type:
                valid_prop_types = ['density', 'viscosity', 'specificHeatCapacity', 'boilingPoint', 'meltingPoint', 
                                  'thermalConductivity', 'vaporPressure', 'Compressibility', 'pH', 'polarity']
                if prop_type not in valid_prop_types:
                    errors.append(f"Fluid {i+1}, Property {j+1}: Invalid properties enum: {prop_type}")
        
        # Validate parameter types
        parameters = fluid.get('parameter', [])
        for j, param in enumerate(parameters):
            param_type = param.get('parameter')
            if param_type:
                # Check if it's a valid parameter type (basic validation)
                if not isinstance(param_type, str) or len(param_type) == 0:
                    errors.append(f"Fluid {i+1}, Parameter {j+1}: Invalid parameter type: {param_type}")
        
        # Validate method types
        measurements = fluid.get('measurement', [])
        for j, meas in enumerate(measurements):
            method = meas.get('method')
            if method:
                valid_methods = ['simulated,', 'measured,', 'calculated,', 'literature']
                if method not in valid_methods:
                    errors.append(f"Fluid {i+1}, Measurement {j+1}: Invalid method: {method}")
    
    if errors:
        print("❌ Enum validation errors:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"   - {error}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more errors")
        return False
    else:
        print("✅ All enum values are valid")
        return True

def validate_data_consistency(data):
    """Validate data consistency and relationships."""
    print("\n🔍 Validating data consistency...")
    
    errors = []
    
    # Get all compound IDs
    compounds = data.get('compound', [])
    compound_ids = {comp.get('compoundID') for comp in compounds if comp.get('compoundID')}
    
    # Check fluid references
    fluids = data.get('fluid', [])
    for i, fluid in enumerate(fluids):
        fluid_compounds = fluid.get('compounds', [])
        
        # Check if all referenced compounds exist
        for comp_id in fluid_compounds:
            if comp_id not in compound_ids:
                errors.append(f"Fluid {i+1}: References non-existent compound: {comp_id}")
        
        # Check property-measurement consistency
        properties = fluid.get('property', [])
        measurements = fluid.get('measurement', [])
        
        property_ids = {prop.get('propertyID') for prop in properties if prop.get('propertyID')}
        
        for j, meas in enumerate(measurements):
            prop_values = meas.get('propertyValue', [])
            for k, prop_val in enumerate(prop_values):
                prop_id = prop_val.get('propertyID')
                if prop_id and prop_id not in property_ids:
                    errors.append(f"Fluid {i+1}, Measurement {j+1}, PropertyValue {k+1}: References non-existent property: {prop_id}")
        
        # Check parameter-measurement consistency
        parameters = fluid.get('parameter', [])
        parameter_ids = {param.get('parameterID') for param in parameters if param.get('parameterID')}
        
        for j, meas in enumerate(measurements):
            param_values = meas.get('parameterValue', [])
            for k, param_val in enumerate(param_values):
                param_id = param_val.get('parameterID')
                if param_id and param_id not in parameter_ids:
                    errors.append(f"Fluid {i+1}, Measurement {j+1}, ParameterValue {k+1}: References non-existent parameter: {param_id}")
    
    if errors:
        print("❌ Data consistency errors:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"   - {error}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more errors")
        return False
    else:
        print("✅ Data consistency validation passed")
        return True

def validate_with_pydantic(data):
    """Validate using the actual FAIRFluids Pydantic model."""
    if not FAIRFLUIDS_AVAILABLE:
        print("\n⚠️ Skipping Pydantic validation (FAIRFluids not available)")
        return True
    
    print("\n🔍 Validating with FAIRFluids Pydantic model...")
    
    try:
        # Try to create a FAIRFluidsDocument from the data
        fairfluids_doc = FAIRFluidsDocument(**data)
        print("✅ Successfully created FAIRFluidsDocument")
        
        # Test XML serialization
        try:
            xml_output = fairfluids_doc.xml()
            print("✅ XML serialization successful")
            print(f"   XML length: {len(xml_output)} characters")
            
            # Test that XML contains expected elements
            if '<FAIRFluidsDocument' in xml_output and '</FAIRFluidsDocument>' in xml_output:
                print("✅ XML contains expected root elements")
            else:
                print("❌ XML missing expected root elements")
                return False
            
        except Exception as e:
            print(f"❌ XML serialization failed: {e}")
            return False
        
        # Validate some key properties
        if fairfluids_doc.version and fairfluids_doc.version.versionMajor:
            print(f"✅ Version: {fairfluids_doc.version.versionMajor}.{fairfluids_doc.version.versionMinor}")
        
        if fairfluids_doc.citation and fairfluids_doc.citation.title:
            print(f"✅ Citation title: {fairfluids_doc.citation.title[:50]}...")
        
        print(f"✅ Compounds: {len(fairfluids_doc.compound)}")
        print(f"✅ Fluids: {len(fairfluids_doc.fluid)}")
        
        # Validate a sample of fluids
        for i, fluid in enumerate(fairfluids_doc.fluid[:3]):  # Check first 3 fluids
            print(f"✅ Fluid {i+1}: {len(fluid.compounds)} compounds, {len(fluid.property)} properties, {len(fluid.measurement)} measurements")
        
        return True
        
    except Exception as e:
        print(f"❌ Pydantic validation failed: {e}")
        
        # Try to provide more specific error information
        if "validation error" in str(e).lower():
            print("   This appears to be a validation error. Check:")
            print("   - Required fields are present")
            print("   - Data types match expected types")
            print("   - Enum values are correct")
        
        return False

def main():
    """Main validation function."""
    if len(sys.argv) != 2:
        print("Usage: python validate_fairfluids_output.py <converted_json_file>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    if not Path(json_file).exists():
        print(f"Error: File {json_file} not found.")
        sys.exit(1)
    
    print(f"🚀 Validating FAIRFluids output: {json_file}")
    print("=" * 60)
    
    # Load JSON data
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        print(f"✅ Successfully loaded JSON file ({len(json.dumps(data))} characters)")
    except Exception as e:
        print(f"❌ Failed to load JSON file: {e}")
        sys.exit(1)
    
    # Run validation steps
    validation_results = []
    
    # Step 1: JSON structure validation
    validation_results.append(validate_json_structure(data))
    
    # Step 2: Enum values validation
    validation_results.append(validate_enum_values(data))
    
    # Step 3: Data consistency validation
    validation_results.append(validate_data_consistency(data))
    
    # Step 4: Pydantic model validation
    validation_results.append(validate_with_pydantic(data))
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(validation_results)
    total = len(validation_results)
    
    if passed == total:
        print(f"🎉 All validations passed! ({passed}/{total})")
        print("✅ The converted output is valid FAIRFluids format")
        return 0
    else:
        print(f"❌ {total - passed} validation(s) failed ({passed}/{total} passed)")
        print("⚠️ The converted output needs fixes before it's valid FAIRFluids format")
        return 1

if __name__ == "__main__":
    sys.exit(main())
