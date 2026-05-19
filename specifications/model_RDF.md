---
repo: "https://github.com/FAIRChemistry/FAIRFluids"
prefix: "fairfluids"
---

# FAIRFluids

FAIR-konformes Datenmodell fuer Fluid-Eigenschaften mit explizitem Zustandsraum (Manifold) statt flacher Parameter-Listen. Der Manifold deklariert den physikalisch gueltigen Teilraum, in dem Messwerte leben - inklusive Simplex-Constraints auf Zusammensetzungen (Sumxi = 1), Intervall-Bounds und optionaler Phasenregel-Annotation.

## Root Objects

### FAIRFluidsDocument

Wurzelobjekt eines FAIRFluids-Datensatzes.

- version
  - Type: Version
  - Description: Version of the FAIRFluidsDocument
- citation
  - Type: Citation
  - Description: Add information about the datareport
- compound
  - Type: Compound[]
  - Description: What Compounds are in the fluid
- fluid
  - Type: Fluid[]
  - Description: Specifications of the Fluid. There can be multiple Fluids in one document.


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
  - Description: Specifies the type of literature or source document.
- author
  - Type: Author[]
  - Description: A list of authors who contributed to the publication.
- doi
  - Type: string
  - Description: Digital Object Identifier (DOI) for the publication.
- page
  - Type: string
  - Description: The page range (e.g. '123-135').
- pub_name
  - Type: string
  - Description: Name of the publication source (journal, book, conference).
- title
  - Type: string
  - Description: Title of the cited work.
- lit_volume_num
  - Type: string
  - Description: Volume number of the source publication, if applicable.
- url_citation
  - Type: string
  - Description: Direct URL link to the publication.
- publication_year
  - Type: string
  - Description: Year of publication.

### Author

Represents an individual contributor of the cited work.

- given_name
  - Type: string
  - Description: Given name (first name) of the author.
- family_name
  - Type: string
  - Description: Family name (surname) of the author.
- email
  - Type: string
  - Description: Email address of the author, if available.
- orcid
  - Type: string
  - Description: ORCID iD (e.g. '0000-0002-1825-0097').
- affiliation
  - Type: string
  - Description: Institution affiliation at time of publication.

### Compound

Metadata for a chemical compound.

- compoundID
  - Type: Identifier
  - Description: Unique identifier within this document.
- pubChemID
  - Type: integer
  - Description: PubChem Compound Identifier (CID).
- commonName
  - Type: string
  - Description: Common name (e.g. 'Water').
- SELFIE
  - Type: string
  - Description: SELFIES representation of the molecular structure.
- name_IUPAC
  - Type: string
  - Description: Full IUPAC name.
- standard_InChI
  - Type: string
  - Description: Standard InChI string.
- standard_InChI_key
  - Type: string
  - Description: Hashed InChIKey for indexing.
- molar_weigth
  - Type: float
  - Description: Molar weight in g/mol.
- smiles_code
  - Type: string
  - Description: SMILES structural notation.
- sigma_profile
  - Type: integer
  - Description: Sigma profile descriptor.


### Fluid

Ein Fluid-Dataset mit explizitem Zustandsraum (`manifold`), einer Liste von konkreten Zustandspunkten (`state_point`) und Messungen, die an diesen Punkten aufgenommen wurden. Die fruehere flache `parameter[]`-Liste ist durch den Manifold ersetzt: Parameter werden dort als Achsen deklariert, ihre Werte als Koordinaten eines StatePoints.

- fluidID
  - Type: Identifier
  - Description: Unique identifier for this fluid dataset.
- compounds
  - Type: Identifier[]
  - Description: References to compounds present in the fluid (pure or mixture).
- manifold
  - Type: Manifold
  - Description: Declaration of the physically valid state space in which all StatePoints of this fluid live. Contains axes, simplex constraints, bounds, and optional phase rule annotation.
- state_point
  - Type: StatePoint[]
  - Description: Concrete points on the manifold at which measurements were taken. Each StatePoint carries coordinates for every axis of the manifold and is referenced by one or more Measurements.
- property
  - Type: Property[]
  - Description: Physical or thermodynamic properties measured or calculated for this fluid. Properties are dependent variables observed at StatePoints.
- sample
  - Type: Sample
  - Description: Sample information (storage, preparation, vendor).

### Constraint

Generische, benutzerdefinierte Nebenbedingung als freier Ausdruck. Uebersetzbar zu SHACL sh:SPARQLConstraint.

- constraint_id
  - Type: Identifier
  - Description: Unique identifier for this constraint.
- constraint_type
  - Type: ConstraintType
  - Description: Category of the constraint (equality, inequality, relational, custom).
- expression
  - Type: string
  - Description: Human- and machine-readable expression using axis_ids as variables (e.g. 'T_upper > T_lower', 'x1 + 2*x2 <= 0.5').
- description
  - Type: string
  - Description: Free-text explanation of the physical meaning of the constraint.

### Ssample

- sample_id
  - Type: Identifier
  - Description: Unique identifier for this sample.
- associated_compounds
  - Type: string[]
  - Description: Compounds contained in the sample.
- measurement
  - Type: Measurement[]
  - Description: Measurements performed on this sample.
- storage
  - Type: Storage
  - Description: Storage conditions of the sample.
- preparation
  - Type: Preparation
  - Description: Preparation procedure.
- vendor_chemical
  - Type: Vendor_Chemical
  - Description: Vendor and purity information.

### Manifold

Deklaration des physikalisch gueltigen Zustandsraums fuer ein Fluid. Der Manifold beschreibt welche Dimensionen existieren und welche Constraints ihn einschraenken, enthaelt aber selbst keine Messwerte - er ist die leere Buehne, auf der StatePoints liegen.

- manifold_id
  - Type: Identifier
  - Description: Unique identifier for this manifold. Enables reuse and cross-dataset referencing.
- axes
  - Type: Axis[]
  - Description: The dimensions that span the state space (e.g. Temperature, Pressure, and one mole-fraction axis per compound in a mixture).
- simplex
  - Type: CompositionSimplex[]
  - Description: Zero or more simplex constraints over subsets of the axes. A simplex enforces Sumxi = sum_value on the referenced axes (typically Sumxi = 1 for mole/mass/volume fractions). Multiple simplexes may coexist (e.g. one for mole fractions and one for a solvent sub-composition).
- bounds
  - Type: Bound[]
  - Description: Interval constraints per axis (e.g. T >= 0 K, x in 0,1). Applied independently to individual axes.
- phase_rule
  - Type: PhaseRuleAnnotation
  - Description: Optional Gibbs phase-rule annotation (F = C - P + 2). Informational only - not hard-enforced, since non-equilibrium data legitimately violates it.
- custom_constraints
  - Type: Constraint[]
  - Description: User-defined constraints as free expressions (e.g. 'T_upper > T_lower'). Translatable to SHACL SPARQLConstraints.

### Axis

Eine Dimension des Manifolds. Axis deklariert was fuer eine Groesse existiert (Temperatur, Druck, Mole-Fraction von Compound X), ohne einen konkreten Wert zu tragen. Werte leben als Coordinate in StatePoint.

- axis_id
  - Type: Identifier
  - Description: Unique identifier for this axis within the manifold.
- quantity
  - Type: Parameters
  - Description: Type of quantity represented by this axis (Temperature, Pressure, MoleFraction, ...). Uses the Parameters enumeration.
- unit
  - Type: UnitDefinition
  - Description: Unit of measurement for values along this axis.
- associated_compound
  - Type: Identifier
  - Description: Reference to a specific compound, if the axis is compound-specific (e.g. mole fraction of ethanol). Empty for system-wide axes like Temperature or Pressure.
- role
  - Type: AxisRole
  - Description: Role of this axis in the dataset - FREE (varies independently), CONSTRAINED (bound by a simplex or other relation), or FIXED (held constant across all measurements in this dataset).

### StatePoint

Ein konkreter Punkt im Manifold-Raum. Ein StatePoint traegt Koordinaten fuer jede Achse des Manifolds und kann von mehreren Measurements geteilt werden, wenn an demselben physikalischen Zustand mehrere Properties gemessen wurden.

- state_point_id
  - Type: Identifier
  - Description: Unique identifier for this state point.
- manifold_id
  - Type: Identifier
  - Description: Reference to the manifold on which this point lies.
- coordinates
  - Type: Coordinate[]
  - Description: One coordinate per axis of the referenced manifold. Each coordinate carries a value and its uncertainty.

### Coordinate

Der Wert eines StatePoints entlang einer einzelnen Achse.

- axis_id
  - Type: Identifier
  - Description: Reference to the axis this coordinate belongs to.
- value
  - Type: float
  - Description: Numerical value along the referenced axis, in the unit declared by that axis.
- uncertainty
  - Type: float
  - Description: Estimated uncertainty (standard deviation or confidence interval) of the coordinate value.


### CompositionSimplex

Strukturelle Erzwingung eines Simplex-Constraints Sumxi = sum_value ueber eine Teilmenge der Manifold-Achsen. Bildet physikalische Normierungen wie Sum(Mole-Fractions) = 1 explizit ab, sodass sie in SHACL/OWL direkt als `sh:SPARQLConstraint` mit `sh:sum` abgebildet werden koennen.

- simplex_id
  - Type: Identifier
  - Description: Unique identifier for this simplex constraint.
- composition_type
  - Type: CompositionType
  - Description: Type of composition the simplex sums (mole, mass, or volume fraction).
- axis_ids
  - Type: Identifier[]
  - Description: Identifiers of the axes that together form the simplex. Typically the set of mole-fraction axes of all compounds in a mixture.
- sum_value
  - Type: float
  - Description: Target sum of the referenced axis values. Default 1.0. Explicit to allow sub-simplexes (e.g. Sum = 0.3 for a fixed solvent cut).
  - Default: 1.0
- tolerance
  - Type: float
  - Description: Numerical tolerance for equality check (|Sumxi - sum_value| <= tolerance). Default 1e-6.
  - Default: 0.000001

### Bound

Interval-Constraint auf eine einzelne Achse. Maps 1:1 auf OWL xsd:minInclusive` / `xsd:maxInclusive.

- bound_id
  - Type: Identifier
  - Description: Unique identifier for this bound.
- axis_id
  - Type: Identifier
  - Description: Axis to which the bound applies.
- lower
  - Type: float
  - Description: Lower bound (inclusive). Omit or use -inf for unbounded below.
- upper
  - Type: float
  - Description: Upper bound (inclusive). Omit or use +inf for unbounded above.
- lower_inclusive
  - Type: boolean
  - Description: Whether the lower bound is inclusive (>=) or strict (>).
  - Default: true
- upper_inclusive
  - Type: boolean
  - Description: Whether the upper bound is inclusive (<=) or strict (<).
  - Default: true

### PhaseRuleAnnotation

Optionale Annotation der Gibbs'schen Phasenregel (F = C - P + 2). Nicht hart erzwungen - dient als Konsistenz-Hinweis fuer Gleichgewichtsdaten. In SHACL als sh:severity sh:Warning abbildbar.

- n_components
  - Type: integer
  - Description: Number of chemical components (C).
- n_phases
  - Type: integer
  - Description: Number of coexisting phases (P).
- degrees_of_freedom
  - Type: integer
  - Description: Expected degrees of freedom (F = C - P + 2). Should match the number of FREE axes in the manifold for equilibrium datasets.
- applies_at_equilibrium
  - Type: boolean
  - Description: Whether this dataset represents equilibrium states. If false, the phase rule is not expected to hold.
  - Default: true




### Property
Eine abhaengige Variable, die am Fluid gemessen oder berechnet wird. Properties leben *nicht* auf dem Manifold - sie werden *an* StatePoints beobachtet.

- propertyID
  - Type: Identifier
  - Description: Unique identifier for this property.
- properties
  - Type: Properties
  - Description: Category of the property (density, viscosity, ...).
- unit
  - Type: UnitDefinition
  - Description: Unit of the property value.

### Measurement

Eine Messung oder Berechnung einer oder mehrerer Properties an einem konkreten Zustandspunkt. Ersetzt das alte Schema, bei dem `parameterValue[]` inline pro Measurement lag - jetzt wird der Zustand ueber `state_point_id` referenziert, was Wiederverwendung ermoeglicht.

- measurement_id
  - Type: Identifier
  - Description: Unique identifier for this measurement.
- state_point_id
  - Type: Identifier
  - Description: Reference to the StatePoint at which this measurement was taken. Multiple measurements may share the same StatePoint.
- source_doi
  - Type: string
  - Description: DOI of the source publication or dataset.
- propertyValue
  - Type: PropertyValue[]
  - Description: Numerical values of the properties measured at the referenced StatePoint.
- method
  - Type: Method
  - Description: How the value was obtained (measured, calculated, simulated, literature).
- method_description
  - Type: string
  - Description: Free-text detail on the experimental setup, computational model, or literature source.

### PropertyValue

Ein Wert einer Property inklusive Unsicherheit.

- properties
  - Type: Properties
  - Description: Category of the property.
- propertyID
  - Type: Identifier
  - Description: Identifier of the referenced property.
- propValue
  - Type: float
  - Description: Measured or calculated numerical value.
- uncertainty
  - Type: float
  - Description: Estimated uncertainty of the property value.


### Preparation

- prepMethod
  - Type: string
  - Description: Description of how the sample was prepared.

### Storage

- storage_type
  - Type: StorageType
  - Description: One of: Fresh, Fridge, Open, Closed, Dessicator.
- storage_conditions
  - Type: StorageConditions
  - Description: Environmental conditions under which the sample is stored.
- vessel
  - Type: Vessel
  - Description: Storage vessel.
- time_prepared
  - Type: string
  - Description: Date of sample preparation.
- time_used
  - Type: string
  - Description: Time when the sample was used.

### StorageConditions

- Temperature
  - Type: float
  - Description: Storage temperature.
- Pressure
  - Type: float
  - Description: Storage pressure.
- gassed
  - Type: boolean
  - Description: Whether the sample was degassed.
- inert
  - Type: boolean
  - Description: Whether the sample was kept under inert atmosphere.
- light
  - Type: boolean
  - Description: Whether the sample was exposed to light.

### Vessel

- id
  - Type: string
  - Description: Unique identifier of the vessel.
- name
  - Type: string
  - Description: Name of the used vessel.
- volume
  - Type: float
  - Description: Volumetric value of the vessel.
- unit
  - Type: UnitDefinition
  - Description: Unit of the volume.
- constant
  - Type: boolean
  - Description: Whether the volume of the vessel is constant.
  - Default: true

### Vendor_Chemical

- associated_compound
  - Type: Identifier
  - Description: Compound this vendor entry refers to.
- CAS
  - Type: string
  - Description: CAS registry number.
- purity
  - Type: string
  - Description: Purity specification.
- Vendor
  - Type: string
  - Description: Vendor name.
- LOT
  - Type: string
  - Description: Lot/batch number.

## Units

### UnitDefinition

- unitID
  - Type: string
  - Description: Unique identifier for the unit definition.
- name
  - Type: string
  - Description: Human-readable name of the unit.
- base_units
  - Type: BaseUnit[]
  - Description: Base unit components with exponents, scale, and multipliers.

### BaseUnit

- kind
  - Type: string
  - Description: Physical quantity (mass, length, time, temperature, ...).
- exponent
  - Type: integer
  - Description: Exponent applied to the base unit.
- multiplier
  - Type: float
  - Description: Numerical multiplier (e.g. 1000 for gram->kilogram).
- scale
  - Type: float
  - Description: Power-of-ten scale factor (applied as 10^scale).



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
MEASURED = measured
CALCULATED = calculated
SIMULATED = simulated
LITERATURE = literature
```

### AxisRole

```python
FREE = free
CONSTRAINED = constrained
FIXED = fixed
```

### CompositionType

```python
MOLE_FRACTION = moleFraction
MASS_FRACTION = massFraction
VOLUME_FRACTION = volumeFraction
```

### ConstraintType

```python
EQUALITY = equality
INEQUALITY = inequality
RELATIONAL = relational
CUSTOM = custom
```

### StorageType

```python
FRESH = Fresh
FRIDGE = Fridge
OPEN = Open
CLOSED = Closed
DESSICATOR = Dessicator
```

### Properties

```python
DENSITY = density
SPECIFIC_HEAT_CAPACITY = specificHeatCapacity
MOLAR_HEAT_CAPACITY = molarHeatCapacity
ELECTRICAL_CONDUCTIVITY = electricalConductivity
THERMAL_CONDUCTIVITY = thermalConductivity
MELTING_POINT = meltingPoint
BOILING_POINT = boilingPoint
VAPOR_PRESSURE = vaporPressure
COMPRESSIBILITY = compressibility
VISCOSITY = viscosity
KINEMATIC_VISCOSITY = kinematicViscosity
PH = pH
POLARITY = polarity
SURFACE_TENSION = surfaceTension
SPEED_OF_SOUND = speedOfSound
REFRACTIVE_INDEX = refractiveIndex
DIFFUSION_COEFFICIENT = diffusionCoefficient
MOLAR_VOLUME = molarVolume
SPECIFIC_VOLUME = specificVolume
EXCESS_MOLAR_VOLUME = excessMolarVolume
ISOBARIC_EXPANSION_COEFFICIENT = isobaricExpansionCoefficient
ISOTHERMAL_COMPRESSIBILITY = isothermalCompressibility
MOLAR_ENTHALPY = molarEnthalpy
MOLAR_ENTROPY = molarEntropy
GIBBS_FREE_ENERGY = gibbsFreeEnergy
HELMHOLTZ_FREE_ENERGY = helmholtzFreeEnergy
EXCESS_MOLAR_ENTHALPY = excessMolarEnthalpy
EXCESS_MOLAR_ENTROPY = excessMolarEntropy
EXCESS_MOLAR_GIBBS_FREE_ENERGY = excessMolarGibbsFreeEnergy
ACTIVATION_ENERGY = activationEnergy
HENRYS_LAW_CONSTANT = henrysLawConstant
ACTIVITY_COEFFICIENT = activityCoefficient
FUGACITY_COEFFICIENT = fugacityCoefficient
OSMOTIC_COEFFICIENT = osmoticCoefficient
ACTIVITY = activity
CRITICAL_TEMPERATURE = criticalTemperature
CRITICAL_PRESSURE = criticalPressure
CRITICAL_DENSITY = criticalDensity
CRITICAL_VOLUME = criticalVolume
TRIPLE_POINT_TEMPERATURE = triplePointTemperature
TRIPLE_POINT_PRESSURE = triplePointPressure
CRITICAL_POINT_TEMPERATURE = criticalPointTemperature
CRITICAL_POINT_PRESSURE = criticalPointPressure
IONIC_STRENGTH = ionicStrength
```

### Parameters

```python
TIME = Time
TEMPERATURE = Temperature
UPPER_TEMPERATURE = Upper temperature
LOWER_TEMPERATURE = Lower temperature
PRESSURE = Pressure
PARTIAL_PRESSURE = Partial pressure
UPPER_PRESSURE = Upper pressure
LOWER_PRESSURE = Lower pressure
MOLE_FRACTION = Mole fraction
MASS_FRACTION = Mass fraction
MOLALITY = Molality
AMOUNT_CONCENTRATION_MOLARITY = Amount concentration (molarity)
VOLUME_FRACTION = Volume fraction
RATIO_OF_AMOUNT_OF_SOLUTE_TO_MASS_OF_SOLUTION = Ratio of amount of solute to mass of solution
RATIO_OF_MASS_OF_SOLUTE_TO_VOLUME_OF_SOLUTION = Ratio of mass of solute to volume of solution
AMOUNT_RATIO_OF_SOLUTE_TO_SOLVENT = Amount ratio of solute to solvent
MASS_RATIO_OF_SOLUTE_TO_SOLVENT = Mass ratio of solute to solvent
VOLUME_RATIO_OF_SOLUTE_TO_SOLVENT = Volume ratio of solute to solvent
INITIAL_MOLE_FRACTION_OF_SOLUTE = Initial mole fraction of solute
FINAL_MOLE_FRACTION_OF_SOLUTE = Final mole fraction of solute
INITIAL_MASS_FRACTION_OF_SOLUTE = Initial mass fraction of solute
FINAL_MASS_FRACTION_OF_SOLUTE = Final mass fraction of solute
INITIAL_MOLALITY_OF_SOLUTE = Initial molality of solute
FINAL_MOLALITY_OF_SOLUTE = Final molality of solute
SOLVENT_MOLE_FRACTION = Solvent: Mole fraction
SOLVENT_MASS_FRACTION = Solvent: Mass fraction
SOLVENT_VOLUME_FRACTION = Solvent: Volume fraction
SOLVENT_MOLALITY = Solvent: Molality
SOLVENT_AMOUNT_CONCENTRATION_MOLARITY = Solvent: Amount concentration (molarity)
SOLVENT_AMOUNT_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT = Solvent: Amount ratio of component to other component of binary solvent
SOLVENT_MASS_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT = Solvent: Mass ratio of component to other component of binary solvent
SOLVENT_VOLUME_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT = Solvent: Volume ratio of component to other component of binary solvent
SOLVENT_RATIO_OF_AMOUNT_OF_COMPONENT_TO_MASS_OF_SOLVENT = Solvent: Ratio of amount of component to mass of solvent
SOLVENT_RATIO_OF_COMPONENT_MASS_TO_VOLUME_OF_SOLVENT = Solvent: Ratio of component mass to volume of solvent
WAVELENGTH = Wavelength
FREQUENCY = Frequency
MOLAR_VOLUME = Molar volume
SPECIFIC_VOLUME = Specific volume
MASS_DENSITY = Mass density
AMOUNT_DENSITY = Amount density
MOLAR_ENTROPY = Molar entropy
RELATIVE_ACTIVITY = Relative activity
ACTIVITY_COEFFICIENT = Activity coefficient
AMOUNT_MOL = Amount
MASS = Mass
```
