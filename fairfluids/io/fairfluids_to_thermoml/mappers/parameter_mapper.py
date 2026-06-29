"""Reverse parameter mapping: FAIRFluids -> ThermoML variable/constraint names."""

from __future__ import annotations

from typing import Dict

from fairfluids.core.lib import Parameters
from fairfluids.io.canonical.mappers.parameter_mapper import PARAMETER_MAP

_REVERSE: Dict[str, str] = {}
for thermo_name, ff_name in PARAMETER_MAP.items():
    _REVERSE.setdefault(ff_name, thermo_name)

_DEFAULT_BY_ENUM: Dict[str, str] = {
    "TEMPERATURE": "Temperature, K",
    "PRESSURE": "Pressure, kPa",
    "MOLE_FRACTION": "Mole fraction",
    "MASS_FRACTION": "Mass fraction",
    "VOLUME_FRACTION": "Volume fraction",
}


class ParameterMapper:
    """Resolve FAIRFluids parameter values to ThermoML type names."""

    @staticmethod
    def to_thermoml_name(value: str) -> str:
        enum_name = _as_enum_name(value, Parameters)
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
