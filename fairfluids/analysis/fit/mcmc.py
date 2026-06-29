"""Bayesian backend for symbolic models — a lazy bridge to NumPyro/JAX.

This module reuses the existing prior primitives from
:mod:`fairfluids.analysis.bayesian.priors` (pure pydantic, cheap to import) but
does **not** touch the Bayesian model registry or its generated models. The mean
function is the model's symbolic ``mean_expr`` compiled to JAX, so NUTS runs on
exactly the same mathematics as the least-squares backend.

JAX and NumPyro are imported lazily inside the functions, so importing this
module (and the whole ``symbolic`` package) never requires the ``[bayesian]``
extra.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

import numpy as np

from ..models.compile import compile_jax
from ..models.model import SymbolicModel
from ..models.resolvers import resolve_constants


def _as_prior_set(priors: Any, model: SymbolicModel):
    """Coerce ``priors`` into a :class:`PriorSet`.

    Accepts an existing ``PriorSet``; or a mapping ``param -> PriorSpec`` where a
    value may be a ``PriorSpec`` instance or a ``{"kind": ...}`` dict. The keys
    ``sigma_scale`` / ``likelihood`` / ``student_t_df`` are pulled out as
    likelihood configuration.
    """
    from pydantic import TypeAdapter

    from fairfluids.analysis.bayesian.priors import PriorSet, PriorSpec

    if priors is None:
        raise ValueError(
            f"Model {model.name!r} needs priors for the Bayesian fit: pass priors=... "
            "or set them on the model."
        )
    if isinstance(priors, PriorSet):
        return priors

    adapter = TypeAdapter(PriorSpec)
    params: dict[str, Any] = {}
    extra: dict[str, Any] = {}
    for key, value in dict(priors).items():
        if key in ("sigma_scale", "likelihood", "student_t_df"):
            extra[key] = value
            continue
        params[key] = adapter.validate_python(value) if isinstance(value, Mapping) else value
    missing = [p for p in model.param_names if p not in params]
    if missing:
        raise ValueError(
            f"Priors for model {model.name!r} are missing parameters {missing}. "
            f"Expected: {list(model.param_names)}."
        )
    return PriorSet(parameters=params, **extra)


def build_numpyro_model(
    model: SymbolicModel,
    features_jax: Mapping[str, Any],
    constants: Mapping[str, float],
    prior_set: Any,
):
    """Return a NumPyro model closure for one group (mean = JAX-compiled ``mean_expr``)."""
    import jax.numpy as jnp
    import numpyro
    import numpyro.distributions as dist

    kernel = compile_jax(model)
    fnames, cnames, pnames = model.features, model.constant_names, model.param_names
    const_vals = [constants[n] for n in cnames]
    feat_vals = [features_jax[n] for n in fnames]

    def numpyro_model(
        observation: Any = None,
        observation_uncertainty: Any = None,
    ) -> None:
        params = {
            p: numpyro.sample(p, prior_set.parameters[p].to_numpyro()) for p in pnames
        }
        mu = kernel(*feat_vals, *const_vals, *[params[p] for p in pnames])
        numpyro.deterministic("mu", mu)
        model_sigma = numpyro.sample("model_sigma", dist.HalfNormal(prior_set.sigma_scale))
        if observation_uncertainty is not None:
            total_sigma = jnp.sqrt(model_sigma**2 + observation_uncertainty**2)
        else:
            total_sigma = model_sigma
        if prior_set.likelihood == "student_t":
            obs_dist = dist.StudentT(prior_set.student_t_df, mu, total_sigma)
        else:
            obs_dist = dist.Normal(mu, total_sigma)
        numpyro.sample("obs", obs_dist, obs=observation)

    return numpyro_model


def fit_mcmc(
    model: SymbolicModel,
    features: Mapping[str, np.ndarray],
    observation: np.ndarray,
    *,
    priors: Any = None,
    observation_uncertainty: Optional[np.ndarray] = None,
    num_warmup: int = 1000,
    num_samples: int = 1000,
    num_chains: int = 2,
    target_accept_prob: float = 0.9,
    seed: int = 0,
):
    """Run NUTS for one group and return the fitted ``numpyro.infer.MCMC`` object.

    ``observation`` is raw (linear); the log transform is applied internally when
    ``model.log_observation`` is True, matching the least-squares backend.
    """
    import jax
    import jax.numpy as jnp
    from numpyro.infer import MCMC, NUTS

    prior_set = _as_prior_set(priors if priors is not None else dict(model.priors), model)

    feats = {n: np.asarray(features[n], dtype=float).ravel() for n in model.features}
    raw_obs = np.asarray(observation, dtype=float).ravel()
    constants = resolve_constants(model.constants, feats, raw_obs)

    if model.log_observation:
        y = np.log(np.clip(raw_obs, 1e-300, None))
        obs_unc = None
        if observation_uncertainty is not None:
            unc = np.asarray(observation_uncertainty, dtype=float).ravel()
            with np.errstate(divide="ignore", invalid="ignore"):
                prop = unc / np.where(raw_obs > 0, raw_obs, np.nan)
            obs_unc = prop if np.any(np.isfinite(prop)) else None
    else:
        y = raw_obs
        obs_unc = (
            np.asarray(observation_uncertainty, dtype=float).ravel()
            if observation_uncertainty is not None
            else None
        )

    features_jax = {n: jnp.asarray(v) for n, v in feats.items()}
    numpyro_model = build_numpyro_model(model, features_jax, constants, prior_set)

    kernel = NUTS(numpyro_model, target_accept_prob=target_accept_prob)
    mcmc = MCMC(
        kernel,
        num_warmup=num_warmup,
        num_samples=num_samples,
        num_chains=num_chains,
        progress_bar=False,
    )
    mcmc.run(
        jax.random.PRNGKey(seed),
        observation=jnp.asarray(y),
        observation_uncertainty=jnp.asarray(obs_unc) if obs_unc is not None else None,
    )
    return mcmc


__all__ = ["build_numpyro_model", "fit_mcmc"]
