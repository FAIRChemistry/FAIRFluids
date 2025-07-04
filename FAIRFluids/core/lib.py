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

    version: Version = Field(
        default=...,
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
        description="""Specifcations of the Fluid""",
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
        pubChemID: Optional[int]= None,
        compound_identifier: Optional[C_id]= None,
        commonName: Optional[str]= None,
        SELFIE: Optional[str]= None,
        name_IUPAC: Optional[str]= None,
        standard_InChI: Optional[str]= None,
        standard_InChI_key: Optional[str]= None,
        **kwargs,
    ):
        params = {
            "pubChemID": pubChemID,
            "compound_identifier": compound_identifier,
            "commonName": commonName,
            "SELFIE": SELFIE,
            "name_IUPAC": name_IUPAC,
            "standard_InChI": standard_InChI,
            "standard_InChI_key": standard_InChI_key
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.compound.append(
            Compound(**params)
        )

        return self.compound[-1]


    def add_to_fluid(
        self,
        components: list[str]= [],
        source_doi: Optional[str]= None,
        property: Optional[Property]= None,
        variable: Optional[Variable]= None,
        constraint: list[Constraint]= [],
        num_value: Optional[NumValue]= None,
        **kwargs,
    ):
        params = {
            "components": components,
            "source_doi": source_doi,
            "property": property,
            "variable": variable,
            "constraint": constraint,
            "num_value": num_value
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

    Type: Optional[str] = Field(
        default=None,
        description="""indicates the type of source document (book,
        journal, report, patent, thesis,
        conference proceedings, archived document,
        personal correspondence, published
        translation, unspecified).""",
    )
    author: list[Author] = Field(
        default_factory=list,
        description="""X""",
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
        given_name: str,
        family_name: str,
        **kwargs,
    ):
        params = {
            "given_name": given_name,
            "family_name": family_name
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

    given_name: str = Field(
        default=...,
        description="""Name of the Author""",
    )
    family_name: str = Field(
        default=...,
        description="""Family name ot the author or contributor""",
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

    pubChemID: Optional[int] = Field(
        default=None,
        description="""PubChemID of the Compound""",
    )
    compound_identifier: Optional[C_id] = Field(
        default=None,
        description="""Unique Id of the compund in this datareport""",
    )
    commonName: Optional[str] = Field(
        default=None,
        description="""The generic name of a substance, e.g. H20 - Water""",
    )
    SELFIE: Optional[str] = Field(
        default=None,
        description="""""",
    )
    name_IUPAC: Optional[str] = Field(
        default=None,
        description="""""",
    )
    standard_InChI: Optional[str] = Field(
        default=None,
        description="""""",
    )
    standard_InChI_key: Optional[str] = Field(
        default=None,
        description="""""",
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


class C_id(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    c_id: Optional[str] = Field(
        default=None,
        description="""Unique id of the compound""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:C_id/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:C_id",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
            "c_id": {
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

    components: list[str] = Field(
        default_factory=list,
        description="""Add the ID of the compund into the fluid""",
    )
    source_doi: Optional[str] = Field(
        default=None,
        description="""The source where the data come form""",
    )
    property: Optional[Property] = Field(
        default=None,
        description="""Property[] complex (Fig. 8) is characterized
        by Property-MethodID[] complex , which
        identifies the property and experimental
        method used;""",
    )
    variable: Optional[Variable] = Field(
        default=None,
        description="""A variable refers to an independent experimental
        parameter that varies across data points
        within a data set. Examples include
        temperature, pressure, composition,
        and other input conditions under which
        thermodynamic properties are measured.""",
    )
    constraint: list[Constraint] = Field(
        default_factory=list,
        description="""A constraint refers to a condition or a fixed
        parameter that applies to an entire data
        set, rather than to each individual data
        point. Constraints are used to define
        experimental or calculated conditions
        that remain constant across all the
        measurements in a data set. Examples might
        include fixed composition, pressure, or
        volume during an experiment.""",
    )
    num_value: Optional[NumValue] = Field(
        default=None,
        description="""Actual meassurement data""",
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
            "components": {
                "@type": "@id",
            },
        }
    )

    def filter_constraint(self, **kwargs) -> list[Constraint]:
        """Filters the constraint attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[Constraint]: The filtered list of Constraint objects
        """

        return FilterWrapper[Constraint](self.constraint, **kwargs).filter()


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


    def add_to_constraint(
        self,
        compound_identifier: Optional[C_id]= None,
        constraint_type: Optional[ConstraintVariableType]= None,
        constraint_digits: Optional[int]= None,
        constraint_value: Optional[float]= None,
        constraint_number: Optional[int]= None,
        **kwargs,
    ):
        params = {
            "compound_identifier": compound_identifier,
            "constraint_type": constraint_type,
            "constraint_digits": constraint_digits,
            "constraint_value": constraint_value,
            "constraint_number": constraint_number
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.constraint.append(
            Constraint(**params)
        )

        return self.constraint[-1]


class Property(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    propertyID: Optional[str] = Field(
        default=None,
        description="""Unique ID of the fluid property""",
    )
    property_group: Optional[Property_Group] = Field(
        default=None,
        description="""An identfication to which group the porperty
        belongs to""",
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


class Property_Group(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    group: Optional[str] = Field(
        default=None,
        description="""To which group does the property belong:
        volumetricProp _ , TransportProp,
        HeatCapacityAndDerivedProp,
        ExcessPartialApparentEnergyProp,
        CompositionAtPhaseEquilibrium""",
    )
    method: Optional[str] = Field(
        default=None,
        description="""How was the property obtained. (Maybe add
        prediction field)""",
    )
    property_name: Optional[str] = Field(
        default=None,
        description="""What is the name of the property, eg. Mass
        Density, (and Units?)""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:Property_Group/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:Property_Group",
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


class Variable(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    variableID: Optional[str] = Field(
        default=None,
        description="""""",
    )
    variableType: Optional[ConstraintVariableType] = Field(
        default=None,
        description="""eTemperture, ePressure, eComponentCompositon,
        eSolventComposition, eMiscellanous""",
    )
    variableName: Optional[str] = Field(
        default=None,
        description="""Name of the Variable- e.g. Temerpature""",
    )
    componentID: Optional[int] = Field(
        default=None,
        description="""Add to Identify to which compound the variable
        applies to""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:Variable/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:Variable",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
            "variableID": {
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


class Constraint(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    compound_identifier: Optional[C_id] = Field(
        default=None,
        description="""""",
    )
    constraint_type: Optional[ConstraintVariableType] = Field(
        default=None,
        description="""Description what constraint is applicaple to the
        data. E.g. Pressure""",
    )
    constraint_digits: Optional[int] = Field(
        default=None,
        description="""""",
    )
    constraint_value: Optional[float] = Field(
        default=None,
        description="""""",
    )
    constraint_number: Optional[int] = Field(
        default=None,
        description="""""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:Constraint/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:Constraint",
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


class ConstraintVariableType(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    e_bio_variables: Optional[eBioVariables] = Field(
        default=None,
        description="""""",
    )
    e_component_composition: Optional[eComponentComposition] = Field(
        default=None,
        description="""""",
    )
    e_miscellaneous: Optional[eMiscellaneous] = Field(
        default=None,
        description="""""",
    )
    e_participant_amount: Optional[eParticipantAmount] = Field(
        default=None,
        description="""""",
    )
    e_pressure: Union[None,ePressure,str] = Field(
        default=None,
        description="""""",
    )
    e_solvent_composition: Optional[eSolventComposition] = Field(
        default=None,
        description="""""",
    )
    e_temperature: Optional[eTemperature] = Field(
        default=None,
        description="""""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:ConstraintVariableType/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:ConstraintVariableType",
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


class NumValue(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    propertyValue: Optional[PropertyValue] = Field(
        default=None,
        description="""""",
    )
    variableValue: Optional[VariableValue] = Field(
        default=None,
        description="""""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:NumValue/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:NumValue",
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

    propDigits: Optional[int] = Field(
        default=None,
        description="""""",
    )
    propNumber: Optional[str] = Field(
        default=None,
        description="""""",
    )
    propValue: Optional[float] = Field(
        default=None,
        description="""Actual value of the property""",
    )
    uncertainty: Optional[float] = Field(
        default=None,
        description="""""",
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
            "propNumber": {
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


class VariableValue(BaseModel):

    model_config: ConfigDict = ConfigDict( # type: ignore
        validate_assignment = True,
    ) # type: ignore

    varDigits: Optional[int] = Field(
        default=None,
        description="""""",
    )
    varNumber: Optional[str] = Field(
        default=None,
        description="""""",
    )
    varValue: Optional[float] = Field(
        default=None,
        description="""Actual value of the variable""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "fairfluids:VariableValue/" + str(uuid4())
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory = lambda: [
            "fairfluids:VariableValue",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory = lambda: {
            "fairfluids": "https://github.com/FAIRChemistry/FAIRFluids",
            "varNumber": {
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


class eType(Enum):
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

class eTemperature(Enum):
    LOWER_TEMPERATURE_K = "'Lower temperature, K'"
    TEMPERATURE_K = "'Temperature, K'"
    UPPER_TEMPERATURE_K = "'Upper temperature, K'"

class ePressure(Enum):
    LOWER_PRESSURE_KPA = "'Lower pressure, kPa'"
    PARTIAL_PRESSURE_KPA = "'Partial pressure, kPa'"
    PRESSURE_KPA = "'Pressure, kPa'"
    UPPER_PRESSURE_KPA = "'Upper pressure, kPa'"

class eComponentComposition(Enum):
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
    IONIC_STRENGTH_AMOUNT_CONCENTRATION_BASIS_MOLDM3 = "'Ionic strength (amount concentration basis), mol/dm3'"
    IONIC_STRENGTH_MOLALITY_BASIS_MOLKG = "'Ionic strength (molality basis), mol/kg'"
    PC_AMOUNT_CONCENTRATION_BASIS = "'pC (amount concentration basis)'"
    PH = "'pH'"
    SOLVENT_PC_AMOUNT_CONCENTRATION_BASIS = "'Solvent: pC (amount concentration basis)'"

class eParticipantAmount(Enum):
    AMOUNT_MOL = "'Amount, mol'"
    MASS_KG = "'Mass, kg'"