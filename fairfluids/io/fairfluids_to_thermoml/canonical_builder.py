"""Build canonical reverse model from parsed FAIRFluids records."""

from __future__ import annotations

from typing import Dict, List

from .canonical_model import (
    CanonicalConstraint,
    CanonicalDataset,
    CanonicalProperty,
    CanonicalRow,
    CanonicalVariable,
    RawDataset,
    RawFairFluids,
)


def build_canonical(raw: RawFairFluids) -> List[CanonicalDataset]:
    """Convert parsed FAIRFluids datasets into canonical reverse datasets."""
    return [_build_dataset(ds) for ds in raw.datasets]


def _build_dataset(ds: RawDataset) -> CanonicalDataset:
    prop_number_by_id = {
        prop.property_id: idx for idx, prop in enumerate(ds.properties, start=1)
    }
    properties = [
        CanonicalProperty(
            prop_number=prop_number_by_id[prop.property_id],
            thermoml_name=prop.thermoml_name,
            property_id=prop.property_id,
            method_name=prop.method_name,
            reg_num=prop.reg_num,
        )
        for prop in ds.properties
    ]

    classification = _classify_parameters(ds)
    variables: List[CanonicalVariable] = []
    constraints: List[CanonicalConstraint] = []
    for var_number, param_id in enumerate(classification["variable_ids"], start=1):
        pdef = classification["by_id"][param_id]
        variables.append(
            CanonicalVariable(
                var_number=var_number,
                thermoml_name=pdef.thermoml_name,
                parameter_id=param_id,
                reg_num=pdef.reg_num,
            )
        )
    for constraint_number, param_id in enumerate(
        classification["constraint_ids"], start=1
    ):
        pdef = classification["by_id"][param_id]
        constraints.append(
            CanonicalConstraint(
                constraint_number=constraint_number,
                thermoml_name=pdef.thermoml_name,
                value=classification["constraint_values"][param_id],
                parameter_id=param_id,
                reg_num=pdef.reg_num,
            )
        )

    var_number_by_id = {v.parameter_id: v.var_number for v in variables}
    rows: List[CanonicalRow] = []
    for meas in ds.measurements:
        row = CanonicalRow()
        for prop_id, value in meas.property_values.items():
            pn = prop_number_by_id.get(prop_id)
            if pn is not None:
                row.property_values[pn] = value
                unc = meas.uncertainties.get(f"{prop_id}_unc")
                if unc is not None:
                    row.uncertainties[f"prop_{pn}_unc"] = unc
        for param_id, value in meas.parameter_values.items():
            vn = var_number_by_id.get(param_id)
            if vn is not None:
                row.variable_values[vn] = value
                unc = meas.uncertainties.get(f"{param_id}_unc")
                if unc is not None:
                    row.uncertainties[f"var_{vn}_unc"] = unc
        rows.append(row)

    return CanonicalDataset(
        dataset_number=ds.dataset_number,
        component_org_nums=ds.component_org_nums,
        properties=properties,
        variables=variables,
        constraints=constraints,
        rows=rows,
        exp_purpose=ds.exp_purpose or "Experimental",
    )


def _classify_parameters(ds: RawDataset) -> Dict[str, object]:
    values_by_id: Dict[str, List[float]] = {p.parameter_id: [] for p in ds.parameters}
    for meas in ds.measurements:
        for pid, value in meas.parameter_values.items():
            if pid in values_by_id:
                values_by_id[pid].append(value)

    variable_ids: List[str] = []
    constraint_ids: List[str] = []
    constraint_values: Dict[str, float] = {}
    for p in ds.parameters:
        vals = values_by_id.get(p.parameter_id, [])
        if vals and _all_close(vals):
            constraint_ids.append(p.parameter_id)
            constraint_values[p.parameter_id] = vals[0]
        else:
            variable_ids.append(p.parameter_id)

    if not variable_ids and constraint_ids:
        first = constraint_ids.pop(0)
        variable_ids.append(first)
        constraint_values.pop(first, None)

    return {
        "by_id": {p.parameter_id: p for p in ds.parameters},
        "variable_ids": variable_ids,
        "constraint_ids": constraint_ids,
        "constraint_values": constraint_values,
    }


def _all_close(values: List[float], tol: float = 1e-12) -> bool:
    if not values:
        return False
    first = values[0]
    return all(abs(v - first) <= tol for v in values[1:])
