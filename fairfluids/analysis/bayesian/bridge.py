"""Synthesise NumPyro :class:`BayesianModel` subclasses from the symbolic store.

Like :mod:`fairfluids.analysis.regression.bridge`, this module removes the need
for a codegen pipeline: instead of rendering one ``BayesianModel`` subclass per
model into ``_generated/`` (and hand-writing the reparametrised density variants
in ``models_builtin``), it builds them *at import time* from the single source of
truth — the :class:`~fairfluids.analysis.models.SymbolicModel` instances in
:data:`fairfluids.analysis.models.registry`.

A single generic base, :class:`_SymbolicBayesianModel`, implements every hook the
inference / workflow / plotting machinery relies on:

* :meth:`mean` evaluates the model's shared JAX kernel (``compile_jax``), so the
  Bayesian mean is byte-for-byte the same mathematics as the least-squares mean;
* :meth:`bind_group` resolves the model's *constants* from a group's data using
  the very same :func:`resolve_constants` machinery as the frequentist backend —
  this is what lets the data-anchored density variants (``T0 = mean(T)``,
  ``rho0 = rho(T0)``) work without any bespoke subclass;
* :meth:`sample_parameters` honours ``metadata.feature_dependent_bounds`` to clip
  feature-dependent priors (the VFT ``T0 < min(T)`` trick);
* :meth:`nuts_kernel_kwargs` honours ``metadata.nuts``.

One concrete subclass is created per symbolic model via :func:`build_model`; each
sets only the class-level metadata (``name``, ``param_names`` ...) and registers
itself with the Bayesian :data:`ModelRegistry` through ``__init_subclass__``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Mapping, Optional

import numpy as np

from ..models import registry as _model_registry
from ..models.compile import compile_jax
from ..models.model import SymbolicModel
from ..models.resolvers import FixedConstant, resolve_constants
from .data import BayesianGroup
from .models import BayesianModel, ModelRegistry

if TYPE_CHECKING:  # pragma: no cover
    import jax

    from .priors import PriorSet


R_GAS: float = 8.314
"""Ideal gas constant ``R`` in J / (mol * K). Used by the inverse-temperature
plotting axis (see :mod:`fairfluids.analysis.bayesian.plots`)."""


def _feature_aliases(model: SymbolicModel) -> dict[str, str]:
    """Map each symbolic feature name to the group column it is stored under."""
    meta = model.metadata if isinstance(model.metadata, Mapping) else {}
    aliases = meta.get("feature_aliases", {}) if isinstance(meta, Mapping) else {}
    return {f: str(aliases.get(f, f)) for f in model.features}


def _eval_bound_expr(expr: Any, t_array: "jax.Array") -> "jax.Array":
    """Evaluate a feature-dependent bound expression (e.g. ``"min(T) - 5.0"``).

    The primary feature array is exposed as ``T``; ``min``/``max``/``mean`` are
    the JAX reductions so the result stays traceable inside the NumPyro model.
    """
    import jax.numpy as jnp

    namespace = {
        "min": lambda a: jnp.min(a),
        "max": lambda a: jnp.max(a),
        "mean": lambda a: jnp.mean(a),
        "T": t_array,
        "inf": float("inf"),
    }
    return eval(str(expr), {"__builtins__": {}}, namespace)  # noqa: S307


class _SymbolicBayesianModel(BayesianModel):
    """Generic NumPyro model backed by a :class:`SymbolicModel`.

    Concrete per-model subclasses (built by :func:`build_model`) only override the
    class-level metadata plus the :attr:`symbolic_model` / :attr:`feature_aliases`
    descriptors; all behaviour lives here so the maths is defined exactly once.
    """

    # Per-subclass descriptors (set in build_model); not Pydantic fields.
    symbolic_model: ClassVar[SymbolicModel]
    feature_aliases: ClassVar[dict[str, str]]
    # Data-independent (``FixedConstant``) constants, resolved once at build.
    static_constants: ClassVar[dict[str, float]] = {}
    # True when at least one constant must be resolved from group data.
    has_dynamic_constants: ClassVar[bool] = False

    # The only instance state: constants resolved from a bound group's data.
    resolved_constants: Optional[dict[str, float]] = None

    # ---- helpers -----------------------------------------------------------

    def _constants(self) -> dict[str, float]:
        sm = type(self).symbolic_model
        if not sm.constant_names:
            return {}
        if self.resolved_constants is not None:
            return self.resolved_constants
        if not type(self).has_dynamic_constants:
            return type(self).static_constants
        raise RuntimeError(
            f"Model {sm.name!r} has data-dependent constants {list(sm.constant_names)} "
            "that must be resolved from group data first. Call bind_group(group) (done "
            "automatically by fit_groups / the workflow) before evaluating the mean."
        )

    # ---- BayesianModel interface ------------------------------------------

    def reconstruction_kwargs(self) -> dict[str, Any]:
        if self.resolved_constants is None:
            return {}
        return {"resolved_constants": dict(self.resolved_constants)}

    def bind_group(self, group: BayesianGroup) -> "_SymbolicBayesianModel":
        sm = type(self).symbolic_model
        if not sm.constant_names:
            return self
        aliases = type(self).feature_aliases
        feats = {
            f: np.asarray(group.features[col], dtype=float).ravel()
            for f, col in aliases.items()
        }
        raw = np.asarray(group.raw_observation, dtype=float).ravel()
        consts = resolve_constants(sm.constants, feats, raw)
        # Carry the user-configured priors onto the group-bound instance so the
        # model stays the single source of priors through fitting.
        return type(self)(
            resolved_constants=consts,
            priors=dict(self.priors),
            sigma_scale=self.sigma_scale,
            likelihood=self.likelihood,
            student_t_df=self.student_t_df,
        )

    def nuts_kernel_kwargs(self, *, target_accept_prob: float) -> dict[str, Any]:
        sm = type(self).symbolic_model
        meta = sm.metadata if isinstance(sm.metadata, Mapping) else {}
        nuts = meta.get("nuts", {}) if isinstance(meta, Mapping) else {}
        out: dict[str, Any] = {"target_accept_prob": target_accept_prob}
        tmin = nuts.get("target_accept_prob_min")
        if tmin is not None:
            out["target_accept_prob"] = max(target_accept_prob, float(tmin))
        if nuts.get("init_strategy") == "init_to_median":
            from numpyro.infer import init_to_median

            out["init_strategy"] = init_to_median()
        return out

    def sample_parameters(
        self,
        priors: "PriorSet | None",
        features: Mapping[str, "jax.Array"],
    ) -> dict[str, "jax.Array"]:
        sm = type(self).symbolic_model
        meta = sm.metadata if isinstance(sm.metadata, Mapping) else {}
        fdb = meta.get("feature_dependent_bounds", {}) if isinstance(meta, Mapping) else {}
        if not fdb:
            return super().sample_parameters(priors, features)

        import numpyro
        import numpyro.distributions as dist
        import jax.numpy as jnp

        from .priors import Uniform

        if priors is None:
            priors = self.prior_set()
        aliases = type(self).feature_aliases
        primary_col = aliases[sm.features[0]]
        t_array = features[primary_col]

        params: dict[str, "jax.Array"] = {}
        for pname in sm.param_names:
            spec = priors.parameters.get(pname)
            if spec is None:
                raise KeyError(
                    f"PriorSet for model {sm.name!r} is missing parameter {pname!r}."
                )
            cfg = fdb.get(pname)
            if cfg and isinstance(spec, Uniform):
                upper = spec.high
                if "upper_expr" in cfg:
                    upper = jnp.minimum(spec.high, _eval_bound_expr(cfg["upper_expr"], t_array))
                lower = jnp.minimum(spec.low, upper - float(cfg.get("lower_margin", 1.0)))
                params[pname] = numpyro.sample(pname, dist.Uniform(lower, upper))
            else:
                params[pname] = numpyro.sample(pname, spec.to_numpyro())
        return params

    def mean(
        self,
        features: Mapping[str, "jax.Array"],
        params: Mapping[str, "jax.Array"],
    ) -> "jax.Array":
        sm = type(self).symbolic_model
        aliases = type(self).feature_aliases
        consts = self._constants()
        kernel = compile_jax(sm)

        values: list[Any] = []
        for f in sm.features:
            values.append(features[aliases[f]])
        for c in sm.constant_names:
            values.append(consts[c])
        for p in sm.param_names:
            values.append(params[p])
        return kernel(*values)


def build_model(model: SymbolicModel) -> type[BayesianModel]:
    """Create (and register) a concrete ``BayesianModel`` subclass for ``model``."""
    aliases = _feature_aliases(model)
    feature_names = tuple(aliases[f] for f in model.features)

    static_constants = {
        name: resolver.resolve({}, None)
        for name, resolver in model.constants.items()
        if isinstance(resolver, FixedConstant)
    }
    has_dynamic = any(
        not isinstance(resolver, FixedConstant)
        for resolver in model.constants.values()
    )

    namespace: dict[str, Any] = {
        "__doc__": model.description,
        "name": model.name,
        "property_name": model.property,
        "feature_names": feature_names,
        "param_names": tuple(model.param_names),
        "log_observation": bool(model.log_observation),
        "symbolic_model": model,
        "feature_aliases": aliases,
        "static_constants": static_constants,
        "has_dynamic_constants": has_dynamic,
    }
    cls_name = "".join(part.capitalize() for part in model.name.split("_")) or "Model"
    return type(cls_name, (_SymbolicBayesianModel,), namespace)


def register_all() -> list[str]:
    """Synthesise and register a Bayesian model for every symbolic model.

    Idempotent: :meth:`BayesianModel.__init_subclass__` registers each subclass on
    creation, and the registry tolerates re-registering the *same* class object, so
    repeated imports are safe.
    """
    built: list[str] = []
    existing = set(ModelRegistry.names())
    for name in _model_registry.names():
        if name in existing:
            continue
        build_model(_model_registry.get(name))
        built.append(name)
    return built


__all__ = ["build_model", "register_all", "_SymbolicBayesianModel", "R_GAS"]
