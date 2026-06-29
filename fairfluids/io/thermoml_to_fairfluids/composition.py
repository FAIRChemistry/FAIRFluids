"""
Composition helpers for ThermoML → FAIRFluids conversion.

ThermoML often reports only n−1 explicit mole or mass fractions per mixture, or
molalities relative to solvent. This module completes those values, converts
mass fractions and molalities to mole fractions when molar masses are available,
and validates that mole fractions sum to 1.
"""

from __future__ import annotations

import logging
from typing import Dict, List

from fairfluids.core.lib import Compound, Parameter, ParameterValue, Parameters

from .id_registry import IDRegistry
from .mappers import UnitMapper
from .pubchem import enrich_compound_from_pubchem

logger = logging.getLogger(__name__)

MOLE_FRACTION_SUM_TOL = 1e-8
MASS_FRACTION_SUM_TOL = 1e-8

_MOLALITY_PARAM_TYPES = (
    Parameters.MOLALITY,
    Parameters.INITIAL_MOLALITY_OF_SOLUTE,
    Parameters.FINAL_MOLALITY_OF_SOLUTE,
)


def _clamp_unit_fraction(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _molality_params(parameters: List[Parameter]) -> List[Parameter]:
    return [p for p in parameters if p.parameters in _MOLALITY_PARAM_TYPES]


def _molality_solute_compounds(
    param_objects: List[Parameter], compound_refs: List[str]
) -> set[str]:
    solutes: set[str] = set()
    for param in _molality_params(param_objects):
        for compound_id in param.associated_compounds or []:
            if compound_id in compound_refs:
                solutes.add(compound_id)
    return solutes


def _water_compound_ids(
    compounds: List[Compound], compound_refs: List[str]
) -> List[str]:
    by_id = {compound.compoundID: compound for compound in compounds if compound.compoundID}
    water_ids: List[str] = []
    for compound_id in compound_refs:
        compound = by_id.get(compound_id)
        if compound is None or not compound.commonName:
            continue
        if compound.commonName.strip().lower() in {"water", "h2o", "oxidane"}:
            water_ids.append(compound_id)
    return water_ids


def _solvent_compound_ids(
    compound_refs: List[str],
    solute_ids: set[str],
    compounds: List[Compound],
) -> List[str]:
    solvents = [compound_id for compound_id in compound_refs if compound_id not in solute_ids]
    if solvents:
        return solvents
    return _water_compound_ids(compounds, compound_refs)


def _ensure_mole_fraction_parameters_from_alternate_composition(
    parameters: List[Parameter],
    compound_refs: List[str],
    registry: IDRegistry,
    *,
    alternate_params: List[Parameter],
) -> None:
    if not compound_refs or len(alternate_params) < max(len(compound_refs) - 1, 1):
        return

    mf_covered: set[str] = set()
    for param in _composition_params(parameters, Parameters.MOLE_FRACTION):
        mf_covered.update(param.associated_compounds or [])

    for compound_id in compound_refs:
        if compound_id in mf_covered:
            continue
        parameters.append(
            Parameter(
                parameterID=registry.new_id("parameter"),
                parameters=Parameters.MOLE_FRACTION,
                unit=UnitMapper.dimensionless(),
                associated_compounds=[compound_id],
            )
        )
        mf_covered.add(compound_id)


def _composition_params(
    parameters: List[Parameter], param_type: Parameters
) -> List[Parameter]:
    return [p for p in parameters if p.parameters == param_type]


def _compound_to_param_id(
    parameters: List[Parameter], param_type: Parameters
) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for param in _composition_params(parameters, param_type):
        if not param.parameterID:
            continue
        for compound_id in param.associated_compounds or []:
            mapping[compound_id] = param.parameterID
    return mapping


def _extract_compound_values(
    param_values: List[ParameterValue],
    param_objects: List[Parameter],
    param_type: Parameters,
) -> tuple[Dict[str, float], Dict[str, ParameterValue]]:
    compound_to_param = _compound_to_param_id(param_objects, param_type)
    compound_to_value: Dict[str, float] = {}
    param_id_to_pv: Dict[str, ParameterValue] = {}
    for pv in param_values:
        if pv.parameterID is None or pv.paramValue is None:
            continue
        param_id_to_pv[pv.parameterID] = pv
        for compound_id, param_id in compound_to_param.items():
            if param_id == pv.parameterID:
                compound_to_value[compound_id] = float(pv.paramValue)
    return compound_to_value, param_id_to_pv


def _ensure_composition_parameters(
    parameters: List[Parameter],
    compound_refs: List[str],
    registry: IDRegistry,
    param_type: Parameters,
    *,
    label: str,
) -> None:
    """Append implicit composition parameters when ThermoML omits them."""
    comp_params = _composition_params(parameters, param_type)
    covered: set[str] = set()
    for param in comp_params:
        covered.update(param.associated_compounds or [])

    n_compounds = len(compound_refs)
    n_explicit = len(comp_params)
    missing_compounds = [cid for cid in compound_refs if cid not in covered]

    if n_compounds == 1 and n_explicit == 0:
        parameters.append(
            Parameter(
                parameterID=registry.new_id("parameter"),
                parameters=param_type,
                unit=UnitMapper.dimensionless(),
                associated_compounds=[compound_refs[0]],
            )
        )
        return

    if (
        n_compounds > 1
        and n_explicit == n_compounds - 1
        and len(missing_compounds) == 1
    ):
        parameters.append(
            Parameter(
                parameterID=registry.new_id("parameter"),
                parameters=param_type,
                unit=UnitMapper.dimensionless(),
                associated_compounds=[missing_compounds[0]],
            )
        )
        return

    if n_compounds > 1 and n_explicit < n_compounds - 1:
        logger.warning(
            "Cannot infer missing %s parameters: %d compound(s), "
            "only %d explicit parameter(s)",
            label,
            n_compounds,
            n_explicit,
        )


def ensure_mole_fraction_parameters(
    parameters: List[Parameter],
    compound_refs: List[str],
    registry: IDRegistry,
) -> None:
    """Append implicit MOLE_FRACTION parameters when ThermoML omits them."""
    _ensure_composition_parameters(
        parameters,
        compound_refs,
        registry,
        Parameters.MOLE_FRACTION,
        label="MOLE_FRACTION",
    )

    mass_params = _composition_params(parameters, Parameters.MASS_FRACTION)
    _ensure_mole_fraction_parameters_from_alternate_composition(
        parameters,
        compound_refs,
        registry,
        alternate_params=mass_params,
    )
    _ensure_mole_fraction_parameters_from_alternate_composition(
        parameters,
        compound_refs,
        registry,
        alternate_params=_molality_params(parameters),
    )


def ensure_mass_fraction_parameters(
    parameters: List[Parameter],
    compound_refs: List[str],
    registry: IDRegistry,
) -> None:
    """Append implicit MASS_FRACTION parameters when ThermoML omits them."""
    _ensure_composition_parameters(
        parameters,
        compound_refs,
        registry,
        Parameters.MASS_FRACTION,
        label="MASS_FRACTION",
    )


def _complete_composition_values(
    param_values: List[ParameterValue],
    param_objects: List[Parameter],
    compound_refs: List[str],
    param_type: Parameters,
    *,
    label: str,
    sum_tol: float,
) -> Dict[str, float]:
    """Fill or normalize composition values so they sum to 1 when possible."""
    compound_to_param = _compound_to_param_id(param_objects, param_type)
    if not compound_refs:
        return {}

    compound_to_value, param_id_to_pv = _extract_compound_values(
        param_values, param_objects, param_type
    )

    if len(compound_refs) == 1:
        compound_id = compound_refs[0]
        if compound_id not in compound_to_value:
            param_id = compound_to_param.get(compound_id)
            if param_id is not None:
                param_values.append(
                    ParameterValue(
                        parameterID=param_id,
                        parameters=param_type,
                        paramValue=1.0,
                        uncertainty=None,
                    )
                )
                compound_to_value[compound_id] = 1.0
        _validate_fraction_sum(compound_refs, compound_to_value, label, sum_tol)
        return compound_to_value

    missing = [cid for cid in compound_refs if cid not in compound_to_value]
    known_values = [
        compound_to_value[cid] for cid in compound_refs if cid in compound_to_value
    ]

    if len(missing) == 1 and len(known_values) == len(compound_refs) - 1:
        complement = _clamp_unit_fraction(1.0 - sum(known_values))
        missing_id = missing[0]
        param_id = compound_to_param.get(missing_id)
        if param_id is not None:
            param_values.append(
                ParameterValue(
                    parameterID=param_id,
                    parameters=param_type,
                    paramValue=complement,
                    uncertainty=None,
                )
            )
            compound_to_value[missing_id] = complement
        _validate_fraction_sum(compound_refs, compound_to_value, label, sum_tol)
        return compound_to_value

    if not missing:
        total = sum(compound_to_value[cid] for cid in compound_refs)
        if abs(total - 1.0) > sum_tol:
            if total <= 0.0:
                logger.warning(
                    "%s values sum to %.6g; cannot normalize to 1",
                    label,
                    total,
                )
            else:
                logger.warning(
                    "%s values sum to %.6g; normalizing to 1",
                    label,
                    total,
                )
                for compound_id in compound_refs:
                    normalized = compound_to_value[compound_id] / total
                    param_id = compound_to_param[compound_id]
                    if param_id in param_id_to_pv:
                        param_id_to_pv[param_id].paramValue = normalized
                    else:
                        param_values.append(
                            ParameterValue(
                                parameterID=param_id,
                                parameters=param_type,
                                paramValue=normalized,
                                uncertainty=None,
                            )
                        )
                    compound_to_value[compound_id] = normalized
        _validate_fraction_sum(compound_refs, compound_to_value, label, sum_tol)
        return compound_to_value

    logger.warning(
        "Incomplete %s for %d of %d compounds; measurement kept",
        label,
        len(missing),
        len(compound_refs),
    )
    return compound_to_value


def complete_mole_fraction_values(
    param_values: List[ParameterValue],
    param_objects: List[Parameter],
    compound_refs: List[str],
) -> None:
    """Fill or normalize mole-fraction values so they sum to 1 when possible."""
    _complete_composition_values(
        param_values,
        param_objects,
        compound_refs,
        Parameters.MOLE_FRACTION,
        label="mole fractions",
        sum_tol=MOLE_FRACTION_SUM_TOL,
    )


def complete_mass_fraction_values(
    param_values: List[ParameterValue],
    param_objects: List[Parameter],
    compound_refs: List[str],
) -> Dict[str, float]:
    """Fill or normalize mass-fraction values so they sum to 1 when possible."""
    return _complete_composition_values(
        param_values,
        param_objects,
        compound_refs,
        Parameters.MASS_FRACTION,
        label="mass fractions",
        sum_tol=MASS_FRACTION_SUM_TOL,
    )


def mass_fractions_to_mole_fractions(
    mass_fractions: Dict[str, float],
    molar_masses: Dict[str, float],
    compound_refs: List[str],
) -> Dict[str, float]:
    """Convert mass fractions to mole fractions using molar masses."""
    if not compound_refs:
        return {}

    if len(compound_refs) == 1:
        return {compound_refs[0]: 1.0}

    moles: List[float] = []
    for compound_id in compound_refs:
        mass_fraction = mass_fractions[compound_id]
        molar_mass = molar_masses[compound_id]
        if molar_mass <= 0.0:
            raise ValueError(
                f"Molar mass must be positive for compound {compound_id!r}, got {molar_mass}"
            )
        moles.append(mass_fraction / molar_mass)

    total_moles = sum(moles)
    if total_moles <= 0.0:
        raise ValueError("Total amount from mass fractions is zero")

    return {
        compound_id: moles[index] / total_moles
        for index, compound_id in enumerate(compound_refs)
    }


def _extract_molality_values(
    param_values: List[ParameterValue],
    param_objects: List[Parameter],
    compound_refs: List[str],
) -> Dict[str, float]:
    solute_ids = _molality_solute_compounds(param_objects, compound_refs)
    if not solute_ids:
        return {}

    param_id_to_compound: Dict[str, str] = {}
    for param in _molality_params(param_objects):
        if not param.parameterID:
            continue
        for compound_id in param.associated_compounds or []:
            if compound_id in solute_ids:
                param_id_to_compound[param.parameterID] = compound_id

    values = {compound_id: 0.0 for compound_id in solute_ids}
    for param_value in param_values:
        if param_value.parameterID not in param_id_to_compound:
            continue
        if param_value.paramValue is None:
            continue
        compound_id = param_id_to_compound[param_value.parameterID]
        values[compound_id] = float(param_value.paramValue)
    return values


def molalities_to_mole_fractions(
    molalities: Dict[str, float],
    molar_masses: Dict[str, float],
    compound_refs: List[str],
    solvent_ids: List[str],
) -> Dict[str, float]:
    """Convert molalities (mol/kg solvent) to mole fractions for one solvent."""
    if not compound_refs:
        return {}

    if len(compound_refs) == 1:
        return {compound_refs[0]: 1.0}

    if len(solvent_ids) != 1:
        raise ValueError(
            f"Molality conversion requires exactly one solvent, got {len(solvent_ids)}"
        )

    solvent_id = solvent_ids[0]
    solvent_molar_mass = molar_masses.get(solvent_id)
    if solvent_molar_mass is None or solvent_molar_mass <= 0.0:
        raise ValueError(f"Missing molar mass for solvent {solvent_id!r}")

    moles = {solvent_id: 1000.0 / solvent_molar_mass}
    for compound_id in compound_refs:
        if compound_id == solvent_id:
            continue
        moles[compound_id] = molalities.get(compound_id, 0.0)

    total_moles = sum(moles[compound_id] for compound_id in compound_refs)
    if total_moles <= 0.0:
        raise ValueError("Total amount from molalities is zero")

    return {
        compound_id: moles[compound_id] / total_moles for compound_id in compound_refs
    }


def _apply_derived_mole_fractions(
    param_values: List[ParameterValue],
    param_objects: List[Parameter],
    derived_mole_fractions: Dict[str, float],
    mole_param_id_to_pv: Dict[str, ParameterValue],
) -> None:
    mole_param_by_compound = _compound_to_param_id(
        param_objects, Parameters.MOLE_FRACTION
    )
    for compound_id, mole_fraction in derived_mole_fractions.items():
        param_id = mole_param_by_compound.get(compound_id)
        if param_id is None:
            continue
        if param_id in mole_param_id_to_pv:
            mole_param_id_to_pv[param_id].paramValue = mole_fraction
        else:
            param_values.append(
                ParameterValue(
                    parameterID=param_id,
                    parameters=Parameters.MOLE_FRACTION,
                    paramValue=mole_fraction,
                    uncertainty=None,
                )
            )


def resolve_molar_masses(
    compounds: List[Compound],
    compound_refs: List[str],
    *,
    fetch_from_pubchem: bool = True,
) -> Dict[str, float]:
    """Resolve molar masses (g/mol) for fluid compounds."""
    by_id = {compound.compoundID: compound for compound in compounds if compound.compoundID}
    resolved: Dict[str, float] = {}

    for compound_id in compound_refs:
        compound = by_id.get(compound_id)
        if compound is None:
            continue

        molar_mass = compound.molar_weigth
        if molar_mass is None or molar_mass <= 0.0:
            if fetch_from_pubchem:
                enriched = enrich_compound_from_pubchem(
                    common_name=compound.commonName,
                    pubchem_cid=compound.pubChemID,
                    standard_inchi=compound.standard_InChI,
                    standard_inchi_key=compound.standard_InChI_key,
                )
                molar_mass = enriched.get("molar_weigth")

        if molar_mass is not None and molar_mass > 0.0:
            resolved[compound_id] = float(molar_mass)

    return resolved


def derive_mole_fractions_from_mass_fractions(
    param_values: List[ParameterValue],
    param_objects: List[Parameter],
    compound_refs: List[str],
    molar_masses: Dict[str, float],
) -> None:
    """Derive mole fractions from completed mass fractions when mole data is missing."""
    if not compound_refs:
        return

    mole_values, mole_param_id_to_pv = _extract_compound_values(
        param_values, param_objects, Parameters.MOLE_FRACTION
    )
    if all(compound_id in mole_values for compound_id in compound_refs):
        return

    mass_values = complete_mass_fraction_values(
        param_values, param_objects, compound_refs
    )
    if not all(compound_id in mass_values for compound_id in compound_refs):
        logger.warning(
            "Cannot derive mole fractions from mass fractions: mass fractions incomplete"
        )
        return

    missing_molar_mass = [
        compound_id
        for compound_id in compound_refs
        if compound_id not in molar_masses
    ]
    if missing_molar_mass:
        logger.warning(
            "Cannot derive mole fractions from mass fractions: missing molar mass for %s",
            missing_molar_mass,
        )
        return

    try:
        derived_mole_fractions = mass_fractions_to_mole_fractions(
            mass_values, molar_masses, compound_refs
        )
    except ValueError as exc:
        logger.warning("Cannot derive mole fractions from mass fractions: %s", exc)
        return

    _apply_derived_mole_fractions(
        param_values,
        param_objects,
        derived_mole_fractions,
        mole_param_id_to_pv,
    )


def derive_mole_fractions_from_molalities(
    param_values: List[ParameterValue],
    param_objects: List[Parameter],
    compound_refs: List[str],
    compounds: List[Compound],
    molar_masses: Dict[str, float],
) -> None:
    """Derive mole fractions from molalities when mole data is missing."""
    if not compound_refs or not _molality_params(param_objects):
        return

    mole_values, mole_param_id_to_pv = _extract_compound_values(
        param_values, param_objects, Parameters.MOLE_FRACTION
    )
    if all(compound_id in mole_values for compound_id in compound_refs):
        return

    molalities = _extract_molality_values(
        param_values, param_objects, compound_refs
    )
    if not molalities:
        logger.warning(
            "Cannot derive mole fractions from molalities: no molality values found"
        )
        return

    solute_ids = set(molalities.keys())
    solvent_ids = _solvent_compound_ids(compound_refs, solute_ids, compounds)
    if not solvent_ids:
        logger.warning(
            "Cannot derive mole fractions from molalities: solvent could not be identified"
        )
        return

    missing_molar_mass = [
        compound_id
        for compound_id in compound_refs
        if compound_id not in molar_masses
    ]
    if missing_molar_mass:
        logger.warning(
            "Cannot derive mole fractions from molalities: missing molar mass for %s",
            missing_molar_mass,
        )
        return

    try:
        derived_mole_fractions = molalities_to_mole_fractions(
            molalities,
            molar_masses,
            compound_refs,
            solvent_ids,
        )
    except ValueError as exc:
        logger.warning("Cannot derive mole fractions from molalities: %s", exc)
        return

    _apply_derived_mole_fractions(
        param_values,
        param_objects,
        derived_mole_fractions,
        mole_param_id_to_pv,
    )


def complete_composition_values(
    param_values: List[ParameterValue],
    param_objects: List[Parameter],
    compound_refs: List[str],
    compounds: List[Compound],
    *,
    fetch_from_pubchem: bool = True,
) -> None:
    """Complete composition, derive mole fractions if needed, then complete mole fractions."""
    molar_masses = resolve_molar_masses(
        compounds, compound_refs, fetch_from_pubchem=fetch_from_pubchem
    )
    derive_mole_fractions_from_molalities(
        param_values,
        param_objects,
        compound_refs,
        compounds,
        molar_masses,
    )
    derive_mole_fractions_from_mass_fractions(
        param_values,
        param_objects,
        compound_refs,
        molar_masses,
    )
    complete_mole_fraction_values(param_values, param_objects, compound_refs)


def _validate_fraction_sum(
    compound_refs: List[str],
    compound_to_value: Dict[str, float],
    label: str,
    sum_tol: float,
) -> None:
    if any(cid not in compound_to_value for cid in compound_refs):
        return
    total = sum(compound_to_value[cid] for cid in compound_refs)
    if abs(total - 1.0) > sum_tol:
        logger.warning(
            "%s still do not sum to 1 after completion (sum=%.6g)",
            label,
            total,
        )


def is_valid_mole_fraction_sum(
    values: List[float], tol: float = MOLE_FRACTION_SUM_TOL
) -> bool:
    """Return True when mole fractions sum to 1 within tolerance."""
    return abs(sum(values) - 1.0) <= tol
