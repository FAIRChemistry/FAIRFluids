"""
Layer 1 (Raw) and Layer 2 (Canonical) Pydantic models.

Raw models mirror the ThermoML XML structure without any normalisation.
Canonical models represent the normalised internal representation used
by the FAIRFluids builder.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


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
    org_num: int
    compound_id: str
    common_name: Optional[str] = None
    standard_inchi: Optional[str] = None
    standard_inchi_key: Optional[str] = None


class CanonicalProperty(BaseModel):
    prop_id: str
    thermoml_name: str
    method_name: Optional[str] = None
    reg_num: Optional[int] = None


class CanonicalParameter(BaseModel):
    param_id: str
    thermoml_name: str
    is_constraint: bool = False
    constraint_value: Optional[float] = None
    reg_num: Optional[int] = None


class CanonicalRow(BaseModel):
    parameter_values: Dict[str, float] = Field(default_factory=dict)
    property_values: Dict[str, float] = Field(default_factory=dict)
    uncertainties: Dict[str, float] = Field(default_factory=dict)


class CanonicalDataset(BaseModel):
    dataset_number: int
    compounds: List[CanonicalCompound] = Field(default_factory=list)
    properties: Dict[str, CanonicalProperty] = Field(default_factory=dict)
    parameters: Dict[str, CanonicalParameter] = Field(default_factory=dict)
    rows: List[CanonicalRow] = Field(default_factory=list)
    exp_purpose: Optional[str] = None
