"""
Generische Prädikate und Filter für ``MeasurementView`` (komponenten-agnostisch).

Molanteile kommen aus ``mole_fractions`` (wie von ``_extract_measurements_with_all_parameters``
befüllt). Zusätzliche Größen (z. B. **Mass fraction**) stehen oft in ``extra_parameters``;
dafür gibt es Hilfs-Prädikate über Schlüssel-Teilstrings.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any, Optional, Union

from .measurement_views import MeasurementView


def _norm(s: str) -> str:
    return str(s).strip().lower().replace(" ", "")


def mole_fraction(view: MeasurementView, *name_substrings: str) -> Optional[float]:
    """
    Molanteil der ersten ``fluid_compounds``-Zeile, deren normalisierter Name alle
    ``name_substrings`` enthält (Teilstrings, case-insensitive).
    """
    for i, comp in enumerate(view.fluid_compounds):
        key = _norm(comp)
        if all(sub.lower().replace(" ", "") in key for sub in name_substrings):
            if i < len(view.mole_fractions):
                raw = view.mole_fractions[i]
                if raw is None:
                    return None
                try:
                    return float(raw)
                except (TypeError, ValueError):
                    return None
    return None


def extra_parameter_float(view: MeasurementView, key_substring: str) -> Optional[float]:
    """Erster numerischer Wert aus ``extra_parameters``, dessen Schlüssel ``key_substring`` enthält."""
    needle = key_substring.lower()
    for k, val in view.extra_parameters.items():
        if needle not in str(k).lower():
            continue
        try:
            return float(val)
        except (TypeError, ValueError):
            continue
    return None


def filter_views(
    views: Iterable[MeasurementView],
    predicate: Callable[[MeasurementView], bool],
) -> list[MeasurementView]:
    """Alle Views, für die ``predicate`` True ist."""
    return [v for v in views if predicate(v)]


def pred_all(
    *predicates: Callable[[MeasurementView], bool],
) -> Callable[[MeasurementView], bool]:
    """AND über mehrere Prädikate."""

    def p(v: MeasurementView) -> bool:
        return all(q(v) for q in predicates)

    return p


def pred_any(
    *predicates: Callable[[MeasurementView], bool],
) -> Callable[[MeasurementView], bool]:
    """OR über mehrere Prädikate."""

    def p(v: MeasurementView) -> bool:
        return any(q(v) for q in predicates)

    return p


def pred_not(
    predicate: Callable[[MeasurementView], bool],
) -> Callable[[MeasurementView], bool]:
    return lambda v: not predicate(v)


def pred_compound_min_mole_fraction(
    *name_substrings: str,
    min_value: float = 1e-8,
) -> Callable[[MeasurementView], bool]:
    """Mind. ``min_value`` Molanteil für die per Teilstrings gewählte Komponente."""

    def p(v: MeasurementView) -> bool:
        mf = mole_fraction(v, *name_substrings)
        return mf is not None and mf > min_value

    return p


def pred_fluid_component_count(n: int) -> Callable[[MeasurementView], bool]:
    """Genau ``n`` Einträge in ``fluid_compounds``."""
    return lambda v: len(v.fluid_compounds) == n


def pred_mole_ratio_close(
    numerator_name_parts: tuple[str, ...],
    denominator_name_parts: tuple[str, ...],
    target_ratio: float,
    *,
    abs_tol: float = 0.06,
) -> Callable[[MeasurementView], bool]:
    """
    Prüft ``mole_fraction(num) / mole_fraction(den) ≈ target_ratio`` (bei definierten,
    positiven Nenner-Molanteilen).
    """

    def p(v: MeasurementView) -> bool:
        xn = mole_fraction(v, *numerator_name_parts)
        xd = mole_fraction(v, *denominator_name_parts)
        if xn is None or xd is None or xd <= 1e-12:
            return False
        return abs(xn / xd - target_ratio) < abs_tol

    return p


def pred_extra_numeric_in_range(
    key_substring: str,
    lo: float,
    hi: float,
) -> Callable[[MeasurementView], bool]:
    """
    Extra-Parameter (z. B. ``Mass fraction``) liegt numerisch in ``[lo, hi]``.
    Nützlich für Dateien ohne vollständige Molanteil-Zuordnung in ``mole_fractions``.
    """

    def p(v: MeasurementView) -> bool:
        x = extra_parameter_float(v, key_substring)
        if x is None:
            return False
        return lo <= x <= hi

    return p


def pred_property_type_in(
    *allowed: Union[str, Sequence[str]],
) -> Callable[[MeasurementView], bool]:
    """Nur Views, deren ``property_type`` in der erlaubten Menge liegt."""
    flat: set[str] = set()
    for a in allowed:
        if isinstance(a, (list, tuple, set)):
            flat.update(str(x) for x in a)
        else:
            flat.add(str(a))

    def p(v: MeasurementView) -> bool:
        return str(v.property_type) in flat

    return p


def inspect_views_composition(
    views: Sequence[MeasurementView],
) -> dict[str, Any]:
    """
    Sammelt alle in den Views vorkommenden Stoff-/Parameter-Labels (ohne Annahme zu Namen).

    Rückgabe u. a. für Notebooks: ``pprint.pp(inspect_views_composition(all_views))``.
    """
    fluid_labels: set[str] = set()
    extra_keys: set[str] = set()
    prop_types: set[str] = set()
    for v in views:
        fluid_labels.update(str(c) for c in v.fluid_compounds)
        extra_keys.update(str(k) for k in v.extra_parameters.keys())
        prop_types.add(str(v.property_type))
    return {
        "n_views": len(views),
        "fluid_compound_labels": sorted(fluid_labels, key=str.lower),
        "extra_parameter_keys": sorted(extra_keys, key=str.lower),
        "property_types": sorted(prop_types, key=str.lower),
    }


def inspect_documents_compounds(docs: Sequence[Any]) -> list[dict[str, Any]]:
    """
    ``compound``-Einträge pro Dokument (``commonName`` / ``compoundID``), wie im Schema.
    """
    from .measurement_views import compound_display_names

    return [
        {"document_index": i, "compounds": compound_display_names(d)}
        for i, d in enumerate(docs)
    ]


def pred_composition(
    *,
    min_mole_fractions: Optional[list[tuple[tuple[str, ...], float]]] = None,
    mole_ratio: Optional[tuple[tuple[str, ...], tuple[str, ...], float]] = None,
    mole_ratio_tol: float = 0.06,
    n_fluid_components: Optional[int] = None,
    exclude_min_mole_fractions: Optional[list[tuple[tuple[str, ...], float]]] = None,
) -> Callable[[MeasurementView], bool]:
    """
    Kombiniert mehrere Kompositions-Bedingungen (AND).

    Args:
        min_mole_fractions: z. B. ``[(("water",), 1e-8)]`` → Molanteil Wasser > Schwelle.
        mole_ratio: ``(Zähler-Teilstrings, Nenner-Teilstrings, Zielratio)`` z. B.
            ``(("choline",), ("glycerol",), 0.5)`` für x_ChCl/x_Gly ≈ 1/2.
        mole_ratio_tol: Toleranz für die Ratio.
        n_fluid_components: exakte Anzahl ``fluid_compounds``.
        exclude_min_mole_fractions: jede Bedingung wird negiert (z. B. kein nennenswertes Wasser:
            ``exclude_min_mole_fractions=[(("water",), 1e-8)]``).

    Ohne ein gesetztes Argument ist das Prädikat für jede View ``True`` (Vorsicht bei leeren Aufrufen).
    """
    parts: list[Callable[[MeasurementView], bool]] = []

    if min_mole_fractions:
        for name_parts, mv in min_mole_fractions:
            parts.append(pred_compound_min_mole_fraction(*name_parts, min_value=mv))

    if mole_ratio is not None:
        num_parts, den_parts, target = mole_ratio
        parts.append(
            pred_mole_ratio_close(
                num_parts,
                den_parts,
                target,
                abs_tol=mole_ratio_tol,
            )
        )

    if n_fluid_components is not None:
        parts.append(pred_fluid_component_count(n_fluid_components))

    if exclude_min_mole_fractions:
        for name_parts, mv in exclude_min_mole_fractions:
            parts.append(
                pred_not(pred_compound_min_mole_fraction(*name_parts, min_value=mv))
            )

    if not parts:
        return lambda _v: True

    return pred_all(*parts)


def dedupe_views(views: Sequence[MeasurementView]) -> list[MeasurementView]:
    """Deduplizierung nach (document_index, measurement_id, DOI, T, property_value)."""
    seen: set[tuple] = set()
    out: list[MeasurementView] = []
    for v in views:
        key = (
            v.document_index,
            v.measurement_id,
            v.source_doi,
            v.temperature,
            v.property_value,
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out


def union_filtered(
    views: Iterable[MeasurementView],
    *predicates: Callable[[MeasurementView], bool],
) -> list[MeasurementView]:
    """Vereinigung der Trefferlisten mehrerer Prädikate, dedupliziert."""
    acc: list[MeasurementView] = []
    for pred in predicates:
        acc.extend(filter_views(views, pred))
    return dedupe_views(acc)
