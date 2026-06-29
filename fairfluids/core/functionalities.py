# Import the FAIRFluids models
from .lib import (
    FAIRFluidsDocument,
    Version,
    Citation,
    Author,
    Compound,
    Fluid,
    Property,
    PropertyValue,
    Parameter,
    ParameterValue,
    Measurement,
    Sample,
    UnitDefinition,
    BaseUnit,
    Method,
    Properties,
    Parameters,
)
from collections.abc import Mapping as MappingABC, Sequence as SequenceABC
from typing import Optional, List, Dict, Any, Tuple, Union
import warnings
import xml.etree.ElementTree as ET
import requests
import numpy as np
import uuid
import hashlib
import colorsys
from collections import defaultdict
import pandas as pd

from fairfluids.inspection.document import (
    show_available_parameters,
    show_available_properties,
)
from fairfluids.operations.sample_utils import _ensure_fluid_sample, _get_measurements
from fairfluids.operations.compounds import (
    combine_compounds,
    calculate_ratio_of_solvent,
    cleanup_orphaned_parameters,
)
from fairfluids.io.cml_parser import FAIRFluidsCMLParser


def _string_to_hex_color(s: str, sat: float = 0.65, val: float = 0.85) -> str:
    """Deterministically map strings to hex colors (used for DOI coloring)."""
    h = hashlib.sha256(str(s).encode()).hexdigest()
    h_int = int(h[:8], 16)
    hue = (h_int * 0.618033988749895) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))


def _get_doi_plot_style(
    doi: Any, custom_styles: Optional[dict[str, dict[str, str]]] = None
) -> dict[str, str]:
    """Return DOI plotting style; prefers caller-provided styles."""
    doi_str = str(doi)
    style = custom_styles.get(doi_str, {}) if custom_styles else {}
    return {
        "color": style.get("color", _string_to_hex_color(doi_str)),
        "marker": style.get("marker", "o"),
    }


def _is_compositional_parameter(param_name_lower: str) -> bool:
    """
    Check if a parameter name represents a compositional parameter.

    Args:
        param_name_lower: Lowercase parameter name

    Returns:
        True if the parameter is compositional, False otherwise
    """
    compositional_keywords = [
        "mole fraction",
        "mass fraction",
        "volume fraction",
        "molality",
        "molarity",
        "amount concentration",
        "amount ratio",
        "mass ratio",
        "volume ratio",
        "ratio of amount",
        "ratio of mass",
        "ratio of component",
        "amount density",
        "amount of solute",
        "mass of solute",
        "volume of solute",
        "solute to solvent",
        "solute to solution",
        "component to other component",
        "component to mass",
        "component mass to volume",
    ]

    return any(keyword in param_name_lower for keyword in compositional_keywords)


def filter_fluid_compounds_by_mole_fractions(fluid):
    """
    Filter compounds and their parameters from a fluid if they have zero mole fractions
    in ALL measurements AND no other compositional parameters are present.

    This function:
    1. Checks each compound's compositional parameters (mole fraction, mass fraction,
       molality, volume fraction, ratios, etc.) across all measurements
    2. Removes compounds that have 0.0 mole fractions in ALL measurements AND no other
       compositional parameters present
    3. Removes associated parameter definitions
    4. Removes parameter values from all measurements

    Args:
        fluid: A Fluid object with measurements

    Returns:
        The fluid object with filtered compounds and parameters
    """
    if not _get_measurements(fluid):
        return fluid

    print(
        f"=== Filtering Fluid with {len(fluid.compounds)} compounds and {len(_get_measurements(fluid))} measurements ==="
    )

    # Track which compounds should be kept (non-zero mole fractions OR other compositional params present)
    compounds_to_keep = set()

    # Build a quick lookup for parameter definitions by ID once
    parameter_lookup = {
        param.parameterID: param
        for param in fluid.parameter
        if getattr(param, "parameterID", None)
    }

    # Check each compound's compositional parameters across all measurements
    for compound_id in fluid.compounds:
        has_non_zero_mole_fraction = False
        has_compositional_signal = False  # any compositional parameter present
        compositional_param_types = []  # track which types we found

        # Check all measurements for this compound
        for measurement in _get_measurements(fluid):
            for param_value in measurement.parameterValue:
                # Find the parameter definition for this parameter value
                param_def = parameter_lookup.get(param_value.parameterID)

                # Check if this is a compositional parameter for this compound
                if (
                    param_def
                    and compound_id in param_def.associated_compounds
                    and hasattr(param_def, "parameters")
                    and param_def.parameters is not None
                ):

                    # Normalize parameter name
                    param_name = str(param_def.parameters)
                    if hasattr(param_def.parameters, "value"):
                        param_name = param_def.parameters.value
                    param_name_lower = param_name.lower()

                    # Check if this is any compositional parameter
                    if _is_compositional_parameter(param_name_lower):
                        has_compositional_signal = True

                        # Track the type for reporting
                        if "mole fraction" in param_name_lower:
                            compositional_param_types.append("mole fraction")
                        elif "mass fraction" in param_name_lower:
                            compositional_param_types.append("mass fraction")
                        elif "molality" in param_name_lower:
                            compositional_param_types.append("molality")
                        elif "volume fraction" in param_name_lower:
                            compositional_param_types.append("volume fraction")
                        elif "ratio" in param_name_lower:
                            compositional_param_types.append("ratio")
                        elif (
                            "molarity" in param_name_lower
                            or "amount concentration" in param_name_lower
                        ):
                            compositional_param_types.append("molarity/concentration")
                        else:
                            compositional_param_types.append("compositional")

                        # Check for non-zero mole fraction specifically
                        if "mole fraction" in param_name_lower:
                            if (
                                param_value.paramValue is not None
                                and param_value.paramValue > 0
                            ):
                                has_non_zero_mole_fraction = True
                                break
                        # For other compositional parameters, just note their presence
                        # (we don't break to continue looking for mole fractions)

            if has_non_zero_mole_fraction:
                break

        if has_non_zero_mole_fraction or has_compositional_signal:
            compounds_to_keep.add(compound_id)
            # Create descriptive reason
            if has_non_zero_mole_fraction:
                reason = "non-zero mole fractions"
            else:
                unique_types = list(set(compositional_param_types))
                if len(unique_types) == 1:
                    reason = f"composition parameter present ({unique_types[0]})"
                else:
                    reason = f"composition parameters present ({', '.join(unique_types[:3])}{'...' if len(unique_types) > 3 else ''})"
            print(f"✅ Keeping compound: {compound_id} ({reason})")
        else:
            print(
                f"❌ Removing compound: {compound_id} (no compositional parameters in measurements)"
            )

    # Update compounds list
    original_compounds = fluid.compounds.copy()
    fluid.compounds = [comp for comp in original_compounds if comp in compounds_to_keep]

    # Remove parameter definitions for compounds that are not kept
    original_parameters = fluid.parameter.copy()
    fluid.parameter = [
        param
        for param in original_parameters
        if (
            not hasattr(param, "associated_compounds")
            or not param.associated_compounds
            or any(comp in compounds_to_keep for comp in param.associated_compounds)
        )
    ]

    # Remove parameter values from measurements for compounds that are not kept
    for measurement in _get_measurements(fluid):
        original_param_values = measurement.parameterValue.copy()
        measurement.parameterValue = []

        for pv in original_param_values:
            # Find the parameter definition for this parameter value
            param_def = None
            for param in fluid.parameter:
                if param.parameterID == pv.parameterID:
                    param_def = param
                    break

            # Keep the parameter value if:
            # 1. It's not associated with any compound (like temperature)
            # 2. It's associated with a compound that we're keeping
            if (
                not param_def
                or not hasattr(param_def, "associated_compounds")
                or not param_def.associated_compounds
                or any(
                    comp in compounds_to_keep for comp in param_def.associated_compounds
                )
            ):
                measurement.parameterValue.append(pv)

    print(
        f"Final result: {len(fluid.compounds)} compounds, {len(fluid.parameter)} parameters"
    )
    return fluid


def group_and_filter_measurements(
    df: pd.DataFrame,
    group_key: str = "source_doi",
    composition_filters: Optional[Dict[str, Union[float, Tuple[float, float]]]] = None,
    filter_before_grouping: bool = True,
    aggregations: Optional[Dict[str, Union[str, List[str]]]] = None,
    tolerance: float = 1e-6,
    dropna_group_key: bool = False,
) -> Union[pd.DataFrame, Any]:
    """
    Group measurement data by a key (e.g. DOI) with optional mole-fraction filters.

    This utility is intended for FAIRFluids DataFrames and supports both workflows:
    1) Filter composition first, then group by DOI
    2) Group by DOI first, then apply composition filter inside each DOI

    Args:
        df: Input DataFrame (e.g. output from visualization/filter utilities)
        group_key: Column name used for grouping (default: "source_doi")
        composition_filters: Dictionary of composition filters. Each key is a column
            name (e.g. "mole_fraction_water"). Value can be:
              - float: exact match within tolerance
              - (min, max): inclusive interval
        filter_before_grouping: If True, apply composition filters before grouping.
            If False, create groups first and then keep filtered rows within each group.
        aggregations: Optional pandas aggregation mapping. If provided, returns
            aggregated DataFrame. If None, returns a GroupBy object.
        tolerance: Absolute tolerance for exact-value composition filters.
        dropna_group_key: Passed to pandas groupby(dropna=...).

    Returns:
        If aggregations is None: pandas GroupBy object.
        If aggregations is provided: aggregated DataFrame with reset index.
    """
    if group_key not in df.columns:
        raise ValueError(
            f"Group key '{group_key}' not found. Available columns: {list(df.columns)}"
        )

    def _apply_composition_filters(frame: pd.DataFrame) -> pd.DataFrame:
        if not composition_filters:
            return frame

        filtered = frame.copy()
        for column, selector in composition_filters.items():
            if column not in filtered.columns:
                raise ValueError(
                    f"Composition column '{column}' not found. "
                    f"Available columns: {list(filtered.columns)}"
                )

            if isinstance(selector, tuple):
                if len(selector) != 2:
                    raise ValueError(
                        f"Range filter for '{column}' must be a (min, max) tuple."
                    )
                lower, upper = selector
                filtered = filtered[
                    filtered[column].between(lower, upper, inclusive="both")
                ]
            else:
                filtered = filtered[
                    (filtered[column] - float(selector)).abs() <= tolerance
                ]

        return filtered

    if filter_before_grouping:
        working_df = _apply_composition_filters(df)
        grouped = working_df.groupby(group_key, dropna=dropna_group_key)
    else:
        grouped = df.groupby(group_key, dropna=dropna_group_key)
        if composition_filters:
            grouped_frames = [
                _apply_composition_filters(group_frame) for _, group_frame in grouped
            ]
            grouped_frames = [g for g in grouped_frames if not g.empty]
            if grouped_frames:
                working_df = pd.concat(grouped_frames, ignore_index=True)
            else:
                working_df = df.iloc[0:0].copy()
            grouped = working_df.groupby(group_key, dropna=dropna_group_key)

    if aggregations is None:
        return grouped

    return grouped.agg(aggregations).reset_index()


def _document_label(doc: FAIRFluidsDocument, index: Optional[int] = None) -> str:
    """Return a human-readable label for warnings and logging."""
    citation = doc.citation
    if citation is not None:
        if citation.doi:
            return citation.doi
        if citation.title:
            return citation.title
    if index is not None:
        return f"Document_{index + 1}"
    return "unknown document"


def _extract_property_dataframe_single(
    doc: FAIRFluidsDocument,
    property_type: str,
    *,
    document_label: str,
    components: Optional[List[str]] = None,
    target_ratio: Optional[float] = None,
    ratio_column: str = "Solvent: Amount ratio of component to other component of binary solvent",
    exact_component_match: bool = False,
    ratio_tolerance: float = 1e-6,
    include_na_ratio: bool = True,
    sort_by: Optional[str] = "temperature",
    ascending: bool = True,
    keep_only_relevant_columns: bool = True,
    warn_on_missing_property: bool = True,
) -> pd.DataFrame:
    """Extract a property DataFrame from a single FAIRFluids document."""
    from .visualization import extract_fairfluids_data

    df = extract_fairfluids_data(doc)
    if df.empty:
        if warn_on_missing_property:
            warnings.warn(
                f"Property {property_type!r} not found in document {document_label!r}. Continuing.",
                UserWarning,
                stacklevel=4,
            )
        return df

    # Keep only selected property type
    if "property_type" not in df.columns:
        raise ValueError(
            "Column 'property_type' missing in extracted data. "
            "Please verify extract_fairfluids_data output."
        )
    df = df[df["property_type"] == property_type].copy()
    if df.empty:
        if warn_on_missing_property:
            warnings.warn(
                f"Property {property_type!r} not found in document {document_label!r}. Continuing.",
                UserWarning,
                stacklevel=4,
            )
        return df

    # Build/refresh mole fraction columns dynamically from fluid_compounds + mole_fractions
    if "fluid_compounds" in df.columns and "mole_fractions" in df.columns:
        all_compounds = set()
        for comp_list in df["fluid_compounds"]:
            if isinstance(comp_list, list):
                all_compounds.update([str(c) for c in comp_list])

        for compound in sorted(all_compounds):
            col_name = f"mole_fraction_{compound}"

            def _extract_compound_fraction(row, target_compound=compound):
                comps = row.get("fluid_compounds")
                fracs = row.get("mole_fractions")
                if not isinstance(comps, list) or not isinstance(fracs, (list, tuple)):
                    return np.nan
                for idx, comp in enumerate(comps):
                    if str(comp).strip().lower() == target_compound.strip().lower():
                        return fracs[idx] if idx < len(fracs) else np.nan
                return 0.0

            df[col_name] = df.apply(_extract_compound_fraction, axis=1)

    # Component filtering
    if components:
        requested = [str(c).strip().lower() for c in components]

        def _matches_components(comp_list):
            if not isinstance(comp_list, list):
                return False
            available = [str(c).strip().lower() for c in comp_list]
            if exact_component_match:
                return set(available) == set(requested)
            return all(c in available for c in requested)

        df = df[df["fluid_compounds"].apply(_matches_components)].copy()
        if df.empty:
            return df

    # Ratio filtering
    if target_ratio is not None:
        if ratio_column not in df.columns:
            raise ValueError(
                f"Ratio column '{ratio_column}' not found. Available columns: {list(df.columns)}"
            )
        ratio_numeric = pd.to_numeric(df[ratio_column], errors="coerce")
        ratio_match = (ratio_numeric - float(target_ratio)).abs() <= ratio_tolerance
        if include_na_ratio:
            ratio_missing = ratio_numeric.isna()
            # Keep rows with requested ratio OR missing ratio values (NA).
            df = df[ratio_match | ratio_missing].copy()
        else:
            df = df[ratio_match].copy()

    # Optional sort
    if sort_by and sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=ascending)

    # Add a robust water mole fraction helper column if composition data is available
    if "fluid_compounds" in df.columns and "mole_fractions" in df.columns:

        def _extract_water_fraction(row):
            comps = row.get("fluid_compounds")
            fracs = row.get("mole_fractions")
            if not isinstance(comps, list) or not isinstance(fracs, (list, tuple)):
                return np.nan
            for idx, comp in enumerate(comps):
                comp_name = str(comp).strip().lower()
                if comp_name in {"water", "h2o"}:
                    return fracs[idx] if idx < len(fracs) else np.nan
            return 0.0

        df["mole_fraction_water"] = df.apply(_extract_water_fraction, axis=1)

    if keep_only_relevant_columns:
        property_value_col = f"{property_type}_value"
        property_uncertainty_col = f"{property_type}_uncertainty"
        desired_columns = [
            "fluid_compounds",
            "mole_fractions",
            property_value_col,
            property_uncertainty_col,
            "temperature",
            "source_doi",
            ratio_column,
            "mole_fraction_water",
        ]
        existing_columns = [col for col in desired_columns if col in df.columns]
        df = df[existing_columns].copy()

    return df


def extract_property_dataframe(
    doc: Union[
        FAIRFluidsDocument,
        SequenceABC[FAIRFluidsDocument],
        MappingABC[str, FAIRFluidsDocument],
    ],
    property_type: str,
    components: Optional[List[str]] = None,
    target_ratio: Optional[float] = None,
    ratio_column: str = "Solvent: Amount ratio of component to other component of binary solvent",
    exact_component_match: bool = False,
    ratio_tolerance: float = 1e-6,
    include_na_ratio: bool = True,
    sort_by: Optional[str] = "temperature",
    ascending: bool = True,
    keep_only_relevant_columns: bool = True,
    document_label_key: str = "document_label",
) -> pd.DataFrame:
    """
    Build a filtered DataFrame for a selected property, components, and optional ratio.

    Accepts a single FAIRFluids document, a sequence of documents, or a mapping
    ``label -> document``. When multiple documents are supplied, rows from documents
    that contain the requested property are concatenated. Documents without the
    property emit a soft warning and are skipped.

    Args:
        doc: One FAIRFluids document, a sequence of documents, or a mapping of
            labels to documents.
        property_type: Property to select (e.g., "viscosity", "thermalConductivity", "density").
        components: Optional component names to filter for (case-insensitive). If provided:
            - exact_component_match=False: all listed components must be present
            - exact_component_match=True: fluid must contain exactly this set of components
        target_ratio: Optional numeric ratio value to filter by using ``ratio_column``.
        ratio_column: Column name for ratio filtering.
        exact_component_match: Whether component filtering should be exact set matching.
        ratio_tolerance: Absolute tolerance for numeric ratio comparison.
        include_na_ratio: If True and target_ratio is provided, keep rows where
            ratio_column is missing/NA in addition to matching target_ratio.
        sort_by: Optional column to sort by.
        ascending: Sort direction.
        keep_only_relevant_columns: If True, returns only a compact set of columns:
            fluid_compounds, mole_fractions, <property>_value, <property>_uncertainty,
            temperature, source_doi, ratio_column, mole_fraction_water (if available).
            Missing per-compound mole fractions (component absent from the fluid) are
            set to ``0.0`` rather than ``NaN``.
        document_label_key: Column name used for mapping keys when ``doc`` is a mapping.

    Returns:
        Filtered pandas DataFrame.
    """
    if isinstance(doc, FAIRFluidsDocument):
        doc_items: list[tuple[Optional[str], FAIRFluidsDocument]] = [(None, doc)]
    elif isinstance(doc, (str, bytes)):
        raise TypeError(
            "doc must be a FAIRFluidsDocument or a sequence of documents, not str."
        )
    elif isinstance(doc, MappingABC):
        doc_items = list(doc.items())
    elif isinstance(doc, SequenceABC):
        doc_items = [(None, single_doc) for single_doc in doc]
    else:
        raise TypeError(
            "doc must be a FAIRFluidsDocument, a sequence of documents, "
            "or a mapping of labels to documents."
        )

    if not doc_items:
        return pd.DataFrame()

    extract_kwargs = dict(
        components=components,
        target_ratio=target_ratio,
        ratio_column=ratio_column,
        exact_component_match=exact_component_match,
        ratio_tolerance=ratio_tolerance,
        include_na_ratio=include_na_ratio,
        sort_by=sort_by,
        ascending=ascending,
        keep_only_relevant_columns=keep_only_relevant_columns,
    )

    frames: list[pd.DataFrame] = []
    for idx, (label, single_doc) in enumerate(doc_items):
        warn_label = (
            label
            if label is not None
            else _document_label(
                single_doc, index=idx if len(doc_items) > 1 else None
            )
        )
        frame = _extract_property_dataframe_single(
            single_doc,
            property_type,
            document_label=warn_label,
            **extract_kwargs,
        )
        if frame.empty:
            continue
        if label is not None:
            frame = frame.copy()
            frame[document_label_key] = label
        frames.append(frame)

    if not frames:
        return pd.DataFrame()

    if len(doc_items) == 1:
        return frames[0]

    return pd.concat(frames, ignore_index=True)
