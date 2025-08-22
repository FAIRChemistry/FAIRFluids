#!/usr/bin/env python3
"""
Script to import FAIRFluids knowledge graph into Neo4j for complex graph queries.
"""

import json
import os
import argparse
from pathlib import Path
from neo4j import GraphDatabase
import pandas as pd
from collections import defaultdict

class FAIRFluidsNeo4jImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        """Clear existing data."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("🗑️  Cleared existing database")
    
    def create_constraints(self):
        """Create constraints for better performance."""
        with self.driver.session() as session:
            # Create constraints
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (f:Fluid) REQUIRE f.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Compound) REQUIRE c.compoundID IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Property) REQUIRE p.propertyID IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:Unit) REQUIRE u.unitID IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (cit:Citation) REQUIRE cit.doi IS UNIQUE")
            print("🔒 Created database constraints")
    
    def import_from_json_files(self, json_directory):
        """Import data directly from JSON files."""
        json_files = list(Path(json_directory).glob("*.json"))
        print(f"📁 Processing {len(json_files)} JSON files...")
        
        # Track unique entities
        compounds_seen = set()
        units_seen = set()
        citations_seen = set()
        
        with self.driver.session() as session:
            for json_file in json_files:
                print(f"Processing: {json_file.name}")
                
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    # Extract fluid name from filename
                    fluid_name = json_file.stem.replace('_', ' ')
                    
                    # Create Fluid node
                    session.run("""
                        MERGE (f:Fluid {name: $name, source_file: $source_file})
                        """, name=fluid_name, source_file=json_file.name)
                    
                    # Process compounds
                    if 'compound' in data and data['compound']:
                        for compound in data['compound']:
                            compound_id = compound.get('compoundID', f"compound_{len(compounds_seen)}")
                            if compound_id not in compounds_seen:
                                compounds_seen.add(compound_id)
                                session.run("""
                                    MERGE (c:Compound {
                                        compoundID: $compoundID,
                                        commonName: $commonName,
                                        name_IUPAC: $name_IUPAC,
                                        pubChemID: $pubChemID
                                    })
                                    """, 
                                    compoundID=compound_id,
                                    commonName=compound.get('commonName') or '',
                                    name_IUPAC=compound.get('name_IUPAC') or '',
                                    pubChemID=compound.get('pubChemID') or 0)
                            
                            # Connect Fluid to Compound
                            session.run("""
                                MATCH (f:Fluid {name: $fluid_name})
                                MATCH (c:Compound {compoundID: $compound_id})
                                MERGE (f)-[:HAS_COMPOUND]->(c)
                                """, fluid_name=fluid_name, compound_id=compound_id)
                    
                    # Process citations
                    if 'citation' in data and data['citation']:
                        citation = data['citation']
                        doi = citation.get('doi')
                        if doi and doi not in citations_seen:
                            citations_seen.add(doi)
                            # Only create citation if required fields are not null
                            if doi:
                                session.run("""
                                    MERGE (cit:Citation {
                                        doi: $doi,
                                        title: $title,
                                        pub_name: $pub_name,
                                        publication_year: $publication_year,
                                        litType: $litType
                                    })
                                    """, 
                                    doi=doi,
                                    title=citation.get('title') or '',
                                    pub_name=citation.get('pub_name') or '',
                                    publication_year=citation.get('publication_year') or '',
                                    litType=citation.get('litType') or '')
                        
                        # Connect Fluid to Citation
                        if doi:
                            session.run("""
                                MATCH (f:Fluid {name: $fluid_name})
                                MATCH (cit:Citation {doi: $doi})
                                MERGE (f)-[:CITED_IN]->(cit)
                                """, fluid_name=fluid_name, doi=doi)
                    
                    # Process fluid properties and parameters
                    if 'fluid' in data and data['fluid']:
                        for fluid_data in data['fluid']:
                            # Properties
                            if 'property' in fluid_data:
                                for prop in fluid_data['property']:
                                    property_id = prop.get('propertyID', f"property_{len(compounds_seen)}")
                                    session.run("""
                                        MERGE (p:Property {
                                            propertyID: $propertyID,
                                            properties: $properties
                                        })
                                        """, 
                                        propertyID=property_id,
                                        properties=prop.get('properties'))
                                    
                                    # Connect Fluid to Property
                                    session.run("""
                                        MATCH (f:Fluid {name: $fluid_name})
                                        MATCH (p:Property {propertyID: $property_id})
                                        MERGE (f)-[:HAS_PROPERTY]->(p)
                                        """, fluid_name=fluid_name, property_id=property_id)
                                    
                                    # Units for properties
                                    if 'unit' in prop and prop['unit']:
                                        unit_id = prop['unit'].get('unitID')
                                        if unit_id and unit_id not in units_seen:
                                            units_seen.add(unit_id)
                                            session.run("""
                                                MERGE (u:Unit {
                                                    unitID: $unitID,
                                                    name: $name
                                                })
                                                """, 
                                                unitID=unit_id,
                                                name=prop['unit'].get('name'))
                                        
                                        # Connect Property to Unit
                                        if unit_id:
                                            session.run("""
                                                MATCH (p:Property {propertyID: $property_id})
                                                MATCH (u:Unit {unitID: $unit_id})
                                                MERGE (p)-[:HAS_UNIT]->(u)
                                                """, property_id=property_id, unit_id=unit_id)
                            
                            # Parameters
                            if 'parameter' in fluid_data:
                                for param in fluid_data['parameter']:
                                    parameter_id = param.get('parameterID', f"parameter_{len(compounds_seen)}")
                                    # Only create parameter if required fields are not null
                                    if parameter_id:
                                        session.run("""
                                            MERGE (param:Parameter {
                                                parameterID: $parameterID,
                                                parameter: $parameter,
                                                associated_compound: $associated_compound
                                            })
                                            """, 
                                            parameterID=parameter_id,
                                            parameter=param.get('parameter') or '',
                                            associated_compound=param.get('associated_compound') or '')
                                    
                                    # Connect Fluid to Parameter
                                    if parameter_id:
                                        session.run("""
                                            MATCH (f:Fluid {name: $fluid_name})
                                            MATCH (param:Parameter {parameterID: $parameter_id})
                                            MERGE (f)-[:HAS_PARAMETER]->(param)
                                            """, fluid_name=fluid_name, parameter_id=parameter_id)
                                    
                                    # Connect Parameter to associated Compound
                                    if param.get('associated_compound') and parameter_id:
                                        session.run("""
                                            MATCH (param:Parameter {parameterID: $parameter_id})
                                            MATCH (c:Compound {compoundID: $compound_id})
                                            MERGE (param)-[:ASSOCIATED_WITH]->(c)
                                            """, 
                                            parameter_id=parameter_id,
                                            compound_id=param['associated_compound'])
                                    
                                    # Units for parameters
                                    if 'unit' in param and param['unit']:
                                        unit_id = param['unit'].get('unitID')
                                        if unit_id and unit_id not in units_seen:
                                            units_seen.add(unit_id)
                                            session.run("""
                                                MERGE (u:Unit {
                                                    unitID: $unitID,
                                                    name: $name
                                                })
                                                """, 
                                                unitID=unit_id,
                                                name=param['unit'].get('name'))
                                        
                                        # Connect Parameter to Unit
                                        if unit_id:
                                            session.run("""
                                                MATCH (param:Parameter {parameterID: $parameter_id})
                                                MATCH (u:Unit {unitID: $unit_id})
                                                MERGE (param)-[:HAS_UNIT]->(u)
                                                """, parameter_id=parameter_id, unit_id=unit_id)
                            
                            # Measurements
                            if 'measurement' in fluid_data:
                                for i, measurement in enumerate(fluid_data['measurement']):
                                    measurement_id = measurement.get('measurement_id', f"measurement_{i}")
                                    
                                    # Create measurement node with property values
                                    for prop_val in measurement.get('propertyValue', []):
                                        prop_id = prop_val.get('propertyID')
                                        prop_value = prop_val.get('propValue')
                                        uncertainty = prop_val.get('uncertainty')
                                        
                                        if prop_id and prop_value is not None:
                                            session.run("""
                                                MERGE (m:Measurement {
                                                    measurement_id: $measurement_id,
                                                    propertyID: $property_id,
                                                    value: $value,
                                                    uncertainty: $uncertainty,
                                                    source_doi: $source_doi
                                                })
                                                """, 
                                                measurement_id=measurement_id,
                                                property_id=prop_id,
                                                value=prop_value,
                                                uncertainty=uncertainty or 0.0,
                                                source_doi=measurement.get('source_doi') or '')
                                            
                                            # Connect Fluid to Measurement
                                            session.run("""
                                                MATCH (f:Fluid {name: $fluid_name})
                                                MATCH (m:Measurement {measurement_id: $measurement_id, propertyID: $property_id})
                                                MERGE (f)-[:HAS_MEASUREMENT]->(m)
                                                """, fluid_name=fluid_name, measurement_id=measurement_id, property_id=prop_id)
                                    
                                    # Parameter values
                                    for param_val in measurement.get('parameterValue', []):
                                        param_id = param_val.get('parameterID')
                                        param_value = param_val.get('paramValue')
                                        uncertainty = param_val.get('uncertainty')
                                        
                                        if param_id and param_value is not None:
                                            session.run("""
                                                MERGE (m:Measurement {
                                                    measurement_id: $measurement_id,
                                                    parameterID: $parameter_id,
                                                    value: $value,
                                                    uncertainty: $uncertainty,
                                                    source_doi: $source_doi
                                                })
                                                """, 
                                                measurement_id=measurement_id,
                                                parameter_id=param_id,
                                                value=param_value,
                                                uncertainty=uncertainty or 0.0,
                                                source_doi=measurement.get('source_doi') or '')
                                            
                                            # Connect Fluid to Measurement
                                            session.run("""
                                                MATCH (f:Fluid {name: $fluid_name})
                                                MATCH (m:Measurement {measurement_id: $measurement_id, parameterID: $parameter_id})
                                                MERGE (f)-[:HAS_MEASUREMENT]->(m)
                                                """, fluid_name=fluid_name, measurement_id=measurement_id, parameter_id=param_id)
                
                except Exception as e:
                    print(f"Error processing {json_file}: {e}")
                    continue
        
        print("✅ Data import completed!")

def run_example_queries(driver):
    """Run example Cypher queries to demonstrate the power of Neo4j."""
    print("\n🔍 EXAMPLE CYPHER QUERIES")
    print("="*50)
    
    with driver.session() as session:
        # Query 1: Find all fluids with a specific compound
        print("\n1️⃣ Fluids containing 'CHOLINE CHLORIDE':")
        result = session.run("""
            MATCH (f:Fluid)-[:HAS_COMPOUND]->(c:Compound)
            WHERE c.commonName CONTAINS 'CHOLINE CHLORIDE'
            RETURN f.name as fluid_name, c.commonName as compound
            LIMIT 10
        """)
        for record in result:
            print(f"   {record['fluid_name']} -> {record['compound']}")
        
        # Query 2: Find fluids with specific molar fraction range
        print("\n2️⃣ Fluids with mole fraction > 0.5:")
        result = session.run("""
            MATCH (f:Fluid)-[:HAS_MEASUREMENT]->(m:Measurement)
            WHERE m.parameterID CONTAINS 'mole_fraction' AND m.value > 0.5
            RETURN f.name as fluid_name, m.parameterID as parameter, m.value as value
            LIMIT 10
        """)
        for record in result:
            print(f"   {record['fluid_name']}: {record['parameter']} = {record['value']}")
        
        # Query 3: Count measurements per fluid
        print("\n3️⃣ Number of measurements per fluid:")
        result = session.run("""
            MATCH (f:Fluid)-[:HAS_MEASUREMENT]->(m:Measurement)
            RETURN f.name as fluid_name, count(m) as measurement_count
            ORDER BY measurement_count DESC
            LIMIT 10
        """)
        for record in result:
            print(f"   {record['fluid_name']}: {record['measurement_count']} measurements")
        
        # Query 4: Temperature vs Viscosity analysis
        print("\n4️⃣ Temperature vs Viscosity data points:")
        result = session.run("""
            MATCH (f:Fluid)-[:HAS_MEASUREMENT]->(temp:Measurement)
            MATCH (f)-[:HAS_MEASUREMENT]->(visc:Measurement)
            WHERE temp.parameterID = 'temperature' AND visc.propertyID = 'viscosity'
            RETURN f.name as fluid_name, temp.value as temperature, visc.value as viscosity
            ORDER BY temperature
            LIMIT 10
        """)
        for record in result:
            print(f"   {record['fluid_name']}: T={record['temperature']}K, η={record['viscosity']}cP")
        
        # Query 5: Complex query: Find fluids with specific compound and temperature range
        print("\n5️⃣ Fluids with 'CHOLINE CHLORIDE' at temperatures 298-308K:")
        result = session.run("""
            MATCH (f:Fluid)-[:HAS_COMPOUND]->(c:Compound)
            MATCH (f)-[:HAS_MEASUREMENT]->(m:Measurement)
            WHERE c.commonName CONTAINS 'CHOLINE CHLORIDE' 
            AND m.parameterID = 'temperature' 
            AND m.value >= 298 AND m.value <= 308
            RETURN f.name as fluid_name, c.commonName as compound, m.value as temperature
            ORDER BY temperature
            LIMIT 10
        """)
        for record in result:
            print(f"   {record['fluid_name']}: {record['compound']} at {record['temperature']}K")

def main():
    parser = argparse.ArgumentParser(description="Import FAIRFluids data into Neo4j")
    parser.add_argument("--uri", default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--user", default="neo4j", help="Neo4j username")
    parser.add_argument("--password", default="password", help="Neo4j password")
    parser.add_argument("--json-dir", default="test_json_only", help="Directory with JSON files")
    parser.add_argument("--clear", action="store_true", help="Clear existing data")
    parser.add_argument("--queries", action="store_true", help="Run example queries")
    
    args = parser.parse_args()
    
    print("🗄️  FAIRFluids Neo4j Import")
    print("="*50)
    
    importer = FAIRFluidsNeo4jImporter(args.uri, args.user, args.password)
    
    try:
        if args.clear:
            importer.clear_database()
        
        importer.create_constraints()
        importer.import_from_json_files(args.json_dir)
        
        if args.queries:
            run_example_queries(importer.driver)
    
    finally:
        importer.close()
    
    print("\n✅ Neo4j import completed!")
    print("\n💡 Example Cypher queries you can now run:")
    print("""
    // Find fluids with compound X and molar fraction Y
    MATCH (f:Fluid)-[:HAS_COMPOUND]->(c:Compound)
    MATCH (f)-[:HAS_MEASUREMENT]->(m:Measurement)
    WHERE c.commonName CONTAINS 'CHOLINE CHLORIDE' 
    AND m.parameterID CONTAINS 'mole_fraction' 
    AND m.value > 0.5
    RETURN f.name, c.commonName, m.value
    
    // Count datapoints for temperature in viscosity
    MATCH (f:Fluid)-[:HAS_MEASUREMENT]->(temp:Measurement)
    MATCH (f)-[:HAS_MEASUREMENT]->(visc:Measurement)
    WHERE temp.parameterID = 'temperature' AND visc.propertyID = 'viscosity'
    RETURN f.name, count(temp) as temp_points, count(visc) as visc_points
    
    // Complex fluid analysis
    MATCH (f:Fluid)-[:HAS_COMPOUND]->(c:Compound)
    MATCH (f)-[:HAS_MEASUREMENT]->(m:Measurement)
    WHERE c.commonName CONTAINS 'CHOLINE CHLORIDE'
    AND m.parameterID = 'temperature'
    AND m.value BETWEEN 298 AND 308
    RETURN f.name, c.commonName, m.value
    ORDER BY m.value
    """)

if __name__ == "__main__":
    main()
