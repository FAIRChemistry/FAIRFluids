"""
Platzhalter-Typen für abgeleitete Größen (z. B. Arrhenius-Fits).

Beim Merge ins Hauptprojekt hier konkrete Felder ergänzen und ggf. mit
``FAIRFluidsDocument`` oder Sidecar-JSON serialisieren.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Sequence, Tuple


def _norm_compound_label(s: str) -> str:
    return str(s).strip().lower().replace(" ", "")


@dataclass(frozen=True)
class ArrheniusGroupKey:
    """
    Gruppierungsschlüssel für Fits (analog zu ``fit_arrhenius``).

    ``fluid_compounds`` und ``mole_fractions`` sind parallel indiziert
    (wie in :class:`MeasurementView` aus der Extraktion).
    """

    source_doi: Optional[str]
    fluid_compounds: Tuple[str, ...]
    mole_fractions: Tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.fluid_compounds) != len(self.mole_fractions):
            raise ValueError(
                "fluid_compounds und mole_fractions müssen gleiche Länge haben: "
                f"{len(self.fluid_compounds)} vs. {len(self.mole_fractions)}"
            )


def group_key_mole_fraction(
    key: ArrheniusGroupKey, *name_substrings: str
) -> Optional[float]:
    """
    Molanteil der ersten Komponente in ``fluid_compounds``, deren normalisierter Name
    alle ``name_substrings`` enthält (wie :func:`thin_layer.view_filters.mole_fraction`).
    """
    for comp, x in zip(key.fluid_compounds, key.mole_fractions):
        cn = _norm_compound_label(comp)
        if all(sub.lower().replace(" ", "") in cn for sub in name_substrings):
            return float(x)
    return None


def group_key_mole_fraction_or_zero(
    key: ArrheniusGroupKey, *name_substrings: str
) -> float:
    """
    Wie :func:`group_key_mole_fraction`, aber wenn die Komponente in dieser Gruppe
    nicht vorkommt (z. B. binäres ChCl–Gly ohne Wasser), wird ``0.0`` zurückgegeben —
    sinnvoll für gemeinsame x-Achse „Wasser-Molanteil“ über ternäre und binäre Fluide.
    """
    v = group_key_mole_fraction(key, *name_substrings)
    return 0.0 if v is None else float(v)


def group_key_mole_fractions_for_components(
    key: ArrheniusGroupKey,
    component_selectors: Sequence[tuple[str, ...]],
    *,
    fill_missing_with_zero: bool = True,
) -> tuple[float, ...]:
    """
    Liefert einen Molanteils-Vektor fester Länge in der Reihenfolge von
    ``component_selectors`` (jede innere Sequenz = Teilstrings wie bei
    ``group_key_mole_fraction``).

    Fehlt eine Komponente in ``fluid_compounds``, wird bei
    ``fill_missing_with_zero=True`` ``0.0`` gesetzt (sonst ``ValueError``).
    """
    out: list[float] = []
    for subs in component_selectors:
        v = group_key_mole_fraction(key, *subs)
        if v is None:
            if not fill_missing_with_zero:
                raise ValueError(
                    f"Komponente {subs!r} in group_key nicht gefunden: {key!r}"
                )
            out.append(0.0)
        else:
            out.append(float(v))
    return tuple(out)


@dataclass
class ArrheniusFitBundle:
    """
    Container für ein Arrhenius-Ergebnis pro Gruppe.

    Unsicherheiten der OLS-Regression (``np.polyfit(..., cov=True)``), analog zu
    :func:`fairfluids.core.functionalities.fit_arrhenius`: ``Ea_J_mol_std`` = ``slope_std``,
    ``lnAs_std`` = ``intercept_std``, ``As_std`` ≈ ``As * lnAs_std`` (log-Normal-Näherung).

    ``viscosity_uncertainty_mean``: Mittelwert der Mess-Unsicherheiten in der Gruppe
    (falls ``MeasurementView.uncertainty`` gesetzt), nur informativ / für Metadaten.
    """

    group_key: ArrheniusGroupKey
    Ea_J_mol: float
    lnAs: float
    n_points: int
    measurement_ids: tuple[str, ...] = field(default_factory=tuple)
    R_squared: Optional[float] = None
    T_min_K: Optional[float] = None
    T_max_K: Optional[float] = None
    As: Optional[float] = None
    Ea_J_mol_std: Optional[float] = None
    Ea_kJ_mol_std: Optional[float] = None
    lnAs_std: Optional[float] = None
    As_std: Optional[float] = None
    viscosity_uncertainty_mean: Optional[float] = None
    meta: dict[str, Any] = field(default_factory=dict)
