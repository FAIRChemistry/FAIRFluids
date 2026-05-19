"""
Layer 1 — XML Parser.

Parses a ThermoML XML file into raw dataclasses without any enum mapping
or unit normalisation.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional
from xml.etree import ElementTree as ET

from .canonical_model import (
    RawCitation,
    RawComponent,
    RawCompound,
    RawConstraint,
    RawDataset,
    RawNumValue,
    RawProperty,
    RawPropertyValue,
    RawThermoML,
    RawVariable,
    RawVariableValue,
)

logger = logging.getLogger(__name__)

NS = "http://www.iupac.org/namespaces/ThermoML"


def _t(tag: str) -> str:
    """Qualify *tag* with the ThermoML namespace."""
    return f"{{{NS}}}{tag}"


def _text(el: Optional[ET.Element]) -> Optional[str]:
    if el is not None and el.text:
        return el.text.strip()
    return None


def _float(el: Optional[ET.Element]) -> Optional[float]:
    txt = _text(el)
    if txt:
        try:
            return float(txt)
        except ValueError:
            return None
    return None


def _int(el: Optional[ET.Element]) -> Optional[int]:
    txt = _text(el)
    if txt:
        try:
            return int(txt)
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse(xml_path: str | Path) -> RawThermoML:
    """Parse a ThermoML XML file and return a :class:`RawThermoML` object."""
    tree = ET.parse(str(xml_path))
    root = tree.getroot()

    citation = _parse_citation(root)
    compounds = _parse_compounds(root)
    datasets = _parse_datasets(root)

    return RawThermoML(
        citation=citation,
        compounds=compounds,
        datasets=datasets,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_citation(root: ET.Element) -> RawCitation:
    cit = root.find(_t("Citation"))
    if cit is None:
        return RawCitation()

    authors: List[str] = []
    for sa in cit.findall(_t("sAuthor")):
        if sa.text:
            authors.append(sa.text.strip())

    return RawCitation(
        title=_text(cit.find(_t("sTitle"))),
        doi=_text(cit.find(_t("sDOI"))),
        pub_name=_text(cit.find(_t("sPubName"))),
        pub_year=_text(cit.find(_t("yrPubYr"))),
        volume=_text(cit.find(_t("sVol"))),
        page=_text(cit.find(_t("sPage"))),
        lit_type=_text(cit.find(_t("eType"))),
        authors=authors,
    )


def _parse_compounds(root: ET.Element) -> List[RawCompound]:
    compounds: List[RawCompound] = []
    for comp_el in root.findall(_t("Compound")):
        org_num = _int(comp_el.find(f"{_t('RegNum')}/{_t('nOrgNum')}"))
        if org_num is None:
            continue

        names = comp_el.findall(_t("sCommonName"))
        common_name = _text(names[0]) if names else None

        compounds.append(
            RawCompound(
                org_num=org_num,
                common_name=common_name,
                pubchem_cid=_int(comp_el.find(_t("nPubChemCID"))),
                standard_inchi=_text(comp_el.find(_t("sStandardInChI"))),
                standard_inchi_key=_text(comp_el.find(_t("sStandardInChIKey"))),
                formula=_text(comp_el.find(_t("sFormulaMolec"))),
            )
        )
    return compounds


def _parse_datasets(root: ET.Element) -> List[RawDataset]:
    datasets: List[RawDataset] = []
    for pom in root.findall(_t("PureOrMixtureData")):
        ds_num = _int(pom.find(_t("nPureOrMixtureDataNumber"))) or 0

        components = _parse_components(pom)
        properties = _parse_properties(pom)
        variables = _parse_variables(pom)
        constraints = _parse_constraints(pom)
        num_values = _parse_num_values(pom)
        exp_purpose = _text(pom.find(_t("eExpPurpose")))

        datasets.append(
            RawDataset(
                dataset_number=ds_num,
                components=components,
                properties=properties,
                variables=variables,
                constraints=constraints,
                num_values=num_values,
                exp_purpose=exp_purpose,
            )
        )
    return datasets


def _parse_components(pom: ET.Element) -> List[RawComponent]:
    result: List[RawComponent] = []
    for comp in pom.findall(_t("Component")):
        org_num = _int(comp.find(f"{_t('RegNum')}/{_t('nOrgNum')}"))
        sample_num = _int(comp.find(_t("nSampleNm")))
        if org_num is not None:
            result.append(RawComponent(org_num=org_num, sample_num=sample_num))
    return result


def _parse_properties(pom: ET.Element) -> List[RawProperty]:
    result: List[RawProperty] = []
    for prop in pom.findall(_t("Property")):
        prop_num = _int(prop.find(_t("nPropNumber")))
        if prop_num is None:
            continue

        prop_name, method_name, reg_num = _extract_property_method_id(prop)

        result.append(
            RawProperty(
                prop_number=prop_num,
                prop_name=prop_name or "unknown",
                method_name=method_name,
                reg_num=reg_num,
            )
        )
    return result


def _extract_property_method_id(
    prop: ET.Element,
) -> tuple[Optional[str], Optional[str], Optional[int]]:
    """Extract ePropName, sMethodName and RegNum from Property-MethodID."""
    pmid = prop.find(_t("Property-MethodID"))
    if pmid is None:
        return None, None, None

    prop_name: Optional[str] = None
    method_name: Optional[str] = None

    pg = pmid.find(_t("PropertyGroup"))
    if pg is not None:
        for group_child in pg:
            name_el = group_child.find(_t("ePropName"))
            if name_el is not None:
                prop_name = _text(name_el)
            meth_el = group_child.find(_t("sMethodName"))
            if meth_el is not None:
                method_name = _text(meth_el)

    reg_num = _int(pmid.find(f"{_t('RegNum')}/{_t('nOrgNum')}"))
    return prop_name, method_name, reg_num


def _parse_variables(pom: ET.Element) -> List[RawVariable]:
    result: List[RawVariable] = []
    for var in pom.findall(_t("Variable")):
        var_num = _int(var.find(_t("nVarNumber")))
        if var_num is None:
            continue

        type_str = _extract_variable_type(var)
        reg_num = _extract_variable_reg_num(var)

        result.append(
            RawVariable(
                var_number=var_num,
                type_string=type_str or "unknown",
                reg_num=reg_num,
            )
        )
    return result


def _extract_variable_type(var: ET.Element) -> Optional[str]:
    """Walk VariableID → VariableType and return the first text child."""
    vid = var.find(_t("VariableID"))
    if vid is None:
        return None
    vtype = vid.find(_t("VariableType"))
    if vtype is None:
        return None
    for child in vtype:
        if child.text:
            return child.text.strip()
    return None


def _extract_variable_reg_num(var: ET.Element) -> Optional[int]:
    vid = var.find(_t("VariableID"))
    if vid is None:
        return None
    return _int(vid.find(f"{_t('RegNum')}/{_t('nOrgNum')}"))


def _parse_constraints(pom: ET.Element) -> List[RawConstraint]:
    result: List[RawConstraint] = []
    for con in pom.findall(_t("Constraint")):
        con_num = _int(con.find(_t("nConstraintNumber")))
        if con_num is None:
            continue

        type_str = _extract_constraint_type(con)
        value = _float(con.find(_t("nConstraintValue")))
        reg_num = _extract_constraint_reg_num(con)

        if type_str and value is not None:
            result.append(
                RawConstraint(
                    constraint_number=con_num,
                    type_string=type_str,
                    value=value,
                    reg_num=reg_num,
                )
            )
    return result


def _extract_constraint_type(con: ET.Element) -> Optional[str]:
    cid = con.find(_t("ConstraintID"))
    if cid is None:
        return None
    ctype = cid.find(_t("ConstraintType"))
    if ctype is None:
        return None
    for child in ctype:
        if child.text:
            return child.text.strip()
    return None


def _extract_constraint_reg_num(con: ET.Element) -> Optional[int]:
    cid = con.find(_t("ConstraintID"))
    if cid is None:
        return None
    return _int(cid.find(f"{_t('RegNum')}/{_t('nOrgNum')}"))


def _parse_num_values(pom: ET.Element) -> List[RawNumValue]:
    result: List[RawNumValue] = []
    for nv in pom.findall(_t("NumValues")):
        var_vals: List[RawVariableValue] = []
        for vv in nv.findall(_t("VariableValue")):
            vn = _int(vv.find(_t("nVarNumber")))
            val = _float(vv.find(_t("nVarValue")))
            unc = _extract_var_uncertainty(vv)
            if vn is not None and val is not None:
                var_vals.append(
                    RawVariableValue(var_number=vn, value=val, uncertainty=unc)
                )

        prop_vals: List[RawPropertyValue] = []
        for pv in nv.findall(_t("PropertyValue")):
            pn = _int(pv.find(_t("nPropNumber")))
            val = _float(pv.find(_t("nPropValue")))
            unc = _extract_prop_uncertainty(pv)
            if pn is not None and val is not None:
                prop_vals.append(
                    RawPropertyValue(prop_number=pn, value=val, uncertainty=unc)
                )

        result.append(
            RawNumValue(variable_values=var_vals, property_values=prop_vals)
        )
    return result


def _extract_prop_uncertainty(pv: ET.Element) -> Optional[float]:
    cu = pv.find(_t("CombinedUncertainty"))
    if cu is not None:
        expand = _float(cu.find(_t("nCombExpandUncertValue")))
        if expand is not None:
            return expand
        std = _float(cu.find(_t("nCombStdUncertValue")))
        if std is not None:
            return std

    pu = pv.find(_t("PropUncertainty"))
    if pu is not None:
        return _float(pu.find(_t("nStdUncertValue")))
    return None


def _extract_var_uncertainty(vv: ET.Element) -> Optional[float]:
    vu = vv.find(_t("VarUncertainty"))
    if vu is not None:
        return _float(vu.find(_t("nStdUncertValue")))
    return None
