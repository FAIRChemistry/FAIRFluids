"""
Thin layer zwischen ``FAIRFluidsDocument`` und Auswertung/Visualisierung.

Eigenständiges Paket unterhalb des Repos — später ins Hauptpaket
(``fairfluids.*``) verschieben oder hier als optionale Abhängigkeit belassen.

Verwendung (Repo-Root auf ``PYTHONPATH``):

    from thin_layer import MeasurementView, iter_measurement_views_from_documents
    from fairfluids import FAIRFluidsDocument

    doc = FAIRFluidsDocument.model_validate_json(path.read_text())
    for row in iter_measurement_views_from_documents([doc], property_types=["viscosity"]):
        ...
"""

from .arrhenius_from_views import (
    fit_arrhenius_from_views,
    group_measurement_views_for_arrhenius,
    partition_views_for_arrhenius_plot,
    plot_arrhenius_panels_combined,
    plot_arrhenius_regression,
    scatter_arrhenius_bundles_vs_component,
)
from .fit_types import (
    ArrheniusFitBundle,
    ArrheniusGroupKey,
    group_key_mole_fraction,
    group_key_mole_fraction_or_zero,
    group_key_mole_fractions_for_components,
)
from .measurement_views import (
    MeasurementView,
    compound_display_names,
    iter_measurement_views,
    iter_measurement_views_from_documents,
    list_measurement_views,
    list_measurement_views_from_documents,
    load_documents_json,
)
from .view_filters import (
    dedupe_views,
    extra_parameter_float,
    filter_views,
    inspect_documents_compounds,
    inspect_views_composition,
    mole_fraction,
    pred_all,
    pred_any,
    pred_compound_min_mole_fraction,
    pred_composition,
    pred_extra_numeric_in_range,
    pred_fluid_component_count,
    pred_mole_ratio_close,
    pred_not,
    pred_property_type_in,
    union_filtered,
)

__all__ = [
    "compound_display_names",
    "load_documents_json",
    "dedupe_views",
    "extra_parameter_float",
    "filter_views",
    "inspect_documents_compounds",
    "inspect_views_composition",
    "mole_fraction",
    "pred_all",
    "pred_any",
    "pred_compound_min_mole_fraction",
    "pred_composition",
    "pred_extra_numeric_in_range",
    "pred_fluid_component_count",
    "pred_mole_ratio_close",
    "pred_not",
    "pred_property_type_in",
    "union_filtered",
    "ArrheniusFitBundle",
    "ArrheniusGroupKey",
    "group_key_mole_fraction",
    "group_key_mole_fraction_or_zero",
    "group_key_mole_fractions_for_components",
    "fit_arrhenius_from_views",
    "group_measurement_views_for_arrhenius",
    "partition_views_for_arrhenius_plot",
    "plot_arrhenius_panels_combined",
    "plot_arrhenius_regression",
    "scatter_arrhenius_bundles_vs_component",
    "MeasurementView",
    "iter_measurement_views",
    "iter_measurement_views_from_documents",
    "list_measurement_views",
    "list_measurement_views_from_documents",
]
