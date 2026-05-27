"""Hierarchical (partial-pooling) Bayesian models.

While :class:`fairfluids.analysis.bayesian.models.BayesianModel` fits every
group independently, the classes in this module pool information across groups
through a population-level layer:

    logA[g] ~ Normal(mu_logA, tau_logA)
    Ea[g]   ~ Normal(mu_Ea,   tau_Ea)

This is the cleanest way to make groups with very few data points "borrow
strength" from groups with many points, to detect systematic DOI / composition
biases, and to quantify *how consistent* a parameter is across groups
(``tau_*`` directly reports the between-group variability).

The entry point is :func:`fit_hierarchical` (or
:meth:`BayesianWorkflow.fit_hierarchical`); the returned
:class:`HierarchicalFit` mirrors the per-group :class:`BayesianFit` API where
it makes sense (posterior samples, diagnostics, prediction) and adds a few
hierarchy-specific helpers (population samples, shrinkage plots).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Iterable, Mapping

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict

from .data import BayesianDataset, BayesianGroup
from .priors import (
    HalfNormalPriorSpec,
    NormalPriorSpec,
    PriorPreset,
)

if TYPE_CHECKING:
    import arviz as az
    import jax
    from numpyro.infer import MCMC


R_GAS: float = 8.314


# ---------------------------------------------------------------------------
# Base class + registry
# ---------------------------------------------------------------------------


class _HierarchicalRegistry:
    """Module-private registry of concrete hierarchical models."""

    def __init__(self) -> None:
        self._entries: dict[str, type["HierarchicalBayesianModel"]] = {}

    def register(self, cls: type["HierarchicalBayesianModel"]) -> None:
        name = cls.name
        if not name:
            return
        if name in self._entries and self._entries[name] is not cls:
            raise ValueError(
                f"HierarchicalBayesianModel name collision: {name!r} already "
                f"registered by {self._entries[name].__qualname__}; cannot register "
                f"{cls.__qualname__}"
            )
        self._entries[name] = cls

    def get(self, name: str) -> type["HierarchicalBayesianModel"]:
        if name not in self._entries:
            raise KeyError(
                f"No hierarchical model registered under {name!r}. "
                f"Available: {sorted(self._entries)}"
            )
        return self._entries[name]

    def names(self) -> list[str]:
        return sorted(self._entries)


HierarchicalRegistry = _HierarchicalRegistry()


class HierarchicalBayesianModel(BaseModel):
    """Abstract Pydantic base for hierarchical (partial-pooling) models.

    Subclasses declare two parameter levels:

    * :attr:`population_param_names` — hyperparameters describing the
      population, e.g. ``("mu_logA", "tau_logA", "mu_Ea", "tau_Ea")``.
    * :attr:`local_param_names` — per-group parameters that the population
      distributes, e.g. ``("logA", "Ea")``.

    Pooling is implemented with a non-centered parameterisation
    (``param[g] = mu + tau * z[g]``) so NUTS does not struggle with the
    funnel geometry that often plagues hierarchical models.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    name: ClassVar[str] = ""
    feature_names: ClassVar[tuple[str, ...]] = ()
    population_param_names: ClassVar[tuple[str, ...]] = ()
    local_param_names: ClassVar[tuple[str, ...]] = ()
    prior_presets: ClassVar[dict[str, PriorPreset]] = {}
    log_observation: ClassVar[bool] = True

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "name", ""):
            return
        HierarchicalRegistry.register(cls)

    def get_preset(self, preset: str) -> PriorPreset:
        if preset not in self.prior_presets:
            raise KeyError(
                f"Hierarchical model {self.name!r} has no preset {preset!r}. "
                f"Available: {sorted(self.prior_presets)}"
            )
        return self.prior_presets[preset]

    @classmethod
    def register_prior_preset(
        cls, preset: PriorPreset, *, overwrite: bool = False
    ) -> None:
        """Attach a user-defined preset; must cover every population parameter."""
        missing = [
            n for n in cls.population_param_names if n not in preset.parameters
        ]
        if missing:
            raise ValueError(
                f"PriorPreset {preset.name!r} is missing population parameters for "
                f"{cls.name!r}: {missing}. Expected: {list(cls.population_param_names)}."
            )
        if preset.name in cls.prior_presets and not overwrite:
            raise ValueError(
                f"Prior preset {preset.name!r} is already registered for "
                f"{cls.name!r}. Pass overwrite=True to replace it."
            )
        cls.prior_presets[preset.name] = preset

    # -- Subclass hook ---------------------------------------------------------

    def mean(
        self,
        features: Mapping[str, "jax.Array"],
        local_params: Mapping[str, "jax.Array"],
    ) -> "jax.Array":
        """Return ``E[obs]`` given per-point feature arrays and per-point local parameters.

        Subclasses should index ``local_params`` by point — i.e. each entry
        already broadcast to the full ``n_points``-long vector via the
        ``group_index`` lookup that :meth:`numpyro_model` does for them.
        """
        raise NotImplementedError

    # -- Generic NumPyro model -------------------------------------------------

    def numpyro_model(
        self,
        features: Mapping[str, "jax.Array"],
        group_index: "jax.Array",
        n_groups: int,
        observation: "jax.Array | None" = None,
        observation_uncertainty: "jax.Array | None" = None,
        preset_name: str = "balanced",
    ) -> None:
        """Generic hierarchical NumPyro model with non-centered local parameters."""
        import jax.numpy as jnp
        import numpyro
        import numpyro.distributions as dist

        preset = self.get_preset(preset_name)

        # Sample population-level hyperparameters from the preset.
        hyper: dict[str, "jax.Array"] = {}
        for pname in self.population_param_names:
            spec = preset.parameters.get(pname)
            if spec is None:
                raise KeyError(
                    f"Prior preset {preset.name!r} for hierarchical model "
                    f"{self.name!r} is missing parameter {pname!r}."
                )
            hyper[pname] = numpyro.sample(pname, spec.to_numpyro())

        # Non-centered local parameters per group.
        local_per_group: dict[str, "jax.Array"] = {}
        with numpyro.plate("groups", n_groups):
            for lname in self.local_param_names:
                mu_name = f"mu_{lname}"
                tau_name = f"tau_{lname}"
                if mu_name not in hyper or tau_name not in hyper:
                    raise KeyError(
                        f"Hierarchical model {self.name!r} expects '{mu_name}' and "
                        f"'{tau_name}' in the preset for the local parameter '{lname}'."
                    )
                z = numpyro.sample(f"z_{lname}", dist.Normal(0.0, 1.0))
                local_per_group[lname] = numpyro.deterministic(
                    lname, hyper[mu_name] + hyper[tau_name] * z
                )

        # Broadcast per-group params to per-point via group_index.
        local_per_point = {
            lname: local_per_group[lname][group_index]
            for lname in self.local_param_names
        }
        mu = self.mean(features, local_per_point)

        model_sigma = numpyro.sample(
            "model_sigma", dist.HalfNormal(preset.sigma_scale)
        )
        if observation_uncertainty is not None:
            total_sigma = jnp.sqrt(model_sigma**2 + observation_uncertainty**2)
        else:
            total_sigma = model_sigma

        if preset.likelihood == "student_t":
            obs_dist = dist.StudentT(preset.student_t_df, mu, total_sigma)
        else:
            obs_dist = dist.Normal(mu, total_sigma)
        numpyro.sample("obs", obs_dist, obs=observation)


# ---------------------------------------------------------------------------
# Concrete hierarchical models
# ---------------------------------------------------------------------------


class HierarchicalArrhenius(HierarchicalBayesianModel):
    """Hierarchical Arrhenius: ``ln(eta_i) = logA[g(i)] + Ea[g(i)] / (R * T_i)``.

    The population distributes both ``logA`` and ``Ea`` so groups (DOIs,
    compositions, ...) share information; the per-group parameters are sampled
    non-centered to keep the geometry well-conditioned.
    """

    name: ClassVar[str] = "hierarchical_arrhenius"
    feature_names: ClassVar[tuple[str, ...]] = ("temperature",)
    population_param_names: ClassVar[tuple[str, ...]] = (
        "mu_logA",
        "tau_logA",
        "mu_Ea",
        "tau_Ea",
    )
    local_param_names: ClassVar[tuple[str, ...]] = ("logA", "Ea")
    log_observation: ClassVar[bool] = True
    prior_presets: ClassVar[dict[str, PriorPreset]] = {
        "balanced": PriorPreset(
            name="balanced",
            parameters={
                "mu_logA": NormalPriorSpec(loc=-20.0, scale=3.0),
                "tau_logA": HalfNormalPriorSpec(scale=2.0),
                "mu_Ea": NormalPriorSpec(loc=30000.0, scale=10000.0),
                "tau_Ea": HalfNormalPriorSpec(scale=5000.0),
            },
            sigma_scale=0.1,
        ),
        "tight": PriorPreset(
            name="tight",
            parameters={
                "mu_logA": NormalPriorSpec(loc=-20.0, scale=1.5),
                "tau_logA": HalfNormalPriorSpec(scale=1.0),
                "mu_Ea": NormalPriorSpec(loc=30000.0, scale=5000.0),
                "tau_Ea": HalfNormalPriorSpec(scale=2500.0),
            },
            sigma_scale=0.05,
        ),
    }

    def mean(self, features, local_params):
        T = features["temperature"]
        return local_params["logA"] + local_params["Ea"] / (R_GAS * T)


# ---------------------------------------------------------------------------
# Fit container
# ---------------------------------------------------------------------------


@dataclass
class HierarchicalFit:
    """Result of fitting one :class:`HierarchicalBayesianModel` over a whole dataset."""

    model_name: str
    model: HierarchicalBayesianModel
    dataset: BayesianDataset
    preset: str
    mcmc: "MCMC"
    inference_data: "az.InferenceData"
    group_index_map: dict[tuple[Any, ...], int]
    rhat: dict[str, float]
    ess_bulk: dict[str, float]
    ess_tail: dict[str, float]
    num_divergences: int

    @property
    def group_ids(self) -> list[tuple[Any, ...]]:
        return list(self.group_index_map)

    def _all_samples(self) -> dict[str, np.ndarray]:
        return {k: np.asarray(v) for k, v in self.mcmc.get_samples().items()}

    def population_posterior(self) -> dict[str, np.ndarray]:
        """Return raw samples for the population hyperparameters only."""
        samples = self._all_samples()
        return {
            name: samples[name]
            for name in self.model.population_param_names
            if name in samples
        }

    def group_posterior(self, group_id: Any) -> dict[str, np.ndarray]:
        """Return the per-group posterior for the requested group.

        ``group_id`` accepts the same selectors as
        :meth:`BayesianFit.resolve_group`.
        """
        idx = self._resolve_index(group_id)
        samples = self._all_samples()
        out: dict[str, np.ndarray] = {}
        for lname in self.model.local_param_names:
            arr = samples.get(lname)
            if arr is None:
                continue
            out[lname] = arr[:, idx]
        return out

    def posterior_samples(self, group_id: Any = None) -> dict[str, np.ndarray]:
        """Convenience that mirrors :meth:`BayesianFit.posterior_samples`.

        Returns hyperparameters + the local parameters for ``group_id`` (default
        = the first group) sliced from the (n_draws, n_groups) arrays.
        """
        pop = self.population_posterior()
        if group_id is None:
            group_id = self.group_ids[0]
        local = self.group_posterior(group_id)
        merged = {**pop, **local}
        samples = self._all_samples()
        if "model_sigma" in samples:
            merged["model_sigma"] = samples["model_sigma"]
        return merged

    def diagnostics(self) -> pd.DataFrame:
        """R-hat / ESS / divergence summary across all parameters."""
        rows: list[dict[str, Any]] = []
        for param, rhat in self.rhat.items():
            rows.append({
                "parameter": param,
                "rhat": rhat,
                "ess_bulk": self.ess_bulk.get(param, np.nan),
                "ess_tail": self.ess_tail.get(param, np.nan),
                "num_divergences": self.num_divergences,
            })
        return pd.DataFrame(rows)

    def predict(
        self,
        features: Mapping[str, np.ndarray],
        *,
        group_id: Any,
        quantiles: tuple[float, ...] = (0.05, 0.5, 0.95),
        seed: int = 0,
        return_samples: bool = False,
    ) -> dict[str, Any]:
        """Posterior predictive distribution for one specific group on new inputs."""
        idx = self._resolve_index(group_id)
        samples = self._all_samples()
        local_arrays: dict[str, np.ndarray] = {}
        for lname in self.model.local_param_names:
            local_arrays[lname] = samples[lname][:, idx]
        return _predict_with_local(
            self.model,
            preset=self.preset,
            features=features,
            local_samples=local_arrays,
            quantiles=quantiles,
            seed=seed,
            return_samples=return_samples,
        )

    def predict_population(
        self,
        features: Mapping[str, np.ndarray],
        *,
        quantiles: tuple[float, ...] = (0.05, 0.5, 0.95),
        seed: int = 0,
        return_samples: bool = False,
    ) -> dict[str, Any]:
        """Predict for a brand-new group drawn from the population.

        Uses the posterior of ``mu_*`` and ``tau_*`` to draw a fresh local
        parameter set per posterior sample, then propagates through the mean
        function. This is the *predictive distribution for a new group* —
        the appropriate uncertainty band when extrapolating to compositions /
        DOIs you have not measured.
        """
        samples = self._all_samples()
        n_draws = next(iter(samples.values())).shape[0]
        rng = np.random.default_rng(seed)
        local_arrays: dict[str, np.ndarray] = {}
        for lname in self.model.local_param_names:
            mu = samples[f"mu_{lname}"]
            tau = samples[f"tau_{lname}"]
            local_arrays[lname] = mu + tau * rng.standard_normal(n_draws)
        return _predict_with_local(
            self.model,
            preset=self.preset,
            features=features,
            local_samples=local_arrays,
            quantiles=quantiles,
            seed=seed,
            return_samples=return_samples,
        )

    def parameter_summary(
        self,
        quantiles: tuple[float, float] = (0.05, 0.95),
    ) -> pd.DataFrame:
        """Long-format DataFrame with median + CI per (parameter, group) pair."""
        samples = self._all_samples()
        q_low, q_high = quantiles
        rows: list[dict[str, Any]] = []
        for pname in self.model.population_param_names:
            arr = samples.get(pname)
            if arr is None:
                continue
            rows.append({
                "scope": "population",
                "parameter": pname,
                "group_label": None,
                "group_id": None,
                "median": float(np.median(arr)),
                f"q{int(round(q_low*100)):02d}": float(np.quantile(arr, q_low)),
                f"q{int(round(q_high*100)):02d}": float(np.quantile(arr, q_high)),
            })
        for gid, idx in self.group_index_map.items():
            grp = self._group(gid)
            for lname in self.model.local_param_names:
                arr = samples.get(lname)
                if arr is None:
                    continue
                slc = arr[:, idx]
                rows.append({
                    "scope": "group",
                    "parameter": lname,
                    "group_label": grp.group_label,
                    "group_id": gid,
                    "median": float(np.median(slc)),
                    f"q{int(round(q_low*100)):02d}": float(np.quantile(slc, q_low)),
                    f"q{int(round(q_high*100)):02d}": float(np.quantile(slc, q_high)),
                })
        return pd.DataFrame(rows)

    # -- helpers ---------------------------------------------------------------

    def _resolve_index(self, selector: Any) -> int:
        if selector is None:
            return 0
        if isinstance(selector, int) and not isinstance(selector, bool):
            return selector if selector >= 0 else len(self.group_ids) + selector
        if isinstance(selector, tuple) and selector in self.group_index_map:
            return self.group_index_map[selector]
        if isinstance(selector, BayesianGroup):
            return self.group_index_map[selector.group_id]
        if isinstance(selector, str):
            for gid in self.group_ids:
                if self._group(gid).group_label == selector:
                    return self.group_index_map[gid]
            partial = [
                gid for gid in self.group_ids
                if selector in self._group(gid).group_label
            ]
            if len(partial) == 1:
                return self.group_index_map[partial[0]]
            raise KeyError(
                f"group label {selector!r} ambiguous or not found among "
                f"{[self._group(g).group_label for g in self.group_ids]}"
            )
        if isinstance(selector, dict):
            matches = []
            for gid in self.group_ids:
                grp = self._group(gid)
                gb = grp.metadata.get("group_by", {}) or {}
                if all((gb.get(k) == v) or (grp.metadata.get(k) == v) for k, v in selector.items()):
                    matches.append(gid)
            if len(matches) == 1:
                return self.group_index_map[matches[0]]
            raise KeyError(f"dict selector {selector!r} did not uniquely match a group.")
        raise TypeError(f"Cannot resolve group selector {selector!r}")

    def _group(self, gid: tuple[Any, ...]) -> BayesianGroup:
        for grp in self.dataset.groups:
            if grp.group_id == gid:
                return grp
        raise KeyError(f"group_id {gid!r} not in dataset")


# ---------------------------------------------------------------------------
# Fitting entrypoint
# ---------------------------------------------------------------------------


def _concatenate_dataset(
    dataset: BayesianDataset,
) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray, np.ndarray | None, dict[tuple[Any, ...], int]]:
    """Concatenate every group's data into long flat arrays plus a group_index."""
    feature_arrays: dict[str, list[np.ndarray]] = {f: [] for f in dataset.feature_names}
    obs: list[np.ndarray] = []
    obs_unc: list[np.ndarray] = []
    group_index: list[np.ndarray] = []
    has_unc = all(g.observation_uncertainty is not None for g in dataset.groups)

    gid_map: dict[tuple[Any, ...], int] = {}
    for i, grp in enumerate(dataset.groups):
        gid_map[grp.group_id] = i
        n = int(grp.observation.shape[0])
        for fname in dataset.feature_names:
            feature_arrays[fname].append(np.asarray(grp.features[fname], dtype=float))
        obs.append(np.asarray(grp.observation, dtype=float))
        if has_unc:
            obs_unc.append(np.asarray(grp.observation_uncertainty, dtype=float))
        group_index.append(np.full(n, i, dtype=np.int32))

    features = {f: np.concatenate(v) for f, v in feature_arrays.items()}
    return (
        features,
        np.concatenate(obs),
        np.concatenate(group_index),
        np.concatenate(obs_unc) if has_unc else None,
        gid_map,
    )


def fit_hierarchical(
    dataset: BayesianDataset,
    model: HierarchicalBayesianModel,
    *,
    preset: str | PriorPreset = "balanced",
    num_warmup: int = 2000,
    num_samples: int = 2000,
    num_chains: int = 4,
    target_accept_prob: float = 0.95,
    seed: int = 0,
    progress_bar: bool = False,
) -> HierarchicalFit:
    """Fit a hierarchical model over every group of ``dataset`` in one MCMC run."""
    import arviz as az
    import jax.numpy as jnp
    import jax.random as random
    from numpyro.infer import MCMC, NUTS

    if isinstance(preset, PriorPreset):
        type(model).register_prior_preset(preset, overwrite=True)
        preset_name = preset.name
    else:
        preset_name = preset

    features_np, obs_np, gindex_np, obs_unc_np, gid_map = _concatenate_dataset(dataset)
    features_jax = {f: jnp.asarray(v) for f, v in features_np.items()}
    obs_jax = jnp.asarray(obs_np)
    gindex_jax = jnp.asarray(gindex_np)
    obs_unc_jax = jnp.asarray(obs_unc_np) if obs_unc_np is not None else None

    kernel = NUTS(model.numpyro_model, target_accept_prob=target_accept_prob)
    mcmc = MCMC(
        kernel,
        num_warmup=num_warmup,
        num_samples=num_samples,
        num_chains=num_chains,
        progress_bar=progress_bar,
    )
    mcmc.run(
        random.PRNGKey(seed),
        features=features_jax,
        group_index=gindex_jax,
        n_groups=len(gid_map),
        observation=obs_jax,
        observation_uncertainty=obs_unc_jax,
        preset_name=preset_name,
        extra_fields=("energy",),
    )

    idata = az.from_numpyro(mcmc, log_likelihood=True)
    rhat = _rhat(idata)
    ess_bulk = _ess(idata, "bulk")
    ess_tail = _ess(idata, "tail")
    divergences = _count_divergences(idata)

    return HierarchicalFit(
        model_name=model.name,
        model=model,
        dataset=dataset,
        preset=preset_name,
        mcmc=mcmc,
        inference_data=idata,
        group_index_map=gid_map,
        rhat=rhat,
        ess_bulk=ess_bulk,
        ess_tail=ess_tail,
        num_divergences=divergences,
    )


def _rhat(idata: "az.InferenceData") -> dict[str, float]:
    import arviz as az

    r = az.rhat(idata)
    return _summarize_diag(r)


def _ess(idata: "az.InferenceData", method: str) -> dict[str, float]:
    import arviz as az

    return _summarize_diag(az.ess(idata, method=method))


def _summarize_diag(diag: Any) -> dict[str, float]:
    out: dict[str, float] = {}
    for var in diag.data_vars:
        arr = np.asarray(diag[var].values)
        if arr.ndim == 0:
            out[str(var)] = float(arr)
            continue
        finite = arr[np.isfinite(arr)]
        out[str(var)] = float(finite.mean()) if finite.size > 0 else float("nan")
    return out


def _count_divergences(idata: "az.InferenceData") -> int:
    ss = getattr(idata, "sample_stats", None)
    if ss is None or "diverging" not in ss:
        return 0
    return int(np.asarray(ss["diverging"]).sum())


def _predict_with_local(
    model: HierarchicalBayesianModel,
    *,
    preset: str,
    features: Mapping[str, np.ndarray],
    local_samples: Mapping[str, np.ndarray],
    quantiles: tuple[float, ...],
    seed: int,
    return_samples: bool,
) -> dict[str, Any]:
    """Compute posterior predictive draws given pre-resolved local parameter samples."""
    import jax.numpy as jnp
    import jax.random as random

    feats = {f: np.asarray(features[f], dtype=float) for f in model.feature_names}
    n_points = int(next(iter(feats.values())).shape[0])
    feats_jax = {f: jnp.asarray(v) for f, v in feats.items()}

    p_preset = model.get_preset(preset)
    n_draws = next(iter(local_samples.values())).shape[0]
    key = random.PRNGKey(seed)

    # The mean is deterministic given local parameters; we add Gaussian/StudentT noise from sigma_scale.
    sigma_draw = float(p_preset.sigma_scale) * np.abs(np.random.default_rng(seed).standard_normal(n_draws))

    mean_draws = np.empty((n_draws, n_points), dtype=float)
    for d in range(n_draws):
        local_d = {k: jnp.asarray(np.array([local_samples[k][d]])[..., None]) for k in local_samples}
        # Reshape: each local param is a scalar for this draw, broadcast over n_points.
        local_broadcast = {k: jnp.full((n_points,), float(local_samples[k][d])) for k in local_samples}
        mean_draws[d] = np.asarray(model.mean(feats_jax, local_broadcast))

    rng = np.random.default_rng(seed + 1)
    noise = rng.standard_normal((n_draws, n_points)) * sigma_draw[:, None]
    obs = mean_draws + noise

    out: dict[str, Any] = {
        "model": model.name,
        "preset": preset,
        "mean": obs.mean(axis=0),
    }
    for q in quantiles:
        out[f"q{int(round(q * 100)):02d}"] = np.quantile(obs, q, axis=0)
    if return_samples:
        out["samples"] = obs
    return out


def list_hierarchical_models() -> list[str]:
    """Return the names of all currently registered hierarchical models."""
    return HierarchicalRegistry.names()


def get_hierarchical_model(name: str) -> HierarchicalBayesianModel:
    """Instantiate a hierarchical model by name."""
    cls = HierarchicalRegistry.get(name)
    return cls()


__all__ = [
    "HierarchicalBayesianModel",
    "HierarchicalArrhenius",
    "HierarchicalFit",
    "HierarchicalRegistry",
    "fit_hierarchical",
    "get_hierarchical_model",
    "list_hierarchical_models",
]
