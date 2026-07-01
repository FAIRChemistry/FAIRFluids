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
    CanonicalCitation,
    CanonicalDataset,
    CanonicalDocument,
    CanonicalParameter,
    CanonicalSourceCompound,
)
from .composition import (
    complete_composition_values,
    ensure_mass_fraction_parameters,
    ensure_mole_fraction_parameters,
)
from .citation import enrich_citation_from_doi
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
    document: CanonicalDocument,
    fetch_from_pubchem: bool = True,
    fetch_from_doi: bool = False,
) -> Dict[str, Any]:
    """Build a FAIRFluidsDocument dict from a neutral :class:`CanonicalDocument`.

    When ``fetch_from_doi`` is True, a missing/partial citation block is filled
    from online bibliographic providers (Crossref / OpenAlex / Semantic Scholar)
    keyed on the document's DOI; caller-provided citation fields stay
    authoritative and network failures degrade to no enrichment.
    """
    registry = IDRegistry()

    # G4: measurement provenance (``source_doi``) defaults to the citation DOI,
    # but a producer may override it (e.g. CSV emits one document per source DOI
    # while sharing a single citation template). Resolve it before the citation
    # so the DOI lookup can attribute even a citation-less document.
    if document.source_doi:
        doi = _clean_doi(document.source_doi)
    elif document.citation.doi:
        doi = _clean_doi(document.citation.doi)
    else:
        doi = None

    citation = _build_citation(
        document.citation, effective_doi=doi, fetch_from_doi=fetch_from_doi
    )
    compounds, compound_id_by_org_num = _build_compounds(
        document.compounds, registry, fetch_from_pubchem=fetch_from_pubchem
    )

    fluids: List[Dict[str, Any]] = []
    for cds in document.datasets:
        fluid = _build_fluid(
            cds,
            doi,
            registry,
            compound_id_by_org_num,
            compounds,
            fetch_from_pubchem=fetch_from_pubchem,
            complete_composition=document.complete_composition,
        )
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


def canonical_citation_from_citation(cit: Citation) -> CanonicalCitation:
    """Convert a lib.py :class:`Citation` template into a neutral CanonicalCitation.

    Producers (CSV, CML) accept a template ``FAIRFluidsDocument`` whose citation
    block seeds attribution. This flattens it to the neutral canonical form the
    builder consumes, so the same DOI-enrichment path runs for every producer.
    """
    authors: List[str] = []
    for a in (cit.author or []):
        fam = (a.family_name or "").strip()
        giv = (a.given_name or "").strip()
        if fam and giv:
            authors.append(f"{fam}, {giv}")
        elif fam or giv:
            authors.append(fam or giv)
    return CanonicalCitation(
        title=cit.title,
        doi=cit.doi,
        pub_name=cit.pub_name,
        pub_year=cit.publication_year,
        volume=cit.lit_volume_num,
        page=cit.page,
        lit_type=(cit.litType.value if cit.litType is not None else None),
        authors=authors,
    )


def _build_citation(
    cit: CanonicalCitation,
    *,
    effective_doi: Optional[str] = None,
    fetch_from_doi: bool = False,
) -> Optional[Citation]:
    # The DOI to attribute + look up: the citation's own DOI wins, else the
    # document's measurement DOI (``source_doi``), which is how CSV documents —
    # whose citation block is otherwise empty — get attributed.
    lookup_doi = _clean_doi(cit.doi) if cit.doi else (
        _clean_doi(effective_doi) if effective_doi else None
    )
    existing = {
        "title": cit.title,
        "doi": lookup_doi,
        "pub_name": cit.pub_name,
        "pub_year": cit.pub_year,
        "volume": cit.volume,
        "page": cit.page,
        "lit_type": cit.lit_type,
    }
    # Fill gaps from the web (Crossref/OpenAlex/Semantic Scholar); the caller's
    # values above stay authoritative. A no-op when ``fetch_from_doi`` is False.
    enriched = enrich_citation_from_doi(lookup_doi, existing, fetch=fetch_from_doi)

    # Authors: producer-supplied names are authoritative; only fall back to the
    # resolved author list (which can carry ORCID iDs) when none were provided.
    authors: List[Author] = []
    for author_str in cit.authors:
        for parsed in _parse_authors(author_str):
            authors.append(Author(**parsed))
    if not authors:
        for a in enriched.get("authors", []):
            authors.append(
                Author(
                    given_name=a.get("given_name"),
                    family_name=a.get("family_name"),
                    orcid=a.get("orcid"),
                )
            )

    title = enriched.get("title")
    doi = enriched.get("doi")
    if not title and not doi and not authors:
        return None

    return Citation(
        title=title,
        doi=doi,
        pub_name=enriched.get("pub_name"),
        publication_year=enriched.get("pub_year"),
        lit_volume_num=enriched.get("volume"),
        page=enriched.get("page"),
        url_citation=enriched.get("url"),
        litType=_map_lit_type(enriched.get("lit_type")),
        author=authors,
    )


# ---------------------------------------------------------------------------
# Compounds
# ---------------------------------------------------------------------------


def _build_compounds(
    source_compounds: List[CanonicalSourceCompound],
    registry: IDRegistry,
    fetch_from_pubchem: bool = True,
) -> tuple[List[Compound], Dict[int, str]]:
    compounds: List[Compound] = []
    id_by_org_num: Dict[int, str] = {}
    for rc in source_compounds:
        cid = registry.new_id("compound")
        id_by_org_num[rc.component_key] = cid
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
    doi: Optional[str],
    registry: IDRegistry,
    compound_id_by_org_num: Dict[int, str],
    compounds: List[Compound],
    *,
    fetch_from_pubchem: bool = True,
    complete_composition: bool = True,
) -> Dict[str, Any]:
    fluid_id = registry.new_id("fluid")

    compound_refs = [
        compound_id_by_org_num[comp.component_key]
        for comp in cds.compounds
        if comp.component_key in compound_id_by_org_num
    ]
    compound_id_map = {
        comp.component_key: compound_id_by_org_num[comp.component_key]
        for comp in cds.compounds
        if comp.component_key in compound_id_by_org_num
    }

    prop_objects, prop_id_map = _build_properties(cds, registry)
    param_objects, param_id_map = _build_parameters(
        cds, registry, compound_id_map, compound_refs,
        complete_composition=complete_composition,
    )
    measurements = _build_measurements(
        cds,
        registry,
        prop_id_map,
        param_id_map,
        doi,
        prop_objects,
        param_objects,
        compound_refs,
        compounds,
        fetch_from_pubchem=fetch_from_pubchem,
        complete_composition=complete_composition,
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

        if cp.resolved_property is not None:
            mapped_prop = cp.resolved_property
        else:
            mapped_prop = PropertyMapper.map(cp.source_term)
        if cp.canonical_unit is not None:
            unit = UnitMapper.from_unit_string(
                cp.canonical_unit, unit_id=registry.new_id("unit")
            )
        else:
            unit = UnitMapper.from_thermoml_name(
                cp.source_term, unit_id=registry.new_id("unit")
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
    compound_refs: List[str],
    *,
    complete_composition: bool = True,
) -> tuple[List[Parameter], Dict[str, str]]:
    result: List[Parameter] = []
    id_map: Dict[str, str] = {}

    for canonical_id, cparam in cds.parameters.items():
        ff_id = registry.new_id("parameter")
        id_map[canonical_id] = ff_id

        if cparam.resolved_parameter is not None:
            mapped_param = cparam.resolved_parameter
        else:
            mapped_param = ParameterMapper.map(cparam.source_term)
        unit = _resolve_param_unit(cparam, registry)

        assoc: List[str] = []
        if cparam.component_ref is not None and cparam.component_ref in compound_id_map:
            assoc.append(compound_id_map[cparam.component_ref])

        result.append(
            Parameter(
                parameterID=ff_id,
                parameters=mapped_param,
                unit=unit,
                associated_compounds=assoc,
            )
        )

    if complete_composition:
        ensure_mass_fraction_parameters(result, compound_refs, registry)
        ensure_mole_fraction_parameters(result, compound_refs, registry)

    return result, id_map


def _resolve_param_unit(cparam: CanonicalParameter, registry: IDRegistry):
    if cparam.canonical_unit is not None:
        if cparam.canonical_unit.strip().lower() in ("", "dimensionless", "1"):
            return UnitMapper.dimensionless()
        return UnitMapper.from_unit_string(
            cparam.canonical_unit, unit_id=registry.new_id("unit")
        )
    name = cparam.source_term.lower()
    if any(
        kw in name
        for kw in ("mole fraction", "mass fraction", "volume fraction")
    ):
        return UnitMapper.dimensionless()
    return UnitMapper.from_thermoml_name(
        cparam.source_term, unit_id=registry.new_id("unit")
    )


# ---------------------------------------------------------------------------
# Measurements
# ---------------------------------------------------------------------------


def _build_measurements(
    cds: CanonicalDataset,
    registry: IDRegistry,
    prop_id_map: Dict[str, str],
    param_id_map: Dict[str, str],
    doi: Optional[str],
    prop_objects: List[Property],
    param_objects: List[Parameter],
    compound_refs: List[str],
    compounds: List[Compound],
    *,
    fetch_from_pubchem: bool = True,
    complete_composition: bool = True,
) -> List[Measurement]:
    dataset_method = _resolve_method(cds)

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

        if complete_composition:
            complete_composition_values(
                param_values=param_values,
                param_objects=param_objects,
                compound_refs=compound_refs,
                compounds=compounds,
                fetch_from_pubchem=fetch_from_pubchem,
            )

        row_method = row.method if row.method is not None else dataset_method

        measurements.append(
            Measurement(
                measurement_id=m_id,
                source_doi=doi,
                propertyValue=prop_values,
                parameterValue=param_values,
                method=row_method,
                method_description=row.method_description,
            )
        )
    return measurements


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
