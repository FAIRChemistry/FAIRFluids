```mermaid
classDiagram
    %% Class definitions with attributes
    class FAIRFluidsDocument {
        +version?: Version
        +citation?: Citation
        +compound[0..*]: Compound
        +fluid[0..*]: Fluid
    }

    class Version {
        +versionMajor?: integer
        +versionMinor?: integer
    }

    class Citation {
        +litType?: LitType
        +author[0..*]: Author
        +doi?: string
        +page?: string
        +pub_name?: string
        +title?: string
        +lit_volume_num?: string
        +url_citation?: string
        +publication_year?: string
    }

    class Author {
        +given_name?: string
        +family_name?: string
        +email?: string
        +orcid?: string
        +affiliation?: string
    }

    class Compound {
        +compoundID?: string
        +pubChemID?: integer
        +commonName?: string
        +SELFIE?: string
        +name_IUPAC?: string
        +standard_InChI?: string
        +standard_InChI_key?: string
    }

    class Fluid {
        +compounds[0..*]: string
        +property[0..*]: Property
        +parameter[0..*]: Parameter
        +measurement[0..*]: Measurement
    }

    class Property {
        +propertyID?: string
        +properties?: Properties
        +unit?: UnitDefinition
    }

    class Parameter {
        +parameterID?: string
        +parameter?: Parameters
        +unit?: UnitDefinition
        +associated_compound?: integer
    }

    class Measurement {
        +measurement_id?: string
        +source_doi?: string
        +propertyValue[0..*]: PropertyValue
        +parameterValue[0..*]: ParameterValue
        +method?: Method
        +method_description?: string
    }

    class PropertyValue {
        +propertyID?: string
        +propValue?: float
        +uncertainty?: float
    }

    class ParameterValue {
        +parameterID?: string
        +paramValue?: float
        +uncertainty?: float
    }

    class UnitDefinition {
        +unitID?: string
        +name?: string
        +base_units[0..*]: BaseUnit
    }

    class BaseUnit {
        +kind?: string
        +exponent?: integer
        +multiplier?: float
        +scale?: float
    }

    %% Enum definitions
    class LitType {
        <<enumeration>>
        ARCHIVEDDOCUMENT
        BOOK
        CONFERENCEPROCEEDINGS
        JOURNAL
        PATENT
        PERSONALCORRESPONDENCE
        PUBLISHEDTRANSLATION
        REPORT
        THESIS
        UNSPECIFIED
    }

    class Method {
        <<enumeration>>
        CALCULATED
        LITERATURE
        MEASURED
        SIMULATED
    }

    class Properties {
        <<enumeration>>
        BOILING_POINT
        COMPRESSIBILITY
        DENSITY
        MELTING_POINT
        PH
        POLARITY
        SPECIFIC_HEAT_CAPACITY
        THERMAL_CONDUCTIVITY
        VAPOR_PRESSURE
        VISCOSITY
    }

    class Parameters {
        <<enumeration>>
        ACTIVITY_COEFFICIENT
        AMOUNT_CONCENTRATION_MOLARITY_MOLDM3
        AMOUNT_DENSITY_MOLM3
        AMOUNT_MOL
        AMOUNT_RATIO_OF_SOLUTE_TO_SOLVENT
        FINAL_MASS_FRACTION_OF_SOLUTE
        FINAL_MOLALITY_OF_SOLUTE_MOLKG
        FINAL_MOLE_FRACTION_OF_SOLUTE
        FREQUENCY_MHZ
        INITIAL_MASS_FRACTION_OF_SOLUTE
        INITIAL_MOLALITY_OF_SOLUTE_MOLKG
        INITIAL_MOLE_FRACTION_OF_SOLUTE
        LOWER_PRESSURE_KPA
        LOWER_TEMPERATURE_K
        MASS_DENSITY_KGM3
        MASS_FRACTION
        MASS_KG
        MASS_RATIO_OF_SOLUTE_TO_SOLVENT
        MOLALITY_MOLKG
        MOLAR_ENTROPY_JKMOL
        MOLAR_VOLUME_M3MOL
        MOLE_FRACTION
        PARTIAL_PRESSURE_KPA
        PRESSURE_KPA
        RATIO_OF_AMOUNT_OF_SOLUTE_TO_MASS_OF_SOLUTION_MOLKG
        RATIO_OF_MASS_OF_SOLUTE_TO_VOLUME_OF_SOLUTION_KGM3
        RELATIVE_ACTIVITY
        SOLVENT_AMOUNT_CONCENTRATION_MOLARITY_MOLDM3
        SOLVENT_AMOUNT_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT
        SOLVENT_MASS_FRACTION
        SOLVENT_MASS_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT
        SOLVENT_MOLALITY_MOLKG
        SOLVENT_MOLE_FRACTION
        SOLVENT_RATIO_OF_AMOUNT_OF_COMPONENT_TO_MASS_OF_SOLVENT_MOLKG
        SOLVENT_RATIO_OF_COMPONENT_MASS_TO_VOLUME_OF_SOLVENT_KGM3
        SOLVENT_VOLUME_FRACTION
        SOLVENT_VOLUME_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT
        SPECIFIC_VOLUME_M3KG
        TEMPERATURE_K
        UPPER_PRESSURE_KPA
        UPPER_TEMPERATURE_K
        VOLUME_FRACTION
        VOLUME_RATIO_OF_SOLUTE_TO_SOLVENT
        WAVELENGTH_NM
    }

    %% Relationships
    FAIRFluidsDocument "1" <|-- "1" Version
    FAIRFluidsDocument "1" <|-- "1" Citation
    FAIRFluidsDocument "1" <|-- "*" Compound
    FAIRFluidsDocument "1" <|-- "*" Fluid
    Citation "1" <|-- "1" LitType
    Citation "1" <|-- "*" Author
    Fluid "1" <|-- "*" Property
    Fluid "1" <|-- "*" Parameter
    Fluid "1" <|-- "*" Measurement
    Property "1" <|-- "1" Properties
    Property "1" <|-- "1" UnitDefinition
    Parameter "1" <|-- "1" Parameters
    Parameter "1" <|-- "1" UnitDefinition
    Measurement "1" <|-- "*" PropertyValue
    Measurement "1" <|-- "*" ParameterValue
    Measurement "1" <|-- "1" Method
    UnitDefinition "1" <|-- "*" BaseUnit
```