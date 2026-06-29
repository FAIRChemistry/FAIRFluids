"""Generic, model-agnostic fitting engine for regression models.

The engine handles everything that is *not* specific to a single model:
data cleaning, grouping by ``(source_doi, mole_fractions)``, optional temperature
windowing, water mole-fraction derivation and goodness-of-fit bookkeeping. The
actual mathematics live in the kernels synthesised from the symbolic store by
:mod:`fairfluids.analysis.regression.bridge`, which the engine looks up through
the registry in :mod:`fairfluids.analysis.regression.spec`.

The result is always a :class:`~fairfluids.analysis.regression.result.ParameterStack`
so heterogeneous models contribute to one universal "derived quantities" object.
"""

from __future__ import annotations

from collections.abc import Mapping as MappingABC, Sequence as SequenceABC
from typing import Any, Optional, Union

import numpy as np
import pandas as pd

from fairfluids.core.functionalities import extract_property_dataframe
from fairfluids.core.lib import FAIRFluidsDocument

from .result import FitResult, FittedParameter, GroupKey, ParameterStack
from .spec import RegressionModelSpec, get_model


def _normalize_molefractions(mf: Any, *, molefrac_round: int) -> Optional[tuple[float, ...]]:
    """Round a sequence of mole fractions into a stable, hashable grouping key."""
    if isinstance(mf, (list, tuple, np.ndarray)):
        try:
            return tuple(round(float(x), molefrac_round) for x in mf)
        except (TypeError, ValueError):
            return None
    return None


def _derive_water_fraction(
    row: pd.Series, *, molefractions_col: str, fluid_compounds_col: str
) -> float:
    """Water mole fraction for a row, identified via its fluid-compound labels."""
    fracs = row.get(molefractions_col)
    comps = row.get(fluid_compounds_col)
    if not isinstance(fracs, (list, tuple, np.ndarray)):
        return float("nan")
    if isinstance(comps, (list, tuple)):
        for idx, comp in enumerate(comps):
            if str(comp).strip().lower() in {"water", "h2o"}:
                return float(fracs[idx]) if idx < len(fracs) else float("nan")
    return float("nan")


def _transform_observation(values: np.ndarray, y_transform: str) -> np.ndarray:
    if y_transform == "log":
        return np.log(values)
    if y_transform == "identity":
        return values
    raise ValueError(f"Unsupported y_transform {y_transform!r}.")


def _sigma_on_transformed_scale(
    raw_values: np.ndarray, raw_uncertainty: np.ndarray, y_transform: str
) -> Optional[np.ndarray]:
    """Propagate the measurement uncertainty onto the fitted (transformed) scale.

    For ``log`` observations, ``d ln(v) = dv / v``; for ``identity`` the
    uncertainty passes through unchanged.
    """
    if y_transform == "log":
        with np.errstate(divide="ignore", invalid="ignore"):
            sigma = np.divide(
                raw_uncertainty,
                raw_values,
                out=np.full_like(raw_uncertainty, np.nan, dtype=float),
                where=raw_values != 0,
            )
        return sigma
    if y_transform == "identity":
        return raw_uncertainty
    raise ValueError(f"Unsupported y_transform {y_transform!r}.")


def fit_model(
    model_name: str,
    df: pd.DataFrame,
    *,
    value_col: str,
    temperature_col: str = "temperature",
    doi_col: str = "source_doi",
    molefractions_col: str = "mole_fractions",
    fluid_compounds_col: str = "fluid_compounds",
    uncertainty_col: Optional[str] = None,
    measurement_id_col: Optional[str] = None,
    include_water_mole_fraction: bool = False,
    water_col: str = "mole_fraction_water",
    t_range: Optional[tuple[float, float]] = None,
    min_points: Optional[int] = None,
    molefrac_round: int = 6,
) -> ParameterStack:
    """Fit a registered model per ``(source_doi, mole_fractions)`` group.

    Args:
        model_name: Registered model name (see :func:`spec.list_models`).
        df: Input DataFrame with at least ``value_col``, ``temperature_col``,
            ``doi_col`` and ``molefractions_col``.
        value_col: Column holding the (positive) property values to fit.
        temperature_col: Column with absolute temperature in K (must be > 0).
        doi_col: First-level grouping column.
        molefractions_col: Column with sequence-like mole fractions.
        fluid_compounds_col: Column with parallel-indexed compound labels (used for
            ``GroupKey.fluid_compounds`` and water derivation when present).
        uncertainty_col: Optional column with per-point property uncertainty.
        measurement_id_col: Optional column with measurement identifiers (provenance).
        include_water_mole_fraction: Derive a water mole fraction per group into
            ``FitResult.meta['mole_fraction_water']`` when possible.
        water_col: Pre-existing water mole-fraction column, if any.
        t_range: Optional inclusive ``(T_min, T_max)`` window in Kelvin.
        min_points: Minimum points per group; defaults to the model's ``min_points``.
        molefrac_round: Rounding for stable mole-fraction grouping.

    Returns:
        A :class:`ParameterStack` with one :class:`FitResult` per fitted group.
    """
    spec, kernel = get_model(model_name)
    effective_min_points = spec.min_points if min_points is None else min_points

    required = [value_col, temperature_col, doi_col, molefractions_col]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns for fit_model({model_name!r}): {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    work = df.copy()
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    work[temperature_col] = pd.to_numeric(work[temperature_col], errors="coerce")
    if uncertainty_col and uncertainty_col in work.columns:
        work[uncertainty_col] = pd.to_numeric(work[uncertainty_col], errors="coerce")

    work = work[
        work[value_col].notna()
        & work[temperature_col].notna()
        & work[doi_col].notna()
        & (work[value_col] > 0)
        & (work[temperature_col] > 0)
    ].copy()

    if t_range is not None:
        if not isinstance(t_range, (list, tuple)) or len(t_range) != 2:
            raise ValueError("t_range must be a tuple/list with two values: (T_min, T_max).")
        t_min, t_max = float(t_range[0]), float(t_range[1])
        if t_min > t_max:
            raise ValueError(f"Invalid t_range: T_min ({t_min}) must be <= T_max ({t_max}).")
        work = work[work[temperature_col].between(t_min, t_max, inclusive="both")].copy()

    if (
        include_water_mole_fraction
        and water_col not in work.columns
        and fluid_compounds_col in work.columns
    ):
        work[water_col] = work.apply(
            _derive_water_fraction,
            axis=1,
            molefractions_col=molefractions_col,
            fluid_compounds_col=fluid_compounds_col,
        )

    work["_mf_key"] = work[molefractions_col].apply(
        _normalize_molefractions, molefrac_round=molefrac_round
    )
    work = work[work["_mf_key"].notna()].copy()

    results: list[FitResult] = []
    for (doi, mf_key), group in work.groupby([doi_col, "_mf_key"], dropna=False):
        if len(group) < effective_min_points:
            continue

        temperatures = group[temperature_col].to_numpy(dtype=float)
        raw_values = group[value_col].to_numpy(dtype=float)
        y = _transform_observation(raw_values, spec.y_transform)

        sigma: Optional[np.ndarray] = None
        value_uncertainty_mean: Optional[float] = None
        if uncertainty_col and uncertainty_col in group.columns:
            raw_unc = group[uncertainty_col].to_numpy(dtype=float)
            sigma = _sigma_on_transformed_scale(raw_values, raw_unc, spec.y_transform)
            finite_unc = raw_unc[np.isfinite(raw_unc)]
            if finite_unc.size:
                value_uncertainty_mean = float(np.mean(finite_unc))

        raw_fit = kernel(temperatures, y, sigma)
        if not raw_fit.success:
            continue

        result = _build_fit_result(
            spec=spec,
            doi=doi,
            mf_key=mf_key,
            group=group,
            raw_fit=raw_fit,
            temperatures=temperatures,
            temperature_col=temperature_col,
            fluid_compounds_col=fluid_compounds_col,
            measurement_id_col=measurement_id_col,
            include_water_mole_fraction=include_water_mole_fraction,
            water_col=water_col,
            value_uncertainty_mean=value_uncertainty_mean,
        )
        results.append(result)

    results.sort(
        key=lambda r: (str(r.group_key.source_doi), r.group_key.mole_fractions)
    )
    return ParameterStack(results=results)


def _build_fit_result(
    *,
    spec: RegressionModelSpec,
    doi: Any,
    mf_key: tuple[float, ...],
    group: pd.DataFrame,
    raw_fit: Any,
    temperatures: np.ndarray,
    temperature_col: str,
    fluid_compounds_col: str,
    measurement_id_col: Optional[str],
    include_water_mole_fraction: bool,
    water_col: str,
    value_uncertainty_mean: Optional[float],
) -> FitResult:
    """Assemble a :class:`FitResult` from a kernel's :class:`RawFit`."""
    fluid_compounds: tuple[str, ...] = ()
    if fluid_compounds_col in group.columns:
        first = group[fluid_compounds_col].iloc[0]
        if isinstance(first, (list, tuple, np.ndarray)):
            fluid_compounds = tuple(str(c) for c in first)

    group_key = GroupKey(
        source_doi=None if doi is None else str(doi),
        fluid_compounds=fluid_compounds,
        mole_fractions=tuple(mf_key),
    )

    parameters: dict[str, FittedParameter] = {}
    for pname in spec.param_names:
        if pname not in raw_fit.params:
            continue
        value, std = raw_fit.params[pname]
        parameters[pname] = FittedParameter(
            name=pname,
            value=float(value),
            std=None if std is None else float(std),
            unit=spec.unit(pname),
        )

    measurement_ids: tuple[str, ...] = ()
    if measurement_id_col and measurement_id_col in group.columns:
        measurement_ids = tuple(
            str(m) for m in group[measurement_id_col].tolist() if m is not None
        )

    meta: dict[str, Any] = {}
    if value_uncertainty_mean is not None:
        meta["value_uncertainty_mean"] = value_uncertainty_mean
    if include_water_mole_fraction and water_col in group.columns:
        water_values = pd.to_numeric(group[water_col], errors="coerce").dropna()
        meta["mole_fraction_water"] = (
            float(water_values.iloc[0]) if not water_values.empty else float("nan")
        )

    return FitResult(
        model_name=spec.name,
        group_key=group_key,
        parameters=parameters,
        n_points=int(len(group)),
        r_squared=raw_fit.r_squared,
        t_min=float(np.min(temperatures)),
        t_max=float(np.max(temperatures)),
        measurement_ids=measurement_ids,
        meta=meta,
    )


def fit_documents(
    model_name: str,
    documents: Union[
        FAIRFluidsDocument,
        SequenceABC[FAIRFluidsDocument],
        MappingABC[str, FAIRFluidsDocument],
    ],
    *,
    property_type: Optional[str] = None,
    t_range: Optional[tuple[float, float]] = None,
    min_points: Optional[int] = None,
    include_water_mole_fraction: bool = False,
    molefrac_round: int = 6,
    extract_kwargs: Optional[dict[str, Any]] = None,
) -> ParameterStack:
    """Fit a model directly from one or more ``FAIRFluidsDocument`` instances.

    Uses :func:`extract_property_dataframe` to build the working frame, then
    delegates to :func:`fit_model`. The property defaults to the model's
    ``observation`` (e.g. ``"viscosity"``).
    """
    spec = get_model(model_name)[0]
    prop = property_type or spec.observation
    df = extract_property_dataframe(documents, property_type=prop, **(extract_kwargs or {}))
    if df.empty:
        return ParameterStack(results=[])
    return fit_model(
        model_name,
        df,
        value_col=f"{prop}_value",
        uncertainty_col=f"{prop}_uncertainty",
        t_range=t_range,
        min_points=min_points,
        include_water_mole_fraction=include_water_mole_fraction,
        molefrac_round=molefrac_round,
    )


__all__ = ["fit_model", "fit_documents"]
