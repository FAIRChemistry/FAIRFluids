"""Parse FAIRFluids dict/json into raw reverse-conversion models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .canonical_model import (
    RawCitation,
    RawCompound,
    RawDataset,
    RawFairFluids,
    RawMeasurement,
    RawParameterDef,
    RawPropertyDef,
)
from .mappers import ParameterMapper, PropertyMapper, UnitMapper


def parse(source: str | Path | Dict[str, Any]) -> RawFairFluids:
    """Parse FAIRFluids input (path or dict) into RawFairFluids."""
    doc = _load_doc(source)
    citation = _parse_citation(doc.get("citation") or {})
    compounds, org_num_by_compound_id = _parse_compounds(doc.get("compound") or [])
    datasets = _parse_datasets(doc.get("fluid") or [], org_num_by_compound_id)
    return RawFairFluids(citation=citation, compounds=compounds, datasets=datasets)


def _load_doc(source: str | Path | Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(source, dict):
        return source
    text = Path(source).read_text(encoding="utf-8")
    return json.loads(text)


def _parse_citation(raw: Dict[str, Any]) -> RawCitation:
    authors = []
    for author in raw.get("author") or []:
        family = (author or {}).get("family_name") or ""
        given = (author or {}).get("given_name") or ""
        authors.append(", ".join([part for part in [family, given] if part]).strip())
    return RawCitation(
        title=raw.get("title"),
        doi=raw.get("doi"),
        pub_name=raw.get("pub_name"),
        pub_year=raw.get("publication_year"),
        volume=raw.get("lit_volume_num"),
        page=raw.get("page"),
        lit_type=raw.get("litType"),
        authors=[a for a in authors if a],
    )


def _parse_compounds(
    compounds: List[Dict[str, Any]],
) -> Tuple[List[RawCompound], Dict[str, int]]:
    result: List[RawCompound] = []
    org_num_by_compound_id: Dict[str, int] = {}
    for idx, comp in enumerate(compounds, start=1):
        compound_id = str(comp.get("compoundID") or f"compound_{idx}")
        org_num_by_compound_id[compound_id] = idx
        result.append(
            RawCompound(
                org_num=idx,
                compound_id=compound_id,
                common_name=comp.get("commonName"),
                standard_inchi=comp.get("standard_InChI"),
                standard_inchi_key=comp.get("standard_InChI_key"),
            )
        )
    return result, org_num_by_compound_id


def _parse_datasets(
    fluids: List[Dict[str, Any]],
    org_num_by_compound_id: Dict[str, int],
) -> List[RawDataset]:
    datasets: List[RawDataset] = []
    for ds_num, fluid in enumerate(fluids, start=1):
        prop_defs = _parse_properties(fluid.get("property") or [])
        param_defs = _parse_parameters(fluid.get("parameter") or [])
        measurements = _parse_measurements(fluid, prop_defs, param_defs)
        component_org_nums = [
            org_num_by_compound_id[cid]
            for cid in fluid.get("compounds") or []
            if cid in org_num_by_compound_id
        ]
        datasets.append(
            RawDataset(
                dataset_number=ds_num,
                component_org_nums=component_org_nums,
                properties=prop_defs,
                parameters=param_defs,
                measurements=measurements,
                exp_purpose="Experimental",
            )
        )
    return datasets


def _parse_properties(props: List[Dict[str, Any]]) -> List[RawPropertyDef]:
    result: List[RawPropertyDef] = []
    for prop in props:
        mapped = PropertyMapper.to_thermoml_name(str(prop.get("properties") or "unknown"))
        unit_suffix = UnitMapper.to_thermoml_unit(prop.get("unit"))
        thermoml_name = _append_unit(mapped, unit_suffix)
        result.append(
            RawPropertyDef(
                property_id=str(prop.get("propertyID") or ""),
                thermoml_name=thermoml_name,
                method_name="measured",
                reg_num=None,
            )
        )
    return result


def _parse_parameters(params: List[Dict[str, Any]]) -> List[RawParameterDef]:
    result: List[RawParameterDef] = []
    for param in params:
        mapped = ParameterMapper.to_thermoml_name(str(param.get("parameters") or "unknown"))
        unit_suffix = UnitMapper.to_thermoml_unit(param.get("unit"))
        thermoml_name = _append_unit(mapped, unit_suffix)
        result.append(
            RawParameterDef(
                parameter_id=str(param.get("parameterID") or ""),
                thermoml_name=thermoml_name,
                reg_num=None,
            )
        )
    return result


def _parse_measurements(
    fluid: Dict[str, Any],
    props: List[RawPropertyDef],
    params: List[RawParameterDef],
) -> List[RawMeasurement]:
    measurements: List[RawMeasurement] = []
    prop_ids = {p.property_id for p in props}
    param_ids = {p.parameter_id for p in params}
    sample = fluid.get("sample") or {}
    for row in sample.get("measurement") or []:
        prop_values: Dict[str, float] = {}
        param_values: Dict[str, float] = {}
        uncertainties: Dict[str, float] = {}
        for pv in row.get("propertyValue") or []:
            pid = str(pv.get("propertyID") or "")
            val = pv.get("propValue")
            if pid and pid in prop_ids and isinstance(val, (int, float)):
                prop_values[pid] = float(val)
                unc = pv.get("uncertainty")
                if isinstance(unc, (int, float)):
                    uncertainties[f"{pid}_unc"] = float(unc)
        for pv in row.get("parameterValue") or []:
            pid = str(pv.get("parameterID") or "")
            val = pv.get("paramValue")
            if pid and pid in param_ids and isinstance(val, (int, float)):
                param_values[pid] = float(val)
                unc = pv.get("uncertainty")
                if isinstance(unc, (int, float)):
                    uncertainties[f"{pid}_unc"] = float(unc)
        measurements.append(
            RawMeasurement(
                property_values=prop_values,
                parameter_values=param_values,
                uncertainties=uncertainties,
            )
        )
    return measurements


def _append_unit(name: str, unit: str | None) -> str:
    if not unit:
        return name
    if "," in name:
        return name
    if unit == "1":
        return name
    return f"{name}, {unit}"
