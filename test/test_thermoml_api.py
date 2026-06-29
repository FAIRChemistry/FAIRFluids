"""Offline tests for fairfluids.io.thermoml_api."""

from __future__ import annotations

from pathlib import Path

import pytest

from fairfluids.io.thermoml_api.client import build_lucene_query, doi_of
from fairfluids.io.thermoml_api.components import ResolvedComponent
from fairfluids.io.thermoml_api.enum_loader import get_property_options, load_enums
from fairfluids.io.thermoml_api.filters import (
    FilterConfig,
    MixtureMode,
    MixtureType,
    apply_filters,
    matches_filter,
    pressure_values_kpa,
    temperature_values_k,
)
from fairfluids.io.thermoml_api.download import bundle_zip

WATER_KEY = "XLYOFNOQVPJJNP-UHFFFAOYSA-N"
METHANOL_KEY = "OKKJLVBELUTLKV-UHFFFAOYSA-N"


def _compound(inchikey: str, orgnum: int, name: str) -> dict:
    return {
        "sStandardInChIKey": inchikey,
        "sCommonName": name,
        "RegNum": {"nOrgNum": orgnum},
    }


def _pom_property(ename: str) -> dict:
    return {
        "Property": [
            {
                "Property-MethodID": {
                    "PropertyGroup": {
                        "VolumetricProp": {"ePropName": ename},
                    }
                }
            }
        ]
    }


def _binary_water_methanol_hit(*, density: bool = True, pressure_kpa: float | None = None) -> dict:
    pom: dict = {
        "Component": [
            _compound(WATER_KEY, 1, "water"),
            _compound(METHANOL_KEY, 2, "methanol"),
        ],
    }
    if density:
        pom.update(_pom_property("Mass density, kg/m3"))
    if pressure_kpa is not None:
        pom["Constraint"] = [
            {
                "ConstraintID": {
                    "ConstraintType": {"ePressure": "Pressure, kPa"},
                },
                "nConstraintValue": pressure_kpa,
            }
        ]
    return {
        "id": "20.5000.trc.thermoml/10.1021/je000001",
        "Compound": [
            _compound(WATER_KEY, 1, "water"),
            _compound(METHANOL_KEY, 2, "methanol"),
        ],
        "PureOrMixtureData": [pom],
    }


def _water_only_hit() -> dict:
    return {
        "id": "20.5000.trc.thermoml/10.1021/je000002",
        "Compound": [_compound(WATER_KEY, 1, "water")],
        "PureOrMixtureData": [
            {
                "Component": [_compound(WATER_KEY, 1, "water")],
                **_pom_property("Viscosity, Pa*s"),
            }
        ],
    }


def _temperature_hit(temp_k: float) -> dict:
    return {
        "id": "20.5000.trc.thermoml/10.1021/je000003",
        "Compound": [_compound(WATER_KEY, 1, "water")],
        "PureOrMixtureData": [
            {
                "Component": [_compound(WATER_KEY, 1, "water")],
                "Variable": [
                    {
                        "VariableID": {
                            "VariableType": {"eTemperature": "Temperature, K"},
                        },
                        "nVarValue": temp_k,
                    }
                ],
            }
        ],
    }


@pytest.mark.parametrize(
    ("components", "expected"),
    [
        (["water"], "type:TRCTml4 AND /Compound/_/sCommonName/_:water"),
        (
            ["water", "methanol"],
            "type:TRCTml4 AND /Compound/_/sCommonName/_:water "
            "AND /Compound/_/sCommonName/_:methanol",
        ),
        (
            ["water", "choline chloride"],
            'type:TRCTml4 AND /Compound/_/sCommonName/_:water '
            'AND /Compound/_/sCommonName/_:"choline chloride"',
        ),
    ],
)
def test_build_lucene_query(components: list[str], expected: str) -> None:
    assert build_lucene_query(components) == expected


def test_build_lucene_query_requires_components() -> None:
    with pytest.raises(ValueError, match="At least one"):
        build_lucene_query([])


def test_doi_of_strips_trc_handle() -> None:
    assert doi_of({"id": "20.5000.trc.thermoml/10.1021/je000001"}) == "10.1021/je000001"


def test_load_enums_includes_parameter_enums() -> None:
    enums = load_enums()
    assert "eMiscellaneous" in enums
    assert "eTemperature" in enums
    assert "ePressure" in enums
    assert "Mass density, kg/m3" in enums["eMiscellaneous"]


def test_get_property_options_includes_mapper_keys() -> None:
    options = get_property_options()
    assert "Mass density, kg/m3" in options
    assert "Viscosity, Pa*s" in options


def test_lenient_binary_filter_with_density() -> None:
    config = FilterConfig(
        components=[
            ResolvedComponent("water", WATER_KEY),
            ResolvedComponent("methanol", METHANOL_KEY),
        ],
        mixture_type=MixtureType.BINARY,
        mode=MixtureMode.LENIENT,
        property_names=["Mass density, kg/m3"],
        require_properties=True,
    )
    hit = _binary_water_methanol_hit(density=True)
    assert matches_filter(hit, config)
    assert len(apply_filters([hit, _water_only_hit()], config)) == 1


def test_pressure_filter() -> None:
    config = FilterConfig(
        components=[
            ResolvedComponent("water", WATER_KEY),
            ResolvedComponent("methanol", METHANOL_KEY),
        ],
        mixture_type=MixtureType.BINARY,
        target_pressure_kpa=101.0,
        pressure_tolerance_kpa=2.0,
    )
    matching = _binary_water_methanol_hit(pressure_kpa=101.5)
    non_matching = _binary_water_methanol_hit(pressure_kpa=200.0)
    assert matches_filter(matching, config)
    assert not matches_filter(non_matching, config)
    assert pressure_values_kpa(matching) == [101.5]


def test_temperature_filter() -> None:
    config = FilterConfig(
        components=[ResolvedComponent("water", WATER_KEY)],
        mixture_type=MixtureType.PURE,
        target_temperature_k=298.15,
        temperature_tolerance_k=1.0,
    )
    hit = _temperature_hit(298.0)
    miss = _temperature_hit(310.0)
    assert matches_filter(hit, config)
    assert not matches_filter(miss, config)
    assert temperature_values_k(hit) == [298.0]


def test_strict_pure_water_filter() -> None:
    config = FilterConfig(
        components=[ResolvedComponent("water", WATER_KEY)],
        mixture_type=MixtureType.PURE,
        mode=MixtureMode.STRICT,
    )
    assert matches_filter(_water_only_hit(), config)
    assert not matches_filter(_binary_water_methanol_hit(), config)


def test_bundle_zip(tmp_path: Path) -> None:
    xml_a = tmp_path / "a.xml"
    xml_b = tmp_path / "b.xml"
    xml_a.write_text("<a/>", encoding="utf-8")
    xml_b.write_text("<b/>", encoding="utf-8")
    zip_path = bundle_zip([xml_a, xml_b], tmp_path / "bundle.zip")
    assert zip_path.is_file()
    assert zip_path.stat().st_size > 0
