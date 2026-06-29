"""Compile a :class:`SymbolicModel` to numerical kernels via ``sympy.lambdify``.

One symbolic ``mean_expr`` is turned into:

* a **numpy** callable for the frequentist least-squares backend, and
* a **JAX** callable for the NumPyro mean (autodiff-traceable, NUTS-ready).

Both use the model's :attr:`~SymbolicModel.arg_order`, so they evaluate the
*same* mathematics. Compiled callables are cached on the (expr, args, backend)
signature because ``lambdify`` is comparatively expensive.
"""

from __future__ import annotations

from typing import Callable, Mapping

import sympy as sp

from .model import SymbolicModel

_CACHE: dict[tuple[str, tuple[str, ...], str], Callable] = {}


def _compile(model: SymbolicModel, backend: str) -> Callable:
    arg_names = model.arg_order
    key = (sp.srepr(model.mean_expr), arg_names, backend)
    fn = _CACHE.get(key)
    if fn is None:
        symbols = model.symbols(arg_names)
        modules = "numpy" if backend == "numpy" else "jax"
        fn = sp.lambdify(symbols, model.mean_expr, modules=modules)
        _CACHE[key] = fn
    return fn


def compile_numpy(model: SymbolicModel) -> Callable:
    """Return a numpy callable ``f(*args)`` over :attr:`SymbolicModel.arg_order`."""
    return _compile(model, "numpy")


def compile_jax(model: SymbolicModel) -> Callable:
    """Return a JAX callable ``f(*args)`` over :attr:`SymbolicModel.arg_order`.

    Importing this triggers ``modules="jax"`` inside ``lambdify``; JAX is only
    required when this function is actually called.
    """
    return _compile(model, "jax")


def evaluate(
    model: SymbolicModel,
    fn: Callable,
    features: Mapping[str, object],
    constants: Mapping[str, float],
    params: Mapping[str, object],
):
    """Call a compiled ``fn`` with values assembled in canonical arg order."""
    values: list[object] = []
    for name in model.features:
        values.append(features[name])
    for name in model.constant_names:
        values.append(constants[name])
    for name in model.param_names:
        values.append(params[name])
    return fn(*values)


__all__ = ["compile_numpy", "compile_jax", "evaluate"]
