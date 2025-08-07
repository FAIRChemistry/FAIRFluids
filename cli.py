#!/usr/bin/env python3
"""
Command-line interface for FAIRFluids.

This module provides a simple CLI for working with FAIR fluid data documents.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from core.lib import FAIRFluidsDocument, Version, Citation
from core.fluid_io import FluidIO
from core.functionalities import FAIRFluidsCMLParser


def create_document(version_major: int = 1, version_minor: int = 0) -> FAIRFluidsDocument:
    """Create a new FAIRFluids document."""
    return FAIRFluidsDocument(
        version=Version(versionMajor=version_major, versionMinor=version_minor)
    )


def load_from_csv(csv_path: str) -> FluidIO:
    """Load fluid data from CSV file."""
    fluid = FluidIO()
    fluid.data_from_csv(csv_path)
    return fluid


def parse_cml(cml_path: str, document: Optional[FAIRFluidsDocument] = None) -> FAIRFluidsDocument:
    """Parse CML file and return document."""
    if document is None:
        document = create_document()
    
    parser = FAIRFluidsCMLParser(cml_path, document=document)
    return parser.parse()


def save_document(document: FAIRFluidsDocument, output_path: str) -> None:
    """Save document to JSON file."""
    with open(output_path, 'w') as f:
        f.write(document.model_dump_json(indent=2))


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="FAIRFluids - A framework for creating FAIR fluid data documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new document
  fairfluids create --output document.json

  # Load data from CSV
  fairfluids csv data.csv --output document.json

  # Parse CML file
  fairfluids cml data.xml --output document.json

  # Convert between formats
  fairfluids convert input.json --output output.xml
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new FAIRFluids document')
    create_parser.add_argument('--output', '-o', required=True, help='Output JSON file path')
    create_parser.add_argument('--version-major', type=int, default=1, help='Major version number')
    create_parser.add_argument('--version-minor', type=int, default=0, help='Minor version number')
    
    # CSV command
    csv_parser = subparsers.add_parser('csv', help='Load data from CSV file')
    csv_parser.add_argument('input', help='Input CSV file path')
    csv_parser.add_argument('--output', '-o', required=True, help='Output JSON file path')
    
    # CML command
    cml_parser = subparsers.add_parser('cml', help='Parse CML file')
    cml_parser.add_argument('input', help='Input CML file path')
    cml_parser.add_argument('--output', '-o', required=True, help='Output JSON file path')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert between formats')
    convert_parser.add_argument('input', help='Input file path')
    convert_parser.add_argument('--output', '-o', required=True, help='Output file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'create':
            doc = create_document(args.version_major, args.version_minor)
            save_document(doc, args.output)
            print(f"Created new FAIRFluids document: {args.output}")
            
        elif args.command == 'csv':
            if not Path(args.input).exists():
                print(f"Error: Input file '{args.input}' not found")
                sys.exit(1)
            
            doc = create_document()
            fluid = load_from_csv(args.input)
            doc.fluid.append(fluid)
            save_document(doc, args.output)
            print(f"Loaded CSV data and saved to: {args.output}")
            
        elif args.command == 'cml':
            if not Path(args.input).exists():
                print(f"Error: Input file '{args.input}' not found")
                sys.exit(1)
            
            doc = parse_cml(args.input)
            save_document(doc, args.output)
            print(f"Parsed CML file and saved to: {args.output}")
            
        elif args.command == 'convert':
            if not Path(args.input).exists():
                print(f"Error: Input file '{args.input}' not found")
                sys.exit(1)
            
            # For now, just copy JSON files
            if args.input.endswith('.json') and args.output.endswith('.json'):
                with open(args.input, 'r') as f:
                    data = json.load(f)
                with open(args.output, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"Converted {args.input} to {args.output}")
            else:
                print("Error: Only JSON to JSON conversion is currently supported")
                sys.exit(1)
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
