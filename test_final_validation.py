#!/usr/bin/env python3
"""
Test the final JSON output to see if it works with XML serialization.
"""

import json
from fairfluids.core.lib import FAIRFluidsDocument

def test_final_output():
    """Test the final converted output."""
    
    # Load the latest data
    with open("spera_et_al_fpe_592_2025_114324_improved_converted.json", 'r') as f:
        data = json.load(f)
    
    print("🔍 Testing latest converted output...")
    
    try:
        # Create FAIRFluids document
        doc = FAIRFluidsDocument(**data)
        print("✅ FAIRFluidsDocument created successfully")
        
        # Test XML serialization
        doc_xml = doc.to_xml()
        print("✅ Full document XML serialization successful!")
        print(f"📄 XML length: {len(doc_xml)} characters")
        
        # Show first part of XML
        print(f"📄 XML preview: {doc_xml[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Final validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_final_output()
    if success:
        print("\n🎉 VALIDATION SUCCESSFUL!")
        print("✅ The converted ThermoML data is fully valid FAIRFluids format")
    else:
        print("\n❌ VALIDATION FAILED")
        print("⚠️ The converted data still has issues")
