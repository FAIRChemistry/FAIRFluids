"""Reverse unit mapper: FAIRFluids units -> ThermoML suffix units."""

from __future__ import annotations

from typing import Dict, Optional

_UNIT_NAME_TO_THERMOML: Dict[str, str] = {
    "kelvin": "K",
    "pascal": "Pa",
    "kilopascal": "kPa",
    "megapascal": "MPa",
    "pascal second": "Pa*s",
    "millipascal second": "mPa*s",
    "square meter per second": "m2/s",
    "kilogram per cubic meter": "kg/m3",
    "gram per cubic centimeter": "g/cm3",
    "dimensionless": "1",
    "mole per kilogram": "mol/kg",
    "mole per cubic decimeter": "mol/dm3",
    "mole per cubic meter": "mol/m3",
    "cubic meter per mole": "m3/mol",
    "cubic centimeter per mole": "cm3/mol",
    "cubic meter per kilogram": "m3/kg",
    "joule per mole": "J/mol",
    "kilojoule per mole": "kJ/mol",
    "joule per mole per kelvin": "J/(mol*K)",
    "joule per kelvin per mole": "J/K/mol",
    "joule per kelvin per kilogram": "J/K/kg",
    "watt per meter per kelvin": "W/(m*K)",
    "newton per meter": "N/m",
    "millinewton per meter": "mN/m",
    "meter per second": "m/s",
    "inverse pascal": "1/Pa",
    "inverse kilopascal": "1/kPa",
    "inverse kelvin": "1/K",
    "nanometer": "nm",
    "megahertz": "MHz",
    "mole": "mol",
    "kilogram": "kg",
}


class UnitMapper:
    """Return ThermoML unit strings from FAIRFluids unit definitions."""

    @staticmethod
    def to_thermoml_unit(unit: Optional[dict]) -> Optional[str]:
        if not unit:
            return None
        name = unit.get("name")
        if not name:
            return None
        return _UNIT_NAME_TO_THERMOML.get(str(name).strip().lower())
