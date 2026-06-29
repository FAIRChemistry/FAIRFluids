"""
Property Mapper.

Resolves ThermoML ``ePropName`` strings to FAIRFluids ``Properties`` enum
members.  All mapping data is self-contained — no external dependencies
beyond ``fairfluids.core.lib``.
"""

from __future__ import annotations

import logging
import re
import warnings
from typing import Dict, Optional

from fairfluids.core.lib import Properties

logger = logging.getLogger(__name__)

PROPERTY_MAP: Dict[str, str] = {
    # Density
    "Mass density, kg/m3": "DENSITY",
    "Mass density, kg/m³": "DENSITY",
    "Density, kg/m3": "DENSITY",
    "Density, kg/m³": "DENSITY",
    # Viscosity
    "Dynamic viscosity, Pa*s": "VISCOSITY",
    "Dynamic viscosity, Pa·s": "VISCOSITY",
    "Kinematic viscosity, m2/s": "KINEMATIC_VISCOSITY",
    "Shear viscosity, Pa*s": "VISCOSITY",
    "Viscosity, Pas": "VISCOSITY",
    "Viscosity, Pa*s": "VISCOSITY",
    "Viscosity, mPa*s": "VISCOSITY",
    # Thermal conductivity
    "Thermal conductivity, W/(m*K)": "THERMAL_CONDUCTIVITY",
    "Thermal conductivity, W/(m·K)": "THERMAL_CONDUCTIVITY",
    # Conductivity
    "Conductivity, S/m": "ELECTRICAL_CONDUCTIVITY",
    "Electrical conductivity, S/m": "ELECTRICAL_CONDUCTIVITY",
    # Heat capacity
    "Heat capacity, J/(mol*K)": "SPECIFIC_HEAT_CAPACITY",
    "Heat capacity, J/(mol·K)": "SPECIFIC_HEAT_CAPACITY",
    "Molar heat capacity at constant pressure, J/K/mol": "SPECIFIC_HEAT_CAPACITY",
    "Specific heat capacity at constant pressure, J/K/kg": "SPECIFIC_HEAT_CAPACITY",
    "Heat capacity at constant pressure, J/(mol*K)": "SPECIFIC_HEAT_CAPACITY",
    "Heat capacity at constant pressure per mole, J/mol/K": "SPECIFIC_HEAT_CAPACITY",
    # Enthalpy
    "Molar enthalpy, J/mol": "MOLAR_ENTHALPY",
    "Molar enthalpy, kJ/mol": "MOLAR_ENTHALPY",
    # Entropy
    "Molar entropy, J/(mol·K)": "MOLAR_ENTROPY",
    "Molar entropy, J/K/mol": "MOLAR_ENTROPY",
    # Vapor / boiling
    "Vapor pressure, kPa": "VAPOR_PRESSURE",
    "Vapor or sublimation pressure, kPa": "VAPOR_PRESSURE",
    "Vapor pressure, Pa": "VAPOR_PRESSURE",
    "Boiling point, K": "BOILING_POINT",
    "Boiling temperature, K": "BOILING_POINT",
    "Normal boiling temperature, K": "BOILING_POINT",
    # Melting / triple point
    "Melting point, K": "MELTING_POINT",
    "Melting temperature, K": "MELTING_POINT",
    "Normal melting temperature, K": "MELTING_POINT",
    "Triple point temperature, K": "TRIPLE_POINT_TEMPERATURE",
    "Triple point pressure, kPa": "TRIPLE_POINT_PRESSURE",
    # Critical properties
    "Critical temperature, K": "CRITICAL_TEMPERATURE",
    "Critical pressure, kPa": "CRITICAL_PRESSURE",
    "Critical pressure, Pa": "CRITICAL_PRESSURE",
    "Critical density, kg/m3": "CRITICAL_DENSITY",
    "Critical volume, m3/mol": "CRITICAL_VOLUME",
    "Critical point pressure, kPa": "CRITICAL_POINT_PRESSURE",
    "Critical point temperature, K": "CRITICAL_POINT_TEMPERATURE",
    "Critical compressibility factor": "COMPRESSIBILITY",
    # Volume / molar volume
    "Molar volume, m3/mol": "MOLAR_VOLUME",
    "Molar volume, cm3/mol": "MOLAR_VOLUME",
    "Specific volume, m3/kg": "SPECIFIC_VOLUME",
    "Excess molar volume, m3/mol": "EXCESS_MOLAR_VOLUME",
    # Compressibility
    "Compressibility": "COMPRESSIBILITY",
    "Compressibility factor, Z": "COMPRESSIBILITY",
    "Isothermal compressibility, 1/Pa": "ISOTHERMAL_COMPRESSIBILITY",
    "Isothermal compressibility, 1/kPa": "ISOTHERMAL_COMPRESSIBILITY",
    "Isobaric expansion coefficient, 1/K": "ISOBARIC_EXPANSION_COEFFICIENT",
    "Isobaric coefficient of expansion, 1/K": "ISOBARIC_EXPANSION_COEFFICIENT",
    # Surface / optical / acoustic
    "Surface tension, N/m": "SURFACE_TENSION",
    "Surface tension liquid-gas, N/m": "SURFACE_TENSION",
    "Surface tension, mN/m": "SURFACE_TENSION",
    "Refractive index": "REFRACTIVE_INDEX",
    "Refractive index (sodium D-line)": "REFRACTIVE_INDEX",
    "Refractive index (Na D-line)": "REFRACTIVE_INDEX",
    "Speed of sound, m/s": "SPEED_OF_SOUND",
    # Diffusion
    "Diffusion coefficient, m2/s": "DIFFUSION_COEFFICIENT",
    "Self diffusion coefficient, m2/s": "DIFFUSION_COEFFICIENT",
    "Self-diffusion coefficient, m2/s": "DIFFUSION_COEFFICIENT",
    # Activity / fugacity / osmotic
    "Activity coefficient": "ACTIVITY_COEFFICIENT",
    "Activity": "ACTIVITY",
    "(Relative) activity": "ACTIVITY",
    "Fugacity coefficient": "FUGACITY_COEFFICIENT",
    "Fugacity coefficient of a component": "FUGACITY_COEFFICIENT",
    "Osmotic coefficient": "OSMOTIC_COEFFICIENT",
    "Henry's law constant, Pa": "HENRYS_LAW_CONSTANT",
    "Henry's law constant, kPa": "HENRYS_LAW_CONSTANT",
    "Henry's Law constant (amount concentration scale), kPadm3/mol": "HENRYS_LAW_CONSTANT",
    # Excess energy
    "Excess molar enthalpy, J/mol": "EXCESS_MOLAR_ENTHALPY",
    "Excess molar enthalpy (molar enthalpy of mixing), J/mol": "EXCESS_MOLAR_ENTHALPY",
    "Excess molar enthalpy (molar enthalpy of mixing), kJ/mol": "EXCESS_MOLAR_ENTHALPY",
    "Excess molar entropy, J/(mol·K)": "EXCESS_MOLAR_ENTROPY",
    "Excess molar Gibbs free energy, J/mol": "EXCESS_MOLAR_GIBBS_FREE_ENERGY",
    "Excess molar Gibbs energy, J/mol": "EXCESS_MOLAR_GIBBS_FREE_ENERGY",
    # Gibbs / Helmholtz
    "Gibbs free energy, J/mol": "GIBBS_FREE_ENERGY",
    "Helmholtz free energy, J/mol": "HELMHOLTZ_FREE_ENERGY",
    # Ionic / biological
    "pH": "PH",
    "Ionic strength, mol/kg": "IONIC_STRENGTH",
    # Polarity
    "Polarity": "POLARITY",
    # Electrical conductivity
    "Electrical conductivity, S/m": "ELECTRICAL_CONDUCTIVITY",
    # Molar heat capacity
    "Molar heat capacity at constant pressure, J/(mol*K)": "MOLAR_HEAT_CAPACITY",
    "Molar heat capacity at constant pressure, J/(mol·K)": "MOLAR_HEAT_CAPACITY",
    "Molar heat capacity, J/(mol*K)": "MOLAR_HEAT_CAPACITY",
    "Molar heat capacity, J/(mol·K)": "MOLAR_HEAT_CAPACITY",
}


class PropertyMapper:
    """Maps ThermoML ``ePropName`` strings to ``Properties`` enum members."""

    @staticmethod
    def map(thermoml_name: str) -> Optional[Properties]:
        key = PROPERTY_MAP.get(thermoml_name)
        if key is not None:
            try:
                return Properties[key]
            except KeyError:
                logger.warning("Properties enum has no member '%s'", key)
                warnings.warn(
                    f"Unknown property mapping target in FAIRFluids enum: '{key}' (source: '{thermoml_name}')",
                    UserWarning,
                    stacklevel=2,
                )
                return None

        normalised = re.sub(r"\s+", " ", thermoml_name.strip().lower())
        for map_key, map_val in PROPERTY_MAP.items():
            if re.sub(r"\s+", " ", map_key.strip().lower()) == normalised:
                try:
                    return Properties[map_val]
                except KeyError:
                    warnings.warn(
                        f"Unknown property mapping target in FAIRFluids enum: '{map_val}' (source: '{thermoml_name}')",
                        UserWarning,
                        stacklevel=2,
                    )
                    return None

        for member in Properties:
            if member.value.lower() == normalised:
                return member

        logger.warning(
            "No FAIRFluids property mapping for ThermoML name: '%s'",
            thermoml_name,
        )
        warnings.warn(
            f"Unknown ThermoML property encountered: '{thermoml_name}'",
            UserWarning,
            stacklevel=2,
        )
        return None
