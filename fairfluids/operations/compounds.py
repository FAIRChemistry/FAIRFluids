"""Compound merging, solvent-ratio derivation, and parameter cleanup on documents."""

from __future__ import annotations

from typing import List, Optional

from fairfluids.core.lib import (
    FAIRFluidsDocument,
    Fluid,
    Parameter,
    ParameterValue,
    Parameters,
    UnitDefinition,
    BaseUnit,
)
from fairfluids.io.pubchem import fetch_compound_from_pubchem
from .sample_utils import _ensure_fluid_sample, _get_measurements


def combine_compounds(
    document: FAIRFluidsDocument,
    old_molecules: List[int],
    new_molecule: int,
    old_compound_ids: Optional[List[str]] = None,
) -> FAIRFluidsDocument:
    """
    Combine separate compounds (e.g., choline chloride ions) into a single compound.

    This function:
    1. Fetches information for the new combined molecule from PubChem
    2. Removes the old compounds from the document
    3. Adds the new compound to the document
    4. Updates all fluid references to use the new compound
    5. Merges parameter values (e.g., mole fractions) for the old compounds
    6. Removes old parameter definitions

    Args:
        document: The FAIRFluidsDocument to modify
        old_molecules: List of pubChemIDs for the old compounds to be combined
        new_molecule: The pubChemID for the new combined compound
        old_compound_ids: Optional explicit compound IDs to merge (used as
            deterministic fallback when CID/InChIKey resolution is incomplete)

    Returns:
        The modified FAIRFluidsDocument
    """
    print(f"=== Combining Compounds ===")
    print(f"Old molecules (pubChemIDs): {old_molecules}")
    print(f"New molecule (pubChemID): {new_molecule}")

    # Fetch compound data from PubChem
    new_compound_data = fetch_compound_from_pubchem(new_molecule)
    if new_compound_data is None:
        raise ValueError(
            f"Could not fetch compound data from PubChem for CID {new_molecule}"
        )

    def _normalize_id_token(value: Optional[str]) -> str:
        if not value:
            return ""
        text = value.lower()
        if text.startswith("compound_"):
            text = text[len("compound_") :]
        # Keep only alphanumeric chars for robust comparisons across styles
        return "".join(ch for ch in text if ch.isalnum())

    # Find old compounds to remove (primary match by pubChemID).
    # We intentionally continue with fallback matching afterwards as well, because
    # documents may contain multiple IDs (aliases) for the same chemical species.
    old_compound_ids_set = set()
    old_compound_indices_set = set()
    for i, compound in enumerate(document.compound):
        if compound.pubChemID in old_molecules:
            if compound.compoundID is not None:
                old_compound_ids_set.add(compound.compoundID)
            old_compound_indices_set.add(i)
            print(
                f"Found old compound to remove: {compound.compoundID} (pubChemID: {compound.pubChemID})"
            )

    # Secondary match by InChIKey (also runs when pubChem matches already exist).
    # Important: build fallback keys primarily from the document itself so the
    # combine step does not depend on live PubChem network access.
    fallback_inchikeys = {
        (compound.standard_InChI_key or "").strip().upper()
        for i, compound in enumerate(document.compound)
        if i in old_compound_indices_set and compound.standard_InChI_key
    }

    # If a CID had no direct match in the document, try to resolve its InChIKey
    # from PubChem as an additional fallback.
    matched_cids = {
        compound.pubChemID
        for i, compound in enumerate(document.compound)
        if i in old_compound_indices_set
    }
    unresolved_cids = [cid for cid in old_molecules if cid not in matched_cids]
    for old_cid in unresolved_cids:
        old_data = fetch_compound_from_pubchem(old_cid)
        if old_data and old_data.get("standard_InChI_key"):
            fallback_inchikeys.add(old_data["standard_InChI_key"].strip().upper())
        else:
            print(
                f"Warning: Could not resolve InChIKey from PubChem for old CID {old_cid}"
            )

    if fallback_inchikeys:
        for i, compound in enumerate(document.compound):
            compound_inchikey = (compound.standard_InChI_key or "").strip().upper()
            if compound_inchikey and compound_inchikey in fallback_inchikeys:
                if compound.compoundID is not None:
                    old_compound_ids_set.add(compound.compoundID)
                old_compound_indices_set.add(i)
                print(
                    "Found old compound to remove via InChIKey fallback: "
                    f"{compound.compoundID} (InChIKey: {compound.standard_InChI_key})"
                )

    explicit_old_ids = set(old_compound_ids or [])
    old_compound_ids_set.update(explicit_old_ids)
    old_compound_ids = list(old_compound_ids_set)
    old_compound_indices = list(old_compound_indices_set)

    # Expand old IDs with alias IDs that are used inside fluids/parameters/samples.
    # Some documents contain inconsistent references where top-level compounds are
    # "compound_1/2/..." while fluids reference "compound_choline", etc.
    target_tokens = set()
    for idx in old_compound_indices:
        comp = document.compound[idx]
        for candidate in [comp.compoundID, comp.commonName]:
            token = _normalize_id_token(candidate)
            if token:
                target_tokens.add(token)

    referenced_compound_ids = set()
    for fluid in document.fluid:
        referenced_compound_ids.update(fluid.compounds or [])
        sample = _ensure_fluid_sample(fluid)
        referenced_compound_ids.update(sample.associated_compounds or [])
        for param in fluid.parameter:
            referenced_compound_ids.update(param.associated_compounds or [])

    for ref_id in referenced_compound_ids:
        ref_token = _normalize_id_token(ref_id)
        if not ref_token:
            continue
        if any(
            ref_token == t or ref_token in t or t in ref_token
            for t in target_tokens
            if len(t) >= 4
        ):
            old_compound_ids_set.add(ref_id)

    old_compound_ids = list(old_compound_ids_set)

    if len(old_compound_ids) == 0:
        print(
            "Warning: No old compounds found to remove (neither by pubChemID nor by InChIKey fallback)"
        )
        return document

    # Create or reuse new compound
    # Clean the common name to generate a consistent compoundID
    clean_name = (
        new_compound_data["commonName"]
        .lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
        .replace(".", "")
    )
    new_compound_id = f"compound_{clean_name}"
    existing_new_compound = next(
        (c for c in document.compound if c.pubChemID == new_molecule),
        None,
    )
    if existing_new_compound is None:
        new_compound = document.add_to_compound(
            compoundID=new_compound_id,
            **new_compound_data,
        )
        print(f"Created new compound: {new_compound.compoundID}")
    else:
        new_compound = existing_new_compound
        new_compound_id = new_compound.compoundID
        print(f"Reusing existing compound: {new_compound.compoundID}")

    # Remove old compounds
    for idx in sorted(old_compound_indices, reverse=True):
        del document.compound[idx]

    # For each fluid, update compounds list and parameter values
    for fluid in document.fluid:
        # Update compounds list and ensure unique entries
        compounds_list = list(fluid.compounds or [])
        old_compound_present = any(
            comp_id in old_compound_ids for comp_id in compounds_list
        )
        if old_compound_present:
            updated_compounds = [
                comp_id for comp_id in compounds_list if comp_id not in old_compound_ids
            ]
            if new_compound_id not in updated_compounds:
                updated_compounds.append(new_compound_id)
            fluid.compounds = updated_compounds
            print(f"Updated fluid compounds: {fluid.compounds}")

        # Keep sample.associated_compounds in sync with fluid.compounds
        sample = _ensure_fluid_sample(fluid)
        sample_assoc = list(sample.associated_compounds or [])
        if any(comp_id in old_compound_ids for comp_id in sample_assoc):
            updated_sample_assoc = [
                comp_id for comp_id in sample_assoc if comp_id not in old_compound_ids
            ]
            if new_compound_id not in updated_sample_assoc:
                updated_sample_assoc.append(new_compound_id)
            sample.associated_compounds = updated_sample_assoc

        # Update parameter associations and collect old mole-fraction parameter IDs
        old_mf_param_ids = []
        for param in fluid.parameter:
            assoc = list(param.associated_compounds or [])
            if any(comp in old_compound_ids for comp in assoc):
                if (
                    param.parameters == Parameters.MOLE_FRACTION
                    and param.parameterID is not None
                ):
                    old_mf_param_ids.append(param.parameterID)
                updated_assoc = [comp for comp in assoc if comp not in old_compound_ids]
                if new_compound_id not in updated_assoc:
                    updated_assoc.append(new_compound_id)
                param.associated_compounds = updated_assoc

        # Remove old mole-fraction parameter definitions for merged compounds
        fluid.parameter = [
            p for p in fluid.parameter if p.parameterID not in old_mf_param_ids
        ]

        # Add new mole-fraction parameter for the combined compound
        if old_mf_param_ids:
            # Get the common name for parameter ID generation
            clean_param_name = (
                new_compound_data["commonName"]
                .lower()
                .replace(" ", "")
                .replace("-", "")
                .replace("_", "")
                .replace(".", "")
            )

            new_param_id = f"parameter_mole_fraction_{clean_param_name}"

            # Check if this parameter already exists
            param_exists = any(p.parameterID == new_param_id for p in fluid.parameter)

            if not param_exists:
                new_param = Parameter(
                    parameterID=new_param_id,
                    parameters=Parameters.MOLE_FRACTION,
                    unit=UnitDefinition(
                        unitID="1",
                        name="dimensionless",
                        base_units=[
                            BaseUnit(
                                kind=None, exponent=None, multiplier=1.0, scale=0.0
                            )
                        ],
                    ),
                    associated_compounds=[new_compound_id],
                )
                fluid.parameter.append(new_param)
                print(f"Added new parameter: {new_param_id}")

        # Update measurements
        for measurement in sample.measurement:
            param_values_to_keep = []

            # Get the common name for the new parameter ID
            clean_param_name = (
                new_compound_data["commonName"]
                .lower()
                .replace(" ", "")
                .replace("-", "")
                .replace("_", "")
                .replace(".", "")
            )
            new_param_id = f"parameter_mole_fraction_{clean_param_name}"

            combined_value = 0.0
            has_old_values = False

            for pv in measurement.parameterValue:
                if pv.parameterID in old_mf_param_ids:
                    combined_value += pv.paramValue or 0.0
                    has_old_values = True
                else:
                    param_values_to_keep.append(pv)

            # If we found old parameter values, add the combined one
            if has_old_values:
                # Find the parameter definition for the new parameter
                new_param = next(
                    (p for p in fluid.parameter if p.parameterID == new_param_id), None
                )

                if new_param:
                    new_param_value = ParameterValue(
                        parameters=Parameters.MOLE_FRACTION,
                        parameterID=new_param_id,
                        paramValue=combined_value,
                        uncertainty=None,
                    )
                    param_values_to_keep.append(new_param_value)
                    print(
                        f"Combined mole fractions: {old_mf_param_ids} -> {combined_value}"
                    )

            measurement.parameterValue = param_values_to_keep

    print("=== Compound Combination Complete ===")
    return document


def calculate_ratio_of_solvent(
    doc: FAIRFluidsDocument,
    name: str,
    compound_id_1: Optional[str] = None,
    compound_id_2: Optional[str] = None,
    parameter_id_1: Optional[str] = None,
    parameter_id_2: Optional[str] = None,
    ratio_parameter: Parameters = Parameters.SOLVENT_AMOUNT_RATIO_OF_COMPONENT_TO_OTHER_COMPONENT_OF_BINARY_SOLVENT,
    new_parameter_id: Optional[str] = None,
    precision: Optional[int] = None,
    print_reported_value: bool = True,
) -> FAIRFluidsDocument:
    """
    Calculate and add a solvent-solvent ratio parameter from two mole fractions.

    Preferred usage is to pass ``compound_id_1`` and ``compound_id_2``. The function
    then finds the corresponding ``Mole fraction`` parameters in each fluid via
    ``associated_compounds`` and computes:
        ratio = x(compound_id_1) / x(compound_id_2)

    For backward compatibility, ``parameter_id_1`` and ``parameter_id_2`` are still
    accepted and used as fallback when compound-based lookup is not possible.

    Args:
        doc: The FAIRFluidsDocument to modify
        name: Name for the new ratio parameter (e.g., "glyceline")
        compound_id_1: Compound ID of numerator component (recommended)
        compound_id_2: Compound ID of denominator component (recommended)
        parameter_id_1: Fallback parameter ID for numerator mole fraction
        parameter_id_2: Fallback parameter ID for denominator mole fraction
        ratio_parameter: Target FAIRFluids parameter enum for the created ratio
        new_parameter_id: Optional explicit ID for the generated ratio parameter
        precision: Number of decimal places to round the ratio to (optional). If None, no rounding is applied.
        print_reported_value: If True, print existing (reported) ratio values before update

    Returns:
        The modified FAIRFluidsDocument

    Example:
        doc = calculate_ratio_of_solvent(
            doc=fairfluids_document,
            parameter_id_1="parameter_mole_fraction_glycerol",
            parameter_id_2="parameter_mole_fraction_cholinechloride",
            name="glyceline",
            compound_id_1="compound_glycerol",
            compound_id_2="compound_cholinechloride",
            precision=2  # Round to 2 decimal places
        )
    """
    print(f"=== Calculating Solvent Ratio: {name} ===")
    print(f"Processing {len(doc.fluid)} fluids")

    def _is_mole_fraction_param(param: Parameter) -> bool:
        return param.parameters == Parameters.MOLE_FRACTION

    def _find_mole_fraction_parameter_id(
        fluid: Fluid, target_compound_id: Optional[str]
    ) -> Optional[str]:
        if not target_compound_id:
            return None
        for param in fluid.parameter:
            assoc = list(param.associated_compounds or [])
            if (
                _is_mole_fraction_param(param)
                and target_compound_id in assoc
                and param.parameterID
            ):
                return param.parameterID
        return None

    ratio_param_id = new_parameter_id or f"parameter_solvent_ratio_{name}"

    for fluid_idx, fluid in enumerate(doc.fluid):
        print(f"\n--- Processing Fluid {fluid_idx + 1} ---")

        compounds_in_fluid = set(fluid.compounds or [])
        if compound_id_1 and compound_id_1 not in compounds_in_fluid:
            print(f"Skipping fluid {fluid_idx + 1}: {compound_id_1} not in fluid")
            continue
        if compound_id_2 and compound_id_2 not in compounds_in_fluid:
            print(f"Skipping fluid {fluid_idx + 1}: {compound_id_2} not in fluid")
            continue

        resolved_param_id_1 = _find_mole_fraction_parameter_id(fluid, compound_id_1)
        resolved_param_id_2 = _find_mole_fraction_parameter_id(fluid, compound_id_2)

        # Backward-compatible fallback to explicit parameter IDs
        if resolved_param_id_1 is None:
            resolved_param_id_1 = parameter_id_1
        if resolved_param_id_2 is None:
            resolved_param_id_2 = parameter_id_2

        if not resolved_param_id_1 or not resolved_param_id_2:
            print(
                f"Skipping fluid {fluid_idx + 1}: no valid mole-fraction parameter pair found"
            )
            continue

        associated_compounds_list: List[str] = []
        if compound_id_1:
            associated_compounds_list.append(compound_id_1)
        if compound_id_2:
            associated_compounds_list.append(compound_id_2)

        existing_ratio_param = next(
            (p for p in fluid.parameter if p.parameterID == ratio_param_id),
            None,
        )
        if existing_ratio_param is None:
            existing_ratio_param = Parameter(
                parameterID=ratio_param_id,
                parameters=ratio_parameter,
                unit=UnitDefinition(
                    unitID="unit_dimensionless",
                    name="dimensionless",
                    base_units=[],
                ),
                associated_compounds=associated_compounds_list,
            )
            fluid.parameter.append(existing_ratio_param)
            print(f"Added new parameter: {ratio_param_id}")
        else:
            existing_ratio_param.parameters = ratio_parameter
            if associated_compounds_list:
                existing_ratio_param.associated_compounds = associated_compounds_list

        for measurement in _get_measurements(fluid):
            value_1 = None
            value_2 = None
            for pv in measurement.parameterValue:
                if pv.parameterID == resolved_param_id_1:
                    value_1 = pv.paramValue
                elif pv.parameterID == resolved_param_id_2:
                    value_2 = pv.paramValue

            if value_1 is None or value_2 is None:
                continue

            if value_2 != 0:
                ratio = value_1 / value_2
                if precision is not None:
                    ratio = round(ratio, precision)
            else:
                ratio = float("inf") if value_1 > 0 else 0.0

            existing_pv = next(
                (
                    pv
                    for pv in measurement.parameterValue
                    if pv.parameterID == ratio_param_id
                ),
                None,
            )
            if existing_pv is None:
                measurement.parameterValue.append(
                    ParameterValue(
                        parameters=ratio_parameter,
                        parameterID=ratio_param_id,
                        paramValue=ratio,
                        uncertainty=None,
                    )
                )
                print(
                    f"Measurement {measurement.measurement_id}: calculated ratio = {ratio}"
                )
            else:
                old_reported_value = existing_pv.paramValue
                existing_pv.parameters = ratio_parameter
                existing_pv.paramValue = ratio
                if print_reported_value:
                    print(
                        "Measurement "
                        f"{measurement.measurement_id}: reported ratio = {old_reported_value}, "
                        f"calculated ratio = {ratio}"
                    )
                else:
                    print(
                        f"Measurement {measurement.measurement_id}: calculated ratio = {ratio}"
                    )

    print("=== Solvent Ratio Calculation Complete ===")
    return doc


def cleanup_orphaned_parameters(doc: FAIRFluidsDocument) -> FAIRFluidsDocument:
    """
    Remove parameters from fluids where the associated compounds are not in the fluid's compounds list.

    This function is useful for cleaning up parameters that were incorrectly added to fluids.
    For example, if a fluid only has water but has a glyceline ratio parameter, this will remove it.

    Args:
        doc: The FAIRFluidsDocument to clean up

    Returns:
        The cleaned FAIRFluidsDocument

    Example:
        doc = cleanup_orphaned_parameters(doc)
    """
    print("=== Cleaning up orphaned parameters ===")

    total_removed = 0

    for fluid_idx, fluid in enumerate(doc.fluid):
        compounds_in_fluid = set(fluid.compounds)
        params_to_remove = []
        param_ids_to_remove = set()

        for param in fluid.parameter:
            # Check if this parameter has associated compounds
            if hasattr(param, "associated_compounds") and param.associated_compounds:
                # Check if ALL associated compounds are in the fluid's compounds list
                compounds_exist = all(
                    comp in compounds_in_fluid for comp in param.associated_compounds
                )

                if not compounds_exist:
                    params_to_remove.append(param)
                    param_ids_to_remove.add(param.parameterID)
                    print(
                        f"Fluid {fluid_idx + 1}: Removing parameter {param.parameterID}"
                    )
                    print(f"  Associated compounds: {param.associated_compounds}")
                    print(f"  Fluid compounds: {list(compounds_in_fluid)}")

        if params_to_remove:
            # Remove from parameter list
            fluid.parameter = [
                p for p in fluid.parameter if p.parameterID not in param_ids_to_remove
            ]

            # Remove from measurements
            for measurement in _get_measurements(fluid):
                measurement.parameterValue = [
                    pv
                    for pv in measurement.parameterValue
                    if pv.parameterID not in param_ids_to_remove
                ]

            total_removed += len(params_to_remove)

    print(f"=== Cleanup complete: removed {total_removed} orphaned parameters ===")
    return doc


__all__ = [
    "combine_compounds",
    "calculate_ratio_of_solvent",
    "cleanup_orphaned_parameters",
]
