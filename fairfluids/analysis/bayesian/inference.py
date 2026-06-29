"""MCMC inference for :class:`BayesianModel` instances on grouped data.

The public entry point is :func:`fit_groups`, which runs NUTS once per
``(model, group)`` combination and packages the results into a
:class:`BayesianFit` container. Posterior samples are exposed both as the
underlying NumPyro ``MCMC`` object (for cheap posterior predictive draws) and
as an :class:`arviz.InferenceData` (for diagnostics and comparison).
"""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Iterable, Mapping

import numpy as np
import pandas as pd

from .data import BayesianDataset, BayesianGroup
from .priors import PriorSet
from .progress import total_mcmc_steps, unified_mcmc_progress

if TYPE_CHECKING:
    import arviz as az
    from numpyro.infer import MCMC

    from .models import BayesianModel


@dataclass
class GroupFit:
    """Result of fitting one model to one group.

    Posterior draws are accessible via ``samples`` (raw dict from NumPyro) or
    via ``inference_data`` (ArviZ wrapper used for diagnostics/comparison).

    ``model_kwargs`` holds any extra arguments needed to reconstruct the exact
    :class:`~fairfluids.analysis.bayesian.models.BayesianModel` instance used for
    this fit (e.g. data-anchored reference temperature and density).
    """

    model_name: str
    group: BayesianGroup
    priors: PriorSet
    mcmc: "MCMC"
    inference_data: "az.InferenceData"
    rhat: dict[str, float]
    ess_bulk: dict[str, float]
    ess_tail: dict[str, float]
    num_divergences: int
    # Extra kwargs for get_model(...) to rebuild the fitted model (group anchors).
    model_kwargs: dict[str, Any] = field(default_factory=dict)

    @property
    def group_id(self) -> tuple[Any, ...]:
        return self.group.group_id

    def samples(self) -> dict[str, np.ndarray]:
        return {k: np.asarray(v) for k, v in self.mcmc.get_samples().items()}


@dataclass
class BayesianFit:
    """Collection of per-(model, group) ``GroupFit`` objects from a single workflow run."""

    model_names: tuple[str, ...]
    group_ids: tuple[tuple[Any, ...], ...]
    fits: dict[tuple[str, tuple[Any, ...]], GroupFit] = field(default_factory=dict)

    def get(self, model_name: str, group_id: tuple[Any, ...]) -> GroupFit:
        try:
            return self.fits[(model_name, group_id)]
        except KeyError as exc:
            raise KeyError(
                f"No fit for (model={model_name!r}, group_id={group_id!r}). "
                f"Available models: {self.model_names}; "
                f"available groups: {self.group_ids[:5]}..."
            ) from exc

    def for_model(self, model_name: str) -> dict[tuple[Any, ...], GroupFit]:
        return {gid: self.fits[(model_name, gid)] for gid in self.group_ids if (model_name, gid) in self.fits}

    def for_group(self, group_id: tuple[Any, ...]) -> dict[str, GroupFit]:
        return {m: self.fits[(m, group_id)] for m in self.model_names if (m, group_id) in self.fits}

    def list_groups(self, model_name: str | None = None) -> list[tuple[Any, ...]]:
        """Return the group IDs that have at least one fit (optionally filtered by model)."""
        if model_name is None:
            return list(self.group_ids)
        return [gid for gid in self.group_ids if (model_name, gid) in self.fits]

    def resolve_group(
        self,
        model_name: str,
        selector: Any = None,
    ) -> tuple[Any, ...]:
        """Map a flexible group selector (int / label / dict / tuple / None) to a ``group_id``.

        Delegates to the shared resolver in :mod:`fairfluids.analysis.bayesian.plots`
        so all per-group accessors and plot helpers honour the same rules.
        """
        from .plots import _resolve_group_id

        return _resolve_group_id(self, model_name, selector)

    def posterior_samples(
        self,
        model_name: str,
        group_id: Any = None,
    ) -> dict[str, np.ndarray]:
        """Return raw posterior samples for one ``(model, group)`` fit.

        ``group_id`` accepts the same flexible selectors as
        :meth:`resolve_group`: ``None`` (first available), an integer index,
        a ``group_label`` (or substring), a ``{group_by_key: value}`` dict, the
        raw ``group_id`` tuple, or a :class:`BayesianGroup`.
        """
        gid = self.resolve_group(model_name, group_id)
        return self.get(model_name, gid).samples()

    def inference_data(
        self,
        model_name: str,
        group_id: Any = None,
    ) -> "az.InferenceData":
        """Return the ArviZ ``InferenceData`` for one ``(model, group)`` fit.

        ``group_id`` accepts the same flexible selectors as
        :meth:`resolve_group`.
        """
        gid = self.resolve_group(model_name, group_id)
        return self.get(model_name, gid).inference_data

    def diagnostics(self) -> pd.DataFrame:
        """Return a per-(group, model, parameter) diagnostics DataFrame."""
        rows: list[dict[str, Any]] = []
        for (model_name, group_id), fit in self.fits.items():
            base: dict[str, Any] = {
                "model": model_name,
                "group_label": fit.group.group_label,
                "n_points": fit.group.n_points,
                "num_divergences": fit.num_divergences,
            }
            for col, val in zip(("group_by_" + str(i) for i in range(len(group_id))), group_id):
                base[col] = val
            for param, value in fit.rhat.items():
                row = dict(base)
                row["parameter"] = param
                row["rhat"] = value
                row["ess_bulk"] = fit.ess_bulk.get(param, np.nan)
                row["ess_tail"] = fit.ess_tail.get(param, np.nan)
                rows.append(row)
        return pd.DataFrame(rows)

    def to_fitted_models(
        self,
        *,
        coverage_probability: float = 0.95,
        point_estimate: str = "median",
        include_model_sigma: bool = True,
    ) -> list[Any]:
        """Map every ``(model, group)`` fit onto a ``fairfluids.core.lib.FittedModel``.

        Parameters carry the posterior point estimate, posterior standard
        deviation (standard uncertainty) and an equal-tailed credible interval at
        ``coverage_probability``. See
        :func:`fairfluids.analysis.bayesian.writeback.fit_to_fitted_models`.
        """
        from .writeback import fit_to_fitted_models

        return fit_to_fitted_models(
            self,
            coverage_probability=coverage_probability,
            point_estimate=point_estimate,  # type: ignore[arg-type]
            include_model_sigma=include_model_sigma,
        )

    def to_fairfluids_document(
        self,
        document: Any,
        *,
        fluid_index: int = 0,
        coverage_probability: float = 0.95,
        point_estimate: str = "median",
        include_model_sigma: bool = True,
    ) -> Any:
        """Append the posterior summaries to ``document.fluid[fluid_index].fitted_model``.

        Returns the (mutated) ``document`` for chaining. See
        :func:`fairfluids.analysis.bayesian.writeback.fit_to_fairfluids_document`.
        """
        from .writeback import fit_to_fairfluids_document

        return fit_to_fairfluids_document(
            self,
            document,
            fluid_index=fluid_index,
            coverage_probability=coverage_probability,
            point_estimate=point_estimate,  # type: ignore[arg-type]
            include_model_sigma=include_model_sigma,
        )


def _scalar_diagnostic_dict(diag: "Any") -> dict[str, float]:
    """Extract per-variable diagnostics that are scalars (skip vector deterministics)."""
    out: dict[str, float] = {}
    for var in diag.data_vars:
        values = np.asarray(diag[var].values)
        if values.ndim == 0:
            out[str(var)] = float(values)
    return out


def _ess_dict(idata: "az.InferenceData", method: str) -> dict[str, float]:
    import arviz as az

    ess = az.ess(idata, method=method)
    return _scalar_diagnostic_dict(ess)


def _rhat_dict(idata: "az.InferenceData") -> dict[str, float]:
    import arviz as az

    rhat = az.rhat(idata)
    return _scalar_diagnostic_dict(rhat)


def _count_divergences(idata: "az.InferenceData") -> int:
    sample_stats = getattr(idata, "sample_stats", None)
    if sample_stats is None or "diverging" not in sample_stats:
        return 0
    return int(np.asarray(sample_stats["diverging"]).sum())


def _densify_inference_data(idata: "az.InferenceData") -> "az.InferenceData":
    """Materialise every group's arrays as NumPy in place.

    ``az.from_numpyro`` keeps the ``posterior`` / ``log_likelihood`` values as
    JAX arrays. ArviZ's PSIS-LOO numerics (``arviz_stats``) operate via in-place
    NumPy assignment, which raises ``TypeError`` on immutable JAX arrays. Copying
    each variable to NumPy up front is lossless (these are already-sampled draws)
    and lets LOO/WAIC/compare run regardless of which array backend NumPyro used.
    """
    groups = idata.groups
    if callable(groups):  # arviz < 1.x exposes groups() as a method
        groups = groups()
    for group_name in groups:
        ds = idata[group_name]
        for var_name, da in ds.data_vars.items():
            data = da.data
            if not isinstance(data, np.ndarray):
                ds[var_name] = da.copy(data=np.asarray(data))
    return idata


def _resolve_priors_for(
    models: list["BayesianModel"],
    priors: "PriorSet | Mapping[str, PriorSet]",
) -> dict[str, PriorSet]:
    """Normalize the ``priors`` argument to a ``{model_name: PriorSet}`` mapping.

    Accepts either a single :class:`PriorSet` (applied to every model) or a
    per-model mapping. Each resolved :class:`PriorSet` is validated against the
    model's ``param_names`` so missing priors fail fast.
    """
    if isinstance(priors, PriorSet):
        resolved = {m.name: priors for m in models}
    else:
        missing = [m.name for m in models if m.name not in priors]
        if missing:
            raise KeyError(
                f"priors mapping is missing entries for models: {missing}. "
                f"Provided keys: {sorted(priors)}"
            )
        resolved = {m.name: priors[m.name] for m in models}

    for model in models:
        model.validate_priors(resolved[model.name])
    return resolved


def fit_groups(
    dataset: BayesianDataset,
    models: Iterable["BayesianModel"],
    *,
    priors: "PriorSet | Mapping[str, PriorSet]",
    num_warmup: int = 2000,
    num_samples: int = 2000,
    num_chains: int = 4,
    target_accept_prob: float = 0.95,
    seed: int = 0,
    progress_bar: bool = False,
) -> BayesianFit:
    """Fit each ``(model, group)`` combination with NumPyro NUTS.

    Args:
        dataset: Prepared :class:`BayesianDataset`.
        models: Iterable of :class:`BayesianModel` instances to fit.
        priors: Either a single :class:`PriorSet` applied to every model, or a
            mapping ``{model_name: PriorSet}`` for per-model priors. Each set must
            cover every parameter of the corresponding model.
        num_warmup, num_samples, num_chains, target_accept_prob: Standard NUTS knobs.
        seed: PRNG seed (each ``(model, group)`` gets a distinct fold-in).
        progress_bar: Show one unified tqdm bar across all ``(model, group)`` fits.
            Updates run on the main thread once per completed group (Jupyter-safe).

    Returns:
        :class:`BayesianFit` with one :class:`GroupFit` per model and group.
    """
    import arviz as az
    import jax.random as random
    from numpyro.infer import MCMC, NUTS

    model_list = list(models)
    model_names = tuple(m.name for m in model_list)
    group_ids = tuple(grp.group_id for grp in dataset.groups)

    priors_for = _resolve_priors_for(model_list, priors)

    base_key = random.PRNGKey(seed)
    fit = BayesianFit(model_names=model_names, group_ids=group_ids)

    n_jobs = len(model_list) * len(dataset.groups)
    total_steps = total_mcmc_steps(
        num_jobs=n_jobs,
        num_warmup=num_warmup,
        num_samples=num_samples,
        num_chains=num_chains,
    )
    steps_per_job = num_chains * (num_warmup + num_samples)
    progress_ctx = (
        unified_mcmc_progress(total_steps=total_steps, description="MCMC fit")
        if progress_bar
        else nullcontext()
    )

    with progress_ctx as progress:
        if progress_bar and progress is not None:
            progress.configure_job(steps_per_job=steps_per_job)
        for m_idx, model in enumerate(model_list):
            run_priors = priors_for[model.name]
            for g_idx, group in enumerate(dataset.groups):
                run_model = model.bind_group(group)
                run_key = random.fold_in(random.fold_in(base_key, m_idx + 1), g_idx + 1)
                kernel = NUTS(
                    run_model.numpyro_model,
                    **run_model.nuts_kernel_kwargs(target_accept_prob=target_accept_prob),
                )
                mcmc = MCMC(
                    kernel,
                    num_warmup=num_warmup,
                    num_samples=num_samples,
                    num_chains=num_chains,
                    progress_bar=False,
                )
                mcmc.run(
                    run_key,
                    features=group.features_jax(),
                    observation=group.observation_jax(),
                    observation_uncertainty=group.observation_uncertainty_jax(),
                    priors=run_priors,
                    extra_fields=("energy",),
                )

                # ``log_likelihood=True`` is required so ArviZ can later compute LOO/WAIC.
                idata = _densify_inference_data(az.from_numpyro(mcmc, log_likelihood=True))
                rhat = _rhat_dict(idata)
                ess_bulk = _ess_dict(idata, method="bulk")
                ess_tail = _ess_dict(idata, method="tail")
                divergences = _count_divergences(idata)

                gfit = GroupFit(
                    model_name=model.name,
                    group=group,
                    priors=run_priors,
                    mcmc=mcmc,
                    inference_data=idata,
                    rhat=rhat,
                    ess_bulk=ess_bulk,
                    ess_tail=ess_tail,
                    num_divergences=divergences,
                    model_kwargs=run_model.reconstruction_kwargs(),
                )
                fit.fits[(model.name, group.group_id)] = gfit

                if progress_bar and progress is not None:
                    progress.complete_job(
                        model=model.name,
                        group=str(group.group_label)[:48],
                    )

    return fit


def predict(
    fit: BayesianFit,
    model_name: str,
    features: Mapping[str, np.ndarray],
    *,
    group_id: Any = None,
    quantiles: tuple[float, ...] = (0.05, 0.5, 0.95),
    return_samples: bool = False,
    seed: int = 0,
    observation_uncertainty: np.ndarray | None = None,
) -> dict[str, Any]:
    """Posterior predictive distribution for a single ``(model, group)`` fit on arbitrary inputs.

    Args:
        fit: The :class:`BayesianFit` produced by ``fit_groups``.
        model_name: Which model in the fit to predict with.
        features: Feature arrays keyed by feature name. Must contain every entry
            in the model's ``feature_names``.
        group_id: Flexible group selector (see :meth:`BayesianFit.resolve_group`).
            Default = first fitted group; the group's posterior samples are what
            drives the prediction.
        quantiles: Quantile levels to summarize the predictive distribution.
        return_samples: If True, include the raw draws as ``samples`` (shape
            ``(n_draws, n_points)``).
        seed: PRNG seed for the predictive draws.
        observation_uncertainty: Optional per-point uncertainty to fold into
            the predictive sigma (already on the observation scale).

    Returns:
        Dict with keys ``model``, ``group_id``, ``group_label``, ``mean``,
        ``q{int(q*100):02d}`` for each requested quantile, and optionally
        ``samples``. The arrays have shape ``(n_points,)`` (or ``(n_draws, n_points)``
        for ``samples``).
    """
    import jax.numpy as jnp
    import jax.random as random
    from numpyro.infer import Predictive

    from .models import get_model

    gid = fit.resolve_group(model_name, group_id)
    gfit = fit.get(model_name, gid)
    model = get_model(model_name, **gfit.model_kwargs)

    n_points: int | None = None
    features_jax: dict[str, Any] = {}
    for fname in model.feature_names:
        if fname not in features:
            raise KeyError(
                f"predict() is missing feature {fname!r}. Provided: {list(features)}."
            )
        arr = jnp.asarray(np.asarray(features[fname], dtype=float))
        features_jax[fname] = arr
        if n_points is None:
            n_points = int(arr.shape[0])

    obs_unc = (
        jnp.asarray(np.asarray(observation_uncertainty, dtype=float))
        if observation_uncertainty is not None
        else None
    )

    samples_dict = gfit.mcmc.get_samples()
    predictive = Predictive(model.numpyro_model, samples_dict)
    key = random.fold_in(random.PRNGKey(seed), abs(hash(gid)) % (2**31))
    pp = predictive(
        key,
        features=features_jax,
        observation=None,
        observation_uncertainty=obs_unc,
        priors=gfit.priors,
    )
    obs = np.asarray(pp["obs"])

    out: dict[str, Any] = {
        "model": model_name,
        "group_id": gid,
        "group_label": gfit.group.group_label,
        "mean": obs.mean(axis=0),
    }
    for q in quantiles:
        out[f"q{int(round(q * 100)):02d}"] = np.quantile(obs, q, axis=0)
    if return_samples:
        out["samples"] = obs
    return out


def predict_averaged(
    fit: BayesianFit,
    features: Mapping[str, np.ndarray],
    *,
    weights: Mapping[str, float] | None = None,
    group_id: Any = None,
    quantiles: tuple[float, ...] = (0.05, 0.5, 0.95),
    return_samples: bool = False,
    seed: int = 0,
    observation_uncertainty: np.ndarray | None = None,
) -> dict[str, Any]:
    """Posterior predictive distribution averaged across models with explicit weights.

    The predictive draws from each model are concatenated using their assigned
    weight (proportional sampling). This is the standard way to turn a stacking
    or pseudo-BMA model comparison into a single predictive distribution.

    Args:
        fit: The :class:`BayesianFit` covering every model in ``weights``.
        features: Same as :func:`predict`.
        weights: Mapping ``model_name -> weight``. Must sum to a positive value
            (the function renormalizes). If ``None``, every model in ``fit``
            receives equal weight.
        group_id, quantiles, return_samples, seed, observation_uncertainty:
            See :func:`predict`.
    """
    if weights is None:
        weights = {m: 1.0 for m in fit.model_names}
    if not weights:
        raise ValueError("predict_averaged() requires at least one model weight.")
    total = float(sum(max(0.0, w) for w in weights.values()))
    if total <= 0.0:
        raise ValueError("predict_averaged() requires the sum of weights to be > 0.")

    n_target = 4000  # total draws after weighting
    rng = np.random.default_rng(seed)
    combined: list[np.ndarray] = []
    per_model: dict[str, np.ndarray] = {}
    for m_name, w in weights.items():
        if w <= 0:
            continue
        n_draws = max(1, int(round(n_target * w / total)))
        single = predict(
            fit,
            m_name,
            features,
            group_id=group_id,
            quantiles=quantiles,
            return_samples=True,
            seed=seed,
            observation_uncertainty=observation_uncertainty,
        )
        samples = single["samples"]
        idx = rng.integers(0, samples.shape[0], size=n_draws)
        combined.append(samples[idx])
        per_model[m_name] = samples

    obs = np.concatenate(combined, axis=0)
    out: dict[str, Any] = {
        "weights": {m: w / total for m, w in weights.items()},
        "mean": obs.mean(axis=0),
    }
    for q in quantiles:
        out[f"q{int(round(q * 100)):02d}"] = np.quantile(obs, q, axis=0)
    if return_samples:
        out["samples"] = obs
        out["per_model_samples"] = per_model
    return out


__all__ = [
    "GroupFit",
    "BayesianFit",
    "fit_groups",
    "predict",
    "predict_averaged",
]
