# Import the FAIRFluids models
from .lib import (
    FAIRFluidsDocument,
    Version,
    Citation,
    Author,
    Compound,
    Fluid,
    Property,
    PropertyValue,
    Parameter,
    ParameterValue,
    Measurement,
    Sample,
    UnitDefinition,
    BaseUnit,
    Method,
    Properties,
    Parameters,
)
from typing import Optional, List, Dict, Any, Tuple, Union
import xml.etree.ElementTree as ET
import requests
import numpy as np
import uuid
import hashlib
import colorsys
from collections import defaultdict
import pandas as pd

from fairfluids.inspection.document import (
    show_available_parameters,
    show_available_properties,
)
from fairfluids.operations.sample_utils import _ensure_fluid_sample, _get_measurements
from fairfluids.operations.compounds import (
    combine_compounds,
    calculate_ratio_of_solvent,
    cleanup_orphaned_parameters,
)
from fairfluids.io.cml_parser import FAIRFluidsCMLParser


def _string_to_hex_color(s: str, sat: float = 0.65, val: float = 0.85) -> str:
    """Deterministically map strings to hex colors (used for DOI coloring)."""
    h = hashlib.sha256(str(s).encode()).hexdigest()
    h_int = int(h[:8], 16)
    hue = (h_int * 0.618033988749895) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))


def _get_doi_plot_style(
    doi: Any, custom_styles: Optional[dict[str, dict[str, str]]] = None
) -> dict[str, str]:
    """Return DOI plotting style; prefers caller-provided styles."""
    doi_str = str(doi)
    style = custom_styles.get(doi_str, {}) if custom_styles else {}
    return {
        "color": style.get("color", _string_to_hex_color(doi_str)),
        "marker": style.get("marker", "o"),
    }


def _is_compositional_parameter(param_name_lower: str) -> bool:
    """
    Check if a parameter name represents a compositional parameter.

    Args:
        param_name_lower: Lowercase parameter name

    Returns:
        True if the parameter is compositional, False otherwise
    """
    compositional_keywords = [
        "mole fraction",
        "mass fraction",
        "volume fraction",
        "molality",
        "molarity",
        "amount concentration",
        "amount ratio",
        "mass ratio",
        "volume ratio",
        "ratio of amount",
        "ratio of mass",
        "ratio of component",
        "amount density",
        "amount of solute",
        "mass of solute",
        "volume of solute",
        "solute to solvent",
        "solute to solution",
        "component to other component",
        "component to mass",
        "component mass to volume",
    ]

    return any(keyword in param_name_lower for keyword in compositional_keywords)


def filter_fluid_compounds_by_mole_fractions(fluid):
    """
    Filter compounds and their parameters from a fluid if they have zero mole fractions
    in ALL measurements AND no other compositional parameters are present.

    This function:
    1. Checks each compound's compositional parameters (mole fraction, mass fraction,
       molality, volume fraction, ratios, etc.) across all measurements
    2. Removes compounds that have 0.0 mole fractions in ALL measurements AND no other
       compositional parameters present
    3. Removes associated parameter definitions
    4. Removes parameter values from all measurements

    Args:
        fluid: A Fluid object with measurements

    Returns:
        The fluid object with filtered compounds and parameters
    """
    if not _get_measurements(fluid):
        return fluid

    print(
        f"=== Filtering Fluid with {len(fluid.compounds)} compounds and {len(_get_measurements(fluid))} measurements ==="
    )

    # Track which compounds should be kept (non-zero mole fractions OR other compositional params present)
    compounds_to_keep = set()

    # Build a quick lookup for parameter definitions by ID once
    parameter_lookup = {
        param.parameterID: param
        for param in fluid.parameter
        if getattr(param, "parameterID", None)
    }

    # Check each compound's compositional parameters across all measurements
    for compound_id in fluid.compounds:
        has_non_zero_mole_fraction = False
        has_compositional_signal = False  # any compositional parameter present
        compositional_param_types = []  # track which types we found

        # Check all measurements for this compound
        for measurement in _get_measurements(fluid):
            for param_value in measurement.parameterValue:
                # Find the parameter definition for this parameter value
                param_def = parameter_lookup.get(param_value.parameterID)

                # Check if this is a compositional parameter for this compound
                if (
                    param_def
                    and compound_id in param_def.associated_compounds
                    and hasattr(param_def, "parameters")
                    and param_def.parameters is not None
                ):

                    # Normalize parameter name
                    param_name = str(param_def.parameters)
                    if hasattr(param_def.parameters, "value"):
                        param_name = param_def.parameters.value
                    param_name_lower = param_name.lower()

                    # Check if this is any compositional parameter
                    if _is_compositional_parameter(param_name_lower):
                        has_compositional_signal = True

                        # Track the type for reporting
                        if "mole fraction" in param_name_lower:
                            compositional_param_types.append("mole fraction")
                        elif "mass fraction" in param_name_lower:
                            compositional_param_types.append("mass fraction")
                        elif "molality" in param_name_lower:
                            compositional_param_types.append("molality")
                        elif "volume fraction" in param_name_lower:
                            compositional_param_types.append("volume fraction")
                        elif "ratio" in param_name_lower:
                            compositional_param_types.append("ratio")
                        elif (
                            "molarity" in param_name_lower
                            or "amount concentration" in param_name_lower
                        ):
                            compositional_param_types.append("molarity/concentration")
                        else:
                            compositional_param_types.append("compositional")

                        # Check for non-zero mole fraction specifically
                        if "mole fraction" in param_name_lower:
                            if (
                                param_value.paramValue is not None
                                and param_value.paramValue > 0
                            ):
                                has_non_zero_mole_fraction = True
                                break
                        # For other compositional parameters, just note their presence
                        # (we don't break to continue looking for mole fractions)

            if has_non_zero_mole_fraction:
                break

        if has_non_zero_mole_fraction or has_compositional_signal:
            compounds_to_keep.add(compound_id)
            # Create descriptive reason
            if has_non_zero_mole_fraction:
                reason = "non-zero mole fractions"
            else:
                unique_types = list(set(compositional_param_types))
                if len(unique_types) == 1:
                    reason = f"composition parameter present ({unique_types[0]})"
                else:
                    reason = f"composition parameters present ({', '.join(unique_types[:3])}{'...' if len(unique_types) > 3 else ''})"
            print(f"✅ Keeping compound: {compound_id} ({reason})")
        else:
            print(
                f"❌ Removing compound: {compound_id} (no compositional parameters in measurements)"
            )

    # Update compounds list
    original_compounds = fluid.compounds.copy()
    fluid.compounds = [comp for comp in original_compounds if comp in compounds_to_keep]

    # Remove parameter definitions for compounds that are not kept
    original_parameters = fluid.parameter.copy()
    fluid.parameter = [
        param
        for param in original_parameters
        if (
            not hasattr(param, "associated_compounds")
            or not param.associated_compounds
            or any(comp in compounds_to_keep for comp in param.associated_compounds)
        )
    ]

    # Remove parameter values from measurements for compounds that are not kept
    for measurement in _get_measurements(fluid):
        original_param_values = measurement.parameterValue.copy()
        measurement.parameterValue = []

        for pv in original_param_values:
            # Find the parameter definition for this parameter value
            param_def = None
            for param in fluid.parameter:
                if param.parameterID == pv.parameterID:
                    param_def = param
                    break

            # Keep the parameter value if:
            # 1. It's not associated with any compound (like temperature)
            # 2. It's associated with a compound that we're keeping
            if (
                not param_def
                or not hasattr(param_def, "associated_compounds")
                or not param_def.associated_compounds
                or any(
                    comp in compounds_to_keep for comp in param_def.associated_compounds
                )
            ):
                measurement.parameterValue.append(pv)

    print(
        f"Final result: {len(fluid.compounds)} compounds, {len(fluid.parameter)} parameters"
    )
    return fluid


def calculate_activationEnergy(
    doc: FAIRFluidsDocument,
    per_source: bool = False,
    solvent_ratio_value: Optional[float] = None,
    return_dataframe: bool = False,
) -> Union[Dict[str, Dict[str, Any]], pd.DataFrame]:
    """
    Calculate activation energy for viscosity using the Arrhenius equation.

    The Arrhenius equation for viscosity is: η = η₀ * exp(Ea/(R*T))
    Taking natural logarithm: ln(η) = ln(η₀) + (Ea/R) * (1/T)

    Linear regression of ln(η) vs 1/T gives: slope = Ea/R
    Therefore: Ea = slope * R, where R = 8.314 J/(mol·K)

    Args:
        doc: The FAIRFluidsDocument containing fluids and measurements
        per_source: If True, group by fluid AND source_doi (separate calculation for each fluid-DOI combination).
                   If False, group by fluid only (use all measurements from each fluid regardless of DOI).
                   Each fluid already represents a unique composition based on mole fractions.
        solvent_ratio_value: Optional filter value. If provided, only processes fluids and measurements where
                           the "Solvent: Amount ratio of component to other component of binary solvent"
                           parameter equals this value (within floating point tolerance). This filters the data
                           before calculating activation energy.
        return_dataframe: If True, returns a pandas DataFrame instead of a dictionary. The DataFrame will have
                         columns: Group ID, Compounds, Water Fraction, Mole Fractions, Activation Energy (J/mol),
                         Activation Energy (kJ/mol), η₀ (mPa·s), R², N points, Source DOI(s).

    Returns:
        If return_dataframe=False (default): Dictionary with keys being group identifiers (fluid index like "fluid_0"
        or fluid-DOI combination) and values containing:
        - 'activation_energy': Activation energy in J/mol
        - 'eta0': Pre-exponential factor (η₀) in mPa·s
        - 'r_squared': R² value of the fit
        - 'n_points': Number of data points used
        - 'temperatures': List of temperatures used (K)
        - 'viscosities': List of viscosities used (mPa·s)
        - 'source_doi': Source DOI for this group
        - 'compounds': List of compound IDs
        - 'mole_fractions': Dictionary of all mole fractions (backward compatibility)
        - 'water_fraction': Water mole fraction (if available)
        - 'mole_fraction_<compound_name>': Individual mole fraction columns for each compound
          (e.g., 'mole_fraction_water', 'mole_fraction_glycerol', 'mole_fraction_cholinechloride')

        If return_dataframe=True: pandas DataFrame with columns:
        - 'Group ID': Group identifier (fluid index or fluid-DOI combination)
        - 'Compounds': Comma-separated string of compound IDs
        - 'Water Fraction': Water mole fraction (NaN if not available)
        - 'Mole Fractions': Formatted string of all mole fractions (e.g., "compound1: 0.3333, compound2: 0.6667")
        - 'Activation Energy (J/mol)': Activation energy in J/mol
        - 'Activation Energy (kJ/mol)': Activation energy in kJ/mol
        - 'η₀ (mPa·s)': Pre-exponential factor
        - 'R²': R² value of the fit
        - 'N points': Number of data points used
        - 'Source DOI(s)': Source DOI string (or "mixed" if multiple sources)

    Example:
        # Return dictionary
        results = calculate_activationEnergy(doc, per_source=False)
        for group_id, result in results.items():
            print(f"{group_id}: Ea = {result['activation_energy']:.2f} J/mol")

        # Return DataFrame
        df = calculate_activationEnergy(doc, per_source=False, return_dataframe=True)
        print(df)

        # Filter by solvent ratio = 2.0 and return DataFrame
        df = calculate_activationEnergy(doc, per_source=False, solvent_ratio_value=2.0, return_dataframe=True)
    """
    R = 8.314  # Gas constant in J/(mol·K)

    # Print filter information if filtering is active
    if solvent_ratio_value is not None:
        print(f"=== Filtering by solvent ratio = {solvent_ratio_value} ===")

    # Group measurements by fluid or source_doi
    grouped_data = defaultdict(
        lambda: {
            "temperatures": [],
            "viscosities": [],
            "source_dois": set(),
            "compounds": None,
            "mole_fractions": {},  # Store mole fractions for each compound
        }
    )

    for fluid_idx, fluid in enumerate(doc.fluid):
        # Build parameter lookup
        parameter_lookup = {}
        for param in fluid.parameter:
            if param.parameterID:
                parameter_lookup[param.parameterID] = param

        # Build property lookup
        property_lookup = {}
        for prop in fluid.property:
            if prop.propertyID:
                property_lookup[prop.propertyID] = prop

        # If filtering by solvent ratio, find parameter IDs that match the filter
        solvent_ratio_param_ids = []
        if solvent_ratio_value is not None:
            target_param_type = (
                Parameters.SOLVENT_AMOUNT_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT
            )
            for param in fluid.parameter:
                if param.parameters and param.parameters == target_param_type:
                    solvent_ratio_param_ids.append(param.parameterID)

            if not solvent_ratio_param_ids:
                # Skip this fluid if filtering is requested but no matching parameter found
                print(
                    f"Fluid {fluid_idx}: Skipping - no solvent ratio parameter found (filtering by ratio={solvent_ratio_value})"
                )
                continue

        # Helper function to check if measurement matches solvent ratio filter
        def matches_solvent_ratio_filter(measurement):
            if solvent_ratio_value is None:
                return True  # No filter, accept all measurements

            # Check if measurement has a parameterValue matching the filter
            for param_val in measurement.parameterValue:
                if param_val.parameterID in solvent_ratio_param_ids:
                    # Use small tolerance for floating point comparison
                    if param_val.paramValue is not None:
                        if abs(param_val.paramValue - solvent_ratio_value) < 1e-6:
                            return True
            return False

        # Use fluid index as base group identifier
        # Each fluid already represents a unique composition (based on mole fractions)
        base_group_id = f"fluid_{fluid_idx}"

        if per_source:
            # Group by fluid AND source_doi
            # Process measurements and group by source_doi within this fluid
            for measurement in _get_measurements(fluid):
                # Apply solvent ratio filter if specified
                if not matches_solvent_ratio_filter(measurement):
                    continue

                source_doi = measurement.source_doi or "unknown_doi"

                # Create group ID combining fluid index and source_doi
                group_id = f"{base_group_id}_doi_{source_doi}"

                # Extract temperature and viscosity
                temperature = None
                viscosity = None

                for param_val in measurement.parameterValue:
                    param_def = parameter_lookup.get(param_val.parameterID)
                    if param_def and param_def.parameters:
                        param_name = str(
                            param_def.parameters.value
                            if hasattr(param_def.parameters, "value")
                            else param_def.parameters
                        )
                        if (
                            "temperature" in param_name.lower()
                            and param_val.paramValue is not None
                        ):
                            temperature = param_val.paramValue

                for prop_val in measurement.propertyValue:
                    prop_def = property_lookup.get(prop_val.propertyID)
                    if prop_def and prop_def.properties:
                        prop_name = str(
                            prop_def.properties.value
                            if hasattr(prop_def.properties, "value")
                            else prop_def.properties
                        )
                        if (
                            "viscosity" in prop_name.lower()
                            and prop_val.propValue is not None
                            and prop_val.propValue > 0
                        ):
                            viscosity = prop_val.propValue

                if temperature is not None and viscosity is not None:
                    grouped_data[group_id]["temperatures"].append(temperature)
                    grouped_data[group_id]["viscosities"].append(viscosity)
                    grouped_data[group_id]["source_dois"].add(source_doi)
                    if grouped_data[group_id]["compounds"] is None:
                        grouped_data[group_id]["compounds"] = fluid.compounds

                    # Extract mole fractions from this measurement (use first measurement to get composition)
                    if not grouped_data[group_id]["mole_fractions"]:
                        for param_val in measurement.parameterValue:
                            param_def = parameter_lookup.get(param_val.parameterID)
                            if param_def and param_def.parameters:
                                param_name = str(
                                    param_def.parameters.value
                                    if hasattr(param_def.parameters, "value")
                                    else param_def.parameters
                                )
                                if (
                                    "mole fraction" in param_name.lower()
                                    and param_val.paramValue is not None
                                ):
                                    # Extract compound name from parameterID
                                    param_id = param_val.parameterID
                                    # Parameter IDs are like "parameter_mole_fraction_water"
                                    # Extract the compound name
                                    if "mole_fraction_" in param_id:
                                        comp_name = param_id.split("mole_fraction_")[-1]
                                        grouped_data[group_id]["mole_fractions"][
                                            comp_name
                                        ] = param_val.paramValue
        else:
            # Group by fluid only (use all measurements from this fluid regardless of source_doi)
            group_id = base_group_id

            for measurement in _get_measurements(fluid):
                # Apply solvent ratio filter if specified
                if not matches_solvent_ratio_filter(measurement):
                    continue

                # Extract temperature and viscosity
                temperature = None
                viscosity = None

                for param_val in measurement.parameterValue:
                    param_def = parameter_lookup.get(param_val.parameterID)
                    if param_def and param_def.parameters:
                        param_name = str(
                            param_def.parameters.value
                            if hasattr(param_def.parameters, "value")
                            else param_def.parameters
                        )
                        if (
                            "temperature" in param_name.lower()
                            and param_val.paramValue is not None
                        ):
                            temperature = param_val.paramValue

                for prop_val in measurement.propertyValue:
                    prop_def = property_lookup.get(prop_val.propertyID)
                    if prop_def and prop_def.properties:
                        prop_name = str(
                            prop_def.properties.value
                            if hasattr(prop_def.properties, "value")
                            else prop_def.properties
                        )
                        if (
                            "viscosity" in prop_name.lower()
                            and prop_val.propValue is not None
                            and prop_val.propValue > 0
                        ):
                            viscosity = prop_val.propValue

                if temperature is not None and viscosity is not None:
                    grouped_data[group_id]["temperatures"].append(temperature)
                    grouped_data[group_id]["viscosities"].append(viscosity)
                    grouped_data[group_id]["source_dois"].add(measurement.source_doi)
                    if grouped_data[group_id]["compounds"] is None:
                        grouped_data[group_id]["compounds"] = fluid.compounds

                    # Extract mole fractions from this measurement (use first measurement to get composition)
                    if not grouped_data[group_id]["mole_fractions"]:
                        for param_val in measurement.parameterValue:
                            param_def = parameter_lookup.get(param_val.parameterID)
                            if param_def and param_def.parameters:
                                param_name = str(
                                    param_def.parameters.value
                                    if hasattr(param_def.parameters, "value")
                                    else param_def.parameters
                                )
                                if (
                                    "mole fraction" in param_name.lower()
                                    and param_val.paramValue is not None
                                ):
                                    # Extract compound name from parameterID
                                    param_id = param_val.parameterID
                                    # Parameter IDs are like "parameter_mole_fraction_water"
                                    # Extract the compound name
                                    if "mole_fraction_" in param_id:
                                        comp_name = param_id.split("mole_fraction_")[-1]
                                        grouped_data[group_id]["mole_fractions"][
                                            comp_name
                                        ] = param_val.paramValue

    # Calculate activation energy for each group
    results = {}

    for group_id, data in grouped_data.items():
        temperatures = np.array(data["temperatures"])
        viscosities = np.array(data["viscosities"])

        # Need at least 2 points for linear regression
        if len(temperatures) < 2:
            print(
                f"Warning: {group_id} has only {len(temperatures)} data point(s), skipping"
            )
            continue

        # Remove any invalid values
        valid_mask = (temperatures > 0) & (viscosities > 0)
        temperatures = temperatures[valid_mask]
        viscosities = viscosities[valid_mask]

        if len(temperatures) < 2:
            print(f"Warning: {group_id} has fewer than 2 valid data points, skipping")
            continue

        # Fit Arrhenius equation: ln(η) = ln(η₀) + (Ea/R) * (1/T)
        x = 1.0 / temperatures  # 1/T
        y = np.log(viscosities)  # ln(η)

        # Linear regression
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]  # Ea/R
        intercept = coeffs[1]  # ln(η₀)

        # Calculate R²
        y_pred = np.polyval(coeffs, x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Calculate activation energy
        activation_energy = slope * R  # J/mol
        eta0 = np.exp(intercept)  # mPa·s

        # Extract source_doi - for per_source=True, each group has single DOI
        # for per_source=False, may have multiple DOIs (set to None to indicate mixed)
        source_doi_result = None
        if per_source:
            # For per_source=True, each group should have exactly one DOI
            source_dois_list = list(data["source_dois"])
            source_doi_result = (
                source_dois_list[0] if len(source_dois_list) == 1 else None
            )
        else:
            # For per_source=False, set to None to indicate measurements may come from multiple sources
            source_doi_result = None

        # Extract water mole fraction (check various possible names)
        water_fraction = None
        mole_fractions_dict = data.get("mole_fractions", {})
        # Try various key formats that might represent water
        for key in mole_fractions_dict.keys():
            key_lower = key.lower()
            if "water" in key_lower:
                water_fraction = mole_fractions_dict[key]
                break

        # Extract individual mole fractions as separate columns
        # Create a dictionary with individual mole fraction columns
        mole_fraction_columns = {}
        for key, value in mole_fractions_dict.items():
            # Create column name: mole_fraction_<compound_name>
            column_name = f"mole_fraction_{key}"
            mole_fraction_columns[column_name] = value

        # Build results dictionary
        result_dict = {
            "activation_energy": activation_energy,
            "eta0": eta0,
            "r_squared": r_squared,
            "n_points": len(temperatures),
            "temperatures": temperatures.tolist(),
            "viscosities": viscosities.tolist(),
            "source_doi": source_doi_result,
            "compounds": data["compounds"],
            "mole_fractions": mole_fractions_dict,  # Keep original dict for backward compatibility
            "water_fraction": water_fraction,
        }

        # Add individual mole fraction columns
        result_dict.update(mole_fraction_columns)

        results[group_id] = result_dict

    # Convert to DataFrame if requested
    if return_dataframe:
        df_data = []
        for group_id, result in results.items():
            # Format compounds as comma-separated string
            compounds_str = (
                ", ".join(result["compounds"]) if result["compounds"] else "unknown"
            )

            # Format mole fractions as string (e.g., "compound1: 0.3333, compound2: 0.6667")
            mole_fractions_dict = result.get("mole_fractions", {})
            mole_fractions_str = ", ".join(
                [f"{k}: {v:.4f}" for k, v in mole_fractions_dict.items()]
            )
            if not mole_fractions_str:
                mole_fractions_str = "N/A"

            # Format source DOI(s)
            source_doi = result.get("source_doi")
            if source_doi:
                source_doi_str = source_doi
            else:
                # For per_source=False, may have multiple DOIs
                source_doi_str = "mixed"

            df_data.append(
                {
                    "Group ID": group_id,
                    "Compounds": compounds_str,
                    "Water Fraction": result.get("water_fraction"),
                    "Mole Fractions": mole_fractions_str,
                    "Activation Energy (J/mol)": result["activation_energy"],
                    "Activation Energy (kJ/mol)": result["activation_energy"] / 1000,
                    "η₀ (mPa·s)": result["eta0"],
                    "R²": result["r_squared"],
                    "N points": result["n_points"],
                    "Source DOI(s)": source_doi_str,
                }
            )

        df = pd.DataFrame(df_data)
        return df

    return results


def group_and_filter_measurements(
    df: pd.DataFrame,
    group_key: str = "source_doi",
    composition_filters: Optional[Dict[str, Union[float, Tuple[float, float]]]] = None,
    filter_before_grouping: bool = True,
    aggregations: Optional[Dict[str, Union[str, List[str]]]] = None,
    tolerance: float = 1e-6,
    dropna_group_key: bool = False,
) -> Union[pd.DataFrame, Any]:
    """
    Group measurement data by a key (e.g. DOI) with optional mole-fraction filters.

    This utility is intended for FAIRFluids DataFrames and supports both workflows:
    1) Filter composition first, then group by DOI
    2) Group by DOI first, then apply composition filter inside each DOI

    Args:
        df: Input DataFrame (e.g. output from visualization/filter utilities)
        group_key: Column name used for grouping (default: "source_doi")
        composition_filters: Dictionary of composition filters. Each key is a column
            name (e.g. "mole_fraction_water"). Value can be:
              - float: exact match within tolerance
              - (min, max): inclusive interval
        filter_before_grouping: If True, apply composition filters before grouping.
            If False, create groups first and then keep filtered rows within each group.
        aggregations: Optional pandas aggregation mapping. If provided, returns
            aggregated DataFrame. If None, returns a GroupBy object.
        tolerance: Absolute tolerance for exact-value composition filters.
        dropna_group_key: Passed to pandas groupby(dropna=...).

    Returns:
        If aggregations is None: pandas GroupBy object.
        If aggregations is provided: aggregated DataFrame with reset index.
    """
    if group_key not in df.columns:
        raise ValueError(
            f"Group key '{group_key}' not found. Available columns: {list(df.columns)}"
        )

    def _apply_composition_filters(frame: pd.DataFrame) -> pd.DataFrame:
        if not composition_filters:
            return frame

        filtered = frame.copy()
        for column, selector in composition_filters.items():
            if column not in filtered.columns:
                raise ValueError(
                    f"Composition column '{column}' not found. "
                    f"Available columns: {list(filtered.columns)}"
                )

            if isinstance(selector, tuple):
                if len(selector) != 2:
                    raise ValueError(
                        f"Range filter for '{column}' must be a (min, max) tuple."
                    )
                lower, upper = selector
                filtered = filtered[
                    filtered[column].between(lower, upper, inclusive="both")
                ]
            else:
                filtered = filtered[
                    (filtered[column] - float(selector)).abs() <= tolerance
                ]

        return filtered

    if filter_before_grouping:
        working_df = _apply_composition_filters(df)
        grouped = working_df.groupby(group_key, dropna=dropna_group_key)
    else:
        grouped = df.groupby(group_key, dropna=dropna_group_key)
        if composition_filters:
            grouped_frames = [
                _apply_composition_filters(group_frame) for _, group_frame in grouped
            ]
            grouped_frames = [g for g in grouped_frames if not g.empty]
            if grouped_frames:
                working_df = pd.concat(grouped_frames, ignore_index=True)
            else:
                working_df = df.iloc[0:0].copy()
            grouped = working_df.groupby(group_key, dropna=dropna_group_key)

    if aggregations is None:
        return grouped

    return grouped.agg(aggregations).reset_index()


def extract_property_dataframe(
    doc: FAIRFluidsDocument,
    property_type: str,
    components: Optional[List[str]] = None,
    target_ratio: Optional[float] = None,
    ratio_column: str = "Solvent: Amount ratio of component to other component of binary solvent",
    exact_component_match: bool = False,
    ratio_tolerance: float = 1e-6,
    include_na_ratio: bool = True,
    sort_by: Optional[str] = "temperature",
    ascending: bool = True,
    keep_only_relevant_columns: bool = True,
) -> pd.DataFrame:
    """
    Build a filtered DataFrame for a selected property, components, and optional ratio.

    Args:
        doc: FAIRFluids document.
        property_type: Property to select (e.g., "viscosity", "thermalConductivity", "density").
        components: Optional component names to filter for (case-insensitive). If provided:
            - exact_component_match=False: all listed components must be present
            - exact_component_match=True: fluid must contain exactly this set of components
        target_ratio: Optional numeric ratio value to filter by using ``ratio_column``.
        ratio_column: Column name for ratio filtering.
        exact_component_match: Whether component filtering should be exact set matching.
        ratio_tolerance: Absolute tolerance for numeric ratio comparison.
        include_na_ratio: If True and target_ratio is provided, keep rows where
            ratio_column is missing/NA in addition to matching target_ratio.
        sort_by: Optional column to sort by.
        ascending: Sort direction.
        keep_only_relevant_columns: If True, returns only a compact set of columns:
            fluid_compounds, mole_fractions, <property>_value, <property>_uncertainty,
            temperature, source_doi, ratio_column, mole_fraction_water (if available).

    Returns:
        Filtered pandas DataFrame.
    """
    from .visualization import extract_fairfluids_data

    df = extract_fairfluids_data(doc)
    if df.empty:
        return df

    # Keep only selected property type
    if "property_type" not in df.columns:
        raise ValueError(
            "Column 'property_type' missing in extracted data. "
            "Please verify extract_fairfluids_data output."
        )
    df = df[df["property_type"] == property_type].copy()
    if df.empty:
        return df

    # Build/refresh mole fraction columns dynamically from fluid_compounds + mole_fractions
    if "fluid_compounds" in df.columns and "mole_fractions" in df.columns:
        all_compounds = set()
        for comp_list in df["fluid_compounds"]:
            if isinstance(comp_list, list):
                all_compounds.update([str(c) for c in comp_list])

        for compound in sorted(all_compounds):
            col_name = f"mole_fraction_{compound}"

            def _extract_compound_fraction(row, target_compound=compound):
                comps = row.get("fluid_compounds")
                fracs = row.get("mole_fractions")
                if not isinstance(comps, list) or not isinstance(fracs, (list, tuple)):
                    return np.nan
                for idx, comp in enumerate(comps):
                    if str(comp).strip().lower() == target_compound.strip().lower():
                        return fracs[idx] if idx < len(fracs) else np.nan
                return np.nan

            df[col_name] = df.apply(_extract_compound_fraction, axis=1)

    # Component filtering
    if components:
        requested = [str(c).strip().lower() for c in components]

        def _matches_components(comp_list):
            if not isinstance(comp_list, list):
                return False
            available = [str(c).strip().lower() for c in comp_list]
            if exact_component_match:
                return set(available) == set(requested)
            return all(c in available for c in requested)

        df = df[df["fluid_compounds"].apply(_matches_components)].copy()
        if df.empty:
            return df

    # Ratio filtering
    if target_ratio is not None:
        if ratio_column not in df.columns:
            raise ValueError(
                f"Ratio column '{ratio_column}' not found. Available columns: {list(df.columns)}"
            )
        ratio_numeric = pd.to_numeric(df[ratio_column], errors="coerce")
        ratio_match = (ratio_numeric - float(target_ratio)).abs() <= ratio_tolerance
        if include_na_ratio:
            ratio_missing = ratio_numeric.isna()
            # Keep rows with requested ratio OR missing ratio values (NA).
            df = df[ratio_match | ratio_missing].copy()
        else:
            df = df[ratio_match].copy()

    # Optional sort
    if sort_by and sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=ascending)

    # Add a robust water mole fraction helper column if composition data is available
    if "fluid_compounds" in df.columns and "mole_fractions" in df.columns:

        def _extract_water_fraction(row):
            comps = row.get("fluid_compounds")
            fracs = row.get("mole_fractions")
            if not isinstance(comps, list) or not isinstance(fracs, (list, tuple)):
                return np.nan
            for idx, comp in enumerate(comps):
                comp_name = str(comp).strip().lower()
                if comp_name in {"water", "h2o"}:
                    return fracs[idx] if idx < len(fracs) else np.nan
            return np.nan

        df["mole_fraction_water"] = df.apply(_extract_water_fraction, axis=1)

    if keep_only_relevant_columns:
        property_value_col = f"{property_type}_value"
        property_uncertainty_col = f"{property_type}_uncertainty"
        desired_columns = [
            "fluid_compounds",
            "mole_fractions",
            property_value_col,
            property_uncertainty_col,
            "temperature",
            "source_doi",
            ratio_column,
            "mole_fraction_water",
        ]
        existing_columns = [col for col in desired_columns if col in df.columns]
        df = df[existing_columns].copy()

    return df


def fit_arrhenius(
    df: pd.DataFrame,
    viscosity_col: str = "viscosity_value",
    temperature_col: str = "temperature",
    doi_col: str = "source_doi",
    molefractions_col: str = "mole_fractions",
    include_water_mole_fraction: bool = False,
    water_col: str = "mole_fraction_water",
    t_range: Optional[Tuple[float, float]] = None,
    show_plot: bool = False,
    plot_figsize: Tuple[float, float] = (8, 5),
    plot_color_by: str = "source_doi",
    plot_cmap: str = "Blues",
    doi_plot_styles: Optional[dict[str, dict[str, str]]] = None,
    min_points: int = 2,
    molefrac_round: int = 6,
    log_base: str = "ln",
    viscosity_uncertainty_col: Optional[str] = None,
) -> pd.DataFrame:
    """
    Fit Arrhenius model per (DOI, mole-fraction) group on a DataFrame.

    Grouping order:
      1) source_doi
      2) mole_fractions

    Arrhenius form (fit axis x = 1/(R*T)):
      - ln(eta) = ln(As) + Ea * x

    Args:
        df: Input DataFrame containing viscosity/temperature/grouping columns.
        viscosity_col: Column with viscosity values (must be > 0).
        temperature_col: Column with absolute temperature in K (must be > 0).
        doi_col: Column used as first-level group key.
        molefractions_col: Column with sequence-like mole fractions (list/tuple).
        include_water_mole_fraction: If True, include water mole fraction per fitted
            group in result column ``mole_fraction_water``.
        water_col: Column name used when water mole fraction already exists in input.
        t_range: Optional inclusive temperature window in Kelvin as (T_min, T_max).
            Only points within this range are used for fitting.
        show_plot: If True, show a per-group Arrhenius fit plot for inspection.
        plot_figsize: Figure size used for inspection plots.
        plot_color_by: Color mapping for plots ("source_doi" or "mole_fraction_water").
        plot_cmap: Colormap used when plot_color_by="mole_fraction_water".
        doi_plot_styles: Optional custom style mapping for DOI-based plotting.
            Expected shape: {"doi": {"color": "#hex", "marker": "o"}, ...}.
            Used only when plot_color_by="source_doi"; missing entries fall back
            to deterministic default color and marker "o".
        min_points: Minimum number of points required per group for fitting.
        molefrac_round: Decimal rounding for stable mole-fraction grouping.
        log_base: Must be "ln". Other values are not supported.
        viscosity_uncertainty_col: Optionally, column name for viscosity uncertainty. Can be NaN/nonexistent.

    Returns:
        DataFrame with one row per fitted group and columns:
            - source_doi
            - mole_fractions
            - n_points
            - lnAs
            - As
            - Ea_J_mol
            - Ea_kJ_mol
            - lnAs_std
            - As_std
            - Ea_J_mol_std
            - Ea_kJ_mol_std
            - R_squared
            - slope
            - intercept
            - slope_std
            - intercept_std
            - T_min
            - T_max
            - viscosity_uncertainty (may be NaN if not available)
    """
    required_cols = [viscosity_col, temperature_col, doi_col, molefractions_col]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns for fit_arrhenius: {missing_cols}. "
            f"Available columns: {list(df.columns)}"
        )

    R = 8.314462618  # J/(mol*K)

    work = df.copy()
    work[viscosity_col] = pd.to_numeric(work[viscosity_col], errors="coerce")
    work[temperature_col] = pd.to_numeric(work[temperature_col], errors="coerce")

    if viscosity_uncertainty_col and viscosity_uncertainty_col in work.columns:
        work[viscosity_uncertainty_col] = pd.to_numeric(
            work[viscosity_uncertainty_col], errors="coerce"
        )

    work = work[
        work[viscosity_col].notna()
        & work[temperature_col].notna()
        & work[doi_col].notna()
        & (work[viscosity_col] > 0)
        & (work[temperature_col] > 0)
    ].copy()

    if t_range is not None:
        if not isinstance(t_range, (list, tuple)) or len(t_range) != 2:
            raise ValueError(
                "t_range must be a tuple/list with two values: (T_min, T_max)."
            )
        t_min, t_max = float(t_range[0]), float(t_range[1])
        if t_min > t_max:
            raise ValueError(
                f"Invalid t_range: T_min ({t_min}) must be <= T_max ({t_max})."
            )
        work = work[
            work[temperature_col].between(t_min, t_max, inclusive="both")
        ].copy()

    if include_water_mole_fraction and water_col not in work.columns:
        if "fluid_compounds" in work.columns:

            def _derive_water_fraction(row):
                fracs = row.get(molefractions_col)
                comps = row.get("fluid_compounds")
                if not isinstance(fracs, (list, tuple, np.ndarray)):
                    return np.nan
                if isinstance(comps, list):
                    for idx, comp in enumerate(comps):
                        if str(comp).strip().lower() in {"water", "h2o"}:
                            return fracs[idx] if idx < len(fracs) else np.nan
                return np.nan

            work[water_col] = work.apply(_derive_water_fraction, axis=1)

    def _normalize_molefractions(mf: Any):
        if isinstance(mf, (list, tuple, np.ndarray)):
            try:
                return tuple(round(float(x), molefrac_round) for x in mf)
            except (TypeError, ValueError):
                return np.nan
        return np.nan

    work["_mf_key"] = work[molefractions_col].apply(_normalize_molefractions)
    work = work[work["_mf_key"].notna()].copy()

    if log_base != "ln":
        raise ValueError(
            "fit_arrhenius supports only natural logarithm. "
            "Please set log_base='ln'."
        )

    results = []
    grouped = list(work.groupby([doi_col, "_mf_key"], dropna=False))
    if show_plot:
        import matplotlib.pyplot as plt
        from matplotlib import colors as mcolors
        from matplotlib.lines import Line2D

        fig, ax = plt.subplots(figsize=plot_figsize)
        cmap = plt.get_cmap(plot_cmap)
        water_for_color = (
            pd.to_numeric(work[water_col], errors="coerce")
            if water_col in work.columns
            else pd.Series(dtype=float)
        )
        has_water_colors = not water_for_color.empty and water_for_color.notna().any()
        if has_water_colors:
            w_min = float(water_for_color.min())
            w_max = float(water_for_color.max())
            if np.isclose(w_min, w_max):
                w_min = max(0.0, w_min - 1e-6)
                w_max = min(1.0, w_max + 1e-6)
            norm = mcolors.Normalize(vmin=w_min, vmax=w_max)
        else:
            norm = None

        if plot_color_by not in {"source_doi", "mole_fraction_water"}:
            raise ValueError(
                "plot_color_by must be 'source_doi' or 'mole_fraction_water'."
            )

        def _doi_style(doi_value: Any) -> dict[str, str]:
            doi_str = str(doi_value)
            if doi_plot_styles:
                if doi_str not in doi_plot_styles:
                    raise ValueError(
                        "Custom 'doi_plot_styles' is missing an entry for DOI: "
                        f"{doi_str}"
                    )
            return _get_doi_plot_style(doi_str, custom_styles=doi_plot_styles)

        def _group_color(doi_value, group_frame):
            if plot_color_by == "source_doi":
                return _doi_style(doi_value)["color"]
            water_values = (
                pd.to_numeric(group_frame[water_col], errors="coerce").dropna()
                if water_col in group_frame.columns
                else pd.Series(dtype=float)
            )
            water_value = (
                float(water_values.iloc[0]) if not water_values.empty else np.nan
            )
            if has_water_colors and np.isfinite(water_value):
                return cmap(norm(water_value))
            return "#9aa0a6"

    for group_idx, ((doi, mf_key), group) in enumerate(grouped):
        # Fit on inverse thermal energy axis: x = 1 / (R*T)
        x_model = 1.0 / (R * group[temperature_col].to_numpy(dtype=float))
        # Plot on the same axis convention as plot_viscosity: 1000/(R*T)
        x_plot = 1000.0 * x_model

        y = np.log(group[viscosity_col].to_numpy(dtype=float))
        y_label = "ln(eta)"

        if len(group) < min_points:
            if show_plot:
                doi_style = _doi_style(doi)
                color = _group_color(doi, group)
                ax.scatter(
                    x_plot,
                    y,
                    s=35,
                    alpha=0.8,
                    color=color,
                    marker=doi_style["marker"],
                    edgecolor="black",
                    linewidth=0.3,
                )
                ax.scatter(
                    x_plot,
                    y,
                    s=45,
                    alpha=0.9,
                    color=color,
                    marker=doi_style["marker"],
                )
            continue

        # Ordinary least squares (OLS) fit on ln(eta) vs 1/(R*T).
        slope_std = np.nan
        intercept_std = np.nan
        slope, intercept = np.polyfit(x_model, y, 1)
        # Approximate parameter standard deviations from covariance (if estimable).
        try:
            _, cov = np.polyfit(x_model, y, 1, cov=True)
            slope_std = (
                float(np.sqrt(cov[0, 0])) if np.isfinite(cov[0, 0]) else np.nan
            )
            intercept_std = (
                float(np.sqrt(cov[1, 1])) if np.isfinite(cov[1, 1]) else np.nan
            )
        except (TypeError, ValueError, np.linalg.LinAlgError):
            slope_std = np.nan
            intercept_std = np.nan
        # With x = 1/(R*T), slope directly equals Ea [J/mol].
        ea_j_mol = slope
        log_as = intercept  # ln(As)
        as_value = np.exp(intercept)
        ea_j_mol_std = slope_std if np.isfinite(slope_std) else np.nan
        ea_kj_mol_std = ea_j_mol_std / 1000.0 if np.isfinite(ea_j_mol_std) else np.nan
        ln_as_std = intercept_std if np.isfinite(intercept_std) else np.nan
        as_std = as_value * ln_as_std if np.isfinite(ln_as_std) else np.nan

        y_pred = slope * x_model + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = np.nan if ss_tot == 0 else 1.0 - (ss_res / ss_tot)

        # A) Uncertainty handling for DataFrame output:
        viscosity_uncertainty = np.nan
        if viscosity_uncertainty_col and viscosity_uncertainty_col in group.columns:
            unc_vals = pd.to_numeric(
                group[viscosity_uncertainty_col], errors="coerce"
            ).dropna()
            if not unc_vals.empty:
                # Use mean (could choose min, max, or first too), but document
                viscosity_uncertainty = float(unc_vals.mean())
            else:
                viscosity_uncertainty = np.nan

        row = {
            "source_doi": doi,
            "mole_fractions": mf_key,
            "n_points": len(group),
            "lnAs": log_as,
            "As": as_value,
            "Ea_J_mol": ea_j_mol,
            "Ea_kJ_mol": ea_j_mol / 1000.0,
            "lnAs_std": ln_as_std,
            "As_std": as_std,
            "Ea_J_mol_std": ea_j_mol_std,
            "Ea_kJ_mol_std": ea_kj_mol_std,
            "R_squared": r_squared,
            "slope": slope,
            "intercept": intercept,
            "slope_std": slope_std,
            "intercept_std": intercept_std,
            "T_min": float(group[temperature_col].min()),
            "T_max": float(group[temperature_col].max()),
        }
        if viscosity_uncertainty_col:
            row["viscosity_uncertainty"] = viscosity_uncertainty
        if include_water_mole_fraction and water_col in group.columns:
            water_values = pd.to_numeric(group[water_col], errors="coerce").dropna()
            row["mole_fraction_water"] = (
                float(water_values.iloc[0]) if not water_values.empty else np.nan
            )

        results.append(row)

        # B) Plotting: Only plot error bars if uncertainty is present and not NaN for each point
        if show_plot:
            doi_style = _doi_style(doi)
            color = _group_color(doi, group)
            marker = doi_style["marker"] if plot_color_by == "source_doi" else "o"
            x_fit_plot = np.linspace(np.min(x_plot), np.max(x_plot), 100)
            y_fit = slope * (x_fit_plot / 1000.0) + intercept

            if viscosity_uncertainty_col and viscosity_uncertainty_col in group.columns:
                # Convert uncertainty to array (log space error propagation)
                unc_vec = pd.to_numeric(
                    group[viscosity_uncertainty_col], errors="coerce"
                ).to_numpy()
                # propagate to ln space: d(ln(eta)) = d(eta)/eta
                visc_arr = group[viscosity_col].to_numpy(dtype=float)
                dy = np.divide(
                    unc_vec,
                    visc_arr,
                    out=np.full_like(unc_vec, np.nan),
                    where=visc_arr != 0,
                )
                # Only plot errorbars for points where dy is finite
                mask_valid = np.isfinite(dy) & np.isfinite(x_plot) & np.isfinite(y)
                if np.any(mask_valid):
                    ax.errorbar(
                        x_plot[mask_valid],
                        y[mask_valid],
                        yerr=dy[mask_valid],
                        fmt=marker,
                        ms=4,
                        alpha=0.8,
                        color=color,
                        ecolor=color,
                        elinewidth=1.2,
                        capsize=3,
                        capthick=1,
                        markeredgecolor="black",
                        markeredgewidth=0.2,
                        label=None if plot_color_by == "source_doi" else None,
                        zorder=11,
                    )
                if np.any(~mask_valid):
                    ax.scatter(
                        x_plot[~mask_valid],
                        y[~mask_valid],
                        s=30,
                        alpha=0.8,
                        color=color,
                        marker=marker,
                        edgecolor="black",
                        linewidth=0.2,
                        zorder=10,
                    )
            else:
                ax.scatter(
                    x_plot,
                    y,
                    s=30,
                    alpha=0.8,
                    color=color,
                    marker=marker,
                    edgecolor="black",
                    linewidth=0.2,
                    zorder=10,
                )
            ax.plot(
                x_fit_plot, y_fit, linestyle="--", linewidth=1.8, color=color, zorder=5
            )

    result_df = pd.DataFrame(results)
    if show_plot:
        ax.set_title(r"Plot of ln($\eta$) vs (RT)$^{-1}$")
        ax.set_xlabel(r"(RT)$^{-1}$ / mol kJ$^{-1}$")
        ax.set_ylabel(r"ln($\eta$ / $Pa \cdot s$)")
        ax.grid(alpha=0.2)
        if plot_color_by == "source_doi":
            doi_values = sorted(work[doi_col].dropna().astype(str).unique())
            handles = [
                Line2D(
                    [0],
                    [0],
                    marker=_doi_style(doi)["marker"],
                    linestyle="None",
                    markerfacecolor=_doi_style(doi)["color"],
                    markeredgecolor="black",
                    markeredgewidth=0.3,
                    markersize=6,
                    label=doi,
                )
                for doi in doi_values
            ]
            ax.legend(
                handles=handles,
                title="DOI",
                bbox_to_anchor=(1.02, 1),
                loc="upper left",
                fontsize=8,
                title_fontsize=9,
            )
        elif plot_color_by == "mole_fraction_water" and has_water_colors:
            sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
            sm.set_array([])
            cbar = plt.colorbar(sm, ax=ax, pad=0.01)
            cbar.set_label("Water mole fraction")
        plt.tight_layout()
        plt.show()
    if not result_df.empty:
        result_df = result_df.sort_values(
            by=["source_doi", "mole_fractions"]
        ).reset_index(drop=True)
    return result_df


def fit_extended_arrhenius(
    df: pd.DataFrame,
    k_col: str = "viscosity_value",
    temperature_col: str = "temperature",
    doi_col: str = "source_doi",
    molefractions_col: str = "mole_fractions",
    include_water_mole_fraction: bool = False,
    water_col: str = "mole_fraction_water",
    t_range: Optional[Tuple[float, float]] = None,
    show_plot: bool = False,
    plot_figsize: Tuple[float, float] = (8, 5),
    plot_color_by: str = "source_doi",
    plot_cmap: str = "Blues",
    min_points: int = 3,
    molefrac_round: int = 6,
) -> pd.DataFrame:
    """
    Fit extended Arrhenius model for viscosity eta per (DOI, mole-fraction) group on a DataFrame.

    Model:
        eta = B * T^n * exp(Ea / (R*T))

    Linearized form used for fitting:
        ln(eta) = ln(B) + n*ln(T) + Ea/(R*T)

    Grouping order:
      1) source_doi
      2) mole_fractions

    Args:
        df: Input DataFrame containing viscosity/temperature/grouping columns.
        k_col: Column with positive viscosity values (eta).
        temperature_col: Column with absolute temperature in K (must be > 0).
        doi_col: Column used as first-level group key.
        molefractions_col: Column with sequence-like mole fractions (list/tuple).
        include_water_mole_fraction: If True, include water mole fraction per fitted
            group in result column ``mole_fraction_water``.
        water_col: Column name used when water mole fraction already exists in input.
        t_range: Optional inclusive temperature window in Kelvin as (T_min, T_max).
            Only points within this range are used for fitting.
        show_plot: If True, show a combined plot with all group fits.
        plot_figsize: Figure size used for inspection plots.
        plot_color_by: Color mapping for plots ("source_doi" or "mole_fraction_water").
        plot_cmap: Colormap used when plot_color_by="mole_fraction_water".
        min_points: Minimum number of points required per group for fitting.
            For this model, at least 3 points are recommended.
        molefrac_round: Decimal rounding for stable mole-fraction grouping.

    Returns:
        DataFrame with one row per fitted group and columns:
            - source_doi
            - mole_fractions
            - n_points
            - B
            - n
            - Ea_J_mol
            - Ea_kJ_mol
            - R_squared
            - lnB
            - T_min
            - T_max
            - mole_fraction_water (optional)
    """
    required_cols = [k_col, temperature_col, doi_col, molefractions_col]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns for fit_extended_arrhenius: {missing_cols}. "
            f"Available columns: {list(df.columns)}"
        )

    R = 8.314462618  # J/(mol*K)

    work = df.copy()
    work[k_col] = pd.to_numeric(work[k_col], errors="coerce")
    work[temperature_col] = pd.to_numeric(work[temperature_col], errors="coerce")

    work = work[
        work[k_col].notna()
        & work[temperature_col].notna()
        & work[doi_col].notna()
        & (work[k_col] > 0)
        & (work[temperature_col] > 0)
    ].copy()

    if t_range is not None:
        if not isinstance(t_range, (list, tuple)) or len(t_range) != 2:
            raise ValueError(
                "t_range must be a tuple/list with two values: (T_min, T_max)."
            )
        t_min, t_max = float(t_range[0]), float(t_range[1])
        if t_min > t_max:
            raise ValueError(
                f"Invalid t_range: T_min ({t_min}) must be <= T_max ({t_max})."
            )
        work = work[
            work[temperature_col].between(t_min, t_max, inclusive="both")
        ].copy()

    if include_water_mole_fraction and water_col not in work.columns:
        if "fluid_compounds" in work.columns:

            def _derive_water_fraction(row):
                fracs = row.get(molefractions_col)
                comps = row.get("fluid_compounds")
                if not isinstance(fracs, (list, tuple, np.ndarray)):
                    return np.nan
                if isinstance(comps, list):
                    for idx, comp in enumerate(comps):
                        if str(comp).strip().lower() in {"water", "h2o"}:
                            return fracs[idx] if idx < len(fracs) else np.nan
                return np.nan

            work[water_col] = work.apply(_derive_water_fraction, axis=1)

    def _normalize_molefractions(mf: Any):
        if isinstance(mf, (list, tuple, np.ndarray)):
            try:
                return tuple(round(float(x), molefrac_round) for x in mf)
            except (TypeError, ValueError):
                return np.nan
        return np.nan

    work["_mf_key"] = work[molefractions_col].apply(_normalize_molefractions)
    work = work[work["_mf_key"].notna()].copy()

    results = []
    grouped = list(work.groupby([doi_col, "_mf_key"], dropna=False))
    if show_plot:
        import matplotlib.pyplot as plt
        from matplotlib import colors as mcolors
        from matplotlib.lines import Line2D

        fig, ax = plt.subplots(figsize=plot_figsize)
        cmap = plt.get_cmap(plot_cmap)
        water_for_color = (
            pd.to_numeric(work[water_col], errors="coerce")
            if water_col in work.columns
            else pd.Series(dtype=float)
        )
        has_water_colors = not water_for_color.empty and water_for_color.notna().any()
        if has_water_colors:
            w_min = float(water_for_color.min())
            w_max = float(water_for_color.max())
            if np.isclose(w_min, w_max):
                w_min = max(0.0, w_min - 1e-6)
                w_max = min(1.0, w_max + 1e-6)
            norm = mcolors.Normalize(vmin=w_min, vmax=w_max)
        else:
            norm = None

        if plot_color_by not in {"source_doi", "mole_fraction_water"}:
            raise ValueError(
                "plot_color_by must be 'source_doi' or 'mole_fraction_water'."
            )

        def _group_color(doi_value, group_frame):
            if plot_color_by == "source_doi":
                return _string_to_hex_color(str(doi_value))
            water_values = (
                pd.to_numeric(group_frame[water_col], errors="coerce").dropna()
                if water_col in group_frame.columns
                else pd.Series(dtype=float)
            )
            water_value = (
                float(water_values.iloc[0]) if not water_values.empty else np.nan
            )
            if has_water_colors and np.isfinite(water_value):
                return cmap(norm(water_value))
            return "#9aa0a6"

    for group_idx, ((doi, mf_key), group) in enumerate(grouped):
        t = group[temperature_col].to_numpy(dtype=float)
        k = group[k_col].to_numpy(dtype=float)

        # Linear model: y = a0 + a1*x1 + a2*x2
        # y = ln(eta), x1 = ln(T), x2 = 1/T
        y = np.log(k)

        if len(group) < min_points:
            if show_plot:
                color = _group_color(doi, group)
                x_plot = 1.0 / (R * t)
                ax.scatter(
                    x_plot,
                    y,
                    s=45,
                    alpha=0.9,
                    color=color,
                    marker="x",
                )
            continue

        x1 = np.log(t)
        x2 = 1.0 / t
        x = np.column_stack([np.ones_like(t), x1, x2])

        coeffs, _, _, _ = np.linalg.lstsq(x, y, rcond=None)
        ln_b, n_value, coeff_inv_t = coeffs

        # coeff_inv_t = Ea/R
        ea_j_mol = coeff_inv_t * R
        b_value = float(np.exp(ln_b))

        y_pred = x @ coeffs
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = np.nan if ss_tot == 0 else 1.0 - (ss_res / ss_tot)

        if show_plot:
            color = _group_color(doi, group)
            t_fit = np.linspace(np.min(t), np.max(t), 120)
            y_fit = ln_b + n_value * np.log(t_fit) + (ea_j_mol / (R * t_fit))
            x_plot = 1.0 / (R * t)
            x_fit = 1.0 / (R * t_fit)
            order = np.argsort(x_plot)
            fit_order = np.argsort(x_fit)
            ax.scatter(
                x_plot[order],
                y[order],
                s=30,
                alpha=0.8,
                color=color,
                edgecolor="black",
                linewidth=0.2,
            )
            ax.plot(
                x_fit[fit_order],
                y_fit[fit_order],
                linestyle="--",
                linewidth=1.8,
                color=color,
            )

        row = {
            "source_doi": doi,
            "mole_fractions": mf_key,
            "n_points": len(group),
            "B": b_value,
            "n": float(n_value),
            "Ea_J_mol": float(ea_j_mol),
            "Ea_kJ_mol": float(ea_j_mol / 1000.0),
            "R_squared": float(r_squared) if not np.isnan(r_squared) else np.nan,
            "lnB": float(ln_b),
            "T_min": float(group[temperature_col].min()),
            "T_max": float(group[temperature_col].max()),
        }
        if include_water_mole_fraction and water_col in group.columns:
            water_values = pd.to_numeric(group[water_col], errors="coerce").dropna()
            row["mole_fraction_water"] = (
                float(water_values.iloc[0]) if not water_values.empty else np.nan
            )

        results.append(row)

    result_df = pd.DataFrame(results)
    if show_plot:
        ax.set_xlabel("1/(R*T) [mol/J]")
        ax.set_ylabel("ln(eta)")
        ax.set_title("Extended Arrhenius fits (all groups)")
        ax.grid(alpha=0.2)
        if plot_color_by == "source_doi":
            doi_values = sorted(work[doi_col].dropna().astype(str).unique())
            handles = [
                Line2D(
                    [0],
                    [0],
                    marker="o",
                    linestyle="None",
                    markerfacecolor=_string_to_hex_color(doi),
                    markeredgecolor="black",
                    markeredgewidth=0.3,
                    markersize=6,
                    label=doi,
                )
                for doi in doi_values
            ]
            ax.legend(
                handles=handles,
                title="DOI",
                bbox_to_anchor=(1.02, 1),
                loc="upper left",
                fontsize=8,
                title_fontsize=9,
            )
        elif plot_color_by == "mole_fraction_water" and has_water_colors:
            sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
            sm.set_array([])
            cbar = plt.colorbar(sm, ax=ax, pad=0.01)
            cbar.set_label("Water mole fraction")
        plt.tight_layout()
        plt.show()
    if not result_df.empty:
        result_df = result_df.sort_values(
            by=["source_doi", "mole_fractions"]
        ).reset_index(drop=True)
    return result_df


def fit_vft(
    df: pd.DataFrame,
    viscosity_col: str = "viscosity_value",
    temperature_col: str = "temperature",
    doi_col: str = "source_doi",
    molefractions_col: str = "mole_fractions",
    include_water_mole_fraction: bool = False,
    water_col: str = "mole_fraction_water",
    t_range: Optional[Tuple[float, float]] = None,
    show_plot: bool = False,
    plot_figsize: Tuple[float, float] = (8, 5),
    plot_color_by: str = "source_doi",
    plot_cmap: str = "Blues",
    doi_plot_styles: Optional[dict[str, dict[str, str]]] = None,
    min_points: int = 4,
    molefrac_round: int = 6,
    initial_guesses: Optional[Dict[str, float]] = None,
    viscosity_uncertainty_col: Optional[str] = None,
) -> pd.DataFrame:
    """
    Fit 3-parameter Vogel-Fulcher-Tammann (VFT) model for viscosity per group.

    Model:
        eta(T) = eta0 * exp(B / (T - T0))

    Equivalent log form used in fitting:
        ln(eta) = ln(eta0) + B / (T - T0)

    Grouping order:
      1) source_doi
      2) mole_fractions

    Args:
        df: Input DataFrame containing viscosity/temperature/grouping columns.
        viscosity_col: Column with positive viscosity values eta.
        temperature_col: Column with absolute temperature in K (must be > 0).
        doi_col: Column used as first-level group key.
        molefractions_col: Column with sequence-like mole fractions (list/tuple).
        include_water_mole_fraction: If True, include water mole fraction per fitted
            group in result column ``mole_fraction_water``.
        water_col: Column name used when water mole fraction already exists in input.
        t_range: Optional inclusive temperature window in Kelvin as (T_min, T_max).
            Only points within this range are used for fitting.
        show_plot: If True, show a combined plot with all group fits.
        plot_figsize: Figure size used for inspection plots.
        plot_color_by: Color mapping for plots ("source_doi" or "mole_fraction_water").
        plot_cmap: Colormap used when plot_color_by="mole_fraction_water".
        doi_plot_styles: Optional custom style mapping for DOI-based plotting.
            Expected shape: {"doi": {"color": "#hex", "marker": "o"}, ...}.
            Used only when plot_color_by="source_doi"; missing entries fall back
            to deterministic default color and marker "o".
        min_points: Minimum number of points required per group for fitting.
            For this model, at least 4 points are recommended.
        molefrac_round: Decimal rounding for stable mole-fraction grouping.
        initial_guesses: Optional dictionary with initial guesses for fitting parameters.
            Keys: "ln_eta0", "B", "T0". If not provided, automatic guesses are used.
        viscosity_uncertainty_col: Optionally, column name for viscosity uncertainty.
            If provided, weighted fitting in log-space is attempted using
            dln(eta)=deta/eta, and uncertainty-aware error bars are shown in plots.

    Returns:
        DataFrame with one row per fitted group and columns:
            - source_doi
            - mole_fractions
            - n_points
            - eta0
            - ln_eta0
            - B
            - T0
            - eta0_std
            - ln_eta0_std
            - B_std
            - T0_std
            - R_squared
            - T_min
            - T_max
            - viscosity_uncertainty (if viscosity_uncertainty_col was provided)
            - mole_fraction_water (optional)
    """
    required_cols = [viscosity_col, temperature_col, doi_col, molefractions_col]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns for fit_vft: {missing_cols}. "
            f"Available columns: {list(df.columns)}"
        )

    R = 8.314462618  # J/(mol*K), only used for x-axis transformation in plots

    work = df.copy()
    work[viscosity_col] = pd.to_numeric(work[viscosity_col], errors="coerce")
    work[temperature_col] = pd.to_numeric(work[temperature_col], errors="coerce")
    if viscosity_uncertainty_col and viscosity_uncertainty_col in work.columns:
        work[viscosity_uncertainty_col] = pd.to_numeric(
            work[viscosity_uncertainty_col], errors="coerce"
        )

    work = work[
        work[viscosity_col].notna()
        & work[temperature_col].notna()
        & work[doi_col].notna()
        & (work[viscosity_col] > 0)
        & (work[temperature_col] > 0)
    ].copy()

    if t_range is not None:
        if not isinstance(t_range, (list, tuple)) or len(t_range) != 2:
            raise ValueError(
                "t_range must be a tuple/list with two values: (T_min, T_max)."
            )
        t_min, t_max = float(t_range[0]), float(t_range[1])
        if t_min > t_max:
            raise ValueError(
                f"Invalid t_range: T_min ({t_min}) must be <= T_max ({t_max})."
            )
        work = work[
            work[temperature_col].between(t_min, t_max, inclusive="both")
        ].copy()

    if include_water_mole_fraction and water_col not in work.columns:
        if "fluid_compounds" in work.columns:

            def _derive_water_fraction(row):
                fracs = row.get(molefractions_col)
                comps = row.get("fluid_compounds")
                if not isinstance(fracs, (list, tuple, np.ndarray)):
                    return np.nan
                if isinstance(comps, list):
                    for idx, comp in enumerate(comps):
                        if str(comp).strip().lower() in {"water", "h2o"}:
                            return fracs[idx] if idx < len(fracs) else np.nan
                return np.nan

            work[water_col] = work.apply(_derive_water_fraction, axis=1)

    def _normalize_molefractions(mf: Any):
        if isinstance(mf, (list, tuple, np.ndarray)):
            try:
                return tuple(round(float(x), molefrac_round) for x in mf)
            except (TypeError, ValueError):
                return np.nan
        return np.nan

    work["_mf_key"] = work[molefractions_col].apply(_normalize_molefractions)
    work = work[work["_mf_key"].notna()].copy()

    def _vft_log_model(t, ln_eta0, b_value, t0):
        return ln_eta0 + (b_value / (t - t0))

    results = []
    grouped = list(work.groupby([doi_col, "_mf_key"], dropna=False))

    if show_plot:
        import matplotlib.pyplot as plt
        from matplotlib import colors as mcolors
        from matplotlib.lines import Line2D

        fig, ax = plt.subplots(figsize=plot_figsize)
        cmap = plt.get_cmap(plot_cmap)
        water_for_color = (
            pd.to_numeric(work[water_col], errors="coerce")
            if water_col in work.columns
            else pd.Series(dtype=float)
        )
        has_water_colors = not water_for_color.empty and water_for_color.notna().any()
        if has_water_colors:
            w_min = float(water_for_color.min())
            w_max = float(water_for_color.max())
            if np.isclose(w_min, w_max):
                w_min = max(0.0, w_min - 1e-6)
                w_max = min(1.0, w_max + 1e-6)
            norm = mcolors.Normalize(vmin=w_min, vmax=w_max)
        else:
            norm = None

        if plot_color_by not in {"source_doi", "mole_fraction_water"}:
            raise ValueError(
                "plot_color_by must be 'source_doi' or 'mole_fraction_water'."
            )

        def _doi_style(doi_value: Any) -> dict[str, str]:
            doi_str = str(doi_value)
            fallback = {"color": _string_to_hex_color(doi_str), "marker": "o"}
            if not doi_plot_styles:
                return fallback
            style = doi_plot_styles.get(doi_str, {})
            color = style.get("color", fallback["color"])
            marker = style.get("marker", fallback["marker"])
            return {"color": color, "marker": marker}

        def _group_color(doi_value, group_frame):
            if plot_color_by == "source_doi":
                return _doi_style(doi_value)["color"]
            water_values = (
                pd.to_numeric(group_frame[water_col], errors="coerce").dropna()
                if water_col in group_frame.columns
                else pd.Series(dtype=float)
            )
            water_value = (
                float(water_values.iloc[0]) if not water_values.empty else np.nan
            )
            if has_water_colors and np.isfinite(water_value):
                return cmap(norm(water_value))
            return "#9aa0a6"

    for group_idx, ((doi, mf_key), group) in enumerate(grouped):
        t = group[temperature_col].to_numpy(dtype=float)
        eta = group[viscosity_col].to_numpy(dtype=float)
        y = np.log(eta)

        if len(group) < min_points:
            if show_plot:
                doi_style = _doi_style(doi)
                color = _group_color(doi, group)
                x_plot = 1.0 / (R * t)
                ax.scatter(
                    x_plot,
                    y,
                    s=45,
                    alpha=0.9,
                    color=color,
                    marker=doi_style["marker"],
                )
            continue

        # Initial guesses and bounds (ensure T0 < min(T))
        min_t = float(np.min(t))
        if initial_guesses is not None:
            ln_eta0_guess = initial_guesses.get("ln_eta0", float(np.min(y)))
            b_guess = initial_guesses.get("B", 1000.0)
            t0_guess = initial_guesses.get("T0", min_t - 50.0)
        else:
            ln_eta0_guess = float(np.min(y))
            b_guess = 1000.0
            t0_guess = min_t - 50.0

        t0_upper = min_t - 1e-6
        if not np.isfinite(t0_upper):
            t0_upper = min_t - 1e-3

        lower_bounds = [-np.inf, 0.0, -np.inf]
        upper_bounds = [np.inf, np.inf, t0_upper]

        try:
            from scipy.optimize import curve_fit

            sigma = None
            fit_kwargs = {}
            if viscosity_uncertainty_col and viscosity_uncertainty_col in group.columns:
                unc_vec = pd.to_numeric(
                    group[viscosity_uncertainty_col], errors="coerce"
                ).to_numpy(dtype=float)
                sigma_candidate = np.divide(
                    unc_vec,
                    eta,
                    out=np.full_like(unc_vec, np.nan, dtype=float),
                    where=eta != 0,
                )
                valid_sigma = np.isfinite(sigma_candidate) & (sigma_candidate > 0)
                if np.any(valid_sigma):
                    sigma = sigma_candidate
                    fit_kwargs["sigma"] = sigma
                    fit_kwargs["absolute_sigma"] = True

            popt, pcov = curve_fit(
                _vft_log_model,
                t,
                y,
                p0=[ln_eta0_guess, b_guess, t0_guess],
                bounds=(lower_bounds, upper_bounds),
                maxfev=20000,
                **fit_kwargs,
            )
            ln_eta0, b_value, t0 = popt
            param_std = np.sqrt(np.diag(pcov)) if pcov is not None else np.array([np.nan, np.nan, np.nan])
            ln_eta0_std = float(param_std[0]) if np.isfinite(param_std[0]) else np.nan
            b_std = float(param_std[1]) if np.isfinite(param_std[1]) else np.nan
            t0_std = float(param_std[2]) if np.isfinite(param_std[2]) else np.nan
        except Exception:
            # Skip non-converged groups silently in the returned fit table;
            # still show points in plot if requested.
            if show_plot:
                doi_style = _doi_style(doi)
                color = _group_color(doi, group)
                x_plot = 1.0 / (R * t)
                ax.scatter(
                    x_plot,
                    y,
                    s=45,
                    alpha=0.9,
                    color=color,
                    marker=doi_style["marker"],
                )
            continue

        y_pred = _vft_log_model(t, ln_eta0, b_value, t0)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = np.nan if ss_tot == 0 else 1.0 - (ss_res / ss_tot)

        eta0 = float(np.exp(ln_eta0))
        eta0_std = eta0 * ln_eta0_std if np.isfinite(ln_eta0_std) else np.nan
        viscosity_uncertainty = np.nan
        if viscosity_uncertainty_col and viscosity_uncertainty_col in group.columns:
            unc_vals = pd.to_numeric(
                group[viscosity_uncertainty_col], errors="coerce"
            ).dropna()
            if not unc_vals.empty:
                viscosity_uncertainty = float(unc_vals.mean())

        if show_plot:
            doi_style = _doi_style(doi)
            color = _group_color(doi, group)
            marker = doi_style["marker"] if plot_color_by == "source_doi" else "o"
            t_fit = np.linspace(np.min(t), np.max(t), 180)
            y_fit = _vft_log_model(t_fit, ln_eta0, b_value, t0)

            x_plot = 1.0 / (R * t)
            x_fit = 1.0 / (R * t_fit)
            order = np.argsort(x_plot)
            fit_order = np.argsort(x_fit)

            if viscosity_uncertainty_col and viscosity_uncertainty_col in group.columns:
                unc_vec = pd.to_numeric(
                    group[viscosity_uncertainty_col], errors="coerce"
                ).to_numpy(dtype=float)
                dy = np.divide(
                    unc_vec,
                    eta,
                    out=np.full_like(unc_vec, np.nan, dtype=float),
                    where=eta != 0,
                )
                mask_valid = np.isfinite(dy) & np.isfinite(x_plot) & np.isfinite(y)
                if np.any(mask_valid):
                    mask_sorted = np.argsort(x_plot[mask_valid])
                    x_ok = x_plot[mask_valid][mask_sorted]
                    y_ok = y[mask_valid][mask_sorted]
                    dy_ok = dy[mask_valid][mask_sorted]
                    ax.errorbar(
                        x_ok,
                        y_ok,
                        yerr=dy_ok,
                        fmt=marker,
                        ms=4,
                        alpha=0.8,
                        color=color,
                        ecolor=color,
                        elinewidth=1.1,
                        capsize=3,
                        markeredgecolor="black",
                        markeredgewidth=0.2,
                        zorder=10,
                    )
                if np.any(~mask_valid):
                    mask_sorted = np.argsort(x_plot[~mask_valid])
                    ax.scatter(
                        x_plot[~mask_valid][mask_sorted],
                        y[~mask_valid][mask_sorted],
                        s=30,
                        alpha=0.8,
                        color=color,
                        marker=marker,
                        edgecolor="black",
                        linewidth=0.2,
                        zorder=9,
                    )
            else:
                ax.scatter(
                    x_plot[order],
                    y[order],
                    s=30,
                    alpha=0.8,
                    color=color,
                    marker=marker,
                    edgecolor="black",
                    linewidth=0.2,
                )
            ax.plot(
                x_fit[fit_order],
                y_fit[fit_order],
                linestyle="--",
                linewidth=1.8,
                color=color,
            )

        row = {
            "source_doi": doi,
            "mole_fractions": mf_key,
            "n_points": len(group),
            "eta0": eta0,
            "ln_eta0": float(ln_eta0),
            "B": float(b_value),
            "T0": float(t0),
            "eta0_std": eta0_std,
            "ln_eta0_std": ln_eta0_std,
            "B_std": b_std,
            "T0_std": t0_std,
            "R_squared": float(r_squared) if not np.isnan(r_squared) else np.nan,
            "T_min": float(group[temperature_col].min()),
            "T_max": float(group[temperature_col].max()),
        }
        if viscosity_uncertainty_col:
            row["viscosity_uncertainty"] = viscosity_uncertainty
        if include_water_mole_fraction and water_col in group.columns:
            water_values = pd.to_numeric(group[water_col], errors="coerce").dropna()
            row["mole_fraction_water"] = (
                float(water_values.iloc[0]) if not water_values.empty else np.nan
            )

        results.append(row)

    result_df = pd.DataFrame(results)
    if show_plot:
        ax.set_xlabel("1/(R*T) [mol/J]")
        ax.set_ylabel("ln(eta)")
        ax.set_title("VFT (3-parameter) fits (all groups)")
        ax.grid(alpha=0.2)
        if plot_color_by == "source_doi":
            doi_values = sorted(work[doi_col].dropna().astype(str).unique())
            handles = [
                Line2D(
                    [0],
                    [0],
                    marker=_doi_style(doi)["marker"],
                    linestyle="None",
                    markerfacecolor=_doi_style(doi)["color"],
                    markeredgecolor="black",
                    markeredgewidth=0.3,
                    markersize=6,
                    label=doi,
                )
                for doi in doi_values
            ]
            ax.legend(
                handles=handles,
                title="DOI",
                bbox_to_anchor=(1.02, 1),
                loc="upper left",
                fontsize=8,
                title_fontsize=9,
            )
        elif plot_color_by == "mole_fraction_water" and has_water_colors:
            sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
            sm.set_array([])
            cbar = plt.colorbar(sm, ax=ax, pad=0.01)
            cbar.set_label("Water mole fraction")
        plt.tight_layout()
        plt.show()

    if not result_df.empty:
        result_df = result_df.sort_values(
            by=["source_doi", "mole_fractions"]
        ).reset_index(drop=True)
    return result_df
