#!/usr/bin/env python3
"""
Test script to verify FAIRFluids imports work correctly.
"""

import sys
import os

# Add current directory to path
current_dir = os.getcwd()
sys.path.append(current_dir)

print(f"Current directory: {current_dir}")
print(f"Python path: {sys.path}")

try:
    # Try importing from specifications.lib
    from FAIRFluids.core.lib import FAIRFluidsDocument, Version
    print("✓ Successfully imported from specifications.lib")
    
    # Test creating a simple document
    version = Version(versionMajor=1, versionMinor=0)
    document = FAIRFluidsDocument(version=version)
    print("✓ Successfully created FAIRFluidsDocument")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("\nTrying alternative import methods...")
    
    try:
        # Try direct import
        import FAIRFluids.core.lib as lib
        print("✓ Successfully imported specifications.lib as lib")
        document = lib.FAIRFluidsDocument(version=lib.Version(versionMajor=1, versionMinor=0))
        print("✓ Successfully created FAIRFluidsDocument")
        
    except ImportError as e2:
        print(f"✗ Alternative import also failed: {e2}")
        
        # List available modules
        print("\nAvailable modules in current directory:")
        for item in os.listdir('.'):
            if os.path.isdir(item):
                print(f"  Directory: {item}")
                if os.path.exists(os.path.join(item, '__init__.py')):
                    print(f"    (has __init__.py)")
            elif item.endswith('.py'):
                print(f"  File: {item}")

except Exception as e:
    print(f"✗ Other error: {e}") 