```mermaid
classDiagram
    %% Class definitions with attributes
    class DataReport {
        +citation?: Citation
        +version?: Version
        +compound[0..*]: Compound
        +pure_or_mixture_data[0..*]: PureOrMixtureData
        +reaction_data[0..*]: ReactionData
    }

    class Version {
        +n_version_major?: integer
        +n_version_minor?: integer
    }

    class Citation {
        +book?: Book
        +journal?: Journal
        +thesis?: Thesis
        +date_cit?: string
        +e_language?: eLanguage | string
        +e_source_type?: eSourceType | string
        +e_type?: eType | string
        +s_abstract?: string
        +s_author[0..*]: string
        +s_cas_cit?: string
        +s_document_origin?: string
        +s_doi?: string
        +s_id_num?: string
        +s_keyword[0..*]: string
        +s_location?: string
        +s_page?: string
        +s_pub_name?: string
        +s_title?: string
        +s_vol?: string
        +trc_ref_id?: TRCRefID
        +url_cit?: string
        +yr_pub_yr?: string
    }

    class TRCRefID {
        +n_authorn?: integer
        +s_author1?: string
        +s_author2?: string
        +yr_yr_pub?: integer
    }

    class Book {
        +s_chapter?: string
        +s_edition?: string
        +s_editor[0..*]: string
        +s_isbn?: string
        +s_publisher?: string
    }

    class Journal {
        +s_coden?: string
        +s_issn?: string
        +s_issue?: string
    }

    class Thesis {
        +s_deg?: string
        +s_deg_inst?: string
        +s_umi_pub_num?: string
    }

    class Compound {
        +biomaterial?: Biomaterial
        +ion?: Ion
        +multicomponent_substance?: MulticomponentSubstance
        +polymer?: Polymer
        +e_speciation_state?: eSpeciationState | string
        +n_comp_index?: integer
        +n_pub_chem_id?: integer
        +reg_num?: RegNum
        +s_cas_name?: string
        +s_common_name[0..*]: string
        +s_formula_molec?: string
        +s_iupac_name?: string
        +s_org_id[0..*]: SOrgID
        +s_smiles[0..*]: string
        +s_standard_in_ch_i?: string
        +s_standard_in_ch_i_key?: string
        +sample[0..*]: Sample
    }

    class RegNum {
        +n_org_num?: integer
        +n_casr_num?: integer
        +s_organization?: string
    }

    class SOrgID {
        +s_org_identifier?: string
        +s_organization?: string
    }

    class Polymer {
        +n_deg_of_polymerization_dispersity?: float
        +n_mass_avg_mol_mass?: float
        +n_molar_mass_dispersity?: float
        +n_number_avg_mol_mass?: float
        +n_peak_avg_mol_mass?: float
        +n_viscosity_avg_mol_mass?: float
        +n_z_avg_mol_mass?: float
    }

    class Ion {
        +n_charge?: integer
    }

    class Biomaterial {
        +s_ec_number?: string
        +s_pdb_identifier?: string
    }

    class MulticomponentSubstance {
        +component[0..*]: Component
        +composition_basis?: string
        +type?: string
    }

    class Component {
        +n_amount?: float
        +n_comp_index?: integer
        +reg_num?: RegNum
        +n_sample_nm?: integer
    }

    class Sample {
        +n_sample_nm?: integer
        +component_sample[0..*]: ComponentSample
        +e_source?: eSource | string
        +e_status?: eStatus | string
        +purity[0..*]: Purity
    }

    class ComponentSample {
        +n_comp_index?: integer
        +n_sample_nm?: integer
        +reg_num?: RegNum
    }

    class Purity {
        +n_halide_mass_per_cent?: float
        +n_halide_mass_per_cent_digits?: integer
        +n_halide_mol_per_cent?: float
        +n_halide_mol_per_cent_digits?: integer
        +n_purity_mass?: float
        +n_purity_mass_digits?: integer
        +n_purity_mol?: float
        +n_purity_mol_digits?: integer
        +n_purity_vol?: float
        +n_purity_vol_digits?: integer
        +n_step?: integer
        +n_unknown_per_cent?: float
        +n_unknown_per_cent_digits?: integer
        +n_water_mass_per_cent?: float
        +n_water_mass_per_cent_digits?: integer
        +n_water_mol_per_cent?: float
        +n_water_mol_per_cent_digits?: integer
        +e_anal_meth[0..*]: eAnalMeth
        +e_purif_method[0..*]: ePurifMethod
        +s_anal_meth[0..*]: string
        +s_purif_method[0..*]: string
    }

    class PureOrMixtureData {
        +component[0..*]: Component
        +phase_id[0..*]: PhaseID
        +property[0..*]: Property
        +auxiliary_substance[0..*]: AuxiliarySubstance
        +constraint[0..*]: Constraint
        +date_date_added?: string
        +e_exp_purpose?: eExpPurpose | string
        +equation[0..*]: Equation
        +n_pure_or_mixture_data_number?: integer
        +num_values[0..*]: NumValues
        +s_compiler?: string
        +s_contributor?: string
        +variable[0..*]: Variable
    }

    class AuxiliarySubstance {
        +e_function?: eFunction | string
        +n_comp_index?: integer
        +reg_num?: RegNum
        +s_function?: string
        +e_phase?: ePhase | string
        +n_sample_nm?: integer
    }

    class Property {
        +e_presentation?: ePresentation | string
        +n_pressure_digits?: integer
        +n_pressure_pa?: float
        +n_prop_number?: integer
        +n_ref_pressure?: float
        +n_ref_pressure_digits?: integer
        +n_ref_temp?: float
        +n_ref_temp_digits?: integer
        +n_temperature_digits?: integer
        +n_temperature_k?: float
        +property_method_id?: PropertyMethodID
        +catalyst[0..*]: Catalyst
        +combined_uncertainty[0..*]: CombinedUncertainty
        +curve_dev[0..*]: CurveDev
        +e_ref_state_type?: eRefStateType | string
        +e_standard_state?: eStandardState | string
        +prop_device_spec?: PropDeviceSpec
        +prop_phase_id[0..*]: PropPhaseID
        +prop_repeatability?: PropRepeatability
        +prop_uncertainty[0..*]: PropUncertainty
        +ref_phase_id?: RefPhaseID
        +solvent?: Solvent
    }

    class ReactionData {
        +e_reaction_type?: eReactionType | string
        +participant[0..*]: Participant
        +property[0..*]: Property
        +auxiliary_substance[0..*]: AuxiliarySubstance
        +constraint[0..*]: Constraint
        +date_date_added?: string
        +e_exp_purpose?: eExpPurpose | string
        +e_reaction_formalism?: eReactionFormalism | string
        +equation[0..*]: Equation
        +n_electron_number?: integer
        +n_reaction_data_number?: integer
        +num_values[0..*]: NumValues
        +s_compiler?: string
        +s_contributor?: string
        +solvent[0..*]: Solvent
        +variable[0..*]: Variable
    }

    class Participant {
        +e_crystal_lattice_type?: eCrystalLatticeType | string
        +e_phase?: ePhase | string
        +n_comp_index?: integer
        +reg_num?: RegNum
        +s_phase_description?: string
        +e_composition_representation?: eCompositionRepresentation | string
        +e_standard_state?: eStandardState | string
        +n_numerical_composition?: float
        +n_sample_nm?: integer
        +n_stoichiometric_coef?: float
    }

    class Catalyst {
        +n_comp_index?: integer
        +reg_num?: RegNum
        +e_phase?: ePhase | string
    }

    class PhaseID {
        +e_crystal_lattice_type?: eCrystalLatticeType | string
        +e_phase?: ePhase | string
        +n_comp_index?: integer
        +reg_num?: RegNum
        +s_phase_description?: string
    }

    class Constraint {
        +constraint_id?: ConstraintID
        +n_constr_digits?: integer
        +n_constraint_value?: float
        +constr_device_spec?: ConstrDeviceSpec
        +constr_repeatability?: ConstrRepeatability
        +constr_uncertainty[0..*]: ConstrUncertainty
        +constraint_phase_id?: ConstraintPhaseID
        +n_constraint_number?: integer
        +solvent?: Solvent
    }

    class Variable {
        +n_var_number?: integer
        +variable_id?: VariableID
        +solvent?: Solvent
        +var_device_spec?: VarDeviceSpec
        +var_phase_id?: VarPhaseID
        +var_repeatability?: VarRepeatability
        +var_uncertainty[0..*]: VarUncertainty
    }

    class Solvent {
        +e_phase?: ePhase | string
        +n_comp_index?: integer
        +reg_num?: RegNum
    }

    class PropertyMethodID {
        +n_comp_index?: integer
        +property_group?: PropertyGroup
        +reg_num?: RegNum
    }

    class PropertyGroup {
        +activity_fugacity_osmotic_prop?: ActivityFugacityOsmoticProp
        +bio_properties?: BioProperties
        +composition_at_phase_equilibrium?: CompositionAtPhaseEquilibrium
        +criticals?: Criticals
        +excess_partial_apparent_energy_prop?: ExcessPartialApparentEnergyProp
        +heat_capacity_and_derived_prop?: HeatCapacityAndDerivedProp
        +phase_transition?: PhaseTransition
        +reaction_equilibrium_prop?: ReactionEquilibriumProp
        +reaction_state_change_prop?: ReactionStateChangeProp
        +refraction_surface_tension_sound_speed?: RefractionSurfaceTensionSoundSpeed
        +transport_prop?: TransportProp
        +vapor_p_boiling_t_azeotrop_tand_p?: VaporPBoilingTAzeotropTandP
        +volumetric_prop?: VolumetricProp
    }

    class PropPhaseID {
        +e_bio_state?: eBioState | string
        +e_crystal_lattice_type?: eCrystalLatticeType | string
        +e_prop_phase?: ePropPhase | string
        +n_comp_index?: integer
        +reg_num?: RegNum
        +s_bio_state?: string
        +s_phase_description?: string
    }

    class RefPhaseID {
        +e_crystal_lattice_type?: eCrystalLatticeType | string
        +e_ref_phase?: eRefPhase | string
        +n_comp_index?: integer
        +reg_num?: RegNum
        +s_phase_description?: string
    }

    class ConstraintID {
        +constraint_type?: ConstraintType
        +n_comp_index?: integer
        +reg_num?: RegNum
    }

    class ConstraintType {
        +e_bio_variables?: eBioVariables | string
        +e_component_composition?: eComponentComposition | string
        +e_miscellaneous?: eMiscellaneous | string
        +e_participant_amount?: eParticipantAmount | string
        +e_pressure?: ePressure | string
        +e_solvent_composition?: eSolventComposition | string
        +e_temperature?: eTemperature | string
    }

    class ConstraintPhaseID {
        +e_constraint_phase?: eConstraintPhase | string
        +e_crystal_lattice_type?: eCrystalLatticeType | string
        +n_comp_index?: integer
        +reg_num?: RegNum
        +s_phase_description?: string
    }

    class VariableID {
        +n_comp_index?: integer
        +reg_num?: RegNum
        +variable_type?: VariableType
    }

    class VariableType {
        +e_bio_variables?: eBioVariables | string
        +e_component_composition?: eComponentComposition | string
        +e_miscellaneous?: eMiscellaneous | string
        +e_participant_amount?: eParticipantAmount | string
        +e_pressure?: ePressure | string
        +e_solvent_composition?: eSolventComposition | string
        +e_temperature?: eTemperature | string
    }

    class VarPhaseID {
        +e_crystal_lattice_type?: eCrystalLatticeType | string
        +e_var_phase?: eVarPhase | string
        +n_comp_index?: integer
        +reg_num?: RegNum
        +s_phase_description?: string
    }

    class NumValues {
        +property_value[0..*]: PropertyValue
        +variable_value[0..*]: VariableValue
    }

    class PropertyValue {
        +n_prop_digits?: integer
        +n_prop_number?: integer
        +n_prop_value?: float
        +prop_limit?: PropLimit
        +combined_uncertainty[0..*]: CombinedUncertainty
        +curve_dev[0..*]: CurveDev
        +n_prop_device_spec_value?: float
        +prop_repeatability?: PropRepeatability
        +prop_uncertainty[0..*]: PropUncertainty
    }

    class VariableValue {
        +n_var_digits?: integer
        +n_var_number?: integer
        +n_var_value?: float
        +n_var_device_spec_value?: float
        +var_repeatability?: VarRepeatability
        +var_uncertainty[0..*]: VarUncertainty
    }

    class PropLimit {
        +n_prop_limit_digits?: integer
        +n_prop_lower_limit_value?: float
        +n_prop_upper_limit_value?: float
    }

    class CombinedUncertainty {
        +e_comb_uncert_eval_method?: eCombUncertEvalMethod | string
        +n_comb_uncert_assess_num?: integer
        +asym_comb_expand_uncert?: AsymCombExpandUncert
        +asym_comb_std_uncert?: AsymCombStdUncert
        +n_comb_coverage_factor?: float
        +n_comb_expand_uncert_value?: float
        +n_comb_std_uncert_value?: float
        +n_comb_uncert_lev_of_confid?: float
        +s_comb_uncert_eval_method?: string
        +s_comb_uncert_evaluator?: string
    }

    class PropUncertainty {
        +n_uncert_assess_num?: integer
        +asym_expand_uncert?: AsymExpandUncert
        +asym_std_uncert?: AsymStdUncert
        +n_coverage_factor?: float
        +n_expand_uncert_value?: float
        +n_std_uncert_value?: float
        +n_uncert_lev_of_confid?: float
        +s_uncert_eval_method?: string
        +s_uncert_evaluator?: string
    }

    class PropRepeatability {
        +e_repeat_method?: eRepeatMethod | string
        +n_prop_repeat_value?: float
        +n_repetitions?: integer
        +s_repeat_evaluator?: string
        +s_repeat_method?: string
    }

    class PropDeviceSpec {
        +e_device_spec_method?: eDeviceSpecMethod | string
        +n_device_spec_lev_of_confid?: float
        +s_device_spec_evaluator?: string
        +s_device_spec_method?: string
    }

    class CurveDev {
        +n_curve_dev_assess_num?: integer
        +n_curve_dev_value?: float
        +s_curve_spec?: string
        +n_curve_rms_dev_value?: float
        +n_curve_rms_relative_dev_value?: float
        +s_curve_dev_evaluator?: string
    }

    class ConstrUncertainty {
        +n_coverage_factor?: float
        +n_expand_uncert_value?: float
        +n_std_uncert_value?: float
        +n_uncert_lev_of_confid?: float
        +s_uncert_eval_method?: string
        +s_uncert_evaluator?: string
    }

    class ConstrRepeatability {
        +e_repeat_method?: eRepeatMethod | string
        +n_repeat_value?: float
        +n_repetitions?: integer
        +s_repeat_evaluator?: string
        +s_repeat_method?: string
    }

    class ConstrDeviceSpec {
        +e_device_spec_method?: eDeviceSpecMethod | string
        +n_device_spec_lev_of_confid?: float
        +n_device_spec_value?: float
        +s_device_spec_evaluator?: string
        +s_device_spec_method?: string
    }

    class VarUncertainty {
        +n_uncert_assess_num?: integer
        +n_coverage_factor?: float
        +n_expand_uncert_value?: float
        +n_std_uncert_value?: float
        +n_uncert_lev_of_confid?: float
        +s_uncert_eval_method?: string
        +s_uncert_evaluator?: string
    }

    class VarRepeatability {
        +e_repeat_method?: eRepeatMethod | string
        +n_repetitions?: integer
        +n_var_repeat_value?: float
        +s_repeat_evaluator?: string
        +s_repeat_method?: string
    }

    class VarDeviceSpec {
        +e_device_spec_method?: eDeviceSpecMethod | string
        +n_device_spec_lev_of_confid?: float
        +s_device_spec_evaluator?: string
        +s_device_spec_method?: string
    }

    class AsymCombStdUncert {
        +n_negative_value?: float
        +n_positive_value?: float
    }

    class AsymCombExpandUncert {
        +n_negative_value?: float
        +n_positive_value?: float
    }

    class AsymStdUncert {
        +n_negative_value?: float
        +n_positive_value?: float
    }

    class AsymExpandUncert {
        +n_negative_value?: float
        +n_positive_value?: float
    }

    class Equation {
        +e_eq_name?: eEqName | string
        +s_eq_name?: string
        +url_math_source?: string
        +covariance[0..*]: Covariance
        +eq_constant[0..*]: EqConstant
        +eq_constraint[0..*]: EqConstraint
        +eq_parameter[0..*]: EqParameter
        +eq_property[0..*]: EqProperty
        +eq_variable[0..*]: EqVariable
        +n_covariance_lev_of_confid?: float
    }

    class ActivityFugacityOsmoticProp {
        +critical_evaluation?: CriticalEvaluation
        +e_method_name?: eMethodName | string
        +e_prop_name?: ePropName | string
        +prediction?: Prediction
        +s_method_name?: string
    }

    class BioProperties {
        +critical_evaluation?: CriticalEvaluation
        +e_method_name?: eMethodName | string
        +e_prop_name?: ePropName | string
        +prediction?: Prediction
        +s_method_name?: string
    }

    class CompositionAtPhaseEquilibrium {
        +critical_evaluation?: CriticalEvaluation
        +e_method_name?: eMethodName | string
        +e_prop_name?: ePropName | string
        +prediction?: Prediction
        +s_method_name?: string
    }

    class Criticals {
        +critical_evaluation?: CriticalEvaluation
        +e_method_name?: eMethodName | string
        +e_prop_name?: ePropName | string
        +prediction?: Prediction
        +s_method_name?: string
    }

    class ExcessPartialApparentEnergyProp {
        +critical_evaluation?: CriticalEvaluation
        +e_method_name?: eMethodName | string
        +e_prop_name?: ePropName | string
        +prediction?: Prediction
        +s_method_name?: string
    }

    class HeatCapacityAndDerivedProp {
        +critical_evaluation?: CriticalEvaluation
        +e_method_name?: eMethodName | string
        +e_prop_name?: ePropName | string
        +prediction?: Prediction
        +s_method_name?: string
    }

    class PhaseTransition {
        +critical_evaluation?: CriticalEvaluation
        +e_method_name?: eMethodName | string
        +e_prop_name?: ePropName | string
        +prediction?: Prediction
        +s_method_name?: string
    }

    class ReactionEquilibriumProp {
        +critical_evaluation?: CriticalEvaluation
        +e_method_name?: eMethodName | string
        +e_prop_name?: ePropName | string
        +prediction?: Prediction
        +s_method_name[0..*]: string
    }

    class ReactionStateChangeProp {
        +critical_evaluation?: CriticalEvaluation
        +e_method_name?: eMethodName | string
        +e_prop_name?: ePropName | string
        +prediction?: Prediction
        +s_method_name[0..*]: string
    }

    class RefractionSurfaceTensionSoundSpeed {
        +critical_evaluation?: CriticalEvaluation
        +e_method_name?: eMethodName | string
        +e_prop_name?: ePropName | string
        +prediction?: Prediction
        +s_method_name?: string
    }

    class TransportProp {
        +critical_evaluation?: CriticalEvaluation
        +e_method_name?: eMethodName | string
        +e_prop_name?: ePropName | string
        +prediction?: Prediction
        +s_method_name?: string
    }

    class VaporPBoilingTAzeotropTandP {
        +critical_evaluation?: CriticalEvaluation
        +e_method_name?: eMethodName | string
        +e_prop_name?: ePropName | string
        +prediction?: Prediction
        +s_method_name?: string
    }

    class VolumetricProp {
        +critical_evaluation?: CriticalEvaluation
        +e_method_name?: eMethodName | string
        +e_prop_name?: ePropName | string
        +prediction?: Prediction
        +s_method_name?: string
    }

    class CriticalEvaluation {
        +equation_of_state?: EquationOfState
        +multi_prop?: MultiProp
        +single_prop?: SingleProp
    }

    class Prediction {
        +e_prediction_type?: ePredictionType | string
        +prediction_method_ref[0..*]: PredictionMethodRef
        +s_prediction_method_description?: string
        +s_prediction_method_name?: string
    }

    class PredictionMethodRef {
        +book?: Book
        +journal?: Journal
        +thesis?: Thesis
        +date_cit?: string
        +e_language?: eLanguage | string
        +e_source_type?: eSourceType | string
        +e_type?: eType | string
        +s_abstract?: string
        +s_author[0..*]: string
        +s_cas_cit?: string
        +s_document_origin?: string
        +s_doi?: string
        +s_id_num?: string
        +s_keyword[0..*]: string
        +s_location?: string
        +s_page?: string
        +s_pub_name?: string
        +s_title?: string
        +s_vol?: string
        +trc_ref_id?: TRCRefID
        +url_cit?: string
        +yr_pub_yr?: string
    }

    class SingleProp {
        +eval_single_prop_ref[0..*]: EvalSinglePropRef
        +s_eval_single_prop_description?: string
    }

    class MultiProp {
        +eval_multi_prop_ref[0..*]: EvalMultiPropRef
        +s_eval_multi_prop_description?: string
        +s_eval_multi_prop_list?: string
    }

    class EvalSinglePropRef {
        +book?: Book
        +journal?: Journal
        +thesis?: Thesis
        +date_cit?: string
        +e_language?: eLanguage | string
        +e_source_type?: eSourceType | string
        +e_type?: eType | string
        +s_abstract?: string
        +s_author[0..*]: string
        +s_cas_cit?: string
        +s_document_origin?: string
        +s_doi?: string
        +s_id_num?: string
        +s_keyword[0..*]: string
        +s_location?: string
        +s_page?: string
        +s_pub_name?: string
        +s_title?: string
        +s_vol?: string
        +trc_ref_id?: TRCRefID
        +url_cit?: string
        +yr_pub_yr?: string
    }

    class EvalMultiPropRef {
        +book?: Book
        +journal?: Journal
        +thesis?: Thesis
        +date_cit?: string
        +e_language?: eLanguage | string
        +e_source_type?: eSourceType | string
        +e_type?: eType | string
        +s_abstract?: string
        +s_author[0..*]: string
        +s_cas_cit?: string
        +s_document_origin?: string
        +s_doi?: string
        +s_id_num?: string
        +s_keyword[0..*]: string
        +s_location?: string
        +s_page?: string
        +s_pub_name?: string
        +s_title?: string
        +s_vol?: string
        +trc_ref_id?: TRCRefID
        +url_cit?: string
        +yr_pub_yr?: string
    }

    class EquationOfState {
        +eval_eos_ref[0..*]: EvalEOSRef
        +s_eval_eos_description?: string
        +s_eval_eos_name?: string
    }

    class EvalEOSRef {
        +book?: Book
        +journal?: Journal
        +thesis?: Thesis
        +date_cit?: string
        +e_language?: eLanguage | string
        +e_source_type?: eSourceType | string
        +e_type?: eType | string
        +s_abstract?: string
        +s_author[0..*]: string
        +s_cas_cit?: string
        +s_document_origin?: string
        +s_doi?: string
        +s_id_num?: string
        +s_keyword[0..*]: string
        +s_location?: string
        +s_page?: string
        +s_pub_name?: string
        +s_title?: string
        +s_vol?: string
        +trc_ref_id?: TRCRefID
        +url_cit?: string
        +yr_pub_yr?: string
    }

    class EqProperty {
        +n_prop_number?: integer
        +n_pure_or_mixture_data_number?: integer
        +n_reaction_data_number?: integer
        +s_eq_symbol?: string
        +n_eq_prop_index[0..*]: integer
        +n_eq_prop_range_max?: float
        +n_eq_prop_range_min?: float
        +s_other_prop_unit?: string
    }

    class EqConstraint {
        +n_constraint_number?: integer
        +n_pure_or_mixture_data_number?: integer
        +n_reaction_data_number?: integer
        +s_eq_symbol?: string
        +n_eq_constraint_index[0..*]: integer
        +n_eq_constraint_range_max?: float
        +n_eq_constraint_range_min?: float
        +s_other_constraint_unit?: string
    }

    class EqVariable {
        +n_pure_or_mixture_data_number?: integer
        +n_reaction_data_number?: integer
        +n_var_number?: integer
        +s_eq_symbol?: string
        +n_eq_var_index[0..*]: integer
        +n_eq_var_range_max?: float
        +n_eq_var_range_min?: float
        +s_other_var_unit?: string
    }

    class EqParameter {
        +n_eq_par_digits?: integer
        +n_eq_par_value?: float
        +s_eq_par_symbol?: string
        +n_eq_par_index[0..*]: integer
        +n_eq_par_number?: integer
    }

    class EqConstant {
        +n_eq_constant_digits?: integer
        +n_eq_constant_value?: float
        +s_eq_constant_symbol?: string
        +n_eq_constant_index[0..*]: integer
    }

    class Covariance {
        +n_covariance_value?: float
        +n_eq_par_number1?: integer
        +n_eq_par_number2?: integer
    }

    %% Enum definitions
    class eType {
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

    class eSourceType {
        <<enumeration>>
        CHEMICALABSTRACTS
        ORIGINAL
        OTHER
    }

    class eLanguage {
        <<enumeration>>
        CHINESE
        ENGLISH
        FRENCH
        GERMAN
        JAPANESE
        OTHER_LANGUAGE
        POLISH
        RUSSIAN
    }

    class eSpeciationState {
        <<enumeration>>
        EQUILIBRIUM
        SINGLE_SPECIES
    }

    class eSource {
        <<enumeration>>
        COMMERCIAL_SOURCE
        ISOLATED_FROM_A_NATURAL_PRODUCT
        NO_SAMPLE_USED
        NOT_STATED_IN_THE_DOCUMENT
        STANDARD_REFERENCE_MATERIAL_SRM
        SYNTHESIZED_BY_OTHERS
        SYNTHESIZED_BY_THE_AUTHORS
    }

    class eStatus {
        <<enumeration>>
        NOSAMPLE
        NOTDESCRIBED
        PREVIOUSPAPER
        UNKNOWN
    }

    class ePurifMethod {
        <<enumeration>>
        CHEMICAL_REAGENT_TREATMENT
        CRYSTALLIZATION_FROM_MELT
        CRYSTALLIZATION_FROM_SOLUTION
        DEGASSED_BY_BOILING_OR_ULTRASONICALLY
        DEGASSED_BY_EVACUATION
        DEGASSED_BY_FREEZING_AND_MELTING_IN_VACUUM
        DRIED_BY_OVEN_HEATING
        DRIED_BY_VACUUM_HEATING
        DRIED_IN_A_DESICCATOR
        DRIED_WITH_CHEMICAL_REAGENT
        FRACTIONAL_CRYSTALLIZATION
        FRACTIONAL_DISTILLATION
        IMPURITY_ADSORPTION
        LIQUID_CHROMATOGRAPHY
        MOLECULAR_SIEVE_TREATMENT
        NONE_USED
        OTHER
        PREPARATIVE_GAS_CHROMATOGRAPHY
        SALTING_OUT_OF_SOLUTION
        SOLVENT_EXTRACTION
        STEAM_DISTILLATION
        SUBLIMATION
        UNSPECIFIED
        VACUUM_DEGASIFICATION
        ZONE_REFINING
    }

    class eAnalMeth {
        <<enumeration>>
        ACIDBASE_TITRATION
        CHEMICAL_ANALYSIS
        CO2_YIELD_IN_COMBUSTION_PRODUCTS
        DENSITY
        DIFFERENCE_BETWEEN_BUBBLE_AND_DEW_TEMPERATURES
        DSC
        ESTIMATED_BY_THE_COMPILER
        ESTIMATION
        FRACTION_MELTING_IN_AN_ADIABATIC_CALORIMETER
        GAS_CHROMATOGRAPHY
        HPLC
        ION_CHROMATOGRAPHY
        IONSELECTIVE_ELECTRODE
        KARL_FISCHER_TITRATION
        MASS_LOSS_ON_DRYING
        MASS_SPECTROMETRY
        NMR_OTHER
        NMR_PROTON
        NOT_KNOWN
        OTHER
        OTHER_TYPES_OF_TITRATION
        SPECTROSCOPY
        STATED_BY_SUPPLIER
        THERMAL_ANALYSIS_USING_TEMPERATURETIME_MEASUREMENT
    }

    class eFunction {
        <<enumeration>>
        BUFFER
        COFACTOR
        INERT
    }

    class eExpPurpose {
        <<enumeration>>
        DETERMINED_FOR_IDENTIFICATION_OF_A_SYNTHESIZED_COMPOUND
        PRINCIPAL_OBJECTIVE_OF_THE_WORK
        SECONDARY_PURPOSE_BYPRODUCT_OF_OTHER_OBJECTIVE
    }

    class ePropName {
        <<enumeration>>
        DECADIC_LOGARITHM_OF_EQUILIBRIUM_CONSTANT_IN_TERMS_OF_AMOUNT_CONCENTRATION_MOLARITY_MOLDM3N
        DECADIC_LOGARITHM_OF_EQUILIBRIUM_CONSTANT_IN_TERMS_OF_MOLALITY_MOLKGN
        DECADIC_LOGARITHM_OF_EQUILIBRIUM_CONSTANT_IN_TERMS_OF_MOLE_FRACTION
        DECADIC_LOGARITHM_OF_EQUILIBRIUM_CONSTANT_IN_TERMS_OF_PARTIAL_PRESSURE_KPAN
        DECADIC_LOGARITHM_OF_THERMODYNAMIC_EQUILIBRIUM_CONSTANT
        EQUILIBRIUM_CONSTANT_IN_TERMS_OF_AMOUNT_CONCENTRATION_MOLARITY_MOLDM3N
        EQUILIBRIUM_CONSTANT_IN_TERMS_OF_MOLALITY_MOLKGN
        EQUILIBRIUM_CONSTANT_IN_TERMS_OF_MOLE_FRACTION
        EQUILIBRIUM_CONSTANT_IN_TERMS_OF_PARTIAL_PRESSURE_KPAN
        NATURAL_LOGARITHM_OF_EQUILIBRIUM_CONSTANT_IN_TERMS_OF_AMOUNT_CONCENTRATION_MOLARITY_MOLDM3N
        NATURAL_LOGARITHM_OF_EQUILIBRIUM_CONSTANT_IN_TERMS_OF_MOLALITY_MOLKGN
        NATURAL_LOGARITHM_OF_EQUILIBRIUM_CONSTANT_IN_TERMS_OF_MOLE_FRACTION
        NATURAL_LOGARITHM_OF_EQUILIBRIUM_CONSTANT_IN_TERMS_OF_PARTIAL_PRESSURE_KPAN
        NATURAL_LOGARITHM_OF_THERMODYNAMIC_EQUILIBRIUM_CONSTANT
        THERMODYNAMIC_EQUILIBRIUM_CONSTANT
    }

    class eMethodName {
        <<enumeration>>
        ANION_EXCHANGE
        CATION_EXCHANGE
        CELL_POTENTIAL_WITH_GLASS_ELECTRODE
        CELL_POTENTIAL_WITH_PLATINUM_ELECTRODE
        CELL_POTENTIAL_WITH_QUINHYDRONE_ELECTRODE
        CELL_POTENTIAL_WITH_REDOX_ELECTRODE
        CHROMATOGRAPHY
        COLORIMETRY
        CONDUCTIVITY_MEASUREMENT
        COULOMETRY
        CRYOSCOPY
        DISTRIBUTION_BETWEEN_TWO_PHASES
        DYNAMIC_EQUILIBRATION
        ION_SELECTIVE_ELECTRODE
        IR_SPECTROMETRY
        MOLAR_VOLUME_DETERMINATION
        NMR_SPECTROMETRY
        OTHER
        POLAROGRAPHY
        POTENTIAL_DIFFERENCE_OF_AN_ELECTROCHEMICAL_CELL
        POTENTIOMETRY
        PROTON_RELAXATION
        RATE_OF_REACTION
        SOLUBILITY_MEASUREMENT
        SOLVENT_EXTRACTION
        SPECTROPHOTOMETRY
        STATIC_EQUILIBRATION
        THERMAL_LENSING_SPECTROPHOTOMETRY
        TITRATION
        TRANSIENT_CONDUCTIVITY_MEASUREMENT
        UV_SPECTROSCOPY
        VOLTAMMETRY
    }

    class ePredictionType {
        <<enumeration>>
        AB_INITIO
        CORRELATION
        CORRESPONDING_STATES
        GROUP_CONTRIBUTION
        MOLECULAR_DYNAMICS
        MOLECULAR_MECHANICS
        SEMIEMPIRICAL_QUANTUM_METHODS
        STATISTICAL_MECHANICS
    }

    class ePropPhase {
        <<enumeration>>
        AIR_AT_1_ATMOSPHERE
        CHOLESTERIC_LIQUID_CRYSTAL
        CRYSTAL
        CRYSTAL_1
        CRYSTAL_2
        CRYSTAL_3
        CRYSTAL_4
        CRYSTAL_5
        CRYSTAL_OF_INTERCOMPONENT_COMPOUND_1
        CRYSTAL_OF_INTERCOMPONENT_COMPOUND_2
        CRYSTAL_OF_INTERCOMPONENT_COMPOUND_3
        CRYSTAL_OF_UNKNOWN_TYPE
        FLUID_SUPERCRITICAL_OR_SUBCRITICAL_PHASES
        GAS
        GLASS
        IDEAL_GAS
        LIQUID
        LIQUID_CRYSTAL_OF_UNKNOWN_TYPE
        LIQUID_MIXTURE_1
        LIQUID_MIXTURE_2
        LIQUID_MIXTURE_3
        METASTABLE_CRYSTAL
        NEMATIC_LIQUID_CRYSTAL
        NEMATIC_LIQUID_CRYSTAL_1
        NEMATIC_LIQUID_CRYSTAL_2
        SMECTIC_LIQUID_CRYSTAL
        SMECTIC_LIQUID_CRYSTAL_1
        SMECTIC_LIQUID_CRYSTAL_2
        SOLUTION
        SOLUTION_1
        SOLUTION_2
        SOLUTION_3
        SOLUTION_4
    }

    class eCrystalLatticeType {
        <<enumeration>>
        CUBIC
        HEXAGONAL
        MONOCLINIC
        ORTHORHOMBIC
        RHOMBOHEDRAL
        TETRAGONAL
        TRICLINIC
    }

    class eBioState {
        <<enumeration>>
        DENATURATED
        NATIVE
    }

    class ePresentation {
        <<enumeration>>
        DIFFERENCE_BETWEEN_UPPER_AND_LOWER_PRESSURE_XP2XP1
        DIFFERENCE_BETWEEN_UPPER_AND_LOWER_TEMPERATURE_XT2XT1
        DIFFERENCE_WITH_THE_REFERENCE_STATE_XXREF
        DIRECT_VALUE_X
        MEAN_BETWEEN_UPPER_AND_LOWER_TEMPERATURE_XT2XT12
        RATIO_OF_DIFFERENCE_WITH_THE_REFERENCE_STATE_TO_THE_REFERENCE_STATE_XXREFXREF
        RATIO_WITH_THE_REFERENCE_STATE_XXREF
    }

    class eRefStateType {
        <<enumeration>>
        IDEAL_GAS_AT_THE_SAME_AMOUNT_DENSITY_TEMPERATURE_AND_COMPOSITION
        IDEAL_MIXTURE_OF_PURE_FLUID_COMPONENTS_AT_THE_SAME_AMOUNT_DENSITY_TEMPERATURE_AND_COMPOSITION
        PHASE_IN_EQUILIBRIUM_WITH_PRIMARY_PHASE_AT_THE_SAME_TEMPERATURE_AND_PRESSURE
        PURE_COMPONENTS_IN_THE_SAME_PROPORTION_AT_FIXED_TEMPERATURE_AND_PRESSURE
        PURE_COMPONENTS_IN_THE_SAME_PROPORTION_AT_THE_SAME_TEMPERATURE_AND_PRESSURE
        PURE_SOLUTE_AT_THE_SAME_TEMPERATURE_AND_PRESSURE
        PURE_SOLVENT_AT_THE_SAME_TEMPERATURE_AND_PRESSURE
        PURE_SOLVENT_AT_THE_TEMPERATURE_OF_THE_SAME_PHASE_EQUILIBRIUM
        REFERENCE_PHASE_AT_FIXED_TEMPERATURE_AND_THE_SAME_PRESSURE
        REFERENCE_PHASE_AT_THE_SAME_TEMPERATURE_AND_FIXED_PRESSURE
        REFERENCE_PHASE_WITH_THE_SAME_COMPOSITION_AT_FIXED_TEMPERATURE_AND_PRESSURE
        REFERENCE_PHASE_WITH_THE_SAME_COMPOSITION_TEMPERATURE_AND_PRESSURE
    }

    class eRefPhase {
        <<enumeration>>
        AIR_AT_1_ATMOSPHERE
        CHOLESTERIC_LIQUID_CRYSTAL
        CRYSTAL
        CRYSTAL_1
        CRYSTAL_2
        CRYSTAL_3
        CRYSTAL_4
        CRYSTAL_5
        CRYSTAL_OF_INTERCOMPONENT_COMPOUND_1
        CRYSTAL_OF_INTERCOMPONENT_COMPOUND_2
        CRYSTAL_OF_INTERCOMPONENT_COMPOUND_3
        CRYSTAL_OF_UNKNOWN_TYPE
        FLUID_SUPERCRITICAL_OR_SUBCRITICAL_PHASES
        GAS
        GLASS
        IDEAL_GAS
        LIQUID
        LIQUID_CRYSTAL_OF_UNKNOWN_TYPE
        LIQUID_MIXTURE_1
        LIQUID_MIXTURE_2
        LIQUID_MIXTURE_3
        METASTABLE_CRYSTAL
        NEMATIC_LIQUID_CRYSTAL
        NEMATIC_LIQUID_CRYSTAL_1
        NEMATIC_LIQUID_CRYSTAL_2
        SMECTIC_LIQUID_CRYSTAL
        SMECTIC_LIQUID_CRYSTAL_1
        SMECTIC_LIQUID_CRYSTAL_2
        SOLUTION
        SOLUTION_1
        SOLUTION_2
        SOLUTION_3
        SOLUTION_4
    }

    class eStandardState {
        <<enumeration>>
        INFINITE_DILUTION_SOLUTE
        PURE_COMPOUND
        PURE_LIQUID_SOLUTE
        STANDARD_AMOUNT_CONCENTRATION_1_MOLDM3_SOLUTE
        STANDARD_MOLALITY_1_MOLKG_SOLUTE
    }

    class eCombUncertEvalMethod {
        <<enumeration>>
        COMPARISON_WITH_REFERENCE_PROPERTY_VALUES
        PROPAGATION_OF_EVALUATED_STANDARD_UNCERTAINTIES
    }

    class eRepeatMethod {
        <<enumeration>>
        OTHER
        STANDARD_DEVIATION_OF_A_SINGLE_VALUE_BIASED
        STANDARD_DEVIATION_OF_A_SINGLE_VALUE_UNBIASED
        STANDARD_DEVIATION_OF_THE_MEAN
    }

    class eDeviceSpecMethod {
        <<enumeration>>
        CALIBRATED_BY_THE_EXPERIMENTALIST
        CERTIFIED_OR_CALIBRATED_BY_A_THIRD_PARTY
        SPECIFIED_BY_THE_MANUFACTURER
    }

    class ePhase {
        <<enumeration>>
        AIR_AT_1_ATMOSPHERE
        CHOLESTERIC_LIQUID_CRYSTAL
        CRYSTAL
        CRYSTAL_1
        CRYSTAL_2
        CRYSTAL_3
        CRYSTAL_4
        CRYSTAL_5
        CRYSTAL_OF_INTERCOMPONENT_COMPOUND_1
        CRYSTAL_OF_INTERCOMPONENT_COMPOUND_2
        CRYSTAL_OF_INTERCOMPONENT_COMPOUND_3
        CRYSTAL_OF_UNKNOWN_TYPE
        FLUID_SUPERCRITICAL_OR_SUBCRITICAL_PHASES
        GAS
        GLASS
        IDEAL_GAS
        LIQUID
        LIQUID_CRYSTAL_OF_UNKNOWN_TYPE
        LIQUID_MIXTURE_1
        LIQUID_MIXTURE_2
        LIQUID_MIXTURE_3
        METASTABLE_CRYSTAL
        NEMATIC_LIQUID_CRYSTAL
        NEMATIC_LIQUID_CRYSTAL_1
        NEMATIC_LIQUID_CRYSTAL_2
        SMECTIC_LIQUID_CRYSTAL
        SMECTIC_LIQUID_CRYSTAL_1
        SMECTIC_LIQUID_CRYSTAL_2
        SOLUTION
        SOLUTION_1
        SOLUTION_2
        SOLUTION_3
        SOLUTION_4
    }

    class eTemperature {
        <<enumeration>>
        LOWER_TEMPERATURE_K
        TEMPERATURE_K
        UPPER_TEMPERATURE_K
    }

    class ePressure {
        <<enumeration>>
        LOWER_PRESSURE_KPA
        PARTIAL_PRESSURE_KPA
        PRESSURE_KPA
        UPPER_PRESSURE_KPA
    }

    class eComponentComposition {
        <<enumeration>>
        AMOUNT_CONCENTRATION_MOLARITY_MOLDM3
        AMOUNT_RATIO_OF_SOLUTE_TO_SOLVENT
        FINAL_MASS_FRACTION_OF_SOLUTE
        FINAL_MOLALITY_OF_SOLUTE_MOLKG
        FINAL_MOLE_FRACTION_OF_SOLUTE
        INITIAL_MASS_FRACTION_OF_SOLUTE
        INITIAL_MOLALITY_OF_SOLUTE_MOLKG
        INITIAL_MOLE_FRACTION_OF_SOLUTE
        MASS_FRACTION
        MASS_RATIO_OF_SOLUTE_TO_SOLVENT
        MOLALITY_MOLKG
        MOLE_FRACTION
        RATIO_OF_AMOUNT_OF_SOLUTE_TO_MASS_OF_SOLUTION_MOLKG
        RATIO_OF_MASS_OF_SOLUTE_TO_VOLUME_OF_SOLUTION_KGM3
        VOLUME_FRACTION
        VOLUME_RATIO_OF_SOLUTE_TO_SOLVENT
    }

    class eSolventComposition {
        <<enumeration>>
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
    }

    class eMiscellaneous {
        <<enumeration>>
        ACTIVITY_COEFFICIENT
        AMOUNT_DENSITY_MOLM3
        FREQUENCY_MHZ
        MASS_DENSITY_KGM3
        MOLAR_ENTROPY_JKMOL
        MOLAR_VOLUME_M3MOL
        RELATIVE_ACTIVITY
        SPECIFIC_VOLUME_M3KG
        WAVELENGTH_NM
    }

    class eBioVariables {
        <<enumeration>>
        IONIC_STRENGTH_AMOUNT_CONCENTRATION_BASIS_MOLDM3
        IONIC_STRENGTH_MOLALITY_BASIS_MOLKG
        PC_AMOUNT_CONCENTRATION_BASIS
        PH
        SOLVENT_PC_AMOUNT_CONCENTRATION_BASIS
    }

    class eParticipantAmount {
        <<enumeration>>
        AMOUNT_MOL
        MASS_KG
    }

    class eConstraintPhase {
        <<enumeration>>
        AIR_AT_1_ATMOSPHERE
        CHOLESTERIC_LIQUID_CRYSTAL
        CRYSTAL
        CRYSTAL_1
        CRYSTAL_2
        CRYSTAL_3
        CRYSTAL_4
        CRYSTAL_5
        CRYSTAL_OF_INTERCOMPONENT_COMPOUND_1
        CRYSTAL_OF_INTERCOMPONENT_COMPOUND_2
        CRYSTAL_OF_INTERCOMPONENT_COMPOUND_3
        CRYSTAL_OF_UNKNOWN_TYPE
        FLUID_SUPERCRITICAL_OR_SUBCRITICAL_PHASES
        GAS
        GLASS
        IDEAL_GAS
        LIQUID
        LIQUID_CRYSTAL_OF_UNKNOWN_TYPE
        LIQUID_MIXTURE_1
        LIQUID_MIXTURE_2
        LIQUID_MIXTURE_3
        METASTABLE_CRYSTAL
        NEMATIC_LIQUID_CRYSTAL
        NEMATIC_LIQUID_CRYSTAL_1
        NEMATIC_LIQUID_CRYSTAL_2
        SMECTIC_LIQUID_CRYSTAL
        SMECTIC_LIQUID_CRYSTAL_1
        SMECTIC_LIQUID_CRYSTAL_2
        SOLUTION
        SOLUTION_1
        SOLUTION_2
        SOLUTION_3
        SOLUTION_4
    }

    class eVarPhase {
        <<enumeration>>
        AIR_AT_1_ATMOSPHERE
        CHOLESTERIC_LIQUID_CRYSTAL
        CRYSTAL
        CRYSTAL_1
        CRYSTAL_2
        CRYSTAL_3
        CRYSTAL_4
        CRYSTAL_5
        CRYSTAL_OF_INTERCOMPONENT_COMPOUND_1
        CRYSTAL_OF_INTERCOMPONENT_COMPOUND_2
        CRYSTAL_OF_INTERCOMPONENT_COMPOUND_3
        CRYSTAL_OF_UNKNOWN_TYPE
        FLUID_SUPERCRITICAL_OR_SUBCRITICAL_PHASES
        GAS
        GLASS
        IDEAL_GAS
        LIQUID
        LIQUID_CRYSTAL_OF_UNKNOWN_TYPE
        LIQUID_MIXTURE_1
        LIQUID_MIXTURE_2
        LIQUID_MIXTURE_3
        METASTABLE_CRYSTAL
        NEMATIC_LIQUID_CRYSTAL
        NEMATIC_LIQUID_CRYSTAL_1
        NEMATIC_LIQUID_CRYSTAL_2
        SMECTIC_LIQUID_CRYSTAL
        SMECTIC_LIQUID_CRYSTAL_1
        SMECTIC_LIQUID_CRYSTAL_2
        SOLUTION
        SOLUTION_1
        SOLUTION_2
        SOLUTION_3
        SOLUTION_4
    }

    class eEqName {
        <<enumeration>>
        THERMOMLANTOINEVAPORPRESSURE
        THERMOMLCUSTOMEXPANSION
        THERMOMLHELMHOLTZ3GENERALEOS
        THERMOMLHELMHOLTZ4GENERALEOS
        THERMOMLPOLYNOMIALEXPANSION
        THERMOMLSPANWAGNER12NONPOLAREOS
        THERMOMLSPANWAGNER12POLAREOS
        THERMOMLWAGNER25LINEARVAPORPRESSURE
        THERMOMLWAGNER36LINEARVAPORPRESSURE
        THERMOMLWAGNERLINEARVAPORPRESSURE
    }

    class eCompositionRepresentation {
        <<enumeration>>
        AMOUNT_CONCENTRATION_AMOUNT_OF_PARTICIPANT_PER_VOLUME_OF_SOLUTION_MOLDM3
        AMOUNT_OF_PARTICIPANT_PER_MASS_OF_SOLUTION_MOLKG
        AMOUNT_RATIO_OF_PARTICIPANT_TO_SOLVENT
        AMOUNT_RATIO_OF_SOLVENT_TO_PARTICIPANT
        MASS_OF_PARTICIPANT_PER_VOLUME_OF_SOLUTION_KGM3
        MASS_RATIO_OF_PARTICIPANT_TO_SOLVENT
        MOLALITY_AMOUNT_OF_PARTICIPANT_PER_MASS_OF_SOLVENT_MOLKG
        VOLUME_RATIO_OF_PARTICIPANT_TO_SOLVENT
    }

    class eReactionFormalism {
        <<enumeration>>
        BIOCHEMICAL
        CHEMICAL
    }

    class eReactionType {
        <<enumeration>>
        ADDITION_OF_VARIOUS_COMPOUNDS_TO_UNSATURATED_COMPOUNDS
        ADDITION_OF_WATER_TO_A_LIQUID_OR_SOLID_TO_PRODUCE_A_HYDRATE
        ATOMIZATION_OR_FORMATION_FROM_ATOMS
        COMBUSTION_WITH_OTHER_ELEMENTS_OR_COMPOUNDS
        COMBUSTION_WITH_OXYGEN
        ESTERIFICATION
        EXCHANGE_OF_ALKYL_GROUPS
        EXCHANGE_OF_HYDROGEN_ATOMS_WITH_OTHER_GROUPS
        FORMATION_OF_A_COMPOUND_FROM_ELEMENTS_IN_THEIR_STABLE_STATE
        FORMATION_OF_ION
        HALOGENATION_ADDITION_OF_OR_REPLACEMENT_BY_A_HALOGEN
        HOMONUCLEAR_DIMERIZATION
        HYDROGENATION_ADDITION_OF_HYDROGEN_TO_UNSATURATED_COMPOUNDS
        HYDROHALOGENATION
        HYDROLYSIS_OF_IONS
        ION_EXCHANGE
        NEUTRALIZATION_REACTION_OF_AN_ACID_WITH_A_BASE
        OTHER_REACTIONS
        OTHER_REACTIONS_WITH_WATER
        OXIDATION_WITH_OXIDIZING_AGENTS_OTHER_THAN_OXYGEN
        OXIDATION_WITH_OXYGEN_NOT_COMPLETE
        POLYMERIZATION_ALL_OTHER_TYPES
        SOLVOLYIS_SOLVENTS_OTHER_THAN_WATER
        STEREOISOMERISM
        STRUCTURAL_ISOMERIZATION
    }

    %% Relationships
    DataReport "1" <|-- "1" Citation
    DataReport "1" <|-- "1" Version
    DataReport "1" <|-- "*" Compound
    DataReport "1" <|-- "*" PureOrMixtureData
    DataReport "1" <|-- "*" ReactionData
    Citation "1" <|-- "1" Book
    Citation "1" <|-- "1" Journal
    Citation "1" <|-- "1" Thesis
    Citation "1" <|-- "1" eLanguage
    Citation "1" <|-- "1" eSourceType
    Citation "1" <|-- "1" eType
    Citation "1" <|-- "1" TRCRefID
    Compound "1" <|-- "1" Biomaterial
    Compound "1" <|-- "1" Ion
    Compound "1" <|-- "1" MulticomponentSubstance
    Compound "1" <|-- "1" Polymer
    Compound "1" <|-- "1" eSpeciationState
    Compound "1" <|-- "1" RegNum
    Compound "1" <|-- "*" SOrgID
    Compound "1" <|-- "*" Sample
    MulticomponentSubstance "1" <|-- "*" Component
    Component "1" <|-- "1" RegNum
    Sample "1" <|-- "*" ComponentSample
    Sample "1" <|-- "1" eSource
    Sample "1" <|-- "1" eStatus
    Sample "1" <|-- "*" Purity
    ComponentSample "1" <|-- "1" RegNum
    Purity "1" <|-- "*" eAnalMeth
    Purity "1" <|-- "*" ePurifMethod
    PureOrMixtureData "1" <|-- "*" Component
    PureOrMixtureData "1" <|-- "*" PhaseID
    PureOrMixtureData "1" <|-- "*" Property
    PureOrMixtureData "1" <|-- "*" AuxiliarySubstance
    PureOrMixtureData "1" <|-- "*" Constraint
    PureOrMixtureData "1" <|-- "1" eExpPurpose
    PureOrMixtureData "1" <|-- "*" Equation
    PureOrMixtureData "1" <|-- "*" NumValues
    PureOrMixtureData "1" <|-- "*" Variable
    AuxiliarySubstance "1" <|-- "1" eFunction
    AuxiliarySubstance "1" <|-- "1" RegNum
    AuxiliarySubstance "1" <|-- "1" ePhase
    Property "1" <|-- "1" ePresentation
    Property "1" <|-- "1" PropertyMethodID
    Property "1" <|-- "*" Catalyst
    Property "1" <|-- "*" CombinedUncertainty
    Property "1" <|-- "*" CurveDev
    Property "1" <|-- "1" eRefStateType
    Property "1" <|-- "1" eStandardState
    Property "1" <|-- "1" PropDeviceSpec
    Property "1" <|-- "*" PropPhaseID
    Property "1" <|-- "1" PropRepeatability
    Property "1" <|-- "*" PropUncertainty
    Property "1" <|-- "1" RefPhaseID
    Property "1" <|-- "1" Solvent
    ReactionData "1" <|-- "1" eReactionType
    ReactionData "1" <|-- "*" Participant
    ReactionData "1" <|-- "*" Property
    ReactionData "1" <|-- "*" AuxiliarySubstance
    ReactionData "1" <|-- "*" Constraint
    ReactionData "1" <|-- "1" eExpPurpose
    ReactionData "1" <|-- "1" eReactionFormalism
    ReactionData "1" <|-- "*" Equation
    ReactionData "1" <|-- "*" NumValues
    ReactionData "1" <|-- "*" Solvent
    ReactionData "1" <|-- "*" Variable
    Participant "1" <|-- "1" eCrystalLatticeType
    Participant "1" <|-- "1" ePhase
    Participant "1" <|-- "1" RegNum
    Participant "1" <|-- "1" eCompositionRepresentation
    Participant "1" <|-- "1" eStandardState
    Catalyst "1" <|-- "1" RegNum
    Catalyst "1" <|-- "1" ePhase
    PhaseID "1" <|-- "1" eCrystalLatticeType
    PhaseID "1" <|-- "1" ePhase
    PhaseID "1" <|-- "1" RegNum
    Constraint "1" <|-- "1" ConstraintID
    Constraint "1" <|-- "1" ConstrDeviceSpec
    Constraint "1" <|-- "1" ConstrRepeatability
    Constraint "1" <|-- "*" ConstrUncertainty
    Constraint "1" <|-- "1" ConstraintPhaseID
    Constraint "1" <|-- "1" Solvent
    Variable "1" <|-- "1" VariableID
    Variable "1" <|-- "1" Solvent
    Variable "1" <|-- "1" VarDeviceSpec
    Variable "1" <|-- "1" VarPhaseID
    Variable "1" <|-- "1" VarRepeatability
    Variable "1" <|-- "*" VarUncertainty
    Solvent "1" <|-- "1" ePhase
    Solvent "1" <|-- "1" RegNum
    PropertyMethodID "1" <|-- "1" PropertyGroup
    PropertyMethodID "1" <|-- "1" RegNum
    PropertyGroup "1" <|-- "1" ActivityFugacityOsmoticProp
    PropertyGroup "1" <|-- "1" BioProperties
    PropertyGroup "1" <|-- "1" CompositionAtPhaseEquilibrium
    PropertyGroup "1" <|-- "1" Criticals
    PropertyGroup "1" <|-- "1" ExcessPartialApparentEnergyProp
    PropertyGroup "1" <|-- "1" HeatCapacityAndDerivedProp
    PropertyGroup "1" <|-- "1" PhaseTransition
    PropertyGroup "1" <|-- "1" ReactionEquilibriumProp
    PropertyGroup "1" <|-- "1" ReactionStateChangeProp
    PropertyGroup "1" <|-- "1" RefractionSurfaceTensionSoundSpeed
    PropertyGroup "1" <|-- "1" TransportProp
    PropertyGroup "1" <|-- "1" VaporPBoilingTAzeotropTandP
    PropertyGroup "1" <|-- "1" VolumetricProp
    PropPhaseID "1" <|-- "1" eBioState
    PropPhaseID "1" <|-- "1" eCrystalLatticeType
    PropPhaseID "1" <|-- "1" ePropPhase
    PropPhaseID "1" <|-- "1" RegNum
    RefPhaseID "1" <|-- "1" eCrystalLatticeType
    RefPhaseID "1" <|-- "1" eRefPhase
    RefPhaseID "1" <|-- "1" RegNum
    ConstraintID "1" <|-- "1" ConstraintType
    ConstraintID "1" <|-- "1" RegNum
    ConstraintType "1" <|-- "1" eBioVariables
    ConstraintType "1" <|-- "1" eComponentComposition
    ConstraintType "1" <|-- "1" eMiscellaneous
    ConstraintType "1" <|-- "1" eParticipantAmount
    ConstraintType "1" <|-- "1" ePressure
    ConstraintType "1" <|-- "1" eSolventComposition
    ConstraintType "1" <|-- "1" eTemperature
    ConstraintPhaseID "1" <|-- "1" eConstraintPhase
    ConstraintPhaseID "1" <|-- "1" eCrystalLatticeType
    ConstraintPhaseID "1" <|-- "1" RegNum
    VariableID "1" <|-- "1" RegNum
    VariableID "1" <|-- "1" VariableType
    VariableType "1" <|-- "1" eBioVariables
    VariableType "1" <|-- "1" eComponentComposition
    VariableType "1" <|-- "1" eMiscellaneous
    VariableType "1" <|-- "1" eParticipantAmount
    VariableType "1" <|-- "1" ePressure
    VariableType "1" <|-- "1" eSolventComposition
    VariableType "1" <|-- "1" eTemperature
    VarPhaseID "1" <|-- "1" eCrystalLatticeType
    VarPhaseID "1" <|-- "1" eVarPhase
    VarPhaseID "1" <|-- "1" RegNum
    NumValues "1" <|-- "*" PropertyValue
    NumValues "1" <|-- "*" VariableValue
    PropertyValue "1" <|-- "1" PropLimit
    PropertyValue "1" <|-- "*" CombinedUncertainty
    PropertyValue "1" <|-- "*" CurveDev
    PropertyValue "1" <|-- "1" PropRepeatability
    PropertyValue "1" <|-- "*" PropUncertainty
    VariableValue "1" <|-- "1" VarRepeatability
    VariableValue "1" <|-- "*" VarUncertainty
    CombinedUncertainty "1" <|-- "1" eCombUncertEvalMethod
    CombinedUncertainty "1" <|-- "1" AsymCombExpandUncert
    CombinedUncertainty "1" <|-- "1" AsymCombStdUncert
    PropUncertainty "1" <|-- "1" AsymExpandUncert
    PropUncertainty "1" <|-- "1" AsymStdUncert
    PropRepeatability "1" <|-- "1" eRepeatMethod
    PropDeviceSpec "1" <|-- "1" eDeviceSpecMethod
    ConstrRepeatability "1" <|-- "1" eRepeatMethod
    ConstrDeviceSpec "1" <|-- "1" eDeviceSpecMethod
    VarRepeatability "1" <|-- "1" eRepeatMethod
    VarDeviceSpec "1" <|-- "1" eDeviceSpecMethod
    Equation "1" <|-- "1" eEqName
    Equation "1" <|-- "*" Covariance
    Equation "1" <|-- "*" EqConstant
    Equation "1" <|-- "*" EqConstraint
    Equation "1" <|-- "*" EqParameter
    Equation "1" <|-- "*" EqProperty
    Equation "1" <|-- "*" EqVariable
    ActivityFugacityOsmoticProp "1" <|-- "1" CriticalEvaluation
    ActivityFugacityOsmoticProp "1" <|-- "1" eMethodName
    ActivityFugacityOsmoticProp "1" <|-- "1" ePropName
    ActivityFugacityOsmoticProp "1" <|-- "1" Prediction
    BioProperties "1" <|-- "1" CriticalEvaluation
    BioProperties "1" <|-- "1" eMethodName
    BioProperties "1" <|-- "1" ePropName
    BioProperties "1" <|-- "1" Prediction
    CompositionAtPhaseEquilibrium "1" <|-- "1" CriticalEvaluation
    CompositionAtPhaseEquilibrium "1" <|-- "1" eMethodName
    CompositionAtPhaseEquilibrium "1" <|-- "1" ePropName
    CompositionAtPhaseEquilibrium "1" <|-- "1" Prediction
    Criticals "1" <|-- "1" CriticalEvaluation
    Criticals "1" <|-- "1" eMethodName
    Criticals "1" <|-- "1" ePropName
    Criticals "1" <|-- "1" Prediction
    ExcessPartialApparentEnergyProp "1" <|-- "1" CriticalEvaluation
    ExcessPartialApparentEnergyProp "1" <|-- "1" eMethodName
    ExcessPartialApparentEnergyProp "1" <|-- "1" ePropName
    ExcessPartialApparentEnergyProp "1" <|-- "1" Prediction
    HeatCapacityAndDerivedProp "1" <|-- "1" CriticalEvaluation
    HeatCapacityAndDerivedProp "1" <|-- "1" eMethodName
    HeatCapacityAndDerivedProp "1" <|-- "1" ePropName
    HeatCapacityAndDerivedProp "1" <|-- "1" Prediction
    PhaseTransition "1" <|-- "1" CriticalEvaluation
    PhaseTransition "1" <|-- "1" eMethodName
    PhaseTransition "1" <|-- "1" ePropName
    PhaseTransition "1" <|-- "1" Prediction
    ReactionEquilibriumProp "1" <|-- "1" CriticalEvaluation
    ReactionEquilibriumProp "1" <|-- "1" eMethodName
    ReactionEquilibriumProp "1" <|-- "1" ePropName
    ReactionEquilibriumProp "1" <|-- "1" Prediction
    ReactionStateChangeProp "1" <|-- "1" CriticalEvaluation
    ReactionStateChangeProp "1" <|-- "1" eMethodName
    ReactionStateChangeProp "1" <|-- "1" ePropName
    ReactionStateChangeProp "1" <|-- "1" Prediction
    RefractionSurfaceTensionSoundSpeed "1" <|-- "1" CriticalEvaluation
    RefractionSurfaceTensionSoundSpeed "1" <|-- "1" eMethodName
    RefractionSurfaceTensionSoundSpeed "1" <|-- "1" ePropName
    RefractionSurfaceTensionSoundSpeed "1" <|-- "1" Prediction
    TransportProp "1" <|-- "1" CriticalEvaluation
    TransportProp "1" <|-- "1" eMethodName
    TransportProp "1" <|-- "1" ePropName
    TransportProp "1" <|-- "1" Prediction
    VaporPBoilingTAzeotropTandP "1" <|-- "1" CriticalEvaluation
    VaporPBoilingTAzeotropTandP "1" <|-- "1" eMethodName
    VaporPBoilingTAzeotropTandP "1" <|-- "1" ePropName
    VaporPBoilingTAzeotropTandP "1" <|-- "1" Prediction
    VolumetricProp "1" <|-- "1" CriticalEvaluation
    VolumetricProp "1" <|-- "1" eMethodName
    VolumetricProp "1" <|-- "1" ePropName
    VolumetricProp "1" <|-- "1" Prediction
    CriticalEvaluation "1" <|-- "1" EquationOfState
    CriticalEvaluation "1" <|-- "1" MultiProp
    CriticalEvaluation "1" <|-- "1" SingleProp
    Prediction "1" <|-- "1" ePredictionType
    Prediction "1" <|-- "*" PredictionMethodRef
    PredictionMethodRef "1" <|-- "1" Book
    PredictionMethodRef "1" <|-- "1" Journal
    PredictionMethodRef "1" <|-- "1" Thesis
    PredictionMethodRef "1" <|-- "1" eLanguage
    PredictionMethodRef "1" <|-- "1" eSourceType
    PredictionMethodRef "1" <|-- "1" eType
    PredictionMethodRef "1" <|-- "1" TRCRefID
    SingleProp "1" <|-- "*" EvalSinglePropRef
    MultiProp "1" <|-- "*" EvalMultiPropRef
    EvalSinglePropRef "1" <|-- "1" Book
    EvalSinglePropRef "1" <|-- "1" Journal
    EvalSinglePropRef "1" <|-- "1" Thesis
    EvalSinglePropRef "1" <|-- "1" eLanguage
    EvalSinglePropRef "1" <|-- "1" eSourceType
    EvalSinglePropRef "1" <|-- "1" eType
    EvalSinglePropRef "1" <|-- "1" TRCRefID
    EvalMultiPropRef "1" <|-- "1" Book
    EvalMultiPropRef "1" <|-- "1" Journal
    EvalMultiPropRef "1" <|-- "1" Thesis
    EvalMultiPropRef "1" <|-- "1" eLanguage
    EvalMultiPropRef "1" <|-- "1" eSourceType
    EvalMultiPropRef "1" <|-- "1" eType
    EvalMultiPropRef "1" <|-- "1" TRCRefID
    EquationOfState "1" <|-- "*" EvalEOSRef
    EvalEOSRef "1" <|-- "1" Book
    EvalEOSRef "1" <|-- "1" Journal
    EvalEOSRef "1" <|-- "1" Thesis
    EvalEOSRef "1" <|-- "1" eLanguage
    EvalEOSRef "1" <|-- "1" eSourceType
    EvalEOSRef "1" <|-- "1" eType
    EvalEOSRef "1" <|-- "1" TRCRefID
```