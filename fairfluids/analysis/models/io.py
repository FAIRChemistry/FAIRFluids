"""JSON round-trip for symbolic models — the bridge to FAIRFluids model stores.

The persisted form is a top-level ``{"models": [...]}`` list (see
``store/<property>.json``) so notebook-declared models and framework-provided
models live in the *same* kind of file. The formula is a **mathematical** string
(``"exp(A + B/(T - T0))"``, parsed with sympy) rather than a code string — which
is what makes it both safely parseable and user-authorable.

Expression parsing is restricted to a whitelist of mathematical functions and
rejects unknown applied functions, so loading a model file cannot execute
arbitrary code.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import sympy as sp
from sympy.core.function import AppliedUndef
from sympy.parsing.sympy_parser import parse_expr, standard_transformations

from .model import SymbolicModel
from .resolvers import resolver_from_json

# Whitelist of functions/constants permitted inside an expression string.
_ALLOWED_NAMES = (
    "exp", "log", "ln", "sqrt", "Abs",
    "sin", "cos", "tan", "sinh", "cosh", "tanh",
    "Pow", "pi", "E",
)


def _allowed_local_dict() -> dict[str, Any]:
    local: dict[str, Any] = {}
    for name in _ALLOWED_NAMES:
        attr = "log" if name == "ln" else name
        obj = getattr(sp, attr, None)
        if obj is not None:
            local[name] = obj
    return local


def parse_expression(text: str) -> sp.Expr:
    """Parse a math string into a sympy expression, safely.

    Unknown *names* become free symbols (intended — that's how parameters and
    features are introduced), but unknown *applied functions* (e.g. ``foo(x)``)
    are rejected so a model file cannot smuggle in arbitrary callables.
    """
    expr = parse_expr(
        text,
        local_dict=_allowed_local_dict(),
        transformations=standard_transformations,
        evaluate=True,
    )
    if not isinstance(expr, sp.Expr):
        raise ValueError(f"Expression {text!r} did not parse to a sympy expression.")
    bad = {f.func.__name__ for f in expr.atoms(AppliedUndef)}
    if bad:
        raise ValueError(
            f"Expression {text!r} uses unknown function(s) {sorted(bad)}. "
            f"Allowed functions: {sorted(set(_ALLOWED_NAMES) - {'pi', 'E'})}."
        )
    return expr


def _prior_to_json(spec: Any) -> Any:
    """Serialise a prior spec. Accepts pydantic PriorSpec objects or raw dicts/lists."""
    if hasattr(spec, "model_dump"):
        return spec.model_dump()
    return spec


def to_dict(model: SymbolicModel) -> dict[str, Any]:
    """Serialise a :class:`SymbolicModel` to a JSON-ready dict."""
    return {
        "name": model.name,
        "property": model.property,
        "expr": str(model.expr),
        "features": list(model.features),
        "constants": {n: r.to_json() for n, r in model.constants.items()},
        "log_observation": model.log_observation,
        "priors": {n: _prior_to_json(s) for n, s in model.priors.items()},
        "p0": dict(model.p0),
        "param_units": dict(model.param_units),
        "derived": {n: str(e) for n, e in model.derived_exprs.items()},
        "derived_units": dict(model.derived_units),
        "metadata": dict(model.metadata),
        "description": model.description,
    }


def from_dict(data: Mapping[str, Any]) -> SymbolicModel:
    """Build a :class:`SymbolicModel` from its JSON form.

    Priors are kept as raw dicts here (left for the Bayesian backend to
    interpret) so this loader has no NumPyro/pydantic-prior dependency.
    """
    constants = {n: resolver_from_json(v) for n, v in data.get("constants", {}).items()}
    return SymbolicModel(
        name=data["name"],
        property=data["property"],
        expr=parse_expression(data["expr"]),
        features=tuple(data["features"]),
        constants=constants,
        log_observation=bool(data.get("log_observation", True)),
        priors=dict(data.get("priors", {})),
        p0=dict(data.get("p0", {})),
        param_units=dict(data.get("param_units", {})),
        derived=dict(data.get("derived", {})),
        derived_units=dict(data.get("derived_units", {})),
        metadata=dict(data.get("metadata", {})),
        description=data.get("description", ""),
    )


def save_models(models: Iterable[SymbolicModel], path: str | Path) -> Path:
    """Write models to a ``{"models": [...]}`` JSON file (codegen-compatible shape)."""
    path = Path(path)
    payload = {"models": [to_dict(m) for m in models]}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_models(path: str | Path) -> list[SymbolicModel]:
    """Read a ``{"models": [...]}`` JSON file into :class:`SymbolicModel` objects."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [from_dict(m) for m in data.get("models", [])]


__all__ = [
    "parse_expression",
    "to_dict",
    "from_dict",
    "save_models",
    "load_models",
]
