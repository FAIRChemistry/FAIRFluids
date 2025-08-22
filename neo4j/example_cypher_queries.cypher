// FAIRFluids Knowledge Graph - Example Cypher Queries
// ===================================================

// 1. Find all fluids with a specific compound
MATCH (f:Fluid)-[:HAS_COMPOUND]->(c:Compound)
WHERE c.commonName CONTAINS 'CHOLINE CHLORIDE'
RETURN f.name as fluid_name, c.commonName as compound
LIMIT 10;

// 2. Find fluids with specific molar fraction range
MATCH (f:Fluid)-[:HAS_MEASUREMENT]->(m:Measurement)
WHERE m.parameterID CONTAINS 'mole_fraction' AND m.value > 0.5
RETURN f.name as fluid_name, m.parameterID as parameter, m.value as value
LIMIT 10;

// 3. Count measurements per fluid
MATCH (f:Fluid)-[:HAS_MEASUREMENT]->(m:Measurement)
RETURN f.name as fluid_name, count(m) as measurement_count
ORDER BY measurement_count DESC
LIMIT 10;

// 4. Temperature vs Viscosity analysis
MATCH (f:Fluid)-[:HAS_MEASUREMENT]->(temp:Measurement)
MATCH (f)-[:HAS_MEASUREMENT]->(visc:Measurement)
WHERE temp.parameterID = 'temperature' AND visc.propertyID = 'viscosity'
RETURN f.name as fluid_name, temp.value as temperature, visc.value as viscosity
ORDER BY temperature
LIMIT 10;

// 5. Complex query: Find fluids with specific compound and temperature range
MATCH (f:Fluid)-[:HAS_COMPOUND]->(c:Compound)
MATCH (f)-[:HAS_MEASUREMENT]->(m:Measurement)
WHERE c.commonName CONTAINS 'CHOLINE CHLORIDE' 
AND m.parameterID = 'temperature' 
AND m.value >= 298 AND m.value <= 308
RETURN f.name as fluid_name, c.commonName as compound, m.value as temperature
ORDER BY temperature
LIMIT 10;

// 6. Find fluids with compound X and molar fraction Y (your specific query)
MATCH (f:Fluid)-[:HAS_COMPOUND]->(c:Compound)
MATCH (f)-[:HAS_MEASUREMENT]->(m:Measurement)
WHERE c.commonName CONTAINS 'CHOLINE CHLORIDE' 
AND m.parameterID CONTAINS 'mole_fraction' 
AND m.value > 0.5
RETURN f.name, c.commonName, m.value;

// 7. Count datapoints for temperature in viscosity
MATCH (f:Fluid)-[:HAS_MEASUREMENT]->(temp:Measurement)
MATCH (f)-[:HAS_MEASUREMENT]->(visc:Measurement)
WHERE temp.parameterID = 'temperature' AND visc.propertyID = 'viscosity'
RETURN f.name, count(temp) as temp_points, count(visc) as visc_points;

// 8. Find all compounds and their usage frequency
MATCH (c:Compound)<-[:HAS_COMPOUND]-(f:Fluid)
RETURN c.commonName as compound, count(f) as fluid_count
ORDER BY fluid_count DESC;

// 9. Find fluids with specific temperature range and count viscosity measurements
MATCH (f:Fluid)-[:HAS_MEASUREMENT]->(temp:Measurement)
MATCH (f)-[:HAS_MEASUREMENT]->(visc:Measurement)
WHERE temp.parameterID = 'temperature' 
AND temp.value BETWEEN 298 AND 308
AND visc.propertyID = 'viscosity'
RETURN f.name as fluid_name, 
       count(temp) as temperature_points,
       count(visc) as viscosity_points,
       avg(visc.value) as avg_viscosity;

// 10. Find all citations and their associated fluids
MATCH (f:Fluid)-[:CITED_IN]->(cit:Citation)
RETURN cit.doi as doi, count(f) as fluid_count
ORDER BY fluid_count DESC;

// 11. Complex analysis: Temperature vs Viscosity for specific compound
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

// 12. Find fluids with multiple compounds (3-component systems)
MATCH (f:Fluid)-[:HAS_COMPOUND]->(c:Compound)
WITH f, count(c) as compound_count
WHERE compound_count >= 3
RETURN f.name as fluid_name, compound_count
ORDER BY compound_count DESC;

// 13. Statistical analysis: Average viscosity by temperature range
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

// 14. Find correlations between mole fraction and viscosity
MATCH (f:Fluid)-[:HAS_MEASUREMENT]->(mf:Measurement)
MATCH (f)-[:HAS_MEASUREMENT]->(visc:Measurement)
WHERE mf.parameterID CONTAINS 'mole_fraction' 
AND visc.propertyID = 'viscosity'
RETURN f.name as fluid_name,
       mf.value as mole_fraction,
       visc.value as viscosity
ORDER BY mole_fraction;

// 15. Network analysis: Most connected compounds
MATCH (c:Compound)<-[:HAS_COMPOUND]-(f:Fluid)
WITH c, count(f) as fluid_count
ORDER BY fluid_count DESC
LIMIT 10
MATCH (c)<-[:HAS_COMPOUND]-(f:Fluid)
RETURN c.commonName as compound, 
       fluid_count,
       collect(f.name) as fluids;

