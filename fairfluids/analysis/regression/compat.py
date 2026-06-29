"""Backward-compatible DataFrame wrappers around the regression engine.

These reproduce the public signatures and output columns of the original
``fit_arrhenius`` / ``fit_extended_arrhenius`` / ``fit_vft`` functions that used
to live in :mod:`fairfluids.core.functionalities`, so existing notebooks and
imports keep working. The fitting math now comes from the generated kernels.

Plotting has moved to a later, dedicated step: the ``show_plot`` / ``plot_*`` /
``doi_plot_styles`` arguments are still accepted but are no-ops and emit a
:class:`DeprecationWarning` when plotting is requested.
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from .engine import fit_model
from .result import FitResult, ParameterStack


def _warn_plotting_dropped(show_plot: bool, func_name: str) -> None:
    if show_plot:
        warnings.warn(
            f"{func_name}: plotting has moved out of the fitting functions and is "
            "not performed here anymore. The 'show_plot'/'plot_*' arguments are "
            "ignored. Use the dedicated plotting helpers instead.",
            DeprecationWarning,
            stacklevel=3,
        )


def _nan_if_none(value: Optional[float]) -> float:
    return float("nan") if value is None else float(value)


def _r2(result: FitResult) -> float:
    return _nan_if_none(result.r_squared)


def fit_arrhenius(
    df: pd.DataFrame,
    viscosity_col: str = "viscosity_value",
    temperature_col: str = "temperature",
    doi_col: str = "source_doi",
    molefractions_col: str = "mole_fractions",
    include_water_mole_fraction: bool = False,
    water_col: str = "mole_fraction_water",
    t_range: Optional[Tuple[float, float]] = None,
    show_plot: bool = False,
    plot_figsize: Tuple[float, float] = (8, 5),
    plot_color_by: str = "source_doi",
    plot_cmap: str = "Blues",
    doi_plot_styles: Optional[dict[str, dict[str, str]]] = None,
    min_points: int = 2,
    molefrac_round: int = 6,
    log_base: str = "ln",
    viscosity_uncertainty_col: Optional[str] = None,
) -> pd.DataFrame:
    """Fit the Arrhenius model per ``(DOI, mole-fraction)`` group (legacy DataFrame API)."""
    if log_base != "ln":
        raise ValueError(
            "fit_arrhenius supports only natural logarithm. Please set log_base='ln'."
        )
    _warn_plotting_dropped(show_plot, "fit_arrhenius")

    stack = fit_model(
        "arrhenius",
        df,
        value_col=viscosity_col,
        temperature_col=temperature_col,
        doi_col=doi_col,
        molefractions_col=molefractions_col,
        uncertainty_col=viscosity_uncertainty_col,
        include_water_mole_fraction=include_water_mole_fraction,
        water_col=water_col,
        t_range=t_range,
        min_points=min_points,
        molefrac_round=molefrac_round,
    )

    rows: list[dict[str, Any]] = []
    for res in stack:
        lnas = res.value("lnAs")
        lnas_std = res.std("lnAs")
        ea = res.value("Ea_J_mol")
        ea_std = res.std("Ea_J_mol")
        row: dict[str, Any] = {
            "source_doi": res.group_key.source_doi,
            "mole_fractions": res.group_key.mole_fractions,
            "n_points": res.n_points,
            "lnAs": _nan_if_none(lnas),
            "As": _nan_if_none(res.value("As")),
            "Ea_J_mol": _nan_if_none(ea),
            "Ea_kJ_mol": _nan_if_none(res.value("Ea_kJ_mol")),
            "lnAs_std": _nan_if_none(lnas_std),
            "As_std": _nan_if_none(res.std("As")),
            "Ea_J_mol_std": _nan_if_none(ea_std),
            "Ea_kJ_mol_std": _nan_if_none(res.std("Ea_kJ_mol")),
            "R_squared": _r2(res),
            "slope": _nan_if_none(ea),
            "intercept": _nan_if_none(lnas),
            "slope_std": _nan_if_none(ea_std),
            "intercept_std": _nan_if_none(lnas_std),
            "T_min": _nan_if_none(res.t_min),
            "T_max": _nan_if_none(res.t_max),
        }
        if viscosity_uncertainty_col:
            row["viscosity_uncertainty"] = res.meta.get(
                "value_uncertainty_mean", float("nan")
            )
        if include_water_mole_fraction and "mole_fraction_water" in res.meta:
            row["mole_fraction_water"] = res.meta["mole_fraction_water"]
        rows.append(row)

    return _finalize_dataframe(rows)


def fit_extended_arrhenius(
    df: pd.DataFrame,
    k_col: str = "viscosity_value",
    temperature_col: str = "temperature",
    doi_col: str = "source_doi",
    molefractions_col: str = "mole_fractions",
    include_water_mole_fraction: bool = False,
    water_col: str = "mole_fraction_water",
    t_range: Optional[Tuple[float, float]] = None,
    show_plot: bool = False,
    plot_figsize: Tuple[float, float] = (8, 5),
    plot_color_by: str = "source_doi",
    plot_cmap: str = "Blues",
    min_points: int = 3,
    molefrac_round: int = 6,
) -> pd.DataFrame:
    """Fit the extended Arrhenius model per group (legacy DataFrame API)."""
    _warn_plotting_dropped(show_plot, "fit_extended_arrhenius")

    stack = fit_model(
        "extended_arrhenius",
        df,
        value_col=k_col,
        temperature_col=temperature_col,
        doi_col=doi_col,
        molefractions_col=molefractions_col,
        include_water_mole_fraction=include_water_mole_fraction,
        water_col=water_col,
        t_range=t_range,
        min_points=min_points,
        molefrac_round=molefrac_round,
    )

    rows: list[dict[str, Any]] = []
    for res in stack:
        row: dict[str, Any] = {
            "source_doi": res.group_key.source_doi,
            "mole_fractions": res.group_key.mole_fractions,
            "n_points": res.n_points,
            "B": _nan_if_none(res.value("B")),
            "n": _nan_if_none(res.value("n")),
            "Ea_J_mol": _nan_if_none(res.value("Ea_J_mol")),
            "Ea_kJ_mol": _nan_if_none(res.value("Ea_kJ_mol")),
            "R_squared": _r2(res),
            "lnB": _nan_if_none(res.value("lnB")),
            "T_min": _nan_if_none(res.t_min),
            "T_max": _nan_if_none(res.t_max),
        }
        if include_water_mole_fraction and "mole_fraction_water" in res.meta:
            row["mole_fraction_water"] = res.meta["mole_fraction_water"]
        rows.append(row)

    return _finalize_dataframe(rows)


def fit_vft(
    df: pd.DataFrame,
    viscosity_col: str = "viscosity_value",
    temperature_col: str = "temperature",
    doi_col: str = "source_doi",
    molefractions_col: str = "mole_fractions",
    include_water_mole_fraction: bool = False,
    water_col: str = "mole_fraction_water",
    t_range: Optional[Tuple[float, float]] = None,
    show_plot: bool = False,
    plot_figsize: Tuple[float, float] = (8, 5),
    plot_color_by: str = "source_doi",
    plot_cmap: str = "Blues",
    doi_plot_styles: Optional[dict[str, dict[str, str]]] = None,
    min_points: int = 4,
    molefrac_round: int = 6,
    initial_guesses: Optional[Dict[str, float]] = None,
    viscosity_uncertainty_col: Optional[str] = None,
) -> pd.DataFrame:
    """Fit the 3-parameter VFT model per group (legacy DataFrame API)."""
    _warn_plotting_dropped(show_plot, "fit_vft")
    if initial_guesses is not None:
        warnings.warn(
            "fit_vft: 'initial_guesses' is not supported by the refactored engine "
            "and is ignored; the model uses data-driven default guesses.",
            DeprecationWarning,
            stacklevel=2,
        )

    stack = fit_model(
        "vft",
        df,
        value_col=viscosity_col,
        temperature_col=temperature_col,
        doi_col=doi_col,
        molefractions_col=molefractions_col,
        uncertainty_col=viscosity_uncertainty_col,
        include_water_mole_fraction=include_water_mole_fraction,
        water_col=water_col,
        t_range=t_range,
        min_points=min_points,
        molefrac_round=molefrac_round,
    )

    rows: list[dict[str, Any]] = []
    for res in stack:
        row: dict[str, Any] = {
            "source_doi": res.group_key.source_doi,
            "mole_fractions": res.group_key.mole_fractions,
            "n_points": res.n_points,
            "eta0": _nan_if_none(res.value("eta0")),
            "ln_eta0": _nan_if_none(res.value("ln_eta0")),
            "B": _nan_if_none(res.value("B")),
            "T0": _nan_if_none(res.value("T0")),
            "eta0_std": _nan_if_none(res.std("eta0")),
            "ln_eta0_std": _nan_if_none(res.std("ln_eta0")),
            "B_std": _nan_if_none(res.std("B")),
            "T0_std": _nan_if_none(res.std("T0")),
            "R_squared": _r2(res),
            "T_min": _nan_if_none(res.t_min),
            "T_max": _nan_if_none(res.t_max),
        }
        if viscosity_uncertainty_col:
            row["viscosity_uncertainty"] = res.meta.get(
                "value_uncertainty_mean", float("nan")
            )
        if include_water_mole_fraction and "mole_fraction_water" in res.meta:
            row["mole_fraction_water"] = res.meta["mole_fraction_water"]
        rows.append(row)

    return _finalize_dataframe(rows)


def _finalize_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    result_df = pd.DataFrame(rows)
    if not result_df.empty:
        result_df = result_df.sort_values(
            by=["source_doi", "mole_fractions"]
        ).reset_index(drop=True)
    return result_df


__all__ = ["fit_arrhenius", "fit_extended_arrhenius", "fit_vft"]
