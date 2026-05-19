"""Build ThermoML XML from canonical reverse datasets."""

from __future__ import annotations

from typing import List
from xml.etree import ElementTree as ET

from .canonical_model import CanonicalDataset, RawFairFluids

NS = "http://www.iupac.org/namespaces/ThermoML"
ET.register_namespace("", NS)


def _t(tag: str) -> str:
    return f"{{{NS}}}{tag}"


def build_thermoml(raw: RawFairFluids, datasets: List[CanonicalDataset]) -> str:
    """Serialize canonical datasets to ThermoML XML string."""
    root = ET.Element(_t("DataReport"))
    _append_citation(root, raw)
    _append_compounds(root, raw)
    for ds in datasets:
        _append_dataset(root, ds)
    return ET.tostring(root, encoding="unicode")


def _append_citation(root: ET.Element, raw: RawFairFluids) -> None:
    cit = raw.citation
    if not any([cit.title, cit.doi, cit.pub_name, cit.pub_year, cit.volume, cit.page]):
        return
    citation = ET.SubElement(root, _t("Citation"))
    _set_if(citation, "sTitle", cit.title)
    _set_if(citation, "sDOI", cit.doi)
    _set_if(citation, "sPubName", cit.pub_name)
    _set_if(citation, "yrPubYr", cit.pub_year)
    _set_if(citation, "sVol", cit.volume)
    _set_if(citation, "sPage", cit.page)
    _set_if(citation, "eType", cit.lit_type)
    for author in cit.authors:
        _set_if(citation, "sAuthor", author)


def _append_compounds(root: ET.Element, raw: RawFairFluids) -> None:
    for comp in raw.compounds:
        cel = ET.SubElement(root, _t("Compound"))
        reg = ET.SubElement(cel, _t("RegNum"))
        ET.SubElement(reg, _t("nOrgNum")).text = str(comp.org_num)
        _set_if(cel, "sCommonName", comp.common_name)
        _set_if(cel, "sStandardInChI", comp.standard_inchi)
        _set_if(cel, "sStandardInChIKey", comp.standard_inchi_key)


def _append_dataset(root: ET.Element, ds: CanonicalDataset) -> None:
    pom = ET.SubElement(root, _t("PureOrMixtureData"))
    ET.SubElement(pom, _t("nPureOrMixtureDataNumber")).text = str(ds.dataset_number)
    _set_if(pom, "eExpPurpose", ds.exp_purpose)

    for org_num in ds.component_org_nums:
        comp = ET.SubElement(pom, _t("Component"))
        reg = ET.SubElement(comp, _t("RegNum"))
        ET.SubElement(reg, _t("nOrgNum")).text = str(org_num)

    for prop in ds.properties:
        prop_el = ET.SubElement(pom, _t("Property"))
        ET.SubElement(prop_el, _t("nPropNumber")).text = str(prop.prop_number)
        pmid = ET.SubElement(prop_el, _t("Property-MethodID"))
        pg = ET.SubElement(pmid, _t("PropertyGroup"))
        pge = ET.SubElement(pg, _t("PropertyGroupEntry"))
        ET.SubElement(pge, _t("ePropName")).text = prop.thermoml_name
        _set_if(pge, "sMethodName", prop.method_name)
        if prop.reg_num is not None:
            reg = ET.SubElement(pmid, _t("RegNum"))
            ET.SubElement(reg, _t("nOrgNum")).text = str(prop.reg_num)

    for var in ds.variables:
        var_el = ET.SubElement(pom, _t("Variable"))
        ET.SubElement(var_el, _t("nVarNumber")).text = str(var.var_number)
        vid = ET.SubElement(var_el, _t("VariableID"))
        vtype = ET.SubElement(vid, _t("VariableType"))
        ET.SubElement(vtype, _t("eVarTypeName")).text = var.thermoml_name
        if var.reg_num is not None:
            reg = ET.SubElement(vid, _t("RegNum"))
            ET.SubElement(reg, _t("nOrgNum")).text = str(var.reg_num)

    for con in ds.constraints:
        con_el = ET.SubElement(pom, _t("Constraint"))
        ET.SubElement(con_el, _t("nConstraintNumber")).text = str(con.constraint_number)
        cid = ET.SubElement(con_el, _t("ConstraintID"))
        ctype = ET.SubElement(cid, _t("ConstraintType"))
        ET.SubElement(ctype, _t("eConstraintTypeName")).text = con.thermoml_name
        ET.SubElement(con_el, _t("nConstraintValue")).text = _format_float(con.value)
        if con.reg_num is not None:
            reg = ET.SubElement(cid, _t("RegNum"))
            ET.SubElement(reg, _t("nOrgNum")).text = str(con.reg_num)

    for row in ds.rows:
        nv = ET.SubElement(pom, _t("NumValues"))
        for var_number, value in row.variable_values.items():
            vv = ET.SubElement(nv, _t("VariableValue"))
            ET.SubElement(vv, _t("nVarNumber")).text = str(var_number)
            ET.SubElement(vv, _t("nVarValue")).text = _format_float(value)
            unc = row.uncertainties.get(f"var_{var_number}_unc")
            if unc is not None:
                vu = ET.SubElement(vv, _t("VarUncertainty"))
                ET.SubElement(vu, _t("nStdUncertValue")).text = _format_float(unc)
        for prop_number, value in row.property_values.items():
            pv = ET.SubElement(nv, _t("PropertyValue"))
            ET.SubElement(pv, _t("nPropNumber")).text = str(prop_number)
            ET.SubElement(pv, _t("nPropValue")).text = _format_float(value)
            unc = row.uncertainties.get(f"prop_{prop_number}_unc")
            if unc is not None:
                pu = ET.SubElement(pv, _t("PropUncertainty"))
                ET.SubElement(pu, _t("nStdUncertValue")).text = _format_float(unc)


def _set_if(parent: ET.Element, tag: str, value: str | None) -> None:
    if value:
        ET.SubElement(parent, _t(tag)).text = value


def _format_float(value: float) -> str:
    return f"{value:.15g}"
