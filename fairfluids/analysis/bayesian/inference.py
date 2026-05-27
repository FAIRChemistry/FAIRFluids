"""MCMC inference for :class:`BayesianModel` instances on grouped data.

The public entry point is :func:`fit_groups`, which runs NUTS once per
``(model, group)`` combination and packages the results into a
:class:`BayesianFit` container. Posterior samples are exposed both as the
underlying NumPyro ``MCMC`` object (for cheap posterior predictive draws) and
as an :class:`arviz.InferenceData` (for diagnostics and comparison).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Iterable, Mapping

import numpy as np
import pandas as pd

from .data import BayesianDataset, BayesianGroup
from .priors import PriorPreset

if TYPE_CHECKING:
    import arviz as az
    from numpyro.infer import MCMC

    from .models import BayesianModel


@dataclass
class GroupFit:
    """Result of fitting one model to one group.

    Posterior draws are accessible via ``samples`` (raw dict from NumPyro) or
    via ``inference_data`` (ArviZ wrapper used for diagnostics/comparison).
    """

    model_name: str
    group: BayesianGroup
    preset: str
    mcmc: "MCMC"
    inference_data: "az.InferenceData"
    rhat: dict[str, float]
    ess_bulk: dict[str, float]
    ess_tail: dict[str, float]
    num_divergences: int

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


def _ess_dict(idata: "az.InferenceData", method: str) -> dict[str, float]:
    import arviz as az

    ess = az.ess(idata, method=method)
    return {str(var): float(ess[var].values) for var in ess.data_vars}


def _rhat_dict(idata: "az.InferenceData") -> dict[str, float]:
    import arviz as az

    rhat = az.rhat(idata)
    return {str(var): float(rhat[var].values) for var in rhat.data_vars}


def _count_divergences(idata: "az.InferenceData") -> int:
    sample_stats = getattr(idata, "sample_stats", None)
    if sample_stats is None or "diverging" not in sample_stats:
        return 0
    return int(np.asarray(sample_stats["diverging"]).sum())


PresetSpec = "str | PriorPreset | Mapping[str, str | PriorPreset]"


def _resolve_preset_for(
    models: list["BayesianModel"],
    preset: "str | PriorPreset | Mapping[str, str | PriorPreset]",
) -> dict[str, str]:
    """Normalize the ``preset`` argument to a ``{model_name: preset_name}`` mapping.

    Any :class:`PriorPreset` objects encountered are auto-registered on the
    corresponding model class (with ``overwrite=True``) so subsequent calls can
    reference them by name. This is what enables the ``prior_preset=my_preset``
    convenience syntax in the workflow.
    """
    if isinstance(preset, PriorPreset):
        resolved: dict[str, str] = {}
        for m in models:
            type(m).register_prior_preset(preset, overwrite=True)
            resolved[m.name] = preset.name
        return resolved
    if isinstance(preset, str):
        return {m.name: preset for m in models}

    # Per-model mapping; values can be either str or PriorPreset.
    missing = [m.name for m in models if m.name not in preset]
    if missing:
        raise KeyError(
            f"preset mapping is missing entries for models: {missing}. "
            f"Provided keys: {sorted(preset)}"
        )
    resolved = {}
    by_name = {m.name: m for m in models}
    for model_name, spec in preset.items():
        if model_name not in by_name:
            continue
        model = by_name[model_name]
        if isinstance(spec, PriorPreset):
            type(model).register_prior_preset(spec, overwrite=True)
            resolved[model_name] = spec.name
        else:
            resolved[model_name] = str(spec)
    return resolved


def fit_groups(
    dataset: BayesianDataset,
    models: Iterable["BayesianModel"],
    *,
    preset: "str | PriorPreset | Mapping[str, str | PriorPreset]" = "balanced",
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
        preset: Prior preset selector. Accepts any of
            (1) a string referring to a registered preset (applied to every model),
            (2) a :class:`PriorPreset` object (auto-registered on every model),
            (3) a mapping ``{model_name: str | PriorPreset}`` for per-model overrides.
        num_warmup, num_samples, num_chains, target_accept_prob: Standard NUTS knobs.
        seed: PRNG seed (each ``(model, group)`` gets a distinct fold-in).
        progress_bar: Forwarded to the NumPyro ``MCMC`` constructor.

    Returns:
        :class:`BayesianFit` with one :class:`GroupFit` per model and group.
    """
    import arviz as az
    import jax.random as random
    from numpyro.infer import MCMC, NUTS

    model_list = list(models)
    model_names = tuple(m.name for m in model_list)
    group_ids = tuple(grp.group_id for grp in dataset.groups)

    preset_for = _resolve_preset_for(model_list, preset)

    base_key = random.PRNGKey(seed)
    fit = BayesianFit(model_names=model_names, group_ids=group_ids)

    for m_idx, model in enumerate(model_list):
        preset_name = preset_for[model.name]
        for g_idx, group in enumerate(dataset.groups):
            run_key = random.fold_in(random.fold_in(base_key, m_idx + 1), g_idx + 1)
            kernel = NUTS(model.numpyro_model, target_accept_prob=target_accept_prob)
            mcmc = MCMC(
                kernel,
                num_warmup=num_warmup,
                num_samples=num_samples,
                num_chains=num_chains,
                progress_bar=progress_bar,
            )
            mcmc.run(
                run_key,
                features=group.features_jax(),
                observation=group.observation_jax(),
                observation_uncertainty=group.observation_uncertainty_jax(),
                preset_name=preset_name,
                extra_fields=("energy",),
            )

            # ``log_likelihood=True`` is required so ArviZ can later compute LOO/WAIC.
            idata = az.from_numpyro(mcmc, log_likelihood=True)
            rhat = _rhat_dict(idata)
            ess_bulk = _ess_dict(idata, method="bulk")
            ess_tail = _ess_dict(idata, method="tail")
            divergences = _count_divergences(idata)

            gfit = GroupFit(
                model_name=model.name,
                group=group,
                preset=preset_name,
                mcmc=mcmc,
                inference_data=idata,
                rhat=rhat,
                ess_bulk=ess_bulk,
                ess_tail=ess_tail,
                num_divergences=divergences,
            )
            fit.fits[(model.name, group.group_id)] = gfit

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
    model = get_model(model_name)

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
        preset_name=gfit.preset,
    )
    obs = np.asarray(pp["obs"])

    out: dict[str, Any] = {
        "model": model_name,
        "group_id": gid,
        "group_label": gfit.group.group_label,
        "preset": gfit.preset,
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
