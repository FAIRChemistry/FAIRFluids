# FAIRFluids Web Interface

A modern web application for visualizing thermophysical property data from the FAIRFluids Neo4j database. This interface allows users to select components and generate interactive viscosity vs temperature plots with multiple compositions.

## Features

- **Component Selection**: Multi-select dropdown with all available compounds from the Neo4j database
- **Fluid Discovery**: Find fluids containing selected components
- **Interactive Plotting**: Generate viscosity vs temperature plots with Plotly
- **Composition Support**: Display multiple compositions for each fluid system
- **Modern UI**: Responsive Bootstrap-based interface with gradient styling
- **Real-time Stats**: Live statistics showing available compounds, matching fluids, and data points

## Prerequisites

- Python 3.8+
- Neo4j database running (see main project setup)
- FAIRFluids package installed

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure Neo4j is Running**:
   ```bash
   cd /path/to/FAIRFluids/neo4j
   ./setup_neo4j.sh
   ```

3. **Verify Database Connection**:
   - Neo4j should be accessible at `bolt://localhost:7687`
   - Username: `neo4j`, Password: `password`

## Usage

1. **Start the Web Application**:
   ```bash
   python app.py
   ```

2. **Access the Interface**:
   - Open your browser and go to: http://localhost:5000
   - The interface will automatically load all available compounds

3. **Generate Plots**:
   - Select one or more compounds from the dropdown
   - Click "Find Fluids" to discover matching fluid systems
   - Click "Generate Plot" to create viscosity vs temperature visualization

## API Endpoints

- `GET /api/compounds` - Get all available compounds
- `GET /api/fluids?compound_ids[]=id1&compound_ids[]=id2` - Find fluids with selected compounds
- `GET /api/viscosity-data?fluid_ids[]=id1&fluid_ids[]=id2` - Get viscosity vs temperature data
- `GET /api/composition-data?fluid_ids[]=id1&fluid_ids[]=id2` - Get composition data
- `GET /api/plot?fluid_ids[]=id1&fluid_ids[]=id2` - Generate interactive plot

## Data Structure

The application queries the following Neo4j node types:
- **Compound**: Chemical compounds with identifiers and names
- **Fluid**: Fluid systems containing multiple compounds
- **Property**: Physical properties (viscosity, density, etc.)
- **Measurement**: Individual measurement data points
- **Parameter**: Measurement parameters (temperature, pressure, composition)

## Plot Features

- **Logarithmic Y-axis**: Viscosity values displayed on log scale
- **Interactive Hover**: Detailed information on hover including compositions
- **Multiple Traces**: Each fluid system shown as separate trace
- **Color Coding**: Automatic color assignment for different fluid systems
- **Responsive Design**: Plots adapt to different screen sizes

## Troubleshooting

### Common Issues

1. **Neo4j Connection Error**:
   - Ensure Neo4j is running: `docker ps | grep neo4j`
   - Check connection: `python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password')); print('Connected'); driver.close()"`

2. **No Compounds Loaded**:
   - Verify the database has been populated with ThermoML data
   - Check Neo4j browser at http://localhost:7474

3. **Plot Generation Fails**:
   - Ensure selected fluids have viscosity data
   - Check browser console for JavaScript errors

### Debug Mode

Run with debug logging:
```bash
export FLASK_DEBUG=1
python app.py
```

## Customization

### Styling
- Modify CSS in the `<style>` section of `templates/index.html`
- Bootstrap classes can be customized for different themes

### Plot Configuration
- Edit the `create_viscosity_plot()` function in `app.py`
- Modify Plotly layout and trace options

### Database Queries
- Customize Cypher queries in the `Neo4jDataService` class
- Add new API endpoints for different property types

## Development

### Adding New Property Types
1. Add new API endpoint in `app.py`
2. Create corresponding query method in `Neo4jDataService`
3. Add frontend functionality in `templates/index.html`

### Extending the UI
1. Add new HTML sections in the template
2. Implement JavaScript functionality
3. Add corresponding Flask routes

## License

This project is part of the FAIRFluids framework. See the main project for licensing information.

