#!/usr/bin/env python3
"""
FAIRFluids Web Interface

A Flask web application for querying and visualizing thermophysical property data
from the Neo4j database. Uses the Experiment-centered graph structure where
Experiments are central nodes connected to Compounds, Properties, and Parameters.
Allows users to select components and generate viscosity vs temperature plots
with multiple compositions.

Graph Structure:
    - Experiment nodes (central) with properties like prop_viscosity, param_temperature
    - Experiment -[:HAS_COMPOUND]-> Compound (with mole_fraction on edge)
    - Experiment -[:HAS_PROPERTY]-> Property (with value and uncertainty on edge)
    - Experiment -[:HAS_PARAMETER]-> Parameter (with value and uncertainty on edge)
    - Experiment -[:CITED_IN]-> Citation

Usage:
    python app.py
    Then visit: http://localhost:5000
"""

from flask import Flask, render_template, jsonify, request
from neo4j import GraphDatabase
import json
import plotly
import plotly.graph_objs as go
from plotly.utils import PlotlyJSONEncoder
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import logging
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


class Neo4jDataService:
    """Service class for interacting with Neo4j database."""

    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_all_compounds(self) -> List[Dict[str, Any]]:
        """Get all compounds from the database."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:Compound)
                RETURN c.compoundID as compoundID, 
                       c.commonName as commonName,
                       c.name_IUPAC as name_IUPAC,
                       c.pubChemID as pubChemID
                ORDER BY c.commonName
            """
            )

            compounds = []
            for record in result:
                compounds.append(
                    {
                        "compoundID": record["compoundID"],
                        "commonName": record["commonName"],
                        "name_IUPAC": record["name_IUPAC"],
                        "pubChemID": record["pubChemID"],
                    }
                )

            return compounds

    def get_fluids_with_compounds(
        self, compound_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Get experiments (grouped by fluidID/composition) that contain the specified compounds."""
        with self.driver.session() as session:
            # Use parameterized query for safety
            result = session.run(
                """
                MATCH (e:Experiment)-[r:HAS_COMPOUND]->(c:Compound)
                WHERE c.compoundID IN $compound_ids
                WITH e, collect(DISTINCT c.commonName) as compounds, 
                     collect(DISTINCT {compound: c.commonName, mole_fraction: r.mole_fraction}) as compound_details
                WHERE size(compounds) >= $min_compounds
                WITH e, compounds, compound_details,
                     COALESCE(e.fluidID, e.experiment_id) as fluid_id
                // Group by fluid_id and compound composition
                WITH fluid_id, 
                     collect(DISTINCT compounds)[0] as compounds,
                     collect(DISTINCT compound_details)[0] as compound_details,
                     count(DISTINCT e) as experiment_count
                RETURN fluid_id,
                       compounds,
                       compound_details,
                       size(compounds) as component_count,
                       experiment_count
                ORDER BY fluid_id
            """,
                compound_ids=compound_ids,
                min_compounds=len(compound_ids),
            )

            fluids = []
            for record in result:
                # Build composition string from compound_details
                comp_details = record["compound_details"]
                comp_strings = []
                for comp_detail in comp_details:
                    comp_name = comp_detail.get("compound", "")
                    mole_frac = comp_detail.get("mole_fraction")
                    if mole_frac is not None:
                        comp_strings.append(f"{comp_name} (x={mole_frac:.3f})")
                    else:
                        comp_strings.append(comp_name)

                fluids.append(
                    {
                        "fluid_id": record["fluid_id"] or "unknown",
                        "compounds": record["compounds"],
                        "compound_details": comp_strings,
                        "component_count": record["component_count"],
                    }
                )

            return fluids

    def get_viscosity_temperature_data(
        self, fluid_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Get viscosity vs temperature data for specified experiments (by fluidID)."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (e:Experiment)-[r:HAS_COMPOUND]->(c:Compound)
                WHERE (e.fluidID IN $fluid_ids OR e.experiment_id IN $fluid_ids)
                AND e.param_temperature IS NOT NULL
                AND e.prop_viscosity IS NOT NULL
                WITH e, collect(DISTINCT {compound: c.commonName, mole_fraction: r.mole_fraction}) as compound_details
                WITH e, compound_details,
                     e.param_temperature as temperature_value,
                     e.prop_viscosity as viscosity_value,
                     [key IN keys(e) WHERE key STARTS WITH 'param_' AND (key CONTAINS 'mole_fraction' OR key CONTAINS 'mass_fraction') | 
                      {param: substring(key, 6), value: e[key]}] as compositions
                RETURN COALESCE(e.fluidID, e.experiment_id) as fluid_id,
                       temperature_value,
                       viscosity_value,
                       compositions,
                       compound_details,
                       e.experiment_id as experiment_id
                ORDER BY fluid_id, temperature_value
            """,
                fluid_ids=fluid_ids,
            )

            data = []
            for record in result:
                # Build compositions from compound_details (mole fractions on edges)
                compositions = list(record["compositions"])

                # Add mole fractions from HAS_COMPOUND relationships
                for comp_detail in record["compound_details"]:
                    mole_frac = comp_detail.get("mole_fraction")
                    if mole_frac is not None:
                        comp_name = comp_detail.get("compound", "")
                        # Check if we already have this composition
                        found = False
                        for comp in compositions:
                            if (
                                comp.get("param", "").lower().replace("_", " ")
                                == comp_name.lower()
                            ):
                                found = True
                                break
                        if not found:
                            compositions.append(
                                {
                                    "param": f"mole_fraction_{comp_name}",
                                    "value": mole_frac,
                                }
                            )

                data.append(
                    {
                        "fluid_id": record["fluid_id"],
                        "compounds": [
                            cd.get("compound", "") for cd in record["compound_details"]
                        ],
                        "viscosity": record["viscosity_value"],
                        "temperature": record["temperature_value"],
                        "compositions": compositions,
                        "measurement_id": record["experiment_id"],
                    }
                )

            return data

    def get_composition_data(self, fluid_ids: List[str]) -> List[Dict[str, Any]]:
        """Get composition data for specified experiments (by fluidID)."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (e:Experiment)-[r:HAS_COMPOUND]->(c:Compound)
                WHERE (e.fluidID IN $fluid_ids OR e.experiment_id IN $fluid_ids)
                WITH e, c, r.mole_fraction as mole_fraction
                WHERE mole_fraction IS NOT NULL
                RETURN COALESCE(e.fluidID, e.experiment_id) as fluid_id,
                       c.commonName as compound_name,
                       c.compoundID as compound_id,
                       'mole_fraction' as parameter_type,
                       mole_fraction as comp_value,
                       e.experiment_id as experiment_id
                ORDER BY fluid_id, compound_name
            """,
                fluid_ids=fluid_ids,
            )

            compositions = []
            for record in result:
                compositions.append(
                    {
                        "fluid_id": record["fluid_id"],
                        "compound_name": record["compound_name"],
                        "compound_id": record["compound_id"],
                        "parameter_type": record["parameter_type"],
                        "value": record["comp_value"],
                        "measurement_id": record["experiment_id"],
                    }
                )

            return compositions


# Initialize the data service
data_service = Neo4jDataService()


@app.route("/")
def index():
    """Main page."""
    return render_template("index.html")


@app.route("/api/compounds")
def get_compounds():
    """API endpoint to get all compounds."""
    try:
        compounds = data_service.get_all_compounds()
        return jsonify({"success": True, "compounds": compounds})
    except Exception as e:
        logger.error(f"Error getting compounds: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/fluids")
def get_fluids():
    """API endpoint to get experiments (grouped by fluidID/composition) containing selected compounds."""
    try:
        compound_ids = request.args.getlist("compound_ids[]")
        if not compound_ids:
            return jsonify({"success": False, "error": "No compounds selected"})

        fluids = data_service.get_fluids_with_compounds(compound_ids)
        return jsonify({"success": True, "fluids": fluids})
    except Exception as e:
        logger.error(f"Error getting fluids: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/viscosity-data")
def get_viscosity_data():
    """API endpoint to get viscosity vs temperature data from experiments."""
    try:
        fluid_ids = request.args.getlist("fluid_ids[]")
        if not fluid_ids:
            return jsonify({"success": False, "error": "No fluids selected"})

        data = data_service.get_viscosity_temperature_data(fluid_ids)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"Error getting viscosity data: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/composition-data")
def get_composition_data():
    """API endpoint to get composition data from experiments (mole fractions from HAS_COMPOUND edges)."""
    try:
        fluid_ids = request.args.getlist("fluid_ids[]")
        if not fluid_ids:
            return jsonify({"success": False, "error": "No fluids selected"})

        data = data_service.get_composition_data(fluid_ids)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"Error getting composition data: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/plot")
def generate_plot():
    """API endpoint to generate viscosity vs temperature plot from experiment data."""
    try:
        fluid_ids = request.args.getlist("fluid_ids[]")
        if not fluid_ids:
            return jsonify({"success": False, "error": "No fluids selected"})

        # Check if regression is requested
        show_regression = request.args.get("show_regression", "false").lower() == "true"

        # Get viscosity data
        viscosity_data = data_service.get_viscosity_temperature_data(fluid_ids)

        if not viscosity_data:
            return jsonify({"success": False, "error": "No viscosity data found"})

        # Create plot
        fig = create_viscosity_plot(viscosity_data, show_regression=show_regression)

        # Convert to JSON
        graphJSON = json.dumps(fig, cls=PlotlyJSONEncoder)

        return jsonify({"success": True, "plot": graphJSON})
    except Exception as e:
        logger.error(f"Error generating plot: {e}")
        return jsonify({"success": False, "error": str(e)})


def calculate_linear_regression(
    x_data: List[float], y_data: List[float]
) -> Dict[str, Any]:
    """
    Calculate linear regression curve for given data points.
    """
    if len(x_data) < 3:
        return None

    x_array = np.array(x_data).reshape(-1, 1)
    y_array = np.array(y_data)

    try:
        model = LinearRegression()
        model.fit(x_array, y_array)
        y_pred = model.predict(x_array)
        r2 = r2_score(y_array, y_pred)

        # Generate smooth curve for plotting
        x_fit = np.linspace(min(x_data), max(x_data), 100)
        y_fit = model.predict(x_fit.reshape(-1, 1))

        return {
            "model_type": "linear",
            "params": {
                "slope": model.coef_[0],
                "intercept": model.intercept_,
                "r2": r2,
            },
            "r2": r2,
            "x_fit": x_fit.tolist(),
            "y_fit": y_fit.tolist(),
        }
    except:
        return None


def create_viscosity_plot(
    data: List[Dict[str, Any]], show_regression: bool = False
) -> Dict[str, Any]:
    """Create a Plotly figure for ln(viscosity) vs 1/RT (Arrhenius plot)."""

    # Group data by fluid and composition
    composition_groups = {}
    for point in data:
        fluid_id = point["fluid_id"]
        compositions = point["compositions"]

        # Create a composition key by sorting and joining mole fractions
        mole_fractions = []
        for comp in compositions:
            if "mole_fraction" in comp["param"]:
                mole_fractions.append(f"{comp['param']}={comp['value']:.3f}")

        if mole_fractions:
            # Sort the mole fraction strings alphabetically
            comp_key = f"{fluid_id} ({', '.join(sorted(mole_fractions))})"
        else:
            comp_key = f"{fluid_id} (no composition data)"

        if comp_key not in composition_groups:
            composition_groups[comp_key] = {
                "temperatures": [],
                "viscosities": [],
                "compositions": [],
            }

        composition_groups[comp_key]["temperatures"].append(point["temperature"])
        composition_groups[comp_key]["viscosities"].append(point["viscosity"])
        composition_groups[comp_key]["compositions"].append(point["compositions"])

    # Create traces for each composition
    traces = []
    colors = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
        "#aec7e8",
        "#ffbb78",
        "#98df8a",
        "#ff9896",
        "#c5b0d5",
        "#c49c94",
        "#f7b6d3",
        "#c7c7c7",
        "#dbdb8d",
        "#9edae5",
    ]

    # Limit the number of visible legend items to prevent overcrowding
    max_legend_items = 15
    composition_items = list(composition_groups.items())

    # If we have too many items, show only the first few and add a note
    if len(composition_items) > max_legend_items:
        composition_items = composition_items[:max_legend_items]
        # Add a note trace for the remaining items
        note_trace = go.Scatter(
            x=[],
            y=[],
            mode="markers",
            name=f"... and {len(composition_groups) - max_legend_items} more series",
            marker=dict(size=0),
            showlegend=True,
            legendgroup="overflow",
        )
        traces.append(note_trace)

    # Gas constant R = 8.314 J/(mol·K)
    R = 8.314

    for i, (comp_key, comp_data) in enumerate(composition_items):
        # Sort by temperature
        temp_visc_comp = list(
            zip(
                comp_data["temperatures"],
                comp_data["viscosities"],
                comp_data["compositions"],
            )
        )
        sorted_data = sorted(temp_visc_comp, key=lambda x: x[0])

        temperatures, viscosities, compositions = zip(*sorted_data)

        # Convert to Arrhenius plot coordinates
        # x = 1/(R*T), y = ln(viscosity)
        inv_rt = [1 / (R * T) for T in temperatures]
        ln_viscosity = [np.log(visc) for visc in viscosities]

        # Create hover text with composition info
        hover_text = []
        for j, comp in enumerate(compositions):
            comp_text = []
            for c in comp:
                comp_text.append(f"{c['param']}: {c['value']:.3f}")
            hover_text.append(
                f"Fluid: {comp_key}<br>"
                f"Temperature: {temperatures[j]:.2f} K<br>"
                f"1/RT: {inv_rt[j]:.6f} mol/J<br>"
                f"Viscosity: {viscosities[j]:.2e} Pa·s<br>"
                f"ln(η): {ln_viscosity[j]:.3f}<br>"
                f"Composition: {', '.join(comp_text)}"
            )

        # Create trace with markers only (no lines connecting points)
        # Truncate long legend names to keep them manageable
        legend_name = comp_key
        if len(legend_name) > 50:  # Truncate very long names
            legend_name = legend_name[:47] + "..."

        trace = go.Scatter(
            x=inv_rt,
            y=ln_viscosity,
            mode="markers",
            name=legend_name,
            marker=dict(
                size=8, color=colors[i % len(colors)], line=dict(width=1, color="white")
            ),
            text=hover_text,
            hovertemplate="%{text}<extra></extra>",
            legendgroup=f"group_{i}",  # Group related traces
        )
        traces.append(trace)

        # Add regression curve if requested and we have enough data points
        if show_regression and len(inv_rt) >= 3:
            regression = calculate_linear_regression(inv_rt, ln_viscosity)
            if regression:
                # Create regression curve trace
                reg_trace = go.Scatter(
                    x=regression["x_fit"],
                    y=regression["y_fit"],
                    mode="lines",
                    name=f"{legend_name} (R²={regression['r2']:.3f})",
                    line=dict(color=colors[i % len(colors)], width=2, dash="dash"),
                    legendgroup=f"group_{i}",
                    showlegend=True,
                    hoverinfo="skip",
                )
                traces.append(reg_trace)

    # Create layout with better legend positioning
    layout = go.Layout(
        title="Arrhenius Plot: ln(Viscosity) vs 1/RT",
        xaxis=dict(
            title="1/RT (mol/J)",
            showgrid=True,
            gridwidth=1,
            gridcolor="lightgray",
            domain=[0.25, 0.95],  # Reserve more space for legend on the left
            tickformat=".6f",  # Remove scientific notation, show 6 decimal places
        ),
        yaxis=dict(
            title="ln(η)",  # Use Greek letter eta
            showgrid=True,
            gridwidth=1,
            gridcolor="lightgray",
        ),
        hovermode="closest",
        showlegend=True,
        legend=dict(
            x=0.02,  # Position legend slightly right of the left edge
            y=0.98,  # Position slightly below the top
            xanchor="left",
            yanchor="top",
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="rgba(0,0,0,0.3)",
            borderwidth=1,
            font=dict(size=9),  # Even smaller font for legend
            orientation="v",  # Vertical orientation
            itemsizing="constant",  # Consistent item sizes
            itemwidth=30,  # Minimum allowed item width
            traceorder="normal",
        ),
        margin=dict(l=60, r=20, t=60, b=60),
        plot_bgcolor="white",
        paper_bgcolor="white",
        width=None,  # Let it use full container width
        height=600,  # Fixed height to ensure visibility
    )

    return {"data": traces, "layout": layout}


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    try:
        # Test Neo4j connection
        compounds = data_service.get_all_compounds()
        logger.info(f"Connected to Neo4j. Found {len(compounds)} compounds.")

        # Run the Flask app
        app.run(debug=True, host="0.0.0.0", port=5000)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
    finally:
        data_service.close()
