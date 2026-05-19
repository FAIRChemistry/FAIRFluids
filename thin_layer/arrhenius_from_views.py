"""
Arrhenius-Regression (ln η vs. 1/(R·T)) aus ``MeasurementView``-Sequenzen.

Konventionen wie ``fairfluids.core.functionalities.fit_arrhenius``:
x_modell = 1/(R·T), Steigung = Ea [J/mol], Achsenabschnitt = ln(As).
Plot-x = 1000/(R·T) (mol kJ⁻¹).
"""

from __future__ import annotations

import colorsys
import hashlib
from collections import defaultdict
from typing import Any, Literal, Optional, Sequence, Tuple

import numpy as np

from .fit_types import (
    ArrheniusFitBundle,
    ArrheniusGroupKey,
    group_key_mole_fraction,
    group_key_mole_fraction_or_zero,
)
from .measurement_views import MeasurementView

R_GAS = 8.314462618  # J/(mol·K)


def _string_to_hex_color(s: str, sat: float = 0.65, val: float = 0.85) -> str:
    """Deterministically map strings to hex colors (used for DOI coloring)."""
    h = hashlib.sha256(str(s).encode()).hexdigest()
    h_int = int(h[:8], 16)
    hue = (h_int * 0.618033988749895) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))


def _gray_blue_component_colormap() -> Any:
    """Hellgrau → Blau (nicht von Weiß), für ``color_by='component'``."""
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list(
        "gray_blue_component",
        ["#d6d6d6", "#bdd9ef", "#74b3d8", "#2b8cbe", "#045a8d"],
        N=256,
    )


def _molefraction_gray_blue_colors(
    xa: np.ndarray,
) -> tuple[list[str], Any, Any]:
    """Mappt Molanteil-Werte auf Hex-Farben; liefert auch ``norm`` und ``cmap`` für eine Colorbar."""
    from matplotlib.colors import Normalize, to_hex

    cmap = _gray_blue_component_colormap()
    if xa.size == 0:
        return [], Normalize(0.0, 1.0), cmap
    vmin = float(np.nanmin(xa))
    vmax = float(np.nanmax(xa))
    if not (np.isfinite(vmin) and np.isfinite(vmax)):
        return ["#d6d6d6"] * int(xa.size), Normalize(0.0, 1.0), cmap
    if np.isclose(vmin, vmax):
        vmin = max(0.0, vmin - 1e-6)
        vmax = min(1.0, vmax + 1e-6)
    norm = Normalize(vmin=vmin, vmax=vmax)
    out: list[str] = []
    for xv in xa:
        t = float(norm(float(xv)))
        out.append(to_hex(cmap(t)))
    return out, norm, cmap


def _finite_or_none(x: float) -> Optional[float]:
    v = float(x)
    return v if np.isfinite(v) else None


def _arrhenius_ols_fit_stats(x_model: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    """
    OLS auf ``y`` vs. ``x_model`` = 1/(R·T); Steigung = Ea [J/mol], Achsenabschnitt = ln(As).

    Standardfehler aus ``np.polyfit(..., cov=True)`` — gleiche Konvention wie
    :func:`fairfluids.core.functionalities.fit_arrhenius`.
    """
    x_model = np.asarray(x_model, dtype=float)
    y = np.asarray(y, dtype=float)
    slope_std = float("nan")
    intercept_std = float("nan")
    try:
        p, cov = np.polyfit(x_model, y, 1, cov=True)
        slope, intercept = float(p[0]), float(p[1])
        if getattr(cov, "shape", None) == (2, 2):
            slope_std = (
                float(np.sqrt(cov[0, 0])) if np.isfinite(cov[0, 0]) else float("nan")
            )
            intercept_std = (
                float(np.sqrt(cov[1, 1])) if np.isfinite(cov[1, 1]) else float("nan")
            )
    except (TypeError, ValueError, np.linalg.LinAlgError):
        coeff = np.polyfit(x_model, y, 1)
        slope, intercept = float(coeff[0]), float(coeff[1])
    if not np.isfinite(slope_std):
        slope_std = float("nan")
    if not np.isfinite(intercept_std):
        intercept_std = float("nan")

    y_pred = slope * x_model + intercept
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r_sq: Optional[float] = None if ss_tot == 0.0 else float(1.0 - (ss_res / ss_tot))

    ln_as = float(intercept)
    as_val = float(np.exp(ln_as))
    ln_as_std = intercept_std if np.isfinite(intercept_std) else float("nan")
    as_std = as_val * ln_as_std if np.isfinite(ln_as_std) else float("nan")
    ea_j_std = slope_std if np.isfinite(slope_std) else float("nan")
    ea_kj_std = ea_j_std / 1000.0 if np.isfinite(ea_j_std) else float("nan")

    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "slope_std": slope_std,
        "intercept_std": intercept_std,
        "R_squared": r_sq,
        "Ea_J_mol": float(slope),
        "lnAs": ln_as,
        "As": as_val,
        "lnAs_std": ln_as_std,
        "As_std": as_std,
        "Ea_J_mol_std": ea_j_std,
        "Ea_kJ_mol_std": ea_kj_std,
    }


def _viscosity_uncertainty_mean_from_views(
    views: Sequence[MeasurementView],
) -> Optional[float]:
    vals: list[float] = []
    for v in views:
        if v.uncertainty is None:
            continue
        try:
            vals.append(float(v.uncertainty))
        except (TypeError, ValueError):
            continue
    if not vals:
        return None
    return float(np.mean(vals))


def _arrhenius_fit_bundle_from_stats(
    *,
    group_key: ArrheniusGroupKey,
    pts: Sequence[tuple[float, float, MeasurementView]],
    stats: dict[str, Any],
    meta_extra: Optional[dict[str, Any]] = None,
) -> ArrheniusFitBundle:
    views_in_group = [p[2] for p in pts]
    temps = [float(w.temperature) for w in views_in_group if w.temperature is not None]
    t_min = min(temps) if temps else None
    t_max = max(temps) if temps else None
    mids: list[str] = []
    for w in views_in_group:
        if w.measurement_id is not None:
            mids.append(str(w.measurement_id))
    meta: dict[str, Any] = {
        "slope": stats["slope"],
        "intercept": stats["intercept"],
        "slope_std": stats["slope_std"],
        "intercept_std": stats["intercept_std"],
    }
    if meta_extra:
        meta.update(meta_extra)
    return ArrheniusFitBundle(
        group_key=group_key,
        Ea_J_mol=stats["Ea_J_mol"],
        lnAs=stats["lnAs"],
        n_points=len(pts),
        measurement_ids=tuple(mids),
        R_squared=stats["R_squared"],
        T_min_K=t_min,
        T_max_K=t_max,
        As=float(stats["As"]),
        Ea_J_mol_std=_finite_or_none(float(stats["Ea_J_mol_std"])),
        Ea_kJ_mol_std=_finite_or_none(float(stats["Ea_kJ_mol_std"])),
        lnAs_std=_finite_or_none(float(stats["lnAs_std"])),
        As_std=_finite_or_none(float(stats["As_std"])),
        viscosity_uncertainty_mean=_viscosity_uncertainty_mean_from_views(
            views_in_group
        ),
        meta=meta,
    )


# Interner Gruppenschlüssel: (DOI, normalisierte Komponentenlabels, gerundete Molbrüche)
_ArrheniusPlotGroupKey = tuple[Any, tuple[str, ...], tuple[float, ...]]


def _norm_compound_label(s: str) -> str:
    return str(s).strip().lower().replace(" ", "")


def _group_tuple_from_view(v: MeasurementView) -> tuple[str, ...]:
    return tuple(_norm_compound_label(str(c)) for c in (v.fluid_compounds or []))


def _normalize_molefractions_key(
    mf: list[Any], *, molefrac_round: int
) -> Optional[tuple[float, ...]]:
    if not isinstance(mf, (list, tuple)) or not mf:
        return None
    out: list[float] = []
    for x in mf:
        if x is None:
            return None
        try:
            out.append(round(float(x), molefrac_round))
        except (TypeError, ValueError):
            return None
    return tuple(out)


def _group_key_for_view(
    v: MeasurementView, *, molefrac_round: int
) -> Optional[_ArrheniusPlotGroupKey]:
    mf_key = _normalize_molefractions_key(
        v.mole_fractions, molefrac_round=molefrac_round
    )
    if mf_key is None:
        return None
    comps = list(v.fluid_compounds or [])
    if len(comps) != len(mf_key):
        return None
    doi = v.source_doi
    comp_key = _group_tuple_from_view(v)
    return (doi, comp_key, mf_key)


def _view_to_arrhenius_point(
    v: MeasurementView,
    *,
    property_type: Optional[str],
) -> Optional[tuple[float, float, MeasurementView]]:
    if property_type is not None and str(v.property_type) != str(property_type):
        return None
    T = v.temperature
    eta = v.property_value
    if T is None or eta is None:
        return None
    try:
        Tf = float(T)
        etaf = float(eta)
    except (TypeError, ValueError):
        return None
    if Tf <= 0 or etaf <= 0:
        return None
    x_model = 1.0 / (R_GAS * Tf)
    y = float(np.log(etaf))
    return (x_model, y, v)


def partition_views_for_arrhenius_plot(
    views: Sequence[MeasurementView],
    *,
    property_type: Optional[str] = "viscosity",
    molefrac_round: int = 6,
) -> tuple[
    dict[_ArrheniusPlotGroupKey, list[tuple[float, float, MeasurementView]]],
    list[tuple[float, float, MeasurementView]],
    int,
]:
    """
    Teilt Views in (a) gruppierte Arrhenius-Punkte, (b) „Waisen“ mit T und Property,
    aber ohne brauchbaren Molbruch-Schlüssel, (c) Zahl der komplett unplottbaren Views.

    Gruppenschlüssel: ``(source_doi, normalisierte Komponentennamen, gerundete Molbrüche)``.

    Nur (a) und (b) können im ln–1/(RT)-Diagramm erscheinen; (c) fehlt z. B. T oder η.
    """
    groups: dict[_ArrheniusPlotGroupKey, list[tuple[float, float, MeasurementView]]] = (
        defaultdict(list)
    )
    orphans: list[tuple[float, float, MeasurementView]] = []
    skipped_no_point = 0
    for v in views:
        pt = _view_to_arrhenius_point(v, property_type=property_type)
        if pt is None:
            skipped_no_point += 1
            continue
        gkey = _group_key_for_view(v, molefrac_round=molefrac_round)
        if gkey is None:
            orphans.append(pt)
        else:
            groups[gkey].append(pt)
    return dict(groups), orphans, skipped_no_point


def group_measurement_views_for_arrhenius(
    views: Sequence[MeasurementView],
    *,
    property_type: Optional[str] = "viscosity",
    molefrac_round: int = 6,
) -> dict[_ArrheniusPlotGroupKey, list[tuple[float, float, MeasurementView]]]:
    """
    Gruppiert gültige Messpunkte nach
    (``source_doi``, Komponenten-Reihenfolge, gerundete ``mole_fractions``).

    Jeder Eintrag ist eine Liste von Tupeln ``(x_model, ln(eta), view)``.
    Views ohne vollständige Molbrüche erscheinen hier **nicht** (dafür
    :func:`partition_views_for_arrhenius_plot`).
    """
    groups, _, _ = partition_views_for_arrhenius_plot(
        views, property_type=property_type, molefrac_round=molefrac_round
    )
    return groups


def fit_arrhenius_from_views(
    views: Sequence[MeasurementView],
    *,
    property_type: Optional[str] = "viscosity",
    min_points: int = 2,
    molefrac_round: int = 6,
) -> list[ArrheniusFitBundle]:
    """
    OLS-Arrhenius-Fit pro Gruppe (DOI + Komponentenlabels + Molbrüche).

    Standardabweichungen von ``Ea``, ``lnAs``, ``As`` wie in
    :func:`fairfluids.core.functionalities.fit_arrhenius` (Kovarianz der OLS-Koeffizienten).

    Gruppen mit weniger als ``min_points`` werden übersprungen (kein Eintrag).
    """
    bundles: list[ArrheniusFitBundle] = []
    grouped = group_measurement_views_for_arrhenius(
        views, property_type=property_type, molefrac_round=molefrac_round
    )
    for (doi, _comp_key, mf_key), pts in sorted(
        grouped.items(), key=lambda kv: (str(kv[0][0]), kv[0][1], kv[0][2])
    ):
        if len(pts) < min_points:
            continue
        x_model = np.array([p[0] for p in pts], dtype=float)
        y = np.array([p[1] for p in pts], dtype=float)
        views_in_group = [p[2] for p in pts]
        stats = _arrhenius_ols_fit_stats(x_model, y)
        rep = views_in_group[0]
        fluid_labels = tuple(str(c) for c in (rep.fluid_compounds or []))
        key = ArrheniusGroupKey(
            source_doi=doi, fluid_compounds=fluid_labels, mole_fractions=mf_key
        )
        bundles.append(
            _arrhenius_fit_bundle_from_stats(group_key=key, pts=pts, stats=stats)
        )
    return bundles


def plot_arrhenius_regression(
    views: Sequence[MeasurementView],
    *,
    ax: Any = None,
    figsize: Tuple[float, float] = (8.0, 5.0),
    property_type: Optional[str] = "viscosity",
    min_points: int = 2,
    molefrac_round: int = 6,
    marker_size: float = 28.0,
    line_width: float = 1.8,
    alpha_points: float = 0.75,
    color_skip_groups: str = "#9aa0a6",
    title: Optional[str] = None,
    grid_alpha: float = 0.2,
    plot_orphans_without_molefractions: bool = True,
    orphan_marker: str = "^",
    orphan_color: str = "#c44e52",
    print_coverage: bool = False,
    plot_measurement_uncertainty: bool = False,
    show_legend: bool = True,
) -> tuple[Any, Any, list[ArrheniusFitBundle]]:
    """
    Scatter ln(η) vs. 1000/(R·T) plus Arrhenius-Geraden pro gültiger Gruppe.

    Args:
        views: Folge von ``MeasurementView`` (typisch Viskosität + T + Zusammensetzung).
        ax: Optional bestehende Matplotlib-Achse; sonst neue Figure mit ``figsize``.
        property_type: Nur diese ``property_type``-Zeichenkette (``None`` = alle).
        min_points: Mindestzahl Punkte pro Gruppe für eine Regressionsgerade.
        molefrac_round: Rundung der Molbrüche für den Gruppenschlüssel.
        plot_orphans_without_molefractions: Zusätzlich Punkte mit T und η, aber ohne
            vollständige ``mole_fractions`` für den Gruppenschlüssel (keine Gerade).
        print_coverage: ``True`` → Kurz ``print`` mit Anzahl gruppiert / Waisen / übersprungen.
        plot_measurement_uncertainty: ``True`` → y-Fehlerbalken in ln-Raum
            (``d ln η ≈ σ_η / η``) wenn ``MeasurementView.uncertainty`` gesetzt ist — wie bei
            ``fit_arrhenius(..., viscosity_uncertainty_col=...)``.

    Returns:
        ``(fig, ax, bundles)`` — ``fig`` ist ``None``, wenn ``ax`` übergeben wurde.
        ``bundles`` enthält nur Gruppen mit erfolgreichem Fit (≥ ``min_points``).
    """
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    created_fig = ax is None
    if created_fig:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    grouped, orphans, skipped = partition_views_for_arrhenius_plot(
        views, property_type=property_type, molefrac_round=molefrac_round
    )
    if print_coverage:
        n_in_groups = sum(len(p) for p in grouped.values())
        print(
            f"[Arrhenius-Plot] Eingabe-Views: {len(views)} | "
            f"im Plot (gruppiert): {n_in_groups} | "
            f"ohne Molbruch-Schlüssel: {len(orphans)} | "
            f"ohne T/η/Property-Filter: {skipped}"
        )
    bundles: list[ArrheniusFitBundle] = []

    doi_with_fit: set[str] = set()
    for _, ((doi, _comp_key, mf_key), pts) in enumerate(
        sorted(grouped.items(), key=lambda kv: (str(kv[0][0]), kv[0][1], kv[0][2]))
    ):
        color = (
            _string_to_hex_color(str(doi or ""))
            if len(pts) >= min_points
            else color_skip_groups
        )
        x_model = np.array([p[0] for p in pts], dtype=float)
        y = np.array([p[1] for p in pts], dtype=float)
        x_plot = 1000.0 * x_model

        if len(pts) < min_points:
            ax.scatter(
                x_plot,
                y,
                s=marker_size,
                alpha=alpha_points,
                color=color,
                edgecolors="black",
                linewidths=0.25,
                zorder=2,
            )
            continue

        stats = _arrhenius_ols_fit_stats(x_model, y)
        slope = stats["slope"]
        intercept = stats["intercept"]
        rep = pts[0][2]
        fluid_labels = tuple(str(c) for c in (rep.fluid_compounds or []))
        gkey = ArrheniusGroupKey(
            source_doi=doi,
            fluid_compounds=fluid_labels,
            mole_fractions=mf_key,
        )
        bundles.append(
            _arrhenius_fit_bundle_from_stats(group_key=gkey, pts=pts, stats=stats)
        )
        doi_with_fit.add(str(doi))

        if plot_measurement_uncertainty:
            etaf_list: list[float] = []
            unc_list: list[float] = []
            for p in pts:
                w = p[2]
                if w.property_value is None:
                    etaf_list.append(float("nan"))
                else:
                    try:
                        etaf_list.append(float(w.property_value))
                    except (TypeError, ValueError):
                        etaf_list.append(float("nan"))
                if w.uncertainty is None:
                    unc_list.append(float("nan"))
                else:
                    try:
                        unc_list.append(float(w.uncertainty))
                    except (TypeError, ValueError):
                        unc_list.append(float("nan"))
            etaf = np.array(etaf_list, dtype=float)
            unc_vec = np.array(unc_list, dtype=float)
            if etaf.size == y.size and unc_vec.size == y.size:
                dy = np.divide(
                    unc_vec,
                    etaf,
                    out=np.full_like(unc_vec, np.nan),
                    where=etaf != 0,
                )
                mask_valid = np.isfinite(dy) & np.isfinite(x_plot) & np.isfinite(y)
                if np.any(mask_valid):
                    ax.errorbar(
                        x_plot[mask_valid],
                        y[mask_valid],
                        yerr=dy[mask_valid],
                        fmt="o",
                        ms=4,
                        alpha=alpha_points,
                        color=color,
                        ecolor=color,
                        elinewidth=1.2,
                        capsize=3,
                        capthick=1,
                        markeredgecolor="black",
                        markeredgewidth=0.2,
                        zorder=11,
                    )
                if np.any(~mask_valid):
                    ax.scatter(
                        x_plot[~mask_valid],
                        y[~mask_valid],
                        s=marker_size,
                        alpha=alpha_points,
                        color=color,
                        edgecolors="black",
                        linewidths=0.25,
                        zorder=10,
                    )
            else:
                ax.scatter(
                    x_plot,
                    y,
                    s=marker_size,
                    alpha=alpha_points,
                    color=color,
                    edgecolors="black",
                    linewidths=0.25,
                    zorder=3,
                )
        else:
            ax.scatter(
                x_plot,
                y,
                s=marker_size,
                alpha=alpha_points,
                color=color,
                edgecolors="black",
                linewidths=0.25,
                zorder=3,
            )
        x_line = np.linspace(float(np.min(x_plot)), float(np.max(x_plot)), 100)
        y_line = slope * (x_line / 1000.0) + intercept
        ax.plot(
            x_line,
            y_line,
            linestyle="--",
            linewidth=line_width,
            color=color,
            zorder=1,
        )

    if plot_orphans_without_molefractions and orphans:
        ox = np.array([1000.0 * p[0] for p in orphans], dtype=float)
        oy = np.array([p[1] for p in orphans], dtype=float)
        ax.scatter(
            ox,
            oy,
            s=marker_size * 0.85,
            alpha=0.9,
            color=orphan_color,
            marker=orphan_marker,
            edgecolors="black",
            linewidths=0.25,
            label="Valid T and eta, incomplete mole fractions",
            zorder=4,
        )

    ax.set_title(title or r"ln($\eta$) vs. (RT)$^{-1}$ mit Arrhenius-Geraden")
    ax.set_xlabel(r"(RT)$^{-1}$ / mol kJ$^{-1}$")
    ax.set_ylabel(r"ln($\eta$ / Pa$\cdot$s)")
    ax.grid(alpha=grid_alpha)
    if show_legend:
        legend_handles: list[Any] = []
        for doi in sorted(doi_with_fit):
            legend_handles.append(
                Line2D(
                    [0],
                    [0],
                    marker="o",
                    linestyle="None",
                    markerfacecolor=_string_to_hex_color(doi),
                    markeredgecolor="black",
                    markeredgewidth=0.3,
                    markersize=6,
                    label=doi,
                )
            )
        if plot_orphans_without_molefractions and orphans:
            legend_handles.append(
                Line2D(
                    [0],
                    [0],
                    marker=orphan_marker,
                    linestyle="None",
                    markerfacecolor=orphan_color,
                    markeredgecolor="black",
                    markeredgewidth=0.3,
                    markersize=6,
                    label="Valid T and eta, incomplete mole fractions",
                )
            )
        if legend_handles:
            ax.legend(handles=legend_handles, title="DOI", loc="best", fontsize=7)
    if created_fig:
        plt.tight_layout()
    return fig, ax, bundles


def plot_arrhenius_panels_combined(
    panel_specs: Sequence[tuple[str, Sequence[MeasurementView]]],
    *,
    ax: Any = None,
    figsize: Tuple[float, float] = (11.0, 6.5),
    property_type: Optional[str] = "viscosity",
    min_points: int = 2,
    molefrac_round: int = 6,
    marker_size: float = 22.0,
    line_width: float = 1.35,
    alpha_points: float = 0.78,
    grid_alpha: float = 0.2,
    color_skip_groups: str = "#9aa0a6",
    panel_markers: Sequence[str] = ("o", "s", "^", "D", "v", "P", "X"),
    title: Optional[str] = None,
) -> tuple[Any, Any, list[list[ArrheniusFitBundle]]]:
    """
    Alle ``PANEL_SPECS`` in **einer** Achse: pro Panel ein Marker, pro
    (DOI, Komponenten, Molbrüche)-Gruppe eine **deterministische Farbe aus dem DOI**
    (:func:`_string_to_hex_color`), inkl. Arrhenius-Geraden.

    Args:
        panel_specs: ``[(Titel, Views), ...]`` wie im Notebook.
        panel_markers: Marker pro Panel (zyklisch).

    Returns:
        ``(fig, ax, all_bundles)`` wobei ``all_bundles[i]`` die Bundles von ``panel_specs[i]`` sind.
    """
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    created_fig = ax is None
    if created_fig:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    all_bundles: list[list[ArrheniusFitBundle]] = []

    for pi, (panel_title, views) in enumerate(panel_specs):
        marker = panel_markers[pi % len(panel_markers)]
        grouped, orphans, _ = partition_views_for_arrhenius_plot(
            views, property_type=property_type, molefrac_round=molefrac_round
        )
        bundles_panel: list[ArrheniusFitBundle] = []

        for (doi, _comp_key, mf_key), pts in sorted(
            grouped.items(), key=lambda kv: (str(kv[0][0]), kv[0][1], kv[0][2])
        ):
            color = (
                _string_to_hex_color(str(doi or ""))
                if len(pts) >= min_points
                else color_skip_groups
            )
            x_model = np.array([p[0] for p in pts], dtype=float)
            y = np.array([p[1] for p in pts], dtype=float)
            x_plot = 1000.0 * x_model

            if len(pts) < min_points:
                ax.scatter(
                    x_plot,
                    y,
                    s=marker_size,
                    alpha=alpha_points,
                    color=color,
                    marker=marker,
                    edgecolors="black",
                    linewidths=0.2,
                    zorder=2,
                )
                continue

            stats = _arrhenius_ols_fit_stats(x_model, y)
            slope = stats["slope"]
            intercept = stats["intercept"]
            rep = pts[0][2]
            fluid_labels = tuple(str(c) for c in (rep.fluid_compounds or []))
            gkey = ArrheniusGroupKey(
                source_doi=doi,
                fluid_compounds=fluid_labels,
                mole_fractions=mf_key,
            )
            bundles_panel.append(
                _arrhenius_fit_bundle_from_stats(
                    group_key=gkey,
                    pts=pts,
                    stats=stats,
                    meta_extra={"panel_title": panel_title},
                )
            )

            ax.scatter(
                x_plot,
                y,
                s=marker_size,
                alpha=alpha_points,
                color=color,
                marker=marker,
                edgecolors="black",
                linewidths=0.2,
                zorder=3,
            )
            x_line = np.linspace(float(np.min(x_plot)), float(np.max(x_plot)), 100)
            y_line = slope * (x_line / 1000.0) + intercept
            ax.plot(
                x_line,
                y_line,
                linestyle="--",
                linewidth=line_width,
                color=color,
                zorder=1,
            )

        if orphans:
            ox = np.array([1000.0 * p[0] for p in orphans], dtype=float)
            oy = np.array([p[1] for p in orphans], dtype=float)
            ax.scatter(
                ox,
                oy,
                s=marker_size * 0.75,
                alpha=0.65,
                color="#888888",
                marker=marker,
                edgecolors="black",
                linewidths=0.15,
                zorder=1,
            )

        all_bundles.append(bundles_panel)

    ax.set_title(
        title
        or r"Alle Panel in einem Plot: ln($\eta$) vs. (RT)$^{-1}$ (Farbe = Fit-Gruppe, Marker = Panel)"
    )
    ax.set_xlabel(r"(RT)$^{-1}$ / mol kJ$^{-1}$")
    ax.set_ylabel(r"ln($\eta$ / Pa$\cdot$s)")
    ax.grid(alpha=grid_alpha)

    handles = [
        Line2D(
            [0],
            [0],
            marker=panel_markers[i % len(panel_markers)],
            linestyle="None",
            color="gray",
            markerfacecolor="lightgray",
            markeredgecolor="black",
            markeredgewidth=0.3,
            markersize=7,
            label=panel_specs[i][0],
        )
        for i in range(len(panel_specs))
    ]
    ax.legend(handles=handles, title="Panel (Marker)", loc="best", fontsize=8)

    if created_fig:
        plt.tight_layout()
    return fig, ax, all_bundles


def scatter_arrhenius_bundles_vs_component(
    bundles: Sequence[ArrheniusFitBundle],
    *,
    component_substrings: tuple[str, ...] = ("water",),
    y_field: str = "Ea_J_mol",
    fill_missing_component_with_zero: bool = True,
    plot_y_uncertainty: bool = True,
    color_by: Literal["doi", "uniform", "component"] = "doi",
    show_component_colorbar: bool = True,
    show_legend: bool = True,
    ax: Any = None,
    figsize: Tuple[float, float] = (7.0, 4.5),
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    title: Optional[str] = None,
) -> tuple[Any, Any]:
    """
    Scatter der Fit-Größe (``Ea_J_mol`` oder ``lnAs``) gegen den Molanteil einer Komponente,
    identifiziert wie bei :func:`thin_layer.view_filters.mole_fraction` über Teilstrings.

    Fehlt die Komponente in :attr:`ArrheniusGroupKey.fluid_compounds` (z. B. kein Wasser im
    binären DES), wird bei ``fill_missing_component_with_zero=True`` der x-Wert ``0.0``
    gesetzt, damit ternäre und binäre Messreihen gemeinsam plottbar sind.

    Bei ``plot_y_uncertainty=True`` (Standard): y-Fehlerbalken aus ``Ea_J_mol_std`` bzw.
    ``lnAs_std`` (OLS aus :func:`fit_arrhenius_from_views`). x-Unsicherheiten (Molanteile)
    werden hier nicht dargestellt.

    ``color_by='doi'`` (Standard): Farbe pro Punkt aus ``group_key.source_doi`` via
    :func:`_string_to_hex_color`; bei ``'uniform'`` einheitliche Farbe; bei
    ``'component'`` Farbe aus dem **x-Molanteil** (gleiche Komponente wie auf der Achse),
    Verlauf **hellgrau → Blau** (nicht von Weiß).     Optional Colorbar: ``show_component_colorbar`` (nur bei ``color_by='component'``).
    """
    import matplotlib.pyplot as plt

    if y_field not in ("Ea_J_mol", "lnAs"):
        raise ValueError("y_field muss 'Ea_J_mol' oder 'lnAs' sein.")
    created = ax is None
    if created:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    yerr_attr = "Ea_J_mol_std" if y_field == "Ea_J_mol" else "lnAs_std"
    xs: list[float] = []
    ys: list[float] = []
    yerrs: list[float] = []
    dois: list[str] = []
    for b in bundles:
        gk = b.group_key
        if fill_missing_component_with_zero:
            x = group_key_mole_fraction_or_zero(gk, *component_substrings)
        else:
            xv = group_key_mole_fraction(gk, *component_substrings)
            if xv is None:
                continue
            x = float(xv)
        xs.append(x)
        ys.append(float(getattr(b, y_field)))
        dois.append(str(gk.source_doi or ""))
        std = getattr(b, yerr_attr, None)
        if std is None or not np.isfinite(float(std)) or float(std) <= 0:
            yerrs.append(float("nan"))
        else:
            yerrs.append(float(std))

    xa = np.asarray(xs, dtype=float)
    ya = np.asarray(ys, dtype=float)
    yea = np.asarray(yerrs, dtype=float)
    comp_norm: Any = None
    comp_cmap: Any = None
    if color_by == "doi":
        point_colors = [_string_to_hex_color(d) for d in dois]
    elif color_by == "uniform":
        point_colors = ["#1f77b4"] * len(xa)
    elif color_by == "component":
        point_colors, comp_norm, comp_cmap = _molefraction_gray_blue_colors(xa)
    else:
        raise ValueError("color_by muss 'doi', 'uniform' oder 'component' sein.")

    n_with_yerr = 0
    n_without_yerr = 0
    for i in range(len(xa)):
        c = point_colors[i]
        has_yerr = plot_y_uncertainty and np.isfinite(yea[i]) and float(yea[i]) > 0.0
        if has_yerr:
            n_with_yerr += 1
            ax.errorbar(
                [xa[i]],
                [ya[i]],
                yerr=[yea[i]],
                fmt="o",
                ms=6,
                alpha=0.85,
                color=c,
                ecolor=c,
                elinewidth=1.0,
                capsize=3,
                markeredgecolor="black",
                markeredgewidth=0.25,
                zorder=3,
            )
        else:
            n_without_yerr += 1
            ax.scatter(
                [xa[i]],
                [ya[i]],
                s=36,
                alpha=0.85,
                color=c,
                edgecolors="black",
                linewidths=0.25,
                zorder=2,
            )
    if xlabel is None:
        comp_label = "_".join(str(x).strip().lower() for x in component_substrings if str(x).strip())
        if not comp_label:
            comp_label = "component"
        xlabel = rf"$\chi_{{{comp_label}}}$"
    ax.set_xlabel(xlabel)
    ax.set_ylabel(
        ylabel or ("$E_a$ / J·mol$^{-1}$" if y_field == "Ea_J_mol" else r"$\ln A_s$")
    )
    ax.set_title(title or f"Arrhenius-Fits: {y_field} vs. Komponente")
    ax.grid(alpha=0.25)
    if show_legend:
        from matplotlib.lines import Line2D

        handles: list[Any] = []
        if plot_y_uncertainty and n_with_yerr > 0:
            handles.append(
                Line2D(
                    [0],
                    [0],
                    marker="o",
                    linestyle="None",
                    color="black",
                    markerfacecolor="white",
                    markeredgecolor="black",
                    markersize=6,
                    label="Fit point with y-uncertainty",
                )
            )
        if n_without_yerr > 0:
            handles.append(
                Line2D(
                    [0],
                    [0],
                    marker="o",
                    linestyle="None",
                    color="black",
                    markerfacecolor="white",
                    markeredgecolor="black",
                    markersize=6,
                    label="Fit point without y-uncertainty",
                )
            )
        if color_by == "doi":
            unique_dois = sorted({d for d in dois if d})
            for doi in unique_dois:
                handles.append(
                    Line2D(
                        [0],
                        [0],
                        marker="o",
                        linestyle="None",
                        markerfacecolor=_string_to_hex_color(doi),
                        markeredgecolor="black",
                        markeredgewidth=0.25,
                        markersize=6,
                        label=doi,
                    )
                )
        elif color_by == "component":
            handles.append(
                Line2D(
                    [0],
                    [0],
                    linestyle="None",
                    marker="",
                    color="none",
                    label="Color encodes component mole fraction",
                )
            )
        if handles:
            ax.legend(handles=handles, loc="best", fontsize=8, title="Legend")
    if (
        color_by == "component"
        and show_component_colorbar
        and comp_norm is not None
        and comp_cmap is not None
        and len(xa) > 0
    ):
        sm = plt.cm.ScalarMappable(cmap=comp_cmap, norm=comp_norm)
        sm.set_array(xa)
        cbar = plt.colorbar(sm, ax=ax, pad=0.02)
        cbar.set_label("Mole fraction (" + ", ".join(component_substrings) + ")")
    if created:
        plt.tight_layout()
    return fig, ax
