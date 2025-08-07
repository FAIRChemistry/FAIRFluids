// Auto-generated BAML definitions

class FAIRFluidsDocument {
  version Version @description("Version of the FAIRFluidsDocument")
  citation Citation @description("Add information about the datareport")
  compound Compound[] @description("What Compounds are in the fluid")
  fluid Fluid [] @description("Specifcations of the Fluid. There can be multible Fluids in one document")
}
class Version {
  versionMajor int @description("Add the major version number to your datareport")
  versionMinor int @description("Add the minor version number to your datareport")
}
class Citation {
  litType LitType @description("Specifies the type of literature or source document. Accepted values include: book, journal, report, patent, thesis, conference proceedings, archived document, personal correspondence, published translation, or unspecified.")
  author Author[] @description("A list of authors who contributed to the publication. Each entry should include structured information such as full name and optionally additional metadata like affiliation or identifier.")
  doi string @description("Digital Object Identifier (DOI) for the publication. A unique alphanumeric string used to identify and provide a permanent link to the document online.")
  page string @description("The page range in which the publication appears, typically formatted as a string (e.g., '123–135').")
  pub_name string @description("The name of the publication source, such as the journal title, book title, or conference name.")
  title string @description("The title of the cited work or publication.")
  lit_volume_num string @description("The volume number of the source publication, if applicable (e.g., journal volume).")
  url_citation string @description("A direct URL link to the publication or citation landing page.")
  publication_year string @description("The year in which the publication was officially released or published.")
}
class Author {
  given_name string @description("The given name (first name or personal name) of the author or contributor.")
  family_name string @description("The family name (surname or last name) of the author or contributor.")
  email string @description("The email address of the author, if available. Used for contact or identification purposes.")
  orcid string @description("The ORCID iD of the author, a unique, persistent identifier used to distinguish researchers (e.g., '0000-0002-1825-0097').")
  affiliation string @description("The name of the institution or organization the author is affiliated with at the time of publication.")
}
class Compound {
  pubChemID int @description("The PubChem Compound Identifier (CID), a unique numeric ID assigned by the PubChem database to this compound.")
  compound_identifier int @description("A unique identifier assigned to the compound within the scope of this specific data report or dataset. Used for internal tracking.")
  commonName string @description("The common or generic name of the compound, such as 'Water' for H₂O.")
  SELFIE string @description("The SELFIES (Self-referencing Embedded Strings) representation of the compound’s molecular structure. A robust, machine-readable encoding for molecules.")
  name_IUPAC string @description("The full IUPAC (International Union of Pure and Applied Chemistry) name of the compound, representing its standardized chemical nomenclature.")
  standard_InChI string @description("The Standard International Chemical Identifier (InChI) string that uniquely represents the compound’s molecular structure.")
  standard_InChI_key string @description("The hashed version of the InChI string, known as the InChIKey. It is a fixed-length, easier-to-search identifier for databases and indexing.")
}
class Fluid {
  compounds Identifier[] @description("A list of unique identifiers referencing the compounds present in the fluid system. Multiple identifiers indicate a mixture; single entries indicate a pure substance.v")
  property Property[] @description("A list of physical or thermodynamic properties that were measured or calculated for the fluid. Each property is associated with a method identifier (Property-MethodID) that defines both the property type (e.g., viscosity, thermal conductivity) and the experimental or computational method used.")
  parameter Parameter[] @description("A list of experimental parameters. Parameters may vary across data points (e.g., temperature, pressure, composition) or serve as constraints that remain fixed across the dataset (e.g., constant pressure or fixed mole ratio). These define the input conditions under which properties are observed or measured.")
  measurement Measurement[] @description("A collection of measured or calculated numerical data points associated with the specified properties and experimental parameters.")
}
class Property {
  propertyID int @description("A unique identifier for the specific property being reported (e.g., viscosity, density, heat capacity).")
  properties Properties @description("Indicates the broader category or group to which the property belongs (e.g., thermodynamic, transport, phase behavior). Used to organize related properties.")
  unit UnitDefinition 
}
class Parameter {
  parameterID int @description("A unique identifier for this parameter within the dataset. Used for referencing in conjunction with numerical values.")
  parameter Parameters @description("The type or name of the parameter being varied, such as temperature, pressure, or mole fraction. Indicates what was controlled or changed during the experiment.")
  unit UnitDefinition 
  associated_compound int @description("Identifies the specific compound (by its index or ID) to which this parameter applies. Useful in multicomponent systems where a parameter (e.g., mole fraction) pertains to a specific compound.")
}
class Measurement {
  measurement_id int 
  source_doi string @description("The Digital Object Identifier (DOI) of the source publication or dataset from which the fluid data was obtained.")
  propertyValue PropertyValue[] @description("An array of numerical values corresponding to the measured or calculated properties (e.g., density, viscosity). Each entry should include the value, units, and possibly uncertainty or error margins.")
  parameterValue ParameterValue[] @description("An array of numerical values corresponding to the parameters that were varied or held constant during the experiment (e.g., temperature, pressure). Each entry should specify the value, units, and related parameter identifier.3")
  method Method @description("Describes how the property value was obtained. Accepted values may include: `measured`, `calculated`, `simulated`, `predicted`, or `literature`. This field helps distinguish between experimental and non-experimental data sources.")
  method_description string @description("A free-text description providing additional detail about the method used to generate the data (e.g., specific experimental setup, calculation model, simulation type, or literature source details).")
}
class PropertyValue {
  prop_id int @description("Identifier referencing the property to which this value corresponds.")
  propDigits int @description("The number of significant digits or decimal places reported for the property value, indicating the precision of the measurement.")
  propValue float @description("The actual measured or calculated numerical value of the property.")
  uncertainty float @description("The estimated uncertainty or error margin associated with the property value, typically representing standard deviation or confidence interval.")
}
class ParameterValue {
  param_id int @description("Identifier referencing the specific parameter this value corresponds to.")
  paramDigits int @description("The number of significant digits or decimal places reported for the parameter value, indicating measurement precision.")
  paramValue float @description("The actual measured or set numerical value of the parameter.")
  uncertainty float @description("The estimated uncertainty or error margin associated with the parameter value.")
}
class UnitDefinition {
  id string @description("Unique identifier for the unit definition, used for referencing in data fields.")
  name string @description("Human-readable name of the unit (e.g., 'kilogram per cubic meter').")
  base_units BaseUnit[] @description("A list of base unit components that, together with exponents, scale, and multipliers, define the full derived unit.")
}
class BaseUnit {
  kind UnitType @description("The physical quantity represented by the unit (e.g., mass, length, time, temperature).")
  exponent int @description("Exponent applied to the base unit (e.g., m² has exponent 2 for 'length').")
  multiplier float @description("Numerical multiplier applied to the base unit (e.g., 1000 for gram when converting to kilogram).")
  scale float @description("Power-of-ten scale factor applied to the unit (e.g., 3 for kilo, -6 for micro). Applied as 10^scale.")
}

enum LitType {
  BOOK
  JOURNAL
  REPORT
  PATENT
  THESIS
  CONFERENCEPROCEEDINGS
  ARCHIVEDDOCUMENT
  PERSONALCORRESPONDENCE
  PUBLISHEDTRANSLATION
  UNSPECIFIED
}
enum Method {
  MEASURED
  CALCULATED
  SIMULATED
  LITERATURE
}
enum Properties {
  DENSITY
  SPECIFIC_HEAT_CAPACITY
  THERMAL_CONDUCTIVITY
  MELTING_POINT
  BOILING_POINT
  VAPOR_PRESSURE
  COMPRESSIBILITY
  VISCOSITY
  PH
  POLARITY
}
enum Parameters {
  TEMPERATURE_K
  UPPER_TEMPERATURE_K
  LOWER_TEMPERATURE_K
  PRESSURE_KPA
  PARTIAL_PRESSURE_KPA
  UPPER_PRESSURE_KPA
  LOWER_PRESSURE_KPA
  MOLE_FRACTION
  MASS_FRACTION
  MOLALITY_MOLKG
  AMOUNT_CONCENTRATION_MOLARITY_MOLDM3
  VOLUME_FRACTION
  RATIO_OF_AMOUNT_OF_SOLUTE_TO_MASS_OF_SOLUTION_MOLKG
  RATIO_OF_MASS_OF_SOLUTE_TO_VOLUME_OF_SOLUTION_KGM3
  AMOUNT_RATIO_OF_SOLUTE_TO_SOLVENT
  MASS_RATIO_OF_SOLUTE_TO_SOLVENT
  VOLUME_RATIO_OF_SOLUTE_TO_SOLVENT
  INITIAL_MOLE_FRACTION_OF_SOLUTE
  FINAL_MOLE_FRACTION_OF_SOLUTE
  INITIAL_MASS_FRACTION_OF_SOLUTE
  FINAL_MASS_FRACTION_OF_SOLUTE
  INITIAL_MOLALITY_OF_SOLUTE_MOLKG
  FINAL_MOLALITY_OF_SOLUTE_MOLKG
  SOLVENT_MOLE_FRACTION
  SOLVENT_MASS_FRACTION
  SOLVENT_VOLUME_FRACTION
  SOLVENT_MOLALITY_MOLKG
  SOLVENT_AMOUNT_CONCENTRATION_MOLARITY_MOLDM3
  SOLVENT_AMOUNT_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT
  SOLVENT_MASS_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT
  SOLVENT_VOLUME_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT
  SOLVENT_RATIO_OF_AMOUNT_OF_COMPONENT_TO_MASS_OF_SOLVENT_MOLKG
  SOLVENT_RATIO_OF_COMPONENT_MASS_TO_VOLUME_OF_SOLVENT_KGM3
  WAVELENGTH_NM
  FREQUENCY_MHZ
  MOLAR_VOLUME_M3MOL
  SPECIFIC_VOLUME_M3KG
  MASS_DENSITY_KGM3
  AMOUNT_DENSITY_MOLM3
  MOLAR_ENTROPY_JKMOL
  RELATIVE_ACTIVITY
  ACTIVITY_COEFFICIENT
  AMOUNT_MOL
  MASS_KG
}
enum UnitType {
  MOLE
}
