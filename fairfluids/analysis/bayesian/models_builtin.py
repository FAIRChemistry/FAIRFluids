"""Built-in Bayesian viscosity models.

Four models with three prior presets each are registered on import:

- :class:`Arrhenius` — ``ln(eta) = logA + Ea / (R * T)``
- :class:`VFT` — ``ln(eta) = A + B / (T - T0)`` (Vogel-Fulcher-Tammann)
- :class:`Litovitz` — ``ln(eta) = a + b * T^{-3}``
- :class:`LitovitzExtended` — ``ln(eta) = a + b * T^{-n}``

Prior bounds are taken from the original notebook workflow ``PRIOR_CANDIDATES``
and exposed as ``conservative``/``balanced``/``flexible`` presets.

Adding a new model is a matter of subclassing :class:`BayesianModel`, declaring
its class-level metadata and implementing :meth:`BayesianModel.mean`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Mapping

from .models import BayesianModel
from .priors import PriorPreset, UniformPriorSpec

if TYPE_CHECKING:
    import jax


R_GAS: float = 8.314
"""Ideal gas constant ``R`` in J / (mol * K) used by the Arrhenius mean."""


def _preset(
    name: str,
    parameters: dict[str, tuple[float, float]],
    sigma_scale: float,
) -> PriorPreset:
    return PriorPreset(
        name=name,
        parameters={
            pname: UniformPriorSpec(low=low, high=high)
            for pname, (low, high) in parameters.items()
        },
        sigma_scale=sigma_scale,
    )


class Arrhenius(BayesianModel):
    """Arrhenius viscosity model: ``ln(eta) = logA + Ea / (R * T)``."""

    name: ClassVar[str] = "arrhenius"
    feature_names: ClassVar[tuple[str, ...]] = ("temperature",)
    param_names: ClassVar[tuple[str, ...]] = ("logA", "Ea")
    log_observation: ClassVar[bool] = True
    prior_presets: ClassVar[dict[str, PriorPreset]] = {
        "conservative": _preset(
            "conservative",
            {"logA": (-20.0, -10.0), "Ea": (10000.0, 55000.0)},
            sigma_scale=0.1,
        ),
        "balanced": _preset(
            "balanced",
            {"logA": (-24.0, -10.0), "Ea": (7000.0, 60000.0)},
            sigma_scale=0.1,
        ),
        "flexible": _preset(
            "flexible",
            {"logA": (-28.0, -10.0), "Ea": (5000.0, 70000.0)},
            sigma_scale=0.1,
        ),
    }

    def mean(
        self,
        features: Mapping[str, "jax.Array"],
        params: Mapping[str, "jax.Array"],
    ) -> "jax.Array":
        T = features["temperature"]
        return params["logA"] + params["Ea"] / (R_GAS * T)


class VFT(BayesianModel):
    """Vogel-Fulcher-Tammann model: ``ln(eta) = A + B / (T - T0)``.

    ``T0`` is constrained to be strictly below the minimum temperature observed
    in the group (with a 5 K safety margin) to keep the equation numerically stable.
    """

    name: ClassVar[str] = "vft"
    feature_names: ClassVar[tuple[str, ...]] = ("temperature",)
    param_names: ClassVar[tuple[str, ...]] = ("A", "B", "T0")
    log_observation: ClassVar[bool] = True
    prior_presets: ClassVar[dict[str, PriorPreset]] = {
        "conservative": _preset(
            "conservative",
            {
                "A": (-7.0, -2.0),
                "B": (300.0, 600.0),
                "T0": (130.0, 220.0),
            },
            sigma_scale=0.05,
        ),
        "balanced": _preset(
            "balanced",
            {
                "A": (-8.0, 0.0),
                "B": (300.0, 1000.0),
                "T0": (110.0, 215.0),
            },
            sigma_scale=0.10,
        ),
        "flexible": _preset(
            "flexible",
            {
                "A": (-18.0, -5.0),
                "B": (200.0, 1400.0),
                "T0": (100.0, 230.0),
            },
            sigma_scale=0.10,
        ),
    }

    def sample_parameters(
        self,
        preset: PriorPreset,
        features: Mapping[str, "jax.Array"],
    ) -> dict[str, "jax.Array"]:
        import jax.numpy as jnp
        import numpyro
        import numpyro.distributions as dist

        from .priors import UniformPriorSpec

        T = features["temperature"]
        t_min = jnp.min(T)

        a_spec = preset.parameters["A"]
        b_spec = preset.parameters["B"]
        t0_spec = preset.parameters["T0"]

        # A and B are sampled directly from whatever distribution the user picked.
        A = numpyro.sample("A", a_spec.to_numpyro())
        B = numpyro.sample("B", b_spec.to_numpyro())

        # T0 needs to stay below T_min - 5 K for numerical stability. We can only
        # apply the data-dependent clip cleanly when the user picked a Uniform
        # preset; for other families we trust the user's prior as-is.
        if isinstance(t0_spec, UniformPriorSpec):
            t0_upper = jnp.minimum(t0_spec.high, t_min - 5.0)
            t0_lower = jnp.minimum(t0_spec.low, t0_upper - 1.0)
            T0 = numpyro.sample("T0", dist.Uniform(t0_lower, t0_upper))
        else:
            T0 = numpyro.sample("T0", t0_spec.to_numpyro())
        return {"A": A, "B": B, "T0": T0}

    def mean(
        self,
        features: Mapping[str, "jax.Array"],
        params: Mapping[str, "jax.Array"],
    ) -> "jax.Array":
        T = features["temperature"]
        return params["A"] + params["B"] / (T - params["T0"])


class Litovitz(BayesianModel):
    """Litovitz model: ``ln(eta) = a + b * T^{-3}``."""

    name: ClassVar[str] = "litovitz"
    feature_names: ClassVar[tuple[str, ...]] = ("temperature",)
    param_names: ClassVar[tuple[str, ...]] = ("a", "b")
    log_observation: ClassVar[bool] = True
    prior_presets: ClassVar[dict[str, PriorPreset]] = {
        "conservative": _preset(
            "conservative",
            {"a": (-12.0, 2.0), "b": (1.0e7, 3.0e8)},
            sigma_scale=0.05,
        ),
        "balanced": _preset(
            "balanced",
            {"a": (-15.0, 4.0), "b": (1.0e6, 5.0e8)},
            sigma_scale=0.10,
        ),
        "flexible": _preset(
            "flexible",
            {"a": (-20.0, 8.0), "b": (-1.0e8, 1.0e9)},
            sigma_scale=0.10,
        ),
    }

    def mean(
        self,
        features: Mapping[str, "jax.Array"],
        params: Mapping[str, "jax.Array"],
    ) -> "jax.Array":
        T = features["temperature"]
        return params["a"] + params["b"] * (T ** -3)


class LitovitzExtended(BayesianModel):
    """Extended Litovitz model with floating temperature exponent: ``ln(eta) = a + b * T^{-n}``."""

    name: ClassVar[str] = "litovitz_extended"
    feature_names: ClassVar[tuple[str, ...]] = ("temperature",)
    param_names: ClassVar[tuple[str, ...]] = ("a", "b", "n")
    log_observation: ClassVar[bool] = True
    prior_presets: ClassVar[dict[str, PriorPreset]] = {
        "conservative": _preset(
            "conservative",
            {"a": (-12.0, 2.0), "b": (1.0e7, 3.0e8), "n": (2.8, 3.7)},
            sigma_scale=0.05,
        ),
        "balanced": _preset(
            "balanced",
            {"a": (-15.0, 4.0), "b": (1.0e6, 5.0e8), "n": (1.5, 4.0)},
            sigma_scale=0.10,
        ),
        "flexible": _preset(
            "flexible",
            {"a": (-20.0, 8.0), "b": (-1.0e8, 1.0e9), "n": (1.5, 4.0)},
            sigma_scale=0.10,
        ),
    }

    def mean(
        self,
        features: Mapping[str, "jax.Array"],
        params: Mapping[str, "jax.Array"],
    ) -> "jax.Array":
        import jax.numpy as jnp

        T = features["temperature"]
        return params["a"] + params["b"] * jnp.power(T, -params["n"])


__all__ = [
    "Arrhenius",
    "VFT",
    "Litovitz",
    "LitovitzExtended",
    "R_GAS",
]
