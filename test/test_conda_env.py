#!/usr/bin/env python3
"""
Test script to verify FAIRFluids conda environment setup.
"""

import sys
import importlib

def test_imports():
    """Test that all required packages can be imported."""
    required_packages = [
        'pydantic',
        'pydantic_xml',
        'lxml',
        'numpy',
        'pandas',
        'ipykernel',
        'matplotlib',
        'seaborn',
        'scipy',
    ]
    
    print("🧪 Testing package imports...")
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError as e:
            print(f"❌ {package}: {e}")
            return False
    
    return True

def test_fairfluids():
    """Test FAIRFluids package imports."""
    print("\n🧪 Testing FAIRFluids imports...")
    
    try:
        import fairfluids
        print("✅ fairfluids package")
        
        from fairfluids import FAIRFluidsDocument, Version, Citation
        print("✅ FAIRFluidsDocument, Version, Citation")
        
        from fairfluids import FluidIO, FAIRFluidsCMLParser
        print("✅ FluidIO, FAIRFluidsCMLParser")
        
        return True
    except ImportError as e:
        print(f"❌ FAIRFluids import error: {e}")
        return False

def test_cli():
    """Test CLI functionality."""
    print("\n🧪 Testing CLI...")
    
    try:
        from fairfluids.cli import main
        print("✅ CLI module imported")
        return True
    except ImportError as e:
        print(f"❌ CLI import error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 FAIRFluids Conda Environment Test")
    print("=" * 40)
    
    # Test Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Run tests
    tests = [
        test_imports,
        test_fairfluids,
        test_cli,
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed! Your conda environment is ready.")
    else:
        print("❌ Some tests failed. Please check your installation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
