#!/usr/bin/env python3
"""
Test script to verify FAIRFluids installation.
"""

def test_import():
    """Test that fairfluids can be imported."""
    try:
        import fairfluids
        print("✅ import fairfluids - SUCCESS")
        return True
    except ImportError as e:
        print(f"❌ import fairfluids - FAILED: {e}")
        return False

def test_main_classes():
    """Test that main classes can be imported."""
    try:
        from fairfluids import FAIRFluidsDocument, Version, Citation
        print("✅ from fairfluids import FAIRFluidsDocument, Version, Citation - SUCCESS")
        return True
    except ImportError as e:
        print(f"❌ from fairfluids import main classes - FAILED: {e}")
        return False

def test_utilities():
    """Test that utility classes can be imported."""
    try:
        from fairfluids import FluidIO, FAIRFluidsCMLParser
        print("✅ from fairfluids import FluidIO, FAIRFluidsCMLParser - SUCCESS")
        return True
    except ImportError as e:
        print(f"❌ from fairfluids import utilities - FAILED: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality."""
    try:
        from fairfluids import FAIRFluidsDocument, Version, Citation
        
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
    """Run all tests."""
    print("🚀 FAIRFluids Installation Test")
    print("=" * 40)
    
    tests = [
        test_import,
        test_main_classes,
        test_utilities,
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
        print("🎉 All tests passed! FAIRFluids is properly installed.")
        print("\nYou can now use FAIRFluids:")
        print("""
# Example usage:
import fairfluids
from fairfluids import FAIRFluidsDocument, Version, Citation

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
        print("❌ Some tests failed. Please check the installation.")
        print("\nTroubleshooting:")
        print("1. Make sure you're in the FAIRFluids directory")
        print("2. Try: pip install -e .")
        print("3. Try: conda env create -f environment.yml")

if __name__ == "__main__":
    main()
