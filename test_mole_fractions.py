#!/usr/bin/env python3

import sys
sys.path.append('/home/sga/Code/FAIRFluids')

from FAIRFluids.core.functionalities import myFAIRFluidsDocument
from FAIRFluids.core.lib import Version

# Test the mole fraction extraction fix
try:
    # Create document
    doc = myFAIRFluidsDocument(version=Version(versionMajor=1, versionMinor=0))
    
    # Add compounds
    doc.add_to_compound(
        pubChemID=962,
        commonName="Water",
        name_IUPAC="oxidane", 
        standard_InChI="InChI=1S/H2O/h1H2",
        standard_InChI_key="XLYOFNOQVPJJNP-UHFFFAOYSA-N"
    )
    
    doc.add_to_compound(
        pubChemID=123345647789,
        commonName="CholinChloride",
        name_IUPAC="CholinChloride", 
        standard_InChI="InChI=1S/C5H11ClNO2/c1"
    )
    
    doc.add_to_compound(
        pubChemID=1128,
        commonName="Glycerol",
        name_IUPAC="glycerol",
        standard_InChI="InChI=1S/C3H8O3/c1-2-3-4/h2-3H,1H3",
        standard_InChI_key="XLYOFNOQVPJJNP-UHFFFAOYSA-N"
    )
    
    # Test the CML parsing
    print("Testing CML parsing...")
    doc.get_data_from_cml("FAIRFluids/data/cml_xml/ChCl_glycerol.xml")
    
    print(f"Success! Parsed {len(doc.fluid)} fluid entries")
    
    # Test viscosity data extraction
    print("\nTesting viscosity data extraction...")
    viscosity_data = doc.get_viscosity_data()
    print(f"Found {len(viscosity_data)} viscosity data points")
    
    # Show first few entries with mole fractions
    for i, data in enumerate(viscosity_data[:10]):
        print(f"Entry {i+1}: Temp={data['temperature']}K, Viscosity={data['viscosity']} mPa·s, Mole Fractions={data['mole_fractions']}")
    
    # Count entries with mole fractions
    entries_with_mole_fractions = sum(1 for data in viscosity_data if data['mole_fractions'])
    print(f"\nEntries with mole fractions: {entries_with_mole_fractions}/{len(viscosity_data)}")
    
    # Show some sample constraints from the first few fluids
    print("\nSample constraints from first 3 fluids:")
    for i, fluid in enumerate(doc.fluid[:3]):
        print(f"Fluid {i+1}: {len(fluid.constraint)} constraints")
        for j, constraint in enumerate(fluid.constraint):
            print(f"  Constraint {j+1}: {constraint.constraint_type.e_component_composition} = {constraint.constraint_value}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 