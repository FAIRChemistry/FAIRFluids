"""Evaluate a model's declared derived quantities and propagate their error.

A :class:`~fairfluids.analysis.models.SymbolicModel` may declare *derived*
quantities — reparametrisations of the fitted parameters such as
``As = exp(logA)`` or ``Ea_kJ_mol = Ea / 1000``. Rather than hand-writing each
value and its ``*_std`` companion (the old codegen approach), we differentiate
the derived expression symbolically and propagate the parameter covariance via
the first-order (delta-method) rule ``var(d) = J Σ Jᵀ``.

Derived expressions that depend on a *feature* (e.g. ``alpha_p(T) = A2*T + A1``)
are not scalars — they are curves — so they are skipped here and left for the
plotting/reconstruction layer to lambdify directly.
"""

from __future__ import annotations

from typing import Mapping, Optional

import numpy as np
import sympy as sp

from fairfluids.analysis.models.model import SymbolicModel


def scalar_derived_names(model: SymbolicModel) -> tuple[str, ...]:
    """Derived quantities that reduce to a scalar (no feature dependence)."""
    feats = set(model.features)
    out = [
        name
        for name, expr in model.derived_exprs.items()
        if not ({s.name for s in expr.free_symbols} & feats)
    ]
    return tuple(sorted(out))


def evaluate_derived(
    model: SymbolicModel,
    param_values: Mapping[str, float],
    constants: Mapping[str, float],
    pcov: Optional[np.ndarray] = None,
) -> dict[str, tuple[float, Optional[float]]]:
    """Return ``{derived_name: (value, std)}`` for every scalar derived quantity.

    Args:
        model: The fitted model.
        param_values: Fitted parameter values keyed by parameter name.
        constants: Resolved constant values (substituted as exact numbers).
        pcov: Parameter covariance matrix ordered like ``model.param_names``.
            When ``None`` (or non-finite) the standard deviations are ``None``.
    """
    pnames = model.param_names
    psyms = model.symbols(pnames)
    const_subs = {sp.Symbol(c): float(v) for c, v in constants.items()}
    pvec = [float(param_values[p]) for p in pnames]

    cov = None
    if pcov is not None:
        cov = np.asarray(pcov, dtype=float)
        if cov.shape != (len(pnames), len(pnames)) or not np.all(np.isfinite(cov)):
            cov = None

    out: dict[str, tuple[float, Optional[float]]] = {}
    for name in scalar_derived_names(model):
        expr_c = model.derived_exprs[name].subs(const_subs)
        f = sp.lambdify(psyms, expr_c, "numpy")
        try:
            value = float(f(*pvec))
        except Exception:
            value = float("nan")

        std: Optional[float] = None
        if cov is not None:
            grads = sp.Matrix([sp.diff(expr_c, s) for s in psyms])
            gfun = sp.lambdify(psyms, grads, "numpy")
            jac = np.asarray(gfun(*pvec), dtype=float).reshape(-1)
            var = float(jac @ cov @ jac)
            std = float(np.sqrt(var)) if np.isfinite(var) and var >= 0.0 else None
        out[name] = (value, std)
    return out


__all__ = ["evaluate_derived", "scalar_derived_names"]
