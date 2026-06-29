"""Frequentist least-squares backend for symbolic models (numpy + SciPy only).

This is the light path: it needs neither JAX nor NumPyro, only SciPy's
``curve_fit``. Constants are resolved from the group's data first, then the
remaining parameters are fitted on the (optionally log-transformed) observation
scale. The compiled numpy kernel comes straight from the model's symbolic
``mean_expr`` so it is guaranteed identical to the Bayesian mean.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

import numpy as np

from ..models.compile import compile_numpy
from ..models.model import SymbolicModel
from ..models.resolvers import resolve_constants
from .derived import evaluate_derived


@dataclass(frozen=True)
class SymbolicFit:
    """Result of a least-squares fit for one group.

    ``params`` holds the primary fitted parameters as ``name -> (value, std)``;
    ``derived`` holds the model's declared scalar derived quantities with their
    delta-method propagated uncertainty.
    """

    model_name: str
    params: dict[str, tuple[float, Optional[float]]]
    constants: dict[str, float]
    r_squared: Optional[float]
    success: bool
    derived: dict[str, tuple[float, Optional[float]]] = field(default_factory=dict)

    def values(self) -> dict[str, float]:
        return {k: v for k, (v, _s) in self.params.items()}

    def derived_values(self) -> dict[str, float]:
        return {k: v for k, (v, _s) in self.derived.items()}


def _eval_numeric_hint(hint: Any, T: np.ndarray, y: np.ndarray) -> float:
    """Resolve a p0/bounds hint that may be a number or a small expression string.

    Expressions may reference the feature array ``T`` and the (transformed)
    observation ``y`` through ``min`` / ``max`` / ``mean`` (e.g.
    ``"min(T) - 50.0"``). Evaluated with an empty builtins namespace.
    """
    if isinstance(hint, (int, float)):
        return float(hint)
    namespace = {
        "min": lambda a: float(np.min(a)),
        "max": lambda a: float(np.max(a)),
        "mean": lambda a: float(np.mean(a)),
        "T": T,
        "y": y,
        "inf": float("inf"),
    }
    return float(eval(str(hint), {"__builtins__": {}}, namespace))  # noqa: S307


def fit(
    model: SymbolicModel,
    features: Mapping[str, np.ndarray],
    observation: np.ndarray,
    *,
    observation_uncertainty: Optional[np.ndarray] = None,
    p0: Optional[Mapping[str, float]] = None,
    maxfev: int = 20000,
) -> SymbolicFit:
    """Fit ``model`` to one group's data via nonlinear least squares.

    Args:
        features: Per-group feature arrays keyed by feature name.
        observation: Raw (linear) property values. The log transform, if any, is
            applied internally according to ``model.log_observation``.
        observation_uncertainty: Optional raw uncertainties; propagated to the
            log scale as ``sigma/y`` when the model is log-fitted.
        p0: Initial guesses overriding ``model.p0`` (missing entries default 1.0).
    """
    from scipy.optimize import curve_fit

    feats = {n: np.asarray(features[n], dtype=float).ravel() for n in model.features}
    raw_obs = np.asarray(observation, dtype=float).ravel()
    consts = resolve_constants(model.constants, feats, raw_obs)
    kernel = compile_numpy(model)
    pnames = model.param_names
    n_feat = len(model.features)
    n_const = len(model.constant_names)
    const_vals = [consts[n] for n in model.constant_names]
    feat_vals = [feats[n] for n in model.features]
    # Primary feature array, exposed as ``T`` to p0/bounds hint expressions.
    feats_arr = feat_vals[0] if feat_vals else np.asarray([], dtype=float)

    def f(_x: np.ndarray, *pv: float) -> np.ndarray:
        return kernel(*feat_vals, *const_vals, *pv)

    if model.log_observation:
        y = np.log(np.clip(raw_obs, 1e-300, None))
        sigma = None
        if observation_uncertainty is not None:
            unc = np.asarray(observation_uncertainty, dtype=float).ravel()
            with np.errstate(divide="ignore", invalid="ignore"):
                prop = unc / np.where(raw_obs > 0, raw_obs, np.nan)
            sigma = prop if np.any(np.isfinite(prop)) else None
    else:
        y = raw_obs
        sigma = (
            np.asarray(observation_uncertainty, dtype=float).ravel()
            if observation_uncertainty is not None
            else None
        )

    # Initial guesses: model.p0, then feature-dependent lsq hints, then caller p0.
    lsq_meta = model.metadata.get("lsq", {}) if isinstance(model.metadata, Mapping) else {}
    guesses: dict[str, float] = {n: float(v) for n, v in model.p0.items()}
    for name, hint in (lsq_meta.get("p0", {}) or {}).items():
        guesses[name] = _eval_numeric_hint(hint, feats_arr, y)
    guesses.update({k: float(v) for k, v in (p0 or {}).items()})
    p0_vec = [float(guesses.get(name, 1.0)) for name in pnames]

    # Optional parameter bounds (feature-dependent expressions allowed).
    lower = np.full(len(pnames), -np.inf)
    upper = np.full(len(pnames), np.inf)
    has_bounds = False
    for idx, name in enumerate(pnames):
        spec = (lsq_meta.get("bounds", {}) or {}).get(name)
        if not spec:
            continue
        if "lower" in spec:
            lower[idx] = _eval_numeric_hint(spec["lower"], feats_arr, y)
            has_bounds = True
        if "upper" in spec:
            upper[idx] = _eval_numeric_hint(spec["upper"], feats_arr, y)
            has_bounds = True
    # Keep the initial guess strictly inside any finite bounds.
    if has_bounds:
        for idx in range(len(pnames)):
            lo, hi, g = lower[idx], upper[idx], p0_vec[idx]
            if np.isfinite(lo) and g <= lo:
                p0_vec[idx] = lo + (1e-6 if not np.isfinite(hi) else (hi - lo) * 1e-3)
            elif np.isfinite(hi) and g >= hi:
                p0_vec[idx] = hi - (1e-6 if not np.isfinite(lo) else (hi - lo) * 1e-3)

    fit_kwargs: dict = {}
    if sigma is not None:
        valid = np.isfinite(sigma) & (sigma > 0)
        if np.any(valid):
            fit_kwargs["sigma"] = sigma
            fit_kwargs["absolute_sigma"] = True
    if has_bounds:
        fit_kwargs["bounds"] = (lower, upper)
        fit_kwargs["max_nfev"] = maxfev
    else:
        fit_kwargs["maxfev"] = maxfev

    xdata = np.arange(y.size, dtype=float)
    try:
        popt, pcov = curve_fit(f, xdata, y, p0=p0_vec, **fit_kwargs)
    except Exception:
        return SymbolicFit(
            model_name=model.name, params={}, constants=consts,
            r_squared=None, success=False,
        )

    pcov = np.asarray(pcov, dtype=float) if pcov is not None else None
    stds = np.sqrt(np.diag(pcov)) if pcov is not None else np.full(len(popt), np.nan)
    params: dict[str, tuple[float, Optional[float]]] = {}
    for name, val, std in zip(pnames, popt, stds):
        s = float(std) if np.isfinite(std) else None
        params[name] = (float(val), s)

    y_pred = f(xdata, *popt)
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = None if ss_tot == 0.0 else float(1.0 - ss_res / ss_tot)

    derived = evaluate_derived(
        model, {n: v for n, (v, _s) in params.items()}, consts, pcov
    )

    return SymbolicFit(
        model_name=model.name, params=params, constants=consts,
        r_squared=r_squared, success=True, derived=derived,
    )


__all__ = ["SymbolicFit", "fit"]
