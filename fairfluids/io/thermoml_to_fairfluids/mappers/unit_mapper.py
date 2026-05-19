"""
Unit Mapper.

Builds FAIRFluids ``UnitDefinition`` objects from ThermoML unit strings.
Contains a self-contained lookup table of SI-decomposed unit definitions.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from fairfluids.core.lib import BaseUnit, UnitDefinition

# ---------------------------------------------------------------------------
# Unit lookup table — maps canonical unit strings to name + base_units
# ---------------------------------------------------------------------------

UNIT_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    # Temperature
    "K": {
        "name": "kelvin",
        "base_units": [{"kind": "temperature", "exponent": 1}],
    },
    # Pressure
    "Pa": {
        "name": "pascal",
        "base_units": [
            {"kind": "mass", "exponent": 1},
            {"kind": "length", "exponent": -1},
            {"kind": "time", "exponent": -2},
        ],
    },
    "kPa": {
        "name": "kilopascal",
        "base_units": [
            {"kind": "mass", "exponent": 1, "scale": 3.0},
            {"kind": "length", "exponent": -1},
            {"kind": "time", "exponent": -2},
        ],
    },
    "MPa": {
        "name": "megapascal",
        "base_units": [
            {"kind": "mass", "exponent": 1, "scale": 6.0},
            {"kind": "length", "exponent": -1},
            {"kind": "time", "exponent": -2},
        ],
    },
    # Viscosity
    "Pa*s": {
        "name": "pascal second",
        "base_units": [
            {"kind": "mass", "exponent": 1},
            {"kind": "length", "exponent": -1},
            {"kind": "time", "exponent": -1},
        ],
    },
    "Pa·s": {
        "name": "pascal second",
        "base_units": [
            {"kind": "mass", "exponent": 1},
            {"kind": "length", "exponent": -1},
            {"kind": "time", "exponent": -1},
        ],
    },
    "mPa*s": {
        "name": "millipascal second",
        "base_units": [
            {"kind": "mass", "exponent": 1, "scale": -3.0},
            {"kind": "length", "exponent": -1},
            {"kind": "time", "exponent": -1},
        ],
    },
    # Kinematic viscosity
    "m2/s": {
        "name": "square meter per second",
        "base_units": [
            {"kind": "length", "exponent": 2},
            {"kind": "time", "exponent": -1},
        ],
    },
    "m²/s": {
        "name": "square meter per second",
        "base_units": [
            {"kind": "length", "exponent": 2},
            {"kind": "time", "exponent": -1},
        ],
    },
    # Density
    "kg/m3": {
        "name": "kilogram per cubic meter",
        "base_units": [
            {"kind": "mass", "exponent": 1},
            {"kind": "length", "exponent": -3},
        ],
    },
    "kg/m³": {
        "name": "kilogram per cubic meter",
        "base_units": [
            {"kind": "mass", "exponent": 1},
            {"kind": "length", "exponent": -3},
        ],
    },
    "g/cm3": {
        "name": "gram per cubic centimeter",
        "base_units": [
            {"kind": "mass", "exponent": 1, "scale": -3.0},
            {"kind": "length", "exponent": -3, "scale": 2.0},
        ],
    },
    # Dimensionless
    "1": {
        "name": "dimensionless",
        "base_units": [],
    },
    "dimensionless": {
        "name": "dimensionless",
        "base_units": [],
    },
    # Concentration
    "mol/kg": {
        "name": "mole per kilogram",
        "base_units": [
            {"kind": "amount", "exponent": 1},
            {"kind": "mass", "exponent": -1},
        ],
    },
    "mol/dm3": {
        "name": "mole per cubic decimeter",
        "base_units": [
            {"kind": "amount", "exponent": 1},
            {"kind": "length", "exponent": -3, "scale": 3.0},
        ],
    },
    "mol/m3": {
        "name": "mole per cubic meter",
        "base_units": [
            {"kind": "amount", "exponent": 1},
            {"kind": "length", "exponent": -3},
        ],
    },
    # Molar / specific volume
    "m3/mol": {
        "name": "cubic meter per mole",
        "base_units": [
            {"kind": "length", "exponent": 3},
            {"kind": "amount", "exponent": -1},
        ],
    },
    "cm3/mol": {
        "name": "cubic centimeter per mole",
        "base_units": [
            {"kind": "length", "exponent": 3, "scale": -6.0},
            {"kind": "amount", "exponent": -1},
        ],
    },
    "m3/kg": {
        "name": "cubic meter per kilogram",
        "base_units": [
            {"kind": "length", "exponent": 3},
            {"kind": "mass", "exponent": -1},
        ],
    },
    # Energy
    "J/mol": {
        "name": "joule per mole",
        "base_units": [
            {"kind": "mass", "exponent": 1},
            {"kind": "length", "exponent": 2},
            {"kind": "time", "exponent": -2},
            {"kind": "amount", "exponent": -1},
        ],
    },
    "kJ/mol": {
        "name": "kilojoule per mole",
        "base_units": [
            {"kind": "mass", "exponent": 1, "scale": 3.0},
            {"kind": "length", "exponent": 2},
            {"kind": "time", "exponent": -2},
            {"kind": "amount", "exponent": -1},
        ],
    },
    # Heat capacity
    "J/(mol*K)": {
        "name": "joule per mole per kelvin",
        "base_units": [
            {"kind": "mass", "exponent": 1},
            {"kind": "length", "exponent": 2},
            {"kind": "time", "exponent": -2},
            {"kind": "amount", "exponent": -1},
            {"kind": "temperature", "exponent": -1},
        ],
    },
    "J/(mol·K)": {
        "name": "joule per mole per kelvin",
        "base_units": [
            {"kind": "mass", "exponent": 1},
            {"kind": "length", "exponent": 2},
            {"kind": "time", "exponent": -2},
            {"kind": "amount", "exponent": -1},
            {"kind": "temperature", "exponent": -1},
        ],
    },
    "J/K/mol": {
        "name": "joule per kelvin per mole",
        "base_units": [
            {"kind": "mass", "exponent": 1},
            {"kind": "length", "exponent": 2},
            {"kind": "time", "exponent": -2},
            {"kind": "temperature", "exponent": -1},
            {"kind": "amount", "exponent": -1},
        ],
    },
    "J/K/kg": {
        "name": "joule per kelvin per kilogram",
        "base_units": [
            {"kind": "length", "exponent": 2},
            {"kind": "time", "exponent": -2},
            {"kind": "temperature", "exponent": -1},
        ],
    },
    # Thermal conductivity
    "W/(m*K)": {
        "name": "watt per meter per kelvin",
        "base_units": [
            {"kind": "mass", "exponent": 1},
            {"kind": "length", "exponent": 1},
            {"kind": "time", "exponent": -3},
            {"kind": "temperature", "exponent": -1},
        ],
    },
    "W/(m·K)": {
        "name": "watt per meter per kelvin",
        "base_units": [
            {"kind": "mass", "exponent": 1},
            {"kind": "length", "exponent": 1},
            {"kind": "time", "exponent": -3},
            {"kind": "temperature", "exponent": -1},
        ],
    },
    # Surface tension
    "N/m": {
        "name": "newton per meter",
        "base_units": [
            {"kind": "mass", "exponent": 1},
            {"kind": "time", "exponent": -2},
        ],
    },
    "mN/m": {
        "name": "millinewton per meter",
        "base_units": [
            {"kind": "mass", "exponent": 1, "scale": -3.0},
            {"kind": "time", "exponent": -2},
        ],
    },
    # Speed of sound
    "m/s": {
        "name": "meter per second",
        "base_units": [
            {"kind": "length", "exponent": 1},
            {"kind": "time", "exponent": -1},
        ],
    },
    # Compressibility
    "1/Pa": {
        "name": "inverse pascal",
        "base_units": [
            {"kind": "mass", "exponent": -1},
            {"kind": "length", "exponent": 1},
            {"kind": "time", "exponent": 2},
        ],
    },
    "1/kPa": {
        "name": "inverse kilopascal",
        "base_units": [
            {"kind": "mass", "exponent": -1, "scale": -3.0},
            {"kind": "length", "exponent": 1},
            {"kind": "time", "exponent": 2},
        ],
    },
    # Thermal expansion
    "1/K": {
        "name": "inverse kelvin",
        "base_units": [{"kind": "temperature", "exponent": -1}],
    },
    # Henry's law constant
    "Pa*m3/mol": {
        "name": "pascal cubic meter per mole",
        "base_units": [
            {"kind": "mass", "exponent": 1},
            {"kind": "length", "exponent": 2},
            {"kind": "time", "exponent": -2},
            {"kind": "amount", "exponent": -1},
        ],
    },
    "kPa*m3/mol": {
        "name": "kilopascal cubic meter per mole",
        "base_units": [
            {"kind": "mass", "exponent": 1, "scale": 3.0},
            {"kind": "length", "exponent": 2},
            {"kind": "time", "exponent": -2},
            {"kind": "amount", "exponent": -1},
        ],
    },
    "kPadm3/mol": {
        "name": "kilopascal cubic decimeter per mole",
        "base_units": [
            {"kind": "mass", "exponent": 1, "scale": 3.0},
            {"kind": "length", "exponent": 2, "scale": -3.0},
            {"kind": "time", "exponent": -2},
            {"kind": "amount", "exponent": -1},
        ],
    },
    # Spectroscopy
    "nm": {
        "name": "nanometer",
        "base_units": [{"kind": "length", "exponent": 1, "scale": -9.0}],
    },
    "MHz": {
        "name": "megahertz",
        "base_units": [{"kind": "time", "exponent": -1, "scale": 6.0}],
    },
    # Amount / mass
    "mol": {
        "name": "mole",
        "base_units": [{"kind": "amount", "exponent": 1}],
    },
    "kg": {
        "name": "kilogram",
        "base_units": [{"kind": "mass", "exponent": 1}],
    },
}

_UNIT_ALIASES: Dict[str, str] = {
    "Pa s": "Pa*s",
    "Pa.s": "Pa*s",
    "m^2/s": "m2/s",
    "m^3/mol": "m3/mol",
    "m^3/kg": "m3/kg",
    "kg m^-3": "kg/m3",
    "kg/m^3": "kg/m3",
    "J mol^-1": "J/mol",
    "J mol-1": "J/mol",
    "kJ mol^-1": "kJ/mol",
    "kJ mol-1": "kJ/mol",
    "W m^-1 K^-1": "W/(m*K)",
    "W m-1 K-1": "W/(m*K)",
    "mPa.s": "mPa*s",
    "g cm^-3": "g/cm3",
    "g/cm^3": "g/cm3",
    "cm^3/mol": "cm3/mol",
    "cm^3 mol^-1": "cm3/mol",
}


def _resolve_unit_str(unit_str: str) -> Optional[str]:
    """Return canonical key for a unit string, or ``None``."""
    if unit_str in UNIT_DEFINITIONS:
        return unit_str
    alias = _UNIT_ALIASES.get(unit_str)
    if alias and alias in UNIT_DEFINITIONS:
        return alias
    stripped = unit_str.replace(" ", "")
    if stripped in UNIT_DEFINITIONS:
        return stripped
    return None


def _extract_unit_from_name(prop_name: str) -> Optional[str]:
    """Extract the unit substring from ``'Quantity, unit'`` patterns."""
    if "," in prop_name:
        return prop_name.split(",", 1)[-1].strip()
    return None


def _build_unit_definition(
    unit_str: str, unit_id: Optional[str] = None
) -> UnitDefinition:
    """Build a ``UnitDefinition`` from a bare or full ThermoML name."""
    bare = _extract_unit_from_name(unit_str)
    if bare is None:
        bare = unit_str

    canonical = _resolve_unit_str(bare)
    if canonical:
        spec = UNIT_DEFINITIONS[canonical]
        base_units = [BaseUnit(**bu) for bu in spec["base_units"]]
        safe_id = unit_id or f"unit_{canonical.replace('/', '_').replace('*', '_').replace(' ', '_')}"
        return UnitDefinition(unitID=safe_id, name=spec["name"], base_units=base_units)

    safe_id = unit_id or f"unit_{re.sub(r'[^a-zA-Z0-9_]', '_', bare)}"
    return UnitDefinition(unitID=safe_id, name=bare, base_units=[])


class UnitMapper:
    """Build ``UnitDefinition`` instances from raw ThermoML strings."""

    @staticmethod
    def from_thermoml_name(
        thermoml_name: str, unit_id: Optional[str] = None
    ) -> UnitDefinition:
        return _build_unit_definition(thermoml_name, unit_id)

    @staticmethod
    def dimensionless() -> UnitDefinition:
        return UnitDefinition(
            unitID="unit_dimensionless",
            name="dimensionless",
            base_units=[],
        )

    @staticmethod
    def from_unit_string(
        unit_str: str, unit_id: Optional[str] = None
    ) -> UnitDefinition:
        return _build_unit_definition(unit_str, unit_id)
