"""Raw and canonical models for FAIRFluids -> ThermoML conversion."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RawCitation(BaseModel):
    title: Optional[str] = None
    doi: Optional[str] = None
    pub_name: Optional[str] = None
    pub_year: Optional[str] = None
    volume: Optional[str] = None
    page: Optional[str] = None
    lit_type: Optional[str] = None
    authors: List[str] = Field(default_factory=list)


class RawCompound(BaseModel):
    org_num: int
    compound_id: str
    common_name: Optional[str] = None
    standard_inchi: Optional[str] = None
    standard_inchi_key: Optional[str] = None


class RawPropertyDef(BaseModel):
    property_id: str
    thermoml_name: str
    method_name: Optional[str] = None
    reg_num: Optional[int] = None


class RawParameterDef(BaseModel):
    parameter_id: str
    thermoml_name: str
    reg_num: Optional[int] = None


class RawMeasurement(BaseModel):
    property_values: Dict[str, float] = Field(default_factory=dict)
    parameter_values: Dict[str, float] = Field(default_factory=dict)
    uncertainties: Dict[str, float] = Field(default_factory=dict)


class RawDataset(BaseModel):
    dataset_number: int
    component_org_nums: List[int] = Field(default_factory=list)
    properties: List[RawPropertyDef] = Field(default_factory=list)
    parameters: List[RawParameterDef] = Field(default_factory=list)
    measurements: List[RawMeasurement] = Field(default_factory=list)
    exp_purpose: Optional[str] = None


class RawFairFluids(BaseModel):
    citation: RawCitation = Field(default_factory=RawCitation)
    compounds: List[RawCompound] = Field(default_factory=list)
    datasets: List[RawDataset] = Field(default_factory=list)


class CanonicalVariable(BaseModel):
    var_number: int
    thermoml_name: str
    parameter_id: str
    reg_num: Optional[int] = None


class CanonicalConstraint(BaseModel):
    constraint_number: int
    thermoml_name: str
    value: float
    parameter_id: str
    reg_num: Optional[int] = None


class CanonicalProperty(BaseModel):
    prop_number: int
    thermoml_name: str
    property_id: str
    method_name: Optional[str] = None
    reg_num: Optional[int] = None


class CanonicalRow(BaseModel):
    variable_values: Dict[int, float] = Field(default_factory=dict)
    property_values: Dict[int, float] = Field(default_factory=dict)
    uncertainties: Dict[str, float] = Field(default_factory=dict)


class CanonicalDataset(BaseModel):
    dataset_number: int
    component_org_nums: List[int] = Field(default_factory=list)
    properties: List[CanonicalProperty] = Field(default_factory=list)
    variables: List[CanonicalVariable] = Field(default_factory=list)
    constraints: List[CanonicalConstraint] = Field(default_factory=list)
    rows: List[CanonicalRow] = Field(default_factory=list)
    exp_purpose: Optional[str] = None
