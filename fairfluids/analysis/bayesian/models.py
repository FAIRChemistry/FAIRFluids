"""Base class and registry for Bayesian models in ``fairfluids.analysis.bayesian``.

Each model is a Pydantic v2 subclass of :class:`BayesianModel`. Subclasses
declare their parameter names, feature names and property as class-level
metadata, and implement :meth:`mean`. The base class supplies a generic NumPyro
model that samples parameters from a caller-supplied :class:`PriorSet`,
evaluates ``mean``, and adds Gaussian observation noise combined with optional
measurement uncertainty.

The registry is populated automatically via ``__init_subclass__`` and accessed
through :func:`get_model` / :func:`list_models`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Literal, Mapping

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from .data import BayesianGroup
from .priors import HalfNormal, Prior, PriorSet, PriorSpec

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


class _Parameter:
    """Catalax-style handle for one model parameter, exposing a settable ``prior``.

    Obtained via ``model.parameters.<name>`` or ``model.parameters[name]``. Reading
    / writing :attr:`prior` reads / writes ``model.priors[name]`` in place.
    """

    __slots__ = ("_model", "_name")

    def __init__(self, model: "BayesianModel", name: str) -> None:
        self._model = model
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def prior(self) -> Prior | None:
        return self._model.priors.get(self._name)

    @prior.setter
    def prior(self, value: Prior) -> None:
        if not isinstance(value, Prior):
            raise TypeError(
                f"parameter {self._name!r}.prior must be a Prior (Normal, Uniform, "
                f"HalfNormal, ...), got {type(value).__name__}."
            )
        self._model.priors[self._name] = value

    def __repr__(self) -> str:
        return f"Parameter({self._name!r}, prior={self.prior!r})"


class _ParametersView:
    """Mapping-like accessor over a model's parameters (``model.parameters``)."""

    __slots__ = ("_model",)

    def __init__(self, model: "BayesianModel") -> None:
        self._model = model

    def __getitem__(self, name: str) -> _Parameter:
        if name not in self._model.param_names:
            raise KeyError(
                f"{self._model.name!r} has no parameter {name!r}. "
                f"Parameters: {list(self._model.param_names)}."
            )
        return _Parameter(self._model, name)

    def __getattr__(self, name: str) -> _Parameter:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(str(exc)) from exc

    def __iter__(self):
        return (self[n] for n in self._model.param_names)

    def __len__(self) -> int:
        return len(self._model.param_names)

    def __repr__(self) -> str:
        return f"ParametersView({list(self._model.param_names)})"


class BayesianModel(BaseModel):
    """Abstract Pydantic v2 base for Bayesian regression models.

    Concrete subclasses override the class-level metadata (:attr:`name`,
    :attr:`property_name`, :attr:`feature_names`, :attr:`param_names`) and
    implement :meth:`mean`. The default :meth:`numpyro_model` handles parameter
    sampling, noise composition and the observation site so subclasses normally
    do not need to touch it.

    Priors live *on the model* (Catalax-style): set them via
    ``model.parameters.<name>.prior = Normal(...)`` or :meth:`set_priors`, tune the
    observation-noise prior through :attr:`error`, and the likelihood family via
    :attr:`likelihood`. The fitting / workflow machinery reads these directly, so
    no separate prior argument is threaded through ``fit``.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=False)

    # -- instance-level prior configuration (Catalax-style) --------------------
    priors: dict[str, PriorSpec] = Field(default_factory=dict)
    """Per-parameter priors, keyed by parameter name."""
    sigma_scale: float = Field(default=0.1, gt=0.0)
    """Scale of the ``HalfNormal`` prior on the model observation noise (``model_sigma``)."""
    likelihood: Literal["normal", "student_t"] = "normal"
    """Observation likelihood family (``student_t`` is outlier-robust)."""
    student_t_df: float = Field(default=4.0, gt=2.0)
    """Degrees of freedom for the Student-t likelihood (used when ``likelihood='student_t'``)."""

    name: ClassVar[str] = ""
    property_name: ClassVar[str] = ""
    """The physical property the model describes (e.g. ``"viscosity"`` or ``"density"``)."""
    feature_names: ClassVar[tuple[str, ...]] = ()
    param_names: ClassVar[tuple[str, ...]] = ()
    log_observation: ClassVar[bool] = True
    """If True, the observation is interpreted as the natural log of the property."""

    property_display_labels: ClassVar[dict[str, tuple[str, str]]] = {
        "density": (
            r"$\rho$ / kg m$^{-3}$",
            r"$\ln(\rho\,/\,\mathrm{kg\,m^{-3}})$",
        ),
        "viscosity": (
            r"$\eta$ / Pa$\cdot$s",
            r"$\ln(\eta\,/\,\mathrm{Pa\cdot s})$",
        ),
    }
    """(linear SI unit, log-likelihood unit) labels for :meth:`observation_axis_label`."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "name", ""):
            return
        ModelRegistry.register(cls)

    # -- Catalax-style prior configuration -------------------------------------

    @property
    def parameters(self) -> _ParametersView:
        """Accessor for per-parameter priors: ``model.parameters.<name>.prior = Normal(...)``."""
        return _ParametersView(self)

    @property
    def error(self) -> HalfNormal:
        """The ``HalfNormal`` prior on the observation noise ``model_sigma``.

        Assign a :class:`~fairfluids.analysis.bayesian.priors.HalfNormal` to change
        it: ``model.error = HalfNormal(sigma=0.05)``.
        """
        return HalfNormal(sigma=self.sigma_scale)

    @error.setter
    def error(self, value: HalfNormal) -> None:
        if not isinstance(value, HalfNormal):
            raise TypeError(
                f"model.error must be a HalfNormal prior, got {type(value).__name__}."
            )
        self.sigma_scale = value.sigma

    def set_priors(self, **priors: Prior) -> "BayesianModel":
        """Set one or more parameter priors and return ``self`` (chainable).

        Example::

            get_model("arrhenius").set_priors(
                logA=Normal(-20, 2), Ea=Normal(50000, 20000),
            )
        """
        unknown = [p for p in priors if p not in self.param_names]
        if unknown:
            raise KeyError(
                f"Model {self.name!r} has no parameter(s) {unknown}. "
                f"Parameters: {list(self.param_names)}."
            )
        for pname, spec in priors.items():
            if not isinstance(spec, Prior):
                raise TypeError(
                    f"Prior for {pname!r} must be a Prior instance, got {type(spec).__name__}."
                )
            self.priors[pname] = spec
        return self

    def prior_set(self) -> PriorSet:
        """Bundle the model's configured priors into a :class:`PriorSet`.

        This is the internal representation consumed by the NumPyro model,
        prior-predictive simulation and plotting. Raises if any parameter is
        still missing a prior.
        """
        self.ensure_priors()
        return PriorSet(
            parameters=dict(self.priors),
            sigma_scale=self.sigma_scale,
            likelihood=self.likelihood,
            student_t_df=self.student_t_df,
        )

    def ensure_priors(self) -> None:
        """Raise if any parameter is missing a prior (configured via the model)."""
        missing = [name for name in self.param_names if name not in self.priors]
        if missing:
            raise ValueError(
                f"Model {self.name!r} is missing priors for parameters {missing}. "
                f"Set them via model.parameters.<name>.prior = ... or "
                f"model.set_priors({missing[0]}=...). Parameters: {list(self.param_names)}."
            )

    def validate_priors(self, priors: PriorSet | None = None) -> None:
        """Raise if ``priors`` (or the model's own priors) miss any parameter."""
        if priors is None:
            self.ensure_priors()
            return
        missing = [name for name in self.param_names if name not in priors.parameters]
        if missing:
            raise ValueError(
                f"PriorSet is missing required parameters for model {self.name!r}: "
                f"{missing}. Expected: {list(self.param_names)}."
            )

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

    def resolve_plot_scale(
        self, plot_scale: str | None = None
    ) -> Literal["property", "likelihood"]:
        """Map a plot-scale selector to ``property`` (SI) or ``likelihood``.

        When ``plot_scale`` is omitted, log-likelihood models default to
        ``property`` so predictive plots show linear SI units while MCMC still
        runs on the transformed observation scale.
        """
        if plot_scale is None:
            return "property" if self.log_observation else "likelihood"
        key = plot_scale.lower().replace("-", "_").replace(" ", "_")
        if key in {"property", "linear", "raw", "si"}:
            return "property"
        if key in {"likelihood", "log", "transformed", "model"}:
            return "likelihood"
        raise ValueError(
            f"Unknown plot_scale={plot_scale!r}. "
            "Use 'property' (linear SI), 'likelihood' (model scale), or None."
        )

    def transform_mean_for_display(
        self,
        values: np.ndarray,
        *,
        plot_scale: str | None = None,
    ) -> np.ndarray:
        """Map latent means ``mu`` from the likelihood scale to plot coordinates."""
        arr = np.asarray(values, dtype=float)
        if self.resolve_plot_scale(plot_scale) == "property" and self.log_observation:
            return np.exp(arr)
        return arr

    def observation_for_display(
        self,
        group: BayesianGroup,
        *,
        plot_scale: str | None = None,
    ) -> np.ndarray:
        """Observation values aligned with :meth:`transform_mean_for_display`."""
        if self.resolve_plot_scale(plot_scale) == "property":
            return np.asarray(group.raw_observation, dtype=float)
        return np.asarray(group.observation, dtype=float)

    def observation_axis_label(self, *, plot_scale: str | None = None) -> str:
        """Y-axis label for predictive and overview plots."""
        scale = self.resolve_plot_scale(plot_scale)
        labels = self.property_display_labels.get(self.property_name)
        if labels is not None:
            linear_lbl, log_lbl = labels
            return log_lbl if scale == "likelihood" else linear_lbl
        if scale == "likelihood" and self.log_observation:
            return "ln(observation)"
        return self.property_name or "observation"

    def nuts_kernel_kwargs(self, *, target_accept_prob: float) -> dict[str, Any]:
        """Extra keyword arguments forwarded to :class:`numpyro.infer.NUTS`.

        Override on models with difficult geometry (e.g. correlated density
        coefficients) to set ``init_strategy`` or model-specific accept rates.
        """
        return {"target_accept_prob": target_accept_prob}

    def bind_group(self, group: BayesianGroup) -> BayesianModel:
        """Return a model instance configured for ``group`` (default: ``self``).

        Override when the likelihood depends on group-specific constants (e.g. a
        reference temperature anchored to the group's data). The default
        implementation is identity so existing models need no changes.
        """
        return self

    def reconstruction_kwargs(self) -> dict[str, Any]:
        """Keyword arguments for :func:`get_model` to rebuild this configured instance.

        Used after MCMC so :func:`fairfluids.analysis.bayesian.inference.predict`
        and plotting helpers can reconstruct the same model state as during the
        fit. The default is an empty mapping (class-level metadata is enough).
        """
        return {}

    def sample_parameters(
        self,
        priors: PriorSet | None,
        features: Mapping[str, "jax.Array"],
    ) -> dict[str, "jax.Array"]:
        """Sample the model's parameters from the supplied :class:`PriorSet`.

        The default implementation pulls each entry in :attr:`param_names` from
        ``priors.parameters`` and converts the typed :data:`PriorSpec` to a
        NumPyro distribution via ``spec.to_numpyro()`` — so any registered family
        (Uniform, Normal, HalfNormal, LogNormal, TruncatedNormal, ...) is
        supported out of the box. Override this for feature-aware bounds
        (see :mod:`fairfluids.analysis.bayesian.bridge`, which clips the VFT
        ``T0`` prior below the minimum observed temperature).
        """
        import numpyro

        if priors is None:
            priors = self.prior_set()
        params: dict[str, "jax.Array"] = {}
        for pname in self.param_names:
            spec = priors.parameters.get(pname)
            if spec is None:
                raise KeyError(
                    f"PriorSet for model {self.name!r} is missing parameter {pname!r}."
                )
            params[pname] = numpyro.sample(pname, spec.to_numpyro())
        return params

    def numpyro_model(
        self,
        features: Mapping[str, "jax.Array"],
        observation: "jax.Array | None" = None,
        observation_uncertainty: "jax.Array | None" = None,
        *,
        priors: PriorSet | None = None,
    ) -> None:
        """Generic NumPyro model used for both prior predictive and MCMC.

        The signature matches what NumPyro's ``Predictive`` / ``MCMC`` expect when
        called via keyword arguments. ``priors`` provides the per-parameter prior
        specs, the ``model_sigma`` scale and the observation likelihood; when
        omitted it defaults to the model's own configured priors
        (:meth:`prior_set`).
        """
        import jax.numpy as jnp
        import numpyro
        import numpyro.distributions as dist

        if priors is None:
            priors = self.prior_set()
        params = self.sample_parameters(priors, features)
        mu = self.mean(features, params)
        numpyro.deterministic("mu", mu)
        model_sigma = numpyro.sample("model_sigma", dist.HalfNormal(priors.sigma_scale))
        if observation_uncertainty is not None:
            total_sigma = jnp.sqrt(model_sigma**2 + observation_uncertainty**2)
        else:
            total_sigma = model_sigma

        if priors.likelihood == "student_t":
            obs_dist = dist.StudentT(priors.student_t_df, mu, total_sigma)
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
