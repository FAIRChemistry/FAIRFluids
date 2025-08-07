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
  compounds int[] @description("A list of unique identifiers referencing the compounds present in the fluid system. Multiple identifiers indicate a mixture; single entries indicate a pure substance.v")
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



function ExtractResume(resume_text: string) -> FAIRFluidsDocument {
  // see clients.baml
  client CustomGPT4o

  prompt #"
    Parse the following Paper and return a structured representation of the data in the schema below.
Concentrate on the viscosity in the table. Every Data point of viscosity belongs to one Temperature and
pressure. So measurements have the property of viscosity and the parameter of temperature and pressure.
Also take care to extract the compounds from the text.
    Paper:
    ---
    {{ resume_text }}
    ---

    {# special macro to print the output instructions. #}
    {{ ctx.output_format }}

    JSON:
  "#
}

test Test1 {
  functions [ExtractResume]
  args {
    resume_text #"
      # NJC
    "#
  }
}



test Test2 {
  functions [ExtractResume]
  args {
    resume_text #"
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
      <PropertyValue>
        <nPropDigits>5</nPropDigits>
        <nPropNumber>1</nPropNumber>
        <nPropValue>989.26692</nPropValue>
        <CombinedUncertainty>
          <nCombUncertAssessNum>1</nCombUncertAssessNum>
          <nCombExpandUncertValue>0.132553</nCombExpandUncertValue>
        </CombinedUncertainty>
      </PropertyValue>
      <VariableValue>
        <nVarDigits>5</nVarDigits>
        <nVarNumber>1</nVarNumber>
        <nVarValue>313.15</nVarValue>
      </VariableValue>
    </NumValues>
    <NumValues>
      <PropertyValue>
        <nPropDigits>5</nPropDigits>
        <nPropNumber>1</nPropNumber>
        <nPropValue>984.23857</nPropValue>
        <CombinedUncertainty>
          <nCombUncertAssessNum>1</nCombUncertAssessNum>
          <nCombExpandUncertValue>0.029222</nCombExpandUncertValue>
        </CombinedUncertainty>
      </PropertyValue>
      <VariableValue>
        <nVarDigits>5</nVarDigits>
        <nVarNumber>1</nVarNumber>
        <nVarValue>323.15</nVarValue>
      </VariableValue>
    </NumValues>
    <NumValues>
     "#
  }
}


test Test3 {
  functions [ExtractResume]
  args {
    resume_text #"
  2.2. Viscosity
NADES, similarly to DES or IL, is normally high in viscosity. The reported values ranged from 138 mPa s to 720 mPa s (Dai et al., 2013) and were much higher as compared to common organic solvents such as water (1.0016 mPa s), ethanol (1.095 mPa s), methanol (0.5600 mPa s) and acetone (0.316 mPa s). Table 2 shows the viscosity of NADES measured at temperature ranged from 25 °C to 60 °C. The high viscosity of NADES was correlated to the intermolecular forces including hydrogen bonds, electrostatic forces of attraction, and Van der Waals that existed between the starting components (Dai et al., 2015; Liu et al., 2018b; Mišan et al., 2020; Zhao et al., 2015). However, the high viscosity was mainly due to the extensive hydrogen bonds formed between the components. Therefore, the higher the amount of hydroxyl group found in the HBD, the larger the number of hydrogen bonds, the higher the viscosity of the NADES.

Table 2. Viscosity of NADES at different temperatures and molar ratios.

NADES Composition	Molar Ratioa	Temperature (°C)	Viscosity (mPa.s)	References
Sugar-based NADES
Choline chloride	Glucose		1:1	27	9037.10	Hayyan et al. (2013a)
Choline chloride	Glucose		1:4 (50 wt%)	25	8.88	Zain et al. (2021)
Choline chloride	Glucose		2.5:1	27	10910.00	Hayyan et al. (2013b)
Choline chloride	Glucose		5:2 (7.84 wt%)	40	479.62	Dai et al. (2013)
Choline chloride	Glucose	Water	3:2:3	25	3939.40	Gómez et al., 2019a, Gómez et al., 2019b
Citric acid	Glucose	Water	1:1:3	25	159.00	Benvenutti et al. (2020)
Citric acid	Glucose	Water	1:1:2	25	437768.50	Gómez et al., 2019a, Gómez et al., 2019b
Lactic acid	Glucose		5:1 (7.89 wt%)	40	46.24	Dai et al. (2013)
Malic acid	Glucose	Water	1:1:3	25	3735.30	Gómez et al., 2019a, Gómez et al., 2019b
Malic acid	Glucose		1:1 (25 wt%)	NA	81.70	Panić et al. (2019)
Malic acid	Glucose	Glycerol	1:1:1 (25 wt%)	NA	44.70	Panić et al. (2019)
Urea	Glucose	Water	1:1:2	25	2638.10	Gómez et al., 2019a, Gómez et al., 2019b
Fructose	Glucose	Sucrose	1:1:1 (22 wt%)	40	983.30	Dai et al. (2013)
Choline chloride	Fructose		1:1 (30 wt%)	20	28.31	Jurić et al. (2021)
Choline chloride	Fructose		1:2 (30 wt%)	20	72.42	Jurić et al. (2021)
Choline chloride	Fructose		5:2 (7.84 wt%)	40	339.15	Dai et al. (2013)
Choline chloride	Fructose	Water	3:2:3	25	2504.00	Gómez et al., 2019a, Gómez et al., 2019b
Citric acid	Fructose	Water	1:1:2	25	115039.00	Gómez et al., 2019a, Gómez et al., 2019b
Malic acid	Fructose	Water	1:1:3	25	2343.10	Gómez et al., 2019a, Gómez et al., 2019b
Glycerol	Fructose		1:1	25	383.90	Rathnasamy et al. (2019)
Urea	Fructose	Water	1:1:2	25	2048.80	Gómez et al., 2019a, Gómez et al., 2019b
Choline chloride	Maltose		1:2	40	975.50	Chanioti and Tzia (2018)
Choline chloride	Maltose		1:2	60	331.20	Chanioti and Tzia (2018)
Choline chloride	Maltose		1:3 (50 wt%)	25	7.92	Zain et al. (2021)
Choline chloride	Sucrose		4:1 (7.40 wt%)	40	712.83	Dai et al. (2013)
Glycerol	Sucrose		1:1	25	1182.00	Rathnasamy et al. (2019)
Choline chloride	Xylose		2:1 (7.74 wt%)	40	372.89	Dai et al. (2013)
Choline chloride	Trehalose		3:1	20	64510	Xin et al. (2017)
Choline chloride	Trehalose		3:1 (25 wt%)	20	57.27	Xin et al. (2017)
Polyol-based NADES
Choline chloride	Glycerol		1:1 (30 wt%)	20	25.05	Jurić et al. (2021)
Choline chloride	Glycerol		1:1	25	234.00	Shang et al. (2019)
Choline chloride	Glycerol		1:2	25	301.00	Esfahani et al. (2020)
Choline chloride	Glycerol		1:2	40	47.50	Chanioti and Tzia (2018)
Choline chloride	Glycerol		1:2 (5.26 wt%)	40	60.24	Dai et al. (2013a)
Choline chloride	Glycerol		1:2	60	23.40	Chanioti and Tzia (2018)
Choline chloride	Glycerol		1:3 (29 wt%)	25	13.10	Zain et al. (2021)
Betaine	Glycerol		1:2	25	8815.00	Shang et al. (2019)
Proline	Glycerol		2:5	25	2543.00	Shang et al. (2019)
Choline chloride	Ethylene glycol		1:2	25	48.00	Esfahani et al. (2020)
Choline chloride	Ethylene glycol		1:2	25	25.00	Shang et al. (2019)
Choline chloride	Propylene glycol		1:1	25	91.0	Shang et al. (2019)
Choline chloride	Propylene glycol		1:2	25	70.0	Benvenutti et al. (2020)
Citric acid	Propylene glycol		1:2	25	2188.00	Benvenutti et al. (2020)
Choline chloride	Propylene glycol	Urea	1:1:1	25	1393.00	Shang et al. (2019)
Choline chloride	1,2-Propanediol		1:2	25	36.00	Esfahani et al. (2020)
Choline chloride	1,2-Propanediol		1:1 (7.70 wt%)	40	35.75	Dai et al. (2013)
Choline chloride	1,2-Propanediol		1:4 (38 wt%)	25	6.69	Zain et al. (2021)
Choline chloride	1,2-Propanediol		1:4	30	83.00	Meng et al. (2018)
Choline chloride	1,4-Butanediol		1:4 (33 wt%)	25	9.48	Zain et al. (2021)
Choline chloride	1,4-Butanediol		1:5	25	40.00	Shang et al. (2019)
Choline chloride	Sorbitol		1:1 (30 wt%)	20	33.35	Jurić et al. (2021)
Choline chloride	Sorbitol		5:2 (9.23 wt%)	40	164.06	Dai et al. (2013)
Choline chloride	Xylitol		2:1 (11.17 wt%)	40	101.46	Dai et al. (2013)
Choline chloride	Isosorbide		1:2	25	>1000	Pan et al. (2021)
Choline chloride	Isosorbide		1:2 (60 wt%)	25	36.30	Pan et al. (2021)
Betaine	Isosorbide		1:2	25	513.30	Pan et al. (2021)
Betaine	Isosorbide		1:2 (60 wt%)	25	10.30	Pan et al. (2021)
Carnitine	Isosorbide		1:2	25	>1000	Pan et al. (2021)
Carnitine	Isosorbide		1:2 (60 wt%)	25	43.20	Pan et al. (2021)
Organic acid-based NADES
Choline chloride	Citric acid		1:1 (30 wt%)	20	48.99	Jurić et al. (2021a)
Choline chloride	Citric acid		1:1	25	14480.00	Benvenutti et al. (2020)
Choline chloride	Citric acid		1:2	40	448.10	Chanioti and Tzia (2018)
Choline chloride	Citric acid		1:2	60	159.00	Chanioti and Tzia (2018)
Choline chloride	Citric acid		2:1 (25 wt%)	NA	16.90	Panić et al. (2019)
Choline chloride	Citric acid		1:2	25	>1000	Pan et al. (2021)
Choline chloride	Citric acid		1:2(60 wt%)	25	32.00	Pan et al. (2021)
Betaine	Citric acid		1:1	25	6367.00	Shang et al. (2019)
Betaine	Citric acid		1:1 (25 wt%)	NA	55.40	Panić et al. (2019)
Betaine	Citric acid		1:2	25	36922.00	Benvenutti et al. (2020)
Carnitine	Citric acid		3:2	25	896.50	Pan et al. (2021)
Carnitine	Citric acid		3:2 (60 wt%)	25	38.10	Pan et al. (2021)
Choline chloride	Malic acid		1:1	25	11475.00	Shang et al. (2019)
Choline chloride	Malic acid		1:1	25	2082.00	Benvenutti et al. (2020)
Choline chloride	Malic acid		1:1	40	445.90	Dai et al. (2013)
Choline chloride	Malic acid		1:1 (30 wt%)	20	26.57	Jurić et al. (2021)
Choline chloride	Malic acid		1:1 (25 wt%)	NA	17.90	Panić et al. (2019)
Choline chloride	Malic acid		1:2	25	530.20	Pan et al. (2021)
Choline chloride	Malic acid		1:2 (60 wt%)	25	13.40	Pan et al. (2021)
Choline chloride	Malic acid	Water	1:1:2	25	304.30	Gómez et al., 2019a, Gómez et al., 2019b
Choline chloride	Malic acid	Xylitol	1:1:1	25	8123.00	Shang et al. (2019)
Choline chloride	Malic acid	Proline	1:1:1 (25 wt%)	NA	12.1	Panić et al. (2019)
Proline	Malic acid		1:1 (17.8 wt%)	40	330.92	Dai et al. (2013)
Proline	Malic acid		1:1 (25 wt%)	NA	15.00	Panić et al. (2019)
Alanine	Malic acid	Water	1:1:3	25	615.30	Gómez et al., 2019a, Gómez et al., 2019b
B-alanine	Malic acid		1:1 (19.48 wt%)	40	236.06	Dai et al. (2013)
Betaine	Malic acid		1:1 (25 wt%)	NA	46.20	Panić et al. (2019)
Carnitine	Malic acid		1:2	25	>1000	Pan et al. (2021)
Carnitine	Malic acid		1:2 (60 wt%)	25	46.50	Pan et al. (2021)
Choline chloride	Lactic acid		1:1	25	3230.00	Shang et al. (2019)
Choline chloride	Lactic acid		1:2	40	29.50	Chanioti and Tzia (2018)
Choline chloride	Lactic acid		1:2	60	9.60	Chanioti and Tzia (2018)
Choline chloride	Lactic acid		1:3 (17 wt%)	25	12.20	Zain et al. (2021)
Choline chloride	Citric acid	Water	1:1:2	25	4080.00	Gómez et al., 2019a, Gómez et al., 2019b
Alanine	Citric acid	Water	1:1:3	25	7082.00	Gómez et al., 2019a, Gómez et al., 2019b
Choline chloride	Ascorbic acid		3:2	25	>1000	Pan et al. (2021)
Choline chloride	Ascorbic acid		3:2 (60 wt%)	25	45.10	Pan et al. (2021)
Carnitine	Ascorbic acid		1:2	25	423.50	Pan et al. (2021)
Carnitine	Ascorbic acid		1:2 (60 wt%)	25	16.20	Pan et al. (2021)
Betaine	Ascorbic acid		1:1	25	721.20	Pan et al. (2021)
Betaine	Ascorbic acid		1:1 (60 wt%)	25	18.70	Pan et al. (2021)
Choline chloride	Tartaric acid		1:2	25	430.3	Pan et al. (2021)
Choline chloride	Tartaric acid		1:2 (60 wt%)	25	11.30	Pan et al. (2021)
Carnitine	Tartaric acid		1:2	25	>1000	Pan et al. (2021)
Carnitine	Tartaric acid		1:2 (60 wt%)	25	68.30	Pan et al. (2021)
Choline chloride	Malonate		1:1	25	721.0	Shang et al. (2019)
Others
Choline chloride	Urea		1:2	25	750.0	Esfahani et al. (2020)
Choline chloride	Urea		1:2	25	632.0	Shang et al. (2019)
Choline chloride	Urea		1:2	25	99.47	Pan et al. (2021)
Choline chloride	Urea		1:2 (60 wt%)	25	5.20	Pan et al. (2021)
Carnitine	Urea		1:2	25	553.00	Pan et al. (2021)
Carnitine	Urea		1:2 (60 wt%)	25	10.50	Pan et al. (2021)
      # NJC
    "#
  }
}

