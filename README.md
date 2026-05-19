# FAIRFluids

A comprehensive framework for creating FAIR (Findable, Accessible, Interoperable, and Reusable) fluid data documents with standardized metadata and experimental data representation.

## Overview

FAIRFluids is a Python-based framework designed to standardize the representation and sharing of fluid property data. It provides a structured approach to document experimental and computational fluid data with comprehensive metadata, ensuring data is FAIR-compliant and easily accessible for research and analysis.

## Features

- **Structured Data Model**: Comprehensive schema for fluid properties, compounds, and experimental parameters
- **Multiple Data Sources**: Support for CSV files, CML (Chemical Markup Language) XML, and ThermoML formats
- **Standardized Metadata**: Includes citation information, compound identifiers (PubChem, InChI, IUPAC names), and experimental methods
- **Flexible Property Support**: Handles various fluid properties including viscosity, density, thermal conductivity, and more
- **Uncertainty Tracking**: Built-in support for measurement uncertainties and error margins
- **Machine-Readable**: JSON-based output format for easy integration with analysis tools

## Project Structure

```
FAIRFluids/
├── fairfluids/          # Main package directory
│   ├── __init__.py      # Package initialization
│   ├── cli.py          # Command-line interface
│   ├── core/           # Core functionality
│   │   ├── __init__.py
│   │   ├── extended_models.py
│   │   ├── fluid_io.py      # CSV data import utilities
│   │   ├── functionalities.py
│   │   ├── lib.py           # Main data models
│   │   └── visualization.py
│   └── data/           # Example data files
│       ├── cml_xml/    # Chemical Markup Language files
│       │   ├── gygli/  # Gygli et al. dataset
│       │   └── xu/     # Xu et al. dataset
│       ├── csvs/       # CSV data files
│       ├── pdf/        # Reference documents
│       └── thermoml_xml/ # ThermoML format files
├── baml_client/        # BAML (BoundaryML) client libraries
├── baml_src/          # BAML schema definitions
├── jinja/             # Template generation
├── specifications/     # Model specifications
├── test/              # Test files and examples
├── schemes/           # Documentation and schemas
├── pyproject.toml     # Modern Python packaging
├── setup.py           # Traditional setup script
├── environment.yml    # Conda environment
└── requirements.txt   # Pip dependencies
```

## Installation

### Using Conda (Recommended)

```bash
# Clone the repository
git clone https://github.com/FAIRChemistry/FAIRFluids.git
cd FAIRFluids

# Create and activate conda environment
conda env create -f environment.yml
conda activate fairfluids
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/FAIRChemistry/FAIRFluids.git
cd FAIRFluids

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install core dependencies and the package
pip install -r requirements.txt
pip install -e .

# Or install everything (workflows, Neo4j, Bayesian inference)
pip install -e ".[all]"
```

### Development Setup

For development work, you can install additional development dependencies:

```bash
# Using conda
conda env create -f environment.yml

# Using pip (after conda env create)
pip install -r requirements-conda.txt

# Optional extras: viz, neo4j, workflows, bayesian, dev, all
pip install -e ".[bayesian]"
```

### Testing the Installation

After installation, you can test that everything works:

```bash
# Test the CLI
fairfluids --help

# Test Python imports
python -c "import fairfluids; print('FAIRFluids imported successfully!')"

# Run comprehensive tests
python test_installation.py
```

## Quick Start

### Creating a FAIRFluids Document

```python
import fairfluids
from fairfluids import FAIRFluidsDocument, Version, Citation

# Create a new document
doc = FAIRFluidsDocument(
    version=Version(versionMajor=1, versionMinor=0)
)

# Add citation information
doc.citation = Citation(litType="journal")
doc.citation.add_to_author(given_name="John", family_name="Doe")

# Add compound information
doc.add_to_compound(
    compoundID="1",
    pubChemID=962,
    commonName="Water",
    name_IUPAC="oxidane",
    standard_InChI="InChI=1S/H2O/h1H2",
    standard_InChI_key="XLYOFNOQVPJJNP-UHFFFAOYSA-N"
)

# Save to JSON
with open('fairfluids_model.json', 'w') as f:
    f.write(doc.model_dump_json(indent=2))
```

### Loading Data from CSV

```python
from fairfluids import FluidIO

# Load fluid data from CSV
fluid = FluidIO()
fluid.data_from_csv('path/to/your/data.csv')

# Add to document
doc.fluid.append(fluid)
```

### Parsing CML Files

```python
from fairfluids import FAIRFluidsCMLParser

# Parse CML XML file
parser = FAIRFluidsCMLParser("path/to/file.xml", document=doc)
doc = parser.parse()
```

### Using the Command Line Interface

FAIRFluids provides a CLI for common operations:

```bash
# Create a new document
fairfluids create --output document.json

# Load data from CSV
fairfluids csv data.csv --output document.json

# Parse CML file
fairfluids cml data.xml --output document.json

# Get help
fairfluids --help
```

## Data Model

The FAIRFluids framework is built around several key components:

### FAIRFluidsDocument
The root container that holds:
- **Version**: Document version information
- **Citation**: Publication and author metadata
- **Compound**: Chemical compound information with identifiers
- **Fluid**: Experimental data and measurements

### Compound
Represents chemical compounds with:
- PubChem ID
- IUPAC names
- InChI identifiers
- SELFIES molecular representations

### Fluid
Contains experimental data including:
- **Property**: Measured properties (viscosity, density, etc.)
- **Parameter**: Experimental conditions (temperature, pressure, composition)
- **Measurement**: Actual data values with uncertainties

### Supported Properties
- Density
- Viscosity
- Thermal conductivity
- Specific heat capacity
- Melting/boiling points
- Vapor pressure
- pH
- And more...

## Data Formats

### Input Formats
- **CSV**: Tabular data with standardized column headers
- **CML**: Chemical Markup Language XML files
- **ThermoML**: Thermodynamic data format

### Output Format
- **JSON**: Structured data with full metadata

## Example Data

The repository includes example datasets:
- **Gygli Dataset**: Ionic liquid mixtures and their properties
- **Xu Dataset**: Experimental and simulation data
- **Various CSV files**: Formatted experimental data

## Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]

## Citation

If you use FAIRFluids in your research, please cite:

[Add citation information here]

## Contact

For questions or support, please open an issue on GitHub or contact the development team.

## Acknowledgments

This project is part of the FAIRChemistry initiative, promoting Findable, Accessible, Interoperable, and Reusable chemical data standards.