"""The single source of truth: a property model declared as one sympy expression.

A :class:`SymbolicModel` carries the *natural-form* expression for a
thermophysical property (e.g. ``rho(T) = rho0 * exp(...)`` or
``eta(T) = exp(A + B/(T - T0))``) plus a classification of its symbols into
three roles:

* **features** — data columns supplied per group (``T``, ``p``, ``x`` ...).
* **constants** — fixed before the fit, either a literal or resolved from the
  group's data via :mod:`fairfluids.analysis.symbolic.resolvers`.
* **parameters** — everything else: the quantities to fit / sample.

Everything both fit backends need is *derived* from this one object — the numpy
kernel for least-squares (:mod:`.regression`) and the JAX mean for NUTS
(:mod:`.bayesian`) — so a model can never drift between the two pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import sympy as sp

from .resolvers import ConstantResolver


@dataclass(frozen=True)
class SymbolicModel:
    """A thermophysical property model defined by a single symbolic expression.

    Args:
        name: Unique model identifier (used by the registry).
        property: Physical property described (``"viscosity"``, ``"density"`` ...).
        expr: The property in *natural* form as a sympy expression. Its free
            symbols are partitioned into features / constants / parameters.
        features: Names of the data-column symbols.
        constants: Mapping ``symbol -> resolver``; resolved before fitting.
        log_observation: If True the model is fitted on ``ln(property)`` and the
            likelihood/least-squares sees ``ln`` of the data.
        priors: Optional mapping ``param -> PriorSpec`` (opaque here; consumed by
            the Bayesian backend). Kept generic so this module needs no NumPyro.
        p0: Optional initial guesses for the nonlinear least-squares backend.
        param_units: Optional unit strings per parameter (metadata only).
        derived: Optional mapping ``derived_name -> expression string`` for
            quantities computed *from* the fitted parameters/constants (e.g.
            ``Ea_kJ_mol = Ea / 1000``). Each expression is parsed lazily and may
            reference parameters, constants and features. The fit backends
            evaluate these and propagate their uncertainty via the parameter
            covariance, so reparametrisations live in one declarative place.
        derived_units: Optional unit strings per derived quantity.
        metadata: Free-form, backend-specific hints that do not belong to the
            mathematics itself — e.g. ``feature_dependent_bounds`` (VFT ``T0``
            clipping), NUTS kwargs, or plot display labels. Kept opaque here so
            this module stays free of backend dependencies.
        description: Human-readable description.
    """

    name: str
    property: str
    expr: sp.Expr
    features: tuple[str, ...]
    constants: Mapping[str, ConstantResolver] = field(default_factory=dict)
    log_observation: bool = True
    priors: Mapping[str, Any] = field(default_factory=dict)
    p0: Mapping[str, float] = field(default_factory=dict)
    param_units: Mapping[str, str | None] = field(default_factory=dict)
    derived: Mapping[str, str] = field(default_factory=dict)
    derived_units: Mapping[str, str | None] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self) -> None:
        free = {s.name for s in self.expr.free_symbols}
        declared = set(self.features) | set(self.constants)
        unknown = declared - free
        if unknown:
            raise ValueError(
                f"Model {self.name!r}: declared feature/constant {sorted(unknown)} "
                f"do not appear in the expression (free symbols: {sorted(free)})."
            )
        overlap = set(self.features) & set(self.constants)
        if overlap:
            raise ValueError(
                f"Model {self.name!r}: symbols {sorted(overlap)} are declared as both "
                "feature and constant."
            )
        if not self.param_names:
            raise ValueError(
                f"Model {self.name!r}: no free parameters left to fit. "
                f"Free symbols: {sorted(free)}; features+constants: {sorted(declared)}."
            )
        for tag, mapping in (("prior", self.priors), ("p0", self.p0)):
            stray = set(mapping) - set(self.param_names)
            if stray:
                raise ValueError(
                    f"Model {self.name!r}: {tag} keys {sorted(stray)} are not parameters "
                    f"({list(self.param_names)})."
                )
        allowed = set(self.param_names) | set(self.constant_names) | set(self.features)
        for dname, dexpr in self.derived_exprs.items():
            stray = {s.name for s in dexpr.free_symbols} - allowed
            if stray:
                raise ValueError(
                    f"Model {self.name!r}: derived quantity {dname!r} references unknown "
                    f"symbol(s) {sorted(stray)}; allowed are parameters/constants/features "
                    f"{sorted(allowed)}."
                )
        stray_units = set(self.derived_units) - set(self.derived)
        if stray_units:
            raise ValueError(
                f"Model {self.name!r}: derived_units keys {sorted(stray_units)} have no "
                f"matching derived quantity ({sorted(self.derived)})."
            )

    # -- derived metadata ------------------------------------------------------

    @property
    def free_symbol_names(self) -> frozenset[str]:
        return frozenset(s.name for s in self.expr.free_symbols)

    @property
    def param_names(self) -> tuple[str, ...]:
        """Fitted parameters: free symbols that are neither feature nor constant."""
        decided = set(self.features) | set(self.constants)
        return tuple(sorted(self.free_symbol_names - decided))

    @property
    def constant_names(self) -> tuple[str, ...]:
        return tuple(sorted(self.constants))

    @property
    def arg_order(self) -> tuple[str, ...]:
        """Canonical positional order used by every compiled kernel.

        Features (declaration order), then constants (sorted), then parameters
        (sorted). Both backends agree on this so a single ``lambdify`` serves
        both numpy and JAX.
        """
        return (*self.features, *self.constant_names, *self.param_names)

    @property
    def mean_expr(self) -> sp.Expr:
        """The expression on the *observation* scale (``ln`` applied if requested).

        ``expand_log(..., force=True)`` collapses ``log(exp(x)) -> x`` and
        ``log(a*b) -> log(a)+log(b)`` so the fitted form is the clean additive
        expression rather than ``log`` wrapped around the whole product.
        """
        if not self.log_observation:
            return self.expr
        return sp.expand_log(sp.log(self.expr), force=True)

    @property
    def derived_names(self) -> tuple[str, ...]:
        """Names of the declared derived quantities (sorted, stable)."""
        return tuple(sorted(self.derived))

    @property
    def derived_exprs(self) -> dict[str, sp.Expr]:
        """Parsed sympy expressions for each derived quantity, keyed by name.

        String expressions are parsed through the safe whitelist parser. Parsing
        is done on demand (no cycle: :mod:`.io` imports this module, so the import
        is local) and the result is cached on the instance.
        """
        cached = self.__dict__.get("_derived_exprs_cache")
        if cached is not None:
            return cached
        from .io import parse_expression

        out: dict[str, sp.Expr] = {}
        for name, expr in self.derived.items():
            out[name] = expr if isinstance(expr, sp.Expr) else parse_expression(str(expr))
        object.__setattr__(self, "_derived_exprs_cache", out)
        return out

    def derived_unit(self, name: str) -> str | None:
        """Unit string for derived quantity ``name`` (``None`` when unknown)."""
        return self.derived_units.get(name)

    def symbols(self, names: tuple[str, ...]) -> list[sp.Symbol]:
        """Return sympy ``Symbol`` objects for ``names`` (matching those in ``expr``)."""
        by_name = {s.name: s for s in self.expr.free_symbols}
        return [by_name.get(n, sp.Symbol(n)) for n in names]

    def __repr__(self) -> str:
        return (
            f"SymbolicModel(name={self.name!r}, property={self.property!r}, "
            f"features={list(self.features)}, constants={self.constant_names}, "
            f"params={self.param_names}, log_observation={self.log_observation})"
        )


__all__ = ["SymbolicModel"]
