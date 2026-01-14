# ThermoML to FAIRFluids Mapping Layer

This directory contains a mapping layer that converts ThermoML XML data to FAIRFluids format. The mapping layer provides a clean interface for converting scientific data from the ThermoML standard to the FAIRFluids data model.

## Overview

The ThermoML mapping layer consists of several components:

- **ThermoMLMapper**: Main conversion class that handles the complete conversion process
- **conversion_utils.py**: Utility functions and mapping dictionaries for properties, parameters, methods, and literature types
- **test_conversion.py**: Test script demonstrating the conversion functionality

## Features

### Supported Conversions

1. **Document Structure**
   - Version information
   - Citation metadata
   - Compound definitions
   - Fluid data

2. **Compounds**
   - PubChem IDs
   - Common names and IUPAC names
   - InChI and InChI Key
   - Molecular formulas

3. **Citations**
   - Literature types (journal, book, report, etc.)
   - Author information
   - DOI, publication details
   - Title and abstract

4. **Properties**
   - Density, viscosity, thermal conductivity
   - Critical properties, phase behavior
   - Transport properties
   - Thermodynamic properties

5. **Parameters**
   - Temperature, pressure
   - Composition parameters (mole fraction, mass fraction, etc.)
   - Concentration parameters
   - Solvent/solute ratios

6. **Measurements**
   - Property values with uncertainties
   - Parameter values
   - Method information
   - Experimental conditions

## Usage

### Basic Usage

```python
from ThermoMLMapping import ThermoMLMapper

# Initialize the mapper
mapper = ThermoMLMapper()

# Convert a ThermoML XML file
fairfluids_doc = mapper.convert_file('path/to/thermoml_file.xml')

# Access the converted data
print(f"Number of compounds: {len(fairfluids_doc.compound)}")
print(f"Number of fluids: {len(fairfluids_doc.fluid)}")
```

### Running the Test Script

```bash
cd /home/sga/Code/FAIRFluids/ThermoMLMapping
python test_conversion.py
```

This will convert the spera_et_al_fpe_592_2025_114324.xml file and save the result to `converted_output.json`.

## Mapping Details

### Property Mapping

The mapper includes comprehensive property mappings from ThermoML property names to FAIRFluids Properties enum values:

- **Density**: `Mass density, kg/m3` → `DENSITY`
- **Viscosity**: `Dynamic viscosity, Pa*s` → `VISCOSITY`
- **Thermal Conductivity**: `Thermal conductivity, W/(m*K)` → `THERMAL_CONDUCTIVITY`
- **Critical Properties**: `Critical temperature, K` → `CRITICAL_TEMPERATURE`
- And many more...

### Parameter Mapping

Parameters are mapped from ThermoML constraint types to FAIRFluids Parameters enum values:

- **Temperature**: `Temperature, K` → `TEMPERATURE_K`
- **Pressure**: `Pressure, kPa` → `PRESSURE_KPA`
- **Composition**: `Mole fraction` → `MOLE_FRACTION`
- **Concentration**: `Molality, mol/kg` → `MOLALITY_MOLKG`

### Method Mapping

Experimental and computational methods are mapped to FAIRFluids Method enum values:

- **Experimental**: `measured` → `MEASURED`
- **Computational**: `calculated` → `CALCULATED`
- **Simulation**: `simulated` → `SIMULATED`
- **Literature**: `literature` → `LITERATURE`

## File Structure

```
ThermoMLMapping/
├── __init__.py              # Package initialization
├── thermoml_mapper.py       # Main mapper class
├── conversion_utils.py      # Utility functions and mappings
├── test_conversion.py       # Test script
└── README.md               # This file
```

## Dependencies

The mapping layer requires:

- Python 3.7+
- FAIRFluids core library (`fairfluids.core.lib`)
- Standard library modules: `xml.etree.ElementTree`, `json`, `pathlib`

## Error Handling

The mapper includes robust error handling:

- Missing XML elements are handled gracefully
- Invalid property/parameter names are logged but don't stop conversion
- Type conversion errors are caught and handled
- Unknown enum values are skipped with warnings

## Extending the Mapper

To add support for new properties or parameters:

1. Add mappings to the appropriate mapper class in `conversion_utils.py`
2. Update the enum mappings if new values are needed
3. Test with sample data

## Example Output

The converted FAIRFluids document includes:

- **Version**: Major and minor version numbers
- **Citation**: Complete bibliographic information
- **Compounds**: Chemical compound metadata
- **Fluids**: Experimental data with properties, parameters, and measurements

The output can be serialized to JSON, XML, or used directly in Python applications.

## Notes

- The mapper preserves uncertainty information where available
- Unit definitions are created automatically from property names
- Compound IDs are generated based on ThermoML organization numbers
- The conversion maintains the hierarchical structure of the original data
