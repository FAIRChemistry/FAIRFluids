"""
Layer 3 — FAIRFluids Builder.

Converts a list of ``CanonicalDataset`` objects (plus citation / compound
metadata from the raw layer) into a FAIRFluids JSON-serialisable dict.

Only depends on ``fairfluids.core.lib`` and modules within this package.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from fairfluids.core.lib import (
    Author,
    Citation,
    Compound,
    Fluid,
    LitType,
    Measurement,
    Method,
    Parameter,
    ParameterValue,
    Parameters,
    Properties,
    Property,
    PropertyValue,
    Sample,
)

from .canonical_model import (
    CanonicalDataset,
    CanonicalParameter,
    RawCitation,
    RawThermoML,
)
from .id_registry import IDRegistry
from .mappers import ParameterMapper, PropertyMapper, UnitMapper
from .pubchem import enrich_compound_from_pubchem

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LitType mapping (self-contained)
# ---------------------------------------------------------------------------

_LIT_TYPE_MAP: Dict[str, str] = {
    "journal": "JOURNAL",
    "book": "BOOK",
    "report": "REPORT",
    "patent": "PATENT",
    "thesis": "THESIS",
    "conference proceedings": "CONFERENCEPROCEEDINGS",
    "conferenceProceedings": "CONFERENCEPROCEEDINGS",
    "archived document": "ARCHIVEDDOCUMENT",
    "archivedDocument": "ARCHIVEDDOCUMENT",
    "personal correspondence": "PERSONALCORRESPONDENCE",
    "personalCorrespondence": "PERSONALCORRESPONDENCE",
    "published translation": "PUBLISHEDTRANSLATION",
    "publishedTranslation": "PUBLISHEDTRANSLATION",
    "unspecified": "UNSPECIFIED",
}

# ---------------------------------------------------------------------------
# Method mapping (self-contained)
# ---------------------------------------------------------------------------

_METHOD_MAP: Dict[str, str] = {
    "measured": "MEASURED",
    "calculated": "CALCULATED",
    "simulated": "SIMULATED",
    "literature": "LITERATURE",
    "molecular dynamics": "SIMULATED",
    "monte carlo": "SIMULATED",
    "ab initio": "CALCULATED",
    "semiempirical quantum methods": "CALCULATED",
    "molecular mechanics": "CALCULATED",
    "statistical mechanics": "CALCULATED",
    "corresponding states": "CALCULATED",
    "correlation": "CALCULATED",
    "group contribution": "CALCULATED",
    "dft": "CALCULATED",
    "quantum chemistry": "CALCULATED",
}


# ---------------------------------------------------------------------------
# Helper functions (self-contained)
# ---------------------------------------------------------------------------


def _clean_doi(doi: str) -> str:
    if not doi:
        return ""
    doi = doi.strip()
    if not doi.startswith("10."):
        if "doi.org/" in doi:
            doi = doi.split("doi.org/")[-1]
        elif "dx.doi.org/" in doi:
            doi = doi.split("dx.doi.org/")[-1]
    return doi


def _parse_authors(author_text: str) -> List[Dict[str, Optional[str]]]:
    if not author_text:
        return []
    author_text = re.sub(r"\[.*?\]", "", author_text).strip()
    authors: List[Dict[str, Optional[str]]] = []
    for entry in author_text.split(";"):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split(",", 1)
        if len(parts) == 2:
            family_name = parts[0].strip()
            given_name = parts[1].strip()
        else:
            family_name = entry
            given_name = ""
        authors.append(
            {
                "family_name": family_name,
                "given_name": given_name,
                "email": None,
                "orcid": None,
                "affiliation": None,
            }
        )
    return authors


def _map_lit_type(raw: Optional[str]) -> Optional[LitType]:
    if not raw:
        return None
    key = _LIT_TYPE_MAP.get(raw) or _LIT_TYPE_MAP.get(raw.lower())
    if key:
        try:
            return LitType[key]
        except KeyError:
            return None
    return None


def _map_method(raw: Optional[str]) -> Optional[Method]:
    if not raw:
        return None
    lower = raw.lower()
    key = _METHOD_MAP.get(lower)
    if key:
        try:
            return Method[key]
        except KeyError:
            return None
    for mkey, mval in _METHOD_MAP.items():
        if mkey in lower or lower in mkey:
            try:
                return Method[mval]
            except KeyError:
                pass
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_fairfluids(
    raw: RawThermoML,
    canonical_datasets: List[CanonicalDataset],
    fetch_from_pubchem: bool = False,
) -> Dict[str, Any]:
    """Build a FAIRFluidsDocument dict from canonical datasets + raw meta."""
    registry = IDRegistry()

    citation = _build_citation(raw.citation)
    compounds, compound_id_by_org_num = _build_compounds(
        raw, registry, fetch_from_pubchem=fetch_from_pubchem
    )

    fluids: List[Dict[str, Any]] = []
    for cds in canonical_datasets:
        fluid = _build_fluid(cds, raw, registry, compound_id_by_org_num)
        fluids.append(fluid)

    doc: Dict[str, Any] = {}
    if citation:
        doc["citation"] = citation.model_dump(mode="json", exclude_none=True)
    doc["compound"] = [
        c.model_dump(mode="json", exclude_none=True) for c in compounds
    ]
    doc["fluid"] = fluids
    return doc


# ---------------------------------------------------------------------------
# Citation
# ---------------------------------------------------------------------------


def _build_citation(raw_cit: RawCitation) -> Optional[Citation]:
    if not raw_cit.title and not raw_cit.doi:
        return None

    authors: List[Author] = []
    for author_str in raw_cit.authors:
        for parsed in _parse_authors(author_str):
            authors.append(Author(**parsed))

    lit_type = _map_lit_type(raw_cit.lit_type)
    doi = _clean_doi(raw_cit.doi) if raw_cit.doi else None

    return Citation(
        title=raw_cit.title,
        doi=doi,
        pub_name=raw_cit.pub_name,
        publication_year=raw_cit.pub_year,
        lit_volume_num=raw_cit.volume,
        page=raw_cit.page,
        litType=lit_type,
        author=authors,
    )


# ---------------------------------------------------------------------------
# Compounds
# ---------------------------------------------------------------------------


def _build_compounds(
    raw: RawThermoML,
    registry: IDRegistry,
    fetch_from_pubchem: bool = False,
) -> tuple[List[Compound], Dict[int, str]]:
    compounds: List[Compound] = []
    id_by_org_num: Dict[int, str] = {}
    for rc in raw.compounds:
        cid = registry.new_id("compound")
        id_by_org_num[rc.org_num] = cid
        pubchem_fields: Dict[str, Any] = {}
        if fetch_from_pubchem:
            pubchem_fields = enrich_compound_from_pubchem(
                common_name=rc.common_name,
                pubchem_cid=rc.pubchem_cid,
                standard_inchi=rc.standard_inchi,
                standard_inchi_key=rc.standard_inchi_key,
            )
        compounds.append(
            Compound(
                compoundID=cid,
                commonName=pubchem_fields.get("commonName", rc.common_name),
                pubChemID=pubchem_fields.get("pubChemID"),
                name_IUPAC=pubchem_fields.get("name_IUPAC"),
                smiles_code=pubchem_fields.get("smiles_code"),
                molar_weigth=pubchem_fields.get("molar_weigth"),
                standard_InChI=pubchem_fields.get("standard_InChI", rc.standard_inchi),
                standard_InChI_key=pubchem_fields.get(
                    "standard_InChI_key", rc.standard_inchi_key
                ),
            )
        )
    return compounds, id_by_org_num


# ---------------------------------------------------------------------------
# Fluid (per canonical dataset)
# ---------------------------------------------------------------------------


def _build_fluid(
    cds: CanonicalDataset,
    raw: RawThermoML,
    registry: IDRegistry,
    compound_id_by_org_num: Dict[int, str],
) -> Dict[str, Any]:
    fluid_id = registry.new_id("fluid")

    compound_refs = [
        compound_id_by_org_num[comp.org_num]
        for comp in cds.compounds
        if comp.org_num in compound_id_by_org_num
    ]
    compound_id_map = {
        comp.org_num: compound_id_by_org_num[comp.org_num]
        for comp in cds.compounds
        if comp.org_num in compound_id_by_org_num
    }

    prop_objects, prop_id_map = _build_properties(cds, registry)
    param_objects, param_id_map = _build_parameters(cds, registry, compound_id_map)
    measurements = _build_measurements(
        cds, registry, prop_id_map, param_id_map, raw,
        prop_objects, param_objects, compound_refs,
    )

    sample = Sample(
        sample_id=registry.new_id("sample"),
        associated_compounds=compound_refs,
        measurement=measurements,
    )

    fluid = Fluid(
        fluidID=[fluid_id],
        compounds=compound_refs,
        property=prop_objects,
        parameter=param_objects,
        sample=sample,
    )
    return fluid.model_dump(mode="json", exclude_none=True)


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


def _build_properties(
    cds: CanonicalDataset,
    registry: IDRegistry,
) -> tuple[List[Property], Dict[str, str]]:
    result: List[Property] = []
    id_map: Dict[str, str] = {}

    for canonical_id, cp in cds.properties.items():
        ff_id = registry.new_id("property")
        id_map[canonical_id] = ff_id

        mapped_prop = PropertyMapper.map(cp.thermoml_name)
        unit = UnitMapper.from_thermoml_name(
            cp.thermoml_name, unit_id=registry.new_id("unit")
        )

        result.append(
            Property(
                propertyID=ff_id,
                properties=mapped_prop,
                unit=unit,
            )
        )
    return result, id_map


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------


def _build_parameters(
    cds: CanonicalDataset,
    registry: IDRegistry,
    compound_id_map: Dict[int, str],
) -> tuple[List[Parameter], Dict[str, str]]:
    result: List[Parameter] = []
    id_map: Dict[str, str] = {}

    for canonical_id, cparam in cds.parameters.items():
        ff_id = registry.new_id("parameter")
        id_map[canonical_id] = ff_id

        mapped_param = ParameterMapper.map(cparam.thermoml_name)
        unit = _resolve_param_unit(cparam, registry)

        assoc: List[str] = []
        if cparam.reg_num is not None and cparam.reg_num in compound_id_map:
            assoc.append(compound_id_map[cparam.reg_num])

        result.append(
            Parameter(
                parameterID=ff_id,
                parameters=mapped_param,
                unit=unit,
                associated_compounds=assoc,
            )
        )

    # ThermoML often stores only one explicit MOLE_FRACTION variable in binary
    # systems. Add an implicit complement parameter for the other compound so
    # per-row composition can be completed to x1 + x2 = 1.
    mf_params = [p for p in result if p.parameters == Parameters.MOLE_FRACTION]
    if len(cds.compounds) == 2 and len(mf_params) == 1:
        explicit = mf_params[0]
        explicit_assoc = set(explicit.associated_compounds or [])
        missing = [c.compound_id for c in cds.compounds if c.compound_id not in explicit_assoc]
        if len(missing) == 1:
            result.append(
                Parameter(
                    parameterID=registry.new_id("parameter"),
                    parameters=Parameters.MOLE_FRACTION,
                    unit=UnitMapper.dimensionless(),
                    associated_compounds=[missing[0]],
                )
            )

    return result, id_map


def _resolve_param_unit(cparam: CanonicalParameter, registry: IDRegistry):
    name = cparam.thermoml_name.lower()
    if any(
        kw in name
        for kw in ("mole fraction", "mass fraction", "volume fraction")
    ):
        return UnitMapper.dimensionless()
    return UnitMapper.from_thermoml_name(
        cparam.thermoml_name, unit_id=registry.new_id("unit")
    )


# ---------------------------------------------------------------------------
# Measurements
# ---------------------------------------------------------------------------


def _build_measurements(
    cds: CanonicalDataset,
    registry: IDRegistry,
    prop_id_map: Dict[str, str],
    param_id_map: Dict[str, str],
    raw: RawThermoML,
    prop_objects: List[Property],
    param_objects: List[Parameter],
    compound_refs: List[str],
) -> List[Measurement]:
    method = _resolve_method(cds)
    doi = _clean_doi(raw.citation.doi) if raw.citation.doi else None

    prop_enum_by_id: Dict[str, Optional[Properties]] = {
        p.propertyID: p.properties for p in prop_objects if p.propertyID
    }
    param_enum_by_id: Dict[str, Optional[Parameters]] = {
        p.parameterID: p.parameters for p in param_objects if p.parameterID
    }

    measurements: List[Measurement] = []
    for row in cds.rows:
        m_id = registry.new_id("measurement")

        prop_values: List[PropertyValue] = []
        for canon_pid, value in row.property_values.items():
            ff_pid = prop_id_map.get(canon_pid)
            if ff_pid is None:
                continue
            unc = row.uncertainties.get(f"{canon_pid}_unc")
            prop_values.append(
                PropertyValue(
                    properties=prop_enum_by_id.get(ff_pid),
                    propertyID=ff_pid,
                    propValue=value,
                    uncertainty=unc,
                )
            )

        param_values: List[ParameterValue] = []
        for canon_pid, value in row.parameter_values.items():
            ff_pid = param_id_map.get(canon_pid)
            if ff_pid is None:
                continue
            unc = row.uncertainties.get(f"{canon_pid}_unc")
            param_values.append(
                ParameterValue(
                    parameterID=ff_pid,
                    parameters=param_enum_by_id.get(ff_pid),
                    paramValue=value,
                    uncertainty=unc,
                )
            )

        _inject_binary_mole_fraction_complement(
            param_values=param_values,
            param_objects=param_objects,
            compound_refs=compound_refs,
        )

        measurements.append(
            Measurement(
                measurement_id=m_id,
                source_doi=doi,
                propertyValue=prop_values,
                parameterValue=param_values,
                method=method,
            )
        )
    return measurements


def _inject_binary_mole_fraction_complement(
    param_values: List[ParameterValue],
    param_objects: List[Parameter],
    compound_refs: List[str],
) -> None:
    """Add missing binary mole-fraction value as complement (1 - x)."""
    if len(compound_refs) != 2:
        return

    mf_ids = {
        p.parameterID
        for p in param_objects
        if p.parameterID and p.parameters == Parameters.MOLE_FRACTION
    }
    if len(mf_ids) != 2:
        return

    existing = {
        pv.parameterID: pv
        for pv in param_values
        if pv.parameterID in mf_ids and pv.paramValue is not None
    }
    if len(existing) != 1:
        return

    known_id, known_pv = next(iter(existing.items()))
    if known_pv.paramValue is None:
        return

    missing_id = next(pid for pid in mf_ids if pid != known_id)
    complement = 1.0 - known_pv.paramValue
    if complement < 0.0:
        complement = 0.0
    elif complement > 1.0:
        complement = 1.0

    param_values.append(
        ParameterValue(
            parameterID=missing_id,
            parameters=Parameters.MOLE_FRACTION,
            paramValue=complement,
            uncertainty=None,
        )
    )


def _resolve_method(cds: CanonicalDataset) -> Optional[Method]:
    for cp in cds.properties.values():
        if cp.method_name:
            m = _map_method(cp.method_name)
            if m:
                return m

    if cds.exp_purpose:
        lower = cds.exp_purpose.lower()
        if "principal" in lower or "experimental" in lower:
            return Method.LITERATURE

    return Method.LITERATURE
