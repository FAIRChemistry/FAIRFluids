#!/usr/bin/env python3
"""
Script to create multiple FAIRFluids documents from the joined_viscosity_density.csv data.
Creates a separate document for each unique combination of Component#1, Component#2, and Component#3.
"""

import pandas as pd
import os
import argparse
from pathlib import Path
from fairfluids.core.lib import (
    FAIRFluidsDocument, Version, Citation, Author, Compound, Fluid, 
    Property, Parameter, Measurement, PropertyValue, ParameterValue,
    UnitDefinition, BaseUnit, LitType, Method, Properties, Parameters
)

def create_unit_definition(unit_id, name, base_units_data):
    """Create a UnitDefinition object"""
    unit = UnitDefinition(unitID=unit_id, name=name)
    for base_unit_data in base_units_data:
        unit.add_to_base_units(**base_unit_data)
    return unit

def create_compound(compound_id, common_name, pubchem_id=None):
    """Create a Compound object"""
    return Compound(
        compoundID=compound_id,
        commonName=common_name,
        pubChemID=pubchem_id
    )

def create_property(property_id, property_type, unit):
    """Create a Property object"""
    return Property(
        propertyID=property_id,
        properties=property_type,
        unit=unit
    )

def create_parameter(parameter_id, parameter_type, unit, associated_compound=None):
    """Create a Parameter object"""
    return Parameter(
        parameterID=parameter_id,
        parameter=parameter_type,
        unit=unit,
        associated_compound=associated_compound
    )

def create_measurement(measurement_id, source_doi, property_values, parameter_values, method_type, method_description):
    """Create a Measurement object"""
    measurement = Measurement(
        measurement_id=measurement_id,
        source_doi=source_doi,
        method=method_type,
        method_description=method_description
    )
    
    # Add property values
    for prop_val in property_values:
        measurement.add_to_propertyValue(**prop_val)
    
    # Add parameter values
    for param_val in parameter_values:
        measurement.add_to_parameterValue(**param_val)
    
    return measurement

def create_fairfluids_document(component_combination, data_group):
    """Create a FAIRFluids document for a specific component combination"""
    
    # Extract unique components
    components = []
    for col in ['Component#1', 'Component#2', 'Component#3']:
        if col in data_group.columns:
            value = data_group[col].iloc[0]
            if pd.notna(value) and value:  # Check for non-null and non-empty
                components.append(str(value))
    
    # Create document
    doc = FAIRFluidsDocument()
    
    # Add version
    doc.version = Version(versionMajor=1, versionMinor=0)
    
    # Add citation (using the first DOI from the data)
    first_doi = data_group['Reference (DOI)'].iloc[0]
    if pd.notna(first_doi):
        doc.citation = Citation(
            litType=LitType.JOURNAL,
            doi=first_doi,
            publication_year=""  # Default year
        )
    
    # Add compounds
    compound_ids = []
    for i, component in enumerate(components):
        compound_id = f"compound_{i+1}"
        compound_ids.append(compound_id)
        
        compound = create_compound(
            compound_id=compound_id,
            common_name=component
        )
        doc.add_to_compound(**compound.model_dump())
    
    # Create fluid
    fluid = doc.add_to_fluid(compounds=compound_ids)
    
    # Define units
    temp_unit = create_unit_definition(
        "temp_k", "kelvin", 
        [{"kind": "temperature", "exponent": 1, "multiplier": 1.0, "scale": 0}]
    )
    
    viscosity_unit = create_unit_definition(
        "viscosity_cp", "centipoise",
        [{"kind": "mass", "exponent": 1, "multiplier": 0.001, "scale": 0},
         {"kind": "length", "exponent": -1, "multiplier": 1.0, "scale": 0},
         {"kind": "time", "exponent": -1, "multiplier": 1.0, "scale": 0}]
    )
    
    density_unit = create_unit_definition(
        "density_gcm3", "gram per cubic centimeter",
        [{"kind": "mass", "exponent": 1, "multiplier": 1.0, "scale": 0},
         {"kind": "length", "exponent": -3, "multiplier": 1.0, "scale": 0}]
    )
    
    mole_fraction_unit = create_unit_definition(
        "mole_fraction", "dimensionless",
        [{"kind": "amount", "exponent": 1, "multiplier": 1.0, "scale": 0}]
    )
    
    # Add properties
    viscosity_property = create_property("viscosity", Properties.VISCOSITY, viscosity_unit)
    density_property = create_property("density", Properties.DENSITY, density_unit)
    
    fluid.add_to_property(**viscosity_property.model_dump())
    fluid.add_to_property(**density_property.model_dump())
    
    # Add parameters
    temp_param = create_parameter("temperature", Parameters.TEMPERATURE_K, temp_unit)
    fluid.add_to_parameter(**temp_param.model_dump())
    
    # Add mole fraction parameters for each component
    for i, component in enumerate(components):
        mole_fraction_param = create_parameter(
            f"mole_fraction_{i+1}", 
            Parameters.MOLE_FRACTION, 
            mole_fraction_unit,
            associated_compound=compound_ids[i]
        )
        fluid.add_to_parameter(**mole_fraction_param.model_dump())
    
    # Add measurements
    for idx, row in data_group.iterrows():
        measurement_id = f"measurement_{idx}"
        
        # Property values
        property_values = []
        if pd.notna(row['Viscosity, cP']):
            property_values.append({
                "propertyID": "viscosity",
                "propValue": float(row['Viscosity, cP'])
            })
        if pd.notna(row['Density, g/cm^3']):
            property_values.append({
                "propertyID": "density",
                "propValue": float(row['Density, g/cm^3'])
            })
        
        # Parameter values
        parameter_values = []
        if pd.notna(row['Temperature, K']):
            parameter_values.append({
                "parameterID": "temperature",
                "paramValue": float(row['Temperature, K'])
            })
        
        # Add mole fraction parameters
        for i, component in enumerate(components):
            mole_fraction_col = f'X#{i+1} (molar fraction)'
            if mole_fraction_col in row and pd.notna(row[mole_fraction_col]):
                parameter_values.append({
                    "parameterID": f"mole_fraction_{i+1}",
                    "paramValue": float(row[mole_fraction_col])
                })
        
        # Create measurement
        measurement = create_measurement(
            measurement_id=measurement_id,
            source_doi=row['Reference (DOI)'] if pd.notna(row['Reference (DOI)']) else None,
            property_values=property_values,
            parameter_values=parameter_values,
            method_type=Method.MEASURED,
            method_description="Experimental measurement"
        )
        
        fluid.add_to_measurement(**measurement.model_dump())
    
    return doc

def main():
    """Main function to process CSV and create documents"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Create FAIRFluids documents from CSV data")
    parser.add_argument("--xml", action="store_true", help="Generate XML files")
    parser.add_argument("--json", action="store_true", help="Generate JSON files")
    parser.add_argument("--both", action="store_true", help="Generate both XML and JSON files (default)")
    parser.add_argument("--output-dir", default="generated_fairfluids_documents", 
                       help="Output directory for generated files (default: generated_fairfluids_documents)")
    
    args = parser.parse_args()
    
    # Set default behavior if no format specified
    if not (args.xml or args.json or args.both):
        args.both = True
    
    # Read the CSV file
    csv_path = "fairfluids/data/joined_viscosity_density.csv"
    df = pd.read_csv(csv_path)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print(f"Processing {len(df)} data points...")
    print(f"Output formats: XML={args.xml or args.both}, JSON={args.json or args.both}")
    print(f"Output directory: {output_dir}")
    
    # Group by unique combinations of components
    # For 2-component systems, use Component#1 and Component#2
    # For 3-component systems, use all three components
    df['component_key'] = df.apply(
        lambda row: (
            row['Component#1'] if pd.notna(row['Component#1']) else '',
            row['Component#2'] if pd.notna(row['Component#2']) else '',
            row['Component#3'] if pd.notna(row['Component#3']) else ''
        ), axis=1
    )
    
    # Group by component combinations
    grouped = df.groupby('component_key')
    
    print(f"Found {len(grouped)} unique component combinations")
    
    for (comp1, comp2, comp3), group_data in grouped:
        # Create a descriptive filename
        components = [comp for comp in [comp1, comp2, comp3] if comp]
        base_filename = "_".join(components).replace(" ", "_").replace(",", "").replace(";", "_")
        base_filename = "".join(c for c in base_filename if c.isalnum() or c in "_-")
        
        print(f"Creating document for: {components}")
        print(f"  Base filename: {base_filename}")
        print(f"  Number of data points: {len(group_data)}")
        
        try:
            # Create the document
            doc = create_fairfluids_document(components, group_data)
            
            # Save files based on flags
            if args.xml or args.both:
                xml_filename = base_filename + ".xml"
                xml_output_path = output_dir / xml_filename
                with open(xml_output_path, 'w') as f:
                    f.write(doc.xml())
                print(f"  Created XML: {xml_output_path}")
            
            if args.json or args.both:
                json_filename = base_filename + ".json"
                json_output_path = output_dir / json_filename
                with open(json_output_path, 'w') as f:
                    f.write(doc.model_dump_json(indent=2))
                print(f"  Created JSON: {json_output_path}")
            
        except Exception as e:
            print(f"  Error creating document: {e}")
            continue
    
    # Count generated files
    xml_count = len(list(output_dir.glob("*.xml"))) if (args.xml or args.both) else 0
    json_count = len(list(output_dir.glob("*.json"))) if (args.json or args.both) else 0
    
    print(f"\nGenerated {xml_count} XML files and {json_count} JSON files in {output_dir}")

if __name__ == "__main__":
    main()
