"""Reverse property mapping: FAIRFluids -> ThermoML ePropName."""

from __future__ import annotations

from typing import Dict

from fairfluids.core.lib import Properties
from fairfluids.io.thermoml_to_fairfluids.mappers.property_mapper import PROPERTY_MAP

_REVERSE: Dict[str, str] = {}
for thermo_name, ff_name in PROPERTY_MAP.items():
    _REVERSE.setdefault(ff_name, thermo_name)

_DEFAULT_BY_ENUM: Dict[str, str] = {
    "DENSITY": "Mass density, kg/m3",
    "VISCOSITY": "Dynamic viscosity, Pa*s",
    "KINEMATIC_VISCOSITY": "Kinematic viscosity, m2/s",
    "THERMAL_CONDUCTIVITY": "Thermal conductivity, W/(m*K)",
    "ELECTRICAL_CONDUCTIVITY": "Electrical conductivity, S/m",
    "SPECIFIC_HEAT_CAPACITY": "Heat capacity, J/(mol*K)",
    "MOLAR_HEAT_CAPACITY": "Molar heat capacity, J/(mol*K)",
    "MOLAR_VOLUME": "Molar volume, m3/mol",
    "MOLAR_ENTHALPY": "Molar enthalpy, J/mol",
    "MOLAR_ENTROPY": "Molar entropy, J/K/mol",
    "VAPOR_PRESSURE": "Vapor pressure, kPa",
}


class PropertyMapper:
    """Resolve FAIRFluids property values to ThermoML property names."""

    @staticmethod
    def to_thermoml_name(value: str) -> str:
        enum_name = _as_enum_name(value, Properties)
        if enum_name in _REVERSE:
            return _REVERSE[enum_name]
        if enum_name in _DEFAULT_BY_ENUM:
            return _DEFAULT_BY_ENUM[enum_name]
        return value


def _as_enum_name(raw: str, enum_cls) -> str:
    for member in enum_cls:
        if raw == member.name or raw == member.value:
            return member.name
    return raw
