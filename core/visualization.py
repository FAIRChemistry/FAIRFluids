import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

def arrhenius(x, ln_eta0, Ea):
    """
    Arrhenius equation: ln(η) = ln(η₀) + Ea/(RT)
    x = 1/(RT)
    ln_eta0 = ln(η₀)
    Ea = activation energy
    """
    return ln_eta0 + Ea*x

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
    compounds = viscosity_data[0]['compound_identifiers']
    
    try:
        component_index = compounds.index(component_name)
    except ValueError:
        raise ValueError(f"Component '{component_name}' not found. Available components: {compounds}")

    R = 8.314  # J/(mol·K)
    mole_frac_groups = {}
    activation_energies = {}

    # Group data by mole fractions
    for data in viscosity_data:
        mole_fraction = round(data['mole_fractions'][component_index], 3)
        if mole_fraction not in mole_frac_groups:
            mole_frac_groups[mole_fraction] = {'temps': [], 'visc': []}
        
        mole_frac_groups[mole_fraction]['temps'].append(1/(R*data['temperature']))
        mole_frac_groups[mole_fraction]['visc'].append(np.log(data['viscosity']))

    # Calculate activation energy for each group
    for mole_frac, values in mole_frac_groups.items():
        fit_results = fit_arrhenius_equation(values['temps'], values['visc'])
        if fit_results:
            ln_eta0, Ea, _, _ = fit_results
            activation_energies[mole_frac] = Ea

    return activation_energies, mole_frac_groups

def plot_viscosity_vs_temperature(doc, component_name = None, fit_arrhenius=False, print_table=False, save_fig=False, group=None):
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
    """
    viscosity_data = get_viscosity_data_with_meta(doc)
    compounds = viscosity_data[0]['compound_identifiers'] if viscosity_data else []

    if component_name is not None:
        activation_energies, mole_frac_groups = calculate_activation_energies(doc, component_name)
        group_labels = sorted(mole_frac_groups.keys())
        group_dict = mole_frac_groups
        group_label_func = lambda mf: f'χ({component_name}) = {mf:.3f}'
    elif group in ('source_doi', 'method'):
        # Group by source_doi or method
        group_dict = {}
        for data in viscosity_data:
            key = data.get(group, 'unknown')
            if key not in group_dict:
                group_dict[key] = {'temps': [], 'visc': [], 'raw': []}
            R = 8.314
            group_dict[key]['temps'].append(1/(R*data['temperature']))
            group_dict[key]['visc'].append(np.log(data['viscosity']))
            group_dict[key]['raw'].append(data)
        group_labels = sorted(group_dict.keys())
        activation_energies = {}
        for key in group_labels:
            fit_results = fit_arrhenius_equation(group_dict[key]['temps'], group_dict[key]['visc'])
            if fit_results:
                ln_eta0, Ea, _, _ = fit_results
                activation_energies[key] = Ea
        group_label_func = lambda k: f'{group}={k}'
    else:
        raise ValueError("If component_name is None, you must set group to 'source_doi' or 'method'.")

    # Create plot
    plt.figure(figsize=(8,6), dpi=300)

    # Plot each group
    for label in group_labels:
        values = group_dict[label]
        scatter = plt.scatter(values['temps'], values['visc'], 
                   label=group_label_func(label))
        if fit_arrhenius and label in activation_energies:
            fit_results = fit_arrhenius_equation(values['temps'], values['visc'])
            if fit_results:
                ln_eta0, Ea, x_fit, y_fit = fit_results
                plt.plot(x_fit, y_fit, '--', alpha=0.7, color=scatter.get_facecolor()[0])

    plt.xlabel('1/RT (mol/J)')
    plt.ylabel('ln(η) (mPa·s)')
    if component_name is not None:
        plt.title(f'Arrhenius Plot for {'-'.join(compounds)} System')
        legend_title = f'{component_name} Content'
    else:
        plt.title(f'Arrhenius Plot for {'-'.join(compounds)} System (Grouped by {group})')
        legend_title = group
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
              title=legend_title)
    plt.tight_layout()
    if save_fig:
        plt.savefig('viscosity_plot.png', dpi=300, bbox_inches='tight')
    plt.show()

    if print_table and activation_energies:
        # Create pandas DataFrame for activation energies
        df = pd.DataFrame({
            'Group': list(activation_energies.keys()),
            'Activation Energy (kJ/mol)': [Ea/1000 for Ea in activation_energies.values()]
        })
        df = df.sort_values('Group').reset_index(drop=True)
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
        # Get compound names or IDs
        compounds = []
        for idx in fluid.compounds:
            comp = None
            for c in doc.compound:
                if str(c.compoundID) == str(idx):
                    comp = c
                    break
            if comp and comp.commonName:
                compounds.append(comp.commonName)
            elif comp and comp.compoundID:
                compounds.append(str(comp.compoundID))
            else:
                compounds.append(str(idx))
        for meas in fluid.measurement:
            viscosity = None
            for pv in meas.propertyValue:
                if pv.propertyID == 'viscosity':
                    viscosity = pv.propValue
            temperature = None
            mole_fractions = []
            for par_val in meas.parameterValue:
                if par_val.parameterID.startswith('T_'):
                    temperature = par_val.paramValue
                if par_val.parameterID.startswith('x_'):
                    mole_fractions.append(par_val.paramValue)
            if viscosity is not None and temperature is not None and mole_fractions:
                data.append({
                    'compound_identifiers': compounds,
                    'mole_fractions': mole_fractions,
                    'temperature': temperature,
                    'viscosity': viscosity
                })
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
        # Get compound names or IDs
        compounds = []
        for idx in fluid.compounds:
            comp = None
            for c in doc.compound:
                if str(c.compoundID) == str(idx):
                    comp = c
                    break
            if comp and comp.commonName:
                compounds.append(comp.commonName)
            elif comp and comp.compoundID:
                compounds.append(str(comp.compoundID))
            else:
                compounds.append(str(idx))
        for meas in fluid.measurement:
            viscosity = None
            for pv in meas.propertyValue:
                if pv.propertyID == 'viscosity':
                    viscosity = pv.propValue
            temperature = None
            mole_fractions = []
            for par_val in meas.parameterValue:
                if par_val.parameterID.startswith('T_'):
                    temperature = par_val.paramValue
                if par_val.parameterID.startswith('x_'):
                    mole_fractions.append(par_val.paramValue)
            if viscosity is not None and temperature is not None and mole_fractions:
                data.append({
                    'compound_identifiers': compounds,
                    'mole_fractions': mole_fractions,
                    'temperature': temperature,
                    'viscosity': viscosity,
                    'source_doi': getattr(meas, 'source_doi', None),
                    'method': getattr(meas, 'method', None).name if getattr(meas, 'method', None) else None
                })
    return data 

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
            method_name = getattr(meas.method, 'name', str(meas.method)).lower() if getattr(meas, 'method', None) else ''
            if group.lower() == 'simulated':
                if 'simul' in method_name:
                    filtered_measurements.append(meas)
            elif group.lower() == 'measured':
                if 'measured' in method_name or 'experimental' in method_name:
                    filtered_measurements.append(meas)
            elif isinstance(group, str):
                # Assume group is a DOI string
                if getattr(meas, 'source_doi', None) == group:
                    filtered_measurements.append(meas)
        fluid.measurement = filtered_measurements
    return filtered_doc 