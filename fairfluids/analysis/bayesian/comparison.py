"""Model comparison and posterior summaries.

Two public entry points:

- :func:`compare_models` — runs ``az.compare`` per group, augments with
  per-group ``LOO`` and Pareto-k diagnostics, and returns three DataFrames
  (per group, per (group, model), and a global ranking).
- :func:`posterior_summary` — builds a tidy DataFrame with per-parameter
  median + asymmetric 90 % credible interval for every fitted model and group.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterable

import numpy as np
import pandas as pd

from .inference import BayesianFit

if TYPE_CHECKING:
    import arviz as az


@dataclass
class ModelComparison:
    """Container with the three model-comparison tables produced by :func:`compare_models`."""

    per_group_best: pd.DataFrame
    per_group_model: pd.DataFrame
    global_ranking: pd.DataFrame


def _pareto_k(loo: "az.ELPDData") -> np.ndarray:
    val = getattr(loo, "pareto_k", None)
    if val is None:
        return np.array([])
    arr = getattr(val, "values", val)
    return np.asarray(arr).reshape(-1)


def _loo_elpd(loo: "az.ELPDData") -> float:
    """Return the ELPD value from an ``ELPDData`` regardless of arviz major version."""
    for attr in ("elpd_loo", "elpd"):
        v = getattr(loo, attr, None)
        if v is not None:
            return float(v)
    raise AttributeError("ELPDData has neither 'elpd_loo' nor 'elpd'.")


def _loo_p(loo: "az.ELPDData") -> float:
    for attr in ("p_loo", "p"):
        v = getattr(loo, attr, None)
        if v is not None:
            return float(v)
    return float("nan")


def compare_models(
    fit: BayesianFit,
    *,
    pareto_k_thresholds: tuple[float, ...] = (0.7, 1.0),
    method: str = "stacking",
) -> ModelComparison:
    """Per-group ArviZ comparison plus aggregated diagnostics.

    Args:
        fit: A :class:`BayesianFit` produced by :func:`fit_groups`.
        pareto_k_thresholds: Thresholds for which the number of points with
            ``pareto_k > threshold`` will be added as columns.
        method: Weighting method forwarded to :func:`arviz.compare`
            (``"stacking"``, ``"BB-pseudo-BMA"`` or ``"pseudo-BMA"``).
    """
    import arviz as az

    per_group_best_rows: list[dict[str, Any]] = []
    per_group_model_rows: list[dict[str, Any]] = []

    for gid in fit.group_ids:
        model_to_idata: dict[str, "az.InferenceData"] = {}
        loo_per_model: dict[str, "az.ELPDData"] = {}
        for m_name in fit.model_names:
            try:
                gfit = fit.get(m_name, gid)
            except KeyError:
                continue
            model_to_idata[m_name] = gfit.inference_data
            loo_per_model[m_name] = az.loo(gfit.inference_data, pointwise=True)

        if not model_to_idata:
            continue

        comp_df = az.compare(model_to_idata, method=method)
        best_model = str(comp_df.index[0])
        group_label = fit.get(next(iter(model_to_idata)), gid).group.group_label
        elpd_col = "elpd" if "elpd" in comp_df.columns else "elpd_loo"
        per_group_best_rows.append(
            {
                "group_id": gid,
                "group_label": group_label,
                "best_model": best_model,
                "best_elpd": float(comp_df.iloc[0][elpd_col]),
            }
        )

        for m_name in model_to_idata:
            loo = loo_per_model[m_name]
            k = _pareto_k(loo)
            comp_row = comp_df.loc[m_name] if m_name in comp_df.index else None
            row: dict[str, Any] = {
                "group_id": gid,
                "group_label": group_label,
                "model": m_name,
                "elpd": _loo_elpd(loo),
                "se_elpd": float(getattr(loo, "se", float("nan"))),
                "p_loo": _loo_p(loo),
                "warning": bool(getattr(loo, "warning", False)),
                "rank": int(comp_df.index.tolist().index(m_name)),
                "weight": float(comp_row["weight"]) if comp_row is not None and "weight" in comp_df.columns else float("nan"),
            }
            for thr in pareto_k_thresholds:
                row[f"n_pareto_k_gt_{thr:.1f}"] = int((k > thr).sum()) if k.size else 0
            per_group_model_rows.append(row)

    per_group_best = pd.DataFrame(per_group_best_rows)
    per_group_model = pd.DataFrame(per_group_model_rows)

    if not per_group_model.empty:
        global_ranking = (
            per_group_model.groupby("model", as_index=False)
            .agg(
                mean_elpd=("elpd", "mean"),
                sum_elpd=("elpd", "sum"),
                n_groups=("elpd", "size"),
                n_warnings=("warning", "sum"),
                weight=("weight", "mean"),
            )
            .sort_values("sum_elpd", ascending=False)
            .reset_index(drop=True)
        )
    else:
        global_ranking = pd.DataFrame(
            columns=["model", "mean_elpd", "sum_elpd", "n_groups", "n_warnings", "weight"]
        )

    return ModelComparison(
        per_group_best=per_group_best,
        per_group_model=per_group_model,
        global_ranking=global_ranking,
    )


def _summarize(samples: np.ndarray) -> dict[str, float]:
    s = np.asarray(samples).reshape(-1)
    median = float(np.quantile(s, 0.5))
    q05, q95 = np.quantile(s, [0.05, 0.95])
    return {
        "median": median,
        "mean": float(np.mean(s)),
        "q05": float(q05),
        "q95": float(q95),
        "err_minus_90": float(median - q05),
        "err_plus_90": float(q95 - median),
        "std": float(np.std(s)),
    }


_NON_PARAMETER_SITES = frozenset({"mu", "obs"})


def _posterior_parameters(model_name: str, sample_keys: Iterable[str]) -> list[str]:
    """Keep only inferential scalars (``param_names`` + ``model_sigma``)."""
    from .models import ModelRegistry

    allowed = set(ModelRegistry.get(model_name).param_names) | {"model_sigma"}
    return [name for name in sample_keys if name in allowed and name not in _NON_PARAMETER_SITES]


def posterior_summary(fit: BayesianFit) -> pd.DataFrame:
    """Return a tidy DataFrame ``[model, group_label, parameter, median, q05, q95, ...]``.

    Useful as input for ``plot_parameter_vs_feature`` and for tabular reports.
    """
    rows: list[dict[str, Any]] = []
    for (model_name, group_id), gfit in fit.fits.items():
        samples = gfit.samples()
        for param in _posterior_parameters(model_name, samples):
            arr = samples[param]
            stats = _summarize(arr)
            row: dict[str, Any] = {
                "model": model_name,
                "group_id": group_id,
                "group_label": gfit.group.group_label,
                "parameter": param,
                "n_points": gfit.group.n_points,
                **stats,
            }
            for col, val in zip(("group_by_" + str(i) for i in range(len(group_id))), group_id):
                row[col] = val
            for col, val in gfit.group.metadata.get("group_by", {}).items():
                row[col] = val
            rows.append(row)
    return pd.DataFrame(rows)


__all__ = ["ModelComparison", "compare_models", "posterior_summary"]
