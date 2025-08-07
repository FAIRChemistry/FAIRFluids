---
repo: "https://github.com/FAIRChemistry/FAIRFluids"
prefix: "fairfluids"
---

# FAIRFluids
Description

## Root Objects

### FAIRFluidsDocument
----Description

- version
  - Type:Version
  - Description: Version of the FAIRFluidsDocument
- citation
  - Type: Citation
  - Description: Add information about the datareport
- compound
  - Type: Compound[]
  - Description: What Compounds are in the fluid
- fluid
  - Type: Fluid []
  - Description: Specifcations of the Fluid. There can be multible Fluids in one document

## General information

### Version
- versionMajor
  - Type: integer
  - Description: Add the major version number to your datareport
- versionMinor
  - Type: integer
  - Description: Add the minor version number to your datareport

### Citation
- litType
  - Type: LitType
  - Description: Specifies the type of literature or source document. Accepted values include: book, journal, report, patent, thesis, conference proceedings, archived document, personal correspondence, published translation, or unspecified.
- author
  - Type: Author[]
  - Description: A list of authors who contributed to the publication. Each entry should include structured information such as full name and optionally additional metadata like affiliation or identifier.
- doi
  - Type: string
  - Description: Digital Object Identifier (DOI) for the publication. A unique alphanumeric string used to identify and provide a permanent link to the document online.
- page
  - Type: string
  - Description: The page range in which the publication appears, typically formatted as a string (e.g., '123–135').
- pub_name
  - Type: string
  - Description: The name of the publication source, such as the journal title, book title, or conference name.
- title
  - Type: string
  - Description: The title of the cited work or publication.
- lit_volume_num
  - Type: string
  - Description: The volume number of the source publication, if applicable (e.g., journal volume).
- url_citation
  - Type: string
  - Description: A direct URL link to the publication or citation landing page.
- publication_year
  - Type: string
  - Description: The year in which the publication was officially released or published.


    
### Author

Description: Represents an individual contributor or creator of the cited work. Each author entry includes identifying details such as name, contact information, unique identifiers, and institutional affiliation.
- given_name
  - Type: string
  - Description: The given name (first name or personal name) of the author or contributor.
- family_name
  - Type: string
  - Description: The family name (surname or last name) of the author or contributor.
- email
  - Type: string
  - Description: The email address of the author, if available. Used for contact or identification purposes.
- orcid
  - Type: string
  - Description: The ORCID iD of the author, a unique, persistent identifier used to distinguish researchers (e.g., '0000-0002-1825-0097').
- affiliation
  - Type: string
  - Description: The name of the institution or organization the author is affiliated with at the time of publication.



### Compound

Description: Contains metadata for a chemical compound, including identifiers, names, and structural representations. Each entry describes one unique compound referenced in the data report.
- compoundID
  - Type: Identifier
  - Description: A unique identifier assigned to the compound within the scope of this specific data report or dataset. Used for internal tracking.
- pubChemID
  - Type: integer
  - Description: The PubChem Compound Identifier (CID), a unique numeric ID assigned by the PubChem database to this compound.
- commonName
  - Type: string
  - Description: The common or generic name of the compound, such as 'Water' for H₂O.
- SELFIE
  - Type: string
  - Description: The SELFIES (Self-referencing Embedded Strings) representation of the compound’s molecular structure. A robust, machine-readable encoding for molecules.
- name_IUPAC
  - Type: string
  - Description: The full IUPAC (International Union of Pure and Applied Chemistry) name of the compound, representing its standardized chemical nomenclature.
- standard_InChI
  - Type: string
  - Description: The Standard International Chemical Identifier (InChI) string that uniquely represents the compound’s molecular structure.
- standard_InChI_key
  - Type: string
  - Description: The hashed version of the InChI string, known as the InChIKey. It is a fixed-length, easier-to-search identifier for databases and indexing.

### Fluid
Description: Contains metadata and experimental context for a dataset related to a fluid system. This includes the chemical composition (pure substance or mixture), source of the data, properties measured, varying experimental parameters, and the corresponding numerical results. There can exist multible fluids in one document.
- compounds
  - Type: Identifier[]
  - Description: A list of unique identifiers referencing the compounds present in the fluid system. Multiple identifiers indicate a mixture; single entries indicate a pure substance.v
- property
  - Type: Property[]
  - Description: A list of physical or thermodynamic properties that were measured or calculated for the fluid. Each property is associated with a method identifier (propertyID) that defines both the property type (e.g., viscosity, thermal conductivity) and the experimental or computational method used.
- parameter
  - Type: Parameter[]
  - Description: A list of experimental parameters. Parameters may vary across data points (e.g., temperature, pressure, composition) or serve as constraints that remain fixed across the dataset (e.g., constant pressure or fixed mole ratio). These define the input conditions under which properties are observed or measured.
- measurement
  - Type: Measurement[]
  - Description: A collection of measured or calculated numerical data points associated with the specified properties and experimental parameters.




### Property

Description: Defines the primary quantity being measured, calculated, or otherwise reported for a fluid system. Each property includes its identifier, grouping, and methodological context.
- propertyID
  - Type: Identifier
  - Description: A unique identifier for the specific property being reported (e.g., viscosity, density, heat capacity).
- properties
  - Type: Properties
  - Description: Indicates the broader category or group to which the property belongs (e.g., thermodynamic, transport, phase behavior). Used to organize related properties.
- unit
  - Type: UnitDefinition



### Parameter

Description: Represents an independent variable or experimental input that was varied during data collection to observe its effect on a reported property. Parameters can apply globally to the system or specifically to one component in a mixture.
Categorizes the type of experimental or system variable that is being controlled or varied during data collection. Each category represents a specific kind of parameter relevant to fluid or chemical systems.

- parameterID
  - Type: Identifier
  - Description: A unique identifier for this parameter within the dataset. Used for referencing in conjunction with numerical values.
- parameter
  - Type: Parameters
  - Description: The type or name of the parameter being varied, such as temperature, pressure, or mole fraction. Indicates what was controlled or changed during the experiment.
- unit
  - Type: UnitDefinition
- associated_compound
  - Type: string
  - Description: Identifies the specific compound (by its index or ID) to which this parameter applies. Useful in multicomponent systems where a parameter (e.g., mole fraction) pertains to a specific compound.


### Measurement

Description: Contains the numerical data values related to both properties and parameters. These values represent the measured or calculated quantities recorded in the experiment or dataset.
- measurement_id
  - Type: Identifier
- source_doi
  - Type: string
  - Description: The Digital Object Identifier (DOI) of the source publication or dataset from which the fluid data was obtained.
- propertyValue
  - Type: PropertyValue[]
  - Description: An array of numerical values corresponding to the measured or calculated properties (e.g., density, viscosity). Each entry should include the value, units, and possibly uncertainty or error margins.
- parameterValue
  - Type: ParameterValue[]
  - Description: An array of numerical values corresponding to the parameters that were varied or held constant during the experiment (e.g., temperature, pressure). Each entry should specify the value, units, and related parameter identifier.3
- method
  - Type: Method
  - Description: Describes how the property value was obtained. Accepted values may include: `measured`, `calculated`, `simulated`, `predicted`, or `literature`. This field helps distinguish between experimental and non-experimental data sources.
- method_description
  - Type: string
  - Description: A free-text description providing additional detail about the method used to generate the data (e.g., specific experimental setup, calculation model, simulation type, or literature source details).

  
### PropertyValue

Description: Represents a numerical value associated with a specific property measurement, including precision and uncertainty information.
- propertyID
  - Type: Identifier
  - Description: Identifier referencing the property to which this value corresponds.
- propValue
  - Type: float
  - Description: The actual measured or calculated numerical value of the property.
- uncertainty
  - Type: float
  - Description: The estimated uncertainty or error margin associated with the property value, typically representing standard deviation or confidence interval.


### ParameterValue

Description: Represents a numerical value for a parameter that was varied or controlled during the experiment, including precision and uncertainty details.
- parameterID
  - Type: Identifier
  - Description: Identifier referencing the specific parameter this value corresponds to.
- paramValue
  - Type: float
  - Description: The actual measured or set numerical value of the parameter.
- uncertainty
  - Type: float
  - Description: The estimated uncertainty or error margin associated with the parameter value.

### UnitDefinition
- unitID
  - Type: string
  - Description: Unique identifier for the unit definition, used for referencing in data fields.
- name
  - Type: string
  - Description: Human-readable name of the unit (e.g., 'kilogram per cubic meter').
- base_units
  - Type: BaseUnit[]
  - Description: A list of base unit components that, together with exponents, scale, and multipliers, define the full derived unit.

### BaseUnit
- kind
  - Type: string
  - Description: The physical quantity represented by the unit (e.g., mass, length, time, temperature).
- exponent
  - Type: integer
  - Description: Exponent applied to the base unit (e.g., m² has exponent 2 for 'length').
- multiplier
  - Type: float
  - Description: Numerical multiplier applied to the base unit (e.g., 1000 for gram when converting to kilogram).
- scale
  - Type: float
  - Description: Power-of-ten scale factor applied to the unit (e.g., 3 for kilo, -6 for micro). Applied as 10^scale.


## Enumerations

### LitType

```python
BOOK = book
JOURNAL = journal
REPORT = report
PATENT = patent
THESIS = thesis
CONFERENCEPROCEEDINGS = conferenceProceedings
ARCHIVEDDOCUMENT = archivedDocument
PERSONALCORRESPONDENCE = personalCorrespondence
PUBLISHEDTRANSLATION = publishedTranslation
UNSPECIFIED = unspecified
```


### Method
```python
MEASURED = measured, 
CALCULATED =calculated, 
SIMULATED = simulated, 
LITERATURE = literature
```

### Properties

```python
DENSITY = density
SPECIFIC_HEAT_CAPACITY= specificHeatCapacity
THERMAL_CONDUCTIVITY = thermalConductivity
MELTING_POINT=meltingPoint
BOILING_POINT=boilingPoint
VAPOR_PRESSURE=vaporPressure
COMPRESSIBILITY=Compressibility
VISCOSITY=viscosity
PH=pH
POLARITY=polarity
```

### Parameters
```python
TEMPERATURE_K = Temperature, K
UPPER_TEMPERATURE_K = Upper temperature, K
LOWER_TEMPERATURE_K = Lower temperature, K
PRESSURE_KPA = Pressure, kPa
PARTIAL_PRESSURE_KPA = Partial pressure, kPa
UPPER_PRESSURE_KPA = Upper pressure, kPa
LOWER_PRESSURE_KPA = Lower pressure, kPa
MOLE_FRACTION = Mole fraction
MASS_FRACTION = Mass fraction
MOLALITY_MOLKG = Molality, mol/kg
AMOUNT_CONCENTRATION_MOLARITY_MOLDM3 = Amount concentration (molarity), mol/dm3
VOLUME_FRACTION = Volume fraction
RATIO_OF_AMOUNT_OF_SOLUTE_TO_MASS_OF_SOLUTION_MOLKG = Ratio of amount of solute to mass of solution, mol/kg
RATIO_OF_MASS_OF_SOLUTE_TO_VOLUME_OF_SOLUTION_KGM3 = Ratio of mass of solute to volume of solution, kg/m3
AMOUNT_RATIO_OF_SOLUTE_TO_SOLVENT = Amount ratio of solute to solvent
MASS_RATIO_OF_SOLUTE_TO_SOLVENT = Mass ratio of solute to solvent
VOLUME_RATIO_OF_SOLUTE_TO_SOLVENT = Volume ratio of solute to solvent
INITIAL_MOLE_FRACTION_OF_SOLUTE = Initial mole fraction of solute
FINAL_MOLE_FRACTION_OF_SOLUTE = Final mole fraction of solute
INITIAL_MASS_FRACTION_OF_SOLUTE = Initial mass fraction of solute
FINAL_MASS_FRACTION_OF_SOLUTE = Final mass fraction of solute
INITIAL_MOLALITY_OF_SOLUTE_MOLKG = Initial molality of solute, mol/kg
FINAL_MOLALITY_OF_SOLUTE_MOLKG = Final molality of solute, mol/kg
SOLVENT_MOLE_FRACTION = Solvent: Mole fraction
SOLVENT_MASS_FRACTION = Solvent: Mass fraction
SOLVENT_VOLUME_FRACTION = Solvent: Volume fraction
SOLVENT_MOLALITY_MOLKG = Solvent: Molality, mol/kg
SOLVENT_AMOUNT_CONCENTRATION_MOLARITY_MOLDM3 = Solvent: Amount concentration (molarity), mol/dm3
SOLVENT_AMOUNT_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT = Solvent: Amount ratio of component to other component of binary solvent
SOLVENT_MASS_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT = Solvent: Mass ratio of component to other component of binary solvent
SOLVENT_VOLUME_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT = Solvent: Volume ratio of component to other component of binary solvent
SOLVENT_RATIO_OF_AMOUNT_OF_COMPONENT_TO_MASS_OF_SOLVENT_MOLKG = Solvent: Ratio of amount of component to mass of solvent, mol/kg
SOLVENT_RATIO_OF_COMPONENT_MASS_TO_VOLUME_OF_SOLVENT_KGM3 = Solvent: Ratio of component mass to volume of solvent, kg/m3
WAVELENGTH_NM = Wavelength, nm
FREQUENCY_MHZ = Frequency, MHz
MOLAR_VOLUME_M3MOL = Molar volume, m3/mol
SPECIFIC_VOLUME_M3KG = Specific volume, m3/kg
MASS_DENSITY_KGM3 = Mass density, kg/m3
AMOUNT_DENSITY_MOLM3 = Amount density, mol/m3
MOLAR_ENTROPY_JKMOL = Molar entropy, J/K/mol
RELATIVE_ACTIVITY = (Relative) activity
ACTIVITY_COEFFICIENT = Activity coefficient
AMOUNT_MOL = Amount, mol
MASS_KG = Mass, kg
```