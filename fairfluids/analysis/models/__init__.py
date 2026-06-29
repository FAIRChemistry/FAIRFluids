"""Symbolic property models: declare a formula once, fit it many ways.

A single :class:`SymbolicModel` — one sympy expression with its symbols
classified into features / constants / parameters — is the single source of
truth for a property model. The fitting backends live in the sibling
:mod:`fairfluids.analysis.fit` package and consume these models, so the
frequentist and Bayesian paths can never drift.

Notebook usage::

    import sympy as sp
    from fairfluids.analysis import models as fm
    from fairfluids.analysis import fit as ff

    T, A, B, T0 = sp.symbols("T A B T0")
    fm.define_model(
        "my_vft", property="viscosity",
        expr=sp.exp(A + B / (T - T0)), features=["T"],
        p0={"A": -4, "B": 600, "T0": 150},
    )
    result = ff.fit_least_squares(fm.get_model("my_vft"), {"T": T_arr}, eta_arr)

Importing this package pulls in only sympy + numpy.
"""

from __future__ import annotations

from . import resolvers
from .builtin import load_builtin_models
from .compile import compile_jax, compile_numpy
from .io import (
    from_dict,
    load_models,
    parse_expression,
    save_models,
    to_dict,
)
from .model import SymbolicModel
from .registry import define_model, get_model, list_models, registry
from .resolvers import FixedConstant, InterpConstant, MeanConstant

# Populate the registry with the framework-provided models (idempotent).
load_builtin_models()

__all__ = [
    # core
    "SymbolicModel",
    # authoring / registry
    "define_model",
    "get_model",
    "list_models",
    "registry",
    "load_builtin_models",
    # constants
    "FixedConstant",
    "MeanConstant",
    "InterpConstant",
    # compile
    "compile_numpy",
    "compile_jax",
    # io
    "to_dict",
    "from_dict",
    "load_models",
    "save_models",
    "parse_expression",
    # submodules
    "resolvers",
]
