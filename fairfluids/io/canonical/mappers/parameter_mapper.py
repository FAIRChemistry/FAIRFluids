"""
Parameter Mapper.

Resolves ThermoML variable / constraint type strings to FAIRFluids
``Parameters`` enum members.  Fully self-contained.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from fairfluids.core.lib import Parameters

logger = logging.getLogger(__name__)

PARAMETER_MAP: Dict[str, str] = {
    # Temperature
    "Temperature, K": "TEMPERATURE",
    "Temperature": "TEMPERATURE",
    "Lower temperature, K": "LOWER_TEMPERATURE",
    "Upper temperature, K": "UPPER_TEMPERATURE",
    # Pressure
    "Pressure, kPa": "PRESSURE",
    "Pressure": "PRESSURE",
    "Lower pressure, kPa": "LOWER_PRESSURE",
    "Upper pressure, kPa": "UPPER_PRESSURE",
    "Partial pressure, kPa": "PARTIAL_PRESSURE",
    # Composition
    "Mole fraction": "MOLE_FRACTION",
    "Mass fraction": "MASS_FRACTION",
    "Volume fraction": "VOLUME_FRACTION",
    "Molality, mol/kg": "MOLALITY",
    "Amount concentration (molarity), mol/dm3": "AMOUNT_CONCENTRATION_MOLARITY",
    "Amount density, mol/m3": "AMOUNT_DENSITY",
    "Amount, mol": "AMOUNT_MOL",
    "Mass, kg": "MASS",
    "Mass density, kg/m3": "MASS_DENSITY",
    # Solute/solvent ratios
    "Amount ratio of solute to solvent": "AMOUNT_RATIO_OF_SOLUTE_TO_SOLVENT",
    "Mass ratio of solute to solvent": "MASS_RATIO_OF_SOLUTE_TO_SOLVENT",
    "Volume ratio of solute to solvent": "VOLUME_RATIO_OF_SOLUTE_TO_SOLVENT",
    # Initial/final
    "Initial mole fraction of solute": "INITIAL_MOLE_FRACTION_OF_SOLUTE",
    "Final mole fraction of solute": "FINAL_MOLE_FRACTION_OF_SOLUTE",
    "Initial mass fraction of solute": "INITIAL_MASS_FRACTION_OF_SOLUTE",
    "Final mass fraction of solute": "FINAL_MASS_FRACTION_OF_SOLUTE",
    "Initial molality of solute, mol/kg": "INITIAL_MOLALITY_OF_SOLUTE",
    "Final molality of solute, mol/kg": "FINAL_MOLALITY_OF_SOLUTE",
    # Solvent composition
    "Solvent: Mole fraction": "SOLVENT_MOLE_FRACTION",
    "Solvent: Mass fraction": "SOLVENT_MASS_FRACTION",
    "Solvent: Volume fraction": "SOLVENT_VOLUME_FRACTION",
    "Solvent: Molality, mol/kg": "SOLVENT_MOLALITY",
    "Solvent: Amount concentration (molarity), mol/dm3": "SOLVENT_AMOUNT_CONCENTRATION_MOLARITY",
    "Solvent: Amount ratio of component to other component of binary solvent": "SOLVENT_AMOUNT_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT",
    "Solvent: Mass ratio of component to other component of binary solvent": "SOLVENT_MASS_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT",
    "Solvent: Volume ratio of component to other component of binary solvent": "SOLVENT_VOLUME_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT",
    "Solvent: Ratio of amount of component to mass of solvent, mol/kg": "SOLVENT_RATIO_OF_AMOUNT_OF_COMPONENT_TO_MASS_OF_SOLVENT",
    "Solvent: Ratio of component mass to volume of solvent, kg/m3": "SOLVENT_RATIO_OF_COMPONENT_MASS_TO_VOLUME_OF_SOLVENT",
    # Concentration ratios
    "Ratio of amount of solute to mass of solution, mol/kg": "RATIO_OF_AMOUNT_OF_SOLUTE_TO_MASS_OF_SOLUTION",
    "Ratio of mass of solute to volume of solution, kg/m3": "RATIO_OF_MASS_OF_SOLUTE_TO_VOLUME_OF_SOLUTION",
    # Activity / misc
    "Activity coefficient": "ACTIVITY_COEFFICIENT",
    "(Relative) activity": "RELATIVE_ACTIVITY",
    "Molar volume, m3/mol": "MOLAR_VOLUME",
    "Specific volume, m3/kg": "SPECIFIC_VOLUME",
    "Molar entropy, J/K/mol": "MOLAR_ENTROPY",
    "Frequency, MHz": "FREQUENCY",
    "Wavelength, nm": "WAVELENGTH",
}


class ParameterMapper:
    """Maps ThermoML variable/constraint type strings to ``Parameters`` enum."""

    @staticmethod
    def map(thermoml_name: str) -> Optional[Parameters]:
        key = PARAMETER_MAP.get(thermoml_name)
        if key is not None:
            try:
                return Parameters[key]
            except KeyError:
                logger.warning("Parameters enum has no member '%s'", key)
                return None

        for member in Parameters:
            if member.value.lower() == thermoml_name.strip().lower():
                return member

        logger.warning(
            "No FAIRFluids parameter mapping for ThermoML name: '%s'",
            thermoml_name,
        )
        return None
