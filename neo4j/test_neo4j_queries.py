#!/usr/bin/env python3
"""
Test script to demonstrate Neo4j query structure for FAIRFluids knowledge graph.
This simulates the queries without requiring a running Neo4j instance.
"""

import json
from pathlib import Path
from collections import defaultdict

def load_sample_data():
    """Load sample data to demonstrate query structure."""
    sample_data = {
        "fluids": [
            {
                "name": "CHOLINE CHLORIDE ETHYLENE GLYCOL",
                "compounds": ["CHOLINE CHLORIDE", "ETHYLENE GLYCOL"],
                "measurements": [
                    {"parameterID": "temperature", "value": 298.15},
                    {"parameterID": "mole_fraction_1", "value": 0.333},
                    {"parameterID": "mole_fraction_2", "value": 0.667},
                    {"propertyID": "viscosity", "value": 50.4466},
                    {"propertyID": "density", "value": 1.0999}
                ]
            },
            {
                "name": "CHOLINE CHLORIDE glycerol",
                "compounds": ["CHOLINE CHLORIDE", "glycerol"],
                "measurements": [
                    {"parameterID": "temperature", "value": 303.15},
                    {"parameterID": "mole_fraction_1", "value": 0.5},
                    {"parameterID": "mole_fraction_2", "value": 0.5},
                    {"propertyID": "viscosity", "value": 45.2},
                    {"propertyID": "density", "value": 1.085}
                ]
            }
        ]
    }
    return sample_data

def simulate_cypher_query_1(data):
    """Simulate: Find fluids with compound X and molar fraction Y"""
    print("🔍 Query 1: Find fluids with CHOLINE CHLORIDE and mole fraction > 0.5")
    print("="*60)
    
    results = []
    for fluid in data["fluids"]:
        if "CHOLINE CHLORIDE" in fluid["compounds"]:
            for measurement in fluid["measurements"]:
                if "mole_fraction" in measurement.get("parameterID", "") and measurement["value"] > 0.5:
                    results.append({
                        "fluid_name": fluid["name"],
                        "compound": "CHOLINE CHLORIDE",
                        "mole_fraction": measurement["value"]
                    })
    
    for result in results:
        print(f"   {result['fluid_name']} -> {result['compound']} (mole fraction: {result['mole_fraction']:.3f})")
    
    return results

def simulate_cypher_query_2(data):
    """Simulate: Count datapoints for temperature in viscosity"""
    print("\n🔍 Query 2: Count datapoints for temperature in viscosity")
    print("="*60)
    
    results = []
    for fluid in data["fluids"]:
        temp_points = sum(1 for m in fluid["measurements"] if m.get("parameterID") == "temperature")
        visc_points = sum(1 for m in fluid["measurements"] if m.get("propertyID") == "viscosity")
        
        if temp_points > 0 or visc_points > 0:
            results.append({
                "fluid_name": fluid["name"],
                "temp_points": temp_points,
                "visc_points": visc_points
            })
    
    for result in results:
        print(f"   {result['fluid_name']}: {result['temp_points']} temp points, {result['visc_points']} viscosity points")
    
    return results

def simulate_cypher_query_3(data):
    """Simulate: Complex analysis - Temperature vs Viscosity for specific compound"""
    print("\n🔍 Query 3: Temperature vs Viscosity for CHOLINE CHLORIDE")
    print("="*60)
    
    results = []
    for fluid in data["fluids"]:
        if "CHOLINE CHLORIDE" in fluid["compounds"]:
            temp_value = None
            visc_value = None
            
            for measurement in fluid["measurements"]:
                if measurement.get("parameterID") == "temperature":
                    temp_value = measurement["value"]
                elif measurement.get("propertyID") == "viscosity":
                    visc_value = measurement["value"]
            
            if temp_value is not None and visc_value is not None:
                results.append({
                    "fluid_name": fluid["name"],
                    "compound": "CHOLINE CHLORIDE",
                    "temperature": temp_value,
                    "viscosity": visc_value
                })
    
    for result in results:
        print(f"   {result['fluid_name']}: T={result['temperature']}K, η={result['viscosity']}cP")
    
    return results

def simulate_cypher_query_4(data):
    """Simulate: Statistical analysis - Average viscosity by temperature range"""
    print("\n🔍 Query 4: Average viscosity by temperature range")
    print("="*60)
    
    temp_ranges = defaultdict(list)
    
    for fluid in data["fluids"]:
        temp_value = None
        visc_value = None
        
        for measurement in fluid["measurements"]:
            if measurement.get("parameterID") == "temperature":
                temp_value = measurement["value"]
            elif measurement.get("propertyID") == "viscosity":
                visc_value = measurement["value"]
        
        if temp_value is not None and visc_value is not None:
            if temp_value < 300:
                temp_ranges["Low (<300K)"].append(visc_value)
            elif temp_value < 310:
                temp_ranges["Medium (300-310K)"].append(visc_value)
            else:
                temp_ranges["High (>310K)"].append(visc_value)
    
    for temp_range, viscosities in temp_ranges.items():
        avg_viscosity = sum(viscosities) / len(viscosities)
        print(f"   {temp_range}: avg viscosity = {avg_viscosity:.2f}cP ({len(viscosities)} data points)")
    
    return temp_ranges

def show_cypher_equivalents():
    """Show the equivalent Cypher queries."""
    print("\n💡 Equivalent Cypher Queries:")
    print("="*60)
    
    queries = {
        "Query 1": """
MATCH (f:Fluid)-[:HAS_COMPOUND]->(c:Compound)
MATCH (f)-[:HAS_MEASUREMENT]->(m:Measurement)
WHERE c.commonName CONTAINS 'CHOLINE CHLORIDE' 
AND m.parameterID CONTAINS 'mole_fraction' 
AND m.value > 0.5
RETURN f.name, c.commonName, m.value;
        """,
        
        "Query 2": """
MATCH (f:Fluid)-[:HAS_MEASUREMENT]->(temp:Measurement)
MATCH (f)-[:HAS_MEASUREMENT]->(visc:Measurement)
WHERE temp.parameterID = 'temperature' AND visc.propertyID = 'viscosity'
RETURN f.name, count(temp) as temp_points, count(visc) as visc_points;
        """,
        
        "Query 3": """
MATCH (f:Fluid)-[:HAS_COMPOUND]->(c:Compound)
MATCH (f)-[:HAS_MEASUREMENT]->(temp:Measurement)
MATCH (f)-[:HAS_MEASUREMENT]->(visc:Measurement)
WHERE c.commonName CONTAINS 'CHOLINE CHLORIDE'
AND temp.parameterID = 'temperature' 
AND visc.propertyID = 'viscosity'
RETURN f.name as fluid_name, 
       c.commonName as compound,
       temp.value as temperature,
       visc.value as viscosity
ORDER BY temperature;
        """,
        
        "Query 4": """
MATCH (f:Fluid)-[:HAS_MEASUREMENT]->(temp:Measurement)
MATCH (f)-[:HAS_MEASUREMENT]->(visc:Measurement)
WHERE temp.parameterID = 'temperature' AND visc.propertyID = 'viscosity'
WITH f, temp.value as temp_val, visc.value as visc_val
RETURN 
  CASE 
    WHEN temp_val < 300 THEN 'Low (<300K)'
    WHEN temp_val < 310 THEN 'Medium (300-310K)'
    ELSE 'High (>310K)'
  END as temperature_range,
  avg(visc_val) as avg_viscosity,
  count(*) as data_points;
        """
    }
    
    for query_name, cypher_query in queries.items():
        print(f"\n{query_name}:")
        print(cypher_query.strip())

def main():
    print("🧠 FAIRFluids Neo4j Query Simulation")
    print("="*50)
    print("This demonstrates the query structure without requiring Neo4j.")
    print("To run with real Neo4j, use: ./setup_neo4j.sh")
    print()
    
    # Load sample data
    data = load_sample_data()
    
    # Run simulated queries
    simulate_cypher_query_1(data)
    simulate_cypher_query_2(data)
    simulate_cypher_query_3(data)
    simulate_cypher_query_4(data)
    
    # Show Cypher equivalents
    show_cypher_equivalents()
    
    print("\n✅ Query simulation completed!")
    print("\n🚀 To run with real Neo4j:")
    print("   1. Start Docker")
    print("   2. Run: ./setup_neo4j.sh")
    print("   3. Run: python create_neo4j_graph.py --clear --queries")

if __name__ == "__main__":
    main()

