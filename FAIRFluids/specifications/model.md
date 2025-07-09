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
  - Description: Specifcations of the Fluid

## General information

### Version
- versionMajor
  - Type:integer
  - Description: Add the major version number to your datareport
- versionMinor
  - Type: integer
  - Description: Add the minor version number to your datareport

### Citation
- litType
  - Type:LitType
  - Description: indicates the type of source document (book, journal, report, patent, thesis, conference proceedings, archived document, personal correspondence, published translation, unspecified).
- author
  - Type: Author[]
  - Description: X

    
### Author

Add more Info 
- given_name
  - Type:string
  - Description: Name of the Author
- family_name
  - Type: string
  - Description: Family name ot the author or contributor
  
### Compound
Here the Metadata of each compound are listed.

- pubChemID
  - Type: integer
  -  Description: PubChemID of the Compound
- compound_identifier
  - Type: C_id
  - Description: Unique Id of the compund in this datareport
- commonName
  - Type: string
  - Description: The generic name of a substance, e.g. H20 - Water
- SELFIE
  - Type: string
  - Description: SELFIES Representation from the Molecule
- name_IUPAC
  - Type: string
- standard_InChI
  - Type: string
- standard_InChI_key
  - Type: string

### C_id
- c_id
  - Type: Identifier
  - Description: Unique id of the compound

### Fluid
 This block contains nonbibliographic information about the source of the file contents, identifies the experimental purpose, specifies meta- and numerical data, and specifies the compound (or mixture) and particular samples to which the data are related.

- components
  - Type: Identifier[]
  - Description: Add the ID of the compund into the fluid
- source_doi
  - Type: string
  - Description: The source where the data come form
- property
  - Type: Property
  - Description: Property [complex] (Fig. 8) is characterized by Property-MethodID [complex], which identifies the property and experimental method used;
- parameter
  - Type: Parameter[]
  - Description:  A variable refers to an independent experimental parameter that varies across data points within a data set. Examples include temperature, pressure, composition, and other input conditions under which thermodynamic properties are measured. A constraint refers to a condition or a fixed parameter that applies to an entire data set, rather than to each individual data point. Constraints are used to define experimental or calculated conditions that remain constant across all the measurements in a data set. Examples might include fixed composition, pressure, or volume during an experiment.
- num_value
  - Type:NumValue
  - Description: Actual meassurement data

### Property
Definition: This is the main quantity being measured or reported.
- propertyID
  - Type: Identifier
  - Description: Unique ID of the fluid property
- property_information
  - Type: Property_Information
  - Description: An identfication to which group the porperty belongs to

### Property_Information
How was the Property Derived, how was it calculated, etc.
- group
  - Type: string
  - Description: To which group does the property belong: volumetricProp_, TransportProp, HeatCapacityAndDerivedProp, ExcessPartialApparentEnergyProp, CompositionAtPhaseEquilibrium
- method
  - Type: string
  - Description: How was the property obtained. (Maybe add prediction field)
- property_name
  - Type: string
  - Description: What is the name of the property, eg. Mass Density, (and Units?)
  
### Parameter
Definition: A quantity that was varied during the experiment to observe its effect on the Property.
- parameterID
  - Type: Identifier
- parameterType
  - Type: ParameterType
  - Description: Name of the Variable- e.g. Temerpature
- componentID
  - Type: integer
  - Description: Add to Identify to which compound the variable applies to

### ParameterType
- bio_variables
  - Type: BioVariables
- component_composition
  - Type: ComponentComposition
- miscellaneous
  - Type: Miscellaneous
- participant_amount
  - Type: ParticipantAmount
- pressure
  - Type: Pressure
- solvent_composition
  - Type: SolventComposition
- temperature
  - Type: Temperature

### NumValue
- propertyValue
  - Type: PropertyValue
- parameterValue
  - Type: ParameterValue
  
### PropertyValue
- propDigits
  - Type: integer
- propNumber
  - Type: Identifier
- propValue
  - Type: float
  - Description: Actual value of the property
- uncertainty
  - Type: float

### ParameterValue
- varDigits
  - Type: integer
- varNumber
  - Type: Identifier
- varValue
  - Type: float
  - Description: Actual value of the variable
  

## Enumerations

### LitType

```python
BOOK = 'book'
JOURNAL = 'journal'
REPORT = 'report'
PATENT = 'patent'
THESIS = 'thesis'
CONFERENCEPROCEEDINGS = 'conferenceProceedings'
ARCHIVEDDOCUMENT = 'archivedDocument'
PERSONALCORRESPONDENCE = 'personalCorrespondence'
PUBLISHEDTRANSLATION = 'publishedTranslation'
UNSPECIFIED = 'unspecified'
```

### Temperature

```python
TEMPERATURE_K = 'Temperature, K'
UPPER_TEMPERATURE_K = 'Upper temperature, K'
LOWER_TEMPERATURE_K = 'Lower temperature, K'
```

### Pressure

```python
PRESSURE_KPA = 'Pressure, kPa'
PARTIAL_PRESSURE_KPA = 'Partial pressure, kPa'
UPPER_PRESSURE_KPA = 'Upper pressure, kPa'
LOWER_PRESSURE_KPA = 'Lower pressure, kPa'
```

### ComponentComposition

```python
MOLE_FRACTION = 'Mole fraction'
MASS_FRACTION = 'Mass fraction'
MOLALITY_MOLKG = 'Molality, mol/kg'
AMOUNT_CONCENTRATION_MOLARITY_MOLDM3 = 'Amount concentration (molarity), mol/dm3'
VOLUME_FRACTION = 'Volume fraction'
RATIO_OF_AMOUNT_OF_SOLUTE_TO_MASS_OF_SOLUTION_MOLKG = 'Ratio of amount of solute to mass of solution, mol/kg'
RATIO_OF_MASS_OF_SOLUTE_TO_VOLUME_OF_SOLUTION_KGM3 = 'Ratio of mass of solute to volume of solution, kg/m3'
AMOUNT_RATIO_OF_SOLUTE_TO_SOLVENT = 'Amount ratio of solute to solvent'
MASS_RATIO_OF_SOLUTE_TO_SOLVENT = 'Mass ratio of solute to solvent'
VOLUME_RATIO_OF_SOLUTE_TO_SOLVENT = 'Volume ratio of solute to solvent'
INITIAL_MOLE_FRACTION_OF_SOLUTE = 'Initial mole fraction of solute'
FINAL_MOLE_FRACTION_OF_SOLUTE = 'Final mole fraction of solute'
INITIAL_MASS_FRACTION_OF_SOLUTE = 'Initial mass fraction of solute'
FINAL_MASS_FRACTION_OF_SOLUTE = 'Final mass fraction of solute'
INITIAL_MOLALITY_OF_SOLUTE_MOLKG = 'Initial molality of solute, mol/kg'
FINAL_MOLALITY_OF_SOLUTE_MOLKG = 'Final molality of solute, mol/kg'
```

### SolventComposition

```python
SOLVENT_MOLE_FRACTION = 'Solvent: Mole fraction'
SOLVENT_MASS_FRACTION = 'Solvent: Mass fraction'
SOLVENT_VOLUME_FRACTION = 'Solvent: Volume fraction'
SOLVENT_MOLALITY_MOLKG = 'Solvent: Molality, mol/kg'
SOLVENT_AMOUNT_CONCENTRATION_MOLARITY_MOLDM3 = 'Solvent: Amount concentration (molarity), mol/dm3'
SOLVENT_AMOUNT_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT = 'Solvent: Amount ratio of component to other component of binary solvent'
SOLVENT_MASS_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT = 'Solvent: Mass ratio of component to other component of binary solvent'
SOLVENT_VOLUME_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT = 'Solvent: Volume ratio of component to other component of binary solvent'
SOLVENT_RATIO_OF_AMOUNT_OF_COMPONENT_TO_MASS_OF_SOLVENT_MOLKG = 'Solvent: Ratio of amount of component to mass of solvent, mol/kg'
SOLVENT_RATIO_OF_COMPONENT_MASS_TO_VOLUME_OF_SOLVENT_KGM3 = 'Solvent: Ratio of component mass to volume of solvent, kg/m3'
```

### Miscellaneous

```python
WAVELENGTH_NM = 'Wavelength, nm'
FREQUENCY_MHZ = 'Frequency, MHz'
MOLAR_VOLUME_M3MOL = 'Molar volume, m3/mol'
SPECIFIC_VOLUME_M3KG = 'Specific volume, m3/kg'
MASS_DENSITY_KGM3 = 'Mass density, kg/m3'
AMOUNT_DENSITY_MOLM3 = 'Amount density, mol/m3'
MOLAR_ENTROPY_JKMOL = 'Molar entropy, J/K/mol'
RELATIVE_ACTIVITY = '(Relative) activity'
ACTIVITY_COEFFICIENT = 'Activity coefficient'
```

### BioVariables

```python
PH = 'pH'
IONIC_STRENGTH_MOLALITY_BASIS_MOLKG = 'Ionic strength (molality basis), mol/kg'
IONIC_STRENGTH_AMOUNT_CONCENTRATION_BASIS_MOLDM3 = 'Ionic strength (amount concentration basis), mol/dm3'
PC_AMOUNT_CONCENTRATION_BASIS = 'pC (amount concentration basis)'
SOLVENT_PC_AMOUNT_CONCENTRATION_BASIS = 'Solvent: pC (amount concentration basis)'
```

### ParticipantAmount

```python
AMOUNT_MOL = 'Amount, mol'
MASS_KG = 'Mass, kg'
```