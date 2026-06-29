"""Local filtering of ThermoML API search hits."""

from __future__ import annotations

from enum import Enum
from typing import Any, Iterable

from pydantic import BaseModel, Field

from .client import compounds_of, poms_of
from .components import ResolvedComponent


class MixtureType(str, Enum):
    PURE = "pure"
    BINARY = "binary"
    TERNARY = "ternary"
    CUSTOM = "custom"


class MixtureMode(str, Enum):
    STRICT = "strict"
    LENIENT = "lenient"


class FilterConfig(BaseModel):
    components: list[ResolvedComponent]
    mixture_type: MixtureType = MixtureType.BINARY
    custom_component_count: int = Field(default=2, ge=1, le=10)
    mode: MixtureMode = MixtureMode.LENIENT
    property_names: list[str] = Field(default_factory=list)
    require_properties: bool = False
    target_pressure_kpa: float | None = None
    pressure_tolerance_kpa: float = 2.0
    target_temperature_k: float | None = None
    temperature_tolerance_k: float = 1.0

    def target_component_count(self) -> int:
        mapping = {
            MixtureType.PURE: 1,
            MixtureType.BINARY: 2,
            MixtureType.TERNARY: 3,
        }
        if self.mixture_type == MixtureType.CUSTOM:
            return self.custom_component_count
        return mapping[self.mixture_type]

    def resolved_inchikeys(self) -> set[str]:
        return {c.inchikey for c in self.components if c.inchikey}


def _compound_inchikeys(obj: dict[str, Any]) -> set[str]:
    return {
        key
        for c in compounds_of(obj)
        if (key := c.get("sStandardInChIKey"))
    }


def orgnums_for_keys(obj: dict[str, Any], target_keys: set[str]) -> set[int]:
    out: set[int] = set()
    for compound in compounds_of(obj):
        if compound.get("sStandardInChIKey") in target_keys:
            orgnum = compound.get("RegNum", {}).get("nOrgNum")
            if orgnum is not None:
                out.add(orgnum)
    return out


def _ename(prop: dict[str, Any]) -> str:
    pg = prop.get("Property-MethodID", {}).get("PropertyGroup", {}) or {}
    for group_body in pg.values():
        if isinstance(group_body, dict):
            name = group_body.get("ePropName")
            if name:
                return str(name)
    return ""


def pom_measures_property(pom: dict[str, Any], property_names: Iterable[str]) -> bool:
    needles = [p.lower() for p in property_names]
    if not needles:
        return True
    for prop in pom.get("Property", []):
        ename = _ename(prop).lower()
        if any(needle in ename for needle in needles):
            return True
    return False


def _pom_component_orgnums(pom: dict[str, Any]) -> set[int]:
    return {
        orgnum
        for c in pom.get("Component", [])
        if (orgnum := c.get("RegNum", {}).get("nOrgNum")) is not None
    }


def _pom_component_inchikeys(pom: dict[str, Any]) -> set[str]:
    return {
        key
        for c in pom.get("Component", [])
        if (key := c.get("sStandardInChIKey"))
    }


def pom_has_component_set(
    pom: dict[str, Any],
    *,
    target_count: int,
    target_orgnums: set[int],
    target_inchikeys: set[str],
) -> bool:
    """True when the POM block has exactly target_count components from the target set."""
    comps = pom.get("Component", [])
    if len(comps) != target_count:
        return False

    comp_orgnums = _pom_component_orgnums(pom)
    comp_inchikeys = _pom_component_inchikeys(pom)

    if target_orgnums and len(comp_orgnums) == target_count:
        return comp_orgnums.issubset(target_orgnums)

    if target_inchikeys and len(comp_inchikeys) == target_count:
        return comp_inchikeys.issubset(target_inchikeys)

    return False


def entry_contains_all_components(
    obj: dict[str, Any],
    target_inchikeys: set[str],
) -> bool:
    if not target_inchikeys:
        return True
    return target_inchikeys.issubset(_compound_inchikeys(obj))


def entry_is_only_target_components(
    obj: dict[str, Any],
    target_inchikeys: set[str],
) -> bool:
    if not target_inchikeys:
        return False
    keys = _compound_inchikeys(obj)
    return entry_contains_all_components(obj, target_inchikeys) and keys.issubset(
        target_inchikeys
    )


def has_matching_pom_block(
    obj: dict[str, Any],
    *,
    target_count: int,
    target_orgnums: set[int],
    target_inchikeys: set[str],
    property_names: Iterable[str],
    require_properties: bool,
) -> bool:
    for pom in poms_of(obj):
        if not pom_has_component_set(
            pom,
            target_count=target_count,
            target_orgnums=target_orgnums,
            target_inchikeys=target_inchikeys,
        ):
            continue
        if require_properties and not pom_measures_property(pom, property_names):
            continue
        return True
    return False


def pressure_values_kpa(obj: dict[str, Any]) -> list[float]:
    values: list[float] = []
    for pom in poms_of(obj):
        for constraint in pom.get("Constraint", []):
            ctype = constraint.get("ConstraintID", {}).get("ConstraintType", {})
            if "ePressure" in ctype:
                val = constraint.get("nConstraintValue")
                if val is not None:
                    values.append(float(val))
    return values


def temperature_values_k(obj: dict[str, Any]) -> list[float]:
    values: list[float] = []

    def _collect_temperature(container: dict[str, Any], value_key: str) -> None:
        var_type = container.get("VariableID", {}) or container.get("ConstraintID", {})
        vtype = var_type.get("VariableType", {}) or var_type.get("ConstraintType", {})
        if "eTemperature" in vtype:
            val = container.get(value_key)
            if val is not None:
                values.append(float(val))

    for pom in poms_of(obj):
        for variable in pom.get("Variable", []):
            _collect_temperature(variable, "nVarValue")
        for constraint in pom.get("Constraint", []):
            _collect_temperature(constraint, "nConstraintValue")

    return values


def _near(target: float, tolerance: float, values: Iterable[float]) -> bool:
    return any(abs(value - target) <= tolerance for value in values)


def matches_filter(obj: dict[str, Any], config: FilterConfig) -> bool:
    target_keys = config.resolved_inchikeys()
    target_count = config.target_component_count()
    target_orgnums = orgnums_for_keys(obj, target_keys) if target_keys else set()

    if config.mode == MixtureMode.STRICT:
        if target_keys:
            if not entry_is_only_target_components(obj, target_keys):
                return False
        elif len(compounds_of(obj)) != target_count:
            return False
        mixture_ok = True
    else:
        if target_keys or target_orgnums:
            mixture_ok = has_matching_pom_block(
                obj,
                target_count=target_count,
                target_orgnums=target_orgnums,
                target_inchikeys=target_keys,
                property_names=config.property_names,
                require_properties=config.require_properties,
            )
        else:
            mixture_ok = any(
                len(pom.get("Component", [])) == target_count for pom in poms_of(obj)
            )

    if not mixture_ok:
        return False

    if config.mode == MixtureMode.STRICT and config.require_properties:
        if not any(
            pom_measures_property(pom, config.property_names) for pom in poms_of(obj)
        ):
            return False

    if config.target_pressure_kpa is not None:
        if not _near(
            config.target_pressure_kpa,
            config.pressure_tolerance_kpa,
            pressure_values_kpa(obj),
        ):
            return False

    if config.target_temperature_k is not None:
        if not _near(
            config.target_temperature_k,
            config.temperature_tolerance_k,
            temperature_values_k(obj),
        ):
            return False

    return True


def apply_filters(
    hits: list[dict[str, Any]],
    config: FilterConfig,
) -> list[dict[str, Any]]:
    return [hit for hit in hits if matches_filter(hit, config)]
