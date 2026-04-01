# ThermoML → FAIRFluids Mapping Specification

> **Purpose:** This document defines the transformation layer from the ThermoML data model
> (`DataReport`) to the FAIRFluids data model (`FAIRFluidsDocument`), with a focus on fluid
> properties. It is intended as the authoritative input for code generation. Edit sections
> marked **[ADJUST]** before handing this to the code generator.

---

## Preamble: Known Problems & Recommended Solutions

Before implementing the transformation, be aware of the following structural conflicts. Each
issue is referenced again in the relevant mapping section.

### P1 — Implicit vs. Explicit Units
**Problem:** ThermoML encodes units as part of enumeration string values (e.g.
`'Temperature, K'`, `'Pressure, kPa'`). FAIRFluids uses a structured `UnitDefinition` with
`BaseUnit[]` components (SBML-style decomposition).

**Solution:** Implement a unit-string parser that maps ThermoML unit strings to FAIRFluids
`UnitDefinition` objects. A lookup table is provided in [Section 6](#6-unit-lookup-table).
Unmapped unit strings should raise a `ValueError` with the original string logged for manual
extension of the lookup table. Create a completly seperate file for this logic. I want to make adjustments later on

---

### P2 — Variable vs. Constraint Collapse
**Problem:** ThermoML explicitly distinguishes between `Variable[]` (swept conditions) and
`Constraint[]` (fixed conditions) inside `PureOrMixtureData`. FAIRFluids uses a single
`Parameter[]` list for both.

**Solution:** Map both ThermoML `Variable` and `Constraint` to FAIRFluids `Parameter`.
Optionally encode the distinction in a free-text `description` field or via a boolean flag.

---

### P3 — pH: Property or Parameter?
**Problem:** In ThermoML, `pH` appears as a bio-variable (inside `eBioVariables`), meaning it
can be a controlled *condition* (constraint/variable). In FAIRFluids, `pH` is listed as a
`Properties` enum value — a *measured* quantity.

**Solution:** During transformation, check whether pH appears as a ThermoML Variable/Constraint
(→ map to FAIRFluids `Parameter`) or as a ThermoML Property (→ map to FAIRFluids `Property`).
Always map it to a `Property`.

---

### P4 — Compound Index Linking
**Problem:** ThermoML uses integer `n_comp_index` to link compounds defined in the top-level
`DataReport.compound[]` list to their occurrence in `PureOrMixtureData.component[]`. FAIRFluids
uses typed `Identifier` objects.

**Solution:** During transformation, build a compound lookup dict `{n_comp_index: Identifier}`
and substitute all integer references with the generated `Identifier` objects.

---

### P5 — Uncertainty Model Mismatch
**Problem:** ThermoML has a rich uncertainty model: `PropUncertainty`, `CombinedUncertainty`,
`AsymExpandUncert`, `AsymStdUncert`, coverage factors, confidence levels, etc. FAIRFluids stores
only a single `uncertainty: float`.

**Solution (choose one):**
- **[OPTION A]** Extract `n_std_uncert_value` (standard uncertainty) into FAIRFluids
  `PropertyValue.uncertainty`.
- **[OPTION B]** Extract `n_expand_uncert_value` (expanded uncertainty) into
  `PropertyValue.uncertainty` and log the coverage factor separately.
- **[OPTION C]** Store the full ThermoML uncertainty object as a JSON string in
  `Measurement.method_description`.

**[ADJUST]** Select one option above. Default recommendation: **Option A**.

---

### P6 — Author Names as Flat Strings
**Problem:** ThermoML stores authors as `s_author: string[]` (e.g. `["Smith, J.", "Doe, A."]`).
FAIRFluids expects `Author[]` objects with `given_name` and `family_name` fields.

**Solution:** Apply a name-splitting heuristic: split on `,` or space, treat the first token
as `family_name` and the remainder as `given_name`. ORCID and affiliation will be unavailable
(set to `null`). Flag ambiguous cases for manual review.

---

### P7 — Sample Placement
**Problem:** In ThermoML, `Sample[]` is nested inside `Compound`. In FAIRFluids, `Sample` is
nested inside `Fluid`. This means ThermoML's per-compound sample data must be aggregated or
re-associated at the fluid level.

**Solution:** Create one FAIRFluids `Sample` per `PureOrMixtureData` entry. Merge purity data
from all constituent ThermoML compound samples. If compounds have conflicting sample metadata,
create separate notes in `Preparation.prepMethod`.

---

### P8 — Properties Not Present in FAIRFluids
**Problem:** Several ThermoML property groups have no direct equivalent in the current FAIRFluids
`Properties` enum (e.g. `CompositionAtPhaseEquilibrium`, `ReactionEquilibriumProp`,
`BioProperties`, `ReactionStateChangeProp`).

**Solution:** **[ADJUST]** Either:
- Skip unmapped properties (log a warning).

---

### P9 — Reaction Data Out of Scope
**Problem:** ThermoML `DataReport.reaction_data[]` (type `ReactionData`) has no counterpart in
the FAIRFluids model, which is focused on fluid/phase data.

**Solution:** **[ADJUST]** Ignore `reaction_data` entirely during transformation, but flag a warning, that these parts are  not implemented with prompting future extension of the FAIRFluids model.

---

### P10 — Presentation Mode Lost
**Problem:** ThermoML `Property.e_presentation` encodes how a value is reported
(direct value, difference, ratio to reference state, etc.). FAIRFluids has no equivalent field.

**Solution:** Store `e_presentation` and `n_ref_temp` / `n_ref_pressure` in
`Measurement.method_description` as a JSON snippet, so the information is not silently discarded.

---

## 1. Top-Level Root Mapping

| ThermoML (`DataReport`) | FAIRFluids (`FAIRFluidsDocument`) | Notes |
|---|---|---|
| `citation` | `citation` | See [Section 2](#2-citation-mapping) |
| `version` | `version` | See [Section 3](#3-version-mapping) |
| `compound[]` | `compound[]` | See [Section 4](#4-compound-mapping) |
| `pure_or_mixture_data[]` | `fluid[]` | One `PureOrMixtureData` → one `Fluid`. See [Section 5](#5-fluid--pureormixturedata-mapping) |
| `reaction_data[]` | *(not mapped)* | See **P9** |

---

## 2. Citation Mapping

ThermoML `Citation` uses sub-objects (`Book`, `Journal`, `Thesis`) for publication-type-specific
fields. FAIRFluids `Citation` is a flat object with a `litType` enum.

| ThermoML (`Citation`) | FAIRFluids (`Citation`) | Notes |
|---|---|---|
| `e_type` | `litType` | Enum values are identical (see enum table below) |
| `s_title` | `title` | Direct string copy |
| `s_doi` | `doi` | Direct string copy |
| `s_page` | `page` | Direct string copy |
| `s_pub_name` | `pub_name` | Direct string copy |
| `s_vol` | `lit_volume_num` | Direct string copy |
| `url_cit` | `url_citation` | Direct string copy |
| `yr_pub_yr` | `publication_year` | Direct string copy |
| `s_author[]` | `author[]` | String → Author object split; see **P6** |
| `book.s_publisher` | *(not mapped)* | Could be appended to `pub_name`, Discard |
| `book.s_isbn` | *(not mapped)* | No FAIRFluids field, Discard |
| `journal.s_issn` | *(not mapped)* | No FAIRFluids field, Discard |
| `journal.s_issue` | *(not mapped)* |Discard |
| `thesis.s_deg_inst` | *(not mapped)* | Discard |
| `thesis.s_deg` | *(not mapped)* |Discard |
| `date_cit` | *(not mapped)* | Different from publication year, Discard |
| `e_language` | *(not mapped)* | FAIRFluids has no language field, Discard |
| `e_source_type` | *(not mapped)* | FAIRFluids has no source-type field, Discard |
| `s_abstract` | *(not mapped)* | FAIRFluids has no abstract field |
| `s_keyword[]` | *(not mapped)* | FAIRFluids has no keyword field, Discard |
| `s_document_origin` | *(not mapped)* | Discard |
| `s_cas_cit` | *(not mapped)* | Discard |
| `trc_ref_id` | *(not mapped)* | TRC-internal; not relevant for FAIRFluids, discard|

### LitType Enum Mapping

| ThermoML `eType` | FAIRFluids `LitType` |
|---|---|
| `'book'` | `BOOK` |
| `'journal'` | `JOURNAL` |
| `'report'` | `REPORT` |
| `'patent'` | `PATENT` |
| `'thesis'` | `THESIS` |
| `'conferenceProceedings'` | `CONFERENCEPROCEEDINGS` |
| `'archivedDocument'` | `ARCHIVEDDOCUMENT` |
| `'personalCorrespondence'` | `PERSONALCORRESPONDENCE` |
| `'publishedTranslation'` | `PUBLISHEDTRANSLATION` |
| `'unspecified'` | `UNSPECIFIED` |

---

## 3. Version Mapping

| ThermoML (`Version`) | FAIRFluids (`Version`) | Notes |
|---|---|---|
| `n_version_major` | `versionMajor` | Direct integer copy |
| `n_version_minor` | `versionMinor` | Direct integer copy |

---

## 4. Compound Mapping

ThermoML `Compound` has additional sub-types (`Polymer`, `Ion`, `Biomaterial`,
`MulticomponentSubstance`) that have no direct counterpart in the FAIRFluids flat `Compound`.

| ThermoML (`Compound`) | FAIRFluids (`Compound`) | Notes |
|---|---|---|
| `n_pub_chem_id` | `pubChemID` | Direct integer copy |
| `s_common_name[0]` | `commonName` | Take first common name; **[ADJUST]** strategy for multiple |
| `s_iupac_name` | `name_IUPAC` | Direct string copy |
| `s_standard_in_ch_i` | `standard_InChI` | Direct string copy |
| `s_standard_in_ch_i_key` | `standard_InChI_key` | Direct string copy |
| `s_smiles[0]` | `smiles_code` | Take first SMILES; strategy for multiple in the same field as list |
| `n_comp_index` | `compoundID` (as Identifier) | Generate a unique Identifier from index using a UUID. Map index to UUID; see **P4** |
| `s_cas_name` | *(not mapped)* | CAS name; could be stored in `commonName` if IUPAC name exists |
| `s_formula_molec` | *(not mapped)* | Molecular formula; FAIRFluids has no formula field, Discard |
| `reg_num` | *(not mapped)* | CAS registry number; no direct field in FAIRFluids Compound, Discard |
| `s_org_id[]` | *(not mapped)* | Org-specific identifiers; no equivalent, Discard |
| `sample[]` | → `Fluid.sample` | See **P7** and [Section 5.4](#54-sample-mapping) |
| `polymer` | *(not mapped)* | Polymer-specific fields; see **P8** note for compounds |
| `ion.n_charge` | *(not mapped)* | No charge field in FAIRFluids |
| `biomaterial` | *(not mapped)* | No biomaterial fields in FAIRFluids |
| `multicomponent_substance` | *(not mapped)* | Decompose into individual compounds |
| `e_speciation_state` | *(not mapped)* | No speciation field in FAIRFluids |

> ⚠️ **Inconsistency:** FAIRFluids `Compound` includes `SELFIE`, `molar_weight`, and
> `sigma_profile` fields that do not exist in ThermoML. These must be populated from an external
> source (e.g. PubChem lookup via `pubChemID`), Therefore a fetcher using the Pubchem API is needed. SELFIE and sigma_profiles are implemented later, ignore for now.

---

## 5. Fluid / PureOrMixtureData Mapping

One ThermoML `PureOrMixtureData` maps to one FAIRFluids `Fluid`.

### 5.1 Fluid Identity

| ThermoML (`PureOrMixtureData`) | FAIRFluids (`Fluid`) | Notes |
|---|---|---|
| `n_pure_or_mixture_data_number` | `fluidID` (as Identifier) use UUID| Generate Identifier from integer |
| `component[].n_comp_index` | `compounds[]` (as Identifier[]) | Resolve via compound lookup dict, and use UUID; see **P4** |
| *(derived)* | `property[]` | Built from `property[]` entries; see [Section 5.2](#52-property-mapping) |
| *(derived)* | `parameter[]` | Built from `variable[]` + `constraint[]`; see [Section 5.3](#53-parameter-mapping) |
| *(derived)* | `sample` | Built from compound samples + num_values; see [Section 5.4](#54-sample-mapping) |
| `s_compiler` | *(not mapped)* | DISCARD |
| `s_contributor` | *(not mapped)* | DISCARD |
| `date_date_added` | *(not mapped)* | DISCARD |
| `e_exp_purpose` | *(not mapped)* | DISCARD |
| `phase_id[]` | *(not mapped)* | Phase information not present in FAIRFluids, ONLY MAP those who are "liquid" |
| `auxiliary_substance[]` | *(not mapped)* | No auxiliary substance concept in FAIRFluids, Discard |
| `equation[]` | *(not mapped)* | Correlation equations not in FAIRFluids, Discard |

---

### 5.2 Property Mapping

ThermoML `Property` uses `property_method_id.property_group` with typed sub-objects
(`TransportProp`, `VolumetricProp`, etc.), each carrying `e_prop_name` and `e_method_name`.
FAIRFluids `Property` uses a flat `Properties` enum.

#### 5.2.1 ThermoML PropertyGroup → FAIRFluids Properties Enum

The `e_prop_name` value lives inside one of the `PropertyGroup` sub-objects. The mapper must
first determine *which* sub-object is populated, then read its `e_prop_name`.

> **[ADJUST]** The `e_prop_name` values are free ThermoML strings. The table below is a
> best-effort mapping of the most common values. Extend as needed.

**TransportProp (`transport_prop.e_prop_name`)**

| ThermoML `e_prop_name` (example values) | FAIRFluids `Properties` |
|---|---|
| `'Viscosity, Pa*s'` | `VISCOSITY` |
| `'Kinematic viscosity, m2/s'` | `KINEMATIC_VISCOSITY` |
| `'Thermal conductivity, W/m/K'` | `THERMAL_CONDUCTIVITY` |
| `'Diffusion coefficient, m2/s'` | `DIFFUSION_COEFFICIENT` |
| `'Self-diffusion coefficient, m2/s'` | `DIFFUSION_COEFFICIENT` |
| *(other)* | **[ADJUST]** — Skip for now, but raise a warning |

**VolumetricProp (`volumetric_prop.e_prop_name`)**

| ThermoML `e_prop_name` | FAIRFluids `Properties` |
|---|---|
| `'Mass density, kg/m3'` | `DENSITY` |
| `'Molar volume, m3/mol'` | `MOLAR_VOLUME` |
| `'Specific volume, m3/kg'` | `SPECIFIC_VOLUME` |
| `'Excess molar volume, m3/mol'` | `EXCESS_MOLAR_VOLUME` |
| `'Isobaric coefficient of expansion, 1/K'` | `ISOBARIC_EXPANSION_COEFFICIENT` |
| `'Isothermal compressibility, 1/kPa'` | `ISOTHERMAL_COMPRESSIBILITY` |
| `'Compressibility factor, Z'` | `COMPRESSIBILITY` |
| *(other)* | Skip for now, but raise a warning  |

**HeatCapacityAndDerivedProp (`heat_capacity_and_derived_prop.e_prop_name`)**

| ThermoML `e_prop_name` | FAIRFluids `Properties` |
|---|---|
| `'Molar heat capacity at constant pressure, J/K/mol'` | `SPECIFIC_HEAT_CAPACITY` |
| `'Specific heat capacity at constant pressure, J/K/kg'` | `MOLAR_HEAT_CAPACITY` |
| `'Molar entropy, J/K/mol'` | `MOLAR_ENTROPY` |
| *(other)* | Skip for now, but raise a warning  |

> ⚠️ **Inconsistency:** If found, Raise a warning.

**VaporPBoilingTAzeotropTandP (`vapor_p_boiling_t_azeotrop_t_and_p.e_prop_name`)**

| ThermoML `e_prop_name` | FAIRFluids `Properties` |
|---|---|
| `'Vapor or sublimation pressure, kPa'` | `VAPOR_PRESSURE` |
| `'Boiling temperature, K'` | `BOILING_POINT` |
| *(other, azeotrope)* | **[ADJUST]** —  Skip for now, but raise a warning |

**Criticals (`criticals.e_prop_name`)**

| ThermoML `e_prop_name` | FAIRFluids `Properties` |
|---|---|
| `'Critical temperature, K'` | `CRITICAL_TEMPERATURE` |
| `'Critical pressure, kPa'` | `CRITICAL_PRESSURE` |
| `'Critical density, kg/m3'` | `CRITICAL_DENSITY` |
| `'Critical volume, m3/mol'` | `CRITICAL_VOLUME` |
| `'Critical compressibility factor'` | `COMPRESSIBILITY` |

**PhaseTransition (`phase_transition.e_prop_name`)**

| ThermoML `e_prop_name` | FAIRFluids `Properties` |
|---|---|
| `'Melting temperature, K'` | `MELTING_POINT` |
| `'Triple point temperature, K'` | `TRIPLE_POINT_TEMPERATURE` |
| `'Triple point pressure, kPa'` | `TRIPLE_POINT_PRESSURE` |
| `'Normal melting temperature, K'` | `MELTING_POINT` |
| *(other)* | **[ADJUST]**  Skip for now, but raise a warning |

**ExcessPartialApparentEnergyProp (`excess_partial_apparent_energy_prop.e_prop_name`)**

| ThermoML `e_prop_name` | FAIRFluids `Properties` |
|---|---|
| `'Excess molar enthalpy (molar enthalpy of mixing), J/mol'` | `EXCESS_MOLAR_ENTHALPY` |
| `'Excess molar entropy, J/K/mol'` | `EXCESS_MOLAR_ENTROPY` |
| `'Excess molar Gibbs energy, J/mol'` | `EXCESS_MOLAR_GIBBS_FREE_ENERGY` |
| `'Molar enthalpy, J/mol'` | `MOLAR_ENTHALPY` |
| *(other)* | **[ADJUST]**  Skip for now, but raise a warning|

**ActivityFugacityOsmoticProp (`activity_fugacity_osmotic_prop.e_prop_name`)**

| ThermoML `e_prop_name` | FAIRFluids `Properties` |
|---|---|
| `'Activity coefficient'` | `ACTIVITY_COEFFICIENT` |
| `'Fugacity coefficient of a component'` | `FUGACITY_COEFFICIENT` |
| `'Osmotic coefficient'` | `OSMOTIC_COEFFICIENT` |
| `'Henry\'s law constant, kPa'` | `HENRYS_LAW_CONSTANT` |
| `'(Relative) activity'` | `ACTIVITY` |
| *(other)* | **[ADJUST]**  Skip for now, but raise a warning|

**RefractionSurfaceTensionSoundSpeed (`refraction_surface_tension_sound_speed.e_prop_name`)**

| ThermoML `e_prop_name` | FAIRFluids `Properties` |
|---|---|
| `'Refractive index (sodium D-line)'` | `REFRACTIVE_INDEX` |
| `'Surface tension liquid-gas, N/m'` | `SURFACE_TENSION` |
| `'Speed of sound, m/s'` | `SPEED_OF_SOUND` |
| *(other)* | **[ADJUST]** Skip for now, but raise a warning |

**BioProperties (`bio_properties.e_prop_name`)**

| ThermoML `e_prop_name` | FAIRFluids `Properties` |
|---|---|
| *(all values)* | **[ADJUST]** —  Skip for now, but raise a warning, requires extensio in the future, Tell the user its a BIOPropertiy |

**CompositionAtPhaseEquilibrium, ReactionEquilibriumProp, ReactionStateChangeProp**

> ⚠️ **No mapping available.** These property groups have no equivalent in the current
> FAIRFluids `Properties` enum. **[ADJUST]** Skip but raise a warning.

#### 5.2.2 Property Object Field Mapping

| ThermoML (`Property`) | FAIRFluids (`Property`) | Notes |
|---|---|---|
| `n_prop_number` | `propertyID` (as Identifier) | Use as local UUID within fluid |
| *(property group + e_prop_name)* | `properties` (Properties enum) | See table above |
| *(unit embedded in e_prop_name string)* | `unit` (UnitDefinition) | Parse from name; see **P1** and [Section 6](#6-unit-lookup-table) |
| `e_presentation` | *(not mapped)* | See **P10**; store in `method_description` as text, raise a warning|
| `n_ref_temp` | *(not mapped)* | Reference temperature for difference presentations |
| `n_ref_pressure` | *(not mapped)* | Reference pressure for difference presentations |
| `prop_phase_id[]` | *(not mapped)* | Phase info not in FAIRFluids |
| `prop_device_spec` | *(not mapped)* | Device calibration info; no field in FAIRFluids |
| `combined_uncertainty[]` | *(not mapped)* | Use per-value uncertainty instead; see **P5** |
| `e_method_name` / `s_method_name` | → `Measurement.method_description` | Stored as text in measurement; see [Section 5.4](#54-sample-mapping) |
| `prop_uncertainty[]` | → `PropertyValue.uncertainty` | See **P5** |

---

### 5.3 Parameter Mapping

ThermoML distinguishes `Variable[]` (swept) and `Constraint[]` (fixed). Both map to
FAIRFluids `Parameter[]`. The type information (Variable vs. Constraint) may optionally be
preserved.

#### 5.3.1 VariableType / ConstraintType → FAIRFluids Parameters Enum

Both `VariableType` and `ConstraintType` share the same sub-enums (`eTemperature`, `ePressure`,
`eComponentComposition`, `eSolventComposition`, `eMiscellaneous`, `eBioVariables`,
`eParticipantAmount`).

**eTemperature**

| ThermoML value | FAIRFluids `Parameters` |
|---|---|
| `'Temperature, K'` | `TEMPERATURE` |
| `'Upper temperature, K'` | `UPPER_TEMPERATURE` |
| `'Lower temperature, K'` | `LOWER_TEMPERATURE` |

**ePressure**

| ThermoML value | FAIRFluids `Parameters` |
|---|---|
| `'Pressure, kPa'` | `PRESSURE` |
| `'Partial pressure, kPa'` | `PARTIAL_PRESSURE` |
| `'Upper pressure, kPa'` | `UPPER_PRESSURE` |
| `'Lower pressure, kPa'` | `LOWER_PRESSURE` |

**eComponentComposition**

| ThermoML value | FAIRFluids `Parameters` |
|---|---|
| `'Mole fraction'` | `MOLE_FRACTION` |
| `'Mass fraction'` | `MASS_FRACTION` |
| `'Molality, mol/kg'` | `MOLALITY` |
| `'Amount concentration (molarity), mol/dm3'` | `AMOUNT_CONCENTRATION_MOLARITY` |
| `'Volume fraction'` | `VOLUME_FRACTION` |
| `'Ratio of amount of solute to mass of solution, mol/kg'` | `RATIO_OF_AMOUNT_OF_SOLUTE_TO_MASS_OF_SOLUTION` |
| `'Ratio of mass of solute to volume of solution, kg/m3'` | `RATIO_OF_MASS_OF_SOLUTE_TO_VOLUME_OF_SOLUTION` |
| `'Amount ratio of solute to solvent'` | `AMOUNT_RATIO_OF_SOLUTE_TO_SOLVENT` |
| `'Mass ratio of solute to solvent'` | `MASS_RATIO_OF_SOLUTE_TO_SOLVENT` |
| `'Volume ratio of solute to solvent'` | `VOLUME_RATIO_OF_SOLUTE_TO_SOLVENT` |
| `'Initial mole fraction of solute'` | `INITIAL_MOLE_FRACTION_OF_SOLUTE` |
| `'Final mole fraction of solute'` | `FINAL_MOLE_FRACTION_OF_SOLUTE` |
| `'Initial mass fraction of solute'` | `INITIAL_MASS_FRACTION_OF_SOLUTE` |
| `'Final mass fraction of solute'` | `FINAL_MASS_FRACTION_OF_SOLUTE` |
| `'Initial molality of solute, mol/kg'` | `INITIAL_MOLALITY_OF_SOLUTE` |
| `'Final molality of solute, mol/kg'` | `FINAL_MOLALITY_OF_SOLUTE` |

**eSolventComposition**

| ThermoML value | FAIRFluids `Parameters` |
|---|---|
| `'Solvent: Mole fraction'` | `SOLVENT_MOLE_FRACTION` |
| `'Solvent: Mass fraction'` | `SOLVENT_MASS_FRACTION` |
| `'Solvent: Volume fraction'` | `SOLVENT_VOLUME_FRACTION` |
| `'Solvent: Molality, mol/kg'` | `SOLVENT_MOLALITY` |
| `'Solvent: Amount concentration (molarity), mol/dm3'` | `SOLVENT_AMOUNT_CONCENTRATION_MOLARITY` |
| `'Solvent: Amount ratio of component to other component of binary solvent'` | `SOLVENT_AMOUNT_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT` |
| `'Solvent: Mass ratio of component to other component of binary solvent'` | `SOLVENT_MASS_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT` |
| `'Solvent: Volume ratio of component to other component of binary solvent'` | `SOLVENT_VOLUME_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT` |
| `'Solvent: Ratio of amount of component to mass of solvent, mol/kg'` | `SOLVENT_RATIO_OF_AMOUNT_OF_COMPONENT_TO_MASS_OF_SOLVENT` |
| `'Solvent: Ratio of component mass to volume of solvent, kg/m3'` | `SOLVENT_RATIO_OF_COMPONENT_MASS_TO_VOLUME_OF_SOLVENT` |

**eMiscellaneous**

| ThermoML value | FAIRFluids `Parameters` |
|---|---|
| `'Wavelength, nm'` | `WAVELENGTH` |
| `'Frequency, MHz'` | `FREQUENCY` |
| `'Molar volume, m3/mol'` | `MOLAR_VOLUME` |
| `'Specific volume, m3/kg'` | `SPECIFIC_VOLUME` |
| `'Mass density, kg/m3'` | `MASS_DENSITY` |
| `'Amount density, mol/m3'` | `AMOUNT_DENSITY` |
| `'Molar entropy, J/K/mol'` | `MOLAR_ENTROPY` |
| `'(Relative) activity'` | `RELATIVE_ACTIVITY` |
| `'Activity coefficient'` | `ACTIVITY_COEFFICIENT` |

**eBioVariables**

| ThermoML value | FAIRFluids mapping | Notes |
|---|---|---|
| `'pH'` | `Parameters` (as condition)  | See **P3** |
| `'Ionic strength (molality basis), mol/kg'` | `IONIC_STRENGTH` (Parameters enum) | |

**eParticipantAmount**

| ThermoML value | FAIRFluids `Parameters` |
|---|---|
| `'Amount, mol'` | `AMOUNT_MOL` |
| `'Mass, kg'` | `MASS` |

#### 5.3.2 Parameter Object Field Mapping

| ThermoML (`Variable` or `Constraint`) | FAIRFluids (`Parameter`) | Notes |
|---|---|---|
| `n_var_number` / `n_constraint_number` | `parameterID` (as Identifier) | Use as local UUID |
| *(type from VariableType / ConstraintType)* | `parameter` (Parameters enum) | See table above |
| *(unit embedded in type string)* | `unit` (UnitDefinition) | See **P1** and [Section 6](#6-unit-lookup-table) |
| `variable_id.n_comp_index` / `constraint_id.n_comp_index` | `associated_compounds[]` | Resolve to compound identifier |
| `var_device_spec` / `constr_device_spec` |  Skip for now, but raise a warning | Device info not in FAIRFluids |
| `var_repeatability` / `constr_repeatability` |  Skip for now, but raise a warning | No repeatability field in FAIRFluids |
| `var_uncertainty[]` / `constr_uncertainty[]` | → `ParameterValue.uncertainty` | See **P5** |

---

### 5.4 Sample Mapping

ThermoML stores sample metadata at the compound level; FAIRFluids stores it at the fluid level.
Data rows live in `PureOrMixtureData.num_values[]`.

#### 5.4.1 Sample Object

| ThermoML source | FAIRFluids (`Sample`) | Notes |
|---|---|---|
| *(generated)* | `sample_id` | Generate new Identifier |
| `PureOrMixtureData.component[].n_comp_index` | `associated_compounds[]` | List of compound IDs in this sample |
| `Compound.sample[].e_source` + `e_status` | → `preparation.prepMethod` | Serialize as text; see **P7** |
| `Compound.sample[].purity[]` | → `vendor_chemical.purity` | Merge; prefer `n_purity_mass` as string |
| `num_values[]` | `measurement[]` | One `NumValues` → one `Measurement`; see below |

#### 5.4.2 Measurement Object (from NumValues)

Each `NumValues` entry becomes one FAIRFluids `Measurement`.

| ThermoML (`NumValues`) | FAIRFluids (`Measurement`) | Notes |
|---|---|---|
| *(generated)* | `measurement_id` | Generate new Identifier |
| *(from DataReport.citation.s_doi)* | `source_doi` | Propagated from top-level citation |
| `property_value[]` | `propertyValue[]` | See [Section 5.4.3](#543-propertyvalue-mapping) |
| `variable_value[]` + constraint values | `parameterValue[]` | See [Section 5.4.4](#544-parametervalue-mapping) |
| *(from Property.property_group.e_method_name)* | `method` | Map to `Method` enum; see below |
| *(from Property.property_group.s_method_name)* | `method_description` | Free text; also include `e_presentation` info |

**Method Enum Mapping**

| ThermoML source | FAIRFluids `Method` |
|---|---|
| `e_exp_purpose = 'Principal objective...'` | `MEASURED` |
| `prediction.e_prediction_type` is set | `CALCULATED` or `SIMULATED` |
| `critical_evaluation` is set | `LITERATURE` |
| Default / no info | `MEASURED` |

> **[ADJUST]** The ThermoML method encoding is more granular (e.g. `ePredictionType` has
> `MOLECULAR_DYNAMICS`, `AB_INITIO`, etc.). Consider extending the FAIRFluids `Method` enum
> or storing the detail in `method_description`.

#### 5.4.3 PropertyValue Mapping

| ThermoML (`PropertyValue`) | FAIRFluids (`PropertyValue`) | Notes |
|---|---|---|
| `n_prop_number` | `propertyID` (as Identifier) | Must match `Property.n_prop_number` in same fluid |
| `n_prop_value` | `propValue` | Direct float copy |
| `prop_uncertainty[0].n_std_uncert_value` | `uncertainty` | See **P5**; pick Option A/B/C |
| `combined_uncertainty[0].n_comb_std_uncert_value` | `uncertainty` | Alternative source; see **P5** |
| `n_prop_digits` | *(not mapped)* | Significant digits; FAIRFluids has no field |
| `prop_limit` | *(not mapped)* | Upper/lower property limits; no FAIRFluids field |

#### 5.4.4 ParameterValue Mapping

| ThermoML (`VariableValue`) | FAIRFluids (`ParameterValue`) | Notes |
|---|---|---|
| `n_var_number` | `parameterID` (as Identifier) | Must match `Variable.n_var_number` in same fluid |
| `n_var_value` | `paramValue` | Direct float copy |
| `var_uncertainty[0].n_std_uncert_value` | `uncertainty` | See **P5** |
| `n_var_digits` | *(not mapped)* | |

For constraint values (fixed parameters):

| ThermoML (`Constraint`) | FAIRFluids (`ParameterValue`) | Notes |
|---|---|---|
| `n_constraint_number` | `parameterID` | Must match `Constraint.n_constraint_number` |
| `n_constraint_value` | `paramValue` | Single value replicated across all measurements |
| `constr_uncertainty[0].n_std_uncert_value` | `uncertainty` | |

---

## 6. Unit Lookup Table

Maps ThermoML unit strings (embedded in enumeration values) to FAIRFluids `UnitDefinition`.
The `UnitDefinition` is expressed here as a compact notation; the code generator should
expand these to full `BaseUnit[]` objects.

> **[ADJUST]** Add missing entries as you encounter them in your data.

| ThermoML unit string | FAIRFluids UnitDefinition (compact) | SI representation |
|---|---|---|
| `K` | `name="kelvin"`, base: `(temperature, exp=1)` | K |
| `kPa` | `name="kilopascal"`, base: `(mass,1),(length,-1),(time,-2)`, mult=1000 | kg·m⁻¹·s⁻² ×10³ |
| `Pa` | `name="pascal"`, base: `(mass,1),(length,-1),(time,-2)` | kg·m⁻¹·s⁻² |
| `Pa*s` | `name="pascal second"`, base: `(mass,1),(length,-1),(time,-1)` | kg·m⁻¹·s⁻¹ |
| `m2/s` | `name="square meter per second"`, base: `(length,2),(time,-1)` | m²·s⁻¹ |
| `kg/m3` | `name="kilogram per cubic meter"`, base: `(mass,1),(length,-3)` | kg·m⁻³ |
| `mol/kg` | `name="mole per kilogram"`, base: `(amount,1),(mass,-1)` | mol·kg⁻¹ |
| `mol/dm3` | `name="mole per cubic decimeter"`, base: `(amount,1),(length,-3)`, mult=1000 | mol·m⁻³ ×10³ |
| `m3/mol` | `name="cubic meter per mole"`, base: `(length,3),(amount,-1)` | m³·mol⁻¹ |
| `m3/kg` | `name="cubic meter per kilogram"`, base: `(length,3),(mass,-1)` | m³·kg⁻¹ |
| `J/mol` | `name="joule per mole"`, base: `(mass,1),(length,2),(time,-2),(amount,-1)` | kg·m²·s⁻²·mol⁻¹ |
| `J/K/mol` | `name="joule per kelvin per mole"`, base: `(mass,1),(length,2),(time,-2),(temp,-1),(amount,-1)` | |
| `J/K/kg` | `name="joule per kelvin per kilogram"`, base: `(mass,0),(length,2),(time,-2),(temp,-1)` | |
| `W/m/K` | `name="watt per meter per kelvin"`, base: `(mass,1),(length,1),(time,-3),(temp,-1)` | |
| `N/m` | `name="newton per meter"`, base: `(mass,1),(time,-2)` | kg·s⁻² |
| `m/s` | `name="meter per second"`, base: `(length,1),(time,-1)` | |
| `nm` | `name="nanometer"`, base: `(length,1)`, scale=-9 | |
| `MHz` | `name="megahertz"`, base: `(time,-1)`, mult=1e6 | |
| `dimensionless` | `name="dimensionless"`, base: `[]` | |
| `mol` | `name="mole"`, base: `(amount,1)` | |
| `kg` | `name="kilogram"`, base: `(mass,1)` | |
| `mol/m3` | `name="mole per cubic meter"`, base: `(amount,1),(length,-3)` | |

---

## 7. Compound Purity → Vendor_Chemical Mapping

| ThermoML (`Purity`) | FAIRFluids (`Vendor_Chemical`) | Notes |
|---|---|---|
| *(linked via Compound)* | `assciciated_compound` | Reference to compound Identifier |
| `Compound.reg_num.n_casr_num` | `CAS` | Convert integer to CAS string format `xxxxxxx-xx-x` |
| `n_purity_mass` | `purity` | As percentage string, e.g. `"99.5 mass%"` |
| `e_source = 'Commercial source'` | `Vendor` | Map eSource to vendor string |
| `Compound.sample[].e_status` | *(not mapped)* | No direct equivalent |
| `e_anal_meth[]` | *(not mapped)* | Analytical method; no FAIRFluids field |
| `e_purif_method[]` | → `Preparation.prepMethod` | Serialize as list of method names |
| `n_water_mass_per_cent` | *(not mapped)* | No specific impurity fields in FAIRFluids |
| `n_halide_mass_per_cent` | *(not mapped)* | No specific impurity fields in FAIRFluids |

---

## 8. Summary of Inconsistencies

| # | Inconsistency | Severity | Action Required |
|---|---|---|---|
| I1 | Units implicit in ThermoML string enums vs. explicit SBML-style in FAIRFluids | High | Implement unit parser + lookup table (Section 6) |
| I2 | ThermoML Variable/Constraint duality collapsed into single Parameter | Medium | Document decision; optionally preserve in a flag |
| I3 | pH is a Parameter in ThermoML but a Property in FAIRFluids | Medium | Add conditional logic based on occurrence context |
| I4 | Compound linkage via integer index vs. Identifier objects | High | Build and maintain index→Identifier lookup dict |
| I5 | Rich ThermoML uncertainty → single float in FAIRFluids | High | Choose Option A/B/C in Preamble P5 |
| I6 | Author strings vs. Author objects | Low | Use name-splitting heuristic |
| I7 | ThermoML Sample under Compound vs. FAIRFluids Sample under Fluid | Medium | Aggregate; document merge strategy |
| I8 | FAIRFluids has no phase information field | Medium | Silently discard ThermoML phase data or extend model |
| I9 | ThermoML `ePresentation` (ratio/difference modes) has no FAIRFluids field | Medium | Store in `method_description` |
| I10 | No ReactionData support in FAIRFluids | Low | Skip with warning |
| I11 | Polymer/Ion/Biomaterial compound sub-types not in FAIRFluids | Medium | Discard sub-type data; log warning |
| I12 | FAIRFluids `Compound` fields `SELFIE`, `molar_weight`, `sigma_profile` have no ThermoML source | Medium | Populate from PubChem API or leave empty |
| I13 | Molar vs. specific heat capacity not distinguished in FAIRFluids enum | Low | Map both to `SPECIFIC_HEAT_CAPACITY`; extend enum if needed |
| I14 | ThermoML method is per-PropertyGroup; FAIRFluids method is per-Measurement | Medium | Propagate method from property definition to each measurement |
| I15 | CompositionAtPhaseEquilibrium, BioProperties have no FAIRFluids equivalent | Low | Skip with warning; extend FAIRFluids enum if needed |

---

## 9. Out-of-Scope (Not Mapped)

The following ThermoML structures are explicitly out of scope for the fluid property
transformation layer. They should be either silently skipped or raise a configurable warning.

- `DataReport.reaction_data[]` — all `ReactionData` content (see **P9**)
- `PureOrMixtureData.equation[]` — fitted correlation equations
- `PureOrMixtureData.phase_id[]` — phase identification
- `PureOrMixtureData.auxiliary_substance[]` — buffers, inert substances
- `Compound.biomaterial` — EC numbers, PDB identifiers
- `Compound.polymer` — polymer dispersity, molecular mass distributions
- `Compound.ion.n_charge` — ion charge
- `Citation.trc_ref_id` — TRC-internal reference
- `Property.curve_dev[]` — curve fitting deviations
- `Property.prop_repeatability` / `var_repeatability` / `constr_repeatability` — no field in FAIRFluids
- `Property.prop_device_spec` — device calibration details
- `CriticalEvaluation` (single/multi/EOS) — critical evaluation metadata

---

## 10. Recommended Implementation Order

1. **Unit parser** — implement the lookup table from Section 6 first; all other mappings depend on it.
2. **Compound mapper** — build the `n_comp_index → Identifier` dict; used throughout.
3. **Citation mapper** — straightforward; depends on author name splitter.
4. **Fluid mapper** — maps `PureOrMixtureData` to `Fluid`; iterates over Property and Variable/Constraint lists.
5. **Property mapper** — resolves `PropertyGroup.e_prop_name` to `Properties` enum.
6. **Parameter mapper** — resolves `VariableType`/`ConstraintType` to `Parameters` enum.
7. **Measurement assembler** — joins `NumValues` rows with property and parameter definitions.
8. **Sample assembler** — merges compound-level sample/purity data into `Fluid.sample`.
