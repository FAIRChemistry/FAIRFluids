# FAIRFluids Visualization Module Documentation

## Overview

The `visualization.py` module provides comprehensive plotting and data analysis capabilities for FAIRFluids documents. It has been updated to work with the new composition-based approach where each fluid block represents a unique composition containing only the compounds present in that specific composition.

## Module Structure and Function Dependencies

### Core Utility Functions

#### `get_fluid_composition_summary(doc)`
- **Purpose**: Get a summary of all fluid compositions in a FAIRFluids document
- **Dependencies**: None (standalone utility)
- **Returns**: Dictionary with composition statistics
- **Used by**: `plot_composition_overview()`

#### `plot_composition_overview(doc, figsize=(12, 8), save_path=None)`
- **Purpose**: Create an overview plot showing distribution of compositions and measurements
- **Dependencies**: `get_fluid_composition_summary()`
- **Returns**: matplotlib.figure.Figure
- **Used by**: None (top-level plotting function)

### Arrhenius Analysis Functions

#### `arrhenius(x, ln_eta0, Ea)`
- **Purpose**: Arrhenius equation implementation
- **Dependencies**: None (mathematical function)
- **Returns**: Calculated value
- **Used by**: `fit_arrhenius_equation()`

#### `fit_arrhenius_equation(temps, visc)`
- **Purpose**: Fit Arrhenius equation to viscosity data
- **Dependencies**: `arrhenius()`, scipy.optimize.curve_fit
- **Returns**: Fitting parameters and fit line data
- **Used by**: `calculate_activation_energies()`, `plot_viscosity_vs_temperature()`

#### `calculate_activation_energies(doc, component_name)`
- **Purpose**: Calculate activation energies for each mole fraction group
- **Dependencies**: `get_viscosity_data()`, `fit_arrhenius_equation()`
- **Returns**: Activation energies and mole fraction groups
- **Used by**: `get_activation_energies()`, `plot_viscosity_vs_temperature()`

#### `get_activation_energies(doc, component_name)`
- **Purpose**: Get activation energies as sorted lists
- **Dependencies**: `calculate_activation_energies()`
- **Returns**: Sorted lists of mole fractions and activation energies
- **Used by**: `plot_activation_energy_analysis()`, `get_activation_energies_dataframe()`

#### `plot_activation_energy_analysis(doc, component_name, E_water=17.0, figsize=(4, 3), dpi=150)`
- **Purpose**: Create comprehensive activation energy analysis plot
- **Dependencies**: `get_activation_energies()`
- **Returns**: matplotlib.figure.Figure and analysis data
- **Used by**: None (top-level plotting function)

#### `get_activation_energies_dataframe(doc, component_name)`
- **Purpose**: Get activation energies as pandas DataFrame
- **Dependencies**: `get_activation_energies()`
- **Returns**: pandas.DataFrame
- **Used by**: None (utility function)

### Viscosity Plotting Functions

#### `plot_viscosity_vs_temperature(doc, component_name=None, fit_arrhenius=False, print_table=False, save_fig=False, group=None)`
- **Purpose**: Create Arrhenius plot of ln(viscosity) vs 1/RT
- **Dependencies**: `get_viscosity_data_with_meta()`, `calculate_activation_energies()`, `fit_arrhenius_equation()`
- **Returns**: None (displays plot)
- **Used by**: None (top-level plotting function)

### Data Extraction Functions

#### `get_viscosity_data(doc)`
- **Purpose**: Extract viscosity data from FAIRFluids document
- **Dependencies**: None (core data extraction)
- **Returns**: List of measurement dictionaries
- **Used by**: `calculate_activation_energies()`

#### `get_viscosity_data_with_meta(doc)`
- **Purpose**: Extract viscosity data with metadata (DOI, method)
- **Dependencies**: None (core data extraction)
- **Returns**: List of measurement dictionaries with metadata
- **Used by**: `plot_viscosity_vs_temperature()`

### Advanced Filtering and Analysis Functions

#### `filter_fluid_measurements(doc, fluid_compounds=None, property_type=None, return_dataframe=False)`
- **Purpose**: Filter fluid measurements by compound composition and property type
- **Dependencies**: None (core filtering function)
- **Returns**: List of dictionaries or pandas.DataFrame
- **Used by**: `discover_plotting_options()`, `extract_fairfluids_data()`, `plot_fairfluids_data()`

#### `get_measurements(doc, group=None)`
- **Purpose**: Filter measurements by group (Simulated/Measured/DOI)
- **Dependencies**: None (utility function)
- **Returns**: Filtered FAIRFluidsDocument
- **Used by**: None (utility function)

### Discovery and Exploration Functions

#### `discover_plotting_options(docs)`
- **Purpose**: Discover available plotting options from FAIRFluids document(s)
- **Dependencies**: `filter_fluid_measurements()`
- **Returns**: Dictionary of available options
- **Used by**: `interactive_plot_explorer()`

#### `interactive_plot_explorer(docs)`
- **Purpose**: Interactive function to explore plotting options
- **Dependencies**: `discover_plotting_options()`
- **Returns**: Options dictionary
- **Used by**: None (interactive exploration function)

### Utility Functions for Plotting

#### `format_composition_label(composition_tuple, compounds=None)`
- **Purpose**: Format composition tuple into readable label
- **Dependencies**: None (utility function)
- **Returns**: Formatted string
- **Used by**: `plot_fairfluids_data()`, `plot_dataframe()`

#### `round_composition_tuple(composition_tuple, decimal_places=3)`
- **Purpose**: Round mole fractions to avoid floating point precision issues
- **Dependencies**: None (utility function)
- **Returns**: Rounded tuple
- **Used by**: `plot_fairfluids_data()`

### Main Plotting Functions

#### `plot_fairfluids_data(docs, x_axis, y_axis, color_by=None, group_by=None, property_type=None, fluid_compounds=None, plot_type="scatter", figsize=(12, 8), title=None, save_path=None, show_legend=True, alpha=0.7, s=50)`
- **Purpose**: Create flexible plots for FAIRFluids data
- **Dependencies**: `filter_fluid_measurements()`, `format_composition_label()`, `round_composition_tuple()`
- **Returns**: matplotlib.figure.Figure
- **Used by**: None (main plotting function)

#### `extract_fairfluids_data(docs, property_types=None, fluid_compounds=None, required_compounds=None, decimal_places=3)`
- **Purpose**: Extract data from FAIRFluids documents into clean pandas DataFrame
- **Dependencies**: `filter_fluid_measurements()`
- **Returns**: pandas.DataFrame
- **Used by**: None (data extraction utility)

#### `plot_dataframe(df, x_axis, y_axis, color_by=None, group_by=None, plot_type="scatter", figsize=(12, 8), title=None, save_path=None, show_legend=True, alpha=0.7, s=50)`
- **Purpose**: Create plots from pandas DataFrame containing FAIRFluids data
- **Dependencies**: `format_composition_label()`
- **Returns**: matplotlib.figure.Figure
- **Used by**: None (DataFrame plotting function)

### Example Usage Functions

#### `example_usage_filter_fluid_measurements()`
- **Purpose**: Example usage of the filter_fluid_measurements function
- **Dependencies**: None (documentation function)
- **Returns**: None (prints examples)
- **Used by**: None (documentation)

## Function Dependency Graph

```
Top-Level Functions (no dependencies):
├── plot_composition_overview()
├── plot_activation_energy_analysis()
├── plot_viscosity_vs_temperature()
├── plot_fairfluids_data()
├── extract_fairfluids_data()
├── plot_dataframe()
├── interactive_plot_explorer()
└── example_usage_filter_fluid_measurements()

Core Data Functions:
├── get_fluid_composition_summary()
├── get_viscosity_data()
├── get_viscosity_data_with_meta()
├── filter_fluid_measurements()
└── get_measurements()

Arrhenius Analysis Chain:
arrhenius() → fit_arrhenius_equation() → calculate_activation_energies() → get_activation_energies()

Utility Functions:
├── format_composition_label()
├── round_composition_tuple()
└── discover_plotting_options()
```

## Key Features

### Composition-Based Approach Support
- All functions now work with the new structure where each fluid block represents a unique composition
- No need for post-processing filtering as data is structured correctly from the start
- Enhanced support for multiple fluid blocks with different compound combinations

### Flexible Plotting
- Support for multiple property types (viscosity, density, conductivity, etc.)
- Composition-based grouping and coloring
- Temperature and mole fraction analysis
- Arrhenius equation fitting and activation energy analysis

### Data Discovery
- Automatic discovery of available plotting options
- Interactive exploration capabilities
- Comprehensive data extraction utilities

### Robust Data Handling
- Handles floating point precision issues in mole fractions
- Supports both single documents and lists of documents
- Flexible filtering by compounds, properties, and metadata

## Usage Examples

### Basic Composition Overview
```python
from fairfluids.core.visualization import plot_composition_overview

# Create overview plot of all compositions
fig = plot_composition_overview(doc, save_path="composition_overview.png")
```

### Flexible Data Plotting
```python
from fairfluids.core.visualization import plot_fairfluids_data

# Plot viscosity vs temperature, colored by composition
fig = plot_fairfluids_data(
    docs=doc,
    x_axis='temperature',
    y_axis='viscosity',
    color_by='composition',
    property_type='viscosity'
)
```

### Activation Energy Analysis
```python
from fairfluids.core.visualization import plot_activation_energy_analysis

# Analyze activation energies for water content
water_fractions, E_values, E_DES, E_water = plot_activation_energy_analysis(
    doc, component_name="Water"
)
```

### Data Discovery
```python
from fairfluids.core.visualization import interactive_plot_explorer

# Discover available plotting options
options = interactive_plot_explorer(doc)
```

## Notes

- The module has been updated to work with both the new composition-based structure (xu_Reline_glycerol_Water.json) and the traditional structure (fairfluids_document.json)
- All functions maintain backward compatibility while providing enhanced functionality for the new approach
- The old filtering functions have been removed as they are no longer needed with the composition-based approach
