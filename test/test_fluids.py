"""Tests for the composable fluid-system selector algebra (``analysis.fluids``).

Pure pandas/numpy — no FAIRFluids documents, no JAX/NumPyro. Mirrors the three
real user needs: pick one exact system, a union of systems, and a ternary with a
pinned sub-ratio while a third component varies.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from fairfluids.analysis import fluids as flu


def _frame() -> pd.DataFrame:
    rows = [
        # glycerol, methanol, water, label
        (0.20, 0.30, 0.50, "GMW-a"),  # ternary, G:M = 2:3
        (0.10, 0.20, 0.70, "GMW-b"),  # ternary, G:M = 1:2
        (0.00, 0.40, 0.60, "MW"),     # methanol-water
        (0.00, 0.00, 1.00, "pureW"),  # pure water
        (0.05, 0.10, 0.85, "GMW-c"),  # ternary, G:M = 1:2
        (0.30, 0.00, 0.70, "GW"),     # glycerol-water
    ]
    return pd.DataFrame(
        {
            "mole_fraction_glycerol": [r[0] for r in rows],
            "mole_fraction_methanol": [r[1] for r in rows],
            "mole_fraction_water": [r[2] for r in rows],
            "label": [r[3] for r in rows],
        }
    )


def _kept(sel) -> list[str]:
    df = _frame()
    return sorted(df[sel(df)]["label"].tolist())


def test_system_exact_selects_only_the_ternary():
    assert _kept(flu.system("glycerol", "methanol", "water")) == ["GMW-a", "GMW-b", "GMW-c"]


def test_union_of_systems():
    sel = flu.system("glycerol", "methanol", "water") | flu.system("water")
    assert _kept(sel) == ["GMW-a", "GMW-b", "GMW-c", "pureW"]


def test_ratio_pins_subratio_with_third_component_free():
    sel = flu.system("glycerol", "methanol", "water").ratio(glycerol=1, methanol=2)
    assert _kept(sel) == ["GMW-b", "GMW-c"]


def test_contains_is_subset_match_allowing_extras():
    assert _kept(flu.contains("methanol")) == ["GMW-a", "GMW-b", "GMW-c", "MW"]


def test_chained_ratio_and_range():
    sel = (
        flu.system("glycerol", "methanol", "water")
        .ratio(glycerol=1, methanol=2)
        .where("mole_fraction_water", low=0.8)
    )
    assert _kept(sel) == ["GMW-c"]


def test_not_and_case_insensitive_component_names():
    assert _kept(~flu.contains("Glycerol")) == ["MW", "pureW"]


def test_exact_false_via_system_kw_equals_contains():
    assert _kept(flu.system("methanol", exact=False)) == _kept(flu.contains("methanol"))


def test_missing_component_raises_with_available_names():
    with pytest.raises(KeyError, match="Available components"):
        flu.system("glyserol", "water")(_frame())


def test_ratio_needs_two_components():
    with pytest.raises(ValueError, match="at least two components"):
        flu.ratio(glycerol=1)


def test_where_needs_a_bound():
    with pytest.raises(ValueError, match="low / high"):
        flu.where("mole_fraction_water")


def test_selector_is_callable_and_returns_boolean_series():
    df = _frame()
    mask = flu.system("water")(df)
    assert isinstance(mask, pd.Series)
    assert mask.dtype == bool
    assert mask.index.equals(df.index)


def test_predicate_escape_hatch_combines_with_algebra():
    sel = flu.contains("methanol") & (lambda d: d["mole_fraction_water"] >= 0.65)
    assert _kept(sel) == ["GMW-b", "GMW-c"]


def test_ratio_tolerance_is_respected():
    df = _frame().copy()
    # nudge GMW-b slightly off 1:2 (0.101 : 0.20 -> share ~0.3355)
    df.loc[1, "mole_fraction_glycerol"] = 0.101
    tight = flu.system("glycerol", "methanol", "water").ratio(glycerol=1, methanol=2, tol=1e-4)
    loose = flu.system("glycerol", "methanol", "water").ratio(glycerol=1, methanol=2, tol=1e-2)
    assert "GMW-b" not in sorted(df[tight(df)]["label"])
    assert "GMW-b" in sorted(df[loose(df)]["label"])
