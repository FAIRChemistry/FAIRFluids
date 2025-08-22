#!/usr/bin/env python3
"""
Script to match compounds from compounds_density folder with FAIRFluids documents
in test_json_only folder based on compoundID and common name matching.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import argparse
from fairfluids.core.lib import FAIRFluidsDocument, Compound


def load_compounds_from_density_folder(density_folder: str) -> Dict[str, Dict]:
    """
    Load all compound files from the compounds_density folder.
    
    Args:
        density_folder: Path to the compounds_density folder
        
    Returns:
        Dictionary mapping compoundID to compound data
    """
    compounds = {}
    density_path = Path(density_folder)
    
    if not density_path.exists():
        print(f"❌ Compounds density folder not found: {density_folder}")
        return compounds
    
    print(f"📁 Loading compounds from: {density_folder}")
    
    for json_file in density_path.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                compound_data = json.load(f)
                
            compound_id = compound_data.get('compoundID')
            if compound_id:
                compounds[compound_id] = compound_data
                print(f"  ✅ Loaded compound: {compound_id}")
            else:
                print(f"  ⚠️  Skipping file {json_file.name} - no compoundID found")
                
        except Exception as e:
            print(f"  ❌ Error loading {json_file.name}: {e}")
    
    print(f"📊 Total compounds loaded: {len(compounds)}")
    return compounds


def load_fairfluids_documents(json_folder: str) -> List[FAIRFluidsDocument]:
    """
    Load all FAIRFluids documents from the test_json_only folder.
    
    Args:
        json_folder: Path to the test_json_only folder
        
    Returns:
        List of FAIRFluidsDocument objects
    """
    documents = []
    json_path = Path(json_folder)
    
    if not json_path.exists():
        print(f"❌ Test JSON folder not found: {json_folder}")
        return documents
    
    print(f"📁 Loading FAIRFluids documents from: {json_folder}")
    
    for json_file in json_path.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                doc_data = json.load(f)
                
            # Create FAIRFluidsDocument from JSON data
            doc = FAIRFluidsDocument.model_validate(doc_data)
            documents.append(doc)
            print(f"  ✅ Loaded document: {json_file.name}")
            
        except Exception as e:
            print(f"  ❌ Error loading {json_file.name}: {e}")
    
    print(f"📊 Total documents loaded: {len(documents)}")
    return documents


def match_compounds_to_documents(compounds: Dict[str, Dict], 
                                documents: List[FAIRFluidsDocument]) -> List[FAIRFluidsDocument]:
    """
    Match compounds from compounds_density to documents based on compoundID and common name.
    
    Args:
        compounds: Dictionary of compound data from compounds_density
        documents: List of FAIRFluidsDocument objects
        
    Returns:
        List of updated FAIRFluidsDocument objects
    """
    print("\n🔍 Matching compounds to documents...")
    
    # Create a mapping from common name to compound data for easier lookup
    common_name_to_compound = {}
    for compound_id, compound_data in compounds.items():
        common_name = compound_data.get('commonName', '').lower().strip()
        if common_name:
            common_name_to_compound[common_name] = compound_data
    
    print(f"📊 Compounds available for matching: {len(common_name_to_compound)}")
    
    updated_documents = []
    total_matches = 0
    
    for doc in documents:
        updated_compounds = []
        doc_matches = 0
        
        for compound in doc.compound:
            compound_id = compound.compoundID
            common_name = compound.commonName.lower().strip() if compound.commonName else ""
            
            # Try to find a match
            matched_compound_data = None
            
            # First try exact compoundID match
            if compound_id in compounds:
                matched_compound_data = compounds[compound_id]
                print(f"  ✅ Exact compoundID match: {compound_id}")
            
            # Then try common name match
            elif common_name in common_name_to_compound:
                matched_compound_data = common_name_to_compound[common_name]
                print(f"  ✅ Common name match: {common_name} -> {matched_compound_data['compoundID']}")
            
            # If we found a match, update the compound
            if matched_compound_data:
                # Create new compound with updated data
                updated_compound = Compound(
                    compoundID=matched_compound_data['compoundID'],
                    pubChemID=matched_compound_data.get('pubChemID'),
                    commonName=matched_compound_data.get('commonName'),
                    SELFIE=matched_compound_data.get('SELFIE'),
                    name_IUPAC=matched_compound_data.get('name_IUPAC'),
                    standard_InChI=matched_compound_data.get('standard_InChI'),
                    standard_InChI_key=matched_compound_data.get('standard_InChI_key')
                )
                updated_compounds.append(updated_compound)
                doc_matches += 1
            else:
                # Keep original compound if no match found
                updated_compounds.append(compound)
                print(f"  ⚠️  No match found for: {compound_id} ({common_name})")
        
        # Create updated document with matched compounds
        updated_doc = FAIRFluidsDocument(
            version=doc.version,
            citation=doc.citation,
            compound=updated_compounds,
            fluid=doc.fluid
        )
        
        # Update fluid compounds references to use new compoundIDs
        for fluid in updated_doc.fluid:
            updated_compounds_refs = []
            for compound_ref in fluid.compounds:
                # Find the original compound that had this reference
                original_compound = None
                for orig_compound in doc.compound:
                    if orig_compound.compoundID == compound_ref:
                        original_compound = orig_compound
                        break
                
                if original_compound:
                    # Find the updated compound that corresponds to this original compound
                    for updated_compound in updated_compounds:
                        orig_common_name = original_compound.commonName.lower().strip() if original_compound.commonName else ""
                        updated_common_name = updated_compound.commonName.lower().strip() if updated_compound.commonName else ""
                        
                        if orig_common_name == updated_common_name:
                            updated_compounds_refs.append(updated_compound.compoundID)
                            break
                    else:
                        # If no match found, keep original reference
                        updated_compounds_refs.append(compound_ref)
                else:
                    # If compound_ref is not found in original compounds, keep it as is
                    updated_compounds_refs.append(compound_ref)
            
            fluid.compounds = updated_compounds_refs
        
        updated_documents.append(updated_doc)
        total_matches += doc_matches
        
        if doc_matches > 0:
            print(f"  📄 Document updated with {doc_matches} compound matches")
    
    print(f"\n📊 Total compound matches: {total_matches}")
    return updated_documents


def save_updated_documents(documents: List[FAIRFluidsDocument], 
                          output_dir: str,
                          original_folder: str):
    """
    Save updated documents to output directory.
    
    Args:
        documents: List of updated FAIRFluidsDocument objects
        output_dir: Output directory path
        original_folder: Original folder name for reference
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"\n💾 Saving updated documents to: {output_dir}")
    
    # Get original filenames from the original folder
    original_path = Path(original_folder)
    original_files = list(original_path.glob("*.json"))
    
    for i, doc in enumerate(documents):
        if i < len(original_files):
            # Use original filename
            filename = original_files[i].name
        else:
            # Fallback to generic name
            filename = f"updated_document_{i+1}.json"
        
        output_file = output_path / filename
        
        try:
            with open(output_file, 'w') as f:
                f.write(doc.model_dump_json(indent=2))
            print(f"  ✅ Saved: {filename}")
        except Exception as e:
            print(f"  ❌ Error saving {filename}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Match compounds from compounds_density with FAIRFluids documents")
    parser.add_argument("--compounds-dir", default="/home/sga/Code/fairfluids_projects/compounds_density",
                       help="Path to compounds_density folder")
    parser.add_argument("--documents-dir", default="test_json_only",
                       help="Path to test_json_only folder")
    parser.add_argument("--output-dir", default="matched_documents",
                       help="Output directory for updated documents")
    
    args = parser.parse_args()
    
    print("🔬 FAIRFluids Compound Matcher")
    print("=" * 50)
    
    # Load compounds from compounds_density folder
    compounds = load_compounds_from_density_folder(args.compounds_dir)
    
    if not compounds:
        print("❌ No compounds loaded. Exiting.")
        return
    
    # Load FAIRFluids documents from test_json_only folder
    documents = load_fairfluids_documents(args.documents_dir)
    
    if not documents:
        print("❌ No documents loaded. Exiting.")
        return
    
    # Match compounds to documents
    updated_documents = match_compounds_to_documents(compounds, documents)
    
    # Save updated documents
    save_updated_documents(updated_documents, args.output_dir, args.documents_dir)
    
    print("\n✅ Compound matching completed!")
    print(f"📁 Updated documents saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
