"""Bind-time resolvers for *constant* symbols in a :class:`SymbolicModel`.

A constant is a symbol in a model expression that is neither a data *feature*
nor a fitted *parameter* — its value is fixed before fitting, either as a
literal number or computed from the group's data (e.g. a reference temperature
``T0 = mean(T)`` or a reference density ``rho0 = rho(T0)`` obtained by
interpolation). This is exactly the machinery that powers the data-anchored
density variants (``density_exp_poly_t0_mean_centered`` and friends): the
*formula* is trivial, but the constants are resolved from each group's data.

Resolvers are deliberately tiny and JSON-serialisable (no Python callables in
the persisted form) so a notebook-declared model round-trips cleanly through a
FAIRFluids JSON. New resolver kinds register via :data:`RESOLVERS`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class ConstantResolver(Protocol):
    """Resolve one constant to a scalar from a group's features and observation."""

    kind: str

    def resolve(
        self,
        features: Mapping[str, np.ndarray],
        observation: np.ndarray | None,
    ) -> float: ...

    def to_json(self) -> dict[str, Any]: ...


@dataclass(frozen=True)
class FixedConstant:
    """A constant with a literal value, independent of the data."""

    value: float
    kind: str = "fixed"

    def resolve(
        self, features: Mapping[str, np.ndarray], observation: np.ndarray | None
    ) -> float:
        return float(self.value)

    def to_json(self) -> dict[str, Any]:
        return {"kind": "fixed", "value": float(self.value)}


@dataclass(frozen=True)
class MeanConstant:
    """A constant equal to the arithmetic mean of a feature column (e.g. ``T0 = mean(T)``)."""

    feature: str
    kind: str = "mean"

    def resolve(
        self, features: Mapping[str, np.ndarray], observation: np.ndarray | None
    ) -> float:
        arr = np.asarray(features[self.feature], dtype=float).ravel()
        if arr.size == 0:
            raise ValueError(f"MeanConstant: feature {self.feature!r} is empty.")
        return float(np.mean(arr))


    def to_json(self) -> dict[str, Any]:
        return {"kind": "mean", "feature": self.feature}


@dataclass(frozen=True)
class InterpConstant:
    """A constant obtained by linear interpolation of the observation at an anchor.

    Resolves ``y(anchor)`` where ``y`` is the (linear, raw) observation as a
    function of ``feature``. When ``anchor`` is ``None`` it defaults to
    ``mean(feature)`` — the convention used by
    ``DensityExpPolyT0_mean_centered`` (``rho0 = rho(mean T)``). When the anchor
    coincides with a measured point the result is exact (no interpolation error).
    """

    feature: str
    anchor: float | None = None
    kind: str = "interp"

    def resolve(
        self, features: Mapping[str, np.ndarray], observation: np.ndarray | None
    ) -> float:
        if observation is None:
            raise ValueError(
                "InterpConstant requires the (raw, linear) observation to interpolate."
            )
        x = np.asarray(features[self.feature], dtype=float).ravel()
        y = np.asarray(observation, dtype=float).ravel()
        if x.shape != y.shape:
            raise ValueError("InterpConstant: feature and observation length mismatch.")
        if x.size < 2:
            raise ValueError("InterpConstant: need at least two points to interpolate.")
        order = np.argsort(x)
        x_sorted, y_sorted = x[order], y[order]
        anchor = float(np.mean(x)) if self.anchor is None else float(self.anchor)
        return float(np.interp(anchor, x_sorted, y_sorted))

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {"kind": "interp", "feature": self.feature}
        if self.anchor is not None:
            out["anchor"] = float(self.anchor)
        return out


RESOLVERS: dict[str, type] = {
    "fixed": FixedConstant,
    "mean": MeanConstant,
    "interp": InterpConstant,
}


def resolver_from_json(data: Any) -> ConstantResolver:
    """Build a resolver from its JSON form, or from a bare number (``FixedConstant``)."""
    if isinstance(data, (int, float)):
        return FixedConstant(value=float(data))
    if not isinstance(data, Mapping):
        raise TypeError(f"Cannot build a constant resolver from {data!r}.")
    kind = data.get("kind")
    if kind not in RESOLVERS:
        raise ValueError(
            f"Unknown constant resolver kind {kind!r}. Available: {sorted(RESOLVERS)}"
        )
    payload = {k: v for k, v in data.items() if k != "kind"}
    return RESOLVERS[kind](**payload)


def resolve_constants(
    constants: Mapping[str, ConstantResolver],
    features: Mapping[str, np.ndarray],
    observation: np.ndarray | None,
) -> dict[str, float]:
    """Resolve every constant to a float for one group."""
    return {
        name: resolver.resolve(features, observation)
        for name, resolver in constants.items()
    }


__all__ = [
    "ConstantResolver",
    "FixedConstant",
    "MeanConstant",
    "InterpConstant",
    "RESOLVERS",
    "resolver_from_json",
    "resolve_constants",
]
