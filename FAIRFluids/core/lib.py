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


class FAIRFluidsDocument(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    ----Description
    """
    version: Optional[Version] = element(
        default= None,
        tag="version",
        description="""Version of the FAIRFluidsDocument""",
        json_schema_extra=dict(),
    )
    citation: Optional[Citation] = element(
        default= None,
        tag="citation",
        description="""Add information about the datareport""",
        json_schema_extra=dict(),
    )
    compound: list[Compound] = element(
        default_factory=list,
        tag="compound",
        description="""What Compounds are in the fluid""",
        json_schema_extra=dict(),
    )
    fluid: list[Fluid] = element(
        default_factory=list,
        tag="fluid",
        description="""Specifcations of the Fluid""",
        json_schema_extra=dict(),
    )


    def add_to_compound(
        self,
        pubChemID: Optional[int]= None,
        compound_identifier: Optional[C_id]= None,
        commonName: Optional[str]= None,
        SELFIE: Optional[str]= None,
        name_IUPAC: Optional[str]= None,
        standard_InChI: Optional[str]= None,
        standard_InChI_key: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new Compound to the compound list."""
        params = {
            "pubChemID": pubChemID,
            "compound_identifier": compound_identifier,
            "commonName": commonName,
            "SELFIE": SELFIE,
            "name_IUPAC": name_IUPAC,
            "standard_InChI": standard_InChI,
            "standard_InChI_key": standard_InChI_key
        }

        self.compound.append(
            Compound(**params)
        )

        return self.compound[-1]

    def add_to_fluid(
        self,
        components: list[str]= [],
        source_doi: Optional[str]= None,
        property: Optional[Property]= None,
        parameter: list[Parameter]= [],
        num_value: Optional[NumValue]= None,
        **kwargs,
    ):
        """Helper method to add a new Fluid to the fluid list."""
        params = {
            "components": components,
            "source_doi": source_doi,
            "property": property,
            "parameter": parameter,
            "num_value": num_value
        }

        self.fluid.append(
            Fluid(**params)
        )

        return self.fluid[-1]
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
    versionMajor: Optional[int] = element(
        default= None,
        tag="versionMajor",
        description="""Add the major version number to your datareport""",
        json_schema_extra=dict(),
    )
    versionMinor: Optional[int] = element(
        default= None,
        tag="versionMinor",
        description="""Add the minor version number to your datareport""",
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
    litType: Optional[LitType] = element(
        default= None,
        tag="litType",
        description="""indicates the type of source document (book, journal, report, patent, thesis,
            conference proceedings, archived document, personal correspondence,
            published translation, unspecified).""",
        json_schema_extra=dict(),
    )
    author: list[Author] = element(
        default_factory=list,
        tag="author",
        description="""X""",
        json_schema_extra=dict(),
    )


    def add_to_author(
        self,
        given_name: Optional[str]= None,
        family_name: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new Author to the author list."""
        params = {
            "given_name": given_name,
            "family_name": family_name
        }

        self.author.append(
            Author(**params)
        )

        return self.author[-1]
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


class Author(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Add more Info
    """
    given_name: Optional[str] = element(
        default= None,
        tag="given_name",
        description="""Name of the Author""",
        json_schema_extra=dict(),
    )
    family_name: Optional[str] = element(
        default= None,
        tag="family_name",
        description="""Family name ot the author or contributor""",
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
    Here the Metadata of each compound are listed.
    """
    pubChemID: Optional[int] = element(
        default= None,
        tag="pubChemID",
        description="""PubChemID of the Compound""",
        json_schema_extra=dict(),
    )
    compound_identifier: Optional[C_id] = element(
        default= None,
        tag="compound_identifier",
        description="""Unique Id of the compund in this datareport""",
        json_schema_extra=dict(),
    )
    commonName: Optional[str] = element(
        default= None,
        tag="commonName",
        description="""The generic name of a substance, e.g. H20 - Water""",
        json_schema_extra=dict(),
    )
    SELFIE: Optional[str] = element(
        default= None,
        tag="SELFIE",
        description="""SELFIES Representation from the Molecule""",
        json_schema_extra=dict(),
    )
    name_IUPAC: Optional[str] = element(
        default= None,
        tag="name_IUPAC",
        json_schema_extra=dict(),
    )
    standard_InChI: Optional[str] = element(
        default= None,
        tag="standard_InChI",
        json_schema_extra=dict(),
    )
    standard_InChI_key: Optional[str] = element(
        default= None,
        tag="standard_InChI_key",
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


class C_id(
    BaseXmlModel,
    search_mode="unordered",
):
    c_id: Optional[str] = element(
        default= None,
        tag="c_id",
        description="""Unique id of the compound""",
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


class Fluid(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    This block contains nonbibliographic information about the source of the file
    contents, identifies the experimental purpose, specifies meta- and numerical
    data, and specifies the compound (or mixture) and particular samples to
    which the data are related.
    """
    components: list[str] = element(
        default_factory=list,
        tag="components",
        description="""Add the ID of the compund into the fluid""",
        json_schema_extra=dict(),
    )
    source_doi: Optional[str] = element(
        default= None,
        tag="source_doi",
        description="""The source where the data come form""",
        json_schema_extra=dict(),
    )
    property: Optional[Property] = element(
        default= None,
        tag="property",
        description="""Property[] complex (Fig. 8) is characterized by Property-MethodID[] complex ,
            which identifies the property and experimental method used;""",
        json_schema_extra=dict(),
    )
    parameter: list[Parameter] = element(
        default_factory=list,
        tag="parameter",
        description="""A variable refers to an independent experimental parameter that varies across
            data points within a data set. Examples include temperature,
            pressure, composition, and other input conditions under which
            thermodynamic properties are measured. A constraint refers to a
            condition or a fixed parameter that applies to an entire data set,
            rather than to each individual data point. Constraints are used to
            define experimental or calculated conditions that remain constant
            across all the measurements in a data set. Examples might include
            fixed composition, pressure, or volume during an experiment.""",
        json_schema_extra=dict(),
    )
    num_value: Optional[NumValue] = element(
        default= None,
        tag="num_value",
        description="""Actual meassurement data""",
        json_schema_extra=dict(),
    )


    def add_to_parameter(
        self,
        parameterID: Optional[str]= None,
        parameterType: Optional[ParameterType]= None,
        componentID: Optional[int]= None,
        **kwargs,
    ):
        """Helper method to add a new Parameter to the parameter list."""
        params = {
            "parameterID": parameterID,
            "parameterType": parameterType,
            "componentID": componentID
        }

        self.parameter.append(
            Parameter(**params)
        )

        return self.parameter[-1]
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
    Definition: This is the main quantity being measured or reported.
    """
    propertyID: Optional[str] = element(
        default= None,
        tag="propertyID",
        description="""Unique ID of the fluid property""",
        json_schema_extra=dict(),
    )
    property_information: Optional[Property_Information] = element(
        default= None,
        tag="property_information",
        description="""An identfication to which group the porperty belongs to""",
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


class Property_Information(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    How was the Property Derived, how was it calculated, etc.
    """
    group: Optional[str] = element(
        default= None,
        tag="group",
        description="""To which group does the property belong: volumetricProp _ , TransportProp,
            HeatCapacityAndDerivedProp, ExcessPartialApparentEnergyProp,
            CompositionAtPhaseEquilibrium""",
        json_schema_extra=dict(),
    )
    method: Optional[str] = element(
        default= None,
        tag="method",
        description="""How was the property obtained. (Maybe add prediction field)""",
        json_schema_extra=dict(),
    )
    property_name: Optional[str] = element(
        default= None,
        tag="property_name",
        description="""What is the name of the property, eg. Mass Density, (and Units?)""",
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


class Parameter(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Definition: A quantity that was varied during the experiment to observe its
    effect on the Property.
    """
    parameterID: Optional[str] = element(
        default= None,
        tag="parameterID",
        json_schema_extra=dict(),
    )
    parameterType: Optional[ParameterType] = element(
        default= None,
        tag="parameterType",
        description="""Name of the Variable- e.g. Temerpature""",
        json_schema_extra=dict(),
    )
    componentID: Optional[int] = element(
        default= None,
        tag="componentID",
        description="""Add to Identify to which compound the variable applies to""",
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


class ParameterType(
    BaseXmlModel,
    search_mode="unordered",
):
    bio_variables: Optional[BioVariables] = element(
        default= None,
        tag="bio_variables",
        json_schema_extra=dict(),
    )
    component_composition: Optional[ComponentComposition] = element(
        default= None,
        tag="component_composition",
        json_schema_extra=dict(),
    )
    miscellaneous: Optional[Miscellaneous] = element(
        default= None,
        tag="miscellaneous",
        json_schema_extra=dict(),
    )
    participant_amount: Optional[ParticipantAmount] = element(
        default= None,
        tag="participant_amount",
        json_schema_extra=dict(),
    )
    pressure: Optional[Pressure] = element(
        default= None,
        tag="pressure",
        json_schema_extra=dict(),
    )
    solvent_composition: Optional[SolventComposition] = element(
        default= None,
        tag="solvent_composition",
        json_schema_extra=dict(),
    )
    temperature: Optional[Temperature] = element(
        default= None,
        tag="temperature",
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


class NumValue(
    BaseXmlModel,
    search_mode="unordered",
):
    propertyValue: Optional[PropertyValue] = element(
        default= None,
        tag="propertyValue",
        json_schema_extra=dict(),
    )
    parameterValue: Optional[ParameterValue] = element(
        default= None,
        tag="parameterValue",
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


class PropertyValue(
    BaseXmlModel,
    search_mode="unordered",
):
    propDigits: Optional[int] = element(
        default= None,
        tag="propDigits",
        json_schema_extra=dict(),
    )
    propNumber: Optional[str] = element(
        default= None,
        tag="propNumber",
        json_schema_extra=dict(),
    )
    propValue: Optional[float] = element(
        default= None,
        tag="propValue",
        description="""Actual value of the property""",
        json_schema_extra=dict(),
    )
    uncertainty: Optional[float] = element(
        default= None,
        tag="uncertainty",
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


class ParameterValue(
    BaseXmlModel,
    search_mode="unordered",
):
    varDigits: Optional[int] = element(
        default= None,
        tag="varDigits",
        json_schema_extra=dict(),
    )
    varNumber: Optional[str] = element(
        default= None,
        tag="varNumber",
        json_schema_extra=dict(),
    )
    varValue: Optional[float] = element(
        default= None,
        tag="varValue",
        description="""Actual value of the variable""",
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


class LitType(Enum):
    """Enumeration for LitType values"""
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

class Temperature(Enum):
    """Enumeration for Temperature values"""
    LOWER_TEMPERATURE_K = "'Lower temperature, K'"
    TEMPERATURE_K = "'Temperature, K'"
    UPPER_TEMPERATURE_K = "'Upper temperature, K'"

class Pressure(Enum):
    """Enumeration for Pressure values"""
    LOWER_PRESSURE_KPA = "'Lower pressure, kPa'"
    PARTIAL_PRESSURE_KPA = "'Partial pressure, kPa'"
    PRESSURE_KPA = "'Pressure, kPa'"
    UPPER_PRESSURE_KPA = "'Upper pressure, kPa'"

class ComponentComposition(Enum):
    """Enumeration for ComponentComposition values"""
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

class SolventComposition(Enum):
    """Enumeration for SolventComposition values"""
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

class Miscellaneous(Enum):
    """Enumeration for Miscellaneous values"""
    ACTIVITY_COEFFICIENT = "'Activity coefficient'"
    AMOUNT_DENSITY_MOLM3 = "'Amount density, mol/m3'"
    FREQUENCY_MHZ = "'Frequency, MHz'"
    MASS_DENSITY_KGM3 = "'Mass density, kg/m3'"
    MOLAR_ENTROPY_JKMOL = "'Molar entropy, J/K/mol'"
    MOLAR_VOLUME_M3MOL = "'Molar volume, m3/mol'"
    RELATIVE_ACTIVITY = "'(Relative) activity'"
    SPECIFIC_VOLUME_M3KG = "'Specific volume, m3/kg'"
    WAVELENGTH_NM = "'Wavelength, nm'"

class BioVariables(Enum):
    """Enumeration for BioVariables values"""
    IONIC_STRENGTH_AMOUNT_CONCENTRATION_BASIS_MOLDM3 = "'Ionic strength (amount concentration basis), mol/dm3'"
    IONIC_STRENGTH_MOLALITY_BASIS_MOLKG = "'Ionic strength (molality basis), mol/kg'"
    PC_AMOUNT_CONCENTRATION_BASIS = "'pC (amount concentration basis)'"
    PH = "'pH'"
    SOLVENT_PC_AMOUNT_CONCENTRATION_BASIS = "'Solvent: pC (amount concentration basis)'"

class ParticipantAmount(Enum):
    """Enumeration for ParticipantAmount values"""
    AMOUNT_MOL = "'Amount, mol'"
    MASS_KG = "'Mass, kg'"