"""In-memory registry for symbolic models, plus the notebook entry point.

Unlike the codegen pipelines (which register models at import time from
generated modules), this registry is populated *at runtime* — a user declares a
model in a notebook cell with :func:`define_model` and it is immediately
available to the fit backends. The registry is intentionally separate from the
``bayesian`` / ``regression`` registries so this module never touches them.
"""

from __future__ import annotations

from typing import Any, Mapping

import sympy as sp

from .model import SymbolicModel
from .resolvers import ConstantResolver, resolver_from_json


class _SymbolicRegistry:
    """Module-private registry of :class:`SymbolicModel` instances by name."""

    def __init__(self) -> None:
        self._entries: dict[str, SymbolicModel] = {}

    def register(self, model: SymbolicModel, *, overwrite: bool = False) -> None:
        if model.name in self._entries and not overwrite:
            raise ValueError(
                f"Symbolic model {model.name!r} already registered. "
                "Pass overwrite=True to replace it (handy when re-running a notebook cell)."
            )
        self._entries[model.name] = model

    def get(self, name: str) -> SymbolicModel:
        if name not in self._entries:
            raise KeyError(
                f"No symbolic model registered under {name!r}. "
                f"Available: {sorted(self._entries)}"
            )
        return self._entries[name]

    def names(self) -> list[str]:
        return sorted(self._entries)

    def clear(self) -> None:
        self._entries.clear()


registry = _SymbolicRegistry()


def _coerce_expr(expr: Any) -> sp.Expr:
    if isinstance(expr, sp.Expr):
        return expr
    if isinstance(expr, str):
        # Local import to avoid a cycle (io imports model/resolvers).
        from .io import parse_expression

        return parse_expression(expr)
    raise TypeError(f"expr must be a sympy expression or string, got {type(expr)!r}.")


def _coerce_constants(
    constants: Mapping[str, Any] | None,
) -> dict[str, ConstantResolver]:
    out: dict[str, ConstantResolver] = {}
    for name, spec in (constants or {}).items():
        out[name] = spec if isinstance(spec, ConstantResolver) else resolver_from_json(spec)
    return out


def define_model(
    name: str,
    *,
    property: str,
    expr: Any,
    features: tuple[str, ...] | list[str],
    constants: Mapping[str, Any] | None = None,
    log_observation: bool = True,
    priors: Mapping[str, Any] | None = None,
    p0: Mapping[str, float] | None = None,
    param_units: Mapping[str, str | None] | None = None,
    derived: Mapping[str, str] | None = None,
    derived_units: Mapping[str, str | None] | None = None,
    metadata: Mapping[str, Any] | None = None,
    description: str = "",
    register: bool = True,
    overwrite: bool = False,
) -> SymbolicModel:
    """Declare a symbolic model (notebook-friendly) and register it for fitting.

    ``expr`` may be a sympy expression or a string (parsed safely). ``constants``
    values may be resolver objects, plain numbers (→ fixed), or JSON dicts.
    Set ``overwrite=True`` to redefine a model when re-running a cell.
    """
    model = SymbolicModel(
        name=name,
        property=property,
        expr=_coerce_expr(expr),
        features=tuple(features),
        constants=_coerce_constants(constants),
        log_observation=log_observation,
        priors=dict(priors or {}),
        p0=dict(p0 or {}),
        param_units=dict(param_units or {}),
        derived=dict(derived or {}),
        derived_units=dict(derived_units or {}),
        metadata=dict(metadata or {}),
        description=description,
    )
    if register:
        registry.register(model, overwrite=overwrite)
    return model


def get_model(name: str) -> SymbolicModel:
    """Return a registered symbolic model by name."""
    return registry.get(name)


def list_models() -> list[str]:
    """Return the names of all registered symbolic models."""
    return registry.names()


__all__ = ["registry", "define_model", "get_model", "list_models"]
