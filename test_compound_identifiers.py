#!/usr/bin/env python3

import sys
sys.path.append('/home/sga/Code/FAIRFluids')

from FAIRFluids.core.functionalities import myFAIRFluidsDocument
from FAIRFluids.core.lib import Version, C_id

# Test the compound identifier assignment
try:
    # Create document
    doc = myFAIRFluidsDocument(version=Version(versionMajor=1, versionMinor=0))
    
    # Add compounds with compound identifiers
    doc.add_to_compound(
        compund_identifier=C_id(c_id="Water"),
        pubChemID=962,
        commonName="Water",
        name_IUPAC="oxidane", 
        standard_InChI="InChI=1S/H2O/h1H2",
        standard_InChI_key="XLYOFNOQVPJJNP-UHFFFAOYSA-N"
    )
    
    doc.add_to_compound(
        compund_identifier=C_id(c_id="CholinChloride"),
        pubChemID=123345647789,
        commonName="CholinChloride",
        name_IUPAC="CholinChloride", 
        standard_InChI="InChI=1S/C5H11ClNO2/c1"
    )
    
    doc.add_to_compound(
        compund_identifier=C_id(c_id="Glycerol"),
        pubChemID=1128,
        commonName="Glycerol",
        name_IUPAC="glycerol",
        standard_InChI="InChI=1S/C3H8O3/c1-2-3-4/h2-3H,1H3",
        standard_InChI_key="XLYOFNOQVPJJNP-UHFFFAOYSA-N"
    )
    
    # Parse CML file
    doc.get_data_from_cml("data/cml_xml/ChCl_glycerol.xml")
    
    # Get viscosity data with compound identifiers
    viscosity_data = doc.get_viscosity_data()
    
    print(f"✅ Successfully parsed CML file")
    print(f"📊 Found {len(viscosity_data)} viscosity data points")
    print(f"🧪 Found {len(doc.fluid)} fluid entries")
    
    # Show first few entries with compound identifiers
    print("\n📋 First 3 entries with compound identifiers:")
    for i, entry in enumerate(viscosity_data[:3]):
        print(f"Entry {i+1}:")
        print(f"  Temperature: {entry['temperature']} K")
        print(f"  Mole fractions: {entry['mole_fractions']}")
        print(f"  Compound IDs: {entry['compound_identifiers']}")
        print(f"  Viscosity: {entry['viscosity']} mPa·s")
        print()
    
    # Check if compound identifiers are properly assigned
    print("🔍 Checking constraint compound identifiers:")
    constraint_count = 0
    identified_constraints = 0
    
    for fluid in doc.fluid:
        if fluid.constraint:
            for constraint in fluid.constraint:
                if (constraint.constraint_type and 
                    constraint.constraint_type.e_component_composition == eComponentComposition.MOLE_FRACTION):
                    constraint_count += 1
                    if constraint.compound_identifier:
                        identified_constraints += 1
                        print(f"  ✓ Constraint {constraint.constraint_number}: {constraint.compound_identifier.c_id} = {constraint.constraint_value}")
                    else:
                        print(f"  ✗ Constraint {constraint.constraint_number}: No compound ID = {constraint.constraint_value}")
    
    print(f"\n📈 Summary:")
    print(f"  Total mole fraction constraints: {constraint_count}")
    print(f"  Constraints with compound IDs: {identified_constraints}")
    print(f"  Success rate: {identified_constraints/constraint_count*100:.1f}%" if constraint_count > 0 else "No constraints found")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 