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
        description="""Specifcations of the Fluid. There can be multible Fluids in one document""",
        json_schema_extra=dict(),
    )


    def add_to_compound(
        self,
        compoundID: Optional[str]= None,
        pubChemID: Optional[int]= None,
        commonName: Optional[str]= None,
        SELFIE: Optional[str]= None,
        name_IUPAC: Optional[str]= None,
        standard_InChI: Optional[str]= None,
        standard_InChI_key: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new Compound to the compound list."""
        params = {
            "compoundID": compoundID,
            "pubChemID": pubChemID,
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
        compounds: list[str]= [],
        property: list[Property]= [],
        parameter: list[Parameter]= [],
        measurement: list[Measurement]= [],
        **kwargs,
    ):
        """Helper method to add a new Fluid to the fluid list."""
        params = {
            "compounds": compounds,
            "property": property,
            "parameter": parameter,
            "measurement": measurement
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

    def get_viscosity_data(self):
        """
        Returns a list of dicts with keys:
            - 'compound_identifiers': list of compound names or IDs
            - 'mole_fractions': list of mole fractions (same order as compounds)
            - 'temperature': temperature in K
            - 'viscosity': viscosity value (mPa·s)
        """
        data = []
        for fluid in self.fluid:
            # Get compound names or IDs
            compounds = []
            for idx in fluid.compounds:
                comp = None
                for c in self.compound:
                    if str(c.compoundID) == str(idx):
                        comp = c
                        break
                if comp and comp.commonName:
                    compounds.append(comp.commonName)
                elif comp and comp.compoundID:
                    compounds.append(str(comp.compoundID))
                else:
                    compounds.append(str(idx))
            for meas in fluid.measurement:
                viscosity = None
                for pv in meas.propertyValue:
                    if pv.propertyID == 'viscosity':
                        viscosity = pv.propValue
                temperature = None
                mole_fractions = []
                for par_val in meas.parameterValue:
                    if par_val.parameterID.startswith('T_'):
                        temperature = par_val.paramValue
                    if par_val.parameterID.startswith('x_'):
                        mole_fractions.append(par_val.paramValue)
                if viscosity is not None and temperature is not None and mole_fractions:
                    data.append({
                        'compound_identifiers': compounds,
                        'mole_fractions': mole_fractions,
                        'temperature': temperature,
                        'viscosity': viscosity
                    })
        return data


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
        description="""Specifies the type of literature or source document. Accepted values include:
            book, journal, report, patent, thesis, conference proceedings,
            archived document, personal correspondence, published translation,
            or unspecified.""",
        json_schema_extra=dict(),
    )
    author: list[Author] = element(
        default_factory=list,
        tag="author",
        description="""A list of authors who contributed to the publication. Each entry should include
            structured information such as full name and optionally additional
            metadata like affiliation or identifier.""",
        json_schema_extra=dict(),
    )
    doi: Optional[str] = element(
        default= None,
        tag="doi",
        description="""Digital Object Identifier (DOI) for the publication. A unique alphanumeric
            string used to identify and provide a permanent link to the document
            online.""",
        json_schema_extra=dict(),
    )
    page: Optional[str] = element(
        default= None,
        tag="page",
        description="""The page range in which the publication appears, typically formatted as a string
            (e.g., '123–135').""",
        json_schema_extra=dict(),
    )
    pub_name: Optional[str] = element(
        default= None,
        tag="pub_name",
        description="""The name of the publication source, such as the journal title, book title, or
            conference name.""",
        json_schema_extra=dict(),
    )
    title: Optional[str] = element(
        default= None,
        tag="title",
        description="""The title of the cited work or publication.""",
        json_schema_extra=dict(),
    )
    lit_volume_num: Optional[str] = element(
        default= None,
        tag="lit_volume_num",
        description="""The volume number of the source publication, if applicable (e.g., journal
            volume).""",
        json_schema_extra=dict(),
    )
    url_citation: Optional[str] = element(
        default= None,
        tag="url_citation",
        description="""A direct URL link to the publication or citation landing page.""",
        json_schema_extra=dict(),
    )
    publication_year: Optional[str] = element(
        default= None,
        tag="publication_year",
        description="""The year in which the publication was officially released or published.""",
        json_schema_extra=dict(),
    )


    def add_to_author(
        self,
        given_name: Optional[str]= None,
        family_name: Optional[str]= None,
        email: Optional[str]= None,
        orcid: Optional[str]= None,
        affiliation: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new Author to the author list."""
        params = {
            "given_name": given_name,
            "family_name": family_name,
            "email": email,
            "orcid": orcid,
            "affiliation": affiliation
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
    Description: Represents an individual contributor or creator of the cited
    work. Each author entry includes identifying details such as name, contact
    information, unique identifiers, and institutional affiliation.
    """
    given_name: Optional[str] = element(
        default= None,
        tag="given_name",
        description="""The given name (first name or personal name) of the author or contributor.""",
        json_schema_extra=dict(),
    )
    family_name: Optional[str] = element(
        default= None,
        tag="family_name",
        description="""The family name (surname or last name) of the author or contributor.""",
        json_schema_extra=dict(),
    )
    email: Optional[str] = element(
        default= None,
        tag="email",
        description="""The email address of the author, if available. Used for contact or
            identification purposes.""",
        json_schema_extra=dict(),
    )
    orcid: Optional[str] = element(
        default= None,
        tag="orcid",
        description="""The ORCID iD of the author, a unique, persistent identifier used to distinguish
            researchers (e.g., '0000-0002-1825-0097').""",
        json_schema_extra=dict(),
    )
    affiliation: Optional[str] = element(
        default= None,
        tag="affiliation",
        description="""The name of the institution or organization the author is affiliated with at the
            time of publication.""",
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
    names, and structural representations. Each entry describes one unique
    compound referenced in the data report.
    """
    compoundID: Optional[str] = element(
        default= None,
        tag="compoundID",
        description="""A unique identifier assigned to the compound within the scope of this specific
            data report or dataset. Used for internal tracking.""",
        json_schema_extra=dict(),
    )
    pubChemID: Optional[int] = element(
        default= None,
        tag="pubChemID",
        description="""The PubChem Compound Identifier (CID), a unique numeric ID assigned by the
            PubChem database to this compound.""",
        json_schema_extra=dict(),
    )
    commonName: Optional[str] = element(
        default= None,
        tag="commonName",
        description="""The common or generic name of the compound, such as 'Water' for H₂O.""",
        json_schema_extra=dict(),
    )
    SELFIE: Optional[str] = element(
        default= None,
        tag="SELFIE",
        description="""The SELFIES (Self-referencing Embedded Strings) representation of the compound’s
            molecular structure. A robust, machine-readable encoding for
            molecules.""",
        json_schema_extra=dict(),
    )
    name_IUPAC: Optional[str] = element(
        default= None,
        tag="name_IUPAC",
        description="""The full IUPAC (International Union of Pure and Applied Chemistry) name of the
            compound, representing its standardized chemical nomenclature.""",
        json_schema_extra=dict(),
    )
    standard_InChI: Optional[str] = element(
        default= None,
        tag="standard_InChI",
        description="""The Standard International Chemical Identifier (InChI) string that uniquely
            represents the compound’s molecular structure.""",
        json_schema_extra=dict(),
    )
    standard_InChI_key: Optional[str] = element(
        default= None,
        tag="standard_InChI_key",
        description="""The hashed version of the InChI string, known as the InChIKey. It is a fixed-
            length, easier-to-search identifier for databases and indexing.""",
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
    Description: Contains metadata and experimental context for a dataset related
    to a fluid system. This includes the chemical composition (pure substance
    or mixture), source of the data, properties measured, varying experimental
    parameters, and the corresponding numerical results. There can exist
    multible fluids in one document.
    """
    compounds: list[str] = element(
        default_factory=list,
        tag="compounds",
        description="""A list of unique identifiers referencing the compounds present in the fluid
            system. Multiple identifiers indicate a mixture; single entries
            indicate a pure substance.v""",
        json_schema_extra=dict(),
    )
    property: list[Property] = element(
        default_factory=list,
        tag="property",
        description="""A list of physical or thermodynamic properties that were measured or calculated
            for the fluid. Each property is associated with a method identifier
            (propertyID) that defines both the property type (e.g., viscosity,
            density, heat capacity) and the experimental or computational method
            used.""",
        json_schema_extra=dict(),
    )
    parameter: list[Parameter] = element(
        default_factory=list,
        tag="parameter",
        description="""A list of experimental parameters. Parameters may vary across data points
            (e.g., temperature, pressure, composition) or serve as constraints
            that remain fixed across the dataset (e.g., constant pressure or
            fixed mole ratio). These define the input conditions under which
            properties are observed or measured.""",
        json_schema_extra=dict(),
    )
    measurement: list[Measurement] = element(
        default_factory=list,
        tag="measurement",
        description="""A collection of measured or calculated numerical data points associated with the
            specified properties and experimental parameters.""",
        json_schema_extra=dict(),
    )


    def add_to_property(
        self,
        propertyID: Optional[str]= None,
        properties: Optional[Properties]= None,
        unit: Optional[UnitDefinition]= None,
        **kwargs,
    ):
        """Helper method to add a new Property to the property list."""
        params = {
            "propertyID": propertyID,
            "properties": properties,
            "unit": unit
        }

        self.property.append(
            Property(**params)
        )

        return self.property[-1]

    def add_to_parameter(
        self,
        parameterID: Optional[str]= None,
        parameter: Optional[Parameters]= None,
        unit: Optional[UnitDefinition]= None,
        associated_compound: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new Parameter to the parameter list."""
        params = {
            "parameterID": parameterID,
            "parameter": parameter,
            "unit": unit,
            "associated_compound": associated_compound
        }

        self.parameter.append(
            Parameter(**params)
        )

        return self.parameter[-1]

    def add_to_measurement(
        self,
        measurement_id: Optional[str]= None,
        source_doi: Optional[str]= None,
        propertyValue: list[PropertyValue]= [],
        parameterValue: list[ParameterValue]= [],
        method: Optional[Method]= None,
        method_description: Optional[str]= None,
        **kwargs,
    ):
        """Helper method to add a new Measurement to the measurement list."""
        params = {
            "measurement_id": measurement_id,
            "source_doi": source_doi,
            "propertyValue": propertyValue,
            "parameterValue": parameterValue,
            "method": method,
            "method_description": method_description
        }

        self.measurement.append(
            Measurement(**params)
        )

        return self.measurement[-1]
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
    Description: Defines the primary quantity being measured, calculated,
    or otherwise reported for a fluid system. Each property includes its
    identifier, grouping, and methodological context.
    """
    propertyID: Optional[str] = element(
        default= None,
        tag="propertyID",
        description="""A unique identifier for the specific property being reported (e.g., viscosity,
            density, heat capacity).""",
        json_schema_extra=dict(),
    )
    properties: Optional[Properties] = element(
        default= None,
        tag="properties",
        description="""Indicates the broader category or group to which the property belongs (e.g.,
            thermodynamic, transport, phase behavior). Used to organize related
            properties.""",
        json_schema_extra=dict(),
    )
    unit: Optional[UnitDefinition] = element(
        default= None,
        tag="unit",
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
    Description: Represents an independent variable or experimental input that was
    varied during data collection to observe its effect on a reported property.
    Parameters can apply globally to the system or specifically to one component
    in a mixture. Categorizes the type of experimental or system variable
    that is being controlled or varied during data collection. Each category
    represents a specific kind of parameter relevant to fluid or chemical
    systems.
    """
    parameterID: Optional[str] = element(
        default= None,
        tag="parameterID",
        description="""A unique identifier for this parameter within the dataset. Used for referencing
            in conjunction with numerical values.""",
        json_schema_extra=dict(),
    )
    parameter: Optional[Parameters] = element(
        default= None,
        tag="parameter",
        description="""The type or name of the parameter being varied, such as temperature, pressure,
            or mole fraction. Indicates what was controlled or changed during
            the experiment.""",
        json_schema_extra=dict(),
    )
    unit: Optional[UnitDefinition] = element(
        default= None,
        tag="unit",
        json_schema_extra=dict(),
    )
    associated_compound: Optional[str] = element(
        default= None,
        tag="associated_compound",
        description="""Identifies the specific compound (by its index or ID) to which this parameter
            applies. Useful in multicomponent systems where a parameter (e.g.,
            mole fraction) pertains to a specific compound.""",
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


class Measurement(
    BaseXmlModel,
    search_mode="unordered",
):
    """
    Description: Contains the numerical data values related to both properties and
    parameters. These values represent the measured or calculated quantities
    recorded in the experiment or dataset.
    """
    measurement_id: Optional[str] = element(
        default= None,
        tag="measurement_id",
        json_schema_extra=dict(),
    )
    source_doi: Optional[str] = element(
        default= None,
        tag="source_doi",
        description="""The Digital Object Identifier (DOI) of the source publication or dataset from
            which the fluid data was obtained.""",
        json_schema_extra=dict(),
    )
    propertyValue: list[PropertyValue] = element(
        default_factory=list,
        tag="propertyValue",
        description="""An array of numerical values corresponding to the measured or calculated
            properties (e.g., density, viscosity). Each entry should include the
            value, units, and possibly uncertainty or error margins.""",
        json_schema_extra=dict(),
    )
    parameterValue: list[ParameterValue] = element(
        default_factory=list,
        tag="parameterValue",
        description="""An array of numerical values corresponding to the parameters that were varied or
            held constant during the experiment (e.g., temperature, pressure).
            Each entry should specify the value, units, and related parameter
            identifier.3""",
        json_schema_extra=dict(),
    )
    method: Optional[Method] = element(
        default= None,
        tag="method",
        description="""Describes how the property value was obtained. Accepted values may
            include: , , , , or . This field helps distinguish between
            experimental and non-experimental data sources.""",
        json_schema_extra=dict(),
    )
    method_description: Optional[str] = element(
        default= None,
        tag="method_description",
        description="""A free-text description providing additional detail about the method used to
            generate the data (e.g., specific experimental setup, calculation
            model, simulation type, or literature source details).""",
        json_schema_extra=dict(),
    )


    def add_to_propertyValue(
        self,
        propertyID: Optional[str]= None,
        propValue: Optional[float]= None,
        uncertainty: Optional[float]= None,
        **kwargs,
    ):
        """Helper method to add a new PropertyValue to the propertyValue list."""
        params = {
            "propertyID": propertyID,
            "propValue": propValue,
            "uncertainty": uncertainty
        }

        self.propertyValue.append(
            PropertyValue(**params)
        )

        return self.propertyValue[-1]

    def add_to_parameterValue(
        self,
        parameterID: Optional[str]= None,
        paramValue: Optional[float]= None,
        uncertainty: Optional[float]= None,
        **kwargs,
    ):
        """Helper method to add a new ParameterValue to the parameterValue list."""
        params = {
            "parameterID": parameterID,
            "paramValue": paramValue,
            "uncertainty": uncertainty
        }

        self.parameterValue.append(
            ParameterValue(**params)
        )

        return self.parameterValue[-1]
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
    Description: Represents a numerical value associated with a specific property
    measurement, including precision and uncertainty information.
    """
    propertyID: Optional[str] = element(
        default= None,
        tag="propertyID",
        description="""Identifier referencing the property to which this value corresponds.""",
        json_schema_extra=dict(),
    )
    propValue: Optional[float] = element(
        default= None,
        tag="propValue",
        description="""The actual measured or calculated numerical value of the property.""",
        json_schema_extra=dict(),
    )
    uncertainty: Optional[float] = element(
        default= None,
        tag="uncertainty",
        description="""The estimated uncertainty or error margin associated with the property value,
            typically representing standard deviation or confidence interval.""",
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
    """
    Description: Represents a numerical value for a parameter that was varied
    or controlled during the experiment, including precision and uncertainty
    details.
    """
    parameterID: Optional[str] = element(
        default= None,
        tag="parameterID",
        description="""Identifier referencing the specific parameter this value corresponds to.""",
        json_schema_extra=dict(),
    )
    paramValue: Optional[float] = element(
        default= None,
        tag="paramValue",
        description="""The actual measured or set numerical value of the parameter.""",
        json_schema_extra=dict(),
    )
    uncertainty: Optional[float] = element(
        default= None,
        tag="uncertainty",
        description="""The estimated uncertainty or error margin associated with the parameter value.""",
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


class UnitDefinition(
    BaseXmlModel,
    search_mode="unordered",
):
    unitID: Optional[str] = element(
        default= None,
        tag="unitID",
        description="""Unique identifier for the unit definition, used for referencing in data fields.""",
        json_schema_extra=dict(),
    )
    name: Optional[str] = element(
        default= None,
        tag="name",
        description="""Human-readable name of the unit (e.g., 'kilogram per cubic meter').""",
        json_schema_extra=dict(),
    )
    base_units: list[BaseUnit] = element(
        default_factory=list,
        tag="base_units",
        description="""A list of base unit components that, together with exponents, scale, and
            multipliers, define the full derived unit.""",
        json_schema_extra=dict(),
    )


    def add_to_base_units(
        self,
        kind: Optional[str]= None,
        exponent: Optional[int]= None,
        multiplier: Optional[float]= None,
        scale: Optional[float]= None,
        **kwargs,
    ):
        """Helper method to add a new BaseUnit to the base_units list."""
        params = {
            "kind": kind,
            "exponent": exponent,
            "multiplier": multiplier,
            "scale": scale
        }

        self.base_units.append(
            BaseUnit(**params)
        )

        return self.base_units[-1]
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


class BaseUnit(
    BaseXmlModel,
    search_mode="unordered",
):
    kind: Optional[str] = element(
        default= None,
        tag="kind",
        description="""The physical quantity represented by the unit (e.g., mass, length, time,
            temperature).""",
        json_schema_extra=dict(),
    )
    exponent: Optional[int] = element(
        default= None,
        tag="exponent",
        description="""Exponent applied to the base unit (e.g., m² has exponent 2 for 'length').""",
        json_schema_extra=dict(),
    )
    multiplier: Optional[float] = element(
        default= None,
        tag="multiplier",
        description="""Numerical multiplier applied to the base unit (e.g., 1000 for gram when
            converting to kilogram).""",
        json_schema_extra=dict(),
    )
    scale: Optional[float] = element(
        default= None,
        tag="scale",
        description="""Power-of-ten scale factor applied to the unit (e.g., 3 for kilo, -6 for micro).
            Applied as 10^scale.""",
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
    ARCHIVEDDOCUMENT = "archivedDocument"
    BOOK = "book"
    CONFERENCEPROCEEDINGS = "conferenceProceedings"
    JOURNAL = "journal"
    PATENT = "patent"
    PERSONALCORRESPONDENCE = "personalCorrespondence"
    PUBLISHEDTRANSLATION = "publishedTranslation"
    REPORT = "report"
    THESIS = "thesis"
    UNSPECIFIED = "unspecified"

class Method(Enum):
    """Enumeration for Method values"""
    CALCULATED = "calculated,"
    LITERATURE = "literature"
    MEASURED = "measured,"
    SIMULATED = "simulated,"

class Properties(Enum):
    """Enumeration for Properties values"""
    BOILING_POINT = "boilingPoint"
    COMPRESSIBILITY = "Compressibility"
    DENSITY = "density"
    MELTING_POINT = "meltingPoint"
    PH = "pH"
    POLARITY = "polarity"
    SPECIFIC_HEAT_CAPACITY = "specificHeatCapacity"
    THERMAL_CONDUCTIVITY = "thermalConductivity"
    VAPOR_PRESSURE = "vaporPressure"
    VISCOSITY = "viscosity"

class Parameters(Enum):
    """Enumeration for Parameters values"""
    ACTIVITY_COEFFICIENT = "Activity coefficient"
    AMOUNT_CONCENTRATION_MOLARITY_MOLDM3 = "Amount concentration (molarity), mol/dm3"
    AMOUNT_DENSITY_MOLM3 = "Amount density, mol/m3"
    AMOUNT_MOL = "Amount, mol"
    AMOUNT_RATIO_OF_SOLUTE_TO_SOLVENT = "Amount ratio of solute to solvent"
    FINAL_MASS_FRACTION_OF_SOLUTE = "Final mass fraction of solute"
    FINAL_MOLALITY_OF_SOLUTE_MOLKG = "Final molality of solute, mol/kg"
    FINAL_MOLE_FRACTION_OF_SOLUTE = "Final mole fraction of solute"
    FREQUENCY_MHZ = "Frequency, MHz"
    INITIAL_MASS_FRACTION_OF_SOLUTE = "Initial mass fraction of solute"
    INITIAL_MOLALITY_OF_SOLUTE_MOLKG = "Initial molality of solute, mol/kg"
    INITIAL_MOLE_FRACTION_OF_SOLUTE = "Initial mole fraction of solute"
    LOWER_PRESSURE_KPA = "Lower pressure, kPa"
    LOWER_TEMPERATURE_K = "Lower temperature, K"
    MASS_DENSITY_KGM3 = "Mass density, kg/m3"
    MASS_FRACTION = "Mass fraction"
    MASS_KG = "Mass, kg"
    MASS_RATIO_OF_SOLUTE_TO_SOLVENT = "Mass ratio of solute to solvent"
    MOLALITY_MOLKG = "Molality, mol/kg"
    MOLAR_ENTROPY_JKMOL = "Molar entropy, J/K/mol"
    MOLAR_VOLUME_M3MOL = "Molar volume, m3/mol"
    MOLE_FRACTION = "Mole fraction"
    PARTIAL_PRESSURE_KPA = "Partial pressure, kPa"
    PRESSURE_KPA = "Pressure, kPa"
    RATIO_OF_AMOUNT_OF_SOLUTE_TO_MASS_OF_SOLUTION_MOLKG = "Ratio of amount of solute to mass of solution, mol/kg"
    RATIO_OF_MASS_OF_SOLUTE_TO_VOLUME_OF_SOLUTION_KGM3 = "Ratio of mass of solute to volume of solution, kg/m3"
    RELATIVE_ACTIVITY = "(Relative) activity"
    SOLVENT_AMOUNT_CONCENTRATION_MOLARITY_MOLDM3 = "Solvent: Amount concentration (molarity), mol/dm3"
    SOLVENT_AMOUNT_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT = "Solvent: Amount ratio of component to other component of binary solvent"
    SOLVENT_MASS_FRACTION = "Solvent: Mass fraction"
    SOLVENT_MASS_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT = "Solvent: Mass ratio of component to other component of binary solvent"
    SOLVENT_MOLALITY_MOLKG = "Solvent: Molality, mol/kg"
    SOLVENT_MOLE_FRACTION = "Solvent: Mole fraction"
    SOLVENT_RATIO_OF_AMOUNT_OF_COMPONENT_TO_MASS_OF_SOLVENT_MOLKG = "Solvent: Ratio of amount of component to mass of solvent, mol/kg"
    SOLVENT_RATIO_OF_COMPONENT_MASS_TO_VOLUME_OF_SOLVENT_KGM3 = "Solvent: Ratio of component mass to volume of solvent, kg/m3"
    SOLVENT_VOLUME_FRACTION = "Solvent: Volume fraction"
    SOLVENT_VOLUME_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT = "Solvent: Volume ratio of component to other component of binary solvent"
    SPECIFIC_VOLUME_M3KG = "Specific volume, m3/kg"
    TEMPERATURE_K = "Temperature, K"
    UPPER_PRESSURE_KPA = "Upper pressure, kPa"
    UPPER_TEMPERATURE_K = "Upper temperature, K"
    VOLUME_FRACTION = "Volume fraction"
    VOLUME_RATIO_OF_SOLUTE_TO_SOLVENT = "Volume ratio of solute to solvent"
    WAVELENGTH_NM = "Wavelength, nm"