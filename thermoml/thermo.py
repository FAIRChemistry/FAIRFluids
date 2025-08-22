"""
This file contains Pydantic XML model definitions for data validation.

Pydantic is a data validation library that uses Python type annotations.
It allows you to define data models with type hints that are validated
at runtime while providing static type checking.

Usage example:
```python
from my_model import MyModel

# Validates data at runtime
my_model = MyModel(name="John", age=30)

# Type-safe - my_model has correct type hints
print(my_model.name)

# Will raise error if validation fails
try:
    MyModel(name="", age=30)
except ValidationError as e:
    print(e)
```

For more information see:
https://pydantic-xml.readthedocs.io/en/latest/

WARNING: This is an auto-generated file.
Do not edit directly - any changes will be overwritten.
"""

## This is a generated file. Do not modify it manually!


from __future__ import annotations
from typing import Dict, List, Optional, Union
from uuid import uuid4
from datetime import date, datetime
from xml.dom import minidom
from enum import Enum

from lxml.etree import _Element
from pydantic import PrivateAttr, model_validator
from pydantic_xml import attr, wrapped, element, BaseXmlModel


class DataReport(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Contains metadata and experimental context for a dataset related to
    a fluid system.
    """
    citation: Optional[Citation] = element(
        default= None,
        tag="citation",
        description="""Citation information about the data report""",
        json_schema_extra=dict(),
    )
    version: Optional[Version] = element(
        default= None,
        tag="version",
        description="""Version information for the data report""",
        json_schema_extra=dict(),
    )
    compound: list[Compound] = element(
        default_factory=list,
        tag="compound",
        description="""List of compounds present in the fluid system""",
        json_schema_extra=dict(),
    )
    pure_or_mixture_data: list[PureOrMixtureData] = element(
        default_factory=list,
        tag="pure_or_mixture_data",
        description="""Data for pure substances or mixtures""",
        json_schema_extra=dict(),
    )
    reaction_data: list[ReactionData] = element(
        default_factory=list,
        tag="reaction_data",
        description="""Data for chemical reactions""",
        json_schema_extra=dict(),
    )


    def add_to_compound(
        self,
        biomaterial: Optional[Biomaterial]= None,
        ion: Optional[Ion]= None,
        multicomponent_substance: Optional[MulticomponentSubstance]= None,
        polymer: Optional[Polymer]= None,
        e_speciation_state: Union[None,eSpeciationState,str]= None,
        n_comp_index: Optional[int]= None,
        n_pub_chem_id: Optional[int]= None,
        reg_num: Optional[RegNum]= None,
        s_cas_name: Optional[str]= None,
        s_common_name: list[str]= [],
        s_formula_molec: Optional[str]= None,
        s_iupac_name: Optional[str]= None,
        s_org_id: list[SOrgID]= [],
        s_smiles: list[str]= [],
        s_standard_in_ch_i: Optional[str]= None,
        s_standard_in_ch_i_key: Optional[str]= None,
        sample: list[Sample]= [],
        **kwargs,
    ):
        """Helper method to add a new Compound to the compound list."""
        params = {
            "biomaterial": biomaterial,
            "ion": ion,
            "multicomponent_substance": multicomponent_substance,
            "polymer": polymer,
            "e_speciation_state": e_speciation_state,
            "n_comp_index": n_comp_index,
            "n_pub_chem_id": n_pub_chem_id,
            "reg_num": reg_num,
            "s_cas_name": s_cas_name,
            "s_common_name": s_common_name,
            "s_formula_molec": s_formula_molec,
            "s_iupac_name": s_iupac_name,
            "s_org_id": s_org_id,
            "s_smiles": s_smiles,
            "s_standard_in_ch_i": s_standard_in_ch_i,
            "s_standard_in_ch_i_key": s_standard_in_ch_i_key,
            "sample": sample
        }

        self.compound.append(
            Compound(**params)
        )

        return self.compound[-1]

    def add_to_pure_or_mixture_data(
        self,
        component: list[Component]= [],
        phase_id: list[PhaseID]= [],
        property: list[Property]= [],
        auxiliary_substance: list[AuxiliarySubstance]= [],
        constraint: list[Constraint]= [],
        date_date_added: Optional[str]= None,
        e_exp_purpose: Union[None,eExpPurpose,str]= None,
        equation: list[Equation]= [],
        n_pure_or_mixture_data_number: Optional[int]= None,
        num_values: list[NumValues]= [],
        s_compiler: Optional[str]= None,
        s_contributor: Optional[str]= None,
        variable: list[Variable]= [],
        **kwargs,
    ):
        """Helper method to add a new PureOrMixtureData to the pure_or_mixture_data list."""
        params = {
            "component": component,
            "phase_id": phase_id,
            "property": property,
            "auxiliary_substance": auxiliary_substance,
            "constraint": constraint,
            "date_date_added": date_date_added,
            "e_exp_purpose": e_exp_purpose,
            "equation": equation,
            "n_pure_or_mixture_data_number": n_pure_or_mixture_data_number,
            "num_values": num_values,
            "s_compiler": s_compiler,
            "s_contributor": s_contributor,
            "variable": variable
        }

        self.pure_or_mixture_data.append(
            PureOrMixtureData(**params)
        )

        return self.pure_or_mixture_data[-1]

    def add_to_reaction_data(
        self,
        e_reaction_type: Union[None,eReactionType,str]= None,
        participant: list[Participant]= [],
        property: list[Property]= [],
        auxiliary_substance: list[AuxiliarySubstance]= [],
        constraint: list[Constraint]= [],
        date_date_added: Optional[str]= None,
        e_exp_purpose: Union[None,eExpPurpose,str]= None,
        e_reaction_formalism: Union[None,eReactionFormalism,str]= None,
        equation: list[Equation]= [],
        n_electron_number: Optional[int]= None,
        n_reaction_data_number: Optional[int]= None,
        num_values: list[NumValues]= [],
        s_compiler: Optional[str]= None,
        s_contributor: Optional[str]= None,
        solvent: list[Solvent]= [],
        variable: list[Variable]= [],
        **kwargs,
    ):
        """Helper method to add a new ReactionData to the reaction_data list."""
        params = {
            "e_reaction_type": e_reaction_type,
            "participant": participant,
            "property": property,
            "auxiliary_substance": auxiliary_substance,
            "constraint": constraint,
            "date_date_added": date_date_added,
            "e_exp_purpose": e_exp_purpose,
            "e_reaction_formalism": e_reaction_formalism,
            "equation": equation,
            "n_electron_number": n_electron_number,
            "n_reaction_data_number": n_reaction_data_number,
            "num_values": num_values,
            "s_compiler": s_compiler,
            "s_contributor": s_contributor,
            "solvent": solvent,
            "variable": variable
        }

        self.reaction_data.append(
            ReactionData(**params)
        )

        return self.reaction_data[-1]
    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Version(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Version information for the data report.
    """
    n_version_major: Optional[int] = element(
        default= None,
        tag="n_version_major",
        description="""Major version number""",
        json_schema_extra=dict(),
    )
    n_version_minor: Optional[int] = element(
        default= None,
        tag="n_version_minor",
        description="""Minor version number""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Citation(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Contains bibliographic information about the source publication.
    """
    book: Optional[Book] = element(
        default= None,
        tag="book",
        description="""Book publication details""",
        json_schema_extra=dict(),
    )
    journal: Optional[Journal] = element(
        default= None,
        tag="journal",
        description="""Journal publication details""",
        json_schema_extra=dict(),
    )
    thesis: Optional[Thesis] = element(
        default= None,
        tag="thesis",
        description="""Thesis publication details""",
        json_schema_extra=dict(),
    )
    date_cit: Optional[str] = element(
        default= None,
        tag="date_cit",
        description="""Date of the citation""",
        json_schema_extra=dict(),
    )
    e_language: Union[None,eLanguage,str] = element(
        default= None,
        tag="e_language",
        description="""Language of publication""",
        json_schema_extra=dict(),
    )
    e_source_type: Union[None,eSourceType,str] = element(
        default= None,
        tag="e_source_type",
        description="""The source status type for a citation""",
        json_schema_extra=dict(),
    )
    e_type: Union[None,eType,str] = element(
        default= None,
        tag="e_type",
        description="""The type of publication""",
        json_schema_extra=dict(),
    )
    s_abstract: Optional[str] = element(
        default= None,
        tag="s_abstract",
        description="""An abstract of the publication""",
        json_schema_extra=dict(),
    )
    s_author: list[str] = element(
        default_factory=list,
        tag="s_author",
        description="""Author of publication""",
        json_schema_extra=dict(),
    )
    s_cas_cit: Optional[str] = element(
        default= None,
        tag="s_cas_cit",
        description="""The Chemical Abstracts Service citation""",
        json_schema_extra=dict(),
    )
    s_document_origin: Optional[str] = element(
        default= None,
        tag="s_document_origin",
        description="""Company, institution, or conference name""",
        json_schema_extra=dict(),
    )
    s_doi: Optional[str] = element(
        default= None,
        tag="s_doi",
        description="""DOI""",
        json_schema_extra=dict(),
    )
    s_id_num: Optional[str] = element(
        default= None,
        tag="s_id_num",
        description="""Identification number, e.g., a patent number or a document number""",
        json_schema_extra=dict(),
    )
    s_keyword: list[str] = element(
        default_factory=list,
        tag="s_keyword",
        description="""Keywords associated with the publication""",
        json_schema_extra=dict(),
    )
    s_location: Optional[str] = element(
        default= None,
        tag="s_location",
        description="""Reference to a location""",
        json_schema_extra=dict(),
    )
    s_page: Optional[str] = element(
        default= None,
        tag="s_page",
        description="""Page range where the publication can be found""",
        json_schema_extra=dict(),
    )
    s_pub_name: Optional[str] = element(
        default= None,
        tag="s_pub_name",
        description="""Name of the publication""",
        json_schema_extra=dict(),
    )
    s_title: Optional[str] = element(
        default= None,
        tag="s_title",
        description="""Title of the publication""",
        json_schema_extra=dict(),
    )
    s_vol: Optional[str] = element(
        default= None,
        tag="s_vol",
        description="""Volume number""",
        json_schema_extra=dict(),
    )
    trc_ref_id: Optional[TRCRefID] = element(
        default= None,
        tag="trc_ref_id",
        description="""TRC reference identifier""",
        json_schema_extra=dict(),
    )
    url_cit: Optional[str] = element(
        default= None,
        tag="url_cit",
        description="""URL to the publication""",
        json_schema_extra=dict(),
    )
    yr_pub_yr: Optional[str] = element(
        default= None,
        tag="yr_pub_yr",
        description="""Publication year""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class TRCRefID(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: TRC reference identifier for distinguishing conflicts.
    """
    n_authorn: Optional[int] = element(
        default= None,
        tag="n_authorn",
        description="""Integer identifier to distinguish conflicts""",
        json_schema_extra=dict(),
    )
    s_author1: Optional[str] = element(
        default= None,
        tag="s_author1",
        description="""First 3 characters of Author 1 last name""",
        json_schema_extra=dict(),
    )
    s_author2: Optional[str] = element(
        default= None,
        tag="s_author2",
        description="""First 3 characters of Author 2 last name""",
        json_schema_extra=dict(),
    )
    yr_yr_pub: Optional[int] = element(
        default= None,
        tag="yr_yr_pub",
        description="""Integer year of publication""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Book(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Book publication details.
    """
    s_chapter: Optional[str] = element(
        default= None,
        tag="s_chapter",
        description="""Chapter number""",
        json_schema_extra=dict(),
    )
    s_edition: Optional[str] = element(
        default= None,
        tag="s_edition",
        description="""Edition number of the book""",
        json_schema_extra=dict(),
    )
    s_editor: list[str] = element(
        default_factory=list,
        tag="s_editor",
        description="""Editor of the book""",
        json_schema_extra=dict(),
    )
    s_isbn: Optional[str] = element(
        default= None,
        tag="s_isbn",
        description="""The International Standard Book Number""",
        json_schema_extra=dict(),
    )
    s_publisher: Optional[str] = element(
        default= None,
        tag="s_publisher",
        description="""Publisher name and city""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Journal(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Journal publication details.
    """
    s_coden: Optional[str] = element(
        default= None,
        tag="s_coden",
        description="""The CODEN identification of the journal""",
        json_schema_extra=dict(),
    )
    s_issn: Optional[str] = element(
        default= None,
        tag="s_issn",
        description="""The International Standard Subscription Number""",
        json_schema_extra=dict(),
    )
    s_issue: Optional[str] = element(
        default= None,
        tag="s_issue",
        description="""Issue number, usually indicates month""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Thesis(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Thesis publication details.
    """
    s_deg: Optional[str] = element(
        default= None,
        tag="s_deg",
        description="""Academic degree designation, e.g., MS or PhD""",
        json_schema_extra=dict(),
    )
    s_deg_inst: Optional[str] = element(
        default= None,
        tag="s_deg_inst",
        description="""Academic degree granting institution""",
        json_schema_extra=dict(),
    )
    s_umi_pub_num: Optional[str] = element(
        default= None,
        tag="s_umi_pub_num",
        description="""University Microfilms International Publication Number""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Compound(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Contains metadata for a chemical compound, including identifiers,
    names, and structural representations.
    """
    biomaterial: Optional[Biomaterial] = element(
        default= None,
        tag="biomaterial",
        description="""Biomaterial compound information""",
        json_schema_extra=dict(),
    )
    ion: Optional[Ion] = element(
        default= None,
        tag="ion",
        description="""Ion compound information""",
        json_schema_extra=dict(),
    )
    multicomponent_substance: Optional[MulticomponentSubstance] = element(
        default= None,
        tag="multicomponent_substance",
        description="""Multicomponent substance information""",
        json_schema_extra=dict(),
    )
    polymer: Optional[Polymer] = element(
        default= None,
        tag="polymer",
        description="""Polymer compound information""",
        json_schema_extra=dict(),
    )
    e_speciation_state: Union[None,eSpeciationState,str] = element(
        default= None,
        tag="e_speciation_state",
        description="""Speciation state of the compound""",
        json_schema_extra=dict(),
    )
    n_comp_index: Optional[int] = element(
        default= None,
        tag="n_comp_index",
        description="""Index to link compounds to data""",
        json_schema_extra=dict(),
    )
    n_pub_chem_id: Optional[int] = element(
        default= None,
        tag="n_pub_chem_id",
        description="""PubChem compound identifier""",
        json_schema_extra=dict(),
    )
    reg_num: Optional[RegNum] = element(
        default= None,
        tag="reg_num",
        description="""Registration number information""",
        json_schema_extra=dict(),
    )
    s_cas_name: Optional[str] = element(
        default= None,
        tag="s_cas_name",
        description="""CAS name of the compound""",
        json_schema_extra=dict(),
    )
    s_common_name: list[str] = element(
        default_factory=list,
        tag="s_common_name",
        description="""Common names of the compound""",
        json_schema_extra=dict(),
    )
    s_formula_molec: Optional[str] = element(
        default= None,
        tag="s_formula_molec",
        description="""Molecular formula""",
        json_schema_extra=dict(),
    )
    s_iupac_name: Optional[str] = element(
        default= None,
        tag="s_iupac_name",
        description="""IUPAC name of the compound""",
        json_schema_extra=dict(),
    )
    s_org_id: list[SOrgID] = element(
        default_factory=list,
        tag="s_org_id",
        description="""Organization identifiers""",
        json_schema_extra=dict(),
    )
    s_smiles: list[str] = element(
        default_factory=list,
        tag="s_smiles",
        description="""SMILES notation""",
        json_schema_extra=dict(),
    )
    s_standard_in_ch_i: Optional[str] = element(
        default= None,
        tag="s_standard_in_ch_i",
        description="""Standard InChI string""",
        json_schema_extra=dict(),
    )
    s_standard_in_ch_i_key: Optional[str] = element(
        default= None,
        tag="s_standard_in_ch_i_key",
        description="""Standard InChI key""",
        json_schema_extra=dict(),
    )
    sample: list[Sample] = element(
        default_factory=list,
        tag="sample",
        description="""Sample information""",
        json_schema_extra=dict(),
    )


    def add_to_s_org_id(
        self,
        s_org_identifier: Optional[str]= None,
        s_organization: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new SOrgID to the s_org_id list."""
        params = {
            "s_org_identifier": s_org_identifier,
            "s_organization": s_organization
        }

        self.s_org_id.append(
            SOrgID(**params)
        )

        return self.s_org_id[-1]

    def add_to_sample(
        self,
        n_sample_nm: Optional[int]= None,
        component_sample: list[ComponentSample]= [],
        e_source: Union[None,eSource,str]= None,
        e_status: Union[None,eStatus,str]= None,
        purity: list[Purity]= [],
        **kwargs,
    ):
        """Helper method to add a new Sample to the sample list."""
        params = {
            "n_sample_nm": n_sample_nm,
            "component_sample": component_sample,
            "e_source": e_source,
            "e_status": e_status,
            "purity": purity
        }

        self.sample.append(
            Sample(**params)
        )

        return self.sample[-1]
    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class RegNum(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Registration number information for compounds.
    """
    n_org_num: Optional[int] = element(
        default= None,
        tag="n_org_num",
        description="""Organization number""",
        json_schema_extra=dict(),
    )
    n_casr_num: Optional[int] = element(
        default= None,
        tag="n_casr_num",
        description="""CAS registry number""",
        json_schema_extra=dict(),
    )
    s_organization: Optional[str] = element(
        default= None,
        tag="s_organization",
        description="""Organization name""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class SOrgID(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Organization identifier information.
    """
    s_org_identifier: Optional[str] = element(
        default= None,
        tag="s_org_identifier",
        description="""Organization identifier""",
        json_schema_extra=dict(),
    )
    s_organization: Optional[str] = element(
        default= None,
        tag="s_organization",
        description="""Organization name""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Polymer(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Polymer compound information.
    """
    n_deg_of_polymerization_dispersity: Optional[float] = element(
        default= None,
        tag="n_deg_of_polymerization_dispersity",
        description="""Degree of polymerization dispersity""",
        json_schema_extra=dict(),
    )
    n_mass_avg_mol_mass: Optional[float] = element(
        default= None,
        tag="n_mass_avg_mol_mass",
        description="""Weight average molecular mass, kg/kmol""",
        json_schema_extra=dict(),
    )
    n_molar_mass_dispersity: Optional[float] = element(
        default= None,
        tag="n_molar_mass_dispersity",
        description="""Molar mass dispersity""",
        json_schema_extra=dict(),
    )
    n_number_avg_mol_mass: Optional[float] = element(
        default= None,
        tag="n_number_avg_mol_mass",
        description="""Number average molecular mass, kg/kmol""",
        json_schema_extra=dict(),
    )
    n_peak_avg_mol_mass: Optional[float] = element(
        default= None,
        tag="n_peak_avg_mol_mass",
        description="""Peak average molecular mass, kg/kmol""",
        json_schema_extra=dict(),
    )
    n_viscosity_avg_mol_mass: Optional[float] = element(
        default= None,
        tag="n_viscosity_avg_mol_mass",
        description="""Viscosity average molecular mass, kg/kmol""",
        json_schema_extra=dict(),
    )
    n_z_avg_mol_mass: Optional[float] = element(
        default= None,
        tag="n_z_avg_mol_mass",
        description="""Z average molecular mass, kg/kmol""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Ion(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Ion compound information.
    """
    n_charge: Optional[int] = element(
        default= None,
        tag="n_charge",
        description="""Charge of the ion""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Biomaterial(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Biomaterial compound information.
    """
    s_ec_number: Optional[str] = element(
        default= None,
        tag="s_ec_number",
        description="""EC number""",
        json_schema_extra=dict(),
    )
    s_pdb_identifier: Optional[str] = element(
        default= None,
        tag="s_pdb_identifier",
        description="""PDB identifier""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class MulticomponentSubstance(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Multicomponent substance information.
    """
    component: list[Component] = element(
        default_factory=list,
        tag="component",
        description="""List of components""",
        json_schema_extra=dict(),
    )
    composition_basis: Optional[str] = element(
        default= None,
        tag="composition_basis",
        description="""Composition basis""",
        json_schema_extra=dict(),
    )
    type: Optional[str] = element(
        default= None,
        tag="type",
        description="""Type of substance""",
        json_schema_extra=dict(),
    )


    def add_to_component(
        self,
        n_amount: Optional[float]= None,
        n_comp_index: Optional[int]= None,
        reg_num: Optional[RegNum]= None,
        n_sample_nm: Optional[int]= None,
        **kwargs,
    ):
        """Helper method to add a new Component to the component list."""
        params = {
            "n_amount": n_amount,
            "n_comp_index": n_comp_index,
            "reg_num": reg_num,
            "n_sample_nm": n_sample_nm
        }

        self.component.append(
            Component(**params)
        )

        return self.component[-1]
    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Component(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Component information for multicomponent substances.
    """
    n_amount: Optional[float] = element(
        default= None,
        tag="n_amount",
        description="""Amount of component""",
        json_schema_extra=dict(),
    )
    n_comp_index: Optional[int] = element(
        default= None,
        tag="n_comp_index",
        description="""Component index""",
        json_schema_extra=dict(),
    )
    reg_num: Optional[RegNum] = element(
        default= None,
        tag="reg_num",
        description="""Registration number""",
        json_schema_extra=dict(),
    )
    n_sample_nm: Optional[int] = element(
        default= None,
        tag="n_sample_nm",
        description="""Sample number""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Sample(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Sample information for compounds.
    """
    n_sample_nm: Optional[int] = element(
        default= None,
        tag="n_sample_nm",
        description="""Sample number""",
        json_schema_extra=dict(),
    )
    component_sample: list[ComponentSample] = element(
        default_factory=list,
        tag="component_sample",
        description="""Component sample information""",
        json_schema_extra=dict(),
    )
    e_source: Union[None,eSource,str] = element(
        default= None,
        tag="e_source",
        description="""Source of the sample""",
        json_schema_extra=dict(),
    )
    e_status: Union[None,eStatus,str] = element(
        default= None,
        tag="e_status",
        description="""Status of the sample""",
        json_schema_extra=dict(),
    )
    purity: list[Purity] = element(
        default_factory=list,
        tag="purity",
        description="""Purity of the sample""",
        json_schema_extra=dict(),
    )


    def add_to_component_sample(
        self,
        n_comp_index: Optional[int]= None,
        n_sample_nm: Optional[int]= None,
        reg_num: Optional[RegNum]= None,
        **kwargs,
    ):
        """Helper method to add a new ComponentSample to the component_sample list."""
        params = {
            "n_comp_index": n_comp_index,
            "n_sample_nm": n_sample_nm,
            "reg_num": reg_num
        }

        self.component_sample.append(
            ComponentSample(**params)
        )

        return self.component_sample[-1]

    def add_to_purity(
        self,
        n_halide_mass_per_cent: Optional[float]= None,
        n_halide_mass_per_cent_digits: Optional[int]= None,
        n_halide_mol_per_cent: Optional[float]= None,
        n_halide_mol_per_cent_digits: Optional[int]= None,
        n_purity_mass: Optional[float]= None,
        n_purity_mass_digits: Optional[int]= None,
        n_purity_mol: Optional[float]= None,
        n_purity_mol_digits: Optional[int]= None,
        n_purity_vol: Optional[float]= None,
        n_purity_vol_digits: Optional[int]= None,
        n_step: Optional[int]= None,
        n_unknown_per_cent: Optional[float]= None,
        n_unknown_per_cent_digits: Optional[int]= None,
        n_water_mass_per_cent: Optional[float]= None,
        n_water_mass_per_cent_digits: Optional[int]= None,
        n_water_mol_per_cent: Optional[float]= None,
        n_water_mol_per_cent_digits: Optional[int]= None,
        e_anal_meth: list[eAnalMeth]= [],
        e_purif_method: list[ePurifMethod]= [],
        s_anal_meth: list[str]= [],
        s_purif_method: list[str]= [],
        **kwargs,
    ):
        """Helper method to add a new Purity to the purity list."""
        params = {
            "n_halide_mass_per_cent": n_halide_mass_per_cent,
            "n_halide_mass_per_cent_digits": n_halide_mass_per_cent_digits,
            "n_halide_mol_per_cent": n_halide_mol_per_cent,
            "n_halide_mol_per_cent_digits": n_halide_mol_per_cent_digits,
            "n_purity_mass": n_purity_mass,
            "n_purity_mass_digits": n_purity_mass_digits,
            "n_purity_mol": n_purity_mol,
            "n_purity_mol_digits": n_purity_mol_digits,
            "n_purity_vol": n_purity_vol,
            "n_purity_vol_digits": n_purity_vol_digits,
            "n_step": n_step,
            "n_unknown_per_cent": n_unknown_per_cent,
            "n_unknown_per_cent_digits": n_unknown_per_cent_digits,
            "n_water_mass_per_cent": n_water_mass_per_cent,
            "n_water_mass_per_cent_digits": n_water_mass_per_cent_digits,
            "n_water_mol_per_cent": n_water_mol_per_cent,
            "n_water_mol_per_cent_digits": n_water_mol_per_cent_digits,
            "e_anal_meth": e_anal_meth,
            "e_purif_method": e_purif_method,
            "s_anal_meth": s_anal_meth,
            "s_purif_method": s_purif_method
        }

        self.purity.append(
            Purity(**params)
        )

        return self.purity[-1]
    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class ComponentSample(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Component sample information.
    """
    n_comp_index: Optional[int] = element(
        default= None,
        tag="n_comp_index",
        description="""Component index""",
        json_schema_extra=dict(),
    )
    n_sample_nm: Optional[int] = element(
        default= None,
        tag="n_sample_nm",
        description="""Sample number""",
        json_schema_extra=dict(),
    )
    reg_num: Optional[RegNum] = element(
        default= None,
        tag="reg_num",
        description="""Registration number""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Purity(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Purity information for samples.
    """
    n_halide_mass_per_cent: Optional[float] = element(
        default= None,
        tag="n_halide_mass_per_cent",
        description="""Mass per cent of halide impurity""",
        json_schema_extra=dict(),
    )
    n_halide_mass_per_cent_digits: Optional[int] = element(
        default= None,
        tag="n_halide_mass_per_cent_digits",
        description="""Digits for halide mass per cent""",
        json_schema_extra=dict(),
    )
    n_halide_mol_per_cent: Optional[float] = element(
        default= None,
        tag="n_halide_mol_per_cent",
        description="""Mole per cent of halide impurity""",
        json_schema_extra=dict(),
    )
    n_halide_mol_per_cent_digits: Optional[int] = element(
        default= None,
        tag="n_halide_mol_per_cent_digits",
        description="""Digits for halide mole per cent""",
        json_schema_extra=dict(),
    )
    n_purity_mass: Optional[float] = element(
        default= None,
        tag="n_purity_mass",
        description="""Purity value in mass percent""",
        json_schema_extra=dict(),
    )
    n_purity_mass_digits: Optional[int] = element(
        default= None,
        tag="n_purity_mass_digits",
        description="""Digits for purity mass""",
        json_schema_extra=dict(),
    )
    n_purity_mol: Optional[float] = element(
        default= None,
        tag="n_purity_mol",
        description="""Purity value in mole percent""",
        json_schema_extra=dict(),
    )
    n_purity_mol_digits: Optional[int] = element(
        default= None,
        tag="n_purity_mol_digits",
        description="""Digits for purity mole""",
        json_schema_extra=dict(),
    )
    n_purity_vol: Optional[float] = element(
        default= None,
        tag="n_purity_vol",
        description="""Purity value in volume percent""",
        json_schema_extra=dict(),
    )
    n_purity_vol_digits: Optional[int] = element(
        default= None,
        tag="n_purity_vol_digits",
        description="""Digits for purity volume""",
        json_schema_extra=dict(),
    )
    n_step: Optional[int] = element(
        default= None,
        tag="n_step",
        description="""Step number""",
        json_schema_extra=dict(),
    )
    n_unknown_per_cent: Optional[float] = element(
        default= None,
        tag="n_unknown_per_cent",
        description="""Purity value in not specified percent""",
        json_schema_extra=dict(),
    )
    n_unknown_per_cent_digits: Optional[int] = element(
        default= None,
        tag="n_unknown_per_cent_digits",
        description="""Digits for unknown per cent""",
        json_schema_extra=dict(),
    )
    n_water_mass_per_cent: Optional[float] = element(
        default= None,
        tag="n_water_mass_per_cent",
        description="""Mass per cent of water""",
        json_schema_extra=dict(),
    )
    n_water_mass_per_cent_digits: Optional[int] = element(
        default= None,
        tag="n_water_mass_per_cent_digits",
        description="""Digits for water mass per cent""",
        json_schema_extra=dict(),
    )
    n_water_mol_per_cent: Optional[float] = element(
        default= None,
        tag="n_water_mol_per_cent",
        description="""Mole per cent of water""",
        json_schema_extra=dict(),
    )
    n_water_mol_per_cent_digits: Optional[int] = element(
        default= None,
        tag="n_water_mol_per_cent_digits",
        description="""Digits for water mole per cent""",
        json_schema_extra=dict(),
    )
    e_anal_meth: list[eAnalMeth] = element(
        default_factory=list,
        tag="e_anal_meth",
        description="""Analytical method used to determine purity""",
        json_schema_extra=dict(),
    )
    e_purif_method: list[ePurifMethod] = element(
        default_factory=list,
        tag="e_purif_method",
        description="""Purification method""",
        json_schema_extra=dict(),
    )
    s_anal_meth: list[str] = element(
        default_factory=list,
        tag="s_anal_meth",
        description="""Analytical method description""",
        json_schema_extra=dict(),
    )
    s_purif_method: list[str] = element(
        default_factory=list,
        tag="s_purif_method",
        description="""Purification method description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class PureOrMixtureData(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Data for pure substances or mixtures.
    """
    component: list[Component] = element(
        default_factory=list,
        tag="component",
        description="""List of components""",
        json_schema_extra=dict(),
    )
    phase_id: list[PhaseID] = element(
        default_factory=list,
        tag="phase_id",
        description="""Phase identification information""",
        json_schema_extra=dict(),
    )
    property: list[Property] = element(
        default_factory=list,
        tag="property",
        description="""List of properties""",
        json_schema_extra=dict(),
    )
    auxiliary_substance: list[AuxiliarySubstance] = element(
        default_factory=list,
        tag="auxiliary_substance",
        description="""Auxiliary substance information""",
        json_schema_extra=dict(),
    )
    constraint: list[Constraint] = element(
        default_factory=list,
        tag="constraint",
        description="""Constraint information""",
        json_schema_extra=dict(),
    )
    date_date_added: Optional[str] = element(
        default= None,
        tag="date_date_added",
        description="""Date when data was added""",
        json_schema_extra=dict(),
    )
    e_exp_purpose: Union[None,eExpPurpose,str] = element(
        default= None,
        tag="e_exp_purpose",
        description="""Purpose of measurement""",
        json_schema_extra=dict(),
    )
    equation: list[Equation] = element(
        default_factory=list,
        tag="equation",
        description="""Equation information""",
        json_schema_extra=dict(),
    )
    n_pure_or_mixture_data_number: Optional[int] = element(
        default= None,
        tag="n_pure_or_mixture_data_number",
        description="""Data number""",
        json_schema_extra=dict(),
    )
    num_values: list[NumValues] = element(
        default_factory=list,
        tag="num_values",
        description="""Numerical values""",
        json_schema_extra=dict(),
    )
    s_compiler: Optional[str] = element(
        default= None,
        tag="s_compiler",
        description="""Compiler information""",
        json_schema_extra=dict(),
    )
    s_contributor: Optional[str] = element(
        default= None,
        tag="s_contributor",
        description="""Contributor information""",
        json_schema_extra=dict(),
    )
    variable: list[Variable] = element(
        default_factory=list,
        tag="variable",
        description="""Variable information""",
        json_schema_extra=dict(),
    )


    def add_to_component(
        self,
        n_amount: Optional[float]= None,
        n_comp_index: Optional[int]= None,
        reg_num: Optional[RegNum]= None,
        n_sample_nm: Optional[int]= None,
        **kwargs,
    ):
        """Helper method to add a new Component to the component list."""
        params = {
            "n_amount": n_amount,
            "n_comp_index": n_comp_index,
            "reg_num": reg_num,
            "n_sample_nm": n_sample_nm
        }

        self.component.append(
            Component(**params)
        )

        return self.component[-1]

    def add_to_phase_id(
        self,
        e_crystal_lattice_type: Union[None,eCrystalLatticeType,str]= None,
        e_phase: Union[None,ePhase,str]= None,
        n_comp_index: Optional[int]= None,
        reg_num: Optional[RegNum]= None,
        s_phase_description: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new PhaseID to the phase_id list."""
        params = {
            "e_crystal_lattice_type": e_crystal_lattice_type,
            "e_phase": e_phase,
            "n_comp_index": n_comp_index,
            "reg_num": reg_num,
            "s_phase_description": s_phase_description
        }

        self.phase_id.append(
            PhaseID(**params)
        )

        return self.phase_id[-1]

    def add_to_property(
        self,
        e_presentation: Union[None,ePresentation,str]= None,
        n_pressure_digits: Optional[int]= None,
        n_pressure_pa: Optional[float]= None,
        n_prop_number: Optional[int]= None,
        n_ref_pressure: Optional[float]= None,
        n_ref_pressure_digits: Optional[int]= None,
        n_ref_temp: Optional[float]= None,
        n_ref_temp_digits: Optional[int]= None,
        n_temperature_digits: Optional[int]= None,
        n_temperature_k: Optional[float]= None,
        property_method_id: Optional[PropertyMethodID]= None,
        catalyst: list[Catalyst]= [],
        combined_uncertainty: list[CombinedUncertainty]= [],
        curve_dev: list[CurveDev]= [],
        e_ref_state_type: Union[None,eRefStateType,str]= None,
        e_standard_state: Union[None,eStandardState,str]= None,
        prop_device_spec: Optional[PropDeviceSpec]= None,
        prop_phase_id: list[PropPhaseID]= [],
        prop_repeatability: Optional[PropRepeatability]= None,
        prop_uncertainty: list[PropUncertainty]= [],
        ref_phase_id: Optional[RefPhaseID]= None,
        solvent: Optional[Solvent]= None,
        **kwargs,
    ):
        """Helper method to add a new Property to the property list."""
        params = {
            "e_presentation": e_presentation,
            "n_pressure_digits": n_pressure_digits,
            "n_pressure_pa": n_pressure_pa,
            "n_prop_number": n_prop_number,
            "n_ref_pressure": n_ref_pressure,
            "n_ref_pressure_digits": n_ref_pressure_digits,
            "n_ref_temp": n_ref_temp,
            "n_ref_temp_digits": n_ref_temp_digits,
            "n_temperature_digits": n_temperature_digits,
            "n_temperature_k": n_temperature_k,
            "property_method_id": property_method_id,
            "catalyst": catalyst,
            "combined_uncertainty": combined_uncertainty,
            "curve_dev": curve_dev,
            "e_ref_state_type": e_ref_state_type,
            "e_standard_state": e_standard_state,
            "prop_device_spec": prop_device_spec,
            "prop_phase_id": prop_phase_id,
            "prop_repeatability": prop_repeatability,
            "prop_uncertainty": prop_uncertainty,
            "ref_phase_id": ref_phase_id,
            "solvent": solvent
        }

        self.property.append(
            Property(**params)
        )

        return self.property[-1]

    def add_to_auxiliary_substance(
        self,
        e_function: Union[None,eFunction,str]= None,
        n_comp_index: Optional[int]= None,
        reg_num: Optional[RegNum]= None,
        s_function: Optional[str]= None,
        e_phase: Union[None,ePhase,str]= None,
        n_sample_nm: Optional[int]= None,
        **kwargs,
    ):
        """Helper method to add a new AuxiliarySubstance to the auxiliary_substance list."""
        params = {
            "e_function": e_function,
            "n_comp_index": n_comp_index,
            "reg_num": reg_num,
            "s_function": s_function,
            "e_phase": e_phase,
            "n_sample_nm": n_sample_nm
        }

        self.auxiliary_substance.append(
            AuxiliarySubstance(**params)
        )

        return self.auxiliary_substance[-1]

    def add_to_constraint(
        self,
        constraint_id: Optional[ConstraintID]= None,
        n_constr_digits: Optional[int]= None,
        n_constraint_value: Optional[float]= None,
        constr_device_spec: Optional[ConstrDeviceSpec]= None,
        constr_repeatability: Optional[ConstrRepeatability]= None,
        constr_uncertainty: list[ConstrUncertainty]= [],
        constraint_phase_id: Optional[ConstraintPhaseID]= None,
        n_constraint_number: Optional[int]= None,
        solvent: Optional[Solvent]= None,
        **kwargs,
    ):
        """Helper method to add a new Constraint to the constraint list."""
        params = {
            "constraint_id": constraint_id,
            "n_constr_digits": n_constr_digits,
            "n_constraint_value": n_constraint_value,
            "constr_device_spec": constr_device_spec,
            "constr_repeatability": constr_repeatability,
            "constr_uncertainty": constr_uncertainty,
            "constraint_phase_id": constraint_phase_id,
            "n_constraint_number": n_constraint_number,
            "solvent": solvent
        }

        self.constraint.append(
            Constraint(**params)
        )

        return self.constraint[-1]

    def add_to_equation(
        self,
        e_eq_name: Union[None,eEqName,str]= None,
        s_eq_name: Optional[str]= None,
        url_math_source: Optional[str]= None,
        covariance: list[Covariance]= [],
        eq_constant: list[EqConstant]= [],
        eq_constraint: list[EqConstraint]= [],
        eq_parameter: list[EqParameter]= [],
        eq_property: list[EqProperty]= [],
        eq_variable: list[EqVariable]= [],
        n_covariance_lev_of_confid: Optional[float]= None,
        **kwargs,
    ):
        """Helper method to add a new Equation to the equation list."""
        params = {
            "e_eq_name": e_eq_name,
            "s_eq_name": s_eq_name,
            "url_math_source": url_math_source,
            "covariance": covariance,
            "eq_constant": eq_constant,
            "eq_constraint": eq_constraint,
            "eq_parameter": eq_parameter,
            "eq_property": eq_property,
            "eq_variable": eq_variable,
            "n_covariance_lev_of_confid": n_covariance_lev_of_confid
        }

        self.equation.append(
            Equation(**params)
        )

        return self.equation[-1]

    def add_to_num_values(
        self,
        property_value: list[PropertyValue]= [],
        variable_value: list[VariableValue]= [],
        **kwargs,
    ):
        """Helper method to add a new NumValues to the num_values list."""
        params = {
            "property_value": property_value,
            "variable_value": variable_value
        }

        self.num_values.append(
            NumValues(**params)
        )

        return self.num_values[-1]

    def add_to_variable(
        self,
        n_var_number: Optional[int]= None,
        variable_id: Optional[VariableID]= None,
        solvent: Optional[Solvent]= None,
        var_device_spec: Optional[VarDeviceSpec]= None,
        var_phase_id: Optional[VarPhaseID]= None,
        var_repeatability: Optional[VarRepeatability]= None,
        var_uncertainty: list[VarUncertainty]= [],
        **kwargs,
    ):
        """Helper method to add a new Variable to the variable list."""
        params = {
            "n_var_number": n_var_number,
            "variable_id": variable_id,
            "solvent": solvent,
            "var_device_spec": var_device_spec,
            "var_phase_id": var_phase_id,
            "var_repeatability": var_repeatability,
            "var_uncertainty": var_uncertainty
        }

        self.variable.append(
            Variable(**params)
        )

        return self.variable[-1]
    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class AuxiliarySubstance(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Auxiliary substance information.
    """
    e_function: Union[None,eFunction,str] = element(
        default= None,
        tag="e_function",
        description="""Function of the substance""",
        json_schema_extra=dict(),
    )
    n_comp_index: Optional[int] = element(
        default= None,
        tag="n_comp_index",
        description="""Component index""",
        json_schema_extra=dict(),
    )
    reg_num: Optional[RegNum] = element(
        default= None,
        tag="reg_num",
        description="""Registration number""",
        json_schema_extra=dict(),
    )
    s_function: Optional[str] = element(
        default= None,
        tag="s_function",
        description="""Function description""",
        json_schema_extra=dict(),
    )
    e_phase: Union[None,ePhase,str] = element(
        default= None,
        tag="e_phase",
        description="""Phase information""",
        json_schema_extra=dict(),
    )
    n_sample_nm: Optional[int] = element(
        default= None,
        tag="n_sample_nm",
        description="""Sample number""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Property(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Property information for measurements.
    """
    e_presentation: Union[None,ePresentation,str] = element(
        default= None,
        tag="e_presentation",
        description="""Presentation method""",
        json_schema_extra=dict(),
    )
    n_pressure_digits: Optional[int] = element(
        default= None,
        tag="n_pressure_digits",
        description="""Pressure digits""",
        json_schema_extra=dict(),
    )
    n_pressure_pa: Optional[float] = element(
        default= None,
        tag="n_pressure_pa",
        description="""Pressure in kPa""",
        json_schema_extra=dict(),
    )
    n_prop_number: Optional[int] = element(
        default= None,
        tag="n_prop_number",
        description="""Property number""",
        json_schema_extra=dict(),
    )
    n_ref_pressure: Optional[float] = element(
        default= None,
        tag="n_ref_pressure",
        description="""Reference pressure""",
        json_schema_extra=dict(),
    )
    n_ref_pressure_digits: Optional[int] = element(
        default= None,
        tag="n_ref_pressure_digits",
        description="""Reference pressure digits""",
        json_schema_extra=dict(),
    )
    n_ref_temp: Optional[float] = element(
        default= None,
        tag="n_ref_temp",
        description="""Reference temperature""",
        json_schema_extra=dict(),
    )
    n_ref_temp_digits: Optional[int] = element(
        default= None,
        tag="n_ref_temp_digits",
        description="""Reference temperature digits""",
        json_schema_extra=dict(),
    )
    n_temperature_digits: Optional[int] = element(
        default= None,
        tag="n_temperature_digits",
        description="""Temperature digits""",
        json_schema_extra=dict(),
    )
    n_temperature_k: Optional[float] = element(
        default= None,
        tag="n_temperature_k",
        description="""Temperature in K""",
        json_schema_extra=dict(),
    )
    property_method_id: Optional[PropertyMethodID] = element(
        default= None,
        tag="property_method_id",
        description="""Property method identification""",
        json_schema_extra=dict(),
    )
    catalyst: list[Catalyst] = element(
        default_factory=list,
        tag="catalyst",
        description="""Catalyst information""",
        json_schema_extra=dict(),
    )
    combined_uncertainty: list[CombinedUncertainty] = element(
        default_factory=list,
        tag="combined_uncertainty",
        description="""Combined uncertainty information""",
        json_schema_extra=dict(),
    )
    curve_dev: list[CurveDev] = element(
        default_factory=list,
        tag="curve_dev",
        description="""Curve deviation information""",
        json_schema_extra=dict(),
    )
    e_ref_state_type: Union[None,eRefStateType,str] = element(
        default= None,
        tag="e_ref_state_type",
        description="""Reference state type""",
        json_schema_extra=dict(),
    )
    e_standard_state: Union[None,eStandardState,str] = element(
        default= None,
        tag="e_standard_state",
        description="""Standard state""",
        json_schema_extra=dict(),
    )
    prop_device_spec: Optional[PropDeviceSpec] = element(
        default= None,
        tag="prop_device_spec",
        description="""Property device specification""",
        json_schema_extra=dict(),
    )
    prop_phase_id: list[PropPhaseID] = element(
        default_factory=list,
        tag="prop_phase_id",
        description="""Property phase identification""",
        json_schema_extra=dict(),
    )
    prop_repeatability: Optional[PropRepeatability] = element(
        default= None,
        tag="prop_repeatability",
        description="""Property repeatability""",
        json_schema_extra=dict(),
    )
    prop_uncertainty: list[PropUncertainty] = element(
        default_factory=list,
        tag="prop_uncertainty",
        description="""Property uncertainty""",
        json_schema_extra=dict(),
    )
    ref_phase_id: Optional[RefPhaseID] = element(
        default= None,
        tag="ref_phase_id",
        description="""Reference phase identification""",
        json_schema_extra=dict(),
    )
    solvent: Optional[Solvent] = element(
        default= None,
        tag="solvent",
        description="""Solvent information""",
        json_schema_extra=dict(),
    )


    def add_to_catalyst(
        self,
        n_comp_index: Optional[int]= None,
        reg_num: Optional[RegNum]= None,
        e_phase: Union[None,ePhase,str]= None,
        **kwargs,
    ):
        """Helper method to add a new Catalyst to the catalyst list."""
        params = {
            "n_comp_index": n_comp_index,
            "reg_num": reg_num,
            "e_phase": e_phase
        }

        self.catalyst.append(
            Catalyst(**params)
        )

        return self.catalyst[-1]

    def add_to_combined_uncertainty(
        self,
        e_comb_uncert_eval_method: Union[None,eCombUncertEvalMethod,str]= None,
        n_comb_uncert_assess_num: Optional[int]= None,
        asym_comb_expand_uncert: Optional[AsymCombExpandUncert]= None,
        asym_comb_std_uncert: Optional[AsymCombStdUncert]= None,
        n_comb_coverage_factor: Optional[float]= None,
        n_comb_expand_uncert_value: Optional[float]= None,
        n_comb_std_uncert_value: Optional[float]= None,
        n_comb_uncert_lev_of_confid: Optional[float]= None,
        s_comb_uncert_eval_method: Optional[str]= None,
        s_comb_uncert_evaluator: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new CombinedUncertainty to the combined_uncertainty list."""
        params = {
            "e_comb_uncert_eval_method": e_comb_uncert_eval_method,
            "n_comb_uncert_assess_num": n_comb_uncert_assess_num,
            "asym_comb_expand_uncert": asym_comb_expand_uncert,
            "asym_comb_std_uncert": asym_comb_std_uncert,
            "n_comb_coverage_factor": n_comb_coverage_factor,
            "n_comb_expand_uncert_value": n_comb_expand_uncert_value,
            "n_comb_std_uncert_value": n_comb_std_uncert_value,
            "n_comb_uncert_lev_of_confid": n_comb_uncert_lev_of_confid,
            "s_comb_uncert_eval_method": s_comb_uncert_eval_method,
            "s_comb_uncert_evaluator": s_comb_uncert_evaluator
        }

        self.combined_uncertainty.append(
            CombinedUncertainty(**params)
        )

        return self.combined_uncertainty[-1]

    def add_to_curve_dev(
        self,
        n_curve_dev_assess_num: Optional[int]= None,
        n_curve_dev_value: Optional[float]= None,
        s_curve_spec: Optional[str]= None,
        n_curve_rms_dev_value: Optional[float]= None,
        n_curve_rms_relative_dev_value: Optional[float]= None,
        s_curve_dev_evaluator: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new CurveDev to the curve_dev list."""
        params = {
            "n_curve_dev_assess_num": n_curve_dev_assess_num,
            "n_curve_dev_value": n_curve_dev_value,
            "s_curve_spec": s_curve_spec,
            "n_curve_rms_dev_value": n_curve_rms_dev_value,
            "n_curve_rms_relative_dev_value": n_curve_rms_relative_dev_value,
            "s_curve_dev_evaluator": s_curve_dev_evaluator
        }

        self.curve_dev.append(
            CurveDev(**params)
        )

        return self.curve_dev[-1]

    def add_to_prop_phase_id(
        self,
        e_bio_state: Union[None,eBioState,str]= None,
        e_crystal_lattice_type: Union[None,eCrystalLatticeType,str]= None,
        e_prop_phase: Union[None,ePropPhase,str]= None,
        n_comp_index: Optional[int]= None,
        reg_num: Optional[RegNum]= None,
        s_bio_state: Optional[str]= None,
        s_phase_description: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new PropPhaseID to the prop_phase_id list."""
        params = {
            "e_bio_state": e_bio_state,
            "e_crystal_lattice_type": e_crystal_lattice_type,
            "e_prop_phase": e_prop_phase,
            "n_comp_index": n_comp_index,
            "reg_num": reg_num,
            "s_bio_state": s_bio_state,
            "s_phase_description": s_phase_description
        }

        self.prop_phase_id.append(
            PropPhaseID(**params)
        )

        return self.prop_phase_id[-1]

    def add_to_prop_uncertainty(
        self,
        n_uncert_assess_num: Optional[int]= None,
        asym_expand_uncert: Optional[AsymExpandUncert]= None,
        asym_std_uncert: Optional[AsymStdUncert]= None,
        n_coverage_factor: Optional[float]= None,
        n_expand_uncert_value: Optional[float]= None,
        n_std_uncert_value: Optional[float]= None,
        n_uncert_lev_of_confid: Optional[float]= None,
        s_uncert_eval_method: Optional[str]= None,
        s_uncert_evaluator: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new PropUncertainty to the prop_uncertainty list."""
        params = {
            "n_uncert_assess_num": n_uncert_assess_num,
            "asym_expand_uncert": asym_expand_uncert,
            "asym_std_uncert": asym_std_uncert,
            "n_coverage_factor": n_coverage_factor,
            "n_expand_uncert_value": n_expand_uncert_value,
            "n_std_uncert_value": n_std_uncert_value,
            "n_uncert_lev_of_confid": n_uncert_lev_of_confid,
            "s_uncert_eval_method": s_uncert_eval_method,
            "s_uncert_evaluator": s_uncert_evaluator
        }

        self.prop_uncertainty.append(
            PropUncertainty(**params)
        )

        return self.prop_uncertainty[-1]
    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class ReactionData(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Data for chemical reactions.
    """
    e_reaction_type: Union[None,eReactionType,str] = element(
        default= None,
        tag="e_reaction_type",
        description="""Type of reaction""",
        json_schema_extra=dict(),
    )
    participant: list[Participant] = element(
        default_factory=list,
        tag="participant",
        description="""Reaction participants""",
        json_schema_extra=dict(),
    )
    property: list[Property] = element(
        default_factory=list,
        tag="property",
        description="""Reaction properties""",
        json_schema_extra=dict(),
    )
    auxiliary_substance: list[AuxiliarySubstance] = element(
        default_factory=list,
        tag="auxiliary_substance",
        description="""Auxiliary substances""",
        json_schema_extra=dict(),
    )
    constraint: list[Constraint] = element(
        default_factory=list,
        tag="constraint",
        description="""Reaction constraints""",
        json_schema_extra=dict(),
    )
    date_date_added: Optional[str] = element(
        default= None,
        tag="date_date_added",
        description="""Date when data was added""",
        json_schema_extra=dict(),
    )
    e_exp_purpose: Union[None,eExpPurpose,str] = element(
        default= None,
        tag="e_exp_purpose",
        description="""Purpose of measurement""",
        json_schema_extra=dict(),
    )
    e_reaction_formalism: Union[None,eReactionFormalism,str] = element(
        default= None,
        tag="e_reaction_formalism",
        description="""Reaction formalism""",
        json_schema_extra=dict(),
    )
    equation: list[Equation] = element(
        default_factory=list,
        tag="equation",
        description="""Reaction equations""",
        json_schema_extra=dict(),
    )
    n_electron_number: Optional[int] = element(
        default= None,
        tag="n_electron_number",
        description="""Number of electrons""",
        json_schema_extra=dict(),
    )
    n_reaction_data_number: Optional[int] = element(
        default= None,
        tag="n_reaction_data_number",
        description="""Reaction data number""",
        json_schema_extra=dict(),
    )
    num_values: list[NumValues] = element(
        default_factory=list,
        tag="num_values",
        description="""Numerical values""",
        json_schema_extra=dict(),
    )
    s_compiler: Optional[str] = element(
        default= None,
        tag="s_compiler",
        description="""Compiler information""",
        json_schema_extra=dict(),
    )
    s_contributor: Optional[str] = element(
        default= None,
        tag="s_contributor",
        description="""Contributor information""",
        json_schema_extra=dict(),
    )
    solvent: list[Solvent] = element(
        default_factory=list,
        tag="solvent",
        description="""Solvent information""",
        json_schema_extra=dict(),
    )
    variable: list[Variable] = element(
        default_factory=list,
        tag="variable",
        description="""Variable information""",
        json_schema_extra=dict(),
    )


    def add_to_participant(
        self,
        e_crystal_lattice_type: Union[None,eCrystalLatticeType,str]= None,
        e_phase: Union[None,ePhase,str]= None,
        n_comp_index: Optional[int]= None,
        reg_num: Optional[RegNum]= None,
        s_phase_description: Optional[str]= None,
        e_composition_representation: Union[None,eCompositionRepresentation,str]= None,
        e_standard_state: Union[None,eStandardState,str]= None,
        n_numerical_composition: Optional[float]= None,
        n_sample_nm: Optional[int]= None,
        n_stoichiometric_coef: Optional[float]= None,
        **kwargs,
    ):
        """Helper method to add a new Participant to the participant list."""
        params = {
            "e_crystal_lattice_type": e_crystal_lattice_type,
            "e_phase": e_phase,
            "n_comp_index": n_comp_index,
            "reg_num": reg_num,
            "s_phase_description": s_phase_description,
            "e_composition_representation": e_composition_representation,
            "e_standard_state": e_standard_state,
            "n_numerical_composition": n_numerical_composition,
            "n_sample_nm": n_sample_nm,
            "n_stoichiometric_coef": n_stoichiometric_coef
        }

        self.participant.append(
            Participant(**params)
        )

        return self.participant[-1]

    def add_to_property(
        self,
        e_presentation: Union[None,ePresentation,str]= None,
        n_pressure_digits: Optional[int]= None,
        n_pressure_pa: Optional[float]= None,
        n_prop_number: Optional[int]= None,
        n_ref_pressure: Optional[float]= None,
        n_ref_pressure_digits: Optional[int]= None,
        n_ref_temp: Optional[float]= None,
        n_ref_temp_digits: Optional[int]= None,
        n_temperature_digits: Optional[int]= None,
        n_temperature_k: Optional[float]= None,
        property_method_id: Optional[PropertyMethodID]= None,
        catalyst: list[Catalyst]= [],
        combined_uncertainty: list[CombinedUncertainty]= [],
        curve_dev: list[CurveDev]= [],
        e_ref_state_type: Union[None,eRefStateType,str]= None,
        e_standard_state: Union[None,eStandardState,str]= None,
        prop_device_spec: Optional[PropDeviceSpec]= None,
        prop_phase_id: list[PropPhaseID]= [],
        prop_repeatability: Optional[PropRepeatability]= None,
        prop_uncertainty: list[PropUncertainty]= [],
        ref_phase_id: Optional[RefPhaseID]= None,
        solvent: Optional[Solvent]= None,
        **kwargs,
    ):
        """Helper method to add a new Property to the property list."""
        params = {
            "e_presentation": e_presentation,
            "n_pressure_digits": n_pressure_digits,
            "n_pressure_pa": n_pressure_pa,
            "n_prop_number": n_prop_number,
            "n_ref_pressure": n_ref_pressure,
            "n_ref_pressure_digits": n_ref_pressure_digits,
            "n_ref_temp": n_ref_temp,
            "n_ref_temp_digits": n_ref_temp_digits,
            "n_temperature_digits": n_temperature_digits,
            "n_temperature_k": n_temperature_k,
            "property_method_id": property_method_id,
            "catalyst": catalyst,
            "combined_uncertainty": combined_uncertainty,
            "curve_dev": curve_dev,
            "e_ref_state_type": e_ref_state_type,
            "e_standard_state": e_standard_state,
            "prop_device_spec": prop_device_spec,
            "prop_phase_id": prop_phase_id,
            "prop_repeatability": prop_repeatability,
            "prop_uncertainty": prop_uncertainty,
            "ref_phase_id": ref_phase_id,
            "solvent": solvent
        }

        self.property.append(
            Property(**params)
        )

        return self.property[-1]

    def add_to_auxiliary_substance(
        self,
        e_function: Union[None,eFunction,str]= None,
        n_comp_index: Optional[int]= None,
        reg_num: Optional[RegNum]= None,
        s_function: Optional[str]= None,
        e_phase: Union[None,ePhase,str]= None,
        n_sample_nm: Optional[int]= None,
        **kwargs,
    ):
        """Helper method to add a new AuxiliarySubstance to the auxiliary_substance list."""
        params = {
            "e_function": e_function,
            "n_comp_index": n_comp_index,
            "reg_num": reg_num,
            "s_function": s_function,
            "e_phase": e_phase,
            "n_sample_nm": n_sample_nm
        }

        self.auxiliary_substance.append(
            AuxiliarySubstance(**params)
        )

        return self.auxiliary_substance[-1]

    def add_to_constraint(
        self,
        constraint_id: Optional[ConstraintID]= None,
        n_constr_digits: Optional[int]= None,
        n_constraint_value: Optional[float]= None,
        constr_device_spec: Optional[ConstrDeviceSpec]= None,
        constr_repeatability: Optional[ConstrRepeatability]= None,
        constr_uncertainty: list[ConstrUncertainty]= [],
        constraint_phase_id: Optional[ConstraintPhaseID]= None,
        n_constraint_number: Optional[int]= None,
        solvent: Optional[Solvent]= None,
        **kwargs,
    ):
        """Helper method to add a new Constraint to the constraint list."""
        params = {
            "constraint_id": constraint_id,
            "n_constr_digits": n_constr_digits,
            "n_constraint_value": n_constraint_value,
            "constr_device_spec": constr_device_spec,
            "constr_repeatability": constr_repeatability,
            "constr_uncertainty": constr_uncertainty,
            "constraint_phase_id": constraint_phase_id,
            "n_constraint_number": n_constraint_number,
            "solvent": solvent
        }

        self.constraint.append(
            Constraint(**params)
        )

        return self.constraint[-1]

    def add_to_equation(
        self,
        e_eq_name: Union[None,eEqName,str]= None,
        s_eq_name: Optional[str]= None,
        url_math_source: Optional[str]= None,
        covariance: list[Covariance]= [],
        eq_constant: list[EqConstant]= [],
        eq_constraint: list[EqConstraint]= [],
        eq_parameter: list[EqParameter]= [],
        eq_property: list[EqProperty]= [],
        eq_variable: list[EqVariable]= [],
        n_covariance_lev_of_confid: Optional[float]= None,
        **kwargs,
    ):
        """Helper method to add a new Equation to the equation list."""
        params = {
            "e_eq_name": e_eq_name,
            "s_eq_name": s_eq_name,
            "url_math_source": url_math_source,
            "covariance": covariance,
            "eq_constant": eq_constant,
            "eq_constraint": eq_constraint,
            "eq_parameter": eq_parameter,
            "eq_property": eq_property,
            "eq_variable": eq_variable,
            "n_covariance_lev_of_confid": n_covariance_lev_of_confid
        }

        self.equation.append(
            Equation(**params)
        )

        return self.equation[-1]

    def add_to_num_values(
        self,
        property_value: list[PropertyValue]= [],
        variable_value: list[VariableValue]= [],
        **kwargs,
    ):
        """Helper method to add a new NumValues to the num_values list."""
        params = {
            "property_value": property_value,
            "variable_value": variable_value
        }

        self.num_values.append(
            NumValues(**params)
        )

        return self.num_values[-1]

    def add_to_solvent(
        self,
        e_phase: Union[None,ePhase,str]= None,
        n_comp_index: Optional[int]= None,
        reg_num: Optional[RegNum]= None,
        **kwargs,
    ):
        """Helper method to add a new Solvent to the solvent list."""
        params = {
            "e_phase": e_phase,
            "n_comp_index": n_comp_index,
            "reg_num": reg_num
        }

        self.solvent.append(
            Solvent(**params)
        )

        return self.solvent[-1]

    def add_to_variable(
        self,
        n_var_number: Optional[int]= None,
        variable_id: Optional[VariableID]= None,
        solvent: Optional[Solvent]= None,
        var_device_spec: Optional[VarDeviceSpec]= None,
        var_phase_id: Optional[VarPhaseID]= None,
        var_repeatability: Optional[VarRepeatability]= None,
        var_uncertainty: list[VarUncertainty]= [],
        **kwargs,
    ):
        """Helper method to add a new Variable to the variable list."""
        params = {
            "n_var_number": n_var_number,
            "variable_id": variable_id,
            "solvent": solvent,
            "var_device_spec": var_device_spec,
            "var_phase_id": var_phase_id,
            "var_repeatability": var_repeatability,
            "var_uncertainty": var_uncertainty
        }

        self.variable.append(
            Variable(**params)
        )

        return self.variable[-1]
    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Participant(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Reaction participant information.
    """
    e_crystal_lattice_type: Union[None,eCrystalLatticeType,str] = element(
        default= None,
        tag="e_crystal_lattice_type",
        description="""Crystal lattice type""",
        json_schema_extra=dict(),
    )
    e_phase: Union[None,ePhase,str] = element(
        default= None,
        tag="e_phase",
        description="""Phase information""",
        json_schema_extra=dict(),
    )
    n_comp_index: Optional[int] = element(
        default= None,
        tag="n_comp_index",
        description="""Component index""",
        json_schema_extra=dict(),
    )
    reg_num: Optional[RegNum] = element(
        default= None,
        tag="reg_num",
        description="""Registration number""",
        json_schema_extra=dict(),
    )
    s_phase_description: Optional[str] = element(
        default= None,
        tag="s_phase_description",
        description="""Phase description""",
        json_schema_extra=dict(),
    )
    e_composition_representation: Union[None,eCompositionRepresentation,str] = element(
        default= None,
        tag="e_composition_representation",
        description="""Composition representation""",
        json_schema_extra=dict(),
    )
    e_standard_state: Union[None,eStandardState,str] = element(
        default= None,
        tag="e_standard_state",
        description="""Standard state""",
        json_schema_extra=dict(),
    )
    n_numerical_composition: Optional[float] = element(
        default= None,
        tag="n_numerical_composition",
        description="""Numerical composition""",
        json_schema_extra=dict(),
    )
    n_sample_nm: Optional[int] = element(
        default= None,
        tag="n_sample_nm",
        description="""Sample number""",
        json_schema_extra=dict(),
    )
    n_stoichiometric_coef: Optional[float] = element(
        default= None,
        tag="n_stoichiometric_coef",
        description="""Stoichiometric coefficient""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Catalyst(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Catalyst information.
    """
    n_comp_index: Optional[int] = element(
        default= None,
        tag="n_comp_index",
        description="""Component index""",
        json_schema_extra=dict(),
    )
    reg_num: Optional[RegNum] = element(
        default= None,
        tag="reg_num",
        description="""Registration number""",
        json_schema_extra=dict(),
    )
    e_phase: Union[None,ePhase,str] = element(
        default= None,
        tag="e_phase",
        description="""Phase information""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class PhaseID(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Phase identification information.
    """
    e_crystal_lattice_type: Union[None,eCrystalLatticeType,str] = element(
        default= None,
        tag="e_crystal_lattice_type",
        description="""Crystal lattice type""",
        json_schema_extra=dict(),
    )
    e_phase: Union[None,ePhase,str] = element(
        default= None,
        tag="e_phase",
        description="""Phase information""",
        json_schema_extra=dict(),
    )
    n_comp_index: Optional[int] = element(
        default= None,
        tag="n_comp_index",
        description="""Component index""",
        json_schema_extra=dict(),
    )
    reg_num: Optional[RegNum] = element(
        default= None,
        tag="reg_num",
        description="""Registration number""",
        json_schema_extra=dict(),
    )
    s_phase_description: Optional[str] = element(
        default= None,
        tag="s_phase_description",
        description="""Phase description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Constraint(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Constraint information.
    """
    constraint_id: Optional[ConstraintID] = element(
        default= None,
        tag="constraint_id",
        description="""Constraint identification""",
        json_schema_extra=dict(),
    )
    n_constr_digits: Optional[int] = element(
        default= None,
        tag="n_constr_digits",
        description="""Constraint digits""",
        json_schema_extra=dict(),
    )
    n_constraint_value: Optional[float] = element(
        default= None,
        tag="n_constraint_value",
        description="""Constraint value""",
        json_schema_extra=dict(),
    )
    constr_device_spec: Optional[ConstrDeviceSpec] = element(
        default= None,
        tag="constr_device_spec",
        description="""Constraint device specification""",
        json_schema_extra=dict(),
    )
    constr_repeatability: Optional[ConstrRepeatability] = element(
        default= None,
        tag="constr_repeatability",
        description="""Constraint repeatability""",
        json_schema_extra=dict(),
    )
    constr_uncertainty: list[ConstrUncertainty] = element(
        default_factory=list,
        tag="constr_uncertainty",
        description="""Constraint uncertainty""",
        json_schema_extra=dict(),
    )
    constraint_phase_id: Optional[ConstraintPhaseID] = element(
        default= None,
        tag="constraint_phase_id",
        description="""Constraint phase identification""",
        json_schema_extra=dict(),
    )
    n_constraint_number: Optional[int] = element(
        default= None,
        tag="n_constraint_number",
        description="""Constraint number""",
        json_schema_extra=dict(),
    )
    solvent: Optional[Solvent] = element(
        default= None,
        tag="solvent",
        description="""Solvent information""",
        json_schema_extra=dict(),
    )


    def add_to_constr_uncertainty(
        self,
        n_coverage_factor: Optional[float]= None,
        n_expand_uncert_value: Optional[float]= None,
        n_std_uncert_value: Optional[float]= None,
        n_uncert_lev_of_confid: Optional[float]= None,
        s_uncert_eval_method: Optional[str]= None,
        s_uncert_evaluator: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new ConstrUncertainty to the constr_uncertainty list."""
        params = {
            "n_coverage_factor": n_coverage_factor,
            "n_expand_uncert_value": n_expand_uncert_value,
            "n_std_uncert_value": n_std_uncert_value,
            "n_uncert_lev_of_confid": n_uncert_lev_of_confid,
            "s_uncert_eval_method": s_uncert_eval_method,
            "s_uncert_evaluator": s_uncert_evaluator
        }

        self.constr_uncertainty.append(
            ConstrUncertainty(**params)
        )

        return self.constr_uncertainty[-1]
    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Variable(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Variable information.
    """
    n_var_number: Optional[int] = element(
        default= None,
        tag="n_var_number",
        description="""Variable number""",
        json_schema_extra=dict(),
    )
    variable_id: Optional[VariableID] = element(
        default= None,
        tag="variable_id",
        description="""Variable identification""",
        json_schema_extra=dict(),
    )
    solvent: Optional[Solvent] = element(
        default= None,
        tag="solvent",
        description="""Solvent information""",
        json_schema_extra=dict(),
    )
    var_device_spec: Optional[VarDeviceSpec] = element(
        default= None,
        tag="var_device_spec",
        description="""Variable device specification""",
        json_schema_extra=dict(),
    )
    var_phase_id: Optional[VarPhaseID] = element(
        default= None,
        tag="var_phase_id",
        description="""Variable phase identification""",
        json_schema_extra=dict(),
    )
    var_repeatability: Optional[VarRepeatability] = element(
        default= None,
        tag="var_repeatability",
        description="""Variable repeatability""",
        json_schema_extra=dict(),
    )
    var_uncertainty: list[VarUncertainty] = element(
        default_factory=list,
        tag="var_uncertainty",
        description="""Variable uncertainty""",
        json_schema_extra=dict(),
    )


    def add_to_var_uncertainty(
        self,
        n_uncert_assess_num: Optional[int]= None,
        n_coverage_factor: Optional[float]= None,
        n_expand_uncert_value: Optional[float]= None,
        n_std_uncert_value: Optional[float]= None,
        n_uncert_lev_of_confid: Optional[float]= None,
        s_uncert_eval_method: Optional[str]= None,
        s_uncert_evaluator: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new VarUncertainty to the var_uncertainty list."""
        params = {
            "n_uncert_assess_num": n_uncert_assess_num,
            "n_coverage_factor": n_coverage_factor,
            "n_expand_uncert_value": n_expand_uncert_value,
            "n_std_uncert_value": n_std_uncert_value,
            "n_uncert_lev_of_confid": n_uncert_lev_of_confid,
            "s_uncert_eval_method": s_uncert_eval_method,
            "s_uncert_evaluator": s_uncert_evaluator
        }

        self.var_uncertainty.append(
            VarUncertainty(**params)
        )

        return self.var_uncertainty[-1]
    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Solvent(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Solvent information.
    """
    e_phase: Union[None,ePhase,str] = element(
        default= None,
        tag="e_phase",
        description="""Phase information""",
        json_schema_extra=dict(),
    )
    n_comp_index: Optional[int] = element(
        default= None,
        tag="n_comp_index",
        description="""Component index""",
        json_schema_extra=dict(),
    )
    reg_num: Optional[RegNum] = element(
        default= None,
        tag="reg_num",
        description="""Registration number""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class PropertyMethodID(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Property method identification information.
    """
    n_comp_index: Optional[int] = element(
        default= None,
        tag="n_comp_index",
        description="""Component index""",
        json_schema_extra=dict(),
    )
    property_group: Optional[PropertyGroup] = element(
        default= None,
        tag="property_group",
        description="""Property group information""",
        json_schema_extra=dict(),
    )
    reg_num: Optional[RegNum] = element(
        default= None,
        tag="reg_num",
        description="""Registration number""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class PropertyGroup(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Property group information.
    """
    activity_fugacity_osmotic_prop: Optional[ActivityFugacityOsmoticProp] = element(
        default= None,
        tag="activity_fugacity_osmotic_prop",
        description="""Activity, fugacity, and osmotic properties""",
        json_schema_extra=dict(),
    )
    bio_properties: Optional[BioProperties] = element(
        default= None,
        tag="bio_properties",
        description="""Biological properties""",
        json_schema_extra=dict(),
    )
    composition_at_phase_equilibrium: Optional[CompositionAtPhaseEquilibrium] = element(
        default= None,
        tag="composition_at_phase_equilibrium",
        description="""Composition at phase equilibrium""",
        json_schema_extra=dict(),
    )
    criticals: Optional[Criticals] = element(
        default= None,
        tag="criticals",
        description="""Critical properties""",
        json_schema_extra=dict(),
    )
    excess_partial_apparent_energy_prop: Optional[ExcessPartialApparentEnergyProp] = element(
        default= None,
        tag="excess_partial_apparent_energy_prop",
        description="""Excess partial apparent energy properties""",
        json_schema_extra=dict(),
    )
    heat_capacity_and_derived_prop: Optional[HeatCapacityAndDerivedProp] = element(
        default= None,
        tag="heat_capacity_and_derived_prop",
        description="""Heat capacity and derived properties""",
        json_schema_extra=dict(),
    )
    phase_transition: Optional[PhaseTransition] = element(
        default= None,
        tag="phase_transition",
        description="""Phase transition properties""",
        json_schema_extra=dict(),
    )
    reaction_equilibrium_prop: Optional[ReactionEquilibriumProp] = element(
        default= None,
        tag="reaction_equilibrium_prop",
        description="""Reaction equilibrium properties""",
        json_schema_extra=dict(),
    )
    reaction_state_change_prop: Optional[ReactionStateChangeProp] = element(
        default= None,
        tag="reaction_state_change_prop",
        description="""Reaction state change properties""",
        json_schema_extra=dict(),
    )
    refraction_surface_tension_sound_speed: Optional[RefractionSurfaceTensionSoundSpeed] = element(
        default= None,
        tag="refraction_surface_tension_sound_speed",
        description="""Refraction, surface tension, and sound speed""",
        json_schema_extra=dict(),
    )
    transport_prop: Optional[TransportProp] = element(
        default= None,
        tag="transport_prop",
        description="""Transport properties""",
        json_schema_extra=dict(),
    )
    vapor_p_boiling_t_azeotrop_tand_p: Optional[VaporPBoilingTAzeotropTandP] = element(
        default= None,
        tag="vapor_p_boiling_t_azeotrop_tand_p",
        description="""Vapor pressure, boiling temperature, azeotrope temperature and pressure""",
        json_schema_extra=dict(),
    )
    volumetric_prop: Optional[VolumetricProp] = element(
        default= None,
        tag="volumetric_prop",
        description="""Volumetric properties""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class PropPhaseID(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Property phase identification information.
    """
    e_bio_state: Union[None,eBioState,str] = element(
        default= None,
        tag="e_bio_state",
        description="""Biological state""",
        json_schema_extra=dict(),
    )
    e_crystal_lattice_type: Union[None,eCrystalLatticeType,str] = element(
        default= None,
        tag="e_crystal_lattice_type",
        description="""Crystal lattice type""",
        json_schema_extra=dict(),
    )
    e_prop_phase: Union[None,ePropPhase,str] = element(
        default= None,
        tag="e_prop_phase",
        description="""Property phase""",
        json_schema_extra=dict(),
    )
    n_comp_index: Optional[int] = element(
        default= None,
        tag="n_comp_index",
        description="""Component index""",
        json_schema_extra=dict(),
    )
    reg_num: Optional[RegNum] = element(
        default= None,
        tag="reg_num",
        description="""Registration number""",
        json_schema_extra=dict(),
    )
    s_bio_state: Optional[str] = element(
        default= None,
        tag="s_bio_state",
        description="""Biological state description""",
        json_schema_extra=dict(),
    )
    s_phase_description: Optional[str] = element(
        default= None,
        tag="s_phase_description",
        description="""Phase description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class RefPhaseID(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Reference phase identification information.
    """
    e_crystal_lattice_type: Union[None,eCrystalLatticeType,str] = element(
        default= None,
        tag="e_crystal_lattice_type",
        description="""Crystal lattice type""",
        json_schema_extra=dict(),
    )
    e_ref_phase: Union[None,eRefPhase,str] = element(
        default= None,
        tag="e_ref_phase",
        description="""Reference phase""",
        json_schema_extra=dict(),
    )
    n_comp_index: Optional[int] = element(
        default= None,
        tag="n_comp_index",
        description="""Component index""",
        json_schema_extra=dict(),
    )
    reg_num: Optional[RegNum] = element(
        default= None,
        tag="reg_num",
        description="""Registration number""",
        json_schema_extra=dict(),
    )
    s_phase_description: Optional[str] = element(
        default= None,
        tag="s_phase_description",
        description="""Phase description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class ConstraintID(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Constraint identification information.
    """
    constraint_type: Optional[ConstraintType] = element(
        default= None,
        tag="constraint_type",
        description="""Constraint type""",
        json_schema_extra=dict(),
    )
    n_comp_index: Optional[int] = element(
        default= None,
        tag="n_comp_index",
        description="""Component index""",
        json_schema_extra=dict(),
    )
    reg_num: Optional[RegNum] = element(
        default= None,
        tag="reg_num",
        description="""Registration number""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class ConstraintType(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Constraint type information.
    """
    e_bio_variables: Union[None,eBioVariables,str] = element(
        default= None,
        tag="e_bio_variables",
        description="""Biological variables""",
        json_schema_extra=dict(),
    )
    e_component_composition: Union[None,eComponentComposition,str] = element(
        default= None,
        tag="e_component_composition",
        description="""Component composition""",
        json_schema_extra=dict(),
    )
    e_miscellaneous: Union[None,eMiscellaneous,str] = element(
        default= None,
        tag="e_miscellaneous",
        description="""Miscellaneous constraints""",
        json_schema_extra=dict(),
    )
    e_participant_amount: Union[None,eParticipantAmount,str] = element(
        default= None,
        tag="e_participant_amount",
        description="""Participant amount""",
        json_schema_extra=dict(),
    )
    e_pressure: Union[None,ePressure,str] = element(
        default= None,
        tag="e_pressure",
        description="""Pressure constraints""",
        json_schema_extra=dict(),
    )
    e_solvent_composition: Union[None,eSolventComposition,str] = element(
        default= None,
        tag="e_solvent_composition",
        description="""Solvent composition""",
        json_schema_extra=dict(),
    )
    e_temperature: Union[None,eTemperature,str] = element(
        default= None,
        tag="e_temperature",
        description="""Temperature constraints""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class ConstraintPhaseID(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Constraint phase identification information.
    """
    e_constraint_phase: Union[None,eConstraintPhase,str] = element(
        default= None,
        tag="e_constraint_phase",
        description="""Constraint phase""",
        json_schema_extra=dict(),
    )
    e_crystal_lattice_type: Union[None,eCrystalLatticeType,str] = element(
        default= None,
        tag="e_crystal_lattice_type",
        description="""Crystal lattice type""",
        json_schema_extra=dict(),
    )
    n_comp_index: Optional[int] = element(
        default= None,
        tag="n_comp_index",
        description="""Component index""",
        json_schema_extra=dict(),
    )
    reg_num: Optional[RegNum] = element(
        default= None,
        tag="reg_num",
        description="""Registration number""",
        json_schema_extra=dict(),
    )
    s_phase_description: Optional[str] = element(
        default= None,
        tag="s_phase_description",
        description="""Phase description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class VariableID(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Variable identification information.
    """
    n_comp_index: Optional[int] = element(
        default= None,
        tag="n_comp_index",
        description="""Component index""",
        json_schema_extra=dict(),
    )
    reg_num: Optional[RegNum] = element(
        default= None,
        tag="reg_num",
        description="""Registration number""",
        json_schema_extra=dict(),
    )
    variable_type: Optional[VariableType] = element(
        default= None,
        tag="variable_type",
        description="""Variable type""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class VariableType(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Variable type information.
    """
    e_bio_variables: Union[None,eBioVariables,str] = element(
        default= None,
        tag="e_bio_variables",
        description="""Biological variables""",
        json_schema_extra=dict(),
    )
    e_component_composition: Union[None,eComponentComposition,str] = element(
        default= None,
        tag="e_component_composition",
        description="""Component composition""",
        json_schema_extra=dict(),
    )
    e_miscellaneous: Union[None,eMiscellaneous,str] = element(
        default= None,
        tag="e_miscellaneous",
        description="""Miscellaneous variables""",
        json_schema_extra=dict(),
    )
    e_participant_amount: Union[None,eParticipantAmount,str] = element(
        default= None,
        tag="e_participant_amount",
        description="""Participant amount""",
        json_schema_extra=dict(),
    )
    e_pressure: Union[None,ePressure,str] = element(
        default= None,
        tag="e_pressure",
        description="""Pressure variables""",
        json_schema_extra=dict(),
    )
    e_solvent_composition: Union[None,eSolventComposition,str] = element(
        default= None,
        tag="e_solvent_composition",
        description="""Solvent composition""",
        json_schema_extra=dict(),
    )
    e_temperature: Union[None,eTemperature,str] = element(
        default= None,
        tag="e_temperature",
        description="""Temperature variables""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class VarPhaseID(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Variable phase identification information.
    """
    e_crystal_lattice_type: Union[None,eCrystalLatticeType,str] = element(
        default= None,
        tag="e_crystal_lattice_type",
        description="""Crystal lattice type""",
        json_schema_extra=dict(),
    )
    e_var_phase: Union[None,eVarPhase,str] = element(
        default= None,
        tag="e_var_phase",
        description="""Variable phase""",
        json_schema_extra=dict(),
    )
    n_comp_index: Optional[int] = element(
        default= None,
        tag="n_comp_index",
        description="""Component index""",
        json_schema_extra=dict(),
    )
    reg_num: Optional[RegNum] = element(
        default= None,
        tag="reg_num",
        description="""Registration number""",
        json_schema_extra=dict(),
    )
    s_phase_description: Optional[str] = element(
        default= None,
        tag="s_phase_description",
        description="""Phase description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class NumValues(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Numerical values information.
    """
    property_value: list[PropertyValue] = element(
        default_factory=list,
        tag="property_value",
        description="""Property values""",
        json_schema_extra=dict(),
    )
    variable_value: list[VariableValue] = element(
        default_factory=list,
        tag="variable_value",
        description="""Variable values""",
        json_schema_extra=dict(),
    )


    def add_to_property_value(
        self,
        n_prop_digits: Optional[int]= None,
        n_prop_number: Optional[int]= None,
        n_prop_value: Optional[float]= None,
        prop_limit: Optional[PropLimit]= None,
        combined_uncertainty: list[CombinedUncertainty]= [],
        curve_dev: list[CurveDev]= [],
        n_prop_device_spec_value: Optional[float]= None,
        prop_repeatability: Optional[PropRepeatability]= None,
        prop_uncertainty: list[PropUncertainty]= [],
        **kwargs,
    ):
        """Helper method to add a new PropertyValue to the property_value list."""
        params = {
            "n_prop_digits": n_prop_digits,
            "n_prop_number": n_prop_number,
            "n_prop_value": n_prop_value,
            "prop_limit": prop_limit,
            "combined_uncertainty": combined_uncertainty,
            "curve_dev": curve_dev,
            "n_prop_device_spec_value": n_prop_device_spec_value,
            "prop_repeatability": prop_repeatability,
            "prop_uncertainty": prop_uncertainty
        }

        self.property_value.append(
            PropertyValue(**params)
        )

        return self.property_value[-1]

    def add_to_variable_value(
        self,
        n_var_digits: Optional[int]= None,
        n_var_number: Optional[int]= None,
        n_var_value: Optional[float]= None,
        n_var_device_spec_value: Optional[float]= None,
        var_repeatability: Optional[VarRepeatability]= None,
        var_uncertainty: list[VarUncertainty]= [],
        **kwargs,
    ):
        """Helper method to add a new VariableValue to the variable_value list."""
        params = {
            "n_var_digits": n_var_digits,
            "n_var_number": n_var_number,
            "n_var_value": n_var_value,
            "n_var_device_spec_value": n_var_device_spec_value,
            "var_repeatability": var_repeatability,
            "var_uncertainty": var_uncertainty
        }

        self.variable_value.append(
            VariableValue(**params)
        )

        return self.variable_value[-1]
    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class PropertyValue(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Property value information.
    """
    n_prop_digits: Optional[int] = element(
        default= None,
        tag="n_prop_digits",
        description="""Property digits""",
        json_schema_extra=dict(),
    )
    n_prop_number: Optional[int] = element(
        default= None,
        tag="n_prop_number",
        description="""Property number""",
        json_schema_extra=dict(),
    )
    n_prop_value: Optional[float] = element(
        default= None,
        tag="n_prop_value",
        description="""Property value""",
        json_schema_extra=dict(),
    )
    prop_limit: Optional[PropLimit] = element(
        default= None,
        tag="prop_limit",
        description="""Property limit""",
        json_schema_extra=dict(),
    )
    combined_uncertainty: list[CombinedUncertainty] = element(
        default_factory=list,
        tag="combined_uncertainty",
        description="""Combined uncertainty""",
        json_schema_extra=dict(),
    )
    curve_dev: list[CurveDev] = element(
        default_factory=list,
        tag="curve_dev",
        description="""Curve deviation""",
        json_schema_extra=dict(),
    )
    n_prop_device_spec_value: Optional[float] = element(
        default= None,
        tag="n_prop_device_spec_value",
        description="""Property device specification value""",
        json_schema_extra=dict(),
    )
    prop_repeatability: Optional[PropRepeatability] = element(
        default= None,
        tag="prop_repeatability",
        description="""Property repeatability""",
        json_schema_extra=dict(),
    )
    prop_uncertainty: list[PropUncertainty] = element(
        default_factory=list,
        tag="prop_uncertainty",
        description="""Property uncertainty""",
        json_schema_extra=dict(),
    )


    def add_to_combined_uncertainty(
        self,
        e_comb_uncert_eval_method: Union[None,eCombUncertEvalMethod,str]= None,
        n_comb_uncert_assess_num: Optional[int]= None,
        asym_comb_expand_uncert: Optional[AsymCombExpandUncert]= None,
        asym_comb_std_uncert: Optional[AsymCombStdUncert]= None,
        n_comb_coverage_factor: Optional[float]= None,
        n_comb_expand_uncert_value: Optional[float]= None,
        n_comb_std_uncert_value: Optional[float]= None,
        n_comb_uncert_lev_of_confid: Optional[float]= None,
        s_comb_uncert_eval_method: Optional[str]= None,
        s_comb_uncert_evaluator: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new CombinedUncertainty to the combined_uncertainty list."""
        params = {
            "e_comb_uncert_eval_method": e_comb_uncert_eval_method,
            "n_comb_uncert_assess_num": n_comb_uncert_assess_num,
            "asym_comb_expand_uncert": asym_comb_expand_uncert,
            "asym_comb_std_uncert": asym_comb_std_uncert,
            "n_comb_coverage_factor": n_comb_coverage_factor,
            "n_comb_expand_uncert_value": n_comb_expand_uncert_value,
            "n_comb_std_uncert_value": n_comb_std_uncert_value,
            "n_comb_uncert_lev_of_confid": n_comb_uncert_lev_of_confid,
            "s_comb_uncert_eval_method": s_comb_uncert_eval_method,
            "s_comb_uncert_evaluator": s_comb_uncert_evaluator
        }

        self.combined_uncertainty.append(
            CombinedUncertainty(**params)
        )

        return self.combined_uncertainty[-1]

    def add_to_curve_dev(
        self,
        n_curve_dev_assess_num: Optional[int]= None,
        n_curve_dev_value: Optional[float]= None,
        s_curve_spec: Optional[str]= None,
        n_curve_rms_dev_value: Optional[float]= None,
        n_curve_rms_relative_dev_value: Optional[float]= None,
        s_curve_dev_evaluator: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new CurveDev to the curve_dev list."""
        params = {
            "n_curve_dev_assess_num": n_curve_dev_assess_num,
            "n_curve_dev_value": n_curve_dev_value,
            "s_curve_spec": s_curve_spec,
            "n_curve_rms_dev_value": n_curve_rms_dev_value,
            "n_curve_rms_relative_dev_value": n_curve_rms_relative_dev_value,
            "s_curve_dev_evaluator": s_curve_dev_evaluator
        }

        self.curve_dev.append(
            CurveDev(**params)
        )

        return self.curve_dev[-1]

    def add_to_prop_uncertainty(
        self,
        n_uncert_assess_num: Optional[int]= None,
        asym_expand_uncert: Optional[AsymExpandUncert]= None,
        asym_std_uncert: Optional[AsymStdUncert]= None,
        n_coverage_factor: Optional[float]= None,
        n_expand_uncert_value: Optional[float]= None,
        n_std_uncert_value: Optional[float]= None,
        n_uncert_lev_of_confid: Optional[float]= None,
        s_uncert_eval_method: Optional[str]= None,
        s_uncert_evaluator: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new PropUncertainty to the prop_uncertainty list."""
        params = {
            "n_uncert_assess_num": n_uncert_assess_num,
            "asym_expand_uncert": asym_expand_uncert,
            "asym_std_uncert": asym_std_uncert,
            "n_coverage_factor": n_coverage_factor,
            "n_expand_uncert_value": n_expand_uncert_value,
            "n_std_uncert_value": n_std_uncert_value,
            "n_uncert_lev_of_confid": n_uncert_lev_of_confid,
            "s_uncert_eval_method": s_uncert_eval_method,
            "s_uncert_evaluator": s_uncert_evaluator
        }

        self.prop_uncertainty.append(
            PropUncertainty(**params)
        )

        return self.prop_uncertainty[-1]
    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class VariableValue(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Variable value information.
    """
    n_var_digits: Optional[int] = element(
        default= None,
        tag="n_var_digits",
        description="""Variable digits""",
        json_schema_extra=dict(),
    )
    n_var_number: Optional[int] = element(
        default= None,
        tag="n_var_number",
        description="""Variable number""",
        json_schema_extra=dict(),
    )
    n_var_value: Optional[float] = element(
        default= None,
        tag="n_var_value",
        description="""Variable value""",
        json_schema_extra=dict(),
    )
    n_var_device_spec_value: Optional[float] = element(
        default= None,
        tag="n_var_device_spec_value",
        description="""Variable device specification value""",
        json_schema_extra=dict(),
    )
    var_repeatability: Optional[VarRepeatability] = element(
        default= None,
        tag="var_repeatability",
        description="""Variable repeatability""",
        json_schema_extra=dict(),
    )
    var_uncertainty: list[VarUncertainty] = element(
        default_factory=list,
        tag="var_uncertainty",
        description="""Variable uncertainty""",
        json_schema_extra=dict(),
    )


    def add_to_var_uncertainty(
        self,
        n_uncert_assess_num: Optional[int]= None,
        n_coverage_factor: Optional[float]= None,
        n_expand_uncert_value: Optional[float]= None,
        n_std_uncert_value: Optional[float]= None,
        n_uncert_lev_of_confid: Optional[float]= None,
        s_uncert_eval_method: Optional[str]= None,
        s_uncert_evaluator: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new VarUncertainty to the var_uncertainty list."""
        params = {
            "n_uncert_assess_num": n_uncert_assess_num,
            "n_coverage_factor": n_coverage_factor,
            "n_expand_uncert_value": n_expand_uncert_value,
            "n_std_uncert_value": n_std_uncert_value,
            "n_uncert_lev_of_confid": n_uncert_lev_of_confid,
            "s_uncert_eval_method": s_uncert_eval_method,
            "s_uncert_evaluator": s_uncert_evaluator
        }

        self.var_uncertainty.append(
            VarUncertainty(**params)
        )

        return self.var_uncertainty[-1]
    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class PropLimit(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Property limit information.
    """
    n_prop_limit_digits: Optional[int] = element(
        default= None,
        tag="n_prop_limit_digits",
        description="""Property limit digits""",
        json_schema_extra=dict(),
    )
    n_prop_lower_limit_value: Optional[float] = element(
        default= None,
        tag="n_prop_lower_limit_value",
        description="""Property lower limit value""",
        json_schema_extra=dict(),
    )
    n_prop_upper_limit_value: Optional[float] = element(
        default= None,
        tag="n_prop_upper_limit_value",
        description="""Property upper limit value""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class CombinedUncertainty(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Combined uncertainty information.
    """
    e_comb_uncert_eval_method: Union[None,eCombUncertEvalMethod,str] = element(
        default= None,
        tag="e_comb_uncert_eval_method",
        description="""Combined uncertainty evaluation method""",
        json_schema_extra=dict(),
    )
    n_comb_uncert_assess_num: Optional[int] = element(
        default= None,
        tag="n_comb_uncert_assess_num",
        description="""Combined uncertainty assessment number""",
        json_schema_extra=dict(),
    )
    asym_comb_expand_uncert: Optional[AsymCombExpandUncert] = element(
        default= None,
        tag="asym_comb_expand_uncert",
        description="""Asymmetric combined expanded uncertainty""",
        json_schema_extra=dict(),
    )
    asym_comb_std_uncert: Optional[AsymCombStdUncert] = element(
        default= None,
        tag="asym_comb_std_uncert",
        description="""Asymmetric combined standard uncertainty""",
        json_schema_extra=dict(),
    )
    n_comb_coverage_factor: Optional[float] = element(
        default= None,
        tag="n_comb_coverage_factor",
        description="""Combined coverage factor""",
        json_schema_extra=dict(),
    )
    n_comb_expand_uncert_value: Optional[float] = element(
        default= None,
        tag="n_comb_expand_uncert_value",
        description="""Combined expanded uncertainty value""",
        json_schema_extra=dict(),
    )
    n_comb_std_uncert_value: Optional[float] = element(
        default= None,
        tag="n_comb_std_uncert_value",
        description="""Combined standard uncertainty value""",
        json_schema_extra=dict(),
    )
    n_comb_uncert_lev_of_confid: Optional[float] = element(
        default= None,
        tag="n_comb_uncert_lev_of_confid",
        description="""Combined uncertainty level of confidence""",
        json_schema_extra=dict(),
    )
    s_comb_uncert_eval_method: Optional[str] = element(
        default= None,
        tag="s_comb_uncert_eval_method",
        description="""Combined uncertainty evaluation method description""",
        json_schema_extra=dict(),
    )
    s_comb_uncert_evaluator: Optional[str] = element(
        default= None,
        tag="s_comb_uncert_evaluator",
        description="""Combined uncertainty evaluator""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class PropUncertainty(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Property uncertainty information.
    """
    n_uncert_assess_num: Optional[int] = element(
        default= None,
        tag="n_uncert_assess_num",
        description="""Uncertainty assessment number""",
        json_schema_extra=dict(),
    )
    asym_expand_uncert: Optional[AsymExpandUncert] = element(
        default= None,
        tag="asym_expand_uncert",
        description="""Asymmetric expanded uncertainty""",
        json_schema_extra=dict(),
    )
    asym_std_uncert: Optional[AsymStdUncert] = element(
        default= None,
        tag="asym_std_uncert",
        description="""Asymmetric standard uncertainty""",
        json_schema_extra=dict(),
    )
    n_coverage_factor: Optional[float] = element(
        default= None,
        tag="n_coverage_factor",
        description="""Coverage factor""",
        json_schema_extra=dict(),
    )
    n_expand_uncert_value: Optional[float] = element(
        default= None,
        tag="n_expand_uncert_value",
        description="""Expanded uncertainty value""",
        json_schema_extra=dict(),
    )
    n_std_uncert_value: Optional[float] = element(
        default= None,
        tag="n_std_uncert_value",
        description="""Standard uncertainty value""",
        json_schema_extra=dict(),
    )
    n_uncert_lev_of_confid: Optional[float] = element(
        default= None,
        tag="n_uncert_lev_of_confid",
        description="""Uncertainty level of confidence""",
        json_schema_extra=dict(),
    )
    s_uncert_eval_method: Optional[str] = element(
        default= None,
        tag="s_uncert_eval_method",
        description="""Uncertainty evaluation method""",
        json_schema_extra=dict(),
    )
    s_uncert_evaluator: Optional[str] = element(
        default= None,
        tag="s_uncert_evaluator",
        description="""Uncertainty evaluator""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class PropRepeatability(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Property repeatability information.
    """
    e_repeat_method: Union[None,eRepeatMethod,str] = element(
        default= None,
        tag="e_repeat_method",
        description="""Repeat method""",
        json_schema_extra=dict(),
    )
    n_prop_repeat_value: Optional[float] = element(
        default= None,
        tag="n_prop_repeat_value",
        description="""Property repeat value""",
        json_schema_extra=dict(),
    )
    n_repetitions: Optional[int] = element(
        default= None,
        tag="n_repetitions",
        description="""Number of repetitions""",
        json_schema_extra=dict(),
    )
    s_repeat_evaluator: Optional[str] = element(
        default= None,
        tag="s_repeat_evaluator",
        description="""Repeat evaluator""",
        json_schema_extra=dict(),
    )
    s_repeat_method: Optional[str] = element(
        default= None,
        tag="s_repeat_method",
        description="""Repeat method description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class PropDeviceSpec(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Property device specification information.
    """
    e_device_spec_method: Union[None,eDeviceSpecMethod,str] = element(
        default= None,
        tag="e_device_spec_method",
        description="""Device specification method""",
        json_schema_extra=dict(),
    )
    n_device_spec_lev_of_confid: Optional[float] = element(
        default= None,
        tag="n_device_spec_lev_of_confid",
        description="""Device specification level of confidence""",
        json_schema_extra=dict(),
    )
    s_device_spec_evaluator: Optional[str] = element(
        default= None,
        tag="s_device_spec_evaluator",
        description="""Device specification evaluator""",
        json_schema_extra=dict(),
    )
    s_device_spec_method: Optional[str] = element(
        default= None,
        tag="s_device_spec_method",
        description="""Device specification method description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class CurveDev(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Curve deviation information.
    """
    n_curve_dev_assess_num: Optional[int] = element(
        default= None,
        tag="n_curve_dev_assess_num",
        description="""Curve deviation assessment number""",
        json_schema_extra=dict(),
    )
    n_curve_dev_value: Optional[float] = element(
        default= None,
        tag="n_curve_dev_value",
        description="""Curve deviation value""",
        json_schema_extra=dict(),
    )
    s_curve_spec: Optional[str] = element(
        default= None,
        tag="s_curve_spec",
        description="""Curve specification""",
        json_schema_extra=dict(),
    )
    n_curve_rms_dev_value: Optional[float] = element(
        default= None,
        tag="n_curve_rms_dev_value",
        description="""Curve RMS deviation value""",
        json_schema_extra=dict(),
    )
    n_curve_rms_relative_dev_value: Optional[float] = element(
        default= None,
        tag="n_curve_rms_relative_dev_value",
        description="""Curve RMS relative deviation value""",
        json_schema_extra=dict(),
    )
    s_curve_dev_evaluator: Optional[str] = element(
        default= None,
        tag="s_curve_dev_evaluator",
        description="""Curve deviation evaluator""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class ConstrUncertainty(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Constraint uncertainty information.
    """
    n_coverage_factor: Optional[float] = element(
        default= None,
        tag="n_coverage_factor",
        description="""Coverage factor""",
        json_schema_extra=dict(),
    )
    n_expand_uncert_value: Optional[float] = element(
        default= None,
        tag="n_expand_uncert_value",
        description="""Expanded uncertainty value""",
        json_schema_extra=dict(),
    )
    n_std_uncert_value: Optional[float] = element(
        default= None,
        tag="n_std_uncert_value",
        description="""Standard uncertainty value""",
        json_schema_extra=dict(),
    )
    n_uncert_lev_of_confid: Optional[float] = element(
        default= None,
        tag="n_uncert_lev_of_confid",
        description="""Uncertainty level of confidence""",
        json_schema_extra=dict(),
    )
    s_uncert_eval_method: Optional[str] = element(
        default= None,
        tag="s_uncert_eval_method",
        description="""Uncertainty evaluation method""",
        json_schema_extra=dict(),
    )
    s_uncert_evaluator: Optional[str] = element(
        default= None,
        tag="s_uncert_evaluator",
        description="""Uncertainty evaluator""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class ConstrRepeatability(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Constraint repeatability information.
    """
    e_repeat_method: Union[None,eRepeatMethod,str] = element(
        default= None,
        tag="e_repeat_method",
        description="""Repeat method""",
        json_schema_extra=dict(),
    )
    n_repeat_value: Optional[float] = element(
        default= None,
        tag="n_repeat_value",
        description="""Repeat value""",
        json_schema_extra=dict(),
    )
    n_repetitions: Optional[int] = element(
        default= None,
        tag="n_repetitions",
        description="""Number of repetitions""",
        json_schema_extra=dict(),
    )
    s_repeat_evaluator: Optional[str] = element(
        default= None,
        tag="s_repeat_evaluator",
        description="""Repeat evaluator""",
        json_schema_extra=dict(),
    )
    s_repeat_method: Optional[str] = element(
        default= None,
        tag="s_repeat_method",
        description="""Repeat method description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class ConstrDeviceSpec(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Constraint device specification information.
    """
    e_device_spec_method: Union[None,eDeviceSpecMethod,str] = element(
        default= None,
        tag="e_device_spec_method",
        description="""Device specification method""",
        json_schema_extra=dict(),
    )
    n_device_spec_lev_of_confid: Optional[float] = element(
        default= None,
        tag="n_device_spec_lev_of_confid",
        description="""Device specification level of confidence""",
        json_schema_extra=dict(),
    )
    n_device_spec_value: Optional[float] = element(
        default= None,
        tag="n_device_spec_value",
        description="""Device specification value""",
        json_schema_extra=dict(),
    )
    s_device_spec_evaluator: Optional[str] = element(
        default= None,
        tag="s_device_spec_evaluator",
        description="""Device specification evaluator""",
        json_schema_extra=dict(),
    )
    s_device_spec_method: Optional[str] = element(
        default= None,
        tag="s_device_spec_method",
        description="""Device specification method description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class VarUncertainty(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Variable uncertainty information.
    """
    n_uncert_assess_num: Optional[int] = element(
        default= None,
        tag="n_uncert_assess_num",
        description="""Uncertainty assessment number""",
        json_schema_extra=dict(),
    )
    n_coverage_factor: Optional[float] = element(
        default= None,
        tag="n_coverage_factor",
        description="""Coverage factor""",
        json_schema_extra=dict(),
    )
    n_expand_uncert_value: Optional[float] = element(
        default= None,
        tag="n_expand_uncert_value",
        description="""Expanded uncertainty value""",
        json_schema_extra=dict(),
    )
    n_std_uncert_value: Optional[float] = element(
        default= None,
        tag="n_std_uncert_value",
        description="""Standard uncertainty value""",
        json_schema_extra=dict(),
    )
    n_uncert_lev_of_confid: Optional[float] = element(
        default= None,
        tag="n_uncert_lev_of_confid",
        description="""Uncertainty level of confidence""",
        json_schema_extra=dict(),
    )
    s_uncert_eval_method: Optional[str] = element(
        default= None,
        tag="s_uncert_eval_method",
        description="""Uncertainty evaluation method""",
        json_schema_extra=dict(),
    )
    s_uncert_evaluator: Optional[str] = element(
        default= None,
        tag="s_uncert_evaluator",
        description="""Uncertainty evaluator""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class VarRepeatability(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Variable repeatability information.
    """
    e_repeat_method: Union[None,eRepeatMethod,str] = element(
        default= None,
        tag="e_repeat_method",
        description="""Repeat method""",
        json_schema_extra=dict(),
    )
    n_repetitions: Optional[int] = element(
        default= None,
        tag="n_repetitions",
        description="""Number of repetitions""",
        json_schema_extra=dict(),
    )
    n_var_repeat_value: Optional[float] = element(
        default= None,
        tag="n_var_repeat_value",
        description="""Variable repeat value""",
        json_schema_extra=dict(),
    )
    s_repeat_evaluator: Optional[str] = element(
        default= None,
        tag="s_repeat_evaluator",
        description="""Repeat evaluator""",
        json_schema_extra=dict(),
    )
    s_repeat_method: Optional[str] = element(
        default= None,
        tag="s_repeat_method",
        description="""Repeat method description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class VarDeviceSpec(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Variable device specification information.
    """
    e_device_spec_method: Union[None,eDeviceSpecMethod,str] = element(
        default= None,
        tag="e_device_spec_method",
        description="""Device specification method""",
        json_schema_extra=dict(),
    )
    n_device_spec_lev_of_confid: Optional[float] = element(
        default= None,
        tag="n_device_spec_lev_of_confid",
        description="""Device specification level of confidence""",
        json_schema_extra=dict(),
    )
    s_device_spec_evaluator: Optional[str] = element(
        default= None,
        tag="s_device_spec_evaluator",
        description="""Device specification evaluator""",
        json_schema_extra=dict(),
    )
    s_device_spec_method: Optional[str] = element(
        default= None,
        tag="s_device_spec_method",
        description="""Device specification method description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class AsymCombStdUncert(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Asymmetric combined standard uncertainty information.
    """
    n_negative_value: Optional[float] = element(
        default= None,
        tag="n_negative_value",
        description="""Negative value""",
        json_schema_extra=dict(),
    )
    n_positive_value: Optional[float] = element(
        default= None,
        tag="n_positive_value",
        description="""Positive value""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class AsymCombExpandUncert(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Asymmetric combined expanded uncertainty information.
    """
    n_negative_value: Optional[float] = element(
        default= None,
        tag="n_negative_value",
        description="""Negative value""",
        json_schema_extra=dict(),
    )
    n_positive_value: Optional[float] = element(
        default= None,
        tag="n_positive_value",
        description="""Positive value""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class AsymStdUncert(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Asymmetric standard uncertainty information.
    """
    n_negative_value: Optional[float] = element(
        default= None,
        tag="n_negative_value",
        description="""Negative value""",
        json_schema_extra=dict(),
    )
    n_positive_value: Optional[float] = element(
        default= None,
        tag="n_positive_value",
        description="""Positive value""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class AsymExpandUncert(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Asymmetric expanded uncertainty information.
    """
    n_negative_value: Optional[float] = element(
        default= None,
        tag="n_negative_value",
        description="""Negative value""",
        json_schema_extra=dict(),
    )
    n_positive_value: Optional[float] = element(
        default= None,
        tag="n_positive_value",
        description="""Positive value""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Equation(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Equation information.
    """
    e_eq_name: Union[None,eEqName,str] = element(
        default= None,
        tag="e_eq_name",
        description="""Equation name""",
        json_schema_extra=dict(),
    )
    s_eq_name: Optional[str] = element(
        default= None,
        tag="s_eq_name",
        description="""Equation name description""",
        json_schema_extra=dict(),
    )
    url_math_source: Optional[str] = element(
        default= None,
        tag="url_math_source",
        description="""URL to mathematical source""",
        json_schema_extra=dict(),
    )
    covariance: list[Covariance] = element(
        default_factory=list,
        tag="covariance",
        description="""Covariance information""",
        json_schema_extra=dict(),
    )
    eq_constant: list[EqConstant] = element(
        default_factory=list,
        tag="eq_constant",
        description="""Equation constants""",
        json_schema_extra=dict(),
    )
    eq_constraint: list[EqConstraint] = element(
        default_factory=list,
        tag="eq_constraint",
        description="""Equation constraints""",
        json_schema_extra=dict(),
    )
    eq_parameter: list[EqParameter] = element(
        default_factory=list,
        tag="eq_parameter",
        description="""Equation parameters""",
        json_schema_extra=dict(),
    )
    eq_property: list[EqProperty] = element(
        default_factory=list,
        tag="eq_property",
        description="""Equation properties""",
        json_schema_extra=dict(),
    )
    eq_variable: list[EqVariable] = element(
        default_factory=list,
        tag="eq_variable",
        description="""Equation variables""",
        json_schema_extra=dict(),
    )
    n_covariance_lev_of_confid: Optional[float] = element(
        default= None,
        tag="n_covariance_lev_of_confid",
        description="""Covariance level of confidence""",
        json_schema_extra=dict(),
    )


    def add_to_covariance(
        self,
        n_covariance_value: Optional[float]= None,
        n_eq_par_number1: Optional[int]= None,
        n_eq_par_number2: Optional[int]= None,
        **kwargs,
    ):
        """Helper method to add a new Covariance to the covariance list."""
        params = {
            "n_covariance_value": n_covariance_value,
            "n_eq_par_number1": n_eq_par_number1,
            "n_eq_par_number2": n_eq_par_number2
        }

        self.covariance.append(
            Covariance(**params)
        )

        return self.covariance[-1]

    def add_to_eq_constant(
        self,
        n_eq_constant_digits: Optional[int]= None,
        n_eq_constant_value: Optional[float]= None,
        s_eq_constant_symbol: Optional[str]= None,
        n_eq_constant_index: list[int]= [],
        **kwargs,
    ):
        """Helper method to add a new EqConstant to the eq_constant list."""
        params = {
            "n_eq_constant_digits": n_eq_constant_digits,
            "n_eq_constant_value": n_eq_constant_value,
            "s_eq_constant_symbol": s_eq_constant_symbol,
            "n_eq_constant_index": n_eq_constant_index
        }

        self.eq_constant.append(
            EqConstant(**params)
        )

        return self.eq_constant[-1]

    def add_to_eq_constraint(
        self,
        n_constraint_number: Optional[int]= None,
        n_pure_or_mixture_data_number: Optional[int]= None,
        n_reaction_data_number: Optional[int]= None,
        s_eq_symbol: Optional[str]= None,
        n_eq_constraint_index: list[int]= [],
        n_eq_constraint_range_max: Optional[float]= None,
        n_eq_constraint_range_min: Optional[float]= None,
        s_other_constraint_unit: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new EqConstraint to the eq_constraint list."""
        params = {
            "n_constraint_number": n_constraint_number,
            "n_pure_or_mixture_data_number": n_pure_or_mixture_data_number,
            "n_reaction_data_number": n_reaction_data_number,
            "s_eq_symbol": s_eq_symbol,
            "n_eq_constraint_index": n_eq_constraint_index,
            "n_eq_constraint_range_max": n_eq_constraint_range_max,
            "n_eq_constraint_range_min": n_eq_constraint_range_min,
            "s_other_constraint_unit": s_other_constraint_unit
        }

        self.eq_constraint.append(
            EqConstraint(**params)
        )

        return self.eq_constraint[-1]

    def add_to_eq_parameter(
        self,
        n_eq_par_digits: Optional[int]= None,
        n_eq_par_value: Optional[float]= None,
        s_eq_par_symbol: Optional[str]= None,
        n_eq_par_index: list[int]= [],
        n_eq_par_number: Optional[int]= None,
        **kwargs,
    ):
        """Helper method to add a new EqParameter to the eq_parameter list."""
        params = {
            "n_eq_par_digits": n_eq_par_digits,
            "n_eq_par_value": n_eq_par_value,
            "s_eq_par_symbol": s_eq_par_symbol,
            "n_eq_par_index": n_eq_par_index,
            "n_eq_par_number": n_eq_par_number
        }

        self.eq_parameter.append(
            EqParameter(**params)
        )

        return self.eq_parameter[-1]

    def add_to_eq_property(
        self,
        n_prop_number: Optional[int]= None,
        n_pure_or_mixture_data_number: Optional[int]= None,
        n_reaction_data_number: Optional[int]= None,
        s_eq_symbol: Optional[str]= None,
        n_eq_prop_index: list[int]= [],
        n_eq_prop_range_max: Optional[float]= None,
        n_eq_prop_range_min: Optional[float]= None,
        s_other_prop_unit: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new EqProperty to the eq_property list."""
        params = {
            "n_prop_number": n_prop_number,
            "n_pure_or_mixture_data_number": n_pure_or_mixture_data_number,
            "n_reaction_data_number": n_reaction_data_number,
            "s_eq_symbol": s_eq_symbol,
            "n_eq_prop_index": n_eq_prop_index,
            "n_eq_prop_range_max": n_eq_prop_range_max,
            "n_eq_prop_range_min": n_eq_prop_range_min,
            "s_other_prop_unit": s_other_prop_unit
        }

        self.eq_property.append(
            EqProperty(**params)
        )

        return self.eq_property[-1]

    def add_to_eq_variable(
        self,
        n_pure_or_mixture_data_number: Optional[int]= None,
        n_reaction_data_number: Optional[int]= None,
        n_var_number: Optional[int]= None,
        s_eq_symbol: Optional[str]= None,
        n_eq_var_index: list[int]= [],
        n_eq_var_range_max: Optional[float]= None,
        n_eq_var_range_min: Optional[float]= None,
        s_other_var_unit: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new EqVariable to the eq_variable list."""
        params = {
            "n_pure_or_mixture_data_number": n_pure_or_mixture_data_number,
            "n_reaction_data_number": n_reaction_data_number,
            "n_var_number": n_var_number,
            "s_eq_symbol": s_eq_symbol,
            "n_eq_var_index": n_eq_var_index,
            "n_eq_var_range_max": n_eq_var_range_max,
            "n_eq_var_range_min": n_eq_var_range_min,
            "s_other_var_unit": s_other_var_unit
        }

        self.eq_variable.append(
            EqVariable(**params)
        )

        return self.eq_variable[-1]
    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class ActivityFugacityOsmoticProp(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Activity, fugacity, and osmotic properties.
    """
    critical_evaluation: Optional[CriticalEvaluation] = element(
        default= None,
        tag="critical_evaluation",
        description="""Critical evaluation information""",
        json_schema_extra=dict(),
    )
    e_method_name: Union[None,eMethodName,str] = element(
        default= None,
        tag="e_method_name",
        description="""Method name""",
        json_schema_extra=dict(),
    )
    e_prop_name: Union[None,ePropName,str] = element(
        default= None,
        tag="e_prop_name",
        description="""Property name""",
        json_schema_extra=dict(),
    )
    prediction: Optional[Prediction] = element(
        default= None,
        tag="prediction",
        description="""Prediction information""",
        json_schema_extra=dict(),
    )
    s_method_name: Optional[str] = element(
        default= None,
        tag="s_method_name",
        description="""Method name description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class BioProperties(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Biological properties.
    """
    critical_evaluation: Optional[CriticalEvaluation] = element(
        default= None,
        tag="critical_evaluation",
        description="""Critical evaluation information""",
        json_schema_extra=dict(),
    )
    e_method_name: Union[None,eMethodName,str] = element(
        default= None,
        tag="e_method_name",
        description="""Method name""",
        json_schema_extra=dict(),
    )
    e_prop_name: Union[None,ePropName,str] = element(
        default= None,
        tag="e_prop_name",
        description="""Property name""",
        json_schema_extra=dict(),
    )
    prediction: Optional[Prediction] = element(
        default= None,
        tag="prediction",
        description="""Prediction information""",
        json_schema_extra=dict(),
    )
    s_method_name: Optional[str] = element(
        default= None,
        tag="s_method_name",
        description="""Method name description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class CompositionAtPhaseEquilibrium(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Composition at phase equilibrium.
    """
    critical_evaluation: Optional[CriticalEvaluation] = element(
        default= None,
        tag="critical_evaluation",
        description="""Critical evaluation information""",
        json_schema_extra=dict(),
    )
    e_method_name: Union[None,eMethodName,str] = element(
        default= None,
        tag="e_method_name",
        description="""Method name""",
        json_schema_extra=dict(),
    )
    e_prop_name: Union[None,ePropName,str] = element(
        default= None,
        tag="e_prop_name",
        description="""Property name""",
        json_schema_extra=dict(),
    )
    prediction: Optional[Prediction] = element(
        default= None,
        tag="prediction",
        description="""Prediction information""",
        json_schema_extra=dict(),
    )
    s_method_name: Optional[str] = element(
        default= None,
        tag="s_method_name",
        description="""Method name description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Criticals(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Critical properties.
    """
    critical_evaluation: Optional[CriticalEvaluation] = element(
        default= None,
        tag="critical_evaluation",
        description="""Critical evaluation information""",
        json_schema_extra=dict(),
    )
    e_method_name: Union[None,eMethodName,str] = element(
        default= None,
        tag="e_method_name",
        description="""Method name""",
        json_schema_extra=dict(),
    )
    e_prop_name: Union[None,ePropName,str] = element(
        default= None,
        tag="e_prop_name",
        description="""Property name""",
        json_schema_extra=dict(),
    )
    prediction: Optional[Prediction] = element(
        default= None,
        tag="prediction",
        description="""Prediction information""",
        json_schema_extra=dict(),
    )
    s_method_name: Optional[str] = element(
        default= None,
        tag="s_method_name",
        description="""Method name description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class ExcessPartialApparentEnergyProp(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Excess partial apparent energy properties.
    """
    critical_evaluation: Optional[CriticalEvaluation] = element(
        default= None,
        tag="critical_evaluation",
        description="""Critical evaluation information""",
        json_schema_extra=dict(),
    )
    e_method_name: Union[None,eMethodName,str] = element(
        default= None,
        tag="e_method_name",
        description="""Method name""",
        json_schema_extra=dict(),
    )
    e_prop_name: Union[None,ePropName,str] = element(
        default= None,
        tag="e_prop_name",
        description="""Property name""",
        json_schema_extra=dict(),
    )
    prediction: Optional[Prediction] = element(
        default= None,
        tag="prediction",
        description="""Prediction information""",
        json_schema_extra=dict(),
    )
    s_method_name: Optional[str] = element(
        default= None,
        tag="s_method_name",
        description="""Method name description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class HeatCapacityAndDerivedProp(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Heat capacity and derived properties.
    """
    critical_evaluation: Optional[CriticalEvaluation] = element(
        default= None,
        tag="critical_evaluation",
        description="""Critical evaluation information""",
        json_schema_extra=dict(),
    )
    e_method_name: Union[None,eMethodName,str] = element(
        default= None,
        tag="e_method_name",
        description="""Method name""",
        json_schema_extra=dict(),
    )
    e_prop_name: Union[None,ePropName,str] = element(
        default= None,
        tag="e_prop_name",
        description="""Property name""",
        json_schema_extra=dict(),
    )
    prediction: Optional[Prediction] = element(
        default= None,
        tag="prediction",
        description="""Prediction information""",
        json_schema_extra=dict(),
    )
    s_method_name: Optional[str] = element(
        default= None,
        tag="s_method_name",
        description="""Method name description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class PhaseTransition(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Phase transition properties.
    """
    critical_evaluation: Optional[CriticalEvaluation] = element(
        default= None,
        tag="critical_evaluation",
        description="""Critical evaluation information""",
        json_schema_extra=dict(),
    )
    e_method_name: Union[None,eMethodName,str] = element(
        default= None,
        tag="e_method_name",
        description="""Method name""",
        json_schema_extra=dict(),
    )
    e_prop_name: Union[None,ePropName,str] = element(
        default= None,
        tag="e_prop_name",
        description="""Property name""",
        json_schema_extra=dict(),
    )
    prediction: Optional[Prediction] = element(
        default= None,
        tag="prediction",
        description="""Prediction information""",
        json_schema_extra=dict(),
    )
    s_method_name: Optional[str] = element(
        default= None,
        tag="s_method_name",
        description="""Method name description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class ReactionEquilibriumProp(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Reaction equilibrium properties.
    """
    critical_evaluation: Optional[CriticalEvaluation] = element(
        default= None,
        tag="critical_evaluation",
        description="""Critical evaluation information""",
        json_schema_extra=dict(),
    )
    e_method_name: Union[None,eMethodName,str] = element(
        default= None,
        tag="e_method_name",
        description="""Method name""",
        json_schema_extra=dict(),
    )
    e_prop_name: Union[None,ePropName,str] = element(
        default= None,
        tag="e_prop_name",
        description="""Property name""",
        json_schema_extra=dict(),
    )
    prediction: Optional[Prediction] = element(
        default= None,
        tag="prediction",
        description="""Prediction information""",
        json_schema_extra=dict(),
    )
    s_method_name: list[str] = element(
        default_factory=list,
        tag="s_method_name",
        description="""Method name descriptions""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class ReactionStateChangeProp(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Reaction state change properties.
    """
    critical_evaluation: Optional[CriticalEvaluation] = element(
        default= None,
        tag="critical_evaluation",
        description="""Critical evaluation information""",
        json_schema_extra=dict(),
    )
    e_method_name: Union[None,eMethodName,str] = element(
        default= None,
        tag="e_method_name",
        description="""Method name""",
        json_schema_extra=dict(),
    )
    e_prop_name: Union[None,ePropName,str] = element(
        default= None,
        tag="e_prop_name",
        description="""Property name""",
        json_schema_extra=dict(),
    )
    prediction: Optional[Prediction] = element(
        default= None,
        tag="prediction",
        description="""Prediction information""",
        json_schema_extra=dict(),
    )
    s_method_name: list[str] = element(
        default_factory=list,
        tag="s_method_name",
        description="""Method name descriptions""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class RefractionSurfaceTensionSoundSpeed(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Refraction, surface tension, and sound speed properties.
    """
    critical_evaluation: Optional[CriticalEvaluation] = element(
        default= None,
        tag="critical_evaluation",
        description="""Critical evaluation information""",
        json_schema_extra=dict(),
    )
    e_method_name: Union[None,eMethodName,str] = element(
        default= None,
        tag="e_method_name",
        description="""Method name""",
        json_schema_extra=dict(),
    )
    e_prop_name: Union[None,ePropName,str] = element(
        default= None,
        tag="e_prop_name",
        description="""Property name""",
        json_schema_extra=dict(),
    )
    prediction: Optional[Prediction] = element(
        default= None,
        tag="prediction",
        description="""Prediction information""",
        json_schema_extra=dict(),
    )
    s_method_name: Optional[str] = element(
        default= None,
        tag="s_method_name",
        description="""Method name description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class TransportProp(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Transport properties.
    """
    critical_evaluation: Optional[CriticalEvaluation] = element(
        default= None,
        tag="critical_evaluation",
        description="""Critical evaluation information""",
        json_schema_extra=dict(),
    )
    e_method_name: Union[None,eMethodName,str] = element(
        default= None,
        tag="e_method_name",
        description="""Method name""",
        json_schema_extra=dict(),
    )
    e_prop_name: Union[None,ePropName,str] = element(
        default= None,
        tag="e_prop_name",
        description="""Property name""",
        json_schema_extra=dict(),
    )
    prediction: Optional[Prediction] = element(
        default= None,
        tag="prediction",
        description="""Prediction information""",
        json_schema_extra=dict(),
    )
    s_method_name: Optional[str] = element(
        default= None,
        tag="s_method_name",
        description="""Method name description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class VaporPBoilingTAzeotropTandP(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Vapor pressure, boiling temperature, azeotrope temperature and
    pressure properties.
    """
    critical_evaluation: Optional[CriticalEvaluation] = element(
        default= None,
        tag="critical_evaluation",
        description="""Critical evaluation information""",
        json_schema_extra=dict(),
    )
    e_method_name: Union[None,eMethodName,str] = element(
        default= None,
        tag="e_method_name",
        description="""Method name""",
        json_schema_extra=dict(),
    )
    e_prop_name: Union[None,ePropName,str] = element(
        default= None,
        tag="e_prop_name",
        description="""Property name""",
        json_schema_extra=dict(),
    )
    prediction: Optional[Prediction] = element(
        default= None,
        tag="prediction",
        description="""Prediction information""",
        json_schema_extra=dict(),
    )
    s_method_name: Optional[str] = element(
        default= None,
        tag="s_method_name",
        description="""Method name description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class VolumetricProp(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Volumetric properties.
    """
    critical_evaluation: Optional[CriticalEvaluation] = element(
        default= None,
        tag="critical_evaluation",
        description="""Critical evaluation information""",
        json_schema_extra=dict(),
    )
    e_method_name: Union[None,eMethodName,str] = element(
        default= None,
        tag="e_method_name",
        description="""Method name""",
        json_schema_extra=dict(),
    )
    e_prop_name: Union[None,ePropName,str] = element(
        default= None,
        tag="e_prop_name",
        description="""Property name""",
        json_schema_extra=dict(),
    )
    prediction: Optional[Prediction] = element(
        default= None,
        tag="prediction",
        description="""Prediction information""",
        json_schema_extra=dict(),
    )
    s_method_name: Optional[str] = element(
        default= None,
        tag="s_method_name",
        description="""Method name description""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class CriticalEvaluation(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Critical evaluation information.
    """
    equation_of_state: Optional[EquationOfState] = element(
        default= None,
        tag="equation_of_state",
        description="""Equation of state information""",
        json_schema_extra=dict(),
    )
    multi_prop: Optional[MultiProp] = element(
        default= None,
        tag="multi_prop",
        description="""Multiple property information""",
        json_schema_extra=dict(),
    )
    single_prop: Optional[SingleProp] = element(
        default= None,
        tag="single_prop",
        description="""Single property information""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Prediction(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Prediction information.
    """
    e_prediction_type: Union[None,ePredictionType,str] = element(
        default= None,
        tag="e_prediction_type",
        description="""Prediction type""",
        json_schema_extra=dict(),
    )
    prediction_method_ref: list[PredictionMethodRef] = element(
        default_factory=list,
        tag="prediction_method_ref",
        description="""Prediction method references""",
        json_schema_extra=dict(),
    )
    s_prediction_method_description: Optional[str] = element(
        default= None,
        tag="s_prediction_method_description",
        description="""Prediction method description""",
        json_schema_extra=dict(),
    )
    s_prediction_method_name: Optional[str] = element(
        default= None,
        tag="s_prediction_method_name",
        description="""Prediction method name""",
        json_schema_extra=dict(),
    )


    def add_to_prediction_method_ref(
        self,
        book: Optional[Book]= None,
        journal: Optional[Journal]= None,
        thesis: Optional[Thesis]= None,
        date_cit: Optional[str]= None,
        e_language: Union[None,eLanguage,str]= None,
        e_source_type: Union[None,eSourceType,str]= None,
        e_type: Union[None,eType,str]= None,
        s_abstract: Optional[str]= None,
        s_author: list[str]= [],
        s_cas_cit: Optional[str]= None,
        s_document_origin: Optional[str]= None,
        s_doi: Optional[str]= None,
        s_id_num: Optional[str]= None,
        s_keyword: list[str]= [],
        s_location: Optional[str]= None,
        s_page: Optional[str]= None,
        s_pub_name: Optional[str]= None,
        s_title: Optional[str]= None,
        s_vol: Optional[str]= None,
        trc_ref_id: Optional[TRCRefID]= None,
        url_cit: Optional[str]= None,
        yr_pub_yr: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new PredictionMethodRef to the prediction_method_ref list."""
        params = {
            "book": book,
            "journal": journal,
            "thesis": thesis,
            "date_cit": date_cit,
            "e_language": e_language,
            "e_source_type": e_source_type,
            "e_type": e_type,
            "s_abstract": s_abstract,
            "s_author": s_author,
            "s_cas_cit": s_cas_cit,
            "s_document_origin": s_document_origin,
            "s_doi": s_doi,
            "s_id_num": s_id_num,
            "s_keyword": s_keyword,
            "s_location": s_location,
            "s_page": s_page,
            "s_pub_name": s_pub_name,
            "s_title": s_title,
            "s_vol": s_vol,
            "trc_ref_id": trc_ref_id,
            "url_cit": url_cit,
            "yr_pub_yr": yr_pub_yr
        }

        self.prediction_method_ref.append(
            PredictionMethodRef(**params)
        )

        return self.prediction_method_ref[-1]
    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class PredictionMethodRef(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Prediction method reference information.
    """
    book: Optional[Book] = element(
        default= None,
        tag="book",
        description="""Book reference""",
        json_schema_extra=dict(),
    )
    journal: Optional[Journal] = element(
        default= None,
        tag="journal",
        description="""Journal reference""",
        json_schema_extra=dict(),
    )
    thesis: Optional[Thesis] = element(
        default= None,
        tag="thesis",
        description="""Thesis reference""",
        json_schema_extra=dict(),
    )
    date_cit: Optional[str] = element(
        default= None,
        tag="date_cit",
        description="""Citation date""",
        json_schema_extra=dict(),
    )
    e_language: Union[None,eLanguage,str] = element(
        default= None,
        tag="e_language",
        description="""Language""",
        json_schema_extra=dict(),
    )
    e_source_type: Union[None,eSourceType,str] = element(
        default= None,
        tag="e_source_type",
        description="""Source type""",
        json_schema_extra=dict(),
    )
    e_type: Union[None,eType,str] = element(
        default= None,
        tag="e_type",
        description="""Publication type""",
        json_schema_extra=dict(),
    )
    s_abstract: Optional[str] = element(
        default= None,
        tag="s_abstract",
        description="""Abstract""",
        json_schema_extra=dict(),
    )
    s_author: list[str] = element(
        default_factory=list,
        tag="s_author",
        description="""Authors""",
        json_schema_extra=dict(),
    )
    s_cas_cit: Optional[str] = element(
        default= None,
        tag="s_cas_cit",
        description="""CAS citation""",
        json_schema_extra=dict(),
    )
    s_document_origin: Optional[str] = element(
        default= None,
        tag="s_document_origin",
        description="""Document origin""",
        json_schema_extra=dict(),
    )
    s_doi: Optional[str] = element(
        default= None,
        tag="s_doi",
        description="""DOI""",
        json_schema_extra=dict(),
    )
    s_id_num: Optional[str] = element(
        default= None,
        tag="s_id_num",
        description="""ID number""",
        json_schema_extra=dict(),
    )
    s_keyword: list[str] = element(
        default_factory=list,
        tag="s_keyword",
        description="""Keywords""",
        json_schema_extra=dict(),
    )
    s_location: Optional[str] = element(
        default= None,
        tag="s_location",
        description="""Location""",
        json_schema_extra=dict(),
    )
    s_page: Optional[str] = element(
        default= None,
        tag="s_page",
        description="""Page range""",
        json_schema_extra=dict(),
    )
    s_pub_name: Optional[str] = element(
        default= None,
        tag="s_pub_name",
        description="""Publication name""",
        json_schema_extra=dict(),
    )
    s_title: Optional[str] = element(
        default= None,
        tag="s_title",
        description="""Title""",
        json_schema_extra=dict(),
    )
    s_vol: Optional[str] = element(
        default= None,
        tag="s_vol",
        description="""Volume""",
        json_schema_extra=dict(),
    )
    trc_ref_id: Optional[TRCRefID] = element(
        default= None,
        tag="trc_ref_id",
        description="""TRC reference ID""",
        json_schema_extra=dict(),
    )
    url_cit: Optional[str] = element(
        default= None,
        tag="url_cit",
        description="""URL citation""",
        json_schema_extra=dict(),
    )
    yr_pub_yr: Optional[str] = element(
        default= None,
        tag="yr_pub_yr",
        description="""Publication year""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class SingleProp(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Single property information.
    """
    eval_single_prop_ref: list[EvalSinglePropRef] = element(
        default_factory=list,
        tag="eval_single_prop_ref",
        description="""Single property evaluation references""",
        json_schema_extra=dict(),
    )
    s_eval_single_prop_description: Optional[str] = element(
        default= None,
        tag="s_eval_single_prop_description",
        description="""Single property evaluation description""",
        json_schema_extra=dict(),
    )


    def add_to_eval_single_prop_ref(
        self,
        book: Optional[Book]= None,
        journal: Optional[Journal]= None,
        thesis: Optional[Thesis]= None,
        date_cit: Optional[str]= None,
        e_language: Union[None,eLanguage,str]= None,
        e_source_type: Union[None,eSourceType,str]= None,
        e_type: Union[None,eType,str]= None,
        s_abstract: Optional[str]= None,
        s_author: list[str]= [],
        s_cas_cit: Optional[str]= None,
        s_document_origin: Optional[str]= None,
        s_doi: Optional[str]= None,
        s_id_num: Optional[str]= None,
        s_keyword: list[str]= [],
        s_location: Optional[str]= None,
        s_page: Optional[str]= None,
        s_pub_name: Optional[str]= None,
        s_title: Optional[str]= None,
        s_vol: Optional[str]= None,
        trc_ref_id: Optional[TRCRefID]= None,
        url_cit: Optional[str]= None,
        yr_pub_yr: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new EvalSinglePropRef to the eval_single_prop_ref list."""
        params = {
            "book": book,
            "journal": journal,
            "thesis": thesis,
            "date_cit": date_cit,
            "e_language": e_language,
            "e_source_type": e_source_type,
            "e_type": e_type,
            "s_abstract": s_abstract,
            "s_author": s_author,
            "s_cas_cit": s_cas_cit,
            "s_document_origin": s_document_origin,
            "s_doi": s_doi,
            "s_id_num": s_id_num,
            "s_keyword": s_keyword,
            "s_location": s_location,
            "s_page": s_page,
            "s_pub_name": s_pub_name,
            "s_title": s_title,
            "s_vol": s_vol,
            "trc_ref_id": trc_ref_id,
            "url_cit": url_cit,
            "yr_pub_yr": yr_pub_yr
        }

        self.eval_single_prop_ref.append(
            EvalSinglePropRef(**params)
        )

        return self.eval_single_prop_ref[-1]
    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class MultiProp(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Multiple property information.
    """
    eval_multi_prop_ref: list[EvalMultiPropRef] = element(
        default_factory=list,
        tag="eval_multi_prop_ref",
        description="""Multiple property evaluation references""",
        json_schema_extra=dict(),
    )
    s_eval_multi_prop_description: Optional[str] = element(
        default= None,
        tag="s_eval_multi_prop_description",
        description="""Multiple property evaluation description""",
        json_schema_extra=dict(),
    )
    s_eval_multi_prop_list: Optional[str] = element(
        default= None,
        tag="s_eval_multi_prop_list",
        description="""Multiple property evaluation list""",
        json_schema_extra=dict(),
    )


    def add_to_eval_multi_prop_ref(
        self,
        book: Optional[Book]= None,
        journal: Optional[Journal]= None,
        thesis: Optional[Thesis]= None,
        date_cit: Optional[str]= None,
        e_language: Union[None,eLanguage,str]= None,
        e_source_type: Union[None,eSourceType,str]= None,
        e_type: Union[None,eType,str]= None,
        s_abstract: Optional[str]= None,
        s_author: list[str]= [],
        s_cas_cit: Optional[str]= None,
        s_document_origin: Optional[str]= None,
        s_doi: Optional[str]= None,
        s_id_num: Optional[str]= None,
        s_keyword: list[str]= [],
        s_location: Optional[str]= None,
        s_page: Optional[str]= None,
        s_pub_name: Optional[str]= None,
        s_title: Optional[str]= None,
        s_vol: Optional[str]= None,
        trc_ref_id: Optional[TRCRefID]= None,
        url_cit: Optional[str]= None,
        yr_pub_yr: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new EvalMultiPropRef to the eval_multi_prop_ref list."""
        params = {
            "book": book,
            "journal": journal,
            "thesis": thesis,
            "date_cit": date_cit,
            "e_language": e_language,
            "e_source_type": e_source_type,
            "e_type": e_type,
            "s_abstract": s_abstract,
            "s_author": s_author,
            "s_cas_cit": s_cas_cit,
            "s_document_origin": s_document_origin,
            "s_doi": s_doi,
            "s_id_num": s_id_num,
            "s_keyword": s_keyword,
            "s_location": s_location,
            "s_page": s_page,
            "s_pub_name": s_pub_name,
            "s_title": s_title,
            "s_vol": s_vol,
            "trc_ref_id": trc_ref_id,
            "url_cit": url_cit,
            "yr_pub_yr": yr_pub_yr
        }

        self.eval_multi_prop_ref.append(
            EvalMultiPropRef(**params)
        )

        return self.eval_multi_prop_ref[-1]
    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class EvalSinglePropRef(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Single property evaluation reference information.
    """
    book: Optional[Book] = element(
        default= None,
        tag="book",
        description="""Book reference""",
        json_schema_extra=dict(),
    )
    journal: Optional[Journal] = element(
        default= None,
        tag="journal",
        description="""Journal reference""",
        json_schema_extra=dict(),
    )
    thesis: Optional[Thesis] = element(
        default= None,
        tag="thesis",
        description="""Thesis reference""",
        json_schema_extra=dict(),
    )
    date_cit: Optional[str] = element(
        default= None,
        tag="date_cit",
        description="""Citation date""",
        json_schema_extra=dict(),
    )
    e_language: Union[None,eLanguage,str] = element(
        default= None,
        tag="e_language",
        description="""Language""",
        json_schema_extra=dict(),
    )
    e_source_type: Union[None,eSourceType,str] = element(
        default= None,
        tag="e_source_type",
        description="""Source type""",
        json_schema_extra=dict(),
    )
    e_type: Union[None,eType,str] = element(
        default= None,
        tag="e_type",
        description="""Publication type""",
        json_schema_extra=dict(),
    )
    s_abstract: Optional[str] = element(
        default= None,
        tag="s_abstract",
        description="""Abstract""",
        json_schema_extra=dict(),
    )
    s_author: list[str] = element(
        default_factory=list,
        tag="s_author",
        description="""Authors""",
        json_schema_extra=dict(),
    )
    s_cas_cit: Optional[str] = element(
        default= None,
        tag="s_cas_cit",
        description="""CAS citation""",
        json_schema_extra=dict(),
    )
    s_document_origin: Optional[str] = element(
        default= None,
        tag="s_document_origin",
        description="""Document origin""",
        json_schema_extra=dict(),
    )
    s_doi: Optional[str] = element(
        default= None,
        tag="s_doi",
        description="""DOI""",
        json_schema_extra=dict(),
    )
    s_id_num: Optional[str] = element(
        default= None,
        tag="s_id_num",
        description="""ID number""",
        json_schema_extra=dict(),
    )
    s_keyword: list[str] = element(
        default_factory=list,
        tag="s_keyword",
        description="""Keywords""",
        json_schema_extra=dict(),
    )
    s_location: Optional[str] = element(
        default= None,
        tag="s_location",
        description="""Location""",
        json_schema_extra=dict(),
    )
    s_page: Optional[str] = element(
        default= None,
        tag="s_page",
        description="""Page range""",
        json_schema_extra=dict(),
    )
    s_pub_name: Optional[str] = element(
        default= None,
        tag="s_pub_name",
        description="""Publication name""",
        json_schema_extra=dict(),
    )
    s_title: Optional[str] = element(
        default= None,
        tag="s_title",
        description="""Title""",
        json_schema_extra=dict(),
    )
    s_vol: Optional[str] = element(
        default= None,
        tag="s_vol",
        description="""Volume""",
        json_schema_extra=dict(),
    )
    trc_ref_id: Optional[TRCRefID] = element(
        default= None,
        tag="trc_ref_id",
        description="""TRC reference ID""",
        json_schema_extra=dict(),
    )
    url_cit: Optional[str] = element(
        default= None,
        tag="url_cit",
        description="""URL citation""",
        json_schema_extra=dict(),
    )
    yr_pub_yr: Optional[str] = element(
        default= None,
        tag="yr_pub_yr",
        description="""Publication year""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class EvalMultiPropRef(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Multiple property evaluation reference information.
    """
    book: Optional[Book] = element(
        default= None,
        tag="book",
        description="""Book reference""",
        json_schema_extra=dict(),
    )
    journal: Optional[Journal] = element(
        default= None,
        tag="journal",
        description="""Journal reference""",
        json_schema_extra=dict(),
    )
    thesis: Optional[Thesis] = element(
        default= None,
        tag="thesis",
        description="""Thesis reference""",
        json_schema_extra=dict(),
    )
    date_cit: Optional[str] = element(
        default= None,
        tag="date_cit",
        description="""Citation date""",
        json_schema_extra=dict(),
    )
    e_language: Union[None,eLanguage,str] = element(
        default= None,
        tag="e_language",
        description="""Language""",
        json_schema_extra=dict(),
    )
    e_source_type: Union[None,eSourceType,str] = element(
        default= None,
        tag="e_source_type",
        description="""Source type""",
        json_schema_extra=dict(),
    )
    e_type: Union[None,eType,str] = element(
        default= None,
        tag="e_type",
        description="""Publication type""",
        json_schema_extra=dict(),
    )
    s_abstract: Optional[str] = element(
        default= None,
        tag="s_abstract",
        description="""Abstract""",
        json_schema_extra=dict(),
    )
    s_author: list[str] = element(
        default_factory=list,
        tag="s_author",
        description="""Authors""",
        json_schema_extra=dict(),
    )
    s_cas_cit: Optional[str] = element(
        default= None,
        tag="s_cas_cit",
        description="""CAS citation""",
        json_schema_extra=dict(),
    )
    s_document_origin: Optional[str] = element(
        default= None,
        tag="s_document_origin",
        description="""Document origin""",
        json_schema_extra=dict(),
    )
    s_doi: Optional[str] = element(
        default= None,
        tag="s_doi",
        description="""DOI""",
        json_schema_extra=dict(),
    )
    s_id_num: Optional[str] = element(
        default= None,
        tag="s_id_num",
        description="""ID number""",
        json_schema_extra=dict(),
    )
    s_keyword: list[str] = element(
        default_factory=list,
        tag="s_keyword",
        description="""Keywords""",
        json_schema_extra=dict(),
    )
    s_location: Optional[str] = element(
        default= None,
        tag="s_location",
        description="""Location""",
        json_schema_extra=dict(),
    )
    s_page: Optional[str] = element(
        default= None,
        tag="s_page",
        description="""Page range""",
        json_schema_extra=dict(),
    )
    s_pub_name: Optional[str] = element(
        default= None,
        tag="s_pub_name",
        description="""Publication name""",
        json_schema_extra=dict(),
    )
    s_title: Optional[str] = element(
        default= None,
        tag="s_title",
        description="""Title""",
        json_schema_extra=dict(),
    )
    s_vol: Optional[str] = element(
        default= None,
        tag="s_vol",
        description="""Volume""",
        json_schema_extra=dict(),
    )
    trc_ref_id: Optional[TRCRefID] = element(
        default= None,
        tag="trc_ref_id",
        description="""TRC reference ID""",
        json_schema_extra=dict(),
    )
    url_cit: Optional[str] = element(
        default= None,
        tag="url_cit",
        description="""URL citation""",
        json_schema_extra=dict(),
    )
    yr_pub_yr: Optional[str] = element(
        default= None,
        tag="yr_pub_yr",
        description="""Publication year""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class EquationOfState(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Equation of state information.
    """
    eval_eos_ref: list[EvalEOSRef] = element(
        default_factory=list,
        tag="eval_eos_ref",
        description="""EOS evaluation references""",
        json_schema_extra=dict(),
    )
    s_eval_eos_description: Optional[str] = element(
        default= None,
        tag="s_eval_eos_description",
        description="""EOS evaluation description""",
        json_schema_extra=dict(),
    )
    s_eval_eos_name: Optional[str] = element(
        default= None,
        tag="s_eval_eos_name",
        description="""EOS evaluation name""",
        json_schema_extra=dict(),
    )


    def add_to_eval_eos_ref(
        self,
        book: Optional[Book]= None,
        journal: Optional[Journal]= None,
        thesis: Optional[Thesis]= None,
        date_cit: Optional[str]= None,
        e_language: Union[None,eLanguage,str]= None,
        e_source_type: Union[None,eSourceType,str]= None,
        e_type: Union[None,eType,str]= None,
        s_abstract: Optional[str]= None,
        s_author: list[str]= [],
        s_cas_cit: Optional[str]= None,
        s_document_origin: Optional[str]= None,
        s_doi: Optional[str]= None,
        s_id_num: Optional[str]= None,
        s_keyword: list[str]= [],
        s_location: Optional[str]= None,
        s_page: Optional[str]= None,
        s_pub_name: Optional[str]= None,
        s_title: Optional[str]= None,
        s_vol: Optional[str]= None,
        trc_ref_id: Optional[TRCRefID]= None,
        url_cit: Optional[str]= None,
        yr_pub_yr: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new EvalEOSRef to the eval_eos_ref list."""
        params = {
            "book": book,
            "journal": journal,
            "thesis": thesis,
            "date_cit": date_cit,
            "e_language": e_language,
            "e_source_type": e_source_type,
            "e_type": e_type,
            "s_abstract": s_abstract,
            "s_author": s_author,
            "s_cas_cit": s_cas_cit,
            "s_document_origin": s_document_origin,
            "s_doi": s_doi,
            "s_id_num": s_id_num,
            "s_keyword": s_keyword,
            "s_location": s_location,
            "s_page": s_page,
            "s_pub_name": s_pub_name,
            "s_title": s_title,
            "s_vol": s_vol,
            "trc_ref_id": trc_ref_id,
            "url_cit": url_cit,
            "yr_pub_yr": yr_pub_yr
        }

        self.eval_eos_ref.append(
            EvalEOSRef(**params)
        )

        return self.eval_eos_ref[-1]
    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class EvalEOSRef(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: EOS evaluation reference information.
    """
    book: Optional[Book] = element(
        default= None,
        tag="book",
        description="""Book reference""",
        json_schema_extra=dict(),
    )
    journal: Optional[Journal] = element(
        default= None,
        tag="journal",
        description="""Journal reference""",
        json_schema_extra=dict(),
    )
    thesis: Optional[Thesis] = element(
        default= None,
        tag="thesis",
        description="""Thesis reference""",
        json_schema_extra=dict(),
    )
    date_cit: Optional[str] = element(
        default= None,
        tag="date_cit",
        description="""Citation date""",
        json_schema_extra=dict(),
    )
    e_language: Union[None,eLanguage,str] = element(
        default= None,
        tag="e_language",
        description="""Language""",
        json_schema_extra=dict(),
    )
    e_source_type: Union[None,eSourceType,str] = element(
        default= None,
        tag="e_source_type",
        description="""Source type""",
        json_schema_extra=dict(),
    )
    e_type: Union[None,eType,str] = element(
        default= None,
        tag="e_type",
        description="""Publication type""",
        json_schema_extra=dict(),
    )
    s_abstract: Optional[str] = element(
        default= None,
        tag="s_abstract",
        description="""Abstract""",
        json_schema_extra=dict(),
    )
    s_author: list[str] = element(
        default_factory=list,
        tag="s_author",
        description="""Authors""",
        json_schema_extra=dict(),
    )
    s_cas_cit: Optional[str] = element(
        default= None,
        tag="s_cas_cit",
        description="""CAS citation""",
        json_schema_extra=dict(),
    )
    s_document_origin: Optional[str] = element(
        default= None,
        tag="s_document_origin",
        description="""Document origin""",
        json_schema_extra=dict(),
    )
    s_doi: Optional[str] = element(
        default= None,
        tag="s_doi",
        description="""DOI""",
        json_schema_extra=dict(),
    )
    s_id_num: Optional[str] = element(
        default= None,
        tag="s_id_num",
        description="""ID number""",
        json_schema_extra=dict(),
    )
    s_keyword: list[str] = element(
        default_factory=list,
        tag="s_keyword",
        description="""Keywords""",
        json_schema_extra=dict(),
    )
    s_location: Optional[str] = element(
        default= None,
        tag="s_location",
        description="""Location""",
        json_schema_extra=dict(),
    )
    s_page: Optional[str] = element(
        default= None,
        tag="s_page",
        description="""Page range""",
        json_schema_extra=dict(),
    )
    s_pub_name: Optional[str] = element(
        default= None,
        tag="s_pub_name",
        description="""Publication name""",
        json_schema_extra=dict(),
    )
    s_title: Optional[str] = element(
        default= None,
        tag="s_title",
        description="""Title""",
        json_schema_extra=dict(),
    )
    s_vol: Optional[str] = element(
        default= None,
        tag="s_vol",
        description="""Volume""",
        json_schema_extra=dict(),
    )
    trc_ref_id: Optional[TRCRefID] = element(
        default= None,
        tag="trc_ref_id",
        description="""TRC reference ID""",
        json_schema_extra=dict(),
    )
    url_cit: Optional[str] = element(
        default= None,
        tag="url_cit",
        description="""URL citation""",
        json_schema_extra=dict(),
    )
    yr_pub_yr: Optional[str] = element(
        default= None,
        tag="yr_pub_yr",
        description="""Publication year""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class EqProperty(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Equation property information.
    """
    n_prop_number: Optional[int] = element(
        default= None,
        tag="n_prop_number",
        description="""Property number""",
        json_schema_extra=dict(),
    )
    n_pure_or_mixture_data_number: Optional[int] = element(
        default= None,
        tag="n_pure_or_mixture_data_number",
        description="""Pure or mixture data number""",
        json_schema_extra=dict(),
    )
    n_reaction_data_number: Optional[int] = element(
        default= None,
        tag="n_reaction_data_number",
        description="""Reaction data number""",
        json_schema_extra=dict(),
    )
    s_eq_symbol: Optional[str] = element(
        default= None,
        tag="s_eq_symbol",
        description="""Equation symbol""",
        json_schema_extra=dict(),
    )
    n_eq_prop_index: list[int] = element(
        default_factory=list,
        tag="n_eq_prop_index",
        description="""Equation property index""",
        json_schema_extra=dict(),
    )
    n_eq_prop_range_max: Optional[float] = element(
        default= None,
        tag="n_eq_prop_range_max",
        description="""Equation property range maximum""",
        json_schema_extra=dict(),
    )
    n_eq_prop_range_min: Optional[float] = element(
        default= None,
        tag="n_eq_prop_range_min",
        description="""Equation property range minimum""",
        json_schema_extra=dict(),
    )
    s_other_prop_unit: Optional[str] = element(
        default= None,
        tag="s_other_prop_unit",
        description="""Other property unit""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class EqConstraint(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Equation constraint information.
    """
    n_constraint_number: Optional[int] = element(
        default= None,
        tag="n_constraint_number",
        description="""Constraint number""",
        json_schema_extra=dict(),
    )
    n_pure_or_mixture_data_number: Optional[int] = element(
        default= None,
        tag="n_pure_or_mixture_data_number",
        description="""Pure or mixture data number""",
        json_schema_extra=dict(),
    )
    n_reaction_data_number: Optional[int] = element(
        default= None,
        tag="n_reaction_data_number",
        description="""Reaction data number""",
        json_schema_extra=dict(),
    )
    s_eq_symbol: Optional[str] = element(
        default= None,
        tag="s_eq_symbol",
        description="""Equation symbol""",
        json_schema_extra=dict(),
    )
    n_eq_constraint_index: list[int] = element(
        default_factory=list,
        tag="n_eq_constraint_index",
        description="""Equation constraint index""",
        json_schema_extra=dict(),
    )
    n_eq_constraint_range_max: Optional[float] = element(
        default= None,
        tag="n_eq_constraint_range_max",
        description="""Equation constraint range maximum""",
        json_schema_extra=dict(),
    )
    n_eq_constraint_range_min: Optional[float] = element(
        default= None,
        tag="n_eq_constraint_range_min",
        description="""Equation constraint range minimum""",
        json_schema_extra=dict(),
    )
    s_other_constraint_unit: Optional[str] = element(
        default= None,
        tag="s_other_constraint_unit",
        description="""Other constraint unit""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class EqVariable(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Equation variable information.
    """
    n_pure_or_mixture_data_number: Optional[int] = element(
        default= None,
        tag="n_pure_or_mixture_data_number",
        description="""Pure or mixture data number""",
        json_schema_extra=dict(),
    )
    n_reaction_data_number: Optional[int] = element(
        default= None,
        tag="n_reaction_data_number",
        description="""Reaction data number""",
        json_schema_extra=dict(),
    )
    n_var_number: Optional[int] = element(
        default= None,
        tag="n_var_number",
        description="""Variable number""",
        json_schema_extra=dict(),
    )
    s_eq_symbol: Optional[str] = element(
        default= None,
        tag="s_eq_symbol",
        description="""Equation symbol""",
        json_schema_extra=dict(),
    )
    n_eq_var_index: list[int] = element(
        default_factory=list,
        tag="n_eq_var_index",
        description="""Equation variable index""",
        json_schema_extra=dict(),
    )
    n_eq_var_range_max: Optional[float] = element(
        default= None,
        tag="n_eq_var_range_max",
        description="""Equation variable range maximum""",
        json_schema_extra=dict(),
    )
    n_eq_var_range_min: Optional[float] = element(
        default= None,
        tag="n_eq_var_range_min",
        description="""Equation variable range minimum""",
        json_schema_extra=dict(),
    )
    s_other_var_unit: Optional[str] = element(
        default= None,
        tag="s_other_var_unit",
        description="""Other variable unit""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class EqParameter(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Equation parameter information.
    """
    n_eq_par_digits: Optional[int] = element(
        default= None,
        tag="n_eq_par_digits",
        description="""Equation parameter digits""",
        json_schema_extra=dict(),
    )
    n_eq_par_value: Optional[float] = element(
        default= None,
        tag="n_eq_par_value",
        description="""Equation parameter value""",
        json_schema_extra=dict(),
    )
    s_eq_par_symbol: Optional[str] = element(
        default= None,
        tag="s_eq_par_symbol",
        description="""Equation parameter symbol""",
        json_schema_extra=dict(),
    )
    n_eq_par_index: list[int] = element(
        default_factory=list,
        tag="n_eq_par_index",
        description="""Equation parameter index""",
        json_schema_extra=dict(),
    )
    n_eq_par_number: Optional[int] = element(
        default= None,
        tag="n_eq_par_number",
        description="""Equation parameter number""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class EqConstant(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Equation constant information.
    """
    n_eq_constant_digits: Optional[int] = element(
        default= None,
        tag="n_eq_constant_digits",
        description="""Equation constant digits""",
        json_schema_extra=dict(),
    )
    n_eq_constant_value: Optional[float] = element(
        default= None,
        tag="n_eq_constant_value",
        description="""Equation constant value""",
        json_schema_extra=dict(),
    )
    s_eq_constant_symbol: Optional[str] = element(
        default= None,
        tag="s_eq_constant_symbol",
        description="""Equation constant symbol""",
        json_schema_extra=dict(),
    )
    n_eq_constant_index: list[int] = element(
        default_factory=list,
        tag="n_eq_constant_index",
        description="""Equation constant index""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class Covariance(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Covariance information.
    """
    n_covariance_value: Optional[float] = element(
        default= None,
        tag="n_covariance_value",
        description="""Covariance value""",
        json_schema_extra=dict(),
    )
    n_eq_par_number1: Optional[int] = element(
        default= None,
        tag="n_eq_par_number1",
        description="""First equation parameter number""",
        json_schema_extra=dict(),
    )
    n_eq_par_number2: Optional[int] = element(
        default= None,
        tag="n_eq_par_number2",
        description="""Second equation parameter number""",
        json_schema_extra=dict(),
    )


    def xml(self, encoding: str = "unicode") -> str | bytes:
        """Converts the object to an XML string

        Args:
            encoding (str, optional): The encoding to use. If set to "bytes", will return a bytes string.
                                      Defaults to "unicode".

        Returns:
            str | bytes: The XML representation of the object
        """
        if encoding == "bytes":
            return self.to_xml()

        raw_xml = self.to_xml(encoding=None)
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ")


class eType(Enum):
    """Enumeration for eType values"""
    ARCHIVEDDOCUMENT = "'archivedDocument'"
    BOOK = "'book'"
    CONFERENCEPROCEEDINGS = "'conferenceProceedings'"
    JOURNAL = "'journal'"
    PATENT = "'patent'"
    PERSONALCORRESPONDENCE = "'personalCorrespondence'"
    PUBLISHEDTRANSLATION = "'publishedTranslation'"
    REPORT = "'report'"
    THESIS = "'thesis'"
    UNSPECIFIED = "'unspecified'"

class eSourceType(Enum):
    """Enumeration for eSourceType values"""
    CHEMICALABSTRACTS = "'ChemicalAbstracts'"
    ORIGINAL = "'Original'"
    OTHER = "'Other'"

class eLanguage(Enum):
    """Enumeration for eLanguage values"""
    CHINESE = "'Chinese'"
    ENGLISH = "'English'"
    FRENCH = "'French'"
    GERMAN = "'German'"
    JAPANESE = "'Japanese'"
    OTHER_LANGUAGE = "'Other language'"
    POLISH = "'Polish'"
    RUSSIAN = "'Russian'"

class eSpeciationState(Enum):
    """Enumeration for eSpeciationState values"""
    EQUILIBRIUM = "'equilibrium'"
    SINGLE_SPECIES = "'single species'"

class eSource(Enum):
    """Enumeration for eSource values"""
    COMMERCIAL_SOURCE = "'Commercial source'"
    ISOLATED_FROM_A_NATURAL_PRODUCT = "'Isolated from a natural product'"
    NO_SAMPLE_USED = "'No sample used'"
    NOT_STATED_IN_THE_DOCUMENT = "'Not stated in the document'"
    STANDARD_REFERENCE_MATERIAL_SRM = "'Standard Reference Material (SRM)'"
    SYNTHESIZED_BY_OTHERS = "'Synthesized by others'"
    SYNTHESIZED_BY_THE_AUTHORS = "'Synthesized by the authors'"

class eStatus(Enum):
    """Enumeration for eStatus values"""
    NOSAMPLE = "'noSample'"
    NOTDESCRIBED = "'notDescribed'"
    PREVIOUSPAPER = "'previousPaper'"
    UNKNOWN = "'unknown'"

class ePurifMethod(Enum):
    """Enumeration for ePurifMethod values"""
    CHEMICAL_REAGENT_TREATMENT = "'Chemical reagent treatment'"
    CRYSTALLIZATION_FROM_MELT = "'Crystallization from melt'"
    CRYSTALLIZATION_FROM_SOLUTION = "'Crystallization from solution'"
    DEGASSED_BY_BOILING_OR_ULTRASONICALLY = "'De-gassed by boiling or ultrasonically'"
    DEGASSED_BY_EVACUATION = "'De-gassed by evacuation'"
    DEGASSED_BY_FREEZING_AND_MELTING_IN_VACUUM = "'De-gassed by freezing and melting in vacuum'"
    DRIED_BY_OVEN_HEATING = "'Dried by oven heating'"
    DRIED_BY_VACUUM_HEATING = "'Dried by vacuum heating'"
    DRIED_IN_A_DESICCATOR = "'Dried in a desiccator'"
    DRIED_WITH_CHEMICAL_REAGENT = "'Dried with chemical reagent'"
    FRACTIONAL_CRYSTALLIZATION = "'Fractional crystallization'"
    FRACTIONAL_DISTILLATION = "'Fractional distillation'"
    IMPURITY_ADSORPTION = "'Impurity adsorption'"
    LIQUID_CHROMATOGRAPHY = "'Liquid chromatography'"
    MOLECULAR_SIEVE_TREATMENT = "'Molecular sieve treatment'"
    NONE_USED = "'None used'"
    OTHER = "'Other'"
    PREPARATIVE_GAS_CHROMATOGRAPHY = "'Preparative gas chromatography'"
    SALTING_OUT_OF_SOLUTION = "'Salting out of solution'"
    SOLVENT_EXTRACTION = "'Solvent extraction'"
    STEAM_DISTILLATION = "'Steam distillation'"
    SUBLIMATION = "'Sublimation'"
    UNSPECIFIED = "'Unspecified'"
    VACUUM_DEGASIFICATION = "'Vacuum degasification'"
    ZONE_REFINING = "'Zone refining'"

class eAnalMeth(Enum):
    """Enumeration for eAnalMeth values"""
    ACIDBASE_TITRATION = "'Acid-base titration'"
    CHEMICAL_ANALYSIS = "'Chemical analysis'"
    CO2_YIELD_IN_COMBUSTION_PRODUCTS = "'CO2 yield in combustion products'"
    DENSITY = "'Density'"
    DIFFERENCE_BETWEEN_BUBBLE_AND_DEW_TEMPERATURES = "'Difference between bubble and dew temperatures'"
    DSC = "'DSC'"
    ESTIMATED_BY_THE_COMPILER = "'Estimated by the compiler'"
    ESTIMATION = "'Estimation'"
    FRACTION_MELTING_IN_AN_ADIABATIC_CALORIMETER = "'Fraction melting in an adiabatic calorimeter'"
    GAS_CHROMATOGRAPHY = "'Gas chromatography'"
    HPLC = "'HPLC'"
    ION_CHROMATOGRAPHY = "'Ion chromatography'"
    IONSELECTIVE_ELECTRODE = "'Ion-selective electrode'"
    KARL_FISCHER_TITRATION = "'Karl Fischer titration'"
    MASS_LOSS_ON_DRYING = "'Mass loss on drying'"
    MASS_SPECTROMETRY = "'Mass spectrometry'"
    NMR_OTHER = "'NMR (other)'"
    NMR_PROTON = "'NMR (proton)'"
    NOT_KNOWN = "'Not known'"
    OTHER = "'Other'"
    OTHER_TYPES_OF_TITRATION = "'Other types of titration'"
    SPECTROSCOPY = "'Spectroscopy'"
    STATED_BY_SUPPLIER = "'Stated by supplier'"
    THERMAL_ANALYSIS_USING_TEMPERATURETIME_MEASUREMENT = "'Thermal analysis using temperature-time measurement'"

class eFunction(Enum):
    """Enumeration for eFunction values"""
    BUFFER = "'Buffer'"
    COFACTOR = "'Cofactor'"
    INERT = "'Inert'"

class eExpPurpose(Enum):
    """Enumeration for eExpPurpose values"""
    DETERMINED_FOR_IDENTIFICATION_OF_A_SYNTHESIZED_COMPOUND = "'Determined for identification of a synthesized compound'"
    PRINCIPAL_OBJECTIVE_OF_THE_WORK = "'Principal objective of the work'"
    SECONDARY_PURPOSE_BYPRODUCT_OF_OTHER_OBJECTIVE = "'Secondary purpose (by-product of other objective)'"

class ePropName(Enum):
    """Enumeration for ePropName values"""
    DECADIC_LOGARITHM_OF_EQUILIBRIUM_CONSTANT_IN_TERMS_OF_AMOUNT_CONCENTRATION_MOLARITY_MOLDM3N = "'Decadic logarithm of equilibrium constant in terms of amount concentration (molarity), (mol/dm3)^n'"
    DECADIC_LOGARITHM_OF_EQUILIBRIUM_CONSTANT_IN_TERMS_OF_MOLALITY_MOLKGN = "'Decadic logarithm of equilibrium constant in terms of molality, (mol/kg)^n'"
    DECADIC_LOGARITHM_OF_EQUILIBRIUM_CONSTANT_IN_TERMS_OF_MOLE_FRACTION = "'Decadic logarithm of equilibrium constant in terms of mole fraction'"
    DECADIC_LOGARITHM_OF_EQUILIBRIUM_CONSTANT_IN_TERMS_OF_PARTIAL_PRESSURE_KPAN = "'Decadic logarithm of equilibrium constant in terms of partial pressure, kPa^n'"
    DECADIC_LOGARITHM_OF_THERMODYNAMIC_EQUILIBRIUM_CONSTANT = "'Decadic logarithm of thermodynamic equilibrium constant'"
    EQUILIBRIUM_CONSTANT_IN_TERMS_OF_AMOUNT_CONCENTRATION_MOLARITY_MOLDM3N = "'Equilibrium constant in terms of amount concentration (molarity), (mol/dm3)^n'"
    EQUILIBRIUM_CONSTANT_IN_TERMS_OF_MOLALITY_MOLKGN = "'Equilibrium constant in terms of molality, (mol/kg)^n'"
    EQUILIBRIUM_CONSTANT_IN_TERMS_OF_MOLE_FRACTION = "'Equilibrium constant in terms of mole fraction'"
    EQUILIBRIUM_CONSTANT_IN_TERMS_OF_PARTIAL_PRESSURE_KPAN = "'Equilibrium constant in terms of partial pressure, kPa^n'"
    NATURAL_LOGARITHM_OF_EQUILIBRIUM_CONSTANT_IN_TERMS_OF_AMOUNT_CONCENTRATION_MOLARITY_MOLDM3N = "'Natural logarithm of equilibrium constant in terms of amount concentration (molarity), (mol/dm3)^n'"
    NATURAL_LOGARITHM_OF_EQUILIBRIUM_CONSTANT_IN_TERMS_OF_MOLALITY_MOLKGN = "'Natural logarithm of equilibrium constant in terms of molality, (mol/kg)^n'"
    NATURAL_LOGARITHM_OF_EQUILIBRIUM_CONSTANT_IN_TERMS_OF_MOLE_FRACTION = "'Natural logarithm of equilibrium constant in terms of mole fraction'"
    NATURAL_LOGARITHM_OF_EQUILIBRIUM_CONSTANT_IN_TERMS_OF_PARTIAL_PRESSURE_KPAN = "'Natural logarithm of equilibrium constant in terms of partial pressure, kPa^n'"
    NATURAL_LOGARITHM_OF_THERMODYNAMIC_EQUILIBRIUM_CONSTANT = "'Natural logarithm of thermodynamic equilibrium constant'"
    THERMODYNAMIC_EQUILIBRIUM_CONSTANT = "'Thermodynamic equilibrium constant'"

class eMethodName(Enum):
    """Enumeration for eMethodName values"""
    ANION_EXCHANGE = "'Anion exchange'"
    CATION_EXCHANGE = "'Cation exchange'"
    CELL_POTENTIAL_WITH_GLASS_ELECTRODE = "'Cell potential with glass electrode'"
    CELL_POTENTIAL_WITH_PLATINUM_ELECTRODE = "'Cell potential with platinum electrode'"
    CELL_POTENTIAL_WITH_QUINHYDRONE_ELECTRODE = "'Cell potential with quinhydrone electrode'"
    CELL_POTENTIAL_WITH_REDOX_ELECTRODE = "'Cell potential with redox electrode'"
    CHROMATOGRAPHY = "'Chromatography'"
    COLORIMETRY = "'Colorimetry'"
    CONDUCTIVITY_MEASUREMENT = "'Conductivity measurement'"
    COULOMETRY = "'Coulometry'"
    CRYOSCOPY = "'Cryoscopy'"
    DISTRIBUTION_BETWEEN_TWO_PHASES = "'Distribution between two phases'"
    DYNAMIC_EQUILIBRATION = "'Dynamic equilibration'"
    ION_SELECTIVE_ELECTRODE = "'Ion selective electrode'"
    IR_SPECTROMETRY = "'IR spectrometry'"
    MOLAR_VOLUME_DETERMINATION = "'Molar volume determination'"
    NMR_SPECTROMETRY = "'NMR spectrometry'"
    OTHER = "'Other'"
    POLAROGRAPHY = "'Polarography'"
    POTENTIAL_DIFFERENCE_OF_AN_ELECTROCHEMICAL_CELL = "'Potential difference of an electrochemical cell'"
    POTENTIOMETRY = "'Potentiometry'"
    PROTON_RELAXATION = "'Proton relaxation'"
    RATE_OF_REACTION = "'Rate of reaction'"
    SOLUBILITY_MEASUREMENT = "'Solubility measurement'"
    SOLVENT_EXTRACTION = "'Solvent extraction'"
    SPECTROPHOTOMETRY = "'Spectrophotometry'"
    STATIC_EQUILIBRATION = "'Static equilibration'"
    THERMAL_LENSING_SPECTROPHOTOMETRY = "'Thermal lensing spectrophotometry'"
    TITRATION = "'Titration'"
    TRANSIENT_CONDUCTIVITY_MEASUREMENT = "'Transient conductivity measurement'"
    UV_SPECTROSCOPY = "'UV spectroscopy'"
    VOLTAMMETRY = "'Voltammetry'"

class ePredictionType(Enum):
    """Enumeration for ePredictionType values"""
    AB_INITIO = "'Ab initio'"
    CORRELATION = "'Correlation'"
    CORRESPONDING_STATES = "'Corresponding states'"
    GROUP_CONTRIBUTION = "'Group contribution'"
    MOLECULAR_DYNAMICS = "'Molecular dynamics'"
    MOLECULAR_MECHANICS = "'Molecular mechanics'"
    SEMIEMPIRICAL_QUANTUM_METHODS = "'Semiempirical quantum methods'"
    STATISTICAL_MECHANICS = "'Statistical mechanics'"

class ePropPhase(Enum):
    """Enumeration for ePropPhase values"""
    AIR_AT_1_ATMOSPHERE = "'Air at 1 atmosphere'"
    CHOLESTERIC_LIQUID_CRYSTAL = "'Cholesteric liquid crystal'"
    CRYSTAL = "'Crystal'"
    CRYSTAL_1 = "'Crystal 1'"
    CRYSTAL_2 = "'Crystal 2'"
    CRYSTAL_3 = "'Crystal 3'"
    CRYSTAL_4 = "'Crystal 4'"
    CRYSTAL_5 = "'Crystal 5'"
    CRYSTAL_OF_INTERCOMPONENT_COMPOUND_1 = "'Crystal of intercomponent compound 1'"
    CRYSTAL_OF_INTERCOMPONENT_COMPOUND_2 = "'Crystal of intercomponent compound 2'"
    CRYSTAL_OF_INTERCOMPONENT_COMPOUND_3 = "'Crystal of intercomponent compound 3'"
    CRYSTAL_OF_UNKNOWN_TYPE = "'Crystal of unknown type'"
    FLUID_SUPERCRITICAL_OR_SUBCRITICAL_PHASES = "'Fluid (supercritical or subcritical phases)'"
    GAS = "'Gas'"
    GLASS = "'Glass'"
    IDEAL_GAS = "'Ideal gas'"
    LIQUID = "'Liquid'"
    LIQUID_CRYSTAL_OF_UNKNOWN_TYPE = "'Liquid crystal of unknown type'"
    LIQUID_MIXTURE_1 = "'Liquid mixture 1'"
    LIQUID_MIXTURE_2 = "'Liquid mixture 2'"
    LIQUID_MIXTURE_3 = "'Liquid mixture 3'"
    METASTABLE_CRYSTAL = "'Metastable crystal'"
    NEMATIC_LIQUID_CRYSTAL = "'Nematic liquid crystal'"
    NEMATIC_LIQUID_CRYSTAL_1 = "'Nematic liquid crystal 1'"
    NEMATIC_LIQUID_CRYSTAL_2 = "'Nematic liquid crystal 2'"
    SMECTIC_LIQUID_CRYSTAL = "'Smectic liquid crystal'"
    SMECTIC_LIQUID_CRYSTAL_1 = "'Smectic liquid crystal 1'"
    SMECTIC_LIQUID_CRYSTAL_2 = "'Smectic liquid crystal 2'"
    SOLUTION = "'Solution'"
    SOLUTION_1 = "'Solution 1'"
    SOLUTION_2 = "'Solution 2'"
    SOLUTION_3 = "'Solution 3'"
    SOLUTION_4 = "'Solution 4'"

class eCrystalLatticeType(Enum):
    """Enumeration for eCrystalLatticeType values"""
    CUBIC = "'Cubic'"
    HEXAGONAL = "'Hexagonal'"
    MONOCLINIC = "'Monoclinic'"
    ORTHORHOMBIC = "'Orthorhombic'"
    RHOMBOHEDRAL = "'Rhombohedral'"
    TETRAGONAL = "'Tetragonal'"
    TRICLINIC = "'Triclinic'"

class eBioState(Enum):
    """Enumeration for eBioState values"""
    DENATURATED = "'Denaturated'"
    NATIVE = "'Native'"

class ePresentation(Enum):
    """Enumeration for ePresentation values"""
    DIFFERENCE_BETWEEN_UPPER_AND_LOWER_PRESSURE_XP2XP1 = "'Difference between upper and lower pressure, X(P2)-X(P1)'"
    DIFFERENCE_BETWEEN_UPPER_AND_LOWER_TEMPERATURE_XT2XT1 = "'Difference between upper and lower temperature, X(T2)-X(T1)'"
    DIFFERENCE_WITH_THE_REFERENCE_STATE_XXREF = "'Difference with the reference state, X-X(REF)'"
    DIRECT_VALUE_X = "'Direct value, X'"
    MEAN_BETWEEN_UPPER_AND_LOWER_TEMPERATURE_XT2XT12 = "'Mean between upper and lower temperature, [X(T2)+X(T1)]/2'"
    RATIO_OF_DIFFERENCE_WITH_THE_REFERENCE_STATE_TO_THE_REFERENCE_STATE_XXREFXREF = "'Ratio of difference with the reference state to the reference state, [X-X(REF)]/X(REF)'"
    RATIO_WITH_THE_REFERENCE_STATE_XXREF = "'Ratio with the reference state, X/X(REF)'"

class eRefStateType(Enum):
    """Enumeration for eRefStateType values"""
    IDEAL_GAS_AT_THE_SAME_AMOUNT_DENSITY_TEMPERATURE_AND_COMPOSITION = "'Ideal gas at the same amount density, temperature, and composition'"
    IDEAL_MIXTURE_OF_PURE_FLUID_COMPONENTS_AT_THE_SAME_AMOUNT_DENSITY_TEMPERATURE_AND_COMPOSITION = "'Ideal mixture of pure fluid components at the same amount density, temperature, and composition'"
    PHASE_IN_EQUILIBRIUM_WITH_PRIMARY_PHASE_AT_THE_SAME_TEMPERATURE_AND_PRESSURE = "'Phase in equilibrium with primary phase at the same temperature and pressure'"
    PURE_COMPONENTS_IN_THE_SAME_PROPORTION_AT_FIXED_TEMPERATURE_AND_PRESSURE = "'Pure components in the same proportion at fixed temperature and pressure'"
    PURE_COMPONENTS_IN_THE_SAME_PROPORTION_AT_THE_SAME_TEMPERATURE_AND_PRESSURE = "'Pure components in the same proportion at the same temperature and pressure'"
    PURE_SOLUTE_AT_THE_SAME_TEMPERATURE_AND_PRESSURE = "'Pure solute at the same temperature and pressure'"
    PURE_SOLVENT_AT_THE_SAME_TEMPERATURE_AND_PRESSURE = "'Pure solvent at the same temperature and pressure'"
    PURE_SOLVENT_AT_THE_TEMPERATURE_OF_THE_SAME_PHASE_EQUILIBRIUM = "'Pure solvent at the temperature of the same phase equilibrium'"
    REFERENCE_PHASE_AT_FIXED_TEMPERATURE_AND_THE_SAME_PRESSURE = "'Reference phase at fixed temperature and the same pressure'"
    REFERENCE_PHASE_AT_THE_SAME_TEMPERATURE_AND_FIXED_PRESSURE = "'Reference phase at the same temperature and fixed pressure'"
    REFERENCE_PHASE_WITH_THE_SAME_COMPOSITION_AT_FIXED_TEMPERATURE_AND_PRESSURE = "'Reference phase with the same composition at fixed temperature and pressure'"
    REFERENCE_PHASE_WITH_THE_SAME_COMPOSITION_TEMPERATURE_AND_PRESSURE = "'Reference phase with the same composition, temperature and pressure'"

class eRefPhase(Enum):
    """Enumeration for eRefPhase values"""
    AIR_AT_1_ATMOSPHERE = "'Air at 1 atmosphere'"
    CHOLESTERIC_LIQUID_CRYSTAL = "'Cholesteric liquid crystal'"
    CRYSTAL = "'Crystal'"
    CRYSTAL_1 = "'Crystal 1'"
    CRYSTAL_2 = "'Crystal 2'"
    CRYSTAL_3 = "'Crystal 3'"
    CRYSTAL_4 = "'Crystal 4'"
    CRYSTAL_5 = "'Crystal 5'"
    CRYSTAL_OF_INTERCOMPONENT_COMPOUND_1 = "'Crystal of intercomponent compound 1'"
    CRYSTAL_OF_INTERCOMPONENT_COMPOUND_2 = "'Crystal of intercomponent compound 2'"
    CRYSTAL_OF_INTERCOMPONENT_COMPOUND_3 = "'Crystal of intercomponent compound 3'"
    CRYSTAL_OF_UNKNOWN_TYPE = "'Crystal of unknown type'"
    FLUID_SUPERCRITICAL_OR_SUBCRITICAL_PHASES = "'Fluid (supercritical or subcritical phases)'"
    GAS = "'Gas'"
    GLASS = "'Glass'"
    IDEAL_GAS = "'Ideal gas'"
    LIQUID = "'Liquid'"
    LIQUID_CRYSTAL_OF_UNKNOWN_TYPE = "'Liquid crystal of unknown type'"
    LIQUID_MIXTURE_1 = "'Liquid mixture 1'"
    LIQUID_MIXTURE_2 = "'Liquid mixture 2'"
    LIQUID_MIXTURE_3 = "'Liquid mixture 3'"
    METASTABLE_CRYSTAL = "'Metastable crystal'"
    NEMATIC_LIQUID_CRYSTAL = "'Nematic liquid crystal'"
    NEMATIC_LIQUID_CRYSTAL_1 = "'Nematic liquid crystal 1'"
    NEMATIC_LIQUID_CRYSTAL_2 = "'Nematic liquid crystal 2'"
    SMECTIC_LIQUID_CRYSTAL = "'Smectic liquid crystal'"
    SMECTIC_LIQUID_CRYSTAL_1 = "'Smectic liquid crystal 1'"
    SMECTIC_LIQUID_CRYSTAL_2 = "'Smectic liquid crystal 2'"
    SOLUTION = "'Solution'"
    SOLUTION_1 = "'Solution 1'"
    SOLUTION_2 = "'Solution 2'"
    SOLUTION_3 = "'Solution 3'"
    SOLUTION_4 = "'Solution 4'"

class eStandardState(Enum):
    """Enumeration for eStandardState values"""
    INFINITE_DILUTION_SOLUTE = "'Infinite dilution solute'"
    PURE_COMPOUND = "'Pure compound'"
    PURE_LIQUID_SOLUTE = "'Pure liquid solute'"
    STANDARD_AMOUNT_CONCENTRATION_1_MOLDM3_SOLUTE = "'Standard amount concentration (1 mol/dm3) solute'"
    STANDARD_MOLALITY_1_MOLKG_SOLUTE = "'Standard molality (1 mol/kg) solute'"

class eCombUncertEvalMethod(Enum):
    """Enumeration for eCombUncertEvalMethod values"""
    COMPARISON_WITH_REFERENCE_PROPERTY_VALUES = "'Comparison with reference property values'"
    PROPAGATION_OF_EVALUATED_STANDARD_UNCERTAINTIES = "'Propagation of evaluated standard uncertainties'"

class eRepeatMethod(Enum):
    """Enumeration for eRepeatMethod values"""
    OTHER = "'Other'"
    STANDARD_DEVIATION_OF_A_SINGLE_VALUE_BIASED = "'Standard deviation of a single value (biased)'"
    STANDARD_DEVIATION_OF_A_SINGLE_VALUE_UNBIASED = "'Standard deviation of a single value (unbiased)'"
    STANDARD_DEVIATION_OF_THE_MEAN = "'Standard deviation of the mean'"

class eDeviceSpecMethod(Enum):
    """Enumeration for eDeviceSpecMethod values"""
    CALIBRATED_BY_THE_EXPERIMENTALIST = "'Calibrated by the experimentalist'"
    CERTIFIED_OR_CALIBRATED_BY_A_THIRD_PARTY = "'Certified or calibrated by a third party'"
    SPECIFIED_BY_THE_MANUFACTURER = "'Specified by the manufacturer'"

class ePhase(Enum):
    """Enumeration for ePhase values"""
    AIR_AT_1_ATMOSPHERE = "'Air at 1 atmosphere'"
    CHOLESTERIC_LIQUID_CRYSTAL = "'Cholesteric liquid crystal'"
    CRYSTAL = "'Crystal'"
    CRYSTAL_1 = "'Crystal 1'"
    CRYSTAL_2 = "'Crystal 2'"
    CRYSTAL_3 = "'Crystal 3'"
    CRYSTAL_4 = "'Crystal 4'"
    CRYSTAL_5 = "'Crystal 5'"
    CRYSTAL_OF_INTERCOMPONENT_COMPOUND_1 = "'Crystal of intercomponent compound 1'"
    CRYSTAL_OF_INTERCOMPONENT_COMPOUND_2 = "'Crystal of intercomponent compound 2'"
    CRYSTAL_OF_INTERCOMPONENT_COMPOUND_3 = "'Crystal of intercomponent compound 3'"
    CRYSTAL_OF_UNKNOWN_TYPE = "'Crystal of unknown type'"
    FLUID_SUPERCRITICAL_OR_SUBCRITICAL_PHASES = "'Fluid (supercritical or subcritical phases)'"
    GAS = "'Gas'"
    GLASS = "'Glass'"
    IDEAL_GAS = "'Ideal gas'"
    LIQUID = "'Liquid'"
    LIQUID_CRYSTAL_OF_UNKNOWN_TYPE = "'Liquid crystal of unknown type'"
    LIQUID_MIXTURE_1 = "'Liquid mixture 1'"
    LIQUID_MIXTURE_2 = "'Liquid mixture 2'"
    LIQUID_MIXTURE_3 = "'Liquid mixture 3'"
    METASTABLE_CRYSTAL = "'Metastable crystal'"
    NEMATIC_LIQUID_CRYSTAL = "'Nematic liquid crystal'"
    NEMATIC_LIQUID_CRYSTAL_1 = "'Nematic liquid crystal 1'"
    NEMATIC_LIQUID_CRYSTAL_2 = "'Nematic liquid crystal 2'"
    SMECTIC_LIQUID_CRYSTAL = "'Smectic liquid crystal'"
    SMECTIC_LIQUID_CRYSTAL_1 = "'Smectic liquid crystal 1'"
    SMECTIC_LIQUID_CRYSTAL_2 = "'Smectic liquid crystal 2'"
    SOLUTION = "'Solution'"
    SOLUTION_1 = "'Solution 1'"
    SOLUTION_2 = "'Solution 2'"
    SOLUTION_3 = "'Solution 3'"
    SOLUTION_4 = "'Solution 4'"

class eTemperature(Enum):
    """Enumeration for eTemperature values"""
    LOWER_TEMPERATURE_K = "'Lower temperature, K'"
    TEMPERATURE_K = "'Temperature, K'"
    UPPER_TEMPERATURE_K = "'Upper temperature, K'"

class ePressure(Enum):
    """Enumeration for ePressure values"""
    LOWER_PRESSURE_KPA = "'Lower pressure, kPa'"
    PARTIAL_PRESSURE_KPA = "'Partial pressure, kPa'"
    PRESSURE_KPA = "'Pressure, kPa'"
    UPPER_PRESSURE_KPA = "'Upper pressure, kPa'"

class eComponentComposition(Enum):
    """Enumeration for eComponentComposition values"""
    AMOUNT_CONCENTRATION_MOLARITY_MOLDM3 = "'Amount concentration (molarity), mol/dm3'"
    AMOUNT_RATIO_OF_SOLUTE_TO_SOLVENT = "'Amount ratio of solute to solvent'"
    FINAL_MASS_FRACTION_OF_SOLUTE = "'Final mass fraction of solute'"
    FINAL_MOLALITY_OF_SOLUTE_MOLKG = "'Final molality of solute, mol/kg'"
    FINAL_MOLE_FRACTION_OF_SOLUTE = "'Final mole fraction of solute'"
    INITIAL_MASS_FRACTION_OF_SOLUTE = "'Initial mass fraction of solute'"
    INITIAL_MOLALITY_OF_SOLUTE_MOLKG = "'Initial molality of solute, mol/kg'"
    INITIAL_MOLE_FRACTION_OF_SOLUTE = "'Initial mole fraction of solute'"
    MASS_FRACTION = "'Mass fraction'"
    MASS_RATIO_OF_SOLUTE_TO_SOLVENT = "'Mass ratio of solute to solvent'"
    MOLALITY_MOLKG = "'Molality, mol/kg'"
    MOLE_FRACTION = "'Mole fraction'"
    RATIO_OF_AMOUNT_OF_SOLUTE_TO_MASS_OF_SOLUTION_MOLKG = "'Ratio of amount of solute to mass of solution, mol/kg'"
    RATIO_OF_MASS_OF_SOLUTE_TO_VOLUME_OF_SOLUTION_KGM3 = "'Ratio of mass of solute to volume of solution, kg/m3'"
    VOLUME_FRACTION = "'Volume fraction'"
    VOLUME_RATIO_OF_SOLUTE_TO_SOLVENT = "'Volume ratio of solute to solvent'"

class eSolventComposition(Enum):
    """Enumeration for eSolventComposition values"""
    SOLVENT_AMOUNT_CONCENTRATION_MOLARITY_MOLDM3 = "'Solvent: Amount concentration (molarity), mol/dm3'"
    SOLVENT_AMOUNT_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT = "'Solvent: Amount ratio of component to other component of binary solvent'"
    SOLVENT_MASS_FRACTION = "'Solvent: Mass fraction'"
    SOLVENT_MASS_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT = "'Solvent: Mass ratio of component to other component of binary solvent'"
    SOLVENT_MOLALITY_MOLKG = "'Solvent: Molality, mol/kg'"
    SOLVENT_MOLE_FRACTION = "'Solvent: Mole fraction'"
    SOLVENT_RATIO_OF_AMOUNT_OF_COMPONENT_TO_MASS_OF_SOLVENT_MOLKG = "'Solvent: Ratio of amount of component to mass of solvent, mol/kg'"
    SOLVENT_RATIO_OF_COMPONENT_MASS_TO_VOLUME_OF_SOLVENT_KGM3 = "'Solvent: Ratio of component mass to volume of solvent, kg/m3'"
    SOLVENT_VOLUME_FRACTION = "'Solvent: Volume fraction'"
    SOLVENT_VOLUME_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT = "'Solvent: Volume ratio of component to other component of binary solvent'"

class eMiscellaneous(Enum):
    """Enumeration for eMiscellaneous values"""
    ACTIVITY_COEFFICIENT = "'Activity coefficient'"
    AMOUNT_DENSITY_MOLM3 = "'Amount density, mol/m3'"
    FREQUENCY_MHZ = "'Frequency, MHz'"
    MASS_DENSITY_KGM3 = "'Mass density, kg/m3'"
    MOLAR_ENTROPY_JKMOL = "'Molar entropy, J/K/mol'"
    MOLAR_VOLUME_M3MOL = "'Molar volume, m3/mol'"
    RELATIVE_ACTIVITY = "'(Relative) activity'"
    SPECIFIC_VOLUME_M3KG = "'Specific volume, m3/kg'"
    WAVELENGTH_NM = "'Wavelength, nm'"

class eBioVariables(Enum):
    """Enumeration for eBioVariables values"""
    IONIC_STRENGTH_AMOUNT_CONCENTRATION_BASIS_MOLDM3 = "'Ionic strength (amount concentration basis), mol/dm3'"
    IONIC_STRENGTH_MOLALITY_BASIS_MOLKG = "'Ionic strength (molality basis), mol/kg'"
    PC_AMOUNT_CONCENTRATION_BASIS = "'pC (amount concentration basis)'"
    PH = "'pH'"
    SOLVENT_PC_AMOUNT_CONCENTRATION_BASIS = "'Solvent: pC (amount concentration basis)'"

class eParticipantAmount(Enum):
    """Enumeration for eParticipantAmount values"""
    AMOUNT_MOL = "'Amount, mol'"
    MASS_KG = "'Mass, kg'"

class eConstraintPhase(Enum):
    """Enumeration for eConstraintPhase values"""
    AIR_AT_1_ATMOSPHERE = "'Air at 1 atmosphere'"
    CHOLESTERIC_LIQUID_CRYSTAL = "'Cholesteric liquid crystal'"
    CRYSTAL = "'Crystal'"
    CRYSTAL_1 = "'Crystal 1'"
    CRYSTAL_2 = "'Crystal 2'"
    CRYSTAL_3 = "'Crystal 3'"
    CRYSTAL_4 = "'Crystal 4'"
    CRYSTAL_5 = "'Crystal 5'"
    CRYSTAL_OF_INTERCOMPONENT_COMPOUND_1 = "'Crystal of intercomponent compound 1'"
    CRYSTAL_OF_INTERCOMPONENT_COMPOUND_2 = "'Crystal of intercomponent compound 2'"
    CRYSTAL_OF_INTERCOMPONENT_COMPOUND_3 = "'Crystal of intercomponent compound 3'"
    CRYSTAL_OF_UNKNOWN_TYPE = "'Crystal of unknown type'"
    FLUID_SUPERCRITICAL_OR_SUBCRITICAL_PHASES = "'Fluid (supercritical or subcritical phases)'"
    GAS = "'Gas'"
    GLASS = "'Glass'"
    IDEAL_GAS = "'Ideal gas'"
    LIQUID = "'Liquid'"
    LIQUID_CRYSTAL_OF_UNKNOWN_TYPE = "'Liquid crystal of unknown type'"
    LIQUID_MIXTURE_1 = "'Liquid mixture 1'"
    LIQUID_MIXTURE_2 = "'Liquid mixture 2'"
    LIQUID_MIXTURE_3 = "'Liquid mixture 3'"
    METASTABLE_CRYSTAL = "'Metastable crystal'"
    NEMATIC_LIQUID_CRYSTAL = "'Nematic liquid crystal'"
    NEMATIC_LIQUID_CRYSTAL_1 = "'Nematic liquid crystal 1'"
    NEMATIC_LIQUID_CRYSTAL_2 = "'Nematic liquid crystal 2'"
    SMECTIC_LIQUID_CRYSTAL = "'Smectic liquid crystal'"
    SMECTIC_LIQUID_CRYSTAL_1 = "'Smectic liquid crystal 1'"
    SMECTIC_LIQUID_CRYSTAL_2 = "'Smectic liquid crystal 2'"
    SOLUTION = "'Solution'"
    SOLUTION_1 = "'Solution 1'"
    SOLUTION_2 = "'Solution 2'"
    SOLUTION_3 = "'Solution 3'"
    SOLUTION_4 = "'Solution 4'"

class eVarPhase(Enum):
    """Enumeration for eVarPhase values"""
    AIR_AT_1_ATMOSPHERE = "'Air at 1 atmosphere'"
    CHOLESTERIC_LIQUID_CRYSTAL = "'Cholesteric liquid crystal'"
    CRYSTAL = "'Crystal'"
    CRYSTAL_1 = "'Crystal 1'"
    CRYSTAL_2 = "'Crystal 2'"
    CRYSTAL_3 = "'Crystal 3'"
    CRYSTAL_4 = "'Crystal 4'"
    CRYSTAL_5 = "'Crystal 5'"
    CRYSTAL_OF_INTERCOMPONENT_COMPOUND_1 = "'Crystal of intercomponent compound 1'"
    CRYSTAL_OF_INTERCOMPONENT_COMPOUND_2 = "'Crystal of intercomponent compound 2'"
    CRYSTAL_OF_INTERCOMPONENT_COMPOUND_3 = "'Crystal of intercomponent compound 3'"
    CRYSTAL_OF_UNKNOWN_TYPE = "'Crystal of unknown type'"
    FLUID_SUPERCRITICAL_OR_SUBCRITICAL_PHASES = "'Fluid (supercritical or subcritical phases)'"
    GAS = "'Gas'"
    GLASS = "'Glass'"
    IDEAL_GAS = "'Ideal gas'"
    LIQUID = "'Liquid'"
    LIQUID_CRYSTAL_OF_UNKNOWN_TYPE = "'Liquid crystal of unknown type'"
    LIQUID_MIXTURE_1 = "'Liquid mixture 1'"
    LIQUID_MIXTURE_2 = "'Liquid mixture 2'"
    LIQUID_MIXTURE_3 = "'Liquid mixture 3'"
    METASTABLE_CRYSTAL = "'Metastable crystal'"
    NEMATIC_LIQUID_CRYSTAL = "'Nematic liquid crystal'"
    NEMATIC_LIQUID_CRYSTAL_1 = "'Nematic liquid crystal 1'"
    NEMATIC_LIQUID_CRYSTAL_2 = "'Nematic liquid crystal 2'"
    SMECTIC_LIQUID_CRYSTAL = "'Smectic liquid crystal'"
    SMECTIC_LIQUID_CRYSTAL_1 = "'Smectic liquid crystal 1'"
    SMECTIC_LIQUID_CRYSTAL_2 = "'Smectic liquid crystal 2'"
    SOLUTION = "'Solution'"
    SOLUTION_1 = "'Solution 1'"
    SOLUTION_2 = "'Solution 2'"
    SOLUTION_3 = "'Solution 3'"
    SOLUTION_4 = "'Solution 4'"

class eEqName(Enum):
    """Enumeration for eEqName values"""
    THERMOMLANTOINEVAPORPRESSURE = "'ThermoML.Antoine.VaporPressure'"
    THERMOMLCUSTOMEXPANSION = "'ThermoML.CustomExpansion'"
    THERMOMLHELMHOLTZ3GENERALEOS = "'ThermoML.Helmholtz3General.EOS'"
    THERMOMLHELMHOLTZ4GENERALEOS = "'ThermoML.Helmholtz4General.EOS'"
    THERMOMLPOLYNOMIALEXPANSION = "'ThermoML.PolynomialExpansion'"
    THERMOMLSPANWAGNER12NONPOLAREOS = "'ThermoML.SpanWagner12Nonpolar.EOS'"
    THERMOMLSPANWAGNER12POLAREOS = "'ThermoML.SpanWagner12Polar.EOS'"
    THERMOMLWAGNER25LINEARVAPORPRESSURE = "'ThermoML.Wagner25Linear.VaporPressure'"
    THERMOMLWAGNER36LINEARVAPORPRESSURE = "'ThermoML.Wagner36Linear.VaporPressure'"
    THERMOMLWAGNERLINEARVAPORPRESSURE = "'ThermoML.WagnerLinear.VaporPressure'"

class eCompositionRepresentation(Enum):
    """Enumeration for eCompositionRepresentation values"""
    AMOUNT_CONCENTRATION_AMOUNT_OF_PARTICIPANT_PER_VOLUME_OF_SOLUTION_MOLDM3 = "'Amount concentration - amount of participant per volume of solution, mol/dm3'"
    AMOUNT_OF_PARTICIPANT_PER_MASS_OF_SOLUTION_MOLKG = "'Amount of participant per mass of solution, mol/kg'"
    AMOUNT_RATIO_OF_PARTICIPANT_TO_SOLVENT = "'Amount ratio of participant to solvent'"
    AMOUNT_RATIO_OF_SOLVENT_TO_PARTICIPANT = "'Amount ratio of solvent to participant'"
    MASS_OF_PARTICIPANT_PER_VOLUME_OF_SOLUTION_KGM3 = "'Mass of participant per volume of solution, kg/m3'"
    MASS_RATIO_OF_PARTICIPANT_TO_SOLVENT = "'Mass ratio of participant to solvent'"
    MOLALITY_AMOUNT_OF_PARTICIPANT_PER_MASS_OF_SOLVENT_MOLKG = "'Molality - amount of participant per mass of solvent, mol/kg'"
    VOLUME_RATIO_OF_PARTICIPANT_TO_SOLVENT = "'Volume ratio of participant to solvent'"

class eReactionFormalism(Enum):
    """Enumeration for eReactionFormalism values"""
    BIOCHEMICAL = "'biochemical'"
    CHEMICAL = "'chemical'"

class eReactionType(Enum):
    """Enumeration for eReactionType values"""
    ADDITION_OF_VARIOUS_COMPOUNDS_TO_UNSATURATED_COMPOUNDS = "'Addition of various compounds to unsaturated compounds'"
    ADDITION_OF_WATER_TO_A_LIQUID_OR_SOLID_TO_PRODUCE_A_HYDRATE = "'Addition of water to a liquid or solid to produce a hydrate'"
    ATOMIZATION_OR_FORMATION_FROM_ATOMS = "'Atomization (or formation from atoms)'"
    COMBUSTION_WITH_OTHER_ELEMENTS_OR_COMPOUNDS = "'Combustion with other elements or compounds'"
    COMBUSTION_WITH_OXYGEN = "'Combustion with oxygen'"
    ESTERIFICATION = "'Esterification'"
    EXCHANGE_OF_ALKYL_GROUPS = "'Exchange of alkyl groups'"
    EXCHANGE_OF_HYDROGEN_ATOMS_WITH_OTHER_GROUPS = "'Exchange of hydrogen (atoms) with other groups'"
    FORMATION_OF_A_COMPOUND_FROM_ELEMENTS_IN_THEIR_STABLE_STATE = "'Formation of a compound from elements in their stable state'"
    FORMATION_OF_ION = "'Formation of ion'"
    HALOGENATION_ADDITION_OF_OR_REPLACEMENT_BY_A_HALOGEN = "'Halogenation (addition of or replacement by a halogen)'"
    HOMONUCLEAR_DIMERIZATION = "'Homonuclear dimerization'"
    HYDROGENATION_ADDITION_OF_HYDROGEN_TO_UNSATURATED_COMPOUNDS = "'Hydrogenation (addition of hydrogen to unsaturated compounds)'"
    HYDROHALOGENATION = "'Hydrohalogenation'"
    HYDROLYSIS_OF_IONS = "'Hydrolysis of ions'"
    ION_EXCHANGE = "'Ion exchange'"
    NEUTRALIZATION_REACTION_OF_AN_ACID_WITH_A_BASE = "'Neutralization (reaction of an acid with a base)'"
    OTHER_REACTIONS = "'Other reactions'"
    OTHER_REACTIONS_WITH_WATER = "'Other reactions with water'"
    OXIDATION_WITH_OXIDIZING_AGENTS_OTHER_THAN_OXYGEN = "'Oxidation with oxidizing agents other than oxygen'"
    OXIDATION_WITH_OXYGEN_NOT_COMPLETE = "'Oxidation with oxygen (not complete)'"
    POLYMERIZATION_ALL_OTHER_TYPES = "'Polymerization (all other types)'"
    SOLVOLYIS_SOLVENTS_OTHER_THAN_WATER = "'Solvolyis (solvents other than water)'"
    STEREOISOMERISM = "'Stereoisomerism'"
    STRUCTURAL_ISOMERIZATION = "'Structural isomerization'"