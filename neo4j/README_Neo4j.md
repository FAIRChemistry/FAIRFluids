# FAIRFluids Knowledge Graph with Neo4j

This setup allows you to query the FAIRFluids data using Neo4j's powerful graph database and Cypher query language.

## 🚀 Quick Start

### 1. Setup Neo4j (Docker)
```bash
./setup_neo4j.sh
```

This will:
- Start a Neo4j container with APOC plugins
- Set up authentication (neo4j/password)
- Make Neo4j available at http://localhost:7474

### 2. Import FAIRFluids Data
```bash
python create_neo4j_graph.py --clear --queries
```

This will:
- Clear existing data
- Import all JSON files from `test_json_only/`
- Run example queries to demonstrate functionality

## 🔍 Example Queries

### Your Specific Query
Find fluids with compound X and molar fraction Y that have Z datapoints for temperature in viscosity:

```cypher
// Find fluids with CHOLINE CHLORIDE and mole fraction > 0.5
MATCH (f:Fluid)-[:HAS_COMPOUND]->(c:Compound)
MATCH (f)-[:HAS_MEASUREMENT]->(m:Measurement)
WHERE c.commonName CONTAINS 'CHOLINE CHLORIDE' 
AND m.parameterID CONTAINS 'mole_fraction' 
AND m.value > 0.5
RETURN f.name, c.commonName, m.value;
```

### Count Temperature vs Viscosity Datapoints
```cypher
// Count datapoints for temperature in viscosity
MATCH (f:Fluid)-[:HAS_MEASUREMENT]->(temp:Measurement)
MATCH (f)-[:HAS_MEASUREMENT]->(visc:Measurement)
WHERE temp.parameterID = 'temperature' AND visc.propertyID = 'viscosity'
RETURN f.name, count(temp) as temp_points, count(visc) as visc_points;
```

### Complex Analysis
```cypher
// Find fluids with specific compound and temperature range
MATCH (f:Fluid)-[:HAS_COMPOUND]->(c:Compound)
MATCH (f)-[:HAS_MEASUREMENT]->(m:Measurement)
WHERE c.commonName CONTAINS 'CHOLINE CHLORIDE'
AND m.parameterID = 'temperature'
AND m.value BETWEEN 298 AND 308
RETURN f.name, c.commonName, m.value
ORDER BY m.value;
```

## 📊 Graph Schema

### Nodes
- **Fluid**: Individual fluid systems
- **Compound**: Chemical compounds (CHOLINE CHLORIDE, etc.)
- **Property**: Measured properties (viscosity, density)
- **Parameter**: Experimental parameters (temperature, mole fraction)
- **Measurement**: Actual data values
- **Unit**: Units of measurement
- **Citation**: Publication references

### Relationships
- `(:Fluid)-[:HAS_COMPOUND]->(:Compound)`
- `(:Fluid)-[:HAS_PROPERTY]->(:Property)`
- `(:Fluid)-[:HAS_PARAMETER]->(:Parameter)`
- `(:Fluid)-[:HAS_MEASUREMENT]->(:Measurement)`
- `(:Parameter)-[:ASSOCIATED_WITH]->(:Compound)`
- `(:Property)-[:HAS_UNIT]->(:Unit)`
- `(:Parameter)-[:HAS_UNIT]->(:Unit)`
- `(:Fluid)-[:CITED_IN]->(:Citation)`

## 🎯 Advanced Queries

### Statistical Analysis
```cypher
// Average viscosity by temperature range
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
```

### Network Analysis
```cypher
// Most connected compounds
MATCH (c:Compound)<-[:HAS_COMPOUND]-(f:Fluid)
WITH c, count(f) as fluid_count
ORDER BY fluid_count DESC
LIMIT 10
MATCH (c)<-[:HAS_COMPOUND]-(f:Fluid)
RETURN c.commonName as compound, 
       fluid_count,
       collect(f.name) as fluids;
```

### Correlation Analysis
```cypher
// Temperature vs Viscosity for specific compound
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
```

## 🛠️ Usage

### Neo4j Browser
1. Open http://localhost:7474
2. Login with neo4j/password
3. Copy and paste queries from `example_cypher_queries.cypher`

### Python Script
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

with driver.session() as session:
    result = session.run("""
        MATCH (f:Fluid)-[:HAS_COMPOUND]->(c:Compound)
        WHERE c.commonName CONTAINS 'CHOLINE CHLORIDE'
        RETURN f.name, c.commonName
        LIMIT 10
    """)
    
    for record in result:
        print(f"{record['f.name']} -> {record['c.commonName']}")
```

## 📁 Files

- `create_neo4j_graph.py` - Main import script
- `setup_neo4j.sh` - Docker setup script
- `example_cypher_queries.cypher` - Example queries
- `README_Neo4j.md` - This documentation

## 🎉 Benefits

1. **Complex Queries**: Easily find fluids with specific compounds and conditions
2. **Data Relationships**: Explore connections between compounds, properties, and measurements
3. **Statistical Analysis**: Perform aggregations and correlations
4. **Network Analysis**: Understand compound usage patterns
5. **Interactive Exploration**: Use Neo4j Browser for visual exploration

## 🔧 Troubleshooting

### Neo4j Connection Issues
```bash
# Check if Neo4j is running
docker ps | grep neo4j

# View logs
docker logs fairfluids-neo4j

# Restart container
docker restart fairfluids-neo4j
```

### Import Issues
```bash
# Clear database and reimport
python create_neo4j_graph.py --clear --queries
```

