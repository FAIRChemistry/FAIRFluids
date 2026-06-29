"""Prior specification primitives for Bayesian property models.

A :class:`PriorSet` bundles the per-parameter prior specifications together with
the scale of the model-level Gaussian noise (``model_sigma``) and the
observation likelihood configuration. It is supplied explicitly at fit time
(there are no built-in presets): the caller defines the priors for every model
parameter when calling :func:`fairfluids.analysis.bayesian.fit_groups`.

Each prior specification is a small Pydantic model exposing a ``to_numpyro()``
factory that returns a ``numpyro.distributions.Distribution``. The supported
families are :class:`UniformPriorSpec`, :class:`NormalPriorSpec`,
:class:`HalfNormalPriorSpec`, :class:`LogNormalPriorSpec` and
:class:`TruncatedNormalPriorSpec`. The :data:`PriorSpec` type alias is a
discriminated union over these, keyed by the ``kind`` field — Pydantic uses it
to deserialize ``PriorSet`` instances from JSON without ambiguity.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Literal, Mapping, Union

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

if TYPE_CHECKING:
    import numpyro.distributions as dist

    from .models import BayesianModel


# ---------------------------------------------------------------------------
# Prior spec primitives
# ---------------------------------------------------------------------------


class _PriorSpecBase(BaseModel):
    """Common configuration for all prior spec variants.

    Each subclass declares a ``kind`` :class:`typing.Literal` field that doubles
    as the discriminator in :data:`PriorSpec`. Subclasses must implement
    :meth:`to_numpyro` (used at fit time) and :meth:`support` (used for prior
    plotting and as an approximate ``(low, high)`` window for diagnostics).
    """

    model_config = ConfigDict(frozen=True)

    def to_numpyro(self) -> "dist.Distribution":
        raise NotImplementedError

    def support(self, n_sigma: float = 4.0) -> tuple[float, float]:
        """Finite range covering the high-density mass of the prior.

        Used by plot helpers that need an x-axis for an otherwise unbounded
        distribution. The default ``n_sigma=4`` covers ~99.99 % of a Normal.
        """
        raise NotImplementedError

    def describe(self) -> str:
        """Single-line human description (e.g. ``"Normal(loc=0.0, scale=1.0)"``)."""
        params = ", ".join(
            f"{k}={v}" for k, v in self.model_dump(exclude={"kind"}).items()
        )
        kind = getattr(self, "kind", type(self).__name__).replace("_", " ").title().replace(" ", "")
        return f"{kind}({params})"


class UniformPriorSpec(_PriorSpecBase):
    """Uniform prior on the closed interval ``[low, high]``."""

    kind: Literal["uniform"] = "uniform"
    low: float
    high: float

    @model_validator(mode="after")
    def _check_interval(self) -> "UniformPriorSpec":
        if not (self.high > self.low):
            raise ValueError(
                f"UniformPriorSpec requires high > low, got low={self.low}, high={self.high}"
            )
        return self

    def to_numpyro(self) -> "dist.Distribution":
        import numpyro.distributions as dist

        return dist.Uniform(self.low, self.high)

    def support(self, n_sigma: float = 4.0) -> tuple[float, float]:
        return self.low, self.high


class NormalPriorSpec(_PriorSpecBase):
    """Normal (Gaussian) prior with mean ``loc`` and standard deviation ``scale``."""

    kind: Literal["normal"] = "normal"
    loc: float
    scale: float = Field(gt=0.0)

    def to_numpyro(self) -> "dist.Distribution":
        import numpyro.distributions as dist

        return dist.Normal(self.loc, self.scale)

    def support(self, n_sigma: float = 4.0) -> tuple[float, float]:
        return self.loc - n_sigma * self.scale, self.loc + n_sigma * self.scale


class HalfNormalPriorSpec(_PriorSpecBase):
    """Half-Normal prior on ``[0, infinity)`` with scale ``scale``.

    Useful for strictly-positive parameters such as activation energies or
    variance scales.
    """

    kind: Literal["half_normal"] = "half_normal"
    scale: float = Field(gt=0.0)

    def to_numpyro(self) -> "dist.Distribution":
        import numpyro.distributions as dist

        return dist.HalfNormal(self.scale)

    def support(self, n_sigma: float = 4.0) -> tuple[float, float]:
        return 0.0, n_sigma * self.scale


class LogNormalPriorSpec(_PriorSpecBase):
    """LogNormal prior — the natural log of the parameter is ``Normal(loc, scale)``.

    Best suited for parameters that are strictly positive and span several
    orders of magnitude.
    """

    kind: Literal["log_normal"] = "log_normal"
    loc: float
    scale: float = Field(gt=0.0)

    def to_numpyro(self) -> "dist.Distribution":
        import numpyro.distributions as dist

        return dist.LogNormal(self.loc, self.scale)

    def support(self, n_sigma: float = 4.0) -> tuple[float, float]:
        lo = math.exp(self.loc - n_sigma * self.scale)
        hi = math.exp(self.loc + n_sigma * self.scale)
        return lo, hi


class TruncatedNormalPriorSpec(_PriorSpecBase):
    """Normal prior truncated to ``[low, high]`` (either bound may be ``None`` for one-sided)."""

    kind: Literal["truncated_normal"] = "truncated_normal"
    loc: float
    scale: float = Field(gt=0.0)
    low: float | None = None
    high: float | None = None

    @model_validator(mode="after")
    def _check_bounds(self) -> "TruncatedNormalPriorSpec":
        if self.low is not None and self.high is not None and self.high <= self.low:
            raise ValueError(
                "TruncatedNormalPriorSpec requires high > low when both bounds are given, "
                f"got low={self.low}, high={self.high}"
            )
        return self

    def to_numpyro(self) -> "dist.Distribution":
        import numpyro.distributions as dist

        return dist.TruncatedNormal(
            loc=self.loc, scale=self.scale, low=self.low, high=self.high
        )

    def support(self, n_sigma: float = 4.0) -> tuple[float, float]:
        lo = self.low if self.low is not None else self.loc - n_sigma * self.scale
        hi = self.high if self.high is not None else self.loc + n_sigma * self.scale
        return float(lo), float(hi)


PriorSpec = Annotated[
    Union[
        UniformPriorSpec,
        NormalPriorSpec,
        HalfNormalPriorSpec,
        LogNormalPriorSpec,
        TruncatedNormalPriorSpec,
    ],
    Field(discriminator="kind"),
]
"""Discriminated union over all supported prior families (keyed on ``kind``)."""


# ---------------------------------------------------------------------------
# Prior sets (supplied at fit time)
# ---------------------------------------------------------------------------


class PriorSet(BaseModel):
    """A set of per-parameter priors plus the observation-likelihood configuration.

    A :class:`PriorSet` is passed explicitly when fitting a model; there are no
    named, pre-registered presets. The caller is responsible for covering every
    sampling parameter of the model in :attr:`parameters`.

    Attributes:
        parameters: Mapping ``parameter_name -> PriorSpec`` covering every
            sampling parameter of the model except ``model_sigma``.
        sigma_scale: Scale of the ``HalfNormal`` prior placed on ``model_sigma``.
        likelihood: Observation likelihood family. ``"normal"`` (default) is
            sensitive to outliers; ``"student_t"`` uses a heavy-tailed
            distribution with ``student_t_df`` degrees of freedom (small df
            = heavier tails = more robust to outliers).
        student_t_df: Degrees of freedom for the Student-t likelihood. Only
            used when ``likelihood == "student_t"``. Typical values: 3-7
            (smaller = more robust, larger = closer to Normal).
    """

    model_config = ConfigDict(frozen=True)

    parameters: dict[str, PriorSpec]
    sigma_scale: float = Field(0.1, gt=0.0)
    likelihood: Literal["normal", "student_t"] = "normal"
    student_t_df: float = Field(4.0, gt=2.0)

    def parameter_bounds(self, parameter: str) -> tuple[float, float]:
        """Return a ``(low, high)`` plotting window for ``parameter``.

        For :class:`UniformPriorSpec` this is the exact interval, for unbounded
        distributions it falls back to ``spec.support()`` (a ``4 sigma`` band).
        """
        spec = self.parameters.get(parameter)
        if spec is None:
            raise KeyError(
                f"PriorSet has no entry for parameter {parameter!r}. "
                f"Available: {sorted(self.parameters)}"
            )
        return spec.support()


def prior_predictive_quantiles(
    model: "BayesianModel",
    features: Mapping[str, np.ndarray],
    *,
    priors: "PriorSet",
    n_samples: int = 3000,
    quantiles: tuple[float, ...] = (0.01, 0.05, 0.5, 0.95, 0.99),
    observation_uncertainty: np.ndarray | None = None,
    seed: int = 0,
) -> dict[str, Any]:
    """Run a NumPyro prior predictive simulation and return summary quantiles.

    Args:
        model: A registered :class:`BayesianModel` instance.
        features: Feature arrays indexed by feature name (matching ``model.feature_names``).
        priors: The :class:`PriorSet` to draw from.
        n_samples: Number of prior predictive draws.
        quantiles: Quantile levels to summarize.
        observation_uncertainty: Optional per-point observation sigma (already on
            the same scale as ``observation``).
        seed: PRNG seed.

    Returns:
        Dict containing the raw prior predictive draws (``samples``) and the
        requested ``quantiles`` evaluated globally across draws and observation
        points.
    """
    import jax
    import jax.numpy as jnp
    from numpyro.infer import Predictive

    feature_arrays = {name: jnp.asarray(np.asarray(arr)) for name, arr in features.items()}
    obs_unc = (
        jnp.asarray(np.asarray(observation_uncertainty))
        if observation_uncertainty is not None
        else None
    )

    predictive = Predictive(
        model.numpyro_model,
        num_samples=n_samples,
        return_sites=("obs", *model.param_names),
    )
    samples = predictive(
        jax.random.PRNGKey(seed),
        features=feature_arrays,
        observation=None,
        observation_uncertainty=obs_unc,
        priors=priors,
    )
    obs = np.asarray(samples["obs"])
    flat = obs.reshape(-1)
    q = {f"q{int(q_ * 100):02d}": float(np.quantile(flat, q_)) for q_ in quantiles}
    return {
        "model": model.name,
        "n_samples": n_samples,
        "n_points": int(obs.shape[-1]),
        **q,
        "samples": obs,
    }


def sample_prior(
    spec: PriorSpec,
    *,
    n_samples: int = 4000,
    seed: int = 0,
) -> np.ndarray:
    """Draw ``n_samples`` from a single :data:`PriorSpec` and return them as a numpy array.

    This is the workhorse for prior-vs-posterior overlays: it sidesteps the
    full ``numpyro_model`` and just samples the chosen distribution directly.
    """
    import jax
    import jax.random as random

    dist_ = spec.to_numpyro()
    key = random.PRNGKey(seed)
    samples = dist_.sample(key, sample_shape=(n_samples,))
    return np.asarray(jax.device_get(samples))


__all__ = [
    "UniformPriorSpec",
    "NormalPriorSpec",
    "HalfNormalPriorSpec",
    "LogNormalPriorSpec",
    "TruncatedNormalPriorSpec",
    "PriorSpec",
    "PriorSet",
    "prior_predictive_quantiles",
    "sample_prior",
]
