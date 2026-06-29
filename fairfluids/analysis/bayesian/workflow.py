"""High-level orchestrator for a Bayesian analysis run.

:class:`BayesianWorkflow` wires together the four canonical phases:

1. **Prior setting** — supply priors and inspect prior predictive quantiles.
2. **Exploration** — visualize prior bands against group data.
3. **Model fitting / evaluation** — NUTS sampling and diagnostics.
4. **Comparison** — LOO with Pareto-k diagnostics and posterior summaries.

The workflow is stateful but explicit: each method returns a value (DataFrame or
plot handles) and the workflow caches fit / comparison results so plot helpers
can be called repeatedly without re-running MCMC.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Iterable, Mapping

import numpy as np
import pandas as pd

from .comparison import ModelComparison, compare_models, posterior_summary
from .data import BayesianDataset, BayesianGroup
from .inference import BayesianFit, fit_groups, predict, predict_averaged
from .models import BayesianModel, get_model
from .priors import (
    HalfNormalPriorSpec,
    LogNormalPriorSpec,
    NormalPriorSpec,
    PriorSet,
    PriorSpec,
    TruncatedNormalPriorSpec,
    UniformPriorSpec,
    prior_predictive_quantiles,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


@dataclass
class BayesianWorkflow:
    """Top-level facade orchestrating prior exploration, MCMC fitting and model comparison.

    Construct with a :class:`BayesianDataset`, an iterable of models (instances
    or registered names) and the :class:`PriorSet` (or per-model mapping) to use.
    The workflow keeps the latest :class:`BayesianFit` and
    :class:`ModelComparison` for downstream plotting.
    """

    dataset: BayesianDataset
    models: list[BayesianModel]
    priors: PriorSet | dict[str, PriorSet]
    fit_result: BayesianFit | None = None
    comparison_result: ModelComparison | None = None

    @classmethod
    def from_names(
        cls,
        dataset: BayesianDataset,
        model_names: Iterable[str],
        *,
        priors: PriorSet | dict[str, PriorSet],
    ) -> "BayesianWorkflow":
        instances = [get_model(n) for n in model_names]
        return cls(dataset=dataset, models=instances, priors=priors)

    # -- Phase 1: Prior setting -------------------------------------------------

    def set_priors(self, priors: PriorSet | Mapping[str, PriorSet]) -> None:
        if isinstance(priors, PriorSet):
            self.priors = priors
        else:
            self.priors = dict(priors)

    def explore_priors(
        self,
        *,
        group: BayesianGroup | None = None,
        n_samples: int = 3000,
        seed: int = 0,
        quantiles: tuple[float, ...] = (0.01, 0.05, 0.5, 0.95, 0.99),
        priors: PriorSet | Mapping[str, PriorSet] | None = None,
    ) -> pd.DataFrame:
        """Return a DataFrame of prior predictive quantiles per model.

        Args:
            group: Reference feature grid (defaults to the first dataset group).
            n_samples: Number of prior predictive draws per model.
            seed: PRNG seed.
            quantiles: Quantile levels to summarize.
            priors: Optional override of the priors to evaluate (a single
                :class:`PriorSet` for every model, or a per-model mapping).
                Defaults to the workflow's configured priors.
        """
        ref_group = group or self.dataset.groups[0]
        features = {name: ref_group.features[name] for name in ref_group.features}

        rows: list[dict[str, Any]] = []
        for model in self.models:
            bound_model = model.bind_group(ref_group)
            model_priors = self._priors_for(model.name, override=priors)
            summary = prior_predictive_quantiles(
                bound_model,
                features=features,
                priors=model_priors,
                n_samples=n_samples,
                quantiles=quantiles,
                observation_uncertainty=ref_group.observation_uncertainty,
                seed=seed,
            )
            summary.pop("samples", None)
            rows.append(
                {
                    "reference_group": ref_group.group_label,
                    **summary,
                }
            )
        return pd.DataFrame(rows)

    # -- Phase 2: Exploration ---------------------------------------------------

    def plot_prior_predictive(
        self,
        model_name: str,
        *,
        group: BayesianGroup | None = None,
        priors: PriorSet | None = None,
        feature: str = "temperature",
        plot_scale: str | None = None,
    ) -> tuple["Figure", "Axes"]:
        from . import plots

        model = self._model_by_name(model_name)
        used_priors = priors or self._priors_for(model.name)
        ref_group = group or self.dataset.groups[0]
        bound_model = model.bind_group(ref_group)
        return plots.plot_prior_predictive(
            bound_model,
            ref_group,
            priors=used_priors,
            feature=feature,
            plot_scale=plot_scale,
        )

    def plot_dataset_overview(self, **kwargs: Any) -> tuple["Figure", "Axes"]:
        from . import plots

        return plots.plot_dataset_overview(self.dataset, **kwargs)

    # -- Phase 3: Fitting & evaluation -----------------------------------------

    def fit(
        self,
        *,
        num_warmup: int = 2000,
        num_samples: int = 2000,
        num_chains: int = 4,
        target_accept_prob: float = 0.95,
        seed: int = 0,
        progress_bar: bool = False,
    ) -> BayesianFit:
        """Fit all ``(model, group)`` pairs.

        Set ``progress_bar=True`` for one unified tqdm bar across the full run.
        """
        self.fit_result = fit_groups(
            self.dataset,
            self.models,
            priors=self.priors,
            num_warmup=num_warmup,
            num_samples=num_samples,
            num_chains=num_chains,
            target_accept_prob=target_accept_prob,
            seed=seed,
            progress_bar=progress_bar,
        )
        return self.fit_result

    def diagnostics(self) -> pd.DataFrame:
        return self._require_fit().diagnostics()

    def posterior_summary(self) -> pd.DataFrame:
        return posterior_summary(self._require_fit())

    def to_fairfluids_document(
        self,
        document: Any,
        *,
        fluid_index: int = 0,
        coverage_probability: float = 0.95,
        point_estimate: str = "median",
        include_model_sigma: bool = True,
    ) -> Any:
        """Write the posterior summaries of the current fit back into ``document``.

        Convenience wrapper around
        :meth:`fairfluids.analysis.bayesian.inference.BayesianFit.to_fairfluids_document`
        using the workflow's latest fit. Returns the (mutated) ``document``.
        """
        return self._require_fit().to_fairfluids_document(
            document,
            fluid_index=fluid_index,
            coverage_probability=coverage_probability,
            point_estimate=point_estimate,
            include_model_sigma=include_model_sigma,
        )

    # -- Posterior inspection (raw access) -------------------------------------

    def list_fitted_groups(
        self, model_name: str | None = None
    ) -> list[tuple[Any, ...]]:
        """Return the group IDs available for the given model (defaults to first model)."""
        fit = self._require_fit()
        target = model_name or self.models[0].name
        return fit.list_groups(target)

    def groups_overview(self, model_name: str | None = None) -> pd.DataFrame:
        """Return a DataFrame of the groups available for ``model_name``.

        Columns: ``index`` (integer selector for ``group_id=...``),
        ``group_label`` (string selector), ``group_id`` (raw tuple),
        ``n_points``, and one column per ``group_by`` key (for dict selectors).
        Defaults to the first model in :attr:`models`.
        """
        fit = self._require_fit()
        target = model_name or self.models[0].name
        rows: list[dict[str, Any]] = []
        for i, gid in enumerate(fit.list_groups(target)):
            grp = fit.get(target, gid).group
            row: dict[str, Any] = {
                "index": i,
                "group_label": grp.group_label,
                "group_id": gid,
                "n_points": grp.n_points,
            }
            row.update(grp.metadata.get("group_by", {}) or {})
            rows.append(row)
        return pd.DataFrame(rows)

    def posterior_samples(
        self,
        model_name: str,
        *,
        group_id: Any = None,
    ) -> dict[str, np.ndarray]:
        """Return raw posterior samples as ``{site_name: ndarray}``.

        ``group_id`` accepts the same flexible selectors as
        :meth:`groups_overview`'s ``index`` column (int), ``group_label`` (str),
        a ``{group_by_key: value}`` dict, the raw tuple, or a
        :class:`BayesianGroup`. ``None`` (the default) picks the first fitted
        group.
        """
        return self._require_fit().posterior_samples(model_name, group_id)

    def inference_data(
        self,
        model_name: str,
        *,
        group_id: Any = None,
    ) -> Any:
        """Return the underlying :class:`arviz.InferenceData` for one fit.

        Selector semantics match :meth:`posterior_samples`.
        """
        return self._require_fit().inference_data(model_name, group_id)

    # -- Posterior predictive on arbitrary inputs ------------------------------

    def predict(
        self,
        model_name: str,
        features: Mapping[str, np.ndarray],
        *,
        group_id: Any = None,
        quantiles: tuple[float, ...] = (0.05, 0.5, 0.95),
        return_samples: bool = False,
        seed: int = 0,
        observation_uncertainty: np.ndarray | None = None,
    ) -> dict[str, Any]:
        """Posterior predictive distribution on user-supplied feature inputs.

        Example::

            import numpy as np
            T_new = np.linspace(290.0, 360.0, 50)
            pred = wf.predict('arrhenius', {'temperature': T_new})
            # pred['mean'], pred['q05'], pred['q50'], pred['q95']
        """
        return predict(
            self._require_fit(),
            model_name=model_name,
            features=features,
            group_id=group_id,
            quantiles=quantiles,
            return_samples=return_samples,
            seed=seed,
            observation_uncertainty=observation_uncertainty,
        )

    def predict_averaged(
        self,
        features: Mapping[str, np.ndarray],
        *,
        weights: Mapping[str, float] | None = None,
        group_id: Any = None,
        quantiles: tuple[float, ...] = (0.05, 0.5, 0.95),
        return_samples: bool = False,
        seed: int = 0,
        observation_uncertainty: np.ndarray | None = None,
    ) -> dict[str, Any]:
        """Stacking-weighted posterior predictive distribution.

        If ``weights`` is ``None``, the weights are taken from the cached
        :meth:`compare` result (column ``weight`` of ``global_ranking``). If
        no comparison has been run yet, every model gets equal weight.
        """
        fit = self._require_fit()
        if weights is None and self.comparison_result is not None:
            df = self.comparison_result.global_ranking
            if "weight" in df.columns and df["weight"].notna().any():
                weights = dict(zip(df["model"], df["weight"].astype(float)))
        return predict_averaged(
            fit,
            features=features,
            weights=weights,
            group_id=group_id,
            quantiles=quantiles,
            return_samples=return_samples,
            seed=seed,
            observation_uncertainty=observation_uncertainty,
        )

    # -- Quantitative posterior diagnostics ------------------------------------

    def energy_diagnostics(self, *, warn_threshold: float = 0.3) -> pd.DataFrame:
        """E-BFMI (Energy-Bayesian Fraction of Missing Information) per (model, group).

        E-BFMI below ~0.3 typically indicates that NUTS is struggling to explore
        the posterior — often a hint that the model needs reparameterization.
        Rows with ``ebfmi < warn_threshold`` are flagged via the ``warning``
        column.
        """
        fit = self._require_fit()
        rows: list[dict[str, Any]] = []
        for (m_name, gid), gfit in fit.fits.items():
            ebfmi = _compute_ebfmi(gfit.inference_data, gfit.mcmc)
            rows.append(
                {
                    "model": m_name,
                    "group_label": gfit.group.group_label,
                    "group_id": gid,
                    "ebfmi": ebfmi,
                    "num_divergences": gfit.num_divergences,
                    "warning": (not np.isnan(ebfmi)) and ebfmi < warn_threshold,
                }
            )
        return pd.DataFrame(rows)

    def bayesian_p_values(
        self,
        *,
        statistics: Iterable[str] = ("mean", "std", "min", "max", "rmse"),
        n_replicates: int = 1000,
        seed: int = 0,
    ) -> pd.DataFrame:
        """Posterior predictive p-values for user-chosen test statistics.

        For each ``(model, group)`` fit we draw ``n_replicates`` posterior
        predictive replicates of the observation, evaluate the requested test
        statistics on each replicate vs. the observed data, and report the
        fraction ``P(T(y_rep) > T(y_obs))``. Values near 0.5 are well-calibrated;
        values near 0 or 1 indicate the model cannot reproduce that aspect of
        the data. ``"rmse"`` uses the posterior mean prediction as the
        reference, otherwise ``"mean"``/``"std"``/``"min"``/``"max"`` are
        applied to the observation vector directly.
        """
        import jax.numpy as jnp
        import jax.random as random
        from numpyro.infer import Predictive

        fit = self._require_fit()
        stat_fns: dict[str, Any] = {
            "mean": np.mean,
            "std": np.std,
            "min": np.min,
            "max": np.max,
        }
        requested = list(statistics)
        rows: list[dict[str, Any]] = []
        for (m_name, gid), gfit in fit.fits.items():
            if any(m.name == m_name for m in self.models):
                proto = self._model_by_name(m_name)
                model = (
                    get_model(m_name, **gfit.model_kwargs)
                    if gfit.model_kwargs
                    else proto
                )
            else:
                model = get_model(m_name, **gfit.model_kwargs)
            features_jax = {
                f: jnp.asarray(gfit.group.features[f]) for f in gfit.group.features
            }
            obs_unc = (
                jnp.asarray(gfit.group.observation_uncertainty)
                if gfit.group.observation_uncertainty is not None
                else None
            )
            mcmc_samples = gfit.mcmc.get_samples()
            n_avail = int(next(iter(mcmc_samples.values())).shape[0])
            n_use = min(n_replicates, n_avail)
            sliced = {k: v[:n_use] for k, v in mcmc_samples.items()}
            predictive = Predictive(model.numpyro_model, sliced)
            key = random.fold_in(
                random.PRNGKey(seed), abs(hash((m_name, gid))) % (2**31)
            )
            pp = predictive(
                key,
                features=features_jax,
                observation=None,
                observation_uncertainty=obs_unc,
                priors=gfit.priors,
            )
            y_rep = np.asarray(pp["obs"])  # (n_use, n_points)
            y_obs = np.asarray(gfit.group.observation)
            base_row: dict[str, Any] = {
                "model": m_name,
                "group_label": gfit.group.group_label,
                "group_id": gid,
            }
            for stat in requested:
                if stat in stat_fns:
                    t_rep = stat_fns[stat](y_rep, axis=1)
                    t_obs = float(stat_fns[stat](y_obs))
                elif stat == "rmse":
                    mean_pred = y_rep.mean(axis=0)
                    t_rep = np.sqrt(((y_rep - mean_pred) ** 2).mean(axis=1))
                    t_obs = float(np.sqrt(((y_obs - mean_pred) ** 2).mean()))
                else:
                    raise ValueError(
                        f"Unknown statistic {stat!r}. Available: "
                        f"{sorted(set(stat_fns) | {'rmse'})}"
                    )
                p_value = float(np.mean(t_rep > t_obs))
                rows.append(
                    {
                        **base_row,
                        "statistic": stat,
                        "T_observed": t_obs,
                        "T_replicated_mean": float(t_rep.mean()),
                        "p_value": p_value,
                        "well_calibrated": 0.05 < p_value < 0.95,
                    }
                )
        return pd.DataFrame(rows)

    # -- Prior sensitivity -----------------------------------------------------

    def prior_sensitivity(
        self,
        *,
        scales: tuple[float, ...] = (0.5, 1.0, 2.0),
        num_warmup: int = 500,
        num_samples: int = 500,
        num_chains: int = 1,
        seed: int = 0,
        progress_bar: bool = False,
    ) -> pd.DataFrame:
        """Refit with priors scaled by each factor and return posterior summaries.

        For each ``scale`` in ``scales``, every prior spec in the configured
        priors is widened (or narrowed) and the workflow is refit on the same data.
        The result is a DataFrame indexed by ``(scale, model, group, parameter)``
        with the posterior median and 5/95 % quantiles — flat curves vs ``scale``
        indicate the data dominates the prior; large shifts mean the prior is
        informative.

        Notes:
            * For ``UniformPriorSpec``: bounds are widened around the midpoint
              by the ``scale`` factor.
            * For ``Normal``/``HalfNormal``/``LogNormal``/``TruncatedNormal``:
              the ``scale`` parameter is multiplied. Truncation bounds are kept.
            * ``sigma_scale`` is also multiplied so the noise prior moves
              accordingly.
        """
        fit_baseline = self.fit_result
        comparison_baseline = self.comparison_result
        original_priors = self.priors

        try:
            rows: list[dict[str, Any]] = []
            for s in scales:
                scaled_priors: dict[str, PriorSet] = {}
                for model in self.models:
                    base = self._priors_for(model.name)
                    scaled_priors[model.name] = _scale_priors(base, s)
                self.priors = scaled_priors

                self.fit_result = None
                self.fit(
                    num_warmup=num_warmup,
                    num_samples=num_samples,
                    num_chains=num_chains,
                    seed=seed,
                    progress_bar=progress_bar,
                )
                summary = self.posterior_summary()
                for _, row in summary.iterrows():
                    rows.append(
                        {
                            "scale": s,
                            "model": row["model"],
                            "group_id": row["group_id"],
                            "group_label": row["group_label"],
                            "parameter": row["parameter"],
                            "median": row["median"],
                            "q05": row["q05"],
                            "q95": row["q95"],
                        }
                    )
        finally:
            self.priors = original_priors
            self.fit_result = fit_baseline
            self.comparison_result = comparison_baseline

        return pd.DataFrame(rows)

    # -- Influence diagnostics / reloo-light -----------------------------------

    def influential_points(
        self,
        *,
        k_threshold: float = 0.7,
    ) -> pd.DataFrame:
        """Identify observations with Pareto-k above ``k_threshold`` (per fit).

        Returns a DataFrame with one row per problematic observation, including
        the model, group, point index, Pareto-k value, the feature values and
        the observation. Use this to spot outliers / measurement errors before
        running a full reloo.
        """
        import arviz as az

        fit = self._require_fit()
        rows: list[dict[str, Any]] = []
        for (m_name, gid), gfit in fit.fits.items():
            try:
                loo = az.loo(gfit.inference_data, pointwise=True)
                k_arr = np.asarray(getattr(loo, "pareto_k", []))
            except Exception:
                continue
            for i, k_val in enumerate(k_arr):
                if not np.isfinite(k_val) or k_val < k_threshold:
                    continue
                row: dict[str, Any] = {
                    "model": m_name,
                    "group_label": gfit.group.group_label,
                    "group_id": gid,
                    "point_index": int(i),
                    "pareto_k": float(k_val),
                    "observation": float(gfit.group.observation[i]),
                }
                for fname in gfit.group.features:
                    row[fname] = float(gfit.group.features[fname][i])
                rows.append(row)
        return pd.DataFrame(rows)

    def refit_without_influential(
        self,
        *,
        k_threshold: float = 0.7,
        num_warmup: int | None = None,
        num_samples: int | None = None,
        num_chains: int | None = None,
        seed: int = 0,
        progress_bar: bool = False,
    ) -> tuple[BayesianFit, pd.DataFrame]:
        """Drop high-Pareto-k points per group and refit (reloo-light).

        For each ``(model, group)`` with at least one influential point, the
        offending point(s) are removed from that group and a fresh fit is
        performed on the cleaned data. The returned :class:`BayesianFit` only
        contains the refit cases; the original :attr:`fit_result` is left
        unchanged. The DataFrame summarizes how many points were dropped per
        group.
        """
        influential = self.influential_points(k_threshold=k_threshold)
        if influential.empty:
            return BayesianFit(model_names=(), group_ids=()), pd.DataFrame(
                columns=[
                    "model",
                    "group_id",
                    "group_label",
                    "n_dropped",
                    "n_remaining",
                ],
            )

        fit = self._require_fit()

        from .data import BayesianDataset, BayesianGroup

        drops: dict[tuple[str, tuple[Any, ...]], list[int]] = {}
        for _, row in influential.iterrows():
            key = (row["model"], row["group_id"])
            drops.setdefault(key, []).append(int(row["point_index"]))

        nw = num_warmup or 1000
        ns = num_samples or 1000
        nc = num_chains or 2

        summary_rows: list[dict[str, Any]] = []
        new_groups: list[BayesianGroup] = []
        models_to_fit: dict[str, list[BayesianGroup]] = {}
        for (m_name, gid), point_indices in drops.items():
            gfit = fit.get(m_name, gid)
            grp = gfit.group
            keep = np.ones(grp.observation.shape[0], dtype=bool)
            keep[point_indices] = False
            new_features = {k: np.asarray(v)[keep] for k, v in grp.features.items()}
            new_obs = np.asarray(grp.observation)[keep]
            new_unc = (
                np.asarray(grp.observation_uncertainty)[keep]
                if grp.observation_uncertainty is not None
                else None
            )
            new_raw_obs = np.asarray(grp.raw_observation)[keep]
            new_raw_unc = (
                np.asarray(grp.raw_observation_uncertainty)[keep]
                if grp.raw_observation_uncertainty is not None
                else None
            )
            new_df = (
                grp.dataframe.iloc[keep].reset_index(drop=True)
                if grp.dataframe is not None
                else None
            )
            cleaned = BayesianGroup(
                group_id=grp.group_id,
                group_label=grp.group_label + " (reloo)",
                metadata=grp.metadata,
                features=new_features,
                observation=new_obs,
                observation_uncertainty=new_unc,
                raw_observation=new_raw_obs,
                raw_observation_uncertainty=new_raw_unc,
                log_observation=grp.log_observation,
                dataframe=new_df,
            )
            new_groups.append(cleaned)
            models_to_fit.setdefault(m_name, []).append(cleaned)
            summary_rows.append(
                {
                    "model": m_name,
                    "group_id": gid,
                    "group_label": grp.group_label,
                    "n_dropped": int(len(point_indices)),
                    "n_remaining": int(new_features[next(iter(new_features))].shape[0]),
                }
            )

        # Run an isolated fit per affected (model, group) to avoid touching self.fit_result.
        cleaned_dataset = BayesianDataset(
            property=self.dataset.property,
            feature_names=self.dataset.feature_names,
            group_by=self.dataset.group_by,
            log_observation=self.dataset.log_observation,
            groups=new_groups,
        )
        models_in_order = [m for m in self.models if m.name in models_to_fit]
        priors_arg: dict[str, PriorSet] = {
            m.name: self._priors_for(m.name) for m in models_in_order
        }
        new_fit = fit_groups(
            cleaned_dataset,
            models_in_order,
            priors=priors_arg,
            num_warmup=nw,
            num_samples=ns,
            num_chains=nc,
            seed=seed,
            progress_bar=progress_bar,
        )
        return new_fit, pd.DataFrame(summary_rows)

    # -- Phase 4: Comparison ----------------------------------------------------

    def compare(
        self,
        *,
        pareto_k_thresholds: tuple[float, ...] = (0.7, 1.0),
        method: str = "stacking",
    ) -> ModelComparison:
        fit = self._require_fit()
        self.comparison_result = compare_models(
            fit,
            pareto_k_thresholds=pareto_k_thresholds,
            method=method,
        )
        return self.comparison_result

    # -- Plotting facades -------------------------------------------------------

    def plot_posterior_predictive(
        self,
        model_name: str,
        *,
        group_id: Any = None,
        feature: str = "temperature",
        x_axis: str | Callable[[np.ndarray], np.ndarray] | None = None,
        xlabel: str | None = None,
        inverse_temperature_axis: bool = True,
        plot_scale: str | None = None,
        **kwargs: Any,
    ) -> tuple["Figure", "Axes"]:
        """Posterior predictive plot.

        Set ``x_axis="feature"`` for raw temperature (K), ``x_axis="inverse_temperature"``
        for ``1000/(R*T)``, or pass a callable ``f(T) -> x``. When ``x_axis`` is
        omitted, ``inverse_temperature_axis`` controls the legacy default.

        ``plot_scale`` defaults to linear SI units (``property``) for log-likelihood
        models; pass ``"likelihood"`` to plot on the transformed observation scale.
        """
        from . import plots

        model = self._model_by_name(model_name)
        return plots.plot_posterior_predictive(
            self._require_fit(),
            model,
            group_id=group_id,
            feature=feature,
            x_axis=x_axis,
            xlabel=xlabel,
            inverse_temperature_axis=inverse_temperature_axis,
            plot_scale=plot_scale,
            **kwargs,
        )

    def plot_parameter_vs_feature(
        self,
        model_name: str,
        *,
        parameter: str,
        feature: str,
        **kwargs: Any,
    ) -> tuple["Figure", "Axes"]:
        from . import plots

        return plots.plot_parameter_vs_feature(
            self._require_fit(),
            model_name=model_name,
            parameter=parameter,
            feature=feature,
            **kwargs,
        )

    def plot_residuals_and_pareto_k(
        self, **kwargs: Any
    ) -> tuple["Figure", "np.ndarray"]:
        from . import plots

        return plots.plot_residuals_and_pareto_k(self._require_fit(), **kwargs)

    # -- Posterior diagnostics plots -------------------------------------------

    def plot_posterior(
        self,
        model_name: str,
        *,
        group_id: Any = None,
        parameters: Iterable[str] | None = None,
        hdi_prob: float = 0.9,
        **kwargs: Any,
    ) -> tuple["Figure", Any]:
        """Marginal posterior histograms (median + HDI) for one ``(model, group)`` fit.

        ``group_id`` accepts an integer index, a ``group_label`` string (or
        unique substring), a ``{group_by_key: value}`` dict, the raw tuple, or
        a :class:`BayesianGroup`. Default = first fitted group.
        Use :meth:`groups_overview` to see what's available.
        """
        from . import plots

        return plots.plot_posterior(
            self._require_fit(),
            model_name=model_name,
            group_id=group_id,
            parameters=parameters,
            hdi_prob=hdi_prob,
            **kwargs,
        )

    def plot_trace(
        self,
        model_name: str,
        *,
        group_id: Any = None,
        parameters: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> tuple["Figure", Any]:
        """Per-chain trace plot for one ``(model, group)`` fit.

        See :meth:`plot_posterior` for the supported ``group_id`` selectors.
        """
        from . import plots

        return plots.plot_trace(
            self._require_fit(),
            model_name=model_name,
            group_id=group_id,
            parameters=parameters,
            **kwargs,
        )

    def plot_pair(
        self,
        model_name: str,
        *,
        group_id: Any = None,
        parameters: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> tuple["Figure", Any]:
        """Pairwise joint posteriors for one ``(model, group)`` fit.

        See :meth:`plot_posterior` for the supported ``group_id`` selectors.
        """
        from . import plots

        return plots.plot_pair(
            self._require_fit(),
            model_name=model_name,
            group_id=group_id,
            parameters=parameters,
            **kwargs,
        )

    def plot_prior_vs_posterior(
        self,
        model_name: str,
        parameter: str,
        *,
        group_id: Any = None,
        priors: PriorSet | None = None,
        n_prior_samples: int = 4000,
        seed: int = 0,
        **kwargs: Any,
    ) -> tuple["Figure", "Axes"]:
        """Overlay the prior and posterior densities for a single parameter.

        ``group_id`` accepts an integer index, a ``group_label`` string, a
        ``{group_by_key: value}`` dict, the raw tuple or a :class:`BayesianGroup`
        — same semantics as :meth:`plot_posterior`. ``priors`` defaults to the
        workflow's configured priors for ``model_name``.
        """
        from . import plots

        model = self._model_by_name(model_name)
        used_priors = priors or self._priors_for(model_name)
        return plots.plot_prior_vs_posterior(
            self._require_fit(),
            model=model,
            parameter=parameter,
            priors=used_priors,
            group_id=group_id,
            n_prior_samples=n_prior_samples,
            seed=seed,
            **kwargs,
        )

    def plot_model_comparison(self, **kwargs: Any) -> tuple["Figure", "Axes"]:
        from . import plots

        if self.comparison_result is None:
            self.compare()
        assert self.comparison_result is not None
        return plots.plot_loo_comparison(self.comparison_result, **kwargs)

    # -- Helpers ----------------------------------------------------------------

    def _model_by_name(self, name: str) -> BayesianModel:
        for m in self.models:
            if m.name == name:
                return m
        raise KeyError(
            f"Model {name!r} is not part of this workflow. "
            f"Available: {[m.name for m in self.models]}"
        )

    def _priors_for(
        self,
        model_name: str,
        *,
        override: PriorSet | Mapping[str, PriorSet] | None = None,
    ) -> PriorSet:
        source: Any = override if override is not None else self.priors
        if isinstance(source, PriorSet):
            return source
        try:
            return source[model_name]
        except KeyError as exc:
            raise KeyError(
                f"No PriorSet configured for model {model_name!r}. "
                f"Provided keys: {sorted(source)}"
            ) from exc

    def _require_fit(self) -> BayesianFit:
        if self.fit_result is None:
            raise RuntimeError(
                "BayesianWorkflow.fit() must be called before accessing diagnostics/plots."
            )
        return self.fit_result


def _compute_ebfmi(idata: Any, mcmc: Any) -> float:
    """Compute E-BFMI from either ``sample_stats.energy`` or, if missing, the MCMC extras.

    Definition (Betancourt 2017): ``E-BFMI = mean[(E_t - E_{t-1})^2] / Var[E]``.
    The result is averaged over chains.
    """
    energy: np.ndarray | None = None
    ss = getattr(idata, "sample_stats", None)
    if ss is not None and "energy" in ss:
        energy = np.asarray(ss["energy"].values)
    else:
        try:
            extras = mcmc.get_extra_fields()
            if isinstance(extras, dict) and "energy" in extras:
                energy = np.asarray(extras["energy"])
                if energy.ndim == 1:
                    energy = energy[None, :]
        except Exception:
            energy = None

    if energy is None or energy.size == 0:
        return float("nan")
    if energy.ndim == 1:
        energy = energy[None, :]
    bfmis: list[float] = []
    for chain in energy:
        chain = np.asarray(chain, dtype=float)
        if chain.size < 2 or not np.isfinite(np.var(chain)) or np.var(chain) == 0:
            continue
        diff = np.diff(chain)
        bfmis.append(float(np.mean(diff**2) / np.var(chain)))
    return float(np.mean(bfmis)) if bfmis else float("nan")


def _scale_priors(priors: PriorSet, scale: float) -> PriorSet:
    """Return a new ``PriorSet`` with every prior widened/narrowed by ``scale``.

    * ``UniformPriorSpec`` — bounds widened around the midpoint by ``scale``.
    * ``Normal``/``HalfNormal``/``LogNormal``/``TruncatedNormal`` — the
      distribution's ``scale`` parameter is multiplied by ``scale``. For
      :class:`TruncatedNormalPriorSpec` truncation bounds are preserved.
    * ``sigma_scale`` is multiplied by ``scale``.
    """
    if scale <= 0.0:
        raise ValueError(f"prior_sensitivity scale must be > 0, got {scale}")
    new_params: dict[str, PriorSpec] = {}
    for name, spec in priors.parameters.items():
        if isinstance(spec, UniformPriorSpec):
            mid = 0.5 * (spec.low + spec.high)
            half = 0.5 * (spec.high - spec.low) * scale
            new_params[name] = UniformPriorSpec(low=mid - half, high=mid + half)
        elif isinstance(spec, NormalPriorSpec):
            new_params[name] = NormalPriorSpec(loc=spec.loc, scale=spec.scale * scale)
        elif isinstance(spec, HalfNormalPriorSpec):
            new_params[name] = HalfNormalPriorSpec(scale=spec.scale * scale)
        elif isinstance(spec, LogNormalPriorSpec):
            new_params[name] = LogNormalPriorSpec(
                loc=spec.loc, scale=spec.scale * scale
            )
        elif isinstance(spec, TruncatedNormalPriorSpec):
            new_params[name] = TruncatedNormalPriorSpec(
                loc=spec.loc,
                scale=spec.scale * scale,
                low=spec.low,
                high=spec.high,
            )
        else:
            new_params[name] = spec
    return PriorSet(
        parameters=new_params,
        sigma_scale=priors.sigma_scale * scale,
        likelihood=priors.likelihood,
        student_t_df=priors.student_t_df,
    )


__all__ = ["BayesianWorkflow"]
