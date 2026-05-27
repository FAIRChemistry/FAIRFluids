"""Base class and registry for Bayesian models in ``fairfluids.analysis.bayesian``.

Each model is a Pydantic v2 subclass of :class:`BayesianModel`. Subclasses
declare their parameter names, feature names and ``PriorPreset`` library as
class-level metadata, and implement :meth:`mean`. The base class supplies a
generic NumPyro model that samples parameters from the active preset, evaluates
``mean``, and adds Gaussian observation noise combined with optional
measurement uncertainty.

The registry is populated automatically via ``__init_subclass__`` and accessed
through :func:`get_model` / :func:`list_models`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Mapping

from pydantic import BaseModel, ConfigDict

from .priors import PriorPreset

if TYPE_CHECKING:
    import jax


class _ModelRegistry:
    """Module-private registry of concrete ``BayesianModel`` subclasses."""

    def __init__(self) -> None:
        self._entries: dict[str, type["BayesianModel"]] = {}

    def register(self, cls: type["BayesianModel"]) -> None:
        name = cls.name
        if not name:
            return
        if name in self._entries and self._entries[name] is not cls:
            raise ValueError(
                f"BayesianModel name collision: {name!r} already registered "
                f"by {self._entries[name].__qualname__}; cannot register {cls.__qualname__}"
            )
        self._entries[name] = cls

    def get(self, name: str) -> type["BayesianModel"]:
        if name not in self._entries:
            raise KeyError(
                f"No Bayesian model registered under {name!r}. "
                f"Available: {sorted(self._entries)}"
            )
        return self._entries[name]

    def names(self) -> list[str]:
        return sorted(self._entries)


ModelRegistry = _ModelRegistry()


class BayesianModel(BaseModel):
    """Abstract Pydantic v2 base for Bayesian regression models.

    Concrete subclasses override the class-level metadata (:attr:`name`,
    :attr:`feature_names`, :attr:`param_names`, :attr:`prior_presets`) and
    implement :meth:`mean`. The default :meth:`numpyro_model` handles parameter
    sampling, noise composition and the observation site so subclasses normally
    do not need to touch it.

    Instances are immutable Pydantic v2 objects so they can safely be shared
    across groups and fits.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    name: ClassVar[str] = ""
    feature_names: ClassVar[tuple[str, ...]] = ()
    param_names: ClassVar[tuple[str, ...]] = ()
    prior_presets: ClassVar[dict[str, PriorPreset]] = {}
    log_observation: ClassVar[bool] = True
    """If True, the observation is interpreted as the natural log of the property."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "name", ""):
            return
        ModelRegistry.register(cls)

    def get_preset(self, preset: str) -> PriorPreset:
        if preset not in self.prior_presets:
            raise KeyError(
                f"Model {self.name!r} has no prior preset {preset!r}. "
                f"Available: {sorted(self.prior_presets)}"
            )
        return self.prior_presets[preset]

    @classmethod
    def register_prior_preset(
        cls,
        preset: PriorPreset,
        *,
        overwrite: bool = False,
    ) -> None:
        """Attach a user-defined :class:`PriorPreset` to this model class.

        The preset must cover every entry in :attr:`param_names`. Once registered,
        the preset is selectable by name via the ``prior_preset`` argument of
        :class:`BayesianWorkflow` or :func:`fit_groups`.

        Args:
            preset: User-defined preset. ``preset.name`` is used as the registry key.
            overwrite: When False (default), raise if a preset with the same name
                already exists; when True, replace it.
        """
        missing = [name for name in cls.param_names if name not in preset.parameters]
        if missing:
            raise ValueError(
                f"PriorPreset {preset.name!r} is missing required parameters for model "
                f"{cls.name!r}: {missing}. Expected: {list(cls.param_names)}."
            )
        if preset.name in cls.prior_presets and not overwrite:
            raise ValueError(
                f"Prior preset {preset.name!r} is already registered for model {cls.name!r}. "
                f"Pass overwrite=True to replace it."
            )
        cls.prior_presets[preset.name] = preset

    def mean(
        self,
        features: Mapping[str, "jax.Array"],
        params: Mapping[str, "jax.Array"],
    ) -> "jax.Array":
        """Return the model's deterministic mean on the (transformed) observation scale.

        If :attr:`log_observation` is True, this should produce ``E[ln(property)]``;
        otherwise it should produce ``E[property]`` directly.
        """
        raise NotImplementedError

    def sample_parameters(
        self,
        preset: PriorPreset,
        features: Mapping[str, "jax.Array"],
    ) -> dict[str, "jax.Array"]:
        """Sample the model's parameters from the active preset.

        The default implementation pulls each entry in :attr:`param_names` from
        ``preset.parameters`` and converts the typed :data:`PriorSpec` to a
        NumPyro distribution via ``spec.to_numpyro()`` — so any registered family
        (Uniform, Normal, HalfNormal, LogNormal, TruncatedNormal, ...) is
        supported out of the box. Override this for feature-aware bounds
        (see :class:`fairfluids.analysis.bayesian.models_builtin.VFT`).
        """
        import numpyro

        params: dict[str, "jax.Array"] = {}
        for pname in self.param_names:
            spec = preset.parameters.get(pname)
            if spec is None:
                raise KeyError(
                    f"Prior preset {preset.name!r} for model {self.name!r} "
                    f"is missing parameter {pname!r}."
                )
            params[pname] = numpyro.sample(pname, spec.to_numpyro())
        return params

    def numpyro_model(
        self,
        features: Mapping[str, "jax.Array"],
        observation: "jax.Array | None" = None,
        observation_uncertainty: "jax.Array | None" = None,
        preset_name: str = "balanced",
    ) -> None:
        """Generic NumPyro model used for both prior predictive and MCMC.

        The signature matches what NumPyro's ``Predictive`` / ``MCMC`` expect when
        called via keyword arguments. ``preset_name`` selects which preset's bounds
        and ``sigma_scale`` are used.
        """
        import jax.numpy as jnp
        import numpyro
        import numpyro.distributions as dist

        preset = self.get_preset(preset_name)
        params = self.sample_parameters(preset, features)
        mu = self.mean(features, params)
        model_sigma = numpyro.sample("model_sigma", dist.HalfNormal(preset.sigma_scale))
        if observation_uncertainty is not None:
            total_sigma = jnp.sqrt(model_sigma**2 + observation_uncertainty**2)
        else:
            total_sigma = model_sigma

        if preset.likelihood == "student_t":
            obs_dist = dist.StudentT(preset.student_t_df, mu, total_sigma)
        else:
            obs_dist = dist.Normal(mu, total_sigma)
        numpyro.sample("obs", obs_dist, obs=observation)


def get_model(name: str, **kwargs: Any) -> BayesianModel:
    """Instantiate a registered model by name.

    Extra ``kwargs`` are forwarded to the Pydantic ``__init__`` (most models take
    none beyond the immutable class-level metadata).
    """
    cls = ModelRegistry.get(name)
    return cls(**kwargs)


def list_models() -> list[str]:
    """Return the names of all currently registered Bayesian models."""
    return ModelRegistry.names()


__all__ = [
    "BayesianModel",
    "ModelRegistry",
    "get_model",
    "list_models",
]
