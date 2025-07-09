// Auto-generated BAML definitions

class FAIRFluidsDocument {
  version Version @description("Version of the FAIRFluidsDocument")
  citation Citation @description("Add information about the datareport")
  compound Compound[] @description("What Compounds are in the fluid")
  fluid Fluid[] @description("Specifcations of the Fluid")
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
  c_id string @description("Unique id of the compound")
}
class Fluid {
  components string[] @description("Add the ID of the compund into the fluid")
  source_doi string @description("The source where the data come form")
  property Property @description("Property [complex] (Fig. 8) is characterized by Property-MethodID [complex], which identifies the property and experimental method used;")
  parameter Parameter[] @description("A variable refers to an independent experimental parameter that varies across data points within a data set. Examples include temperature, pressure, composition, and other input conditions under which thermodynamic properties are measured. A constraint refers to a condition or a fixed parameter that applies to an entire data set, rather than to each individual data point. Constraints are used to define experimental or calculated conditions that remain constant across all the measurements in a data set. Examples might include fixed composition, pressure, or volume during an experiment.")
  num_value NumValue @description("Actual meassurement data")
}
class Property {
  propertyID string @description("Unique ID of the fluid property")
  property_information Property_Information @description("An identfication to which group the porperty belongs to")
}
class Property_Information {
  group string @description("To which group does the property belong: volumetricProp_, TransportProp, HeatCapacityAndDerivedProp, ExcessPartialApparentEnergyProp, CompositionAtPhaseEquilibrium")
  method string @description("How was the property obtained. (Maybe add prediction field)")
  property_name string @description("What is the name of the property, eg. Mass Density, (and Units?)")
}
class Parameter {
  parameterID string 
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
  propNumber string 
  propValue float @description("Actual value of the property")
  uncertainty float 
}
class ParameterValue {
  varDigits int 
  varNumber string 
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


// Create a function to extract the resume from a string.
function ExtractResume(resume: string) -> FAIRFluidsDocument {
  // Specify a client as provider/model-name
  // you can use custom LLM params with a custom client name from clients.baml like "client CustomHaiku"
  client "MyClient" // Set OPENAI_API_KEY to use this client.
  prompt #"
    Extract from this content:
    {{ resume }}

    {{ ctx.output_format }}
  "#
}



// Test the function with a sample resume. Open the VSCode playground to run this.
test vaibhav_resume {
  functions [ExtractResume]
  args {
    resume #"
      <?xml version='1.0' encoding='UTF-8'?>
<!-- Generated by the ITT, Institute of Thermodynamics and Thermal Process Engineering, University of Stuttgart, Germany (http://www.itt.uni-stuttgart.de) -->
<DataReport xmlns="http://www.iupac.org/namespaces/ThermoML" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.iupac.org/namespaces/ThermoML http://trc.nist.gov/ThermoML.xsd">
  <Version>
    <nVersionMajor>2</nVersionMajor>
    <nVersionMinor>0</nVersionMinor>
  </Version>
  <Citation>
    <eType>journal</eType>
    <eSourceType>Original</eSourceType>
    <sAuthor>Spera, Marcelle B. M.</sAuthor>
    <sAuthor>Darouich, Samir</sAuthor>
    <sAuthor>Pleiss, Jurgen</sAuthor>
    <sAuthor>Hansen, Niels</sAuthor>
    <sPubName>Fluid Phase Equilib.</sPubName>
    <yrPubYr>2025</yrPubYr>
    <dateCit>2025-01-02</dateCit>  
    <sTitle>Influence of water content on thermophysical properties of aqueous glyceline solutions predicted by molecular dynamics simulations</sTitle>
    <sAbstract>Molecular simulations allow the prediction of a large variety of thermophysical properties for complex mixtures based on one underlying model, i.e. the force field. In the present work static and dynamic properties of aqueous 1:2 choline chloride:glycerol mixtures are computed by molecular dynamics simulations with the aim to report robust simulation protocols that allow for a thorough evaluation of the molecular model with regard to experimental data. In particular for the shear viscosity a rather strong dependence of the results on the simulation method can be found. The simulations do not only provide quantitative data but also insight into the effect of water on the microscopic structure of the fluid. The isobaric thermal expansivity shows a transition from DES-like to water-like behavior beyond a water mole fraction of 0.75. Moreover, inconsistencies in experimental datasets are identified. Molecular dynamics simulations serve as a powerful tool to support the decision for one or the other data set in case of contradictory experimental data.</sAbstract>
    <sKeyword>Molecular simulation</sKeyword>    
    <sKeyword>Eutectic solvents</sKeyword>        
    <sKeyword>Water content</sKeyword>    
    <sKeyword>Density</sKeyword>        
    <sKeyword>Viscosity</sKeyword>    
    <sDOI>10.1016/j.fluid.2024.114324</sDOI>
    <sVol>592</sVol>
    <sPage>114324</sPage>
  </Citation>
  <Compound>
    <nPubChemID>305</nPubChemID>
    <RegNum>
      <nOrgNum>1</nOrgNum>
    </RegNum>
    <sCommonName>choline</sCommonName>
    <sCommonName>Choline ion</sCommonName>
    <sCommonName>Bilineurine</sCommonName>
    <sFormulaMolec>C5H14NO+</sFormulaMolec>
    <sIUPACName>2-hydroxyethyl(trimethyl)azanium</sIUPACName>
    <sStandardInChI>InChI=1S/C5H14NO/c1-6(2,3)4-5-7/h7H,4-5H2,1-3H3/q+1</sStandardInChI>
    <sStandardInChIKey>OEYIOHPDSNJKLS-UHFFFAOYSA-N</sStandardInChIKey>
  </Compound>
  <Compound>
    <nPubChemID>312</nPubChemID>
    <RegNum>
      <nOrgNum>2</nOrgNum>
    </RegNum>
    <sCommonName>16887-00-6</sCommonName>
    <sCommonName>chloride</sCommonName>
    <sCommonName>chloride ion</sCommonName>
    <sFormulaMolec>Cl-</sFormulaMolec>
    <sIUPACName>chloride</sIUPACName>
    <sStandardInChI>InChI=1S/ClH/h1H/p-1</sStandardInChI>
    <sStandardInChIKey>VEXZGXHMUGYJMC-UHFFFAOYSA-M</sStandardInChIKey>
  </Compound>
  <Compound>
    <nPubChemID>753</nPubChemID>
    <RegNum>
      <nOrgNum>3</nOrgNum>
    </RegNum>
    <sCommonName>glycerol</sCommonName>
    <sCommonName>glycerin</sCommonName>
    <sCommonName>56-81-5</sCommonName>
    <sFormulaMolec>C3H8O3</sFormulaMolec>
    <sIUPACName>propane-1,2,3-triol</sIUPACName>
    <sStandardInChI>InChI=1S/C3H8O3/c4-1-3(6)2-5/h3-6H,1-2H2</sStandardInChI>
    <sStandardInChIKey>PEDCQBHIVMGVHV-UHFFFAOYSA-N</sStandardInChIKey>
  </Compound>
  <Compound>
    <nPubChemID>962</nPubChemID>
    <RegNum>
      <nOrgNum>4</nOrgNum>
    </RegNum>
    <sCommonName>water</sCommonName>
    <sCommonName>7732-18-5</sCommonName>
    <sCommonName>Distilled water</sCommonName>
    <sFormulaMolec>H2O</sFormulaMolec>
    <sIUPACName>oxidane</sIUPACName>
    <sStandardInChI>InChI=1S/H2O/h1H2</sStandardInChI>
    <sStandardInChIKey>XLYOFNOQVPJJNP-UHFFFAOYSA-N</sStandardInChIKey>
  </Compound>
  <Compound>
    <nPubChemID>280</nPubChemID>
    <RegNum>
      <nOrgNum>5</nOrgNum>
    </RegNum>
    <sCommonName>carbon dioxide</sCommonName>
    <sCommonName>carbonic anhydride</sCommonName>
    <sCommonName>Dry ice</sCommonName>
    <sFormulaMolec>CO2</sFormulaMolec>
    <sStandardInChI>InChI=1S/CO2/c2-1-3</sStandardInChI>
    <sStandardInChIKey>CURLTUGMZLYLDI-UHFFFAOYSA-N</sStandardInChIKey>
  </Compound>
  <Compound>
    <nPubChemID>977</nPubChemID>
    <RegNum>
      <nOrgNum>6</nOrgNum>
    </RegNum>
    <sCommonName>7782-44-7</sCommonName>
    <sCommonName>O</sCommonName>
    <sCommonName>Oxygen</sCommonName>
    <sCommonName>oxygen</sCommonName>
    <sFormulaMolec>O2</sFormulaMolec>
    <sIUPACName>molecular oxygen</sIUPACName>
    <sStandardInChI>InChI=1S/O2/c1-2</sStandardInChI>
    <sStandardInChIKey>MYMOFIZGZYHOMD-UHFFFAOYSA-N</sStandardInChIKey>
  </Compound>
  <PureOrMixtureData>
    <Component>
      <RegNum>
        <nOrgNum>4</nOrgNum>
      </RegNum>
    </Component>
    <PhaseID>
      <ePhase>Liquid</ePhase>
    </PhaseID>
    <Property>
      <ePresentation>Direct value, X</ePresentation>
      <nPropNumber>1</nPropNumber>
      <Property-MethodID>
        <PropertyGroup>
          <VolumetricProp>
            <eMethodName>N/A</eMethodName>
            <ePropName>Mass density, kg/m3</ePropName>
            <Prediction>
              <ePredictionType>Molecular dynamics</ePredictionType>
              <sPredictionMethodDescription>Simulations in NPT ensemble.</sPredictionMethodDescription>
            </Prediction>
          </VolumetricProp>
        </PropertyGroup>
      </Property-MethodID>
      <CombinedUncertainty>
        <eCombUncertEvalMethod>Standard deviation over 3 copies of the same system with different initial velocities.</eCombUncertEvalMethod>
        <nCombUncertAssessNum>1</nCombUncertAssessNum>
        <nCombUncertLevOfConfid>95.0</nCombUncertLevOfConfid>
        <sCombUncertEvalMethod>Data file compiler</sCombUncertEvalMethod>
      </CombinedUncertainty>
      <PropPhaseID>
        <ePropPhase>Liquid</ePropPhase>
      </PropPhaseID>
    </Property>
    <Constraint>
      <ConstraintID>
        <ConstraintType>
          <eComponentComposition>Mole fraction</eComponentComposition>
        </ConstraintType>
        <RegNum>
          <nOrgNum>4</nOrgNum>
        </RegNum>
      </ConstraintID>
      <nConstrDigits>5</nConstrDigits>
      <nConstraintValue>1.0</nConstraintValue>
      <nConstraintNumber>1</nConstraintNumber>
    </Constraint>
    <Constraint>
      <ConstraintID>
        <ConstraintType>
          <ePressure>Pressure, kPa</ePressure>
        </ConstraintType>
      </ConstraintID>
      <nConstrDigits>3</nConstrDigits>
      <nConstraintValue>100.0</nConstraintValue>
      <nConstraintNumber>2</nConstraintNumber>
    </Constraint>
    <NumValues>
    "#
  }
}
