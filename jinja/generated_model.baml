// Auto-generated BAML definitions

class FAIRFluidsDocument {
  version Version @description("Version of the FAIRFluidsDocument")
  citation Citation @description("Add information about the datareport")
  compound Compound[] @description("What Compounds are in the fluid")
  fluid Fluid [] @description("Specifcations of the Fluid")
}
class Version {
  versionMajor int @description("Add the major version number to your datareport")
  versionMinor int @description("Add the minor version number to your datareport")
}
class Citation {
  litType LitType @description("indicates the type of source document (book, journal, report, patent, thesis, conference proceedings, archived document, personal correspondence, published translation, unspecified).")
  author Author[] @description("X")
}
class Author {
  given_name string @description("Name of the Author")
  family_name string @description("Family name ot the author or contributor")
}
class Compound {
  pubChemID int 
  compound_identifier C_id @description("Unique Id of the compund in this datareport")
  commonName string @description("The generic name of a substance, e.g. H20 - Water")
  SELFIE string @description("SELFIES Representation from the Molecule")
  name_IUPAC string 
  standard_InChI string 
  standard_InChI_key string 
}
class C_id {
  c_id Identifier @description("Unique id of the compound")
}
class Fluid {
  components Identifier[] @description("Add the ID of the compund into the fluid")
  source_doi string @description("The source where the data come form")
  property Property @description("Property [complex] (Fig. 8) is characterized by Property-MethodID [complex], which identifies the property and experimental method used;")
  parameter Parameter[] @description("A variable refers to an independent experimental parameter that varies across data points within a data set. Examples include temperature, pressure, composition, and other input conditions under which thermodynamic properties are measured. A constraint refers to a condition or a fixed parameter that applies to an entire data set, rather than to each individual data point. Constraints are used to define experimental or calculated conditions that remain constant across all the measurements in a data set. Examples might include fixed composition, pressure, or volume during an experiment.")
  num_value NumValue @description("Actual meassurement data")
}
class Property {
  propertyID Identifier @description("Unique ID of the fluid property")
  property_information Property_Information @description("An identfication to which group the porperty belongs to")
}
class Property_Information {
  group string @description("To which group does the property belong: volumetricProp_, TransportProp, HeatCapacityAndDerivedProp, ExcessPartialApparentEnergyProp, CompositionAtPhaseEquilibrium")
  method string @description("How was the property obtained. (Maybe add prediction field)")
  property_name string @description("What is the name of the property, eg. Mass Density, (and Units?)")
}
class Parameter {
  parameterID Identifier 
  parameterType ParameterType @description("Name of the Variable- e.g. Temerpature")
  componentID int @description("Add to Identify to which compound the variable applies to")
}
class ParameterType {
  bio_variables BioVariables 
  component_composition ComponentComposition 
  miscellaneous Miscellaneous 
  participant_amount ParticipantAmount 
  pressure Pressure 
  solvent_composition SolventComposition 
  temperature Temperature 
}
class NumValue {
  propertyValue PropertyValue 
  parameterValue ParameterValue 
}
class PropertyValue {
  propDigits int 
  propNumber Identifier 
  propValue float @description("Actual value of the property")
  uncertainty float 
}
class ParameterValue {
  varDigits int 
  varNumber Identifier 
  varValue float @description("Actual value of the variable")
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
enum Temperature {
  TEMPERATURE_K
  UPPER_TEMPERATURE_K
  LOWER_TEMPERATURE_K
}
enum Pressure {
  PRESSURE_KPA
  PARTIAL_PRESSURE_KPA
  UPPER_PRESSURE_KPA
  LOWER_PRESSURE_KPA
}
enum ComponentComposition {
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
}
enum SolventComposition {
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
}
enum Miscellaneous {
  WAVELENGTH_NM
  FREQUENCY_MHZ
  MOLAR_VOLUME_M3MOL
  SPECIFIC_VOLUME_M3KG
  MASS_DENSITY_KGM3
  AMOUNT_DENSITY_MOLM3
  MOLAR_ENTROPY_JKMOL
  RELATIVE_ACTIVITY
  ACTIVITY_COEFFICIENT
}
enum BioVariables {
  PH
  IONIC_STRENGTH_MOLALITY_BASIS_MOLKG
  IONIC_STRENGTH_AMOUNT_CONCENTRATION_BASIS_MOLDM3
  PC_AMOUNT_CONCENTRATION_BASIS
  SOLVENT_PC_AMOUNT_CONCENTRATION_BASIS
}
enum ParticipantAmount {
  AMOUNT_MOL
  MASS_KG
}
