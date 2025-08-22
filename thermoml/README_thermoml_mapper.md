# ThermoML XML to Python Model Mapper

This utility provides a comprehensive solution for parsing ThermoML XML files and converting them to Python models using the generated `thermo.py` classes.

## Overview

The ThermoML mapper bridges the gap between ThermoML XML files and the Python Pydantic models generated from the `ThermoML.md` specification. It handles:

- XML parsing with namespace management
- Data validation against the generated models
- Conversion to JSON format
- Programmatic access to all ThermoML data structures
- Error handling and logging

## Files

- **`thermoml_mapper.py`** - Main mapper class and utilities
- **`example_usage.py`** - Example script demonstrating usage
- **`thermo.py`** - Generated Python models (from ThermoML.md)
- **`README_thermoml_mapper.md`** - This documentation

## Installation

1. Ensure you have the required dependencies:
   ```bash
   pip install pydantic-xml lxml
   ```

2. Make sure `thermo.py` is in the same directory as the mapper

## Usage

### Command Line Interface

The mapper provides several command-line utilities:

#### 1. Parse XML and Show Summary
```bash
python thermoml_mapper.py summary <xml_file_path>
```

Example:
```bash
python thermoml_mapper.py summary fairfluids/data/thermoml_xml/spera_et_al_fpe_592_2025_114324.xml
```

#### 2. Validate XML File
```bash
python thermoml_mapper.py validate_xml <xml_file_path>
```

Example:
```bash
python thermoml_mapper.py validate_xml fairfluids/data/thermoml_xml/spera_et_al_fpe_592_2025_114324.xml
```

#### 3. Convert XML to JSON
```bash
python thermoml_mapper.py convert_to_json <xml_file_path> [output_file]
```

Example:
```bash
# Convert to JSON and print to console
python thermoml_mapper.py convert_to_json fairfluids/data/thermoml_xml/spera_et_al_fpe_592_2025_114324.xml

# Convert to JSON and save to file
python thermoml_mapper.py convert_to_json fairfluids/data/thermoml_xml/spera_et_al_fpe_592_2025_114324.xml output.json
```

#### 4. Parse XML and Show Basic Info
```bash
python thermoml_mapper.py parse_xml <xml_file_path>
```

Example:
```bash
python thermoml_mapper.py parse_xml fairfluids/data/thermoml_xml/spera_et_al_fpe_592_2025_114324.xml
```

### Programmatic Usage

#### Basic Usage

```python
from thermoml_mapper import ThermoMLMapper

# Initialize mapper
mapper = ThermoMLMapper()

# Parse XML file
data_report = mapper.parse_xml_file("path/to/your/file.xml")

# Access data
print(f"Found {len(data_report.compound)} compounds")
print(f"Title: {data_report.citation.s_title}")
```

#### Get File Summary

```python
summary = mapper.get_summary("path/to/your/file.xml")
print(f"Version: {summary['version']}")
print(f"Compounds: {summary['compounds']}")
print(f"Title: {summary['citation']['title']}")
```

#### Validate File

```python
is_valid = mapper.validate_xml_file("path/to/your/file.xml")
if is_valid:
    print("File is valid!")
else:
    print("File has validation errors")
```

#### Convert to JSON

```python
# Convert to JSON string
json_data = mapper.convert_to_json("path/to/your/file.xml")

# Convert and save to file
mapper.convert_to_json("path/to/your/file.xml", "output.json")
```

## Data Structure Access

Once you have a `DataReport` object, you can access all the data programmatically:

### Compounds
```python
for compound in data_report.compound:
    print(f"PubChem ID: {compound.n_pub_chem_id}")
    print(f"Common Names: {compound.s_common_name}")
    print(f"Formula: {compound.s_formula_molec}")
    print(f"IUPAC Name: {compound.s_iupac_name}")
    print(f"SMILES: {compound.s_smiles}")
    print(f"Standard InChI: {compound.s_standard_in_ch_i}")
    print(f"Standard InChI Key: {compound.s_standard_in_ch_i_key}")
```

### Citation Information
```python
if data_report.citation:
    citation = data_report.citation
    print(f"Title: {citation.s_title}")
    print(f"Authors: {citation.s_author}")
    print(f"Publication: {citation.s_pub_name}")
    print(f"Year: {citation.yr_pub_yr}")
    print(f"DOI: {citation.s_doi}")
    print(f"Abstract: {citation.s_abstract}")
    print(f"Keywords: {citation.s_keyword}")
```

### Pure/Mixture Data
```python
for data_set in data_report.pure_or_mixture_data:
    print(f"Data Set Number: {data_set.n_pure_or_mixture_data_number}")
    print(f"Compiler: {data_set.s_compiler}")
    print(f"Contributor: {data_set.s_contributor}")
    print(f"Date Added: {data_set.date_date_added}")
    print(f"Purpose: {data_set.e_exp_purpose}")
```

### Reaction Data
```python
for reaction in data_report.reaction_data:
    print(f"Reaction Number: {reaction.n_reaction_data_number}")
    print(f"Reaction Type: {reaction.e_reaction_type}")
    print(f"Reaction Formalism: {reaction.e_reaction_formalism}")
```

## Supported ThermoML Elements

The mapper supports all major ThermoML elements including:

- **Core Elements**: DataReport, Version, Citation
- **Compound Information**: Compound, RegNum, SOrgID, Biomaterial, Ion, Polymer
- **Data Sets**: PureOrMixtureData, ReactionData
- **Properties**: Property, PropertyValue, PropertyMethodID, PropertyGroup
- **Constraints & Variables**: Constraint, Variable, ConstraintID, VariableID
- **Phases**: PhaseID, PropPhaseID, RefPhaseID, VarPhaseID
- **Uncertainty**: CombinedUncertainty, PropUncertainty, VarUncertainty
- **Equations**: Equation, EqProperty, EqConstraint, EqVariable, EqParameter, EqConstant
- **Evaluation**: CriticalEvaluation, Prediction, SingleProp, MultiProp
- **References**: Book, Journal, Thesis, TRCRefID

## Error Handling

The mapper includes comprehensive error handling:

- **XML Parsing Errors**: Handles malformed XML gracefully
- **Validation Errors**: Reports validation issues with detailed messages
- **Missing Data**: Gracefully handles missing optional fields
- **Logging**: Provides detailed logging for debugging

## Example Output

### Summary Output
```json
{
  "file_path": "example.xml",
  "version": "2.0",
  "citation": {
    "title": "Example Title",
    "authors": ["Author 1", "Author 2"],
    "publication": "Journal Name",
    "year": "2025",
    "doi": "10.1234/example.123"
  },
  "compounds": 5,
  "pure_mixture_data_sets": 25,
  "reaction_data_sets": 0,
  "compound_details": [...]
}
```

### Parsed Data Structure
The parsed data maintains the full hierarchical structure of the original ThermoML XML, with all data accessible through Python object attributes and methods.

## Limitations

- **Large Files**: Very large XML files (>100MB) may require significant memory
- **Complex Relationships**: Some complex nested relationships may need manual handling
- **Custom Extensions**: Non-standard ThermoML extensions may not be fully supported

## Troubleshooting

### Common Issues

1. **Import Error**: Ensure `thermo.py` is in the same directory
2. **XML Namespace Issues**: The mapper automatically handles ThermoML namespaces
3. **Memory Issues**: For very large files, consider processing in chunks
4. **Validation Errors**: Check the XML structure against the ThermoML specification

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

To extend the mapper:

1. Add new model creation methods in the `ThermoMLMapper` class
2. Update the import statements to include new models
3. Add corresponding test cases
4. Update this documentation

## License

This utility is part of the FAIRFluids project and follows the same licensing terms.
