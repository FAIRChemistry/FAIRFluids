# ThermoML Tools

This folder contains tools for working with ThermoML XML files and converting them to Python models.

## Contents

- **`thermo.py`** - Generated Python Pydantic models from the ThermoML.md specification
- **`thermoml_mapper.py`** - Main utility for parsing ThermoML XML files and converting them to Python models
- **`example_usage.py`** - Example script demonstrating how to use the mapper
- **`README_thermoml_mapper.md`** - Comprehensive documentation for the mapper

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install pydantic-xml lxml
   ```

2. **Test the mapper:**
   ```bash
   cd thermoml
   python thermoml_mapper.py summary ../fairfluids/data/thermoml_xml/spera_et_al_fpe_592_2025_114324.xml
   ```

3. **Run the example:**
   ```bash
   python example_usage.py
   ```

## Usage Examples

### Command Line
```bash
# Get summary
python thermoml_mapper.py summary <xml_file>

# Validate XML
python thermoml_mapper.py validate_xml <xml_file>

# Convert to JSON
python thermoml_mapper.py convert_to_json <xml_file> [output_file]
```

### Python
```python
from thermoml_mapper import ThermoMLMapper

mapper = ThermoMLMapper()
data_report = mapper.parse_xml_file("your_file.xml")

# Access data
for compound in data_report.compound:
    print(f"Compound: {compound.s_common_name}")
```

## Documentation

See `README_thermoml_mapper.md` for detailed usage instructions and examples.

