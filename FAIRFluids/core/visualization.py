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
    viscosity_data = doc.get_viscosity_data()
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

def plot_viscosity_vs_temperature(doc, component_name, fit_arrhenius=False, print_table=False, save_fig=False):
    """
    Create a plot of ln(viscosity) vs 1/RT for a FAIRFluids document.
    Groups data points by mole fraction of the selected component.
    
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
    """
    viscosity_data = doc.get_viscosity_data()
    compounds = viscosity_data[0]['compound_identifiers']
    
    activation_energies, mole_frac_groups = calculate_activation_energies(doc, component_name)

    # Create plot
    plt.figure(figsize=(8,6), dpi=300)

    # Plot each group
    for mole_frac, values in sorted(mole_frac_groups.items()):
        scatter = plt.scatter(values['temps'], values['visc'], 
                   label=f'χ({component_name}) = {mole_frac:.3f}')
        
        if fit_arrhenius and mole_frac in activation_energies:
            fit_results = fit_arrhenius_equation(values['temps'], values['visc'])
            if fit_results:
                ln_eta0, Ea, x_fit, y_fit = fit_results
                plt.plot(x_fit, y_fit, '--', alpha=0.7, color=scatter.get_facecolor()[0])

    plt.xlabel('1/RT (mol/J)')
    plt.ylabel('ln(η) (mPa·s)')
    plt.title(f'Arrhenius Plot for {'-'.join(compounds)} System')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
              title=f'{component_name} Content')
    plt.tight_layout()
    if save_fig:
        plt.savefig('viscosity_plot.png', dpi=300, bbox_inches='tight')
    plt.show()

    if print_table and activation_energies:
        # Create pandas DataFrame for activation energies
        df = pd.DataFrame({
            'Mole Fraction': list(activation_energies.keys()),
            'Activation Energy (kJ/mol)': [Ea/1000 for Ea in activation_energies.values()]
        })
        df = df.sort_values('Mole Fraction').reset_index(drop=True)
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