"""
ThermoML to FAIRFluids Conversion Utilities

This module contains utility functions for converting ThermoML XML elements
to FAIRFluids format, including property mappings, unit conversions, and
data validation.
"""

import re
from typing import Dict, List, Optional, Any, Union
from xml.etree import ElementTree as ET


class ThermoMLPropertyMapper:
    """Maps ThermoML property names to FAIRFluids Properties enum values."""

    PROPERTY_MAPPING = {
        # Density properties
        "Mass density, kg/m3": "DENSITY",
        "Mass density, kg/m³": "DENSITY",
        "Density, kg/m3": "DENSITY",
        "Density, kg/m³": "DENSITY",
        # Viscosity properties
        "Dynamic viscosity, Pa*s": "VISCOSITY",
        "Dynamic viscosity, Pa·s": "VISCOSITY",
        "Kinematic viscosity, m2/s": "KINEMATIC_VISCOSITY",
        "Shear viscosity, Pa*s": "VISCOSITY",
        "Viscosity, Pas": "VISCOSITY",
        "Viscosity, Pa*s": "VISCOSITY",
        # Thermal properties
        "Thermal conductivity, W/(m*K)": "THERMAL_CONDUCTIVITY",
        "Thermal conductivity, W/(m·K)": "THERMAL_CONDUCTIVITY",
        "Heat capacity, J/(mol*K)": "SPECIFIC_HEAT_CAPACITY",
        "Heat capacity, J/(mol·K)": "SPECIFIC_HEAT_CAPACITY",
        # Enthalpy (additional units)
        "Molar enthalpy, kJ/mol": "MOLAR_ENTHALPY",
        # Pressure properties
        "Vapor pressure, kPa": "VAPOR_PRESSURE",
        "Vapor pressure, Pa": "VAPOR_PRESSURE",
        "Critical pressure, kPa": "CRITICAL_PRESSURE",
        "Critical pressure, Pa": "CRITICAL_PRESSURE",
        # Temperature properties
        "Critical temperature, K": "CRITICAL_TEMPERATURE",
        "Boiling point, K": "BOILING_POINT",
        "Melting point, K": "MELTING_POINT",
        # Volume properties
        "Molar volume, m3/mol": "MOLAR_VOLUME",
        "Molar volume, cm3/mol": "MOLAR_VOLUME",
        "Specific volume, m3/kg": "SPECIFIC_VOLUME",
        # Surface properties
        "Surface tension, N/m": "SURFACE_TENSION",
        "Surface tension, mN/m": "SURFACE_TENSION",
        # Refractive properties
        "Refractive index": "REFRACTIVE_INDEX",
        # Speed of sound
        "Speed of sound, m/s": "SPEED_OF_SOUND",
        # Compressibility
        "Isothermal compressibility, 1/Pa": "ISOTHERMAL_COMPRESSIBILITY",
        "Isothermal compressibility, 1/kPa": "ISOTHERMAL_COMPRESSIBILITY",
        # Expansion coefficient
        "Isobaric expansion coefficient, 1/K": "ISOBARIC_EXPANSION_COEFFICIENT",
        "Isobaric coefficient of expansion, 1/K": "ISOBARIC_EXPANSION_COEFFICIENT",
        # pH
        "pH": "PH",
        # Activity properties
        "Activity coefficient": "ACTIVITY_COEFFICIENT",
        "Activity": "ACTIVITY",
        # Fugacity
        "Fugacity coefficient": "FUGACITY_COEFFICIENT",
        # Henry's law
        "Henry's law constant, Pa": "HENRYS_LAW_CONSTANT",
        "Henry's law constant, kPa": "HENRYS_LAW_CONSTANT",
        "Henry's Law constant (amount concentration scale), kPadm3/mol": "HENRYS_LAW_CONSTANT",
        # Osmotic coefficient
        "Osmotic coefficient": "OSMOTIC_COEFFICIENT",
        # Ionic strength
        "Ionic strength, mol/kg": "IONIC_STRENGTH",
        # Excess properties
        "Excess molar volume, m3/mol": "EXCESS_MOLAR_VOLUME",
        "Excess molar enthalpy, J/mol": "EXCESS_MOLAR_ENTHALPY",
        "Excess molar enthalpy (molar enthalpy of mixing), kJ/mol": "EXCESS_MOLAR_ENTHALPY",
        "Excess molar entropy, J/(mol·K)": "EXCESS_MOLAR_ENTROPY",
        "Excess molar Gibbs free energy, J/mol": "EXCESS_MOLAR_GIBBS_FREE_ENERGY",
        # Gibbs free energy
        "Gibbs free energy, J/mol": "GIBBS_FREE_ENERGY",
        # Helmholtz free energy
        "Helmholtz free energy, J/mol": "HELMHOLTZ_FREE_ENERGY",
        # Molar properties
        "Molar enthalpy, J/mol": "MOLAR_ENTHALPY",
        "Molar entropy, J/(mol·K)": "MOLAR_ENTROPY",
        # Diffusion
        "Diffusion coefficient, m2/s": "DIFFUSION_COEFFICIENT",
        "Self diffusion coefficient, m2/s": "DIFFUSION_COEFFICIENT",
        # Critical properties
        "Critical density, kg/m3": "CRITICAL_DENSITY",
        "Critical volume, m3/mol": "CRITICAL_VOLUME",
        "Critical point pressure, kPa": "CRITICAL_POINT_PRESSURE",
        "Critical point temperature, K": "CRITICAL_POINT_TEMPERATURE",
        # Triple point
        "Triple point pressure, kPa": "TRIPLE_POINT_PRESSURE",
        "Triple point temperature, K": "TRIPLE_POINT_TEMPERATURE",
        # Compressibility
        "Compressibility": "COMPRESSIBILITY",
        # Polarity
        "Polarity": "POLARITY",
    }

    @classmethod
    def map_property(cls, thermoml_prop_name: str) -> Optional[str]:
        """
        Map ThermoML property name to FAIRFluids Properties enum value.

        Args:
            thermoml_prop_name: The property name from ThermoML

        Returns:
            The corresponding FAIRFluids Properties enum value or None if not found
        """
        return cls.PROPERTY_MAPPING.get(thermoml_prop_name)


class ThermoMLParameterMapper:
    """Maps ThermoML parameter names to FAIRFluids Parameters enum values."""

    PARAMETER_MAPPING = {
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
        # Composition parameters
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
        # Initial/Final values
        "Initial mole fraction of solute": "INITIAL_MOLE_FRACTION_OF_SOLUTE",
        "Final mole fraction of solute": "FINAL_MOLE_FRACTION_OF_SOLUTE",
        "Initial mass fraction of solute": "INITIAL_MASS_FRACTION_OF_SOLUTE",
        "Final mass fraction of solute": "FINAL_MASS_FRACTION_OF_SOLUTE",
        "Initial molality of solute, mol/kg": "INITIAL_MOLALITY_OF_SOLUTE",
        "Final molality of solute, mol/kg": "FINAL_MOLALITY_OF_SOLUTE",
        # Solvent parameters - normalize to base composition types
        "Solvent: Mole fraction": "SOLVENT_MOLE_FRACTION",
        "Solvent: Mass fraction": "SOLVENT_MASS_FRACTION",
        "Solvent: Volume fraction": "SOLVENT_VOLUME_FRACTION",
        "Solvent: Molality, mol/kg": "SOLVENT_MOLALITY",
        "Solvent: Amount concentration (molarity), mol/dm3": "SOLVENT_AMOUNT_CONCENTRATION_MOLARITY",
        # Solvent ratios
        "Solvent: Amount ratio of component to other component of binary solvent": "SOLVENT_AMOUNT_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT",
        "Solvent: Mass ratio of component to other component of binary solvent": "SOLVENT_MASS_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT",
        "Solvent: Volume ratio of component to other component of binary solvent": "SOLVENT_VOLUME_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT",
        # Other solvent parameters
        "Solvent: Ratio of amount of component to mass of solvent, mol/kg": "SOLVENT_RATIO_OF_AMOUNT_OF_COMPONENT_TO_MASS_OF_SOLVENT",
        "Solvent: Ratio of component mass to volume of solvent, kg/m3": "SOLVENT_RATIO_OF_COMPONENT_MASS_TO_VOLUME_OF_SOLVENT",
        # Concentration ratios
        "Ratio of amount of solute to mass of solution, mol/kg": "RATIO_OF_AMOUNT_OF_SOLUTE_TO_MASS_OF_SOLUTION",
        "Ratio of mass of solute to volume of solution, kg/m3": "RATIO_OF_MASS_OF_SOLUTE_TO_VOLUME_OF_SOLUTION",
        # Activity and activity coefficient
        "Activity coefficient": "ACTIVITY_COEFFICIENT",
        "(Relative) activity": "RELATIVE_ACTIVITY",
        # Volume and density
        "Molar volume, m3/mol": "MOLAR_VOLUME",
        "Specific volume, m3/kg": "SPECIFIC_VOLUME",
        # Entropy
        "Molar entropy, J/K/mol": "MOLAR_ENTROPY",
        # Frequency and wavelength
        "Frequency, MHz": "FREQUENCY",
        "Wavelength, nm": "WAVELENGTH",
    }

    @classmethod
    def map_parameter(cls, thermoml_param_name: str) -> Optional[str]:
        """
        Map ThermoML parameter name to FAIRFluids Parameters enum value.

        Args:
            thermoml_param_name: The parameter name from ThermoML

        Returns:
            The corresponding FAIRFluids Parameters enum value or None if not found
        """
        return cls.PARAMETER_MAPPING.get(thermoml_param_name)


class ThermoMLMethodMapper:
    """Maps ThermoML method types to FAIRFluids Method enum values."""

    METHOD_MAPPING = {
        "measured": "MEASURED",
        "Measured": "MEASURED",
        "calculated": "CALCULATED",
        "Calculated": "CALCULATED",
        "simulated": "SIMULATED",
        "Simulated": "SIMULATED",
        "literature": "LITERATURE",
        "Literature": "LITERATURE",
        "Molecular dynamics": "SIMULATED",
        "Monte Carlo": "SIMULATED",
        "DFT": "CALCULATED",
        "Quantum chemistry": "CALCULATED",
    }

    @classmethod
    def map_method(cls, thermoml_method: str) -> Optional[str]:
        """
        Map ThermoML method to FAIRFluids Method enum value.

        Args:
            thermoml_method: The method from ThermoML

        Returns:
            The corresponding FAIRFluids Method enum value or None if not found
        """
        # Try exact match first
        if thermoml_method in cls.METHOD_MAPPING:
            return cls.METHOD_MAPPING[thermoml_method]

        # Try case-insensitive match
        for key, value in cls.METHOD_MAPPING.items():
            if key.lower() == thermoml_method.lower():
                return value

        # Try partial match
        thermoml_lower = thermoml_method.lower()
        for key, value in cls.METHOD_MAPPING.items():
            if key.lower() in thermoml_lower or thermoml_lower in key.lower():
                return value

        return None


class ThermoMLLitTypeMapper:
    """Maps ThermoML literature types to FAIRFluids LitType enum values."""

    LIT_TYPE_MAPPING = {
        "journal": "JOURNAL",
        "Journal": "JOURNAL",
        "book": "BOOK",
        "Book": "BOOK",
        "report": "REPORT",
        "Report": "REPORT",
        "patent": "PATENT",
        "Patent": "PATENT",
        "thesis": "THESIS",
        "Thesis": "THESIS",
        "conference proceedings": "CONFERENCEPROCEEDINGS",
        "Conference proceedings": "CONFERENCEPROCEEDINGS",
        "archived document": "ARCHIVEDDOCUMENT",
        "Archived document": "ARCHIVEDDOCUMENT",
        "personal correspondence": "PERSONALCORRESPONDENCE",
        "Personal correspondence": "PERSONALCORRESPONDENCE",
        "published translation": "PUBLISHEDTRANSLATION",
        "Published translation": "PUBLISHEDTRANSLATION",
        "unspecified": "UNSPECIFIED",
        "Unspecified": "UNSPECIFIED",
    }

    @classmethod
    def map_lit_type(cls, thermoml_lit_type: str) -> Optional[str]:
        """
        Map ThermoML literature type to FAIRFluids LitType enum value.

        Args:
            thermoml_lit_type: The literature type from ThermoML

        Returns:
            The corresponding FAIRFluids LitType enum value or None if not found
        """
        return cls.LIT_TYPE_MAPPING.get(thermoml_lit_type)


def extract_text_content(element: ET.Element) -> Optional[str]:
    """Extract text content from XML element, handling None cases."""
    if element is not None and element.text:
        return element.text.strip()
    return None


def extract_numeric_value(element: ET.Element) -> Optional[float]:
    """Extract numeric value from XML element."""
    text = extract_text_content(element)
    if text:
        try:
            return float(text)
        except ValueError:
            return None
    return None


def extract_integer_value(element: ET.Element) -> Optional[int]:
    """Extract integer value from XML element."""
    text = extract_text_content(element)
    if text:
        try:
            return int(text)
        except ValueError:
            return None
    return None


def clean_doi(doi: str) -> str:
    """Clean and standardize DOI format."""
    if not doi:
        return ""

    # Remove any whitespace
    doi = doi.strip()

    # Ensure it starts with 10. if it doesn't already
    if not doi.startswith("10."):
        # Try to extract DOI from URL format
        if "doi.org/" in doi:
            doi = doi.split("doi.org/")[-1]
        elif "dx.doi.org/" in doi:
            doi = doi.split("dx.doi.org/")[-1]

    return doi


def parse_authors(author_text: str) -> List[Dict[str, str]]:
    """
    Parse author text from ThermoML format to list of author dictionaries.

    ThermoML typically has authors in format: "Last, First; Last2, First2"
    """
    if not author_text:
        return []

    authors = []
    # Split by semicolon first
    author_entries = author_text.split(";")

    for entry in author_entries:
        entry = entry.strip()
        if not entry:
            continue

        # Split by comma to separate last name and first name
        parts = entry.split(",", 1)
        if len(parts) == 2:
            family_name = parts[0].strip()
            given_name = parts[1].strip()
        else:
            # If no comma, treat as family name only
            family_name = entry
            given_name = ""

        authors.append(
            {
                "family_name": family_name,
                "given_name": given_name,
                "email": None,
                "orcid": None,
                "affiliation": None,
            }
        )

    return authors


def create_unit_definition(
    unit_name: str, unit_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a unit definition from unit name.

    This is a simplified version - in a full implementation, you might want to
    parse the unit name and create proper base units.
    """
    return {
        "unitID": unit_id
        or f"unit_{unit_name.replace(' ', '_').replace(',', '').replace('(', '').replace(')', '')}",
        "name": unit_name,
        "base_units": [],  # Could be expanded to parse unit components
    }
