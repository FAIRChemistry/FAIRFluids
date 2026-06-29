"""Regression fits (Arrhenius, extended Arrhenius, VFT) from the symbolic store.

Models are no longer rendered by a codegen pipeline. The ``(spec, kernel)`` pairs
this engine dispatches to are *synthesised at import time* from the single source
of truth — the :class:`~fairfluids.analysis.models.SymbolicModel` instances in
:data:`fairfluids.analysis.models.registry` — via :mod:`.bridge`. A generic,
model-agnostic engine groups the data and dispatches to those kernels, returning
a universal :class:`ParameterStack` of derived quantities.

Public surface:

- :func:`fit_model` / :func:`fit_documents` -- object-oriented entry points.
- :class:`ParameterStack`, :class:`FitResult`, :class:`FittedParameter`,
  :class:`GroupKey` -- universal result objects.
- :func:`list_models`, :func:`get_spec` -- model registry introspection.
- :func:`fit_arrhenius`, :func:`fit_extended_arrhenius`, :func:`fit_vft` --
  backward-compatible DataFrame wrappers.
"""

from __future__ import annotations

# Synthesise and register every model from the symbolic store on import.
from . import bridge

bridge.register_all()

from .compat import fit_arrhenius, fit_extended_arrhenius, fit_vft
from .engine import fit_documents, fit_model
from .result import (
    FitResult,
    FittedParameter,
    GroupKey,
    ParameterStack,
    stack_from_results,
)
from .spec import (
    RawFit,
    RegressionModelSpec,
    get_model,
    get_spec,
    list_models,
    register_model,
)

__all__ = [
    "fit_model",
    "fit_documents",
    "ParameterStack",
    "FitResult",
    "FittedParameter",
    "GroupKey",
    "stack_from_results",
    "RegressionModelSpec",
    "RawFit",
    "list_models",
    "get_spec",
    "get_model",
    "register_model",
    "fit_arrhenius",
    "fit_extended_arrhenius",
    "fit_vft",
]
