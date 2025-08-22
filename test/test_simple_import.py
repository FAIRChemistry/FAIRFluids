#!/usr/bin/env python3
"""
Simple test to check direct imports work.
"""

def test_direct_imports():
    """Test direct imports from the current directory."""
    print("🧪 Testing direct imports...")
    
    try:
        # Test direct imports
        from core.lib import FAIRFluidsDocument, Version, Citation
        print("✅ from core.lib import FAIRFluidsDocument, Version, Citation")
        
        from core.fluid_io import FluidIO
        print("✅ from core.fluid_io import FluidIO")
        
        from core.functionalities import FAIRFluidsCMLParser
        print("✅ from core.functionalities import FAIRFluidsCMLParser")
        
        return True
    except ImportError as e:
        print(f"❌ Direct import error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality with direct imports."""
    print("\n🧪 Testing basic functionality...")
    
    try:
        from core.lib import FAIRFluidsDocument, Version, Citation
        
        # Create a document
        doc = FAIRFluidsDocument(version=Version(versionMajor=1, versionMinor=0))
        
        # Add citation
        doc.citation = Citation(litType="journal")
        doc.citation.add_to_author(given_name="John", family_name="Doe")
        
        # Add compound
        doc.add_to_compound(
            compoundID="1",
            pubChemID=962,
            commonName="Water",
            name_IUPAC="oxidane"
        )
        
        print("✅ Basic functionality test - SUCCESS")
        return True
    except Exception as e:
        print(f"❌ Basic functionality test - FAILED: {e}")
        return False

def main():
    """Run tests."""
    print("🚀 FAIRFluids Direct Import Test")
    print("=" * 40)
    
    tests = [
        test_direct_imports,
        test_basic_functionality,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! You can use FAIRFluids with direct imports:")
        print("""
# Example usage with direct imports:
from core.lib import FAIRFluidsDocument, Version, Citation

# Create a document
doc = FAIRFluidsDocument(version=Version(versionMajor=1, versionMinor=0))

# Add citation
doc.citation = Citation(litType="journal")
doc.citation.add_to_author(given_name="John", family_name="Doe")

# Add compound
doc.add_to_compound(
    compoundID="1",
    pubChemID=962,
    commonName="Water",
    name_IUPAC="oxidane"
)

# Save to JSON
with open('my_document.json', 'w') as f:
    f.write(doc.model_dump_json(indent=2))
        """)
    else:
        print("❌ Some tests failed.")

if __name__ == "__main__":
    main()
