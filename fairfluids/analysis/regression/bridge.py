"""Bridge the unified symbolic model store onto the regression engine.

The regression engine (:mod:`.engine`) is model-agnostic: it groups the data,
transforms the observation and dispatches to a registered ``(spec, kernel)``
pair looked up by name. Historically those pairs were rendered by a codegen
pipeline into ``_generated/``. They are now *synthesised at import time* from the
single source of truth — the :class:`~fairfluids.analysis.models.SymbolicModel`
instances in :data:`fairfluids.analysis.models.registry` — so the regression and
Bayesian backends can never describe a model differently.

For each symbolic model we build:

* a :class:`~fairfluids.analysis.regression.spec.RegressionModelSpec` whose
  ``param_names`` are the primary fitted parameters *plus* the model's scalar
  derived quantities (``As``, ``Ea_kJ_mol`` ...), so the engine surfaces them in
  the :class:`ParameterStack`; and
* a kernel that reuses the shared least-squares backend
  (:func:`fairfluids.analysis.fit.least_squares.fit`) — reconstructing the raw
  observation from the engine's already-transformed ``y`` — and returns both the
  fitted and the (delta-method propagated) derived quantities.
"""

from __future__ import annotations

from typing import Mapping, Optional

import numpy as np

from ..fit.derived import scalar_derived_names
from ..fit.least_squares import fit as _ls_fit
from ..models import registry as _model_registry
from ..models.model import SymbolicModel
from .spec import ModelRegistry, RawFit, RegressionModelSpec, register_model


def build_spec(model: SymbolicModel) -> RegressionModelSpec:
    """Synthesise a :class:`RegressionModelSpec` from a symbolic model."""
    reg: Mapping = model.metadata.get("regression", {}) if isinstance(model.metadata, Mapping) else {}
    kind = str(reg.get("kind", "nonlinear"))
    n_fitted = int(reg.get("n_fitted", len(model.param_names)))
    default_min = n_fitted + (1 if kind == "nonlinear" else 0)
    min_points = max(int(reg.get("min_points", default_min)), 2)

    derived = scalar_derived_names(model)
    param_names = tuple(model.param_names) + derived

    units: dict[str, Optional[str]] = {p: model.param_units.get(p) for p in model.param_names}
    for d in derived:
        units[d] = model.derived_units.get(d)

    return RegressionModelSpec(
        name=model.name,
        kind=kind,
        param_names=param_names,
        observation=model.property,
        property=model.property,
        y_transform="log" if model.log_observation else "identity",
        min_points=min_points,
        n_fitted=n_fitted,
        param_units=units,
        description=model.description,
    )


def build_kernel(model: SymbolicModel):
    """Synthesise a fit kernel ``(T, y, sigma) -> RawFit`` for a symbolic model.

    The engine has already applied the observation transform, so ``y`` is on the
    fitted scale. The shared least-squares backend re-applies the transform
    internally, so we hand it the reconstructed *raw* observation (and propagate
    ``sigma`` back to raw units) to keep one code path for both entry points.
    """
    feature = model.features[0]

    def kernel(
        temperatures: np.ndarray,
        y: np.ndarray,
        sigma: Optional[np.ndarray],
    ) -> RawFit:
        T = np.asarray(temperatures, dtype=float).ravel()
        y_arr = np.asarray(y, dtype=float).ravel()
        raw = np.exp(y_arr) if model.log_observation else y_arr

        raw_unc: Optional[np.ndarray] = None
        if sigma is not None:
            sig = np.asarray(sigma, dtype=float).ravel()
            raw_unc = sig * raw if model.log_observation else sig

        fit = _ls_fit(model, {feature: T}, raw, observation_uncertainty=raw_unc)
        if not fit.success:
            return RawFit(params={}, r_squared=None, success=False)

        params: dict[str, tuple[float, Optional[float]]] = dict(fit.params)
        params.update(fit.derived)
        return RawFit(params=params, r_squared=fit.r_squared, success=True)

    return kernel


def register_all(*, overwrite: bool = False) -> list[str]:
    """Register every symbolic model with the regression engine's registry.

    Idempotent: already-registered names are skipped unless ``overwrite`` forces
    a fresh registration (the spec registry otherwise rejects name collisions).
    """
    registered: list[str] = []
    existing = set(ModelRegistry.names())
    for name in _model_registry.names():
        if name in existing and not overwrite:
            continue
        model = _model_registry.get(name)
        register_model(build_spec(model), build_kernel(model))
        registered.append(name)
    return registered


__all__ = ["build_spec", "build_kernel", "register_all"]
