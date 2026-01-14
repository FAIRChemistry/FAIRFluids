import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

# Note: The old filtering function has been removed as the new composition-based approach
# automatically creates separate fluid blocks for each unique composition, containing
# only the compounds present in that specific composition.


def get_fluid_composition_summary(doc):
    """
    Get a summary of all fluid compositions in a FAIRFluids document.

    This function is particularly useful for the new composition-based approach
    where each fluid block represents a unique composition.

    Args:
        doc: FAIRFluidsDocument

    Returns:
        dict: Summary containing:
            - total_fluids: Number of fluid blocks
            - compositions: List of composition dictionaries
            - compound_combinations: Set of unique compound combinations
            - property_types: Set of all property types found
    """
    summary = {
        "total_fluids": len(doc.fluid),
        "compositions": [],
        "compound_combinations": set(),
        "property_types": set(),
    }

    for i, fluid in enumerate(doc.fluid):
        # Get compound names for this fluid
        fluid_compound_names = []
        for comp_id in fluid.compounds:
            comp_name = str(comp_id)  # Default to ID if name not found
            for compound in doc.compound:
                if str(compound.compoundID) == str(comp_id):
                    if hasattr(compound, "commonName") and compound.commonName:
                        comp_name = compound.commonName
                    break
            fluid_compound_names.append(comp_name)

        # Get property types for this fluid
        fluid_property_types = []
        for prop in getattr(fluid, "property", []):
            if hasattr(prop, "properties") and prop.properties:
                if hasattr(prop.properties, "value"):
                    fluid_property_types.append(prop.properties.value)
                else:
                    fluid_property_types.append(str(prop.properties))
            elif hasattr(prop, "propertyID"):
                fluid_property_types.append(prop.propertyID)

        composition = {
            "fluid_index": i,
            "compounds": fluid_compound_names,
            "compound_count": len(fluid_compound_names),
            "property_types": fluid_property_types,
            "measurement_count": len(fluid.measurement),
            "parameter_count": len(fluid.parameter),
        }

        summary["compositions"].append(composition)
        summary["compound_combinations"].add(tuple(sorted(fluid_compound_names)))
        summary["property_types"].update(fluid_property_types)

    # Convert sets to lists for JSON serialization
    summary["compound_combinations"] = list(summary["compound_combinations"])
    summary["property_types"] = list(summary["property_types"])

    return summary


def plot_composition_overview(doc, figsize=(12, 8), save_path=None):
    """
    Create an overview plot showing the distribution of compositions and measurements.

    This function is designed for the new composition-based approach and shows:
    - Number of measurements per composition
    - Property types available per composition
    - Compound combinations

    Args:
        doc: FAIRFluidsDocument
        figsize: Figure size tuple
        save_path: Path to save the plot (optional)

    Returns:
        matplotlib.figure.Figure: The created figure
    """
    import matplotlib.pyplot as plt
    import numpy as np

    summary = get_fluid_composition_summary(doc)

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=figsize)

    # Plot 1: Measurements per fluid
    fluid_indices = [comp["fluid_index"] for comp in summary["compositions"]]
    measurement_counts = [comp["measurement_count"] for comp in summary["compositions"]]

    ax1.bar(fluid_indices, measurement_counts, alpha=0.7, color="skyblue")
    ax1.set_xlabel("Fluid Index")
    ax1.set_ylabel("Number of Measurements")
    ax1.set_title("Measurements per Fluid Block")
    ax1.grid(True, alpha=0.3)

    # Plot 2: Compound count distribution
    compound_counts = [comp["compound_count"] for comp in summary["compositions"]]
    unique_counts, count_freq = np.unique(compound_counts, return_counts=True)

    ax2.bar(unique_counts, count_freq, alpha=0.7, color="lightgreen")
    ax2.set_xlabel("Number of Compounds")
    ax2.set_ylabel("Number of Fluids")
    ax2.set_title("Distribution of Compound Counts")
    ax2.grid(True, alpha=0.3)

    # Plot 3: Property types per fluid
    property_type_counts = {}
    for comp in summary["compositions"]:
        count = len(comp["property_types"])
        property_type_counts[count] = property_type_counts.get(count, 0) + 1

    counts = list(property_type_counts.keys())
    freqs = list(property_type_counts.values())

    ax3.bar(counts, freqs, alpha=0.7, color="lightcoral")
    ax3.set_xlabel("Number of Property Types")
    ax3.set_ylabel("Number of Fluids")
    ax3.set_title("Distribution of Property Types per Fluid")
    ax3.grid(True, alpha=0.3)

    # Plot 4: Summary statistics
    ax4.axis("off")
    stats_text = f"""
    Document Summary:
    
    Total Fluid Blocks: {summary['total_fluids']}
    Unique Compound Combinations: {len(summary['compound_combinations'])}
    Total Property Types: {len(summary['property_types'])}
    
    Property Types Found:
    {', '.join(sorted(summary['property_types']))}
    
    Compound Combinations:
    {', '.join([f"{len(combo)} compounds: {', '.join(combo)}" for combo in summary['compound_combinations'][:5]])}
    {'...' if len(summary['compound_combinations']) > 5 else ''}
    """

    ax4.text(
        0.1,
        0.9,
        stats_text,
        transform=ax4.transAxes,
        fontsize=10,
        verticalalignment="top",
        fontfamily="monospace",
    )

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Composition overview plot saved to: {save_path}")

    return fig


def plot_with_required_compounds(
    doc,
    required_compounds,
    x_axis="temperature",
    y_axis="viscosity",
    property_type="viscosity",
    color_by=None,
    group_by=None,
    marker_by=None,
    plot_type="scatter",
    figsize=(10, 6),
    save_path=None,
):
    """
    Enhanced helper function for plotting properties only when all required compounds are present.

    This function is specifically designed for the composition-based approach where you want to
    ensure that all specified compounds are present in a fluid block before plotting properties.
    It supports all the advanced plotting options including coloring and grouping.

    Args:
        doc: FAIRFluidsDocument
        required_compounds: List of compounds that must ALL be present in a fluid block.
                           The fluid block must contain EXACTLY these compounds (no more, no less).
                           This ensures only specific compositions are plotted (e.g., binary mixtures only).
        x_axis: Column name for x-axis (default: 'temperature')
        y_axis: Column name for y-axis (default: 'viscosity')
        property_type: Property type to plot (default: 'viscosity')
        color_by: Column name for coloring points (optional) - e.g., 'composition', 'source_doi', 'mole_fraction_Glycerol'
        group_by: Column name for grouping data (optional) - e.g., 'composition', 'source_doi'
        marker_by: Column name for marker shapes/faces (optional) - e.g., 'composition', 'source_doi', 'method'
        plot_type: Type of plot ('scatter', 'line', 'both') (default: 'scatter')
        figsize: Figure size tuple
        save_path: Path to save the plot (optional)

    Returns:
        matplotlib.figure.Figure: The created figure

    Examples:
        # Basic usage - binary mixtures only (excludes ternary mixtures with water)
        plot_with_required_compounds(doc, ['Choline chloride', 'Glycerol'])

        # With composition coloring - binary mixtures only
        plot_with_required_compounds(doc, ['Choline chloride', 'Glycerol'],
                                   color_by='composition')

        # With source DOI coloring - binary mixtures only
        plot_with_required_compounds(doc, ['Choline chloride', 'Glycerol'],
                                   color_by='source_doi')

        # With mole fraction coloring - binary mixtures only
        plot_with_required_compounds(doc, ['Choline chloride', 'Glycerol'],
                                   color_by='mole_fraction_Glycerol')

        # With grouping - binary mixtures only
        plot_with_required_compounds(doc, ['Choline chloride', 'Glycerol'],
                                   group_by='composition', plot_type='line')

        # With markers and colors - binary mixtures only
        plot_with_required_compounds(doc, ['Choline chloride', 'Glycerol'],
                                   color_by='source_doi', marker_by='composition')
    """
    import matplotlib.pyplot as plt

    print(
        f"🔍 Filtering for fluid blocks containing EXACTLY these compounds: {required_compounds}"
    )

    fig = plot_fairfluids_data(
        docs=doc,
        x_axis=x_axis,
        y_axis=y_axis,
        required_compounds=required_compounds,
        property_type=property_type,
        color_by=color_by,
        group_by=group_by,
        marker_by=marker_by,
        plot_type=plot_type,
        figsize=figsize,
        title=f'{y_axis.title()} vs {x_axis.title()} - Required Compounds: {", ".join(required_compounds)}',
        save_path=save_path,
    )

    plt.show()

    return fig


def arrhenius(x, ln_eta0, Ea):
    """
    Arrhenius equation: ln(η) = ln(η₀) + Ea/(RT)
    x = 1/(RT)
    ln_eta0 = ln(η₀)
    Ea = activation energy
    """
    return ln_eta0 + Ea * x


def fit_arrhenius_equation(temps, visc):
    """
    Fit Arrhenius equation to viscosity data

    Args:
        temps: List of 1/(RT) values
        visc: List of ln(viscosity) values

    Returns:
        tuple: (ln_eta0, Ea, x_fit, y_fit) where:
            ln_eta0: Pre-exponential factor
            Ea: Activation energy
            x_fit: Array of x values for plotting fit line
            y_fit: Array of fitted y values
    """
    if len(temps) <= 2:
        return None

    x = np.array(temps)
    y = np.array(visc)
    popt, pcov = curve_fit(arrhenius, x, y)
    ln_eta0, Ea = popt

    # Generate points for the fit line
    x_fit = np.linspace(min(x), max(x), 100)
    y_fit = arrhenius(x_fit, ln_eta0, Ea)

    return ln_eta0, Ea, x_fit, y_fit


def calculate_activation_energies(doc, component_name):
    """
    Calculate activation energies for each mole fraction group in the data

    Args:
        doc: A FAIRFluids document containing viscosity data
        component_name: Name of the component to group by

    Returns:
        dict: Mapping of mole fractions to activation energies
    """
    viscosity_data = get_viscosity_data(doc)
    compounds = viscosity_data[0]["compound_identifiers"]

    try:
        component_index = compounds.index(component_name)
    except ValueError:
        raise ValueError(
            f"Component '{component_name}' not found. Available components: {compounds}"
        )

    R = 8.314  # J/(mol·K)
    mole_frac_groups = {}
    activation_energies = {}

    # Group data by mole fractions
    for data in viscosity_data:
        mole_fraction = round(data["mole_fractions"][component_index], 3)
        if mole_fraction not in mole_frac_groups:
            mole_frac_groups[mole_fraction] = {"temps": [], "visc": []}

        mole_frac_groups[mole_fraction]["temps"].append(1 / (R * data["temperature"]))
        mole_frac_groups[mole_fraction]["visc"].append(np.log(data["viscosity"]))

    # Calculate activation energy for each group
    for mole_frac, values in mole_frac_groups.items():
        fit_results = fit_arrhenius_equation(values["temps"], values["visc"])
        if fit_results:
            ln_eta0, Ea, _, _ = fit_results
            activation_energies[mole_frac] = Ea

    return activation_energies, mole_frac_groups


def get_activation_energies(doc, component_name):
    """
    Calculate activation energies for each mole fraction group in the data.

    Args:
        doc: A FAIRFluids document containing viscosity data
        component_name: Name of the component to group by (e.g. "Water", "CholinChloride", "Glycerol")

    Returns:
        tuple: (water_fractions, activation_energies) where:
            water_fractions: List of mole fractions (sorted)
            activation_energies: List of activation energies in J/mol (same order as water_fractions)
    """
    activation_energies, mole_frac_groups = calculate_activation_energies(
        doc, component_name
    )
    water_fractions = sorted(activation_energies.keys())
    activation_energies_list = [activation_energies[mf] for mf in water_fractions]
    return water_fractions, activation_energies_list


def plot_viscosity_vs_temperature(
    doc,
    component_name=None,
    fit_arrhenius=False,
    print_table=False,
    save_fig=False,
    group=None,
):
    """
    Create a plot of ln(viscosity) vs 1/RT for a FAIRFluids document.
    Groups data points by mole fraction of the selected component, or by source_doi/method if component_name is None and group is set.

    The Arrhenius equation for viscosity is:
    ln(η) = ln(η₀) + Ea/(RT)

    where:
    η = dynamic viscosity (mPa·s)
    η₀ = pre-exponential factor
    Ea = activation energy for viscous flow (J/mol)
    R = universal gas constant (8.314 J/mol·K)
    T = absolute temperature (K)

    Args:
        doc: A FAIRFluids document containing viscosity data
        component_name: Name of the component to group by (e.g. "Water", "CholinChloride", "Glycerol")
        fit_arrhenius: If True, fit Arrhenius equation to each group and plot trendlines
        print_table: If True, print a table of activation energies after plotting
        save_fig: If True, save the figure to 'viscosity_plot.png'
        group: If component_name is None, group by 'source_doi' or 'method'

    Returns:
        None
    """
    viscosity_data = get_viscosity_data_with_meta(doc)
    compounds = viscosity_data[0]["compound_identifiers"] if viscosity_data else []

    if component_name is not None:
        activation_energies, mole_frac_groups = calculate_activation_energies(
            doc, component_name
        )
        group_labels = sorted(mole_frac_groups.keys())
        group_dict = mole_frac_groups
        group_label_func = lambda mf: f"χ({component_name}) = {mf:.3f}"
    elif group in ("source_doi", "method"):
        # Group by source_doi or method
        group_dict = {}
        for data in viscosity_data:
            key = data.get(group, "unknown")
            if key not in group_dict:
                group_dict[key] = {"temps": [], "visc": [], "raw": []}
            R = 8.314
            group_dict[key]["temps"].append(1 / (R * data["temperature"]))
            group_dict[key]["visc"].append(np.log(data["viscosity"]))
            group_dict[key]["raw"].append(data)
        group_labels = sorted(group_dict.keys())
        activation_energies = {}
        for key in group_labels:
            fit_results = fit_arrhenius_equation(
                group_dict[key]["temps"], group_dict[key]["visc"]
            )
            if fit_results:
                ln_eta0, Ea, _, _ = fit_results
                activation_energies[key] = Ea
        group_label_func = lambda k: f"{group}={k}"
    else:
        raise ValueError(
            "If component_name is None, you must set group to 'source_doi' or 'method'."
        )

    # Create plot
    plt.figure(figsize=(6, 4), dpi=150)

    # Plot each group
    for label in group_labels:
        values = group_dict[label]
        scatter = plt.scatter(
            values["temps"], values["visc"], label=group_label_func(label)
        )
        if fit_arrhenius and label in activation_energies:
            fit_results = fit_arrhenius_equation(values["temps"], values["visc"])
            if fit_results:
                ln_eta0, Ea, x_fit, y_fit = fit_results
                plt.plot(
                    x_fit, y_fit, "--", alpha=0.7, color=scatter.get_facecolor()[0]
                )

    plt.xlabel("1/RT (mol/J)", fontsize=9)
    plt.ylabel("ln(η) (mPa·s)", fontsize=9)
    if component_name is not None:
        plt.title(f"Arrhenius Plot for {'-'.join(compounds)} System", fontsize=10)
        legend_title = f"{component_name} Content"
    else:
        plt.title(
            f"Arrhenius Plot for {'-'.join(compounds)} System (Grouped by {group})",
            fontsize=10,
        )
        legend_title = group
    plt.legend(
        bbox_to_anchor=(1.0, 1.0),
        loc="upper left",
        title=legend_title,
        fontsize=8,
        title_fontsize=8,
    )
    plt.tick_params(axis="both", which="major", labelsize=8)
    plt.tight_layout()
    if save_fig:
        plt.savefig("viscosity_plot.png", dpi=300, bbox_inches="tight")
    plt.show()

    if print_table and activation_energies:
        # Create pandas DataFrame for activation energies
        df = pd.DataFrame(
            {
                "Group": list(activation_energies.keys()),
                "Activation Energy (kJ/mol)": [
                    Ea / 1000 for Ea in activation_energies.values()
                ],
            }
        )
        df = df.sort_values("Group").reset_index(drop=True)
        print("\nActivation Energies:")
        print(df.to_string(index=False, float_format=lambda x: f"{x:.3f}"))


def get_viscosity_data(doc):
    """
    Returns a list of dicts with keys:
        - 'compound_identifiers': list of compound names or IDs
        - 'mole_fractions': list of mole fractions (same order as compounds)
        - 'temperature': temperature in K
        - 'viscosity': viscosity value (mPa·s)
    """
    data = []
    for fluid in doc.fluid:
        # Build property lookup: propertyID -> Property object
        property_lookup = {}
        for p in getattr(fluid, "property", []):
            pid = getattr(p, "propertyID", None)
            if pid:
                property_lookup[pid] = p

        # Build parameter lookup: parameterID -> Parameter object
        parameter_lookup = {}
        for param in getattr(fluid, "parameter", []):
            pid = getattr(param, "parameterID", None)
            if pid:
                parameter_lookup[pid] = param

        # Get compound names for this fluid
        # Note: fluid.compounds now only contains compounds present in this specific composition
        # thanks to the new composition-based approach that creates separate fluid blocks
        fluid_compound_names = []
        for comp_id in fluid.compounds:
            # Find compound name from compound list
            comp_name = str(comp_id)  # Default to ID if name not found
            for compound in doc.compound:
                if str(compound.compoundID) == str(comp_id):
                    if hasattr(compound, "commonName") and compound.commonName:
                        comp_name = compound.commonName
                    break
            fluid_compound_names.append(comp_name)

        # Process measurements for this fluid
        for measurement in fluid.measurement:
            # Extract temperature and mole fractions using parameter definitions
            temperature = None
            mole_fractions = [None] * len(fluid_compound_names)

            # Process each parameter value
            for param_val in measurement.parameterValue:
                param_def = parameter_lookup.get(param_val.parameterID)

                if param_def is not None:
                    # Check if this is a temperature parameter
                    param_obj = getattr(param_def, "parameter", None)
                    if param_obj is not None:
                        # Handle Parameters enum - get the string value
                        if hasattr(param_obj, "value"):
                            param_name = param_obj.value
                        else:
                            param_name = str(param_obj)

                        # Ensure param_name is a string
                        if not isinstance(param_name, str):
                            param_name = str(param_name)

                        if "temperature" in param_name.lower():
                            temperature = param_val.paramValue

                        # Check if this is a mole fraction parameter
                        elif "mole fraction" in param_name.lower():
                            # Get the associated compounds
                            associated_compounds = getattr(
                                param_def, "associated_compounds", []
                            )
                            # Use the first associated compound for this logic
                            associated_compound = (
                                associated_compounds[0]
                                if associated_compounds
                                else None
                            )
                            if associated_compound:
                                # Find the compound name from the associated compound ID
                                compound_name = str(associated_compound)

                                # First try to match by compound ID
                                for compound in doc.compound:
                                    if str(compound.compoundID) == str(
                                        associated_compound
                                    ):
                                        if (
                                            hasattr(compound, "commonName")
                                            and compound.commonName
                                        ):
                                            compound_name = compound.commonName
                                        break

                                # If no match by ID, try to match by common name directly
                                if compound_name == str(associated_compound):
                                    for compound in doc.compound:
                                        if (
                                            hasattr(compound, "commonName")
                                            and compound.commonName
                                            and compound.commonName
                                            == str(associated_compound)
                                        ):
                                            compound_name = compound.commonName
                                            break

                                # Map to the correct position in fluid_compound_names
                                if compound_name in fluid_compound_names:
                                    compound_index = fluid_compound_names.index(
                                        compound_name
                                    )
                                    mole_fractions[compound_index] = (
                                        param_val.paramValue
                                    )

            # Only process if we have complete mole fraction data and temperature
            if None not in mole_fractions and temperature is not None:
                # Normalize mole fractions to sum to 1.0
                mole_frac_sum = sum(mole_fractions)
                if mole_frac_sum > 0:
                    normalized_mole_fractions = [
                        mf / mole_frac_sum for mf in mole_fractions
                    ]
                else:
                    normalized_mole_fractions = mole_fractions

                # Process each property value in this measurement
                for prop_val in measurement.propertyValue:
                    # Get the property definition
                    pdef = property_lookup.get(prop_val.propertyID)

                    # Resolve the property type
                    if pdef is not None:
                        # Try to get the property type from the properties field
                        if hasattr(pdef, "properties") and pdef.properties is not None:
                            # Handle both enum and string values
                            if hasattr(pdef.properties, "value"):
                                resolved_type = pdef.properties.value
                            else:
                                resolved_type = str(pdef.properties)
                        else:
                            # Fallback to propertyID
                            resolved_type = prop_val.propertyID
                    else:
                        # Fallback if property definition not found
                        resolved_type = prop_val.propertyID

                    # Only process viscosity data
                    if resolved_type == "viscosity":
                        data.append(
                            {
                                "compound_identifiers": fluid_compound_names,
                                "mole_fractions": normalized_mole_fractions,
                                "temperature": temperature,
                                "viscosity": prop_val.propValue,
                            }
                        )
    return data


# Helper to get viscosity data with source_doi and method


def get_viscosity_data_with_meta(doc):
    """
    Returns a list of dicts with keys:
        - 'compound_identifiers': list of compound names or IDs
        - 'mole_fractions': list of mole fractions (same order as compounds)
        - 'temperature': temperature in K
        - 'viscosity': viscosity value (mPa·s)
        - 'source_doi': source DOI for the measurement
        - 'method': method for the measurement
    """
    data = []
    for fluid in doc.fluid:
        # Build property lookup: propertyID -> Property object
        property_lookup = {}
        for p in getattr(fluid, "property", []):
            pid = getattr(p, "propertyID", None)
            if pid:
                property_lookup[pid] = p

        # Build parameter lookup: parameterID -> Parameter object
        parameter_lookup = {}
        for param in getattr(fluid, "parameter", []):
            pid = getattr(param, "parameterID", None)
            if pid:
                parameter_lookup[pid] = param

        # Get compound names for this fluid
        # Note: fluid.compounds now only contains compounds present in this specific composition
        # thanks to the new composition-based approach that creates separate fluid blocks
        fluid_compound_names = []
        for comp_id in fluid.compounds:
            # Find compound name from compound list
            comp_name = str(comp_id)  # Default to ID if name not found
            for compound in doc.compound:
                if str(compound.compoundID) == str(comp_id):
                    if hasattr(compound, "commonName") and compound.commonName:
                        comp_name = compound.commonName
                    break
            fluid_compound_names.append(comp_name)

        # Process measurements for this fluid
        for measurement in fluid.measurement:
            # Extract temperature and mole fractions using parameter definitions
            temperature = None
            mole_fractions = [None] * len(fluid_compound_names)

            # Process each parameter value
            for param_val in measurement.parameterValue:
                param_def = parameter_lookup.get(param_val.parameterID)

                if param_def is not None:
                    # Check if this is a temperature parameter
                    param_obj = getattr(param_def, "parameter", None)
                    if param_obj is not None:
                        # Handle Parameters enum - get the string value
                        if hasattr(param_obj, "value"):
                            param_name = param_obj.value
                        else:
                            param_name = str(param_obj)

                        # Ensure param_name is a string
                        if not isinstance(param_name, str):
                            param_name = str(param_name)

                        if "temperature" in param_name.lower():
                            temperature = param_val.paramValue

                        # Check if this is a mole fraction parameter
                        elif "mole fraction" in param_name.lower():
                            # Get the associated compounds
                            associated_compounds = getattr(
                                param_def, "associated_compounds", []
                            )
                            # Use the first associated compound for this logic
                            associated_compound = (
                                associated_compounds[0]
                                if associated_compounds
                                else None
                            )
                            if associated_compound:
                                # Find the compound name from the associated compound ID
                                compound_name = str(associated_compound)

                                # First try to match by compound ID
                                for compound in doc.compound:
                                    if str(compound.compoundID) == str(
                                        associated_compound
                                    ):
                                        if (
                                            hasattr(compound, "commonName")
                                            and compound.commonName
                                        ):
                                            compound_name = compound.commonName
                                        break

                                # If no match by ID, try to match by common name directly
                                if compound_name == str(associated_compound):
                                    for compound in doc.compound:
                                        if (
                                            hasattr(compound, "commonName")
                                            and compound.commonName
                                            and compound.commonName
                                            == str(associated_compound)
                                        ):
                                            compound_name = compound.commonName
                                            break

                                # Map to the correct position in fluid_compound_names
                                if compound_name in fluid_compound_names:
                                    compound_index = fluid_compound_names.index(
                                        compound_name
                                    )
                                    mole_fractions[compound_index] = (
                                        param_val.paramValue
                                    )

            # Only process if we have complete mole fraction data and temperature
            if None not in mole_fractions and temperature is not None:
                # Normalize mole fractions to sum to 1.0
                mole_frac_sum = sum(mole_fractions)
                if mole_frac_sum > 0:
                    normalized_mole_fractions = [
                        mf / mole_frac_sum for mf in mole_fractions
                    ]
                else:
                    normalized_mole_fractions = mole_fractions

                # Process each property value in this measurement
                for prop_val in measurement.propertyValue:
                    # Get the property definition
                    pdef = property_lookup.get(prop_val.propertyID)

                    # Resolve the property type
                    if pdef is not None:
                        # Try to get the property type from the properties field
                        if hasattr(pdef, "properties") and pdef.properties is not None:
                            # Handle both enum and string values
                            if hasattr(pdef.properties, "value"):
                                resolved_type = pdef.properties.value
                            else:
                                resolved_type = str(pdef.properties)
                        else:
                            # Fallback to propertyID
                            resolved_type = prop_val.propertyID
                    else:
                        # Fallback if property definition not found
                        resolved_type = prop_val.propertyID

                    # Only process viscosity data
                    if resolved_type == "viscosity":
                        data.append(
                            {
                                "compound_identifiers": fluid_compound_names,
                                "mole_fractions": normalized_mole_fractions,
                                "temperature": temperature,
                                "viscosity": prop_val.propValue,
                                "source_doi": getattr(measurement, "source_doi", None),
                                "method": (
                                    getattr(measurement, "method", None).name
                                    if getattr(measurement, "method", None)
                                    else None
                                ),
                            }
                        )
    return data


def plot_activation_energy_analysis(
    doc, component_name, E_water=17.0, figsize=(4, 3), dpi=150
):
    """
    Create a comprehensive activation energy analysis plot showing experimental data vs ideal mixing.

    Args:
        doc: A FAIRFluids document containing viscosity data
        component_name: Name of the component to analyze (e.g. "Water", "CholinChloride", "Glycerol")
        E_water: Activation energy of pure water in kJ/mol (default: 17.0)
        figsize: Figure size tuple (default: (4, 3))
        dpi: Figure DPI (default: 150)

    Returns:
        tuple: (water_fractions, E_values, E_DES, E_water) where:
            water_fractions: List of mole fractions
            E_values: List of activation energies in kJ/mol
            E_DES: Activation energy of pure DES in kJ/mol
            E_water: Activation energy of pure water in kJ/mol
    """
    # Get activation energies and water fractions
    water_fractions, E_values = get_activation_energies(doc, component_name)

    # Convert E_values to kJ/mol
    E_values = [E / 1000 for E in E_values]

    # Make sure both lists are the same length
    min_len = min(len(water_fractions), len(E_values))
    water_fractions = water_fractions[:min_len]
    E_values = E_values[:min_len]

    # Calculate ideal fluid activation energy
    E_DES = max(E_values)  # Use highest activation energy (pure DES) as reference

    # Generate smooth line for ideal behavior
    x_water_ideal = np.linspace(0, 1, 100)
    E_ideal = [x * E_water + (1 - x) * E_DES for x in x_water_ideal]

    # Create the plot with better styling
    plt.figure(figsize=figsize, dpi=dpi)
    plt.scatter(
        water_fractions,
        E_values,
        label="Experimental Data",
        s=10,
        alpha=0.8,
        color="blue",
        edgecolors="darkblue",
        linewidth=1,
    )
    plt.plot(
        x_water_ideal, E_ideal, "r--", label="Ideal Mixing", linewidth=1, alpha=0.8
    )

    plt.xlabel("Water Mole Fraction", fontsize=9)
    plt.ylabel("Activation Energy (kJ/mol)", fontsize=9)
    plt.title(
        f"Activation Energy vs {component_name} Mole Fraction\n{component_name} System",
        fontsize=6,
    )
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=8)
    plt.tick_params(axis="both", which="major", labelsize=8)
    plt.tight_layout()

    # Add some annotations
    plt.annotate(
        f"Pure DES\nE = {E_DES:.1f} kJ/mol",
        xy=(0, E_DES),
        xytext=(0.1, E_DES + 5),
        fontsize=4,
        ha="center",
    )
    plt.annotate(
        f"Pure {component_name}\nE = {E_water} kJ/mol",
        xy=(1, E_water),
        xytext=(0.9, E_water + 5),
        fontsize=4,
        ha="center",
    )

    plt.show()

    # Print summary statistics
    print(f"\nSummary:")
    print(f"Number of data points: {len(water_fractions)}")
    print(
        f"{component_name} fraction range: {min(water_fractions):.3f} - {max(water_fractions):.3f}"
    )
    print(f"Activation energy range: {min(E_values):.1f} - {max(E_values):.1f} kJ/mol")
    print(f"E_DES (pure DES): {E_DES:.1f} kJ/mol")
    print(f"E_{component_name} (pure {component_name}): {E_water:.1f} kJ/mol")

    # Calculate deviation from ideal at x=0.5 if possible
    if len(E_values) > 5:
        mid_index = len(E_values) // 2
        ideal_mid = 0.5 * E_water + 0.5 * E_DES
        deviation = E_values[mid_index] - ideal_mid
        print(f"Deviation from ideal at x=0.5: {deviation:.1f} kJ/mol")

    return water_fractions, E_values, E_DES, E_water


def get_activation_energies_dataframe(doc, component_name):
    """
    Get activation energies as a pandas DataFrame.

    Args:
        doc: A FAIRFluids document containing viscosity data
        component_name: Name of the component to analyze (e.g. "Water", "CholinChloride", "Glycerol")

    Returns:
        pandas.DataFrame: DataFrame with columns:
            - Mole_Fraction: Mole fraction of the component
            - Activation_Energy_J_mol: Activation energy in J/mol
            - Activation_Energy_kJ_mol: Activation energy in kJ/mol
    """
    water_fractions, E_values = get_activation_energies(doc, component_name)

    # Create DataFrame
    df = pd.DataFrame(
        {
            "Mole_Fraction": water_fractions,
            "Activation_Energy_J_mol": E_values,
            "Activation_Energy_kJ_mol": [E / 1000 for E in E_values],
        }
    )

    return df


def filter_fluid_measurements(
    doc,
    fluid_compounds=None,
    property_type=None,
    required_compounds=None,
    return_dataframe=False,
):
    """
    Filter fluid measurements by compound composition and property type.
    This function is robust and works with any parameter naming convention by using
    the actual property definitions and parameter associations from the FAIRFluids schema.

    Args:
        doc: A FAIRFluids document containing fluid data
        fluid_compounds: List of compound names to filter by (e.g., ["water", "glycerol"]).
                        If None, includes all fluids. Can also be a single compound name.
                        This requires an EXACT match of all compounds in the fluid.
        property_type: Property to filter by ("viscosity", "density", "specific_heat_capacity", etc.).
                      If None, includes all properties.
        required_compounds: List of compounds that must ALL be present in a fluid block for it to be included.
                           The fluid block must contain EXACTLY these compounds (no more, no less).
                           This is useful for the composition-based approach where you want to ensure
                           only specific compositions are included (e.g., binary mixtures only).
        return_dataframe: If True, returns a pandas DataFrame instead of list of dicts.

    Returns:
        If return_dataframe=False: List of dictionaries with measurement data
        If return_dataframe=True: pandas DataFrame with measurement data

    Each measurement dict/row contains:
        - 'fluid_compounds': List of compound names in the fluid
        - 'property_type': Type of property measured
        - 'property_value': Measured value
        - 'uncertainty': Measurement uncertainty (if available)
        - 'temperature': Temperature in K
        - 'mole_fractions': List of mole fractions (same order as fluid_compounds)
        - 'measurement_id': Unique measurement identifier
        - 'source_doi': Source DOI (if available)
    """
    import pandas as pd

    # Convert single compound to list for consistent handling
    if isinstance(fluid_compounds, str):
        fluid_compounds = [fluid_compounds]

    # Convert single required compound to list for consistent handling
    if isinstance(required_compounds, str):
        required_compounds = [required_compounds]

    measurements = []

    for fluid in doc.fluid:
        # Build property lookup: propertyID -> Property object
        property_lookup = {}
        for p in getattr(fluid, "property", []):
            pid = getattr(p, "propertyID", None)
            if pid:
                property_lookup[pid] = p

        # Build parameter lookup: parameterID -> Parameter object
        parameter_lookup = {}
        for param in getattr(fluid, "parameter", []):
            pid = getattr(param, "parameterID", None)
            if pid:
                parameter_lookup[pid] = param

        # Get compound names for this fluid
        # Note: fluid.compounds now only contains compounds present in this specific composition
        # thanks to the new composition-based approach that creates separate fluid blocks
        fluid_compound_names = []
        for comp_id in fluid.compounds:
            # Find compound name from compound list
            comp_name = str(comp_id)  # Default to ID if name not found
            for compound in doc.compound:
                if str(compound.compoundID) == str(comp_id):
                    if hasattr(compound, "commonName") and compound.commonName:
                        comp_name = compound.commonName
                    break
            fluid_compound_names.append(comp_name)

        # Check if this fluid matches the compound filter
        if fluid_compounds is not None:
            if not all(comp in fluid_compound_names for comp in fluid_compounds):
                continue
            if len(fluid_compound_names) != len(fluid_compounds):
                continue

        # Check if this fluid contains EXACTLY the required compounds (no more, no less)
        if required_compounds is not None:
            # Check if all required compounds are present
            if not all(comp in fluid_compound_names for comp in required_compounds):
                continue
            # Check if there are no additional compounds beyond the required ones
            if len(fluid_compound_names) != len(required_compounds):
                continue

        # Process measurements for this fluid
        for measurement in fluid.measurement:
            # Extract temperature and mole fractions using parameter definitions
            temperature = None
            mole_fractions = [None] * len(fluid_compound_names)

            # Process each parameter value
            for param_val in measurement.parameterValue:
                param_def = parameter_lookup.get(param_val.parameterID)

                if param_def is not None:
                    # Check if this is a temperature parameter
                    param_obj = getattr(param_def, "parameter", None)
                    if param_obj is not None:
                        # Handle Parameters enum - get the string value
                        if hasattr(param_obj, "value"):
                            param_name = param_obj.value
                        else:
                            param_name = str(param_obj)

                        # Ensure param_name is a string
                        if not isinstance(param_name, str):
                            param_name = str(param_name)

                        if "temperature" in param_name.lower():
                            temperature = param_val.paramValue

                        # Check if this is a mole fraction parameter
                        elif "mole fraction" in param_name.lower():
                            # Get the associated compounds
                            associated_compounds = getattr(
                                param_def, "associated_compounds", []
                            )
                            # Use the first associated compound for this logic
                            associated_compound = (
                                associated_compounds[0]
                                if associated_compounds
                                else None
                            )
                            if associated_compound:
                                # Find the compound name from the associated compound ID
                                compound_name = str(associated_compound)

                                # First try to match by compound ID
                                for compound in doc.compound:
                                    if str(compound.compoundID) == str(
                                        associated_compound
                                    ):
                                        if (
                                            hasattr(compound, "commonName")
                                            and compound.commonName
                                        ):
                                            compound_name = compound.commonName
                                        break

                                # If no match by ID, try to match by common name directly
                                if compound_name == str(associated_compound):
                                    for compound in doc.compound:
                                        if (
                                            hasattr(compound, "commonName")
                                            and compound.commonName
                                            and compound.commonName
                                            == str(associated_compound)
                                        ):
                                            compound_name = compound.commonName
                                            break

                                # Map to the correct position in fluid_compound_names
                                if compound_name in fluid_compound_names:
                                    compound_index = fluid_compound_names.index(
                                        compound_name
                                    )
                                    mole_fractions[compound_index] = (
                                        param_val.paramValue
                                    )

            # Only process if we have complete mole fraction data and temperature
            if None not in mole_fractions and temperature is not None:
                # Normalize mole fractions to sum to 1.0
                mole_frac_sum = sum(mole_fractions)
                if mole_frac_sum > 0:
                    normalized_mole_fractions = [
                        mf / mole_frac_sum for mf in mole_fractions
                    ]
                else:
                    normalized_mole_fractions = mole_fractions

                # Process each property value in this measurement
                for prop_val in measurement.propertyValue:
                    # Get the property definition
                    pdef = property_lookup.get(prop_val.propertyID)

                    # Resolve the property type
                    if pdef is not None:
                        # Try to get the property type from the properties field
                        if hasattr(pdef, "properties") and pdef.properties is not None:
                            # Handle both enum and string values
                            if hasattr(pdef.properties, "value"):
                                resolved_type = pdef.properties.value
                            else:
                                resolved_type = str(pdef.properties)
                        else:
                            # Fallback to propertyID
                            resolved_type = prop_val.propertyID
                    else:
                        # Fallback if property definition not found
                        resolved_type = prop_val.propertyID

                    # Check property type filter against resolved type
                    if property_type is not None and resolved_type != property_type:
                        continue

                    measurement_data = {
                        "fluid_compounds": fluid_compound_names,
                        "property_type": resolved_type,
                        "property_value": prop_val.propValue,
                        "uncertainty": getattr(prop_val, "uncertainty", None),
                        "temperature": temperature,
                        "mole_fractions": normalized_mole_fractions,
                        "measurement_id": getattr(measurement, "measurement_id", None),
                        "source_doi": getattr(measurement, "source_doi", None),
                    }

                    measurements.append(measurement_data)

    if return_dataframe:
        if not measurements:
            return pd.DataFrame(
                columns=[
                    "fluid_compounds",
                    "property_type",
                    "property_value",
                    "uncertainty",
                    "temperature",
                    "mole_fractions",
                    "measurement_id",
                    "source_doi",
                ]
            )
        return pd.DataFrame(measurements)

    return measurements


def get_measurements(doc, group=None):
    """
    Returns a new FAIRFluidsDocument containing only measurements filtered by group:
    - group='Simulated': only simulation measurements
    - group='Measured': only experimental/measured measurements
    - group=<doi string>: only measurements with the given source_doi
    If group is None, returns the original doc.
    The returned object can be used with plot_viscosity_vs_temperature.
    """
    from copy import deepcopy

    # If no filtering, return as is
    if group is None:
        return doc
    # Deepcopy to avoid mutating the original
    filtered_doc = deepcopy(doc)
    for fluid in filtered_doc.fluid:
        filtered_measurements = []
        for meas in fluid.measurement:
            method_obj = getattr(meas, "method", None)
            if method_obj is not None:
                method_name_obj = getattr(method_obj, "name", str(method_obj))
                # Handle enum objects
                if hasattr(method_name_obj, "value"):
                    method_name = method_name_obj.value.lower()
                else:
                    method_name = str(method_name_obj).lower()
            else:
                method_name = ""
            if group.lower() == "simulated":
                if "simul" in method_name:
                    filtered_measurements.append(meas)
            elif group.lower() == "measured":
                if "measured" in method_name or "experimental" in method_name:
                    filtered_measurements.append(meas)
            elif isinstance(group, str):
                # Assume group is a DOI string
                if getattr(meas, "source_doi", None) == group:
                    filtered_measurements.append(meas)
        fluid.measurement = filtered_measurements
    return filtered_doc


def example_usage_filter_fluid_measurements():
    """
    Example usage of the filter_fluid_measurements function.
    This function demonstrates how to use the filter to extract specific data.
    """
    import json

    # Example: Load a FAIRFluids document from JSON
    # with open('path/to/your/fairfluids_document.json', 'r') as f:
    #     doc_data = json.load(f)
    #     doc = FAIRFluidsDocument(**doc_data)  # Assuming you have a parser

    print("Example usage of filter_fluid_measurements:")
    print("=" * 50)

    print("\n1. Get all viscosity measurements:")
    print("   measurements = filter_fluid_measurements(doc, property_type='viscosity')")

    print("\n2. Get all density measurements:")
    print("   measurements = filter_fluid_measurements(doc, property_type='density')")

    print("\n3. Get measurements for water-glycerol systems:")
    print(
        "   measurements = filter_fluid_measurements(doc, fluid_compounds=['water', 'glycerol'])"
    )

    print("\n4. Get viscosity measurements for specific fluid composition:")
    print(
        "   measurements = filter_fluid_measurements(doc, fluid_compounds=['water', 'choline', '16887-00-6', 'glycerol'], property_type='viscosity')"
    )

    print("\n5. Get data as pandas DataFrame:")
    print(
        "   df = filter_fluid_measurements(doc, property_type='viscosity', return_dataframe=True)"
    )

    print("\n6. Get all measurements for a single compound:")
    print("   measurements = filter_fluid_measurements(doc, fluid_compounds='water')")

    print("\nEach measurement contains:")
    print("   - fluid_compounds: List of compound names")
    print("   - property_type: Type of property (viscosity, density, etc.)")
    print("   - property_value: Measured value")
    print("   - uncertainty: Measurement uncertainty")
    print("   - temperature: Temperature in K")
    print("   - mole_fractions: List of mole fractions")
    print("   - measurement_id: Unique identifier")
    print("   - source_doi: Source DOI if available")


def discover_plotting_options(docs):
    """
    Discover available plotting options from FAIRFluids document(s).

    Args:
        docs: Single FAIRFluidsDocument or list of FAIRFluidsDocument objects

    Returns:
        dict: Dictionary containing available options for plotting
    """
    import pandas as pd

    # Ensure docs is a list
    if not isinstance(docs, list):
        docs = [docs]

    # Collect all measurements
    all_measurements = []
    doc_labels = []

    for i, doc in enumerate(docs):
        measurements = filter_fluid_measurements(doc, return_dataframe=True)
        if len(measurements) > 0:
            measurements["doc_label"] = f"Document_{i+1}"
            all_measurements.append(measurements)
            doc_labels.append(f"Document_{i+1}")

    if not all_measurements:
        return {"error": "No measurements found in any document"}

    # Combine all measurements
    combined_df = pd.concat(all_measurements, ignore_index=True)

    # Discover available options
    options = {
        "x_axis_options": [],
        "y_axis_options": [],
        "color_options": [],
        "grouping_options": [],
        "property_types": [],
        "compounds": [],
        "temperature_range": {},
        "documents": doc_labels,
    }

    # Property types (can be used as x or y axis)
    property_types = combined_df["property_type"].unique().tolist()
    options["property_types"] = property_types
    options["x_axis_options"].extend(property_types)
    options["y_axis_options"].extend(property_types)

    # Temperature (always available as x or y axis)
    if "temperature" in combined_df.columns:
        options["x_axis_options"].append("temperature")
        options["y_axis_options"].append("temperature")
        options["temperature_range"] = {
            "min": float(combined_df["temperature"].min()),
            "max": float(combined_df["temperature"].max()),
            "unit": "K",
        }

    # Mole fractions (can be used as x or y axis)
    mole_fraction_cols = [
        col for col in combined_df.columns if col.startswith("mole_fraction_")
    ]
    options["x_axis_options"].extend(mole_fraction_cols)
    options["y_axis_options"].extend(mole_fraction_cols)

    # Color options (everything that can be used for coloring)
    color_options = property_types.copy()
    color_options.extend(mole_fraction_cols)
    if "temperature" in combined_df.columns:
        color_options.append("temperature")
    if "uncertainty" in combined_df.columns:
        color_options.append("uncertainty")
    if "doc_label" in combined_df.columns:
        color_options.append("doc_label")
    options["color_options"] = color_options

    # Grouping options
    grouping_options = mole_fraction_cols.copy()
    if "doc_label" in combined_df.columns:
        grouping_options.append("doc_label")
    if "source_doi" in combined_df.columns:
        grouping_options.append("source_doi")
    if "measurement_id" in combined_df.columns:
        grouping_options.append("measurement_id")
    # Add composition-based grouping
    grouping_options.append("composition")
    options["grouping_options"] = grouping_options

    # Compounds
    all_compounds = set()
    for compounds_list in combined_df["fluid_compounds"]:
        all_compounds.update(compounds_list)
    options["compounds"] = sorted(list(all_compounds))

    # Summary statistics
    # Convert fluid_compounds lists to tuples for grouping (lists are unhashable)
    combined_df["fluid_compounds_tuple"] = combined_df["fluid_compounds"].apply(tuple)

    options["summary"] = {
        "total_measurements": len(combined_df),
        "total_documents": len(docs),
        "property_types_count": len(property_types),
        "unique_compositions": len(combined_df.groupby("fluid_compounds_tuple").size()),
        "temperature_points": (
            len(combined_df["temperature"].unique())
            if "temperature" in combined_df.columns
            else 0
        ),
    }

    return options


def format_composition_label(composition_tuple, compounds=None):
    """
    Format a composition tuple into a readable label.

    Args:
        composition_tuple: Tuple of mole fractions
        compounds: List of compound names (optional)

    Returns:
        str: Formatted composition label
    """
    if compounds and len(compounds) == len(composition_tuple):
        parts = []
        for i, (compound, fraction) in enumerate(zip(compounds, composition_tuple)):
            if fraction is not None and fraction > 0:
                parts.append(f"{compound}: {fraction:.3f}")
        return " | ".join(parts)
    else:
        # Fallback to simple tuple representation
        return (
            f"({', '.join([f'{x:.3f}' for x in composition_tuple if x is not None])})"
        )


def get_marker_styles():
    """
    Get a list of distinct marker styles for plotting.

    Returns:
        list: List of matplotlib marker styles
    """
    return [
        "o",
        "s",
        "^",
        "v",
        "D",
        "p",
        "*",
        "h",
        "H",
        "8",
        "X",
        "P",
        "d",
        "|",
        "_",
        "+",
        "x",
        "<",
        ">",
        "1",
        "2",
        "3",
        "4",
    ]


def get_marker_for_value(value, marker_data, marker_styles=None):
    """
    Get marker style for a given value based on marker_data.

    Args:
        value: The value to get marker for
        marker_data: Series of marker values
        marker_styles: List of marker styles (optional)

    Returns:
        str: Marker style string
    """
    if marker_styles is None:
        marker_styles = get_marker_styles()

    unique_values = marker_data.unique()
    marker_map = dict(zip(unique_values, marker_styles[: len(unique_values)]))
    return marker_map.get(value, "o")  # Default to circle if not found


def round_composition_tuple(composition_tuple, decimal_places=3):
    """
    Round all mole fractions in a composition tuple to avoid floating point precision issues.

    Args:
        composition_tuple: Tuple of mole fractions
        decimal_places: Number of decimal places to round to (default: 3)

    Returns:
        tuple: Rounded composition tuple
    """
    return tuple(
        round(x, decimal_places) if x is not None else x for x in composition_tuple
    )


def plot_fairfluids_data(
    docs,
    x_axis,
    y_axis,
    color_by=None,
    group_by=None,
    marker_by=None,
    property_type=None,
    fluid_compounds=None,
    required_compounds=None,
    plot_type="scatter",
    figsize=(12, 8),
    title=None,
    save_path=None,
    show_legend=True,
    alpha=0.7,
    s=50,
):
    """
    Create flexible plots for FAIRFluids data.

    Args:
        docs: Single FAIRFluidsDocument or list of FAIRFluidsDocument objects
        x_axis: Column name for x-axis (e.g., 'temperature', 'density', 'mole_fraction_Water')
        y_axis: Column name for y-axis (e.g., 'temperature', 'density', 'mole_fraction_Water')
        color_by: Column name for coloring points (optional)
        group_by: Column name for grouping data (optional)
        marker_by: Column name for marker shapes/faces (optional) - e.g., 'composition', 'source_doi', 'method'
        property_type: Filter by specific property type (optional)
        fluid_compounds: Filter by specific compounds (optional) - exact match required
        required_compounds: List of compounds that must ALL be present in a fluid block for it to be included (optional)
        plot_type: Type of plot ('scatter', 'line', 'both')
        figsize: Figure size tuple
        title: Custom title for the plot
        save_path: Path to save the plot (optional)
        show_legend: Whether to show legend
        alpha: Transparency for scatter points
        s: Size of scatter points

    Returns:
        matplotlib.figure.Figure: The created figure
    """
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np

    # Ensure docs is a list
    if not isinstance(docs, list):
        docs = [docs]

    # Collect and filter data
    all_data = []
    doc_labels = []

    for i, doc in enumerate(docs):
        # Filter data
        measurements = filter_fluid_measurements(
            doc,
            property_type=property_type,
            fluid_compounds=fluid_compounds,
            required_compounds=required_compounds,
            return_dataframe=True,
        )

        if len(measurements) > 0:
            # Add mole fraction columns if they don't exist
            if "mole_fractions" in measurements.columns:
                compounds = (
                    measurements["fluid_compounds"].iloc[0]
                    if len(measurements) > 0
                    else []
                )
                for j, compound in enumerate(compounds):
                    measurements[f"mole_fraction_{compound}"] = measurements[
                        "mole_fractions"
                    ].apply(lambda x: x[j] if j < len(x) else None)

            measurements["doc_label"] = f"Document_{i+1}"
            all_data.append(measurements)
            doc_labels.append(f"Document_{i+1}")

    if not all_data:
        raise ValueError("No data found matching the specified criteria")

    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)

    # Handle property types - they need to be filtered and mapped to property_value
    property_columns = {}
    for prop_type in combined_df["property_type"].unique():
        property_columns[prop_type] = f"property_value_{prop_type}"
        # Create a column for each property type
        mask = combined_df["property_type"] == prop_type
        combined_df.loc[mask, f"property_value_{prop_type}"] = combined_df.loc[
            mask, "property_value"
        ]

    # Check if required columns exist, with special handling for property types
    x_axis_actual = x_axis
    y_axis_actual = y_axis

    if x_axis in property_columns:
        x_axis_actual = property_columns[x_axis]
    elif x_axis not in combined_df.columns:
        raise ValueError(
            f"Column '{x_axis}' not found in data. Available columns: {list(combined_df.columns)}"
        )

    if y_axis in property_columns:
        y_axis_actual = property_columns[y_axis]
    elif y_axis not in combined_df.columns:
        raise ValueError(
            f"Column '{y_axis}' not found in data. Available columns: {list(combined_df.columns)}"
        )

    # Create the plot
    fig, ax = plt.subplots(figsize=figsize)

    # Generate title if not provided
    if title is None:
        title_parts = [f"{y_axis} vs {x_axis}"]
        if property_type:
            title_parts.append(f"({property_type})")
        if fluid_compounds:
            title_parts.append(f"[{', '.join(fluid_compounds)}]")
        title = " ".join(title_parts)

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(x_axis.replace("_", " ").title())
    ax.set_ylabel(y_axis.replace("_", " ").title())
    ax.grid(True, alpha=0.3)

    # Determine markers - focus on categorical marker assignment
    if marker_by and marker_by in combined_df.columns:
        # Handle fluid_compounds markers (convert lists to tuples)
        if marker_by == "fluid_compounds":
            combined_df["fluid_compounds_tuple"] = combined_df["fluid_compounds"].apply(
                tuple
            )
            marker_data = combined_df["fluid_compounds_tuple"]
        # Handle mole fraction composition markers (use complete composition)
        elif marker_by.startswith("mole_fraction_") or marker_by == "composition":
            # Create composition tuples for categorical markers
            combined_df["composition_tuple"] = combined_df["mole_fractions"].apply(
                tuple
            )
            marker_data = combined_df["composition_tuple"]
        else:
            marker_data = combined_df[marker_by]

        # Get marker styles for each unique value
        marker_styles = get_marker_styles()
        unique_markers = marker_data.unique()
        marker_map = dict(zip(unique_markers, marker_styles[: len(unique_markers)]))
        point_markers = [marker_map[val] for val in marker_data]
    else:
        point_markers = "o"  # Default to circle

    # Determine colors - focus on categorical coloring
    if color_by and color_by in combined_df.columns:
        # Handle fluid_compounds coloring (convert lists to tuples)
        if color_by == "fluid_compounds":
            combined_df["fluid_compounds_tuple"] = combined_df["fluid_compounds"].apply(
                tuple
            )
            color_data = combined_df["fluid_compounds_tuple"]
        # Handle mole fraction composition coloring (use complete composition)
        elif color_by.startswith("mole_fraction_") or color_by == "composition":
            # Create composition tuples for categorical coloring
            combined_df["composition_tuple"] = combined_df["mole_fractions"].apply(
                tuple
            )
            color_data = combined_df["composition_tuple"]
        else:
            color_data = combined_df[color_by]

        # Always use categorical coloring for better legends
        unique_colors = color_data.unique()
        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_colors)))
        color_map = dict(zip(unique_colors, colors))
        point_colors = [color_map[val] for val in color_data]
    else:
        point_colors = "blue"

    # Create plots based on grouping
    if group_by and group_by in combined_df.columns:
        # Handle fluid_compounds grouping (convert lists to tuples)
        if group_by == "fluid_compounds":
            combined_df["fluid_compounds_tuple"] = combined_df["fluid_compounds"].apply(
                tuple
            )
            groups = combined_df.groupby("fluid_compounds_tuple")
        # Handle mole fraction composition grouping (use complete composition)
        elif group_by.startswith("mole_fraction_") or group_by == "composition":
            # Create composition tuples for grouping with proper rounding
            combined_df["composition_tuple"] = combined_df["mole_fractions"].apply(
                lambda x: round_composition_tuple(tuple(x))
            )
            groups = combined_df.groupby("composition_tuple")
        else:
            groups = combined_df.groupby(group_by)
        colors = plt.cm.tab10(np.linspace(0, 1, min(len(groups), 10)))

        for i, (group_name, group_data) in enumerate(groups):
            if i >= 10:  # Limit to 10 groups for clarity
                break

            color = colors[i] if point_colors is None else point_colors

            # Format group label for better readability
            if group_by.startswith("mole_fraction_") or group_by == "composition":
                # Get compounds from the first row of this group
                compounds = (
                    group_data["fluid_compounds"].iloc[0] if len(group_data) > 0 else []
                )
                group_label = format_composition_label(group_name, compounds)
            elif group_by == "fluid_compounds":
                group_label = " + ".join(group_name)
            else:
                group_label = str(group_name)

            if plot_type in ["scatter", "both"]:
                # Get markers for this group
                if marker_by and marker_by in combined_df.columns:
                    group_markers = group_data.apply(
                        lambda row: get_marker_for_value(
                            row[marker_by] if marker_by in row else "o",
                            (
                                combined_df[marker_by]
                                if marker_by in combined_df.columns
                                else pd.Series(["o"])
                            ),
                            get_marker_styles(),
                        ),
                        axis=1,
                    ).tolist()
                else:
                    group_markers = "o"

                ax.scatter(
                    group_data[x_axis_actual],
                    group_data[y_axis_actual],
                    c=[color],
                    marker=(
                        group_markers[0]
                        if isinstance(group_markers, list) and len(group_markers) > 0
                        else group_markers
                    ),
                    alpha=alpha,
                    s=s,
                    label=group_label,
                )

            if plot_type in ["line", "both"]:
                # Sort by x-axis for line plots
                sorted_data = group_data.sort_values(x_axis_actual)
                ax.plot(
                    sorted_data[x_axis_actual],
                    sorted_data[y_axis_actual],
                    color=color,
                    alpha=alpha,
                    linewidth=2,
                    label=None,
                )

        # Add legend if grouping is used and there are multiple groups
        if show_legend:
            if len(groups) > 1:
                ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
            elif len(groups) == 1:
                # Only one group - add a note to the title
                group_name = list(groups.keys())[0]
                if group_by.startswith("mole_fraction_") or group_by == "composition":
                    compounds = (
                        groups[group_name]["fluid_compounds"].iloc[0]
                        if len(groups[group_name]) > 0
                        else []
                    )
                    group_label = format_composition_label(group_name, compounds)
                elif group_by == "fluid_compounds":
                    group_label = " + ".join(group_name)
                else:
                    group_label = str(group_name)

                # Update title to include group information
                current_title = ax.get_title()
                ax.set_title(f"{current_title}\n(All data: {group_label})", fontsize=12)
    else:
        # No grouping - but handle composition coloring intelligently
        if color_by and (
            color_by.startswith("mole_fraction_") or color_by == "composition"
        ):
            # When coloring by composition, create separate traces for each composition
            # Create composition tuples for grouping with proper rounding
            combined_df["composition_tuple"] = combined_df["mole_fractions"].apply(
                lambda x: round_composition_tuple(tuple(x))
            )
            groups = combined_df.groupby("composition_tuple")
            colors = plt.cm.tab10(np.linspace(0, 1, min(len(groups), 10)))

            for i, (group_name, group_data) in enumerate(groups):
                if i >= 10:  # Limit to 10 groups for clarity
                    break

                color = colors[i]

                # Format group label for better readability
                compounds = (
                    group_data["fluid_compounds"].iloc[0] if len(group_data) > 0 else []
                )
                group_label = format_composition_label(group_name, compounds)

                if plot_type in ["scatter", "both"]:
                    # Get markers for this composition group
                    if marker_by and marker_by in combined_df.columns:
                        group_markers = group_data.apply(
                            lambda row: get_marker_for_value(
                                row[marker_by] if marker_by in row else "o",
                                (
                                    combined_df[marker_by]
                                    if marker_by in combined_df.columns
                                    else pd.Series(["o"])
                                ),
                                get_marker_styles(),
                            ),
                            axis=1,
                        ).tolist()
                    else:
                        group_markers = "o"

                    ax.scatter(
                        group_data[x_axis_actual],
                        group_data[y_axis_actual],
                        c=[color],
                        marker=(
                            group_markers[0]
                            if isinstance(group_markers, list)
                            and len(group_markers) > 0
                            else group_markers
                        ),
                        alpha=alpha,
                        s=s,
                        label=group_label,
                    )

                if plot_type in ["line", "both"]:
                    # Sort by x-axis for line plots
                    sorted_data = group_data.sort_values(x_axis_actual)
                    ax.plot(
                        sorted_data[x_axis_actual],
                        sorted_data[y_axis_actual],
                        color=color,
                        alpha=alpha,
                        linewidth=2,
                        label=None,
                    )

            # Add legend for composition coloring
            if show_legend and len(groups) > 1:
                ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        else:
            # Standard plotting without composition grouping
            if plot_type in ["scatter", "both"]:
                ax.scatter(
                    combined_df[x_axis_actual],
                    combined_df[y_axis_actual],
                    c=point_colors,
                    marker=point_markers,
                    alpha=alpha,
                    s=s,
                )

            if plot_type in ["line", "both"]:
                # Sort by x-axis for line plots
                sorted_data = combined_df.sort_values(x_axis_actual)
                ax.plot(
                    sorted_data[x_axis_actual],
                    sorted_data[y_axis_actual],
                    color=point_colors,
                    alpha=alpha,
                    linewidth=2,
                )

    plt.tight_layout()

    # Save plot if requested
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Plot saved to: {save_path}")

    return fig


def interactive_plot_explorer(docs):
    """
    Interactive function to explore plotting options and create plots.

    Args:
        docs: Single FAIRFluidsDocument or list of FAIRFluidsDocument objects
    """
    # Discover options
    options = discover_plotting_options(docs)

    if "error" in options:
        print(f"Error: {options['error']}")
        return

    print("🔍 FAIRFluids Plotting Options Discovery")
    print("=" * 50)

    print(f"\n📊 Summary:")
    print(f"   Total measurements: {options['summary']['total_measurements']}")
    print(f"   Documents: {options['summary']['total_documents']}")
    print(f"   Property types: {options['summary']['property_types_count']}")
    print(f"   Unique compositions: {options['summary']['unique_compositions']}")

    print(f"\n📈 Available X-axis options:")
    for i, option in enumerate(options["x_axis_options"], 1):
        print(f"   {i:2d}. {option}")

    print(f"\n📈 Available Y-axis options:")
    for i, option in enumerate(options["y_axis_options"], 1):
        print(f"   {i:2d}. {option}")

    print(f"\n🎨 Available color options:")
    for i, option in enumerate(options["color_options"], 1):
        print(f"   {i:2d}. {option}")

    print(f"\n👥 Available grouping options:")
    for i, option in enumerate(options["grouping_options"], 1):
        print(f"   {i:2d}. {option}")

    print(f"\n🧪 Available compounds:")
    for i, compound in enumerate(options["compounds"], 1):
        print(f"   {i:2d}. {compound}")

    print(f"\n🔬 Available property types:")
    for i, prop_type in enumerate(options["property_types"], 1):
        print(f"   {i:2d}. {prop_type}")

    if options["temperature_range"]:
        print(f"\n🌡️ Temperature range:")
        print(
            f"   {options['temperature_range']['min']:.2f} - {options['temperature_range']['max']:.2f} {options['temperature_range']['unit']}"
        )

    print(f"\n💡 Example usage:")
    print(f"   # Basic plot")
    print(
        f"   fig = plot_fairfluids_data(docs, x_axis='temperature', y_axis='density')"
    )
    print(f"   ")
    print(f"   # Colored by composition")
    print(
        f"   fig = plot_fairfluids_data(docs, x_axis='temperature', y_axis='density', color_by='composition')"
    )
    print(f"   ")
    print(f"   # Grouped by composition")
    print(
        f"   fig = plot_fairfluids_data(docs, x_axis='temperature', y_axis='viscosity', group_by='composition')"
    )
    print(f"   ")
    print(f"   # Grouped by document")
    print(
        f"   fig = plot_fairfluids_data(docs, x_axis='temperature', y_axis='density', group_by='doc_label')"
    )
    print(f"   ")
    print(f"   # Filtered plot")
    print(
        f"   fig = plot_fairfluids_data(docs, x_axis='temperature', y_axis='density', property_type='density', fluid_compounds=['Water', 'ChCl'])"
    )

    return options


def classify_des_type(compounds):
    """
    Classify DES type based on compound composition.

    Args:
        compounds: List of compound names

    Returns:
        tuple: (des_type, type_indicators) where:
            - des_type: String representation of DES type (Ⅰ, Ⅱ, Ⅲ, Ⅳ, Ⅴ)
            - type_indicators: List of 5 integers indicating type presence [I, II, III, IV, V]
    """
    # Convert to lowercase for matching
    compounds_lower = [comp.lower() for comp in compounds]

    # DES Type I: Quaternary ammonium salt + metal chloride
    type_i_keywords = ["chloride", "bromide", "iodide", "acetate", "nitrate"]
    type_i_cations = ["ammonium", "choline", "tetrabutyl", "benzyl", "methyl", "ethyl"]

    # DES Type II: Metal chloride hydrate + quaternary ammonium salt
    type_ii_keywords = ["hydrate", "metal"]

    # DES Type III: Quaternary ammonium salt + hydrogen bond donor
    type_iii_keywords = [
        "glycerol",
        "urea",
        "thiourea",
        "phenol",
        "imidazole",
        "triazole",
        "benzotriazole",
        "tetrazole",
        "benzimidazole",
        "succinimide",
    ]

    # DES Type IV: Metal chloride + hydrogen bond donor
    type_iv_keywords = ["zinc", "aluminum", "iron", "copper", "tin"]

    # DES Type V: Non-ionic components
    type_v_keywords = ["menthol", "thymol", "camphor"]

    # Check for each type
    type_indicators = [0, 0, 0, 0, 0]

    # Check Type I
    has_cation = any(
        any(cation in comp for cation in type_i_cations) for comp in compounds_lower
    )
    has_anion = any(
        any(anion in comp for anion in type_i_keywords) for comp in compounds_lower
    )
    if has_cation and has_anion and len(compounds) == 2:
        type_indicators[0] = 1

    # Check Type II
    has_hydrate = any("hydrate" in comp for comp in compounds_lower)
    if has_hydrate and len(compounds) == 2:
        type_indicators[1] = 1

    # Check Type III
    has_hbd = any(
        any(hbd in comp for hbd in type_iii_keywords) for comp in compounds_lower
    )
    if has_hbd and len(compounds) == 2:
        type_indicators[2] = 1

    # Check Type IV
    has_metal = any(
        any(metal in comp for metal in type_iv_keywords) for comp in compounds_lower
    )
    if has_metal and len(compounds) == 2:
        type_indicators[3] = 1

    # Check Type V
    has_nonionic = any(
        any(nonionic in comp for nonionic in type_v_keywords)
        for comp in compounds_lower
    )
    if has_nonionic and len(compounds) == 2:
        type_indicators[4] = 1

    # Determine primary type
    if type_indicators[0] == 1:
        des_type = "Ⅰ"
    elif type_indicators[1] == 1:
        des_type = "Ⅱ"
    elif type_indicators[2] == 1:
        des_type = "Ⅲ"
    elif type_indicators[3] == 1:
        des_type = "Ⅳ"
    elif type_indicators[4] == 1:
        des_type = "Ⅴ"
    else:
        des_type = "Unknown"

    return des_type, type_indicators


def _extract_measurements_with_all_parameters(
    doc,
    property_types=None,
    fluid_compounds=None,
    required_compounds=None,
):
    """
    Helper function to extract measurements with all parameters included.

    This function is similar to filter_fluid_measurements but extracts ALL parameters,
    not just temperature and mole fractions.

    Args:
        doc: FAIRFluids document
        property_types: List of property types to filter by
        fluid_compounds: List of compounds to filter by
        required_compounds: List of required compounds

    Returns:
        List of measurement dictionaries with all parameters extracted
    """
    import pandas as pd

    # Convert single compound to list for consistent handling
    if isinstance(fluid_compounds, str):
        fluid_compounds = [fluid_compounds]

    if isinstance(required_compounds, str):
        required_compounds = [required_compounds]

    measurements = []

    for fluid in doc.fluid:
        # Build property lookup
        property_lookup = {}
        for p in getattr(fluid, "property", []):
            pid = getattr(p, "propertyID", None)
            if pid:
                property_lookup[pid] = p

        # Build parameter lookup
        parameter_lookup = {}
        for param in getattr(fluid, "parameter", []):
            pid = getattr(param, "parameterID", None)
            if pid:
                parameter_lookup[pid] = param

        # Get compound names for this fluid
        fluid_compound_names = []
        for comp_id in fluid.compounds:
            comp_name = str(comp_id)
            for compound in doc.compound:
                if str(compound.compoundID) == str(comp_id):
                    if hasattr(compound, "commonName") and compound.commonName:
                        comp_name = compound.commonName
                    break
            fluid_compound_names.append(comp_name)

        # Check filters
        if fluid_compounds is not None:
            if not all(comp in fluid_compound_names for comp in fluid_compounds):
                continue
            if len(fluid_compound_names) != len(fluid_compounds):
                continue

        if required_compounds is not None:
            if not all(comp in fluid_compound_names for comp in required_compounds):
                continue
            if len(fluid_compound_names) != len(required_compounds):
                continue

        # Process measurements
        for measurement in fluid.measurement:
            # Extract all parameters
            temperature = None
            mole_fractions = [None] * len(fluid_compound_names)
            all_parameters = {}  # Store all parameters here

            # Process each parameter value
            for param_val in measurement.parameterValue:
                param_def = parameter_lookup.get(param_val.parameterID)

                if param_def is not None:
                    param_obj = getattr(param_def, "parameter", None)
                    if param_obj is not None:
                        # Get parameter name
                        if hasattr(param_obj, "value"):
                            param_name = param_obj.value
                        else:
                            param_name = str(param_obj)

                        if not isinstance(param_name, str):
                            param_name = str(param_name)

                        # Store parameter value
                        all_parameters[param_name] = param_val.paramValue

                        # Special handling for temperature and mole fractions for backwards compatibility
                        if "temperature" in param_name.lower():
                            temperature = param_val.paramValue

                        elif "mole fraction" in param_name.lower():
                            associated_compounds = getattr(
                                param_def, "associated_compounds", []
                            )
                            associated_compound = (
                                associated_compounds[0]
                                if associated_compounds
                                else None
                            )
                            if associated_compound:
                                compound_name = str(associated_compound)

                                for compound in doc.compound:
                                    if str(compound.compoundID) == str(
                                        associated_compound
                                    ):
                                        if (
                                            hasattr(compound, "commonName")
                                            and compound.commonName
                                        ):
                                            compound_name = compound.commonName
                                        break

                                if compound_name == str(associated_compound):
                                    for compound in doc.compound:
                                        if (
                                            hasattr(compound, "commonName")
                                            and compound.commonName
                                            and compound.commonName
                                            == str(associated_compound)
                                        ):
                                            compound_name = compound.commonName
                                            break

                                if compound_name in fluid_compound_names:
                                    compound_index = fluid_compound_names.index(
                                        compound_name
                                    )
                                    mole_fractions[compound_index] = (
                                        param_val.paramValue
                                    )

            # Only process if we have complete mole fraction data and temperature
            if None not in mole_fractions and temperature is not None:
                # Normalize mole fractions
                mole_frac_sum = sum(mole_fractions)
                if mole_frac_sum > 0:
                    normalized_mole_fractions = [
                        mf / mole_frac_sum for mf in mole_fractions
                    ]
                else:
                    normalized_mole_fractions = mole_fractions

                # Process each property value
                for prop_val in measurement.propertyValue:
                    pdef = property_lookup.get(prop_val.propertyID)

                    if pdef is not None:
                        if hasattr(pdef, "properties") and pdef.properties is not None:
                            if hasattr(pdef.properties, "value"):
                                resolved_type = pdef.properties.value
                            else:
                                resolved_type = str(pdef.properties)
                        else:
                            resolved_type = prop_val.propertyID
                    else:
                        resolved_type = prop_val.propertyID

                    # Check property type filter
                    if (
                        property_types is not None
                        and resolved_type not in property_types
                    ):
                        continue

                    measurement_data = {
                        "fluid_compounds": fluid_compound_names,
                        "property_type": resolved_type,
                        "property_value": prop_val.propValue,
                        "uncertainty": getattr(prop_val, "uncertainty", None),
                        "temperature": temperature,
                        "mole_fractions": normalized_mole_fractions,
                        "measurement_id": getattr(measurement, "measurement_id", None),
                        "source_doi": getattr(measurement, "source_doi", None),
                    }

                    # Add all parameters to the measurement data
                    measurement_data.update(all_parameters)

                    measurements.append(measurement_data)

    return measurements


def extract_fairfluids_data(
    docs,
    property_types=None,
    fluid_compounds=None,
    required_compounds=None,
    decimal_places=3,
):
    """
    Extract data from one or more FAIRFluids documents into a pandas DataFrame.

    This function extracts all available properties AND all parameters from FAIRFluids documents
    while maintaining the original DataFrame structure with additional property and parameter
    columns for easier analysis.

    Args:
        docs: Single FAIRFluidsDocument or list of FAIRFluidsDocument objects
        property_types: List of property types to include (e.g., ['density', 'viscosity'])
                       If None, includes all properties
        fluid_compounds: List of compound names to filter by (e.g., ['Water', 'ChCl'])
                        If None, includes all fluids. Requires exact match.
        required_compounds: List of compounds that must ALL be present in a fluid block for it to be included.
                           This is useful for the composition-based approach where you want to ensure
                           all specified compounds are present before extracting properties.
        decimal_places: Number of decimal places to round mole fractions to (default: 3)

    Returns:
        pandas.DataFrame: DataFrame with columns:
            - fluid_compounds: List of compound names
            - property_type: Type of property measured
            - property_value: Measured value
            - uncertainty: Measurement uncertainty (if available)
            - temperature: Temperature in K
            - mole_fractions: List of mole fractions (rounded)
            - mole_fraction_<compound>: Individual mole fraction columns
            - measurement_id: Unique measurement identifier
            - source_doi: Source DOI (if available)
            - doc_label: Label for the source document
            - <property>_value: Property value columns for each property type
            - <property>_uncertainty: Uncertainty columns for each property type
            - <parameter>: Parameter value columns for each parameter found (e.g., pressure, pH, etc.)
    """
    import pandas as pd

    # Ensure docs is a list
    if not isinstance(docs, list):
        docs = [docs]

    all_measurements = []

    for doc_idx, doc in enumerate(docs):
        # Get all measurements with all parameters
        measurements = _extract_measurements_with_all_parameters(
            doc,
            property_types=property_types,
            fluid_compounds=fluid_compounds,
            required_compounds=required_compounds,
        )

        # Add document label
        for measurement in measurements:
            measurement["doc_label"] = f"Document_{doc_idx + 1}"
            all_measurements.append(measurement)

    if not all_measurements:
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame(all_measurements)

    # Round mole fractions to avoid floating point precision issues
    if "mole_fractions" in df.columns:
        df["mole_fractions_rounded"] = df["mole_fractions"].apply(
            lambda x: tuple(round(f, decimal_places) if f is not None else f for f in x)
        )

        # Create individual mole fraction columns
        if len(df) > 0:
            compounds = df["fluid_compounds"].iloc[0]
            for i, compound in enumerate(compounds):
                df[f"mole_fraction_{compound}"] = df["mole_fractions_rounded"].apply(
                    lambda x: x[i] if i < len(x) else None
                )

    # Create additional property columns for easier analysis
    # Group by composition and temperature to create property columns
    if len(df) > 0:
        # Create a unique identifier for each composition-temperature combination
        df["composition_temp_id"] = df.apply(
            lambda row: (
                tuple(sorted(row["fluid_compounds"])),
                row["temperature"],
                row.get("measurement_id", ""),
            ),
            axis=1,
        )

        # Create property columns for each property type
        property_types_found = df["property_type"].unique()

        for prop_type in property_types_found:
            # Skip empty or None property types
            if not prop_type or prop_type == "" or pd.isna(prop_type):
                continue

            prop_mask = df["property_type"] == prop_type
            prop_data = df[prop_mask].copy()

            # Create property value column (ensure valid column name)
            prop_value_col = f"{prop_type}_value"
            if prop_value_col and prop_value_col.strip():
                df[prop_value_col] = None
                df.loc[prop_mask, prop_value_col] = prop_data["property_value"]

            # Create uncertainty column if available (ensure valid column name)
            if "uncertainty" in df.columns:
                prop_uncertainty_col = f"{prop_type}_uncertainty"
                if prop_uncertainty_col and prop_uncertainty_col.strip():
                    df[prop_uncertainty_col] = None
                    df.loc[prop_mask, prop_uncertainty_col] = prop_data["uncertainty"]

    return df


def debug_dataframe_columns(df):
    """
    Debug function to identify problematic columns in a DataFrame.

    Args:
        df: pandas.DataFrame to debug

    Returns:
        dict: Debug information about the DataFrame columns
    """
    debug_info = {
        "total_columns": len(df.columns),
        "empty_columns": [],
        "whitespace_columns": [],
        "none_columns": [],
        "all_columns": list(df.columns),
    }

    for col in df.columns:
        if col == "":
            debug_info["empty_columns"].append(col)
        elif col is None:
            debug_info["none_columns"].append(col)
        elif isinstance(col, str) and col.strip() == "":
            debug_info["whitespace_columns"].append(col)

    print("🔍 DataFrame Column Debug Info:")
    print(f"   Total columns: {debug_info['total_columns']}")
    print(f"   Empty string columns: {debug_info['empty_columns']}")
    print(f"   None columns: {debug_info['none_columns']}")
    print(f"   Whitespace-only columns: {debug_info['whitespace_columns']}")
    print(f"   All columns: {debug_info['all_columns']}")

    return debug_info


def example_data_usage():
    """
    Example usage of the extract_fairfluids_data function.

    This function demonstrates how to use the data extraction to get
    all available properties while maintaining the DataFrame structure.
    """
    import json

    print("📊 Example: Extracting FAIRFluids data with all properties")
    print("=" * 60)

    print("\n1. Load FAIRFluids document from JSON:")
    print("   with open('fairfluids_document.json', 'r') as f:")
    print("       data = json.load(f)")
    print("   doc = FAIRFluidsDocument(**data)")

    print("\n2. Extract all data with all properties:")
    print("   df = extract_fairfluids_data(doc)")

    print("\n3. Extract specific properties only:")
    print(
        "   df = extract_fairfluids_data(doc, property_types=['viscosity', 'density'])"
    )

    print("\n4. Filter by specific compounds:")
    print(
        "   df = extract_fairfluids_data(doc, fluid_compounds=['Choline chloride', 'Urea'])"
    )

    print("\n5. Filter by required compounds (exact match):")
    print(
        "   df = extract_fairfluids_data(doc, required_compounds=['Choline chloride', 'Urea'])"
    )

    print("\n📋 Output DataFrame structure:")
    print("   - fluid_compounds: List of compound names")
    print("   - property_type: Type of property measured")
    print("   - property_value: Measured value")
    print("   - uncertainty: Measurement uncertainty (if available)")
    print("   - temperature: Temperature in K")
    print("   - mole_fractions: List of mole fractions (rounded)")
    print("   - mole_fraction_<compound>: Individual mole fraction columns")
    print("   - measurement_id: Unique measurement identifier")
    print("   - source_doi: Source DOI (if available)")
    print("   - doc_label: Label for the source document")
    print("   - <property>_value: Property value columns for each property type")
    print("   - <property>_uncertainty: Uncertainty columns for each property type")
    print("   - <parameter>: Parameter columns (e.g., pressure, pH, molarity, etc.)")
    print(
        "                   These are automatically extracted from all parameter definitions"
    )

    print("\n⚗️ Available Properties (from FAIRFluids schema):")
    properties = [
        "density",
        "viscosity",
        "specificHeatCapacity",
        "thermalConductivity",
        "meltingPoint",
        "boilingPoint",
        "vaporPressure",
        "compressibility",
        "pH",
        "polarity",
        "refractiveIndex",
        "surfaceTension",
        "diffusionCoefficient",
        "excessMolarVolume",
        "excessMolarEnthalpy",
        "excessMolarEntropy",
        "excessMolarGibbsFreeEnergy",
        "criticalTemperature",
        "criticalPressure",
        "criticalDensity",
        "criticalVolume",
        "triplePointTemperature",
        "triplePointPressure",
        "henrysLawConstant",
        "osmoticCoefficient",
        "activityCoefficient",
        "fugacityCoefficient",
        "ionicStrength",
        "isobaricExpansionCoefficient",
        "isothermalCompressibility",
        "molarVolume",
        "specificVolume",
        "molarEnthalpy",
        "molarEntropy",
        "gibbsFreeEnergy",
        "helmholtzFreeEnergy",
        "speedOfSound",
    ]

    for i, prop in enumerate(properties, 1):
        print(f"   {i:2d}. {prop}")

    print(f"\n💡 This format provides:")
    print(f"   - Original DataFrame structure for compatibility")
    print(f"   - All available properties from FAIRFluids documents")
    print(f"   - Individual property columns for easy analysis")
    print(f"   - Uncertainty information when available")
    print(f"   - Mole fraction columns for each compound")
    print(f"   - Easy integration with existing plotting functions")


def plot_dataframe(
    df,
    x_axis,
    y_axis,
    color_by=None,
    group_by=None,
    plot_type="scatter",
    figsize=(12, 8),
    title=None,
    save_path=None,
    show_legend=True,
    alpha=0.7,
    s=50,
):
    """
    Create plots from a pandas DataFrame containing FAIRFluids data.

    This function provides a clean interface for plotting data that has been
    extracted using extract_fairfluids_data().

    Args:
        df: pandas.DataFrame from extract_fairfluids_data()
        x_axis: Column name for x-axis
        y_axis: Column name for y-axis
        color_by: Column name for coloring points (optional)
        group_by: Column name for grouping data (optional)
        plot_type: Type of plot ('scatter', 'line', 'both')
        figsize: Figure size tuple
        title: Custom title for the plot
        save_path: Path to save the plot (optional)
        show_legend: Whether to show legend
        alpha: Transparency for scatter points
        s: Size of scatter points

    Returns:
        matplotlib.figure.Figure: The created figure
    """
    import matplotlib.pyplot as plt
    import numpy as np

    if df.empty:
        raise ValueError("DataFrame is empty")

    # Check if required columns exist
    if x_axis not in df.columns:
        raise ValueError(
            f"Column '{x_axis}' not found. Available columns: {list(df.columns)}"
        )
    if y_axis not in df.columns:
        raise ValueError(
            f"Column '{y_axis}' not found. Available columns: {list(df.columns)}"
        )

    # Create the plot
    fig, ax = plt.subplots(figsize=figsize)

    # Generate title if not provided
    if title is None:
        title = f"{y_axis} vs {x_axis}"
        if "property_type" in df.columns:
            prop_types = df["property_type"].unique()
            if len(prop_types) == 1:
                title += f" ({prop_types[0]})"

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(x_axis.replace("_", " ").title())
    ax.set_ylabel(y_axis.replace("_", " ").title())
    ax.grid(True, alpha=0.3)

    # Handle grouping
    if group_by and group_by in df.columns:
        groups = df.groupby(group_by)
        colors = plt.cm.tab10(np.linspace(0, 1, min(len(groups), 10)))

        for i, (group_name, group_data) in enumerate(groups):
            if i >= 10:  # Limit to 10 groups for clarity
                break

            color = colors[i]

            # Format group label
            if group_by == "mole_fractions_rounded":
                # Special handling for composition grouping
                compounds = (
                    group_data["fluid_compounds"].iloc[0] if len(group_data) > 0 else []
                )
                group_label = format_composition_label(group_name, compounds)
            else:
                group_label = str(group_name)

            # Plot data
            if plot_type in ["scatter", "both"]:
                ax.scatter(
                    group_data[x_axis],
                    group_data[y_axis],
                    c=[color],
                    alpha=alpha,
                    s=s,
                    label=group_label,
                )

            if plot_type in ["line", "both"]:
                # Sort by x-axis for line plots
                sorted_data = group_data.sort_values(x_axis)
                ax.plot(
                    sorted_data[x_axis],
                    sorted_data[y_axis],
                    color=color,
                    alpha=alpha,
                    linewidth=2,
                    label=None,  # Don't duplicate labels when both scatter and line
                )

        # Add legend
        if show_legend and len(groups) > 1:
            ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

    else:
        # No grouping
        if plot_type in ["scatter", "both"]:
            ax.scatter(df[x_axis], df[y_axis], alpha=alpha, s=s)

        if plot_type in ["line", "both"]:
            sorted_data = df.sort_values(x_axis)
            ax.plot(sorted_data[x_axis], sorted_data[y_axis], alpha=alpha, linewidth=2)

    plt.tight_layout()

    # Save plot if requested
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Plot saved to: {save_path}")

    return fig
