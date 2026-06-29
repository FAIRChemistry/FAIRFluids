"""
Layer 2 — Canonical Builder.

Transforms a :class:`RawThermoML` into a list of :class:`CanonicalDataset`
objects. Assigns stable internal IDs and flattens constraints into the
parameter space so that every independent variable (including fixed
constraints) appears uniformly.
"""

from __future__ import annotations

import logging
from typing import Dict, List

from fairfluids.io.canonical.canonical_model import (
    CanonicalCitation,
    CanonicalCompound,
    CanonicalDataset,
    CanonicalDocument,
    CanonicalParameter,
    CanonicalProperty,
    CanonicalRow,
    CanonicalSourceCompound,
    RawDataset,
    RawThermoML,
)

logger = logging.getLogger(__name__)


def build_canonical(raw: RawThermoML) -> CanonicalDocument:
    """Convert *raw* into a neutral :class:`CanonicalDocument`.

    The document bundles the citation, the global compound registry, and the
    per-dataset canonical views, so that downstream builders depend only on
    neutral canonical types.
    """
    compound_map = _build_compound_map(raw)
    return CanonicalDocument(
        citation=_build_citation(raw),
        compounds=_build_source_compounds(raw),
        datasets=[_build_dataset(ds, compound_map) for ds in raw.datasets],
    )


def _build_citation(raw: RawThermoML) -> CanonicalCitation:
    c = raw.citation
    return CanonicalCitation(
        title=c.title,
        doi=c.doi,
        pub_name=c.pub_name,
        pub_year=c.pub_year,
        volume=c.volume,
        page=c.page,
        lit_type=c.lit_type,
        authors=list(c.authors),
    )


def _build_source_compounds(raw: RawThermoML) -> List[CanonicalSourceCompound]:
    return [
        CanonicalSourceCompound(
            component_key=c.org_num,
            common_name=c.common_name,
            pubchem_cid=c.pubchem_cid,
            standard_inchi=c.standard_inchi,
            standard_inchi_key=c.standard_inchi_key,
        )
        for c in raw.compounds
    ]


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _build_compound_map(raw: RawThermoML) -> Dict[int, CanonicalCompound]:
    result: Dict[int, CanonicalCompound] = {}
    for c in raw.compounds:
        cid = f"compound_{_safe(c.common_name or str(c.org_num))}"
        result[c.org_num] = CanonicalCompound(
            component_key=c.org_num,
            compound_id=cid,
            common_name=c.common_name,
            standard_inchi=c.standard_inchi,
            standard_inchi_key=c.standard_inchi_key,
        )
    return result


def _safe(name: str) -> str:
    return (
        name.lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace(",", "")
        .replace("(", "")
        .replace(")", "")
    )


def _build_dataset(
    ds: RawDataset,
    compound_map: Dict[int, CanonicalCompound],
) -> CanonicalDataset:
    compounds = [
        compound_map[comp.org_num]
        for comp in ds.components
        if comp.org_num in compound_map
    ]

    properties = _build_properties(ds)
    parameters = _build_parameters(ds)
    rows = _build_rows(ds, properties, parameters)

    return CanonicalDataset(
        index=ds.dataset_number,
        compounds=compounds,
        properties=properties,
        parameters=parameters,
        rows=rows,
        exp_purpose=ds.exp_purpose,
    )


def _build_properties(ds: RawDataset) -> Dict[str, CanonicalProperty]:
    result: Dict[str, CanonicalProperty] = {}
    for p in ds.properties:
        pid = f"prop_{p.prop_number}"
        result[pid] = CanonicalProperty(
            prop_id=pid,
            source_term=p.prop_name,
            method_name=p.method_name,
            component_ref=p.reg_num,
        )
    return result


def _build_parameters(ds: RawDataset) -> Dict[str, CanonicalParameter]:
    result: Dict[str, CanonicalParameter] = {}

    for v in ds.variables:
        pid = f"param_{v.var_number}"
        result[pid] = CanonicalParameter(
            param_id=pid,
            source_term=v.type_string,
            component_ref=v.reg_num,
        )

    for c in ds.constraints:
        pid = f"constraint_{c.constraint_number}"
        result[pid] = CanonicalParameter(
            param_id=pid,
            source_term=c.type_string,
            is_constraint=True,
            constraint_value=c.value,
            component_ref=c.reg_num,
        )

    return result


def _build_rows(
    ds: RawDataset,
    properties: Dict[str, CanonicalProperty],
    parameters: Dict[str, CanonicalParameter],
) -> List[CanonicalRow]:
    var_id_map = {v.var_number: f"param_{v.var_number}" for v in ds.variables}
    prop_id_map = {p.prop_number: f"prop_{p.prop_number}" for p in ds.properties}

    rows: List[CanonicalRow] = []
    for nv in ds.num_values:
        row = CanonicalRow()

        for vv in nv.variable_values:
            pid = var_id_map.get(vv.var_number)
            if pid:
                row.parameter_values[pid] = vv.value
                if vv.uncertainty is not None:
                    row.uncertainties[f"{pid}_unc"] = vv.uncertainty

        for cp in parameters.values():
            if cp.is_constraint and cp.constraint_value is not None:
                row.parameter_values[cp.param_id] = cp.constraint_value

        for pv in nv.property_values:
            pid = prop_id_map.get(pv.prop_number)
            if pid:
                row.property_values[pid] = pv.value
                if pv.uncertainty is not None:
                    row.uncertainties[f"{pid}_unc"] = pv.uncertainty

        rows.append(row)
    return rows
