"""Declarative fluid-system selection for multi-system documents.

A single FAIRFluids document often mixes several fluid systems — e.g.
Methanol-Water, Ethanol-Water and Glycerol-Methanol-Water rows side by side.
Picking out *exactly* the rows you want ("only the ternary", "the ternary plus
pure water", "the ternary with Glycerol:Methanol pinned at 1:2 while water
varies") is fiddly with plain per-column range filters.

This module provides a tiny, composable selector algebra that compiles to a
boolean **row mask** over the extracted DataFrame. It leans on the
``mole_fraction_<compound>`` columns that
:func:`fairfluids.core.functionalities.extract_property_dataframe` builds, where
an *absent* component is filled with ``0.0`` (not NaN) — which is exactly what
makes "present / absent / exact set" expressible as arithmetic on those columns.

The result of any selector is callable as ``selector(df) -> pd.Series[bool]`` so
it can be handed straight to ``BayesianDataset.from_documents(..., row_filter=...)``.

Examples::

    from fairfluids.analysis import fluids as flu

    # exactly this ternary (all other components ~ 0)
    sel = flu.system("glycerol", "methanol", "water")

    # the ternary OR pure water
    sel = flu.system("glycerol", "methanol", "water") | flu.system("water")

    # the ternary with Glycerol:Methanol pinned at 1:2, water free
    sel = flu.system("glycerol", "methanol", "water").ratio(glycerol=1, methanol=2)

    mask = sel(df)            # pd.Series[bool]
    df_kept = df[sel(df)]
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

_PREFIX = "mole_fraction_"
# A component counts as "present" when its mole fraction exceeds this, and as
# "absent" when at or below it. Extraction fills absent components with exactly
# 0.0, so a tiny threshold cleanly separates true-zero from any real fraction.
_DEFAULT_ABSENT_TOL = 1e-9


# --- column helpers -----------------------------------------------------------


def _component_columns(df: pd.DataFrame) -> list[str]:
    """All ``mole_fraction_<compound>`` columns present in ``df``."""
    return [c for c in df.columns if c.lower().startswith(_PREFIX)]


def _resolve_column(df: pd.DataFrame, component: str) -> Optional[str]:
    """Find the ``mole_fraction_<component>`` column case-insensitively (or None)."""
    target = f"{_PREFIX}{component}".strip().lower()
    for col in df.columns:
        if col.lower() == target:
            return col
    return None


def _fractions(df: pd.DataFrame, component: str, *, required: bool) -> np.ndarray:
    """Numeric mole-fraction array for ``component``.

    A missing column means the component is absent everywhere → all-zero. When
    ``required`` is True (the component must be *present*), a missing column is a
    likely typo and raises with the available component names.
    """
    col = _resolve_column(df, component)
    if col is None:
        if required:
            available = sorted(
                c[len(_PREFIX):] for c in _component_columns(df)
            )
            raise KeyError(
                f"No mole-fraction column for component {component!r}. "
                f"Available components: {available}."
            )
        return np.zeros(len(df), dtype=float)
    return pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=float)


# --- selector base ------------------------------------------------------------


class FluidSelector:
    """Base class: anything that turns a DataFrame into a boolean row mask.

    Combine selectors with ``&`` (and), ``|`` (or) and ``~`` (not). Call a
    selector on a DataFrame to get the mask, or chain ``.ratio(...)`` /
    ``.where(...)`` / ``.contains(...)`` to AND further constraints onto it.
    """

    def mask(self, df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError

    def __call__(self, df: pd.DataFrame) -> pd.Series:
        return self.mask(df)

    # boolean algebra
    def __and__(self, other: "FluidSelector") -> "FluidSelector":
        return _And(self, _coerce(other))

    def __or__(self, other: "FluidSelector") -> "FluidSelector":
        return _Or(self, _coerce(other))

    def __invert__(self) -> "FluidSelector":
        return _Not(self)

    # chainers (AND an extra constraint onto this selector)
    def ratio(self, tol: float = 1e-3, **shares: float) -> "FluidSelector":
        """AND a sub-ratio constraint among named components (see :class:`RatioSelector`)."""
        return self & RatioSelector(shares, tol=tol)

    def where(
        self, column: str, low: Optional[float] = None, high: Optional[float] = None
    ) -> "FluidSelector":
        """AND an inclusive numeric range on any column."""
        return self & RangeSelector(column, low=low, high=high)

    def contains(self, *components: str) -> "FluidSelector":
        """AND a requirement that the named components are present (others allowed)."""
        return self & SystemSelector(components, exact=False)


def _coerce(obj: Any) -> FluidSelector:
    if isinstance(obj, FluidSelector):
        return obj
    if callable(obj):
        return Predicate(obj)
    raise TypeError(
        f"Cannot combine FluidSelector with {type(obj).__name__}; expected a "
        "FluidSelector or a callable df -> mask."
    )


# --- concrete selectors -------------------------------------------------------


class SystemSelector(FluidSelector):
    """Select rows whose fluid system matches a set of components.

    Args:
        components: Component names that must be **present** (fraction > 0).
        exact: When True (default) every *other* component must be absent
            (fraction ≈ 0), so the system is exactly ``components``. When False
            the named components must be present but extra ones are allowed.
        absent_tol: Threshold below which a component counts as absent.
    """

    def __init__(
        self,
        components: Sequence[str],
        *,
        exact: bool = True,
        absent_tol: float = _DEFAULT_ABSENT_TOL,
    ) -> None:
        if not components:
            raise ValueError("system() needs at least one component name.")
        self.components = tuple(components)
        self.exact = exact
        self.absent_tol = absent_tol

    def mask(self, df: pd.DataFrame) -> pd.Series:
        present_lower = {c.strip().lower() for c in self.components}
        mask = pd.Series(True, index=df.index)
        # every named component must be present
        for comp in self.components:
            mask &= _fractions(df, comp, required=True) > self.absent_tol
        if self.exact:
            # every other component column must be ~ absent. NaN means the
            # component simply isn't part of this row's fluid (it shows up only
            # because concatenating multi-system documents unions the columns),
            # so NaN counts as absent just like an explicit 0.0.
            for col in _component_columns(df):
                comp_name = col[len(_PREFIX):]
                if comp_name.strip().lower() in present_lower:
                    continue
                vals = pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=float)
                absent = np.isnan(vals) | (np.abs(vals) <= self.absent_tol)
                mask &= absent
        return mask

    def __repr__(self) -> str:
        kind = "exact" if self.exact else "contains"
        return f"SystemSelector({list(self.components)}, {kind})"


class RatioSelector(FluidSelector):
    """Pin the proportions among a subset of components, ignoring the rest.

    ``ratio(glycerol=1, methanol=2)`` keeps rows where, *within* the named
    components, the mole fractions sit at 1:2 — i.e. normalised shares of
    ``{1/3, 2/3}`` — within ``tol``. Components outside the set (e.g. water) are
    free to vary. Rows where all named components are absent never match.

    Args:
        shares: Relative amounts per component (any positive scale; normalised
            internally). Needs at least two components.
        tol: Absolute tolerance on each normalised share.
    """

    def __init__(self, shares: Mapping[str, float], *, tol: float = 1e-3) -> None:
        if len(shares) < 2:
            raise ValueError("ratio() needs at least two components, e.g. a=1, b=2.")
        total = float(sum(shares.values()))
        if total <= 0:
            raise ValueError("ratio() shares must sum to a positive number.")
        self.targets = {c: float(v) / total for c, v in shares.items()}
        self.tol = tol

    def mask(self, df: pd.DataFrame) -> pd.Series:
        comps = list(self.targets)
        fracs = {c: _fractions(df, c, required=True) for c in comps}
        subset_sum = np.sum([fracs[c] for c in comps], axis=0)
        with np.errstate(divide="ignore", invalid="ignore"):
            present = subset_sum > _DEFAULT_ABSENT_TOL
            mask = present.copy()
            for comp, target in self.targets.items():
                share = np.where(present, fracs[comp] / subset_sum, np.nan)
                mask &= present & (np.abs(share - target) <= self.tol)
        return pd.Series(mask, index=df.index)

    def __repr__(self) -> str:
        ratio = ":".join(f"{c}={v:.3g}" for c, v in self.targets.items())
        return f"RatioSelector({ratio}, tol={self.tol})"


class RangeSelector(FluidSelector):
    """Keep rows where ``column`` lies in the inclusive ``[low, high]`` range."""

    def __init__(
        self, column: str, *, low: Optional[float] = None, high: Optional[float] = None
    ) -> None:
        if low is None and high is None:
            raise ValueError("where() needs at least one of low / high.")
        self.column = column
        self.low = low
        self.high = high

    def mask(self, df: pd.DataFrame) -> pd.Series:
        if self.column not in df.columns:
            raise KeyError(
                f"where() references unknown column {self.column!r}. "
                f"Available: {list(df.columns)}"
            )
        vals = pd.to_numeric(df[self.column], errors="coerce")
        mask = pd.Series(True, index=df.index)
        if self.low is not None:
            mask &= vals >= self.low
        if self.high is not None:
            mask &= vals <= self.high
        return mask.fillna(False)

    def __repr__(self) -> str:
        return f"RangeSelector({self.column!r}, low={self.low}, high={self.high})"


class Predicate(FluidSelector):
    """Escape hatch: wrap an arbitrary ``df -> boolean mask`` callable."""

    def __init__(self, func: Callable[[pd.DataFrame], Any]) -> None:
        self.func = func

    def mask(self, df: pd.DataFrame) -> pd.Series:
        result = self.func(df)
        return pd.Series(np.asarray(result, dtype=bool), index=df.index)


# --- combinators --------------------------------------------------------------


class _And(FluidSelector):
    def __init__(self, left: FluidSelector, right: FluidSelector) -> None:
        self.left, self.right = left, right

    def mask(self, df: pd.DataFrame) -> pd.Series:
        return self.left.mask(df) & self.right.mask(df)

    def __repr__(self) -> str:
        return f"({self.left!r} & {self.right!r})"


class _Or(FluidSelector):
    def __init__(self, left: FluidSelector, right: FluidSelector) -> None:
        self.left, self.right = left, right

    def mask(self, df: pd.DataFrame) -> pd.Series:
        return self.left.mask(df) | self.right.mask(df)

    def __repr__(self) -> str:
        return f"({self.left!r} | {self.right!r})"


class _Not(FluidSelector):
    def __init__(self, inner: FluidSelector) -> None:
        self.inner = inner

    def mask(self, df: pd.DataFrame) -> pd.Series:
        return ~self.inner.mask(df)

    def __repr__(self) -> str:
        return f"~{self.inner!r}"


# --- public factories ---------------------------------------------------------


def system(*components: str, exact: bool = True) -> SystemSelector:
    """Select a fluid system by its components (exact set by default)."""
    return SystemSelector(components, exact=exact)


def contains(*components: str) -> SystemSelector:
    """Select rows where the named components are present (extras allowed)."""
    return SystemSelector(components, exact=False)


def ratio(tol: float = 1e-3, **shares: float) -> RatioSelector:
    """Select rows where named components hold the given proportions."""
    return RatioSelector(shares, tol=tol)


def where(
    column: str, low: Optional[float] = None, high: Optional[float] = None
) -> RangeSelector:
    """Select rows where ``column`` is within ``[low, high]``."""
    return RangeSelector(column, low=low, high=high)


__all__ = [
    "FluidSelector",
    "SystemSelector",
    "RatioSelector",
    "RangeSelector",
    "Predicate",
    "system",
    "contains",
    "ratio",
    "where",
]
