"""
Layer 1 (Raw) and Layer 2 (Canonical) Pydantic models.

Raw models mirror the ThermoML XML structure without any normalisation.
Canonical models represent the normalised internal representation used
by the FAIRFluids builder.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from fairfluids.core.lib import Method, Parameters, Properties


# ---------------------------------------------------------------------------
# Layer 1 – Raw models (output of parser.py)
# ---------------------------------------------------------------------------


class RawVariableValue(BaseModel):
    var_number: int
    value: float
    uncertainty: Optional[float] = None


class RawPropertyValue(BaseModel):
    prop_number: int
    value: float
    uncertainty: Optional[float] = None


class RawNumValue(BaseModel):
    variable_values: List[RawVariableValue] = Field(default_factory=list)
    property_values: List[RawPropertyValue] = Field(default_factory=list)


class RawVariable(BaseModel):
    var_number: int
    type_string: str
    reg_num: Optional[int] = None


class RawProperty(BaseModel):
    prop_number: int
    prop_name: str
    method_name: Optional[str] = None
    reg_num: Optional[int] = None


class RawConstraint(BaseModel):
    constraint_number: int
    type_string: str
    value: float
    reg_num: Optional[int] = None


class RawComponent(BaseModel):
    org_num: int
    sample_num: Optional[int] = None


class RawDataset(BaseModel):
    dataset_number: int
    components: List[RawComponent] = Field(default_factory=list)
    properties: List[RawProperty] = Field(default_factory=list)
    variables: List[RawVariable] = Field(default_factory=list)
    constraints: List[RawConstraint] = Field(default_factory=list)
    num_values: List[RawNumValue] = Field(default_factory=list)
    exp_purpose: Optional[str] = None


class RawCompound(BaseModel):
    org_num: int
    common_name: Optional[str] = None
    pubchem_cid: Optional[int] = None
    standard_inchi: Optional[str] = None
    standard_inchi_key: Optional[str] = None
    formula: Optional[str] = None


class RawCitation(BaseModel):
    title: Optional[str] = None
    doi: Optional[str] = None
    pub_name: Optional[str] = None
    pub_year: Optional[str] = None
    volume: Optional[str] = None
    page: Optional[str] = None
    lit_type: Optional[str] = None
    authors: List[str] = Field(default_factory=list)


class RawThermoML(BaseModel):
    citation: RawCitation = Field(default_factory=RawCitation)
    compounds: List[RawCompound] = Field(default_factory=list)
    datasets: List[RawDataset] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Layer 2 – Canonical models (normalised, mapper-ready)
# ---------------------------------------------------------------------------


class CanonicalCompound(BaseModel):
    component_key: int
    compound_id: str
    common_name: Optional[str] = None
    standard_inchi: Optional[str] = None
    standard_inchi_key: Optional[str] = None


class CanonicalProperty(BaseModel):
    prop_id: str
    source_term: str
    method_name: Optional[str] = None
    component_ref: Optional[int] = None
    # Route B: a producer that already knows the controlled-vocab member and
    # canonical unit may set these to bypass the source-term name mappers.
    resolved_property: Optional[Properties] = None
    canonical_unit: Optional[str] = None


class CanonicalParameter(BaseModel):
    param_id: str
    source_term: str
    is_constraint: bool = False
    constraint_value: Optional[float] = None
    component_ref: Optional[int] = None
    # Route B: pre-resolved controlled-vocab member + canonical unit string.
    # ``canonical_unit`` of "" or "dimensionless" yields a dimensionless unit.
    resolved_parameter: Optional[Parameters] = None
    canonical_unit: Optional[str] = None


class CanonicalRow(BaseModel):
    parameter_values: Dict[str, float] = Field(default_factory=dict)
    property_values: Dict[str, float] = Field(default_factory=dict)
    uncertainties: Dict[str, float] = Field(default_factory=dict)
    # Route B: a producer that knows the method per measurement (e.g. CML mixes
    # measured/simulated within one fluid) may set these per row. When unset,
    # the builder falls back to a dataset-level method.
    method: Optional[Method] = None
    method_description: Optional[str] = None


class CanonicalDataset(BaseModel):
    index: int
    compounds: List[CanonicalCompound] = Field(default_factory=list)
    properties: Dict[str, CanonicalProperty] = Field(default_factory=dict)
    parameters: Dict[str, CanonicalParameter] = Field(default_factory=dict)
    rows: List[CanonicalRow] = Field(default_factory=list)
    exp_purpose: Optional[str] = None


# ---------------------------------------------------------------------------
# Layer 2 – Document-level metadata (source-format neutral)
# ---------------------------------------------------------------------------
#
# These bundle the citation and the global compound list so that the
# FAIRFluids builder depends only on neutral canonical types, never on the
# ThermoML-specific Layer-1 ``Raw*`` models.


class CanonicalCitation(BaseModel):
    title: Optional[str] = None
    doi: Optional[str] = None
    pub_name: Optional[str] = None
    pub_year: Optional[str] = None
    volume: Optional[str] = None
    page: Optional[str] = None
    lit_type: Optional[str] = None
    authors: List[str] = Field(default_factory=list)


class CanonicalSourceCompound(BaseModel):
    """A compound in the document-global registry (pre-FAIRFluids-ID)."""

    component_key: int
    common_name: Optional[str] = None
    pubchem_cid: Optional[int] = None
    standard_inchi: Optional[str] = None
    standard_inchi_key: Optional[str] = None


class CanonicalDocument(BaseModel):
    """Neutral, source-format-agnostic input to the FAIRFluids builder."""

    citation: CanonicalCitation = Field(default_factory=CanonicalCitation)
    compounds: List[CanonicalSourceCompound] = Field(default_factory=list)
    datasets: List[CanonicalDataset] = Field(default_factory=list)
    # Route B: ThermoML reports partial composition that must be inferred and
    # completed. Producers that already provide fully-specified composition
    # (e.g. CML, which computes exact mole fractions) set this False to bypass
    # the inference/completion machinery.
    complete_composition: bool = True
    # Route B / G4: the DOI stamped onto every measurement's ``source_doi``.
    # When unset, the builder falls back to ``citation.doi`` (the behaviour
    # ThermoML and CML rely on). Producers whose measurement provenance is
    # decoupled from the citation block (e.g. CSV, where one citation template
    # spans several per-DOI documents) set this explicitly.
    source_doi: Optional[str] = None
