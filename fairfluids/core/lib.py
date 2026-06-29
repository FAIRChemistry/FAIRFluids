"""
This file contains Pydantic model definitions for data validation.

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
https://docs.pydantic.dev/

WARNING: This is an auto-generated file.
Do not edit directly - any changes will be overwritten.
"""


## This is a generated file. Do not modify it manually!

from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Generic, TypeVar, Union
from enum import Enum
from uuid import uuid4
from datetime import date, datetime

# Filter Wrapper definition used to filter a list of objects
# based on their attributes
Cls = TypeVar("Cls")

class FilterWrapper(Generic[Cls]):
    """Wrapper class to filter a list of objects based on their attributes"""

    def __init__(self, collection: list[Cls], **kwargs):
        self.collection = collection
        self.kwargs = kwargs

    def filter(self) -> list[Cls]:
        for key, value in self.kwargs.items():
            self.collection = [
                item for item in self.collection if self._fetch_attr(key, item) == value
            ]
        return self.collection

    def _fetch_attr(self, name: str, item: Cls):
        try:
            return getattr(item, name)
        except AttributeError:
            raise AttributeError(f"{item} does not have attribute {name}")


# JSON-LD Helper Functions
def add_namespace(obj, prefix: str | None, iri: str | None):
    """Adds a namespace to the JSON-LD context

    Args:
        prefix (str): The prefix to add
        iri (str): The IRI to add
    """
    if prefix is None and iri is None:
        return
    elif prefix and iri is None:
        raise ValueError("If prefix is provided, iri must also be provided")
    elif iri and prefix is None:
        raise ValueError("If iri is provided, prefix must also be provided")

    obj.ld_context[prefix] = iri # type: ignore

def validate_prefix(term: str | dict, prefix: str):
    """Validates that a term is prefixed with a given prefix

    Args:
        term (str): The term to validate
        prefix (str): The prefix to validate against

    Returns:
        bool: True if the term is prefixed with the prefix, False otherwise
    """

    if isinstance(term, dict) and not term["@id"].startswith(prefix + ":"):
        raise ValueError(f"Term {term} is not prefixed with {prefix}")
    elif isinstance(term, str) and not term.startswith(prefix + ":"):
        raise ValueError(f"Term {term} is not prefixed with {prefix}")

# Model Definitions

class FAIRFluidsDocument(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    version: Optional[Version] = Field(
        default=None,
        description="""Version of the FAIRFluidsDocument""",
    )
    citation: Optional[Citation] = Field(
        default=None,
        description="""Add information about the datareport""",
    )
    compound: list[Compound] = Field(
        default_factory=list,
        description="""What Compounds are in the fluid""",
    )
    fluid: list[Fluid] = Field(
        default_factory=list,
        description="""Specifcations of the Fluid. There can be multible
        Fluids in one document""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:FAIRFluidsDocument/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:FAIRFluidsDocument",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
        }
    )

    def filter_compound(self, **kwargs) -> list[Compound]:
        """Filters the compound attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[Compound]: The filtered list of Compound objects
        """

        return FilterWrapper[Compound](self.compound, **kwargs).filter()

    def filter_fluid(self, **kwargs) -> list[Fluid]:
        """Filters the fluid attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[Fluid]: The filtered list of Fluid objects
        """

        return FilterWrapper[Fluid](self.fluid, **kwargs).filter()


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


    def add_to_compound(
        self,
        compoundID: Optional[str]= None,
        pubChemID: Optional[int]= None,
        commonName: Optional[str]= None,
        SELFIE: Optional[str]= None,
        name_IUPAC: Optional[str]= None,
        standard_InChI: Optional[str]= None,
        standard_InChI_key: Optional[str]= None,
        molar_weigth: Optional[float]= None,
        smiles_code: Optional[str]= None,
        sigma_profile: Optional[int]= None,
        **kwargs,
    ):
        params = {
            "compoundID": compoundID,
            "pubChemID": pubChemID,
            "commonName": commonName,
            "SELFIE": SELFIE,
            "name_IUPAC": name_IUPAC,
            "standard_InChI": standard_InChI,
            "standard_InChI_key": standard_InChI_key,
            "molar_weigth": molar_weigth,
            "smiles_code": smiles_code,
            "sigma_profile": sigma_profile
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.compound.append(
            Compound(**params)
        )

        return self.compound[-1]


    def add_to_fluid(
        self,
        fluidID: list[str]= [],
        compounds: list[str]= [],
        property: list[Property]= [],
        parameter: list[Parameter]= [],
        sample: Optional[Sample]= None,
        fitted_model: list[FittedModel]= [],
        **kwargs,
    ):
        params = {
            "fluidID": fluidID,
            "compounds": compounds,
            "property": property,
            "parameter": parameter,
            "sample": sample,
            "fitted_model": fitted_model
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.fluid.append(
            Fluid(**params)
        )

        return self.fluid[-1]

class Version(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    versionMajor: Optional[int] = Field(
        default=None,
        description="""Add the major version number to your datareport""",
    )
    versionMinor: Optional[int] = Field(
        default=None,
        description="""Add the minor version number to your datareport""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:Version/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:Version",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
        }
    )


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class Citation(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    litType: Optional[LitType] = Field(
        default=None,
        description="""Specifies the type of literature or source
        document. Accepted values include:
        book, journal, report, patent, thesis,
        conference proceedings, archived document,
        personal correspondence, published
        translation, or unspecified.""",
    )
    author: list[Author] = Field(
        default_factory=list,
        description="""A list of authors who contributed to the
        publication. Each entry should include
        structured information such as full name
        and optionally additional metadata like
        affiliation or identifier.""",
    )
    doi: Optional[str] = Field(
        default=None,
        description="""Digital Object Identifier (DOI) for the
        publication. A unique alphanumeric string
        used to identify and provide a permanent
        link to the document online.""",
    )
    page: Optional[str] = Field(
        default=None,
        description="""The page range in which the publication appears,
        typically formatted as a string (e.g.,
        '123–135').""",
    )
    pub_name: Optional[str] = Field(
        default=None,
        description="""The name of the publication source, such as the
        journal title, book title, or conference
        name.""",
    )
    title: Optional[str] = Field(
        default=None,
        description="""The title of the cited work or publication.""",
    )
    lit_volume_num: Optional[str] = Field(
        default=None,
        description="""The volume number of the source publication, if
        applicable (e.g., journal volume).""",
    )
    url_citation: Optional[str] = Field(
        default=None,
        description="""A direct URL link to the publication or citation
        landing page.""",
    )
    publication_year: Optional[str] = Field(
        default=None,
        description="""The year in which the publication was officially
        released or published.""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:Citation/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:Citation",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
        }
    )

    def filter_author(self, **kwargs) -> list[Author]:
        """Filters the author attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[Author]: The filtered list of Author objects
        """

        return FilterWrapper[Author](self.author, **kwargs).filter()


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


    def add_to_author(
        self,
        given_name: Optional[str]= None,
        family_name: Optional[str]= None,
        email: Optional[str]= None,
        orcid: Optional[str]= None,
        affiliation: Optional[str]= None,
        **kwargs,
    ):
        params = {
            "given_name": given_name,
            "family_name": family_name,
            "email": email,
            "orcid": orcid,
            "affiliation": affiliation
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.author.append(
            Author(**params)
        )

        return self.author[-1]


class Author(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    given_name: Optional[str] = Field(
        default=None,
        description="""The given name (first name or personal name) of
        the author or contributor.""",
    )
    family_name: Optional[str] = Field(
        default=None,
        description="""The family name (surname or last name) of the
        author or contributor.""",
    )
    email: Optional[str] = Field(
        default=None,
        description="""The email address of the author, if available.
        Used for contact or identification
        purposes.""",
    )
    orcid: Optional[str] = Field(
        default=None,
        description="""The ORCID iD of the author, a unique, persistent
        identifier used to distinguish researchers
        (e.g., '0000-0002-1825-0097').""",
    )
    affiliation: Optional[str] = Field(
        default=None,
        description="""The name of the institution or organization the
        author is affiliated with at the time of
        publication.""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:Author/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:Author",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
        }
    )


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class Compound(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    compoundID: Optional[str] = Field(
        default=None,
        description="""A unique identifier assigned to the compound
        within the scope of this specific data
        report or dataset. Used for internal
        tracking.""",
    )
    pubChemID: Optional[int] = Field(
        default=None,
        description="""The PubChem Compound Identifier (CID), a unique
        numeric ID assigned by the PubChem
        database to this compound.""",
    )
    commonName: Optional[str] = Field(
        default=None,
        description="""The common or generic name of the compound, such
        as 'Water' for H₂O.""",
    )
    SELFIE: Optional[str] = Field(
        default=None,
        description="""The SELFIES (Self-referencing Embedded Strings)
        representation of the compound’s molecular
        structure. A robust, machine-readable
        encoding for molecules.""",
    )
    name_IUPAC: Optional[str] = Field(
        default=None,
        description="""The full IUPAC (International Union of Pure and
        Applied Chemistry) name of the compound,
        representing its standardized chemical
        nomenclature.""",
    )
    standard_InChI: Optional[str] = Field(
        default=None,
        description="""The Standard International Chemical Identifier
        (InChI) string that uniquely represents
        the compound’s molecular structure.""",
    )
    standard_InChI_key: Optional[str] = Field(
        default=None,
        description="""The hashed version of the InChI string, known
        as the InChIKey. It is a fixed-length,
        easier-to-search identifier for databases
        and indexing.""",
    )
    molar_weigth: Optional[float] = Field(
        default=None,
        description="""The Molar weight in g/mol""",
    )
    smiles_code: Optional[str] = Field(
        default=None,
        description="""""",
    )
    sigma_profile: Optional[int] = Field(
        default=None,
        description="""The sigma profil""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:Compound/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:Compound",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
            "compoundID": {
                "@type": "@id",
            },
        }
    )


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class Fluid(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    fluidID: list[str] = Field(
        default_factory=list,
        description="""""",
    )
    compounds: list[str] = Field(
        default_factory=list,
        description="""A list of unique identifiers referencing the
        compounds present in the fluid system.
        Multiple identifiers indicate a mixture;
        single entries indicate a pure substance.v""",
    )
    property: list[Property] = Field(
        default_factory=list,
        description="""A list of physical or thermodynamic properties
        that were measured or calculated for the
        fluid. Each property is associated with
        a method identifier (propertyID) that
        defines both the property type (e.g.,
        viscosity, thermal conductivity) and the
        experimental or computational method used.""",
    )
    parameter: list[Parameter] = Field(
        default_factory=list,
        description="""A list of experimental parameters. Parameters
        may vary across data points (e.g.,
        temperature, pressure, composition) or
        serve as constraints that remain fixed
        across the dataset (e.g., constant
        pressure or fixed mole ratio). These
        define the input conditions under which
        properties are observed or measured.""",
    )
    sample: Optional[Sample] = Field(
        default=None,
        description="""Sample""",
    )
    fitted_model: list[FittedModel] = Field(
        default_factory=list,
        description="""Models fitted to subsets of this fluid's
        measurements (e.g. Arrhenius/VFT
        regression or Bayesian posteriors).
        Each entry stores the derived parameters
        together with their uncertainties
        expressed according to the GUM (Guide
        to the Expression of Uncertainty in
        Measurement).""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:Fluid/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:Fluid",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
            "fluidID": {
                "@type": "@id",
            },
            "compounds": {
                "@type": "@id",
            },
        }
    )

    def filter_property(self, **kwargs) -> list[Property]:
        """Filters the property attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[Property]: The filtered list of Property objects
        """

        return FilterWrapper[Property](self.property, **kwargs).filter()

    def filter_parameter(self, **kwargs) -> list[Parameter]:
        """Filters the parameter attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[Parameter]: The filtered list of Parameter objects
        """

        return FilterWrapper[Parameter](self.parameter, **kwargs).filter()

    def filter_fitted_model(self, **kwargs) -> list[FittedModel]:
        """Filters the fitted_model attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[FittedModel]: The filtered list of FittedModel objects
        """

        return FilterWrapper[FittedModel](self.fitted_model, **kwargs).filter()


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


    def add_to_property(
        self,
        propertyID: Optional[str]= None,
        properties: Optional[Properties]= None,
        unit: Optional[UnitDefinition]= None,
        **kwargs,
    ):
        params = {
            "propertyID": propertyID,
            "properties": properties,
            "unit": unit
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.property.append(
            Property(**params)
        )

        return self.property[-1]


    def add_to_parameter(
        self,
        parameterID: Optional[str]= None,
        parameters: Optional[Parameters]= None,
        unit: Optional[UnitDefinition]= None,
        associated_compounds: list[str]= [],
        **kwargs,
    ):
        params = {
            "parameterID": parameterID,
            "parameters": parameters,
            "unit": unit,
            "associated_compounds": associated_compounds
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.parameter.append(
            Parameter(**params)
        )

        return self.parameter[-1]


    def add_to_fitted_model(
        self,
        modelID: Optional[str]= None,
        model_name: Optional[str]= None,
        model_equation: Optional[str]= None,
        method: Optional[FitMethod]= None,
        method_description: Optional[str]= None,
        fitted_property: Optional[Properties]= None,
        parameter: list[FittedParameter]= [],
        covariance: list[float]= [],
        r_squared: Optional[float]= None,
        n_points: Optional[int]= None,
        temperature_lower: Optional[float]= None,
        temperature_upper: Optional[float]= None,
        applied_parameters: list[ParameterValue]= [],
        source_measurement_ids: list[str]= [],
        **kwargs,
    ):
        params = {
            "modelID": modelID,
            "model_name": model_name,
            "model_equation": model_equation,
            "method": method,
            "method_description": method_description,
            "fitted_property": fitted_property,
            "parameter": parameter,
            "covariance": covariance,
            "r_squared": r_squared,
            "n_points": n_points,
            "temperature_lower": temperature_lower,
            "temperature_upper": temperature_upper,
            "applied_parameters": applied_parameters,
            "source_measurement_ids": source_measurement_ids
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.fitted_model.append(
            FittedModel(**params)
        )

        return self.fitted_model[-1]

class Property(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    propertyID: Optional[str] = Field(
        default=None,
        description="""A unique identifier for the specific property
        being reported (e.g., viscosity, density,
        heat capacity).""",
    )
    properties: Optional[Properties] = Field(
        default=None,
        description="""Indicates the broader category or group to which
        the property belongs (e.g., thermodynamic,
        transport, phase behavior). Used to
        organize related properties.""",
    )
    unit: Optional[UnitDefinition] = Field(
        default=None,
        description="""""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:Property/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:Property",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
            "propertyID": {
                "@type": "@id",
            },
        }
    )


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class Parameter(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    parameterID: Optional[str] = Field(
        default=None,
        description="""A unique identifier for this parameter within
        the dataset. Used for referencing in
        conjunction with numerical values.""",
    )
    parameters: Optional[Parameters] = Field(
        default=None,
        description="""The type or name of the parameter being varied,
        such as temperature, pressure, or mole
        fraction. Indicates what was controlled or
        changed during the experiment.""",
    )
    unit: Optional[UnitDefinition] = Field(
        default=None,
        description="""""",
    )
    associated_compounds: list[str] = Field(
        default_factory=list,
        description="""Identifies the specific compound (by its index
        or ID) to which this parameter applies.
        Useful in multicomponent systems where a
        parameter (e.g., mole fraction) pertains
        to a specific compound.""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:Parameter/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:Parameter",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
            "parameterID": {
                "@type": "@id",
            },
        }
    )


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class Measurement(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    measurement_id: Optional[str] = Field(
        default=None,
        description="""""",
    )
    source_doi: Optional[str] = Field(
        default=None,
        description="""The Digital Object Identifier (DOI) of the source
        publication or dataset from which the
        fluid data was obtained.""",
    )
    propertyValue: list[PropertyValue] = Field(
        default_factory=list,
        description="""An array of numerical values corresponding to the
        measured or calculated properties (e.g.,
        density, viscosity). Each entry should
        include the value, units, and possibly
        uncertainty or error margins.""",
    )
    parameterValue: list[ParameterValue] = Field(
        default_factory=list,
        description="""An array of numerical values corresponding to
        the parameters that were varied or held
        constant during the experiment (e.g.,
        temperature, pressure). Each entry should
        specify the value, units, and related
        parameter identifier.3""",
    )
    method: Optional[Method] = Field(
        default=None,
        description="""Describes how the property value was obtained.
        Accepted values may include: , , , ,
        or . This field helps distinguish between
        experimental and non-experimental data
        sources.""",
    )
    method_description: Optional[str] = Field(
        default=None,
        description="""A free-text description providing additional
        detail about the method used to generate
        the data (e.g., specific experimental
        setup, calculation model, simulation type,
        or literature source details).""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:Measurement/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:Measurement",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
            "measurement_id": {
                "@type": "@id",
            },
        }
    )

    def filter_propertyValue(self, **kwargs) -> list[PropertyValue]:
        """Filters the propertyValue attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[PropertyValue]: The filtered list of PropertyValue objects
        """

        return FilterWrapper[PropertyValue](self.propertyValue, **kwargs).filter()

    def filter_parameterValue(self, **kwargs) -> list[ParameterValue]:
        """Filters the parameterValue attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[ParameterValue]: The filtered list of ParameterValue objects
        """

        return FilterWrapper[ParameterValue](self.parameterValue, **kwargs).filter()


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


    def add_to_propertyValue(
        self,
        properties: Optional[Properties]= None,
        propertyID: Optional[str]= None,
        propValue: Optional[float]= None,
        uncertainty: Optional[float]= None,
        **kwargs,
    ):
        params = {
            "properties": properties,
            "propertyID": propertyID,
            "propValue": propValue,
            "uncertainty": uncertainty
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.propertyValue.append(
            PropertyValue(**params)
        )

        return self.propertyValue[-1]


    def add_to_parameterValue(
        self,
        parameters: Optional[Parameters]= None,
        parameterID: Optional[str]= None,
        paramValue: Optional[float]= None,
        uncertainty: Optional[float]= None,
        **kwargs,
    ):
        params = {
            "parameters": parameters,
            "parameterID": parameterID,
            "paramValue": paramValue,
            "uncertainty": uncertainty
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.parameterValue.append(
            ParameterValue(**params)
        )

        return self.parameterValue[-1]


class Sample(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    sample_id: Optional[str] = Field(
        default=None,
        description="""""",
    )
    associated_compounds: list[str] = Field(
        default_factory=list,
        description="""""",
    )
    measurement: list[Measurement] = Field(
        default_factory=list,
        description="""A collection of measured or calculated numerical
        data points associated with the specified
        properties and experimental parameters.""",
    )
    storage: Optional[Storage] = Field(
        default=None,
        description="""""",
    )
    preparation: Optional[Preparation] = Field(
        default=None,
        description="""""",
    )
    vendor_chemical: Optional[Vendor_Chemical] = Field(
        default=None,
        description="""""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:Sample/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:Sample",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
            "sample_id": {
                "@type": "@id",
            },
        }
    )

    def filter_measurement(self, **kwargs) -> list[Measurement]:
        """Filters the measurement attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[Measurement]: The filtered list of Measurement objects
        """

        return FilterWrapper[Measurement](self.measurement, **kwargs).filter()


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


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
        params = {
            "measurement_id": measurement_id,
            "source_doi": source_doi,
            "propertyValue": propertyValue,
            "parameterValue": parameterValue,
            "method": method,
            "method_description": method_description
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.measurement.append(
            Measurement(**params)
        )

        return self.measurement[-1]


class Preparation(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    prepMethod: Optional[str] = Field(
        default=None,
        description="""The description on how it was prepared""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:Preparation/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:Preparation",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
        }
    )


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class PropertyValue(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    properties: Optional[Properties] = Field(
        default=None,
        description="""""",
    )
    propertyID: Optional[str] = Field(
        default=None,
        description="""Identifier referencing the property to which this
        value corresponds.""",
    )
    propValue: Optional[float] = Field(
        default=None,
        description="""The actual measured or calculated numerical value
        of the property.""",
    )
    uncertainty: Optional[float] = Field(
        default=None,
        description="""The estimated uncertainty or error margin
        associated with the property value,
        typically representing standard deviation
        or confidence interval.""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:PropertyValue/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:PropertyValue",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
            "propertyID": {
                "@type": "@id",
            },
        }
    )


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class ParameterValue(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    parameters: Optional[Parameters] = Field(
        default=None,
        description="""The type or name of the parameter being varied,
        such as temperature, pressure, or mole
        fraction. Indicates what was controlled or
        changed during the experiment.""",
    )
    parameterID: Optional[str] = Field(
        default=None,
        description="""Identifier referencing the specific parameter this
        value corresponds to.""",
    )
    paramValue: Optional[float] = Field(
        default=None,
        description="""The actual measured or set numerical value of
        the parameter.""",
    )
    uncertainty: Optional[float] = Field(
        default=None,
        description="""The estimated uncertainty or error margin
        associated with the parameter value.""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:ParameterValue/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:ParameterValue",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
            "parameterID": {
                "@type": "@id",
            },
        }
    )


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class FittedModel(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    modelID: Optional[str] = Field(
        default=None,
        description="""A unique identifier for this fitted model within
        the dataset.""",
    )
    model_name: Optional[str] = Field(
        default=None,
        description="""Short machine-readable name of the model, e.g.
        'arrhenius', 'extended_arrhenius' or
        'vft'.""",
    )
    model_equation: Optional[str] = Field(
        default=None,
        description="""Human-readable form of the fitted equation,
        e.g. 'ln(eta) = ln(As) + Ea / (R * T)'.
        Documents what the parameters mean.""",
    )
    method: Optional[FitMethod] = Field(
        default=None,
        description="""How the parameters were obtained (e.g. ordinary
        least squares regression or Bayesian
        Markov chain Monte Carlo).""",
    )
    method_description: Optional[str] = Field(
        default=None,
        description="""Free-text provenance about the fit, such
        as software name and version, prior
        distributions, sampler settings,
        weighting, or any non-default options.""",
    )
    fitted_property: Optional[Properties] = Field(
        default=None,
        description="""The physical property that the model describes
        (e.g. viscosity), linking the fit to the
        standardized property vocabulary.""",
    )
    parameter: list[FittedParameter] = Field(
        default_factory=list,
        description="""The derived parameters of the model, each with its
        value, unit and GUM-style uncertainty.""",
    )
    covariance: list[float] = Field(
        default_factory=list,
        description="""Optional parameter covariance matrix. Row and
        column order follow the order of the
        parameter list. Required to correctly
        propagate correlated parameters into
        predicted quantities.""",
    )
    r_squared: Optional[float] = Field(
        default=None,
        description="""Optional coefficient of determination of the fit,
        as a quick goodness-of-fit indicator.""",
    )
    n_points: Optional[int] = Field(
        default=None,
        description="""Optional number of measurement points used in
        the fit.""",
    )
    temperature_lower: Optional[float] = Field(
        default=None,
        description="""Optional lower bound of the temperature range over
        which the fit is valid, in Kelvin.""",
    )
    temperature_upper: Optional[float] = Field(
        default=None,
        description="""Optional upper bound of the temperature range over
        which the fit is valid, in Kelvin.""",
    )
    applied_parameters: list[ParameterValue] = Field(
        default_factory=list,
        description="""Optional fixed conditions this fit applies
        to, such as the mole fractions of the
        composition. Pins the fit to a specific
        subset of the fluid's data.""",
    )
    source_measurement_ids: list[str] = Field(
        default_factory=list,
        description="""Optional list of measurement identifiers that
        were used in the fit, for provenance and
        traceability.""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:FittedModel/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:FittedModel",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
            "modelID": {
                "@type": "@id",
            },
        }
    )

    def filter_parameter(self, **kwargs) -> list[FittedParameter]:
        """Filters the parameter attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[FittedParameter]: The filtered list of FittedParameter objects
        """

        return FilterWrapper[FittedParameter](self.parameter, **kwargs).filter()

    def filter_applied_parameters(self, **kwargs) -> list[ParameterValue]:
        """Filters the applied_parameters attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[ParameterValue]: The filtered list of ParameterValue objects
        """

        return FilterWrapper[ParameterValue](self.applied_parameters, **kwargs).filter()


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


    def add_to_parameter(
        self,
        name: Optional[str]= None,
        value: Optional[float]= None,
        unit: Optional[UnitDefinition]= None,
        standard_uncertainty: Optional[float]= None,
        uncertainty_evaluation: Optional[UncertaintyEvaluation]= None,
        coverage_factor: Optional[float]= None,
        expanded_uncertainty: Optional[float]= None,
        coverage_probability: Optional[float]= None,
        degrees_of_freedom: Optional[float]= None,
        distribution: Optional[DistributionType]= None,
        interval_low: Optional[float]= None,
        interval_high: Optional[float]= None,
        properties: Optional[Properties]= None,
        **kwargs,
    ):
        params = {
            "name": name,
            "value": value,
            "unit": unit,
            "standard_uncertainty": standard_uncertainty,
            "uncertainty_evaluation": uncertainty_evaluation,
            "coverage_factor": coverage_factor,
            "expanded_uncertainty": expanded_uncertainty,
            "coverage_probability": coverage_probability,
            "degrees_of_freedom": degrees_of_freedom,
            "distribution": distribution,
            "interval_low": interval_low,
            "interval_high": interval_high,
            "properties": properties
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.parameter.append(
            FittedParameter(**params)
        )

        return self.parameter[-1]


    def add_to_applied_parameters(
        self,
        parameters: Optional[Parameters]= None,
        parameterID: Optional[str]= None,
        paramValue: Optional[float]= None,
        uncertainty: Optional[float]= None,
        **kwargs,
    ):
        params = {
            "parameters": parameters,
            "parameterID": parameterID,
            "paramValue": paramValue,
            "uncertainty": uncertainty
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.applied_parameters.append(
            ParameterValue(**params)
        )

        return self.applied_parameters[-1]


class FittedParameter(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    name: Optional[str] = Field(
        default=None,
        description="""Name of the parameter, e.g. 'Ea', 'lnAs', 'B'
        or 'T0'.""",
    )
    value: Optional[float] = Field(
        default=None,
        description="""Best estimate of the parameter. For regression
        this is the fitted coefficient; for
        Bayesian inference it is the posterior
        mean or median.""",
    )
    unit: Optional[UnitDefinition] = Field(
        default=None,
        description="""The unit of the parameter value.""",
    )
    standard_uncertainty: Optional[float] = Field(
        default=None,
        description="""The standard uncertainty u(x) of the parameter,
        i.e. the estimated standard deviation.
        For regression this is the standard error;
        for Bayesian inference it is the posterior
        standard deviation.""",
    )
    uncertainty_evaluation: Optional[UncertaintyEvaluation] = Field(
        default=None,
        description="""How the standard uncertainty was evaluated,
        named explicitly so that no specialized
        background is required to interpret it.""",
    )
    coverage_factor: Optional[float] = Field(
        default=None,
        description="""The factor k by which the standard uncertainty
        is multiplied to obtain the expanded
        uncertainty (e.g. k = 2).""",
    )
    expanded_uncertainty: Optional[float] = Field(
        default=None,
        description="""The expanded uncertainty U = k * u, defining a
        symmetric coverage interval value +/- U.""",
    )
    coverage_probability: Optional[float] = Field(
        default=None,
        description="""The probability that the coverage interval
        contains the value, e.g. 0.95.""",
    )
    degrees_of_freedom: Optional[float] = Field(
        default=None,
        description="""Effective number of degrees of freedom behind the
        uncertainty (e.g. number of points minus
        number of fitted parameters), needed to
        interpret the coverage factor for small
        samples.""",
    )
    distribution: Optional[DistributionType] = Field(
        default=None,
        description="""The distribution assumed or sampled for the
        parameter, which gives meaning to the
        coverage interval.""",
    )
    interval_low: Optional[float] = Field(
        default=None,
        description="""Lower bound of the coverage interval (confidence
        interval for regression, credible interval
        for Bayesian inference).""",
    )
    interval_high: Optional[float] = Field(
        default=None,
        description="""Upper bound of the coverage interval.""",
    )
    properties: Optional[Properties] = Field(
        default=None,
        description="""Optional link to a standardized quantity when
        the parameter corresponds to one (e.g.
        activationEnergy), so that derived
        quantities remain discoverable through the
        property vocabulary.""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:FittedParameter/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:FittedParameter",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
        }
    )


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class UnitDefinition(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    unitID: Optional[str] = Field(
        default=None,
        description="""Unique identifier for the unit definition, used
        for referencing in data fields.""",
    )
    name: Optional[str] = Field(
        default=None,
        description="""Human-readable name of the unit (e.g., 'kilogram
        per cubic meter').""",
    )
    base_units: list[BaseUnit] = Field(
        default_factory=list,
        description="""A list of base unit components that, together with
        exponents, scale, and multipliers, define
        the full derived unit.""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:UnitDefinition/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:UnitDefinition",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
        }
    )

    def filter_base_units(self, **kwargs) -> list[BaseUnit]:
        """Filters the base_units attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[BaseUnit]: The filtered list of BaseUnit objects
        """

        return FilterWrapper[BaseUnit](self.base_units, **kwargs).filter()


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


    def add_to_base_units(
        self,
        kind: Optional[str]= None,
        exponent: Optional[int]= None,
        multiplier: Optional[float]= None,
        scale: Optional[float]= None,
        **kwargs,
    ):
        params = {
            "kind": kind,
            "exponent": exponent,
            "multiplier": multiplier,
            "scale": scale
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.base_units.append(
            BaseUnit(**params)
        )

        return self.base_units[-1]

class BaseUnit(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    kind: Optional[str] = Field(
        default=None,
        description="""The physical quantity represented by the unit
        (e.g., mass, length, time, temperature).""",
    )
    exponent: Optional[int] = Field(
        default=None,
        description="""Exponent applied to the base unit (e.g., m² has
        exponent 2 for 'length').""",
    )
    multiplier: Optional[float] = Field(
        default=None,
        description="""Numerical multiplier applied to the base unit
        (e.g., 1000 for gram when converting to
        kilogram).""",
    )
    scale: Optional[float] = Field(
        default=None,
        description="""Power-of-ten scale factor applied to the unit
        (e.g., 3 for kilo, -6 for micro). Applied
        as 10^scale.""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:BaseUnit/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:BaseUnit",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
        }
    )


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class Storage(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    storage_type: Optional[StorageType] = Field(
        default=None,
        description="""One of: Fresh, Fridge, Open, Closed""",
    )
    storage_conditions: Optional[StorageConditions] = Field(
        default=None,
        description="""What storage conditions have been used for the
        sample""",
    )
    vessel: Optional[Vessel] = Field(
        default=None,
        description="""Type of vessel used for storage""",
    )
    time_prepared: Optional[str] = Field(
        default=None,
        description="""Date, of Sample preparation""",
    )
    time_used: Optional[str] = Field(
        default=None,
        description="""Time when the sample has been used""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:Storage/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:Storage",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
        }
    )


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class StorageConditions(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    Temperature: Optional[float] = Field(
        default=None,
        description="""Temperature under which the sample is stored""",
    )
    Pressure: Optional[float] = Field(
        default=None,
        description="""Pressure under which the sample is stored""",
    )
    gassed: Optional[bool] = Field(
        default=None,
        description="""Wether the sample was degassed""",
    )
    inert: Optional[bool] = Field(
        default=None,
        description="""x""",
    )
    light: Optional[bool] = Field(
        default=None,
        description="""Wether the sample was under light""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:StorageConditions/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:StorageConditions",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
        }
    )


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class Vessel(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    id: Optional[str] = Field(
        default=None,
        description="""Unique identifier of the vessel.""",
    )
    name: Optional[str] = Field(
        default=None,
        description="""Name of the used vessel.""",
    )
    volume: Optional[float] = Field(
        default=None,
        description="""Volumetric value of the vessel.""",
    )
    unit: Optional[UnitDefinition] = Field(
        default=None,
        description="""Unit""",
    )
    constant: Optional[bool] = Field(
        default= True,
        description="""Whether the volume of the vessel is constant or
        not. Default is True.""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:Vessel/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:Vessel",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
        }
    )


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class Vendor_Chemical(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    assciciated_compound: Optional[str] = Field(
        default=None,
        description="""""",
    )
    CAS: Optional[str] = Field(
        default=None,
        description="""""",
    )
    purity: Optional[str] = Field(
        default=None,
        description="""""",
    )
    Vendor: Optional[str] = Field(
        default=None,
        description="""""",
    )
    LOT: Optional[str] = Field(
        default=None,
        description="""""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:Vendor_Chemical/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:Vendor_Chemical",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
            "assciciated_compound": {
                "@type": "@id",
            },
        }
    )


    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert attr in self.model_fields, f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self,
        term: str,
        prefix: str | None = None,
        iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class LitType(Enum):
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
    CALCULATED = "calculated"
    LITERATURE = "literature"
    MEASURED = "measured"
    SIMULATED = "simulated"

class Properties(Enum):
    ACTIVATION_ENERGY = "activationEnergy"
    ACTIVITY = "activity"
    ACTIVITY_COEFFICIENT = "activityCoefficient"
    BOILING_POINT = "boilingPoint"
    COMPRESSIBILITY = "compressibility"
    CRITICAL_DENSITY = "criticalDensity"
    CRITICAL_POINT_PRESSURE = "criticalPointPressure"
    CRITICAL_POINT_TEMPERATURE = "criticalPointTemperature"
    CRITICAL_PRESSURE = "criticalPressure"
    CRITICAL_TEMPERATURE = "criticalTemperature"
    CRITICAL_VOLUME = "criticalVolume"
    DENSITY = "density"
    DIFFUSION_COEFFICIENT = "diffusionCoefficient"
    ELECTRICAL_CONDUCTIVITY = "electricalConductivity"
    EXCESS_MOLAR_ENTHALPY = "excessMolarEnthalpy"
    EXCESS_MOLAR_ENTROPY = "excessMolarEntropy"
    EXCESS_MOLAR_GIBBS_FREE_ENERGY = "excessMolarGibbsFreeEnergy"
    EXCESS_MOLAR_VOLUME = "excessMolarVolume"
    FUGACITY_COEFFICIENT = "fugacityCoefficient"
    GIBBS_FREE_ENERGY = "gibbsFreeEnergy"
    HELMHOLTZ_FREE_ENERGY = "helmholtzFreeEnergy"
    HENRYS_LAW_CONSTANT = "henrysLawConstant"
    IONIC_STRENGTH = "ionicStrength"
    ISOBARIC_EXPANSION_COEFFICIENT = "isobaricExpansionCoefficient"
    ISOTHERMAL_COMPRESSIBILITY = "isothermalCompressibility"
    KINEMATIC_VISCOSITY = "kinematicViscosity"
    MELTING_POINT = "meltingPoint"
    MOLAR_ENTHALPY = "molarEnthalpy"
    MOLAR_ENTROPY = "molarEntropy"
    MOLAR_HEAT_CAPACITY = "molarHeatCapacity"
    MOLAR_VOLUME = "molarVolume"
    OSMOTIC_COEFFICIENT = "osmoticCoefficient"
    PH = "pH"
    POLARITY = "polarity"
    REFRACTIVE_INDEX = "refractiveIndex"
    SOLUBILITY = "solubility"
    SPECIFIC_HEAT_CAPACITY = "specificHeatCapacity"
    SPECIFIC_VOLUME = "specificVolume"
    SPEED_OF_SOUND = "speedOfSound"
    SURFACE_TENSION = "surfaceTension"
    THERMAL_CONDUCTIVITY = "thermalConductivity"
    TRIPLE_POINT_PRESSURE = "triplePointPressure"
    TRIPLE_POINT_TEMPERATURE = "triplePointTemperature"
    VAPOR_PRESSURE = "vaporPressure"
    VISCOSITY = "viscosity"
    WATER_ACTIVITY = "waterActivity"

class Parameters(Enum):
    ACTIVITY_COEFFICIENT = "Activity coefficient"
    AMOUNT_CONCENTRATION_MOLARITY = "Amount concentration (molarity)"
    AMOUNT_DENSITY = "Amount density"
    AMOUNT_MOL = "Amount"
    AMOUNT_RATIO_OF_SOLUTE_TO_SOLVENT = "Amount ratio of solute to solvent"
    FINAL_MASS_FRACTION_OF_SOLUTE = "Final mass fraction of solute"
    FINAL_MOLALITY_OF_SOLUTE = "Final molality of solute"
    FINAL_MOLE_FRACTION_OF_SOLUTE = "Final mole fraction of solute"
    FREQUENCY = "Frequency"
    INITIAL_MASS_FRACTION_OF_SOLUTE = "Initial mass fraction of solute"
    INITIAL_MOLALITY_OF_SOLUTE = "Initial molality of solute"
    INITIAL_MOLE_FRACTION_OF_SOLUTE = "Initial mole fraction of solute"
    LOWER_PRESSURE = "Lower pressure"
    LOWER_TEMPERATURE = "Lower temperature"
    MASS = "Mass"
    MASS_DENSITY = "Mass density"
    MASS_FRACTION = "Mass fraction"
    MASS_RATIO_OF_SOLUTE_TO_SOLVENT = "Mass ratio of solute to solvent"
    MOLALITY = "Molality"
    MOLAR_ENTROPY = "Molar entropy"
    MOLAR_VOLUME = "Molar volume"
    MOLE_FRACTION = "Mole fraction"
    PARTIAL_PRESSURE = "Partial pressure"
    PRESSURE = "Pressure"
    RATIO_OF_AMOUNT_OF_SOLUTE_TO_MASS_OF_SOLUTION = "Ratio of amount of solute to mass of solution"
    RATIO_OF_MASS_OF_SOLUTE_TO_VOLUME_OF_SOLUTION = "Ratio of mass of solute to volume of solution"
    RELATIVE_ACTIVITY = "Relative activity"
    SOLVENT_AMOUNT_CONCENTRATION_MOLARITY = "Solvent: Amount concentration (molarity)"
    SOLVENT_AMOUNT_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT = "Solvent: Amount ratio of component to other component of binary solvent"
    SOLVENT_MASS_FRACTION = "Solvent: Mass fraction"
    SOLVENT_MASS_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT = "Solvent: Mass ratio of component to other component of binary solvent"
    SOLVENT_MOLALITY = "Solvent: Molality"
    SOLVENT_MOLE_FRACTION = "Solvent: Mole fraction"
    SOLVENT_RATIO_OF_AMOUNT_OF_COMPONENT_TO_MASS_OF_SOLVENT = "Solvent: Ratio of amount of component to mass of solvent"
    SOLVENT_RATIO_OF_COMPONENT_MASS_TO_VOLUME_OF_SOLVENT = "Solvent: Ratio of component mass to volume of solvent"
    SOLVENT_VOLUME_FRACTION = "Solvent: Volume fraction"
    SOLVENT_VOLUME_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT = "Solvent: Volume ratio of component to other component of binary solvent"
    SPECIFIC_VOLUME = "Specific volume"
    TEMPERATURE = "Temperature"
    TIME = "Time"
    UPPER_PRESSURE = "Upper pressure"
    UPPER_TEMPERATURE = "Upper temperature"
    VOLUME_FRACTION = "Volume fraction"
    VOLUME_RATIO_OF_SOLUTE_TO_SOLVENT = "Volume ratio of solute to solvent"
    WAVELENGTH = "Wavelength"

class StorageType(Enum):
    CLOSED = "Closed"
    DESSICATOR = "Dessicator"
    FRESH = "Fresh"
    FRIDGE = "Fridge"
    OPEN = "Open"

class FitMethod(Enum):
    BAYESIAN_MCMC = "bayesianMCMC"
    LITERATURE = "literature"
    REGRESSION_NLS = "regressionNLS"
    REGRESSION_OLS = "regressionOLS"

class UncertaintyEvaluation(Enum):
    COMBINED = "combined"
    NON_STATISTICAL = "nonStatistical"
    POSTERIOR = "posterior"
    STATISTICAL = "statistical"

class DistributionType(Enum):
    LOGNORMAL = "lognormal"
    NORMAL = "normal"
    POSTERIOR = "posterior"
    STUDENT_T = "studentT"
    UNIFORM = "uniform"