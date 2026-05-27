"""Matplotlib plotting helpers for the Bayesian analysis subpackage.

All plot functions return ``(fig, ax)`` (or ``(fig, axes)`` for grids) without
calling ``plt.show()``, matching the convention used by
:mod:`fairfluids.visualization.core_plots`. DOI styling is delegated to
:func:`fairfluids.core.functionalities._get_doi_plot_style` and marker cycles
come from :func:`fairfluids.visualization.core_plots.get_marker_styles` so the
look is consistent with the rest of the package.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, Mapping

import numpy as np
import pandas as pd

from fairfluids.core.functionalities import _get_doi_plot_style, _string_to_hex_color
from fairfluids.visualization.core_plots import get_marker_styles

from .comparison import ModelComparison, posterior_summary
from .data import BayesianDataset, BayesianGroup
from .inference import BayesianFit
from .priors import sample_prior

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.figure import Figure

    from .models import BayesianModel


_WATER_CMAP_STOPS: tuple[tuple[float, str], ...] = (
    (0.0, "#e0e5ec"),
    (0.15, "#c3ccd8"),
    (0.40, "#97abc6"),
    (0.70, "#5f8fc6"),
    (1.0, "#1f5aa6"),
)


def _composition_cmap(n: int) -> "LinearSegmentedColormap":
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list("ff_composition", list(_WATER_CMAP_STOPS), N=max(2, n))


def _doi_marker(doi: str, doi_order: list[str]) -> str:
    markers = get_marker_styles()
    if doi in doi_order:
        return markers[doi_order.index(doi) % len(markers)]
    return markers[abs(hash(doi)) % len(markers)]


def _doi_color(doi: str, doi_styles: Mapping[str, dict[str, str]] | None = None) -> str:
    return _get_doi_plot_style(doi, custom_styles=dict(doi_styles or {}))["color"]


def _resolve_doi(group: BayesianGroup, doi_field: str = "source_doi") -> str:
    meta = group.metadata
    if doi_field in meta:
        return str(meta[doi_field])
    group_by = meta.get("group_by", {})
    if doi_field in group_by:
        return str(group_by[doi_field])
    return group.group_label


def _resolve_composition(
    group: BayesianGroup, composition_field: str | None
) -> float | None:
    if composition_field is None:
        return None
    meta = group.metadata
    if composition_field in meta and meta[composition_field] is not None:
        try:
            return float(meta[composition_field])
        except (TypeError, ValueError):
            return None
    group_by = meta.get("group_by", {})
    val = group_by.get(composition_field)
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _posterior_predictive_bands(
    model: "BayesianModel",
    fit: BayesianFit,
    group: BayesianGroup,
    *,
    feature: str,
    n_grid: int = 120,
    quantiles: tuple[float, float] = (0.05, 0.95),
    seed: int = 0,
) -> dict[str, np.ndarray]:
    """Predict the model's observation distribution on a dense feature grid."""
    import jax.numpy as jnp
    import jax.random as random
    from numpyro.infer import Predictive

    gfit = fit.get(model.name, group.group_id)
    f_arr = group.features[feature]
    f_grid = np.linspace(float(np.min(f_arr)), float(np.max(f_arr)), n_grid)

    features_jax: dict[str, Any] = {}
    for fname in model.feature_names:
        if fname == feature:
            features_jax[fname] = jnp.asarray(f_grid)
        else:
            features_jax[fname] = jnp.asarray(group.features[fname])

    predictive = Predictive(model.numpyro_model, gfit.mcmc.get_samples())
    key = random.fold_in(random.PRNGKey(seed), abs(hash(group.group_id)) % (2**31))
    samples = predictive(
        key,
        features=features_jax,
        observation=None,
        observation_uncertainty=None,
        preset_name=gfit.preset,
    )
    obs = np.asarray(samples["obs"])
    return {
        "grid": f_grid,
        "mean": obs.mean(axis=0),
        "lo": np.quantile(obs, quantiles[0], axis=0),
        "hi": np.quantile(obs, quantiles[1], axis=0),
    }


def plot_posterior_predictive(
    fit: BayesianFit,
    model: "BayesianModel",
    *,
    group_id: Any = None,
    feature: str = "temperature",
    composition_field: str | None = "mole_fraction_water",
    doi_field: str = "source_doi",
    inverse_temperature_axis: bool = True,
    figsize: tuple[float, float] = (10.0, 7.0),
    title: str | None = None,
    doi_styles: Mapping[str, dict[str, str]] | None = None,
) -> tuple["Figure", "Axes"]:
    """Posterior predictive plot in log-property vs. ``1/(R*T)`` space (default).

    Marker per DOI, color per composition value (using the same blue gradient as
    the legacy notebook). Set ``inverse_temperature_axis=False`` to plot directly
    against the feature.

    ``group_id`` accepts the same flexible selectors as :func:`plot_posterior`
    (``None`` = all fitted groups, ``int`` index, label substring, metadata
    dict, raw ``group_id`` tuple, or :class:`BayesianGroup`).
    """
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    from .models_builtin import R_GAS

    if feature not in model.feature_names:
        raise KeyError(
            f"feature={feature!r} not in model {model.name!r} features {model.feature_names}."
        )

    fig, ax = plt.subplots(figsize=figsize)

    groups = [g for g in fit.group_ids if (model.name, g) in fit.fits]
    if not groups:
        raise ValueError(f"No fits found for model {model.name!r}.")

    if group_id is not None:
        groups = [_resolve_group_id(fit, model.name, group_id)]

    bayesian_groups = [fit.get(model.name, gid).group for gid in groups]
    doi_order = list(dict.fromkeys(_resolve_doi(g, doi_field) for g in bayesian_groups))
    compositions = sorted(
        {
            round(_resolve_composition(g, composition_field) or 0.0, 4)
            for g in bayesian_groups
            if _resolve_composition(g, composition_field) is not None
        }
    )
    cmap = _composition_cmap(len(compositions) or 2)
    comp_to_idx = {c: i for i, c in enumerate(compositions)}

    for group in bayesian_groups:
        doi = _resolve_doi(group, doi_field)
        comp = _resolve_composition(group, composition_field)
        comp_round = round(comp, 4) if comp is not None else None
        if comp_round is not None and comp_round in comp_to_idx and len(compositions) > 1:
            color = cmap(comp_to_idx[comp_round] / max(1, len(compositions) - 1))
        else:
            color = _doi_color(doi, doi_styles)
        marker = _doi_marker(doi, doi_order)

        bands = _posterior_predictive_bands(model, fit, group, feature=feature)
        f_grid = bands["grid"]
        f_obs = group.features[feature]
        if inverse_temperature_axis and feature == "temperature":
            x_grid = 1000.0 / (R_GAS * f_grid)
            x_obs = 1000.0 / (R_GAS * f_obs)
            xlabel = r"$(RT)^{-1}$ / mol kJ$^{-1}$"
        else:
            x_grid = f_grid
            x_obs = f_obs
            xlabel = feature

        ax.plot(x_grid, bands["mean"], color=color, lw=2, alpha=0.9, zorder=1)
        ax.fill_between(x_grid, bands["lo"], bands["hi"], color=color, alpha=0.2, zorder=1)
        ax.scatter(
            x_obs,
            group.observation,
            color=color,
            marker=marker,
            s=55,
            edgecolor="black",
            zorder=2,
            alpha=0.9,
        )

    ax.set_xlabel(xlabel, fontsize=14)
    if model.log_observation:
        ax.set_ylabel(r"$\ln(\eta\,/\,\mathrm{Pa\cdot s})$", fontsize=14)
    else:
        ax.set_ylabel("observation", fontsize=14)
    ax.set_title(title or f"{model.name} posterior predictive", fontsize=15)

    legend_handles: list[Line2D] = []
    if compositions:
        for i, c in enumerate(compositions):
            color = cmap(i / max(1, len(compositions) - 1))
            legend_handles.append(
                Line2D(
                    [0],
                    [0],
                    marker="o",
                    color="w",
                    markerfacecolor=color,
                    markeredgecolor="k",
                    markersize=10,
                    label=f"{composition_field}={c:.3f}",
                )
            )
    for doi in doi_order:
        legend_handles.append(
            Line2D(
                [0],
                [0],
                marker=_doi_marker(doi, doi_order),
                color="black",
                linestyle="None",
                markersize=10,
                label=doi,
            )
        )
    if legend_handles:
        ax.legend(
            handles=legend_handles,
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            fontsize=10,
            frameon=True,
        )
    fig.tight_layout()
    return fig, ax


def plot_prior_predictive(
    model: "BayesianModel",
    group: BayesianGroup,
    *,
    preset: str = "balanced",
    feature: str = "temperature",
    n_samples: int = 2000,
    quantiles: tuple[float, ...] = (0.05, 0.5, 0.95),
    figsize: tuple[float, float] = (8.0, 5.0),
) -> tuple["Figure", "Axes"]:
    """Plot prior predictive median + interval bands on the group's feature range."""
    import jax.numpy as jnp
    import jax.random as random
    import matplotlib.pyplot as plt
    from numpyro.infer import Predictive

    f_arr = group.features[feature]
    grid = np.linspace(float(np.min(f_arr)), float(np.max(f_arr)), 200)

    features_jax: dict[str, Any] = {}
    for fname in model.feature_names:
        features_jax[fname] = jnp.asarray(grid if fname == feature else group.features[fname])

    predictive = Predictive(model.numpyro_model, num_samples=n_samples)
    key = random.PRNGKey(0)
    samples = predictive(
        key,
        features=features_jax,
        observation=None,
        observation_uncertainty=None,
        preset_name=preset,
    )
    obs = np.asarray(samples["obs"])
    q_arrays = {q: np.quantile(obs, q, axis=0) for q in quantiles}

    fig, ax = plt.subplots(figsize=figsize)
    median = q_arrays.get(0.5, np.quantile(obs, 0.5, axis=0))
    ax.plot(grid, median, color="#1f5aa6", lw=2, label="prior median")
    lo = min(quantiles)
    hi = max(quantiles)
    if lo != 0.5 and hi != 0.5:
        ax.fill_between(
            grid,
            q_arrays[lo],
            q_arrays[hi],
            color="#1f5aa6",
            alpha=0.2,
            label=f"prior {int(lo*100)}-{int(hi*100)}%",
        )
    ax.scatter(f_arr, group.observation, color="black", s=40, marker="o", label="observed")
    ax.set_xlabel(feature, fontsize=13)
    ax.set_ylabel("ln(observation)" if model.log_observation else "observation", fontsize=13)
    ax.set_title(f"{model.name} prior predictive ({preset}) — {group.group_label}", fontsize=12)
    ax.legend(loc="best", fontsize=10)
    fig.tight_layout()
    return fig, ax


def plot_parameter_vs_feature(
    fit: BayesianFit,
    model_name: str,
    *,
    parameter: str,
    feature: str,
    doi_field: str = "source_doi",
    system_field: str = "system_name",
    figsize: tuple[float, float] = (8.0, 5.0),
    xlabel: str | None = None,
    ylabel: str | None = None,
    title: str | None = None,
) -> tuple["Figure", "Axes"]:
    """Posterior median + 90 % CI of one parameter against a group-level feature.

    Useful for inspecting how a fitted parameter varies with composition or another
    grouping variable.
    """
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    summary = posterior_summary(fit)
    sub = summary[(summary["model"] == model_name) & (summary["parameter"] == parameter)].copy()
    if sub.empty:
        raise ValueError(
            f"No posterior samples for model={model_name!r}, parameter={parameter!r}."
        )

    feature_values: list[float] = []
    for gid in sub["group_id"]:
        gfit = fit.get(model_name, gid)
        val = _resolve_composition(gfit.group, feature)
        feature_values.append(val if val is not None else float("nan"))
    sub["__feature"] = feature_values

    dois: list[str] = []
    for gid in sub["group_id"]:
        dois.append(_resolve_doi(fit.get(model_name, gid).group, doi_field))
    sub["__doi"] = dois

    systems: list[str] = []
    for gid in sub["group_id"]:
        meta = fit.get(model_name, gid).group.metadata
        sys_val = meta.get(system_field)
        systems.append(str(sys_val) if sys_val is not None else "(unknown)")
    sub["__system"] = systems

    unique_systems = list(dict.fromkeys(sub["__system"]))
    sys_color = {s: _string_to_hex_color(s) for s in unique_systems}
    doi_order = list(dict.fromkeys(sub["__doi"]))

    fig, ax = plt.subplots(figsize=figsize)
    for _, row in sub.iterrows():
        ax.errorbar(
            row["__feature"],
            row["median"],
            yerr=[[row["err_minus_90"]], [row["err_plus_90"]]],
            fmt=_doi_marker(row["__doi"], doi_order),
            color=sys_color[row["__system"]],
            ecolor="gray",
            capsize=4,
            markersize=8,
            markeredgecolor="black",
            markeredgewidth=0.6,
            linestyle="none",
            alpha=0.9,
        )

    ax.set_xlabel(xlabel or feature, fontsize=13)
    ax.set_ylabel(ylabel or parameter, fontsize=13)
    ax.set_title(title or f"{model_name}: {parameter} vs {feature}", fontsize=13)

    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=sys_color[s],
            markeredgecolor="k",
            markersize=9,
            label=s,
        )
        for s in unique_systems
    ]
    if handles:
        ax.legend(
            handles=handles,
            title="System",
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            fontsize=9,
            frameon=True,
        )
    fig.tight_layout()
    return fig, ax


def plot_residuals_and_pareto_k(
    fit: BayesianFit,
    *,
    feature: str = "temperature",
    doi_field: str = "source_doi",
    figsize: tuple[float, float] = (12.0, 4.0),
) -> tuple["Figure", "np.ndarray"]:
    """One row per model: residual scatter (left) + Pareto-k scatter (right)."""
    import arviz as az
    import matplotlib.pyplot as plt

    model_names = list(fit.model_names)
    fig, axes = plt.subplots(
        len(model_names), 2, figsize=(figsize[0], figsize[1] * len(model_names)), squeeze=False
    )

    doi_order: list[str] = []
    for (m, gid), gfit in fit.fits.items():
        d = _resolve_doi(gfit.group, doi_field)
        if d not in doi_order:
            doi_order.append(d)

    for row, m_name in enumerate(model_names):
        ax_res, ax_k = axes[row]
        for gid in fit.group_ids:
            if (m_name, gid) not in fit.fits:
                continue
            gfit = fit.get(m_name, gid)
            doi = _resolve_doi(gfit.group, doi_field)
            color = _doi_color(doi)
            marker = _doi_marker(doi, doi_order)
            loo = az.loo(gfit.inference_data, pointwise=True)
            k = _pareto_k_safe(loo)
            samples = gfit.mcmc.get_samples()
            # Reconstruct mean prediction at observed features
            import jax.numpy as jnp
            from numpyro.infer import Predictive
            import jax.random as random

            features_jax = {f: jnp.asarray(gfit.group.features[f]) for f in gfit.group.features}
            pred = Predictive(_get_model_for(m_name).numpyro_model, samples)
            key = random.fold_in(random.PRNGKey(123), abs(hash(gid)) % (2**31))
            pp = pred(
                key,
                features=features_jax,
                observation=None,
                observation_uncertainty=None,
                preset_name=gfit.preset,
            )
            mean_pred = np.asarray(pp["obs"]).mean(axis=0)
            resid = np.asarray(gfit.group.observation) - mean_pred
            x = gfit.group.features[feature]
            ax_res.scatter(x, resid, color=color, marker=marker, s=45, edgecolor="black", alpha=0.85)
            if k.size:
                ax_k.scatter(x[: k.size], k, color=color, marker=marker, s=45, edgecolor="black", alpha=0.85)

        ax_res.axhline(0.0, color="gray", linestyle=":")
        ax_k.axhline(0.7, color="gray", linestyle="--")
        ax_k.axhline(1.0, color="gray", linestyle=":")
        ax_res.set_xlabel(feature, fontsize=11)
        ax_res.set_ylabel("residual", fontsize=11)
        ax_res.set_title(f"{m_name} residuals", fontsize=12)
        ax_k.set_xlabel(feature, fontsize=11)
        ax_k.set_ylabel("Pareto-k", fontsize=11)
        ax_k.set_title(f"{m_name} Pareto-k", fontsize=12)

    fig.tight_layout()
    return fig, axes


def _pareto_k_safe(loo: Any) -> np.ndarray:
    v = getattr(loo, "pareto_k", None)
    if v is None:
        return np.array([])
    return np.asarray(v)


def _get_model_for(model_name: str) -> "BayesianModel":
    from .models import get_model

    return get_model(model_name)


def plot_loo_comparison(comparison: ModelComparison, figsize: tuple[float, float] = (8.0, 5.0)) -> tuple["Figure", "Axes"]:
    """Bar chart of summed ELPD per model from a :class:`ModelComparison`."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=figsize)
    df = comparison.global_ranking.sort_values("sum_elpd", ascending=False)
    ax.bar(df["model"], df["sum_elpd"], color="#1f5aa6", edgecolor="black")
    ax.set_ylabel("Sum ELPD (LOO)", fontsize=12)
    ax.set_title("Model comparison (higher is better)", fontsize=13)
    for i, row in df.iterrows():
        ax.text(row["model"], row["sum_elpd"], f"  n={int(row['n_groups'])}", va="center", fontsize=10)
    fig.tight_layout()
    return fig, ax


def plot_dataset_overview(
    dataset: BayesianDataset,
    *,
    feature: str = "temperature",
    doi_field: str = "source_doi",
    composition_field: str | None = "mole_fraction_water",
    figsize: tuple[float, float] = (10.0, 6.0),
) -> tuple["Figure", "Axes"]:
    """Scatter of all groups' observations in feature-vs-observation space."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=figsize)
    dois: list[str] = []
    for grp in dataset.groups:
        dois.append(_resolve_doi(grp, doi_field))
    doi_order = list(dict.fromkeys(dois))

    for grp in dataset.groups:
        doi = _resolve_doi(grp, doi_field)
        color = _doi_color(doi)
        marker = _doi_marker(doi, doi_order)
        comp = _resolve_composition(grp, composition_field)
        label = grp.group_label if comp is None else f"{doi} | {composition_field}={comp:.3f}"
        ax.scatter(
            grp.features[feature],
            grp.observation,
            color=color,
            marker=marker,
            s=45,
            edgecolor="black",
            alpha=0.85,
            label=label,
        )
    ax.set_xlabel(feature, fontsize=12)
    ax.set_ylabel(
        "ln(observation)" if dataset.log_observation else dataset.property, fontsize=12
    )
    ax.set_title("Dataset overview", fontsize=13)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=8)
    fig.tight_layout()
    return fig, ax


def _resolve_group_id(
    fit: BayesianFit,
    model_name: str,
    selector: Any,
) -> tuple[Any, ...]:
    """Map a flexible group selector to the canonical ``group_id`` tuple.

    Supported selector types:
        * ``None`` — first available group (default).
        * ``int`` — index into the available groups (negative allowed).
        * ``str`` — exact match on ``group_label``; if no exact match, a unique
          substring match is accepted.
        * ``dict`` — keys/values are matched against ``metadata["group_by"]``
          (or top-level ``metadata``). The selector must match exactly one group.
        * ``tuple`` — exact ``group_id`` tuple (legacy path).
        * :class:`BayesianGroup` — direct group object.
    """
    available = fit.list_groups(model_name)
    if not available:
        raise KeyError(f"No fits available for model {model_name!r}.")

    if selector is None:
        return available[0]

    if isinstance(selector, BayesianGroup):
        if selector.group_id in available:
            return selector.group_id
        raise KeyError(
            f"BayesianGroup {selector.group_label!r} has no fit for model {model_name!r}."
        )

    if isinstance(selector, tuple):
        if selector in available:
            return selector
        raise KeyError(
            f"group_id {selector!r} not found for model {model_name!r}. "
            f"Available group_ids (first 5): {available[:5]}"
        )

    if isinstance(selector, bool):
        # bool is a subclass of int — guard against accidental True/False selectors.
        raise TypeError(
            f"Boolean is not a valid group selector. Pass an int index, label or dict instead."
        )

    if isinstance(selector, int):
        if not (-len(available) <= selector < len(available)):
            raise IndexError(
                f"group index {selector} out of range for {len(available)} fitted groups."
            )
        return available[selector]

    if isinstance(selector, str):
        labels = [fit.get(model_name, gid).group.group_label for gid in available]
        exact = [gid for gid, lbl in zip(available, labels) if lbl == selector]
        if exact:
            return exact[0]
        partial = [gid for gid, lbl in zip(available, labels) if selector in lbl]
        if len(partial) == 1:
            return partial[0]
        if len(partial) > 1:
            match_labels = [
                fit.get(model_name, gid).group.group_label for gid in partial
            ]
            raise KeyError(
                f"group label {selector!r} matches multiple groups: {match_labels}. "
                "Be more specific."
            )
        raise KeyError(
            f"No group label matches {selector!r} for model {model_name!r}. "
            f"Available labels: {labels}"
        )

    if isinstance(selector, dict):
        matches: list[tuple[Any, ...]] = []
        for gid in available:
            grp = fit.get(model_name, gid).group
            group_by = grp.metadata.get("group_by", {}) or {}
            meta = grp.metadata
            if all((group_by.get(k) == v) or (meta.get(k) == v) for k, v in selector.items()):
                matches.append(gid)
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            match_labels = [
                fit.get(model_name, gid).group.group_label for gid in matches
            ]
            raise KeyError(
                f"selector {selector!r} matches {len(matches)} groups: {match_labels}. "
                "Be more specific."
            )
        raise KeyError(
            f"No group matches selector {selector!r} for model {model_name!r}."
        )

    raise TypeError(
        f"Cannot resolve group selector of type {type(selector).__name__}: {selector!r}. "
        "Pass None, an int index, a label substring, a dict of group_by values, "
        "a group_id tuple, or a BayesianGroup."
    )


def _figure_from_axes(ax_obj: Any) -> "Figure":
    """Best-effort extraction of a matplotlib Figure from whatever arviz returns."""
    if hasattr(ax_obj, "figure"):
        return ax_obj.figure  # type: ignore[no-any-return]
    if isinstance(ax_obj, np.ndarray) and ax_obj.size > 0:
        first = ax_obj.flat[0]
        return first.figure  # type: ignore[no-any-return]
    import matplotlib.pyplot as plt

    return plt.gcf()


def _default_var_names(model_name: str, include_sigma: bool = True) -> list[str]:
    from .models import get_model

    m = get_model(model_name)
    names = list(m.param_names)
    if include_sigma:
        names.append("model_sigma")
    return names


def _hdi(samples: np.ndarray, prob: float = 0.9) -> tuple[float, float]:
    """Highest-Density Interval for a 1-D posterior sample array."""
    s = np.sort(samples)
    n = s.size
    width = int(np.floor(prob * n))
    if width <= 0 or width >= n:
        return float(s[0]), float(s[-1])
    diffs = s[width:] - s[:-width]
    idx = int(np.argmin(diffs))
    return float(s[idx]), float(s[idx + width])


def plot_posterior(
    fit: BayesianFit,
    *,
    model_name: str,
    group_id: Any = None,
    parameters: Iterable[str] | None = None,
    hdi_prob: float = 0.9,
    n_bins: int = 50,
    figsize_per_param: tuple[float, float] = (4.0, 3.0),
    color: str = "#1f5aa6",
) -> tuple["Figure", "np.ndarray"]:
    """Marginal posterior histograms with median + HDI overlay for one fit.

    One subplot per requested parameter. ``parameters`` defaults to the model's
    declared ``param_names`` plus ``model_sigma``.
    """
    import matplotlib.pyplot as plt

    gid = _resolve_group_id(fit, model_name, group_id)
    gfit = fit.get(model_name, gid)
    var_names = list(parameters) if parameters is not None else _default_var_names(model_name)
    samples = gfit.samples()

    n_cols = min(3, len(var_names))
    n_rows = int(np.ceil(len(var_names) / n_cols))
    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(figsize_per_param[0] * n_cols, figsize_per_param[1] * n_rows),
        squeeze=False,
    )
    axes_flat = axes.ravel()

    for i, name in enumerate(var_names):
        ax = axes_flat[i]
        if name not in samples:
            ax.text(0.5, 0.5, f"missing site {name!r}", ha="center", va="center")
            ax.set_axis_off()
            continue
        arr = np.asarray(samples[name]).reshape(-1)
        median = float(np.median(arr))
        lo, hi = _hdi(arr, prob=hdi_prob)
        ax.hist(arr, bins=n_bins, color=color, alpha=0.8, edgecolor="white", linewidth=0.4)
        ax.axvline(median, color="black", lw=1.4, linestyle="--", label=f"median = {median:.4g}")
        ax.axvspan(lo, hi, color=color, alpha=0.15, label=f"{int(hdi_prob*100)}% HDI")
        ax.set_title(name, fontsize=12)
        ax.set_xlabel(name, fontsize=10)
        ax.legend(loc="best", fontsize=8)

    for j in range(len(var_names), axes_flat.size):
        axes_flat[j].set_axis_off()

    fig.suptitle(
        f"{model_name} posterior — {gfit.group.group_label}", fontsize=13
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig, axes


def plot_trace(
    fit: BayesianFit,
    *,
    model_name: str,
    group_id: Any = None,
    parameters: Iterable[str] | None = None,
    figsize_per_param: tuple[float, float] = (8.0, 1.8),
) -> tuple["Figure", "np.ndarray"]:
    """Per-chain trace plot — quickly checks chain mixing.

    The MCMC samples are reshaped to ``(num_chains, num_samples)`` per site,
    then each chain is drawn as a line. Mean across chains is shown as a thick
    dark line to make stationarity inspection easier.
    """
    import matplotlib.pyplot as plt

    gid = _resolve_group_id(fit, model_name, group_id)
    gfit = fit.get(model_name, gid)
    var_names = list(parameters) if parameters is not None else _default_var_names(model_name)
    raw = gfit.mcmc.get_samples(group_by_chain=True)

    n_rows = len(var_names)
    fig, axes = plt.subplots(
        n_rows,
        1,
        figsize=(figsize_per_param[0], figsize_per_param[1] * max(1, n_rows)),
        squeeze=False,
    )
    palette = ["#1f5aa6", "#d9531e", "#3aa055", "#a23ca0", "#cb9e1f", "#5fc6c9"]

    for i, name in enumerate(var_names):
        ax = axes[i, 0]
        if name not in raw:
            ax.text(0.5, 0.5, f"missing site {name!r}", ha="center", va="center")
            ax.set_axis_off()
            continue
        chain_arr = np.asarray(raw[name])
        if chain_arr.ndim == 1:
            chain_arr = chain_arr[None, :]
        for c in range(chain_arr.shape[0]):
            ax.plot(
                chain_arr[c],
                color=palette[c % len(palette)],
                alpha=0.6,
                lw=0.7,
                label=f"chain {c}",
            )
        ax.axhline(float(chain_arr.mean()), color="black", lw=1.2, linestyle=":")
        ax.set_ylabel(name, fontsize=10)
        if i == 0:
            ax.legend(loc="best", fontsize=8, ncol=min(4, chain_arr.shape[0]))
    axes[-1, 0].set_xlabel("draw", fontsize=10)
    fig.suptitle(f"{model_name} trace — {gfit.group.group_label}", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig, axes


def plot_pair(
    fit: BayesianFit,
    *,
    model_name: str,
    group_id: Any = None,
    parameters: Iterable[str] | None = None,
    figsize: tuple[float, float] | None = None,
    color: str = "#1f5aa6",
    n_bins: int = 40,
) -> tuple["Figure", "np.ndarray"]:
    """Corner-style pairwise scatter plot with marginal histograms.

    Built on plain matplotlib so we don't depend on the (volatile) ArviZ 1.0
    ``plot_pair`` signature. Defaults to the model's ``param_names`` (no
    ``model_sigma``).
    """
    import matplotlib.pyplot as plt

    gid = _resolve_group_id(fit, model_name, group_id)
    gfit = fit.get(model_name, gid)
    var_names = (
        list(parameters)
        if parameters is not None
        else _default_var_names(model_name, include_sigma=False)
    )
    samples = gfit.samples()
    arrs = {n: np.asarray(samples[n]).reshape(-1) for n in var_names if n in samples}
    names = list(arrs)
    k = len(names)
    if k == 0:
        raise ValueError("No requested parameters were found in the posterior samples.")

    fig, axes = plt.subplots(
        k,
        k,
        figsize=figsize or (2.5 * k + 1.0, 2.5 * k + 1.0),
        squeeze=False,
    )

    for i, ni in enumerate(names):
        for j, nj in enumerate(names):
            ax = axes[i, j]
            if i == j:
                ax.hist(arrs[ni], bins=n_bins, color=color, alpha=0.8, edgecolor="white", lw=0.4)
            elif j < i:
                ax.scatter(arrs[nj], arrs[ni], s=4, alpha=0.25, color=color, edgecolor="none")
            else:
                ax.set_visible(False)
                continue
            if i == k - 1:
                ax.set_xlabel(nj, fontsize=10)
            else:
                ax.set_xticklabels([])
            if j == 0 and i > 0:
                ax.set_ylabel(ni, fontsize=10)
            elif j > 0:
                ax.set_yticklabels([])
    fig.suptitle(f"{model_name} pair plot — {gfit.group.group_label}", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig, axes


def plot_prior_vs_posterior(
    fit: BayesianFit,
    *,
    model: "BayesianModel",
    parameter: str,
    preset_name: str,
    group_id: Any = None,
    n_prior_samples: int = 4000,
    n_bins: int = 60,
    seed: int = 0,
    figsize: tuple[float, float] = (8.0, 5.0),
    title: str | None = None,
) -> tuple["Figure", "Axes"]:
    """Overlay prior and posterior densities for a single parameter.

    The prior is drawn directly from the spec's :class:`numpyro.distributions`
    object, while the posterior comes from the cached MCMC samples — so this
    works seamlessly for any prior family (Uniform, Normal, HalfNormal, ...).
    """
    import matplotlib.pyplot as plt

    gid = _resolve_group_id(fit, model.name, group_id)
    gfit = fit.get(model.name, gid)

    samples = gfit.samples()
    if parameter not in samples:
        raise KeyError(
            f"Posterior site {parameter!r} not found for model {model.name!r}. "
            f"Available: {sorted(samples)}"
        )
    posterior = np.asarray(samples[parameter]).reshape(-1)

    preset = model.get_preset(preset_name)
    if parameter in preset.parameters:
        prior_samples = sample_prior(
            preset.parameters[parameter], n_samples=n_prior_samples, seed=seed
        )
        prior_label = (
            f"prior: {preset.parameters[parameter].describe()}"
        )
    elif parameter == "model_sigma":
        import jax.random as random
        import numpyro.distributions as dist

        key = random.PRNGKey(seed)
        prior_samples = np.asarray(
            dist.HalfNormal(preset.sigma_scale).sample(key, sample_shape=(n_prior_samples,))
        )
        prior_label = f"prior: HalfNormal(scale={preset.sigma_scale})"
    else:
        raise KeyError(
            f"Cannot draw a prior for {parameter!r}: not in preset {preset.name!r}."
        )

    fig, ax = plt.subplots(figsize=figsize)
    lo = float(min(prior_samples.min(), posterior.min()))
    hi = float(max(prior_samples.max(), posterior.max()))
    pad = 0.02 * (hi - lo) if hi > lo else 1e-3
    bins = np.linspace(lo - pad, hi + pad, n_bins)

    ax.hist(
        prior_samples,
        bins=bins,
        density=True,
        color="#9aa0a6",
        alpha=0.45,
        label=prior_label,
        edgecolor="white",
        linewidth=0.4,
    )
    ax.hist(
        posterior,
        bins=bins,
        density=True,
        color="#1f5aa6",
        alpha=0.75,
        label="posterior",
        edgecolor="white",
        linewidth=0.4,
    )

    med = float(np.median(posterior))
    q05, q95 = (float(np.quantile(posterior, q)) for q in (0.05, 0.95))
    ax.axvline(med, color="black", linestyle="--", lw=1.2, label=f"posterior median = {med:.4g}")
    ax.axvspan(q05, q95, color="#1f5aa6", alpha=0.10, label="posterior 5-95 %")

    ax.set_xlabel(parameter, fontsize=12)
    ax.set_ylabel("density", fontsize=12)
    ax.set_title(
        title or f"{model.name}: prior vs. posterior of {parameter!r} — {gfit.group.group_label}",
        fontsize=12,
    )
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    return fig, ax


__all__ = [
    "plot_posterior_predictive",
    "plot_prior_predictive",
    "plot_parameter_vs_feature",
    "plot_residuals_and_pareto_k",
    "plot_loo_comparison",
    "plot_dataset_overview",
    "plot_posterior",
    "plot_trace",
    "plot_pair",
    "plot_prior_vs_posterior",
]
