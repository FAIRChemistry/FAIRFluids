# FAIRFluids

A Python framework for creating **FAIR** (Findable, Accessible, Interoperable, Reusable) fluid property documents with standardized metadata and experimental data representation.

Part of the [FAIRChemistry](https://github.com/FAIRChemistry) initiative.

## Overview

FAIRFluids standardizes how experimental and literature fluid data are represented, converted, and shared. It provides:

- A **Pydantic-based data model** for compounds, samples, properties, parameters, and measurements
- **I/O pipelines** for CSV, CML XML, and ThermoML
- **Analysis and visualization** helpers (Arrhenius/VFT fits, plots, DataFrames)
- Optional **Bayesian inference** workflows (NumPyro / JAX / ArviZ)

**Requirements:** Python ≥ 3.12 (reference environment: **3.13** via `environment.yml`). The `bayesian` / `all` extras require Python ≥ 3.12 because of the ArviZ stack.

## Features

- Structured schema for fluids, compounds, properties, parameters, and uncertainties
- Import from **CSV**, **CML**, and **ThermoML**; export to **JSON** and ThermoML
- Bidirectional ThermoML conversion (`fairfluids.io.thermoml_to_fairfluids`, `fairfluids.io.fairfluids_to_thermoml`)
- PubChem enrichment for compound metadata
- Plotting and DataFrame extraction for workflow notebooks
- Neo4j graph export (`neo4j/`) for querying document collections
- CLI for common create / CSV / CML operations

## Project structure

```
FAIRFluids/
├── fairfluids/                 # Main package
│   ├── core/                   # Data models (lib.py), analysis helpers, plot utils
│   ├── io/                     # CSV/JSON I/O, CML, PubChem, ThermoML converters
│   ├── operations/             # Compound/sample operations
│   ├── visualization/          # Plotting and DataFrame APIs
│   ├── analysis/               # Fits, activation energy, Bayesian hooks
│   ├── inspection/             # Document inspection, CST export
│   └── data/                   # Example CSV, CML, ThermoML files
├── docs/                       # Migration guide, API inventory, model layers
├── specifications/             # Model and ThermoML specifications
├── neo4j/                      # Neo4j import and query scripts
├── thin_layer/                 # Lightweight views / Arrhenius helpers
├── test/                       # Pytest suite
├── environment.yml             # Conda environment (Python 3.13, self-contained)
├── requirements.txt            # Core pip deps (see pyproject.toml extras)
├── requirements-conda.txt        # Pip-only add-ons for custom minimal conda envs
└── pyproject.toml              # Package metadata and optional extras
```

See [docs/MIGRATION.md](docs/MIGRATION.md) if you are updating code from an older package layout.

## Installation

`pyproject.toml` is the single source of truth for dependencies and optional extras.

### Conda (recommended)

```bash
git clone https://github.com/FAIRChemistry/FAIRFluids.git
cd FAIRFluids

conda env create -f environment.yml
conda activate fairfluids
```

`environment.yml` is self-contained: core packages, notebooks, Neo4j, Bayesian stack, test tools, and an editable install of FAIRFluids.

### pip

```bash
git clone https://github.com/FAIRChemistry/FAIRFluids.git
cd FAIRFluids

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -e ".[all]"
```

For a minimal install (library + CLI only):

```bash
pip install -e .
```

### uv

```bash
git clone https://github.com/FAIRChemistry/FAIRFluids.git
cd FAIRFluids

uv sync --extra all
```

Run commands without activating the virtual environment:

```bash
uv run fairfluids --help
uv run pytest test/
```

### Optional dependency groups

Install only what you need via [optional dependencies](pyproject.toml):

| Extra | Purpose |
|-------|---------|
| `viz` | Matplotlib, SciPy, Seaborn |
| `neo4j` | Neo4j Python driver |
| `workflows` | Notebooks (ipykernel, openpyxl, plotly, flask, pint, …) |
| `bayesian` | NumPyro, JAX, ArviZ (+ arviz-plots) |
| `dev` / `test` | pytest, pytest-asyncio, pytest-cov |
| `all` | All of the above |

```bash
pip install -e ".[viz]"
pip install -e ".[bayesian]"
pip install -e ".[all]"

uv sync --extra workflows --extra bayesian
```

`requirements.txt` lists core runtime dependencies only. Prefer the extras above instead of maintaining a separate full requirements file.

For a **custom minimal conda env** (without the pip section in `environment.yml`), use:

```bash
pip install -r requirements-conda.txt
```

### Verify installation

```bash
fairfluids --help
python -c "import fairfluids; print(fairfluids.__version__)"
python test/test_installation.py
python test/test_conda_env.py
pytest test/
```

## Quick start

### Create a document

```python
from fairfluids import FAIRFluidsDocument, Version, Citation

doc = FAIRFluidsDocument(version=Version(versionMajor=1, versionMinor=0))
doc.citation = Citation(litType="journal")
doc.citation.add_to_author(given_name="Jane", family_name="Doe")

doc.add_to_compound(
    compoundID="1",
    pubChemID=962,
    commonName="Water",
    name_IUPAC="oxidane",
)

doc.save_to_json("fairfluids_model.json")
```

### Load CSV data

```python
from fairfluids import FluidIO, FAIRFluidsDocument, Version

doc = FAIRFluidsDocument(version=Version(versionMajor=1, versionMinor=0))
fluid = FluidIO()
fluid.data_from_csv("fairfluids/data/csvs/exp_glycerol.csv")
doc.fluid.append(fluid)
```

### Parse CML

```python
from fairfluids import FAIRFluidsDocument, Version, FAIRFluidsCMLParser

doc = FAIRFluidsDocument(version=Version(versionMajor=1, versionMinor=0))
parser = FAIRFluidsCMLParser("fairfluids/data/cml_xml/gygli/glycerol.xml", document=doc)
doc = parser.parse()
```

### ThermoML → FAIRFluids

```python
from pathlib import Path
from fairfluids.core.lib import FAIRFluidsDocument
from fairfluids.io.thermoml_to_fairfluids import convert

payload = convert(Path("fairfluids/data/thermoml_xml/j.jct.2013.05.041.xml"))
doc = FAIRFluidsDocument.model_validate(payload)
```

### FAIRFluids → ThermoML

```python
from pathlib import Path
from fairfluids.io.fairfluids_to_thermoml import convert

xml_bytes = convert(Path("fairfluids_model.json"))
Path("output.thermoml.xml").write_bytes(xml_bytes)
```

CLI modules:

```bash
python -m fairfluids.io.thermoml_to_fairfluids.main --help
python -m fairfluids.io.fairfluids_to_thermoml.main --help
```

### Command-line interface

```bash
fairfluids create --output document.json
fairfluids csv fairfluids/data/csvs/exp_glycerol.csv --output document.json
fairfluids cml fairfluids/data/cml_xml/gygli/glycerol.xml --output document.json
fairfluids --help
```

## Workflows

Interactive Jupyter notebooks are kept in a local `Workflows/` directory that is
**not tracked in the repository** (it is gitignored as a personal scratch/experiment
area). Typical examples you can build there:

| Notebook | Description |
|----------|-------------|
| Basic creation | Create and populate a FAIRFluids document |
| CSV → FAIRFluids | Import tabular data via `FluidIO` |
| CML → FF | Parse CML and visualize viscosity data |
| ThermoML → FF | Convert ThermoML files to FAIRFluids JSON |
| Query & visualize | Query and plot document collections |
| Bayesian inference | Bayesian Arrhenius / VFT fitting (requires `[bayesian]`) |

Install the notebook stack and start Jupyter after creating your own `Workflows/`:

```bash
pip install -e ".[workflows]"   # or use environment.yml
jupyter notebook Workflows/
```

## Data model (summary)

| Component | Role |
|-----------|------|
| `FAIRFluidsDocument` | Root container (version, citation, compounds, fluids) |
| `Compound` | Chemical identity (PubChem, InChI, IUPAC, …) |
| `Fluid` / `Sample` | Experimental context and measurements |
| `Property` / `Parameter` | Measured quantities and conditions |
| `Measurement` | Values with uncertainties |

Full schema details: [`specifications/model.md`](specifications/model.md), [`specifications/ThermoML.md`](specifications/ThermoML.md).

## Migration from older layouts

If your code used `fairfluids.core.fluid_io`, `fairfluids.ThermoMLMapping`, or top-level ThermoML shims, see **[docs/MIGRATION.md](docs/MIGRATION.md)** for the new import paths.

## Development

```bash
conda activate fairfluids   # or your venv
pip install -e ".[dev,test]"
pytest test/ -v
```

Branch **`testing`** carries the current development line; open PRs against `main` when ready.

## Contributing

1. Fork the repository
2. Create a feature branch from `testing` or `main`
3. Make changes and add tests where applicable
4. Open a pull request on [GitHub](https://github.com/FAIRChemistry/FAIRFluids)

## License

MIT License — see [pyproject.toml](pyproject.toml).

## Citation

If you use FAIRFluids in your research, please cite the FAIRChemistry project and the relevant dataset publications. *(Citation block to be added.)*

## Contact

- Issues: [github.com/FAIRChemistry/FAIRFluids/issues](https://github.com/FAIRChemistry/FAIRFluids/issues)
- FAIRChemistry: [github.com/FAIRChemistry](https://github.com/FAIRChemistry)
