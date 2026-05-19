"""Parameter and property inventory across fluids."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Union

import pandas as pd

from fairfluids.core.lib import FAIRFluidsDocument
from fairfluids.operations.sample_utils import _get_measurements


def show_available_parameters(
    doc: FAIRFluidsDocument,
    return_dataframe: bool = True,
    print_output: bool = True,
) -> Union[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Show all parameter definitions available in a FAIRFluids document.

    Aggregates parameters across all fluids and reports where/how often they appear.

    Args:
        doc: The FAIRFluidsDocument to inspect.
        return_dataframe: If True, return a pandas DataFrame, otherwise a list of dicts.
        print_output: If True, print a compact summary to stdout.

    Returns:
        A pandas DataFrame (default) or a list of dictionaries with one row per
        unique parameterID and the columns/keys:
        - parameterID
        - parameter_name
        - unit_name
        - associated_compounds
        - fluid_count
        - measurement_value_count
    """
    parameter_summary: Dict[str, Dict[str, Any]] = {}

    for fluid_idx, fluid in enumerate(doc.fluid):
        parameter_lookup = {
            param.parameterID: param for param in fluid.parameter if param.parameterID
        }
        value_count_by_parameter: Dict[str, int] = defaultdict(int)

        for measurement in _get_measurements(fluid):
            for param_value in measurement.parameterValue:
                if param_value.parameterID:
                    value_count_by_parameter[param_value.parameterID] += 1

        for parameter_id, param_def in parameter_lookup.items():
            if parameter_id not in parameter_summary:
                parameter_summary[parameter_id] = {
                    "parameterID": parameter_id,
                    "parameter_name": set(),
                    "unit_name": set(),
                    "associated_compounds": set(),
                    "fluid_ids": set(),
                    "measurement_value_count": 0,
                }

            row = parameter_summary[parameter_id]
            fluid_key = f"fluid_{fluid_idx}"
            row["fluid_ids"].add(fluid_key)

            if getattr(param_def, "parameters", None) is not None:
                param_name = (
                    param_def.parameters.value
                    if hasattr(param_def.parameters, "value")
                    else str(param_def.parameters)
                )
                row["parameter_name"].add(param_name)

            unit_obj = getattr(param_def, "unit", None)
            if unit_obj is not None:
                unit_name = getattr(unit_obj, "name", None) or str(unit_obj)
                row["unit_name"].add(unit_name)

            for compound_id in getattr(param_def, "associated_compounds", []) or []:
                row["associated_compounds"].add(compound_id)

            row["measurement_value_count"] += value_count_by_parameter.get(
                parameter_id, 0
            )

    rows: List[Dict[str, Any]] = []
    for data in parameter_summary.values():
        rows.append(
            {
                "parameterID": data["parameterID"],
                "parameter_name": (
                    ", ".join(sorted(data["parameter_name"]))
                    if data["parameter_name"]
                    else "unknown"
                ),
                "unit_name": (
                    ", ".join(sorted(data["unit_name"]))
                    if data["unit_name"]
                    else "unknown"
                ),
                "associated_compounds": sorted(data["associated_compounds"]),
                "fluid_count": len(data["fluid_ids"]),
                "measurement_value_count": data["measurement_value_count"],
            }
        )

    rows = sorted(rows, key=lambda x: x["parameterID"])

    if return_dataframe:
        result = pd.DataFrame(rows)
    else:
        result = rows

    if print_output:
        print(f"Found {len(rows)} unique parameters across {len(doc.fluid)} fluid(s).")
        if rows:
            preview_df = pd.DataFrame(rows)[
                [
                    "parameterID",
                    "parameter_name",
                    "fluid_count",
                    "measurement_value_count",
                ]
            ]
            print(preview_df.to_string(index=False))

    return result


def show_available_properties(
    doc: FAIRFluidsDocument,
    return_dataframe: bool = True,
    print_output: bool = True,
) -> Union[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Show all property definitions available in a FAIRFluids document.

    Aggregates properties across all fluids and reports where/how often they appear.

    Args:
        doc: The FAIRFluidsDocument to inspect.
        return_dataframe: If True, return a pandas DataFrame, otherwise a list of dicts.
        print_output: If True, print a compact summary to stdout.

    Returns:
        A pandas DataFrame (default) or a list of dictionaries with one row per
        unique propertyID and the columns/keys:
        - propertyID
        - property_name
        - unit_name
        - fluid_count
        - measurement_value_count
    """
    property_summary: Dict[str, Dict[str, Any]] = {}

    for fluid_idx, fluid in enumerate(doc.fluid):
        property_lookup = {
            prop.propertyID: prop for prop in fluid.property if prop.propertyID
        }
        value_count_by_property: Dict[str, int] = defaultdict(int)

        for measurement in _get_measurements(fluid):
            for prop_value in measurement.propertyValue:
                if prop_value.propertyID:
                    value_count_by_property[prop_value.propertyID] += 1

        for property_id, prop_def in property_lookup.items():
            if property_id not in property_summary:
                property_summary[property_id] = {
                    "propertyID": property_id,
                    "property_name": set(),
                    "unit_name": set(),
                    "fluid_ids": set(),
                    "measurement_value_count": 0,
                }

            row = property_summary[property_id]
            fluid_key = f"fluid_{fluid_idx}"
            row["fluid_ids"].add(fluid_key)

            if getattr(prop_def, "properties", None) is not None:
                prop_name = (
                    prop_def.properties.value
                    if hasattr(prop_def.properties, "value")
                    else str(prop_def.properties)
                )
                row["property_name"].add(prop_name)

            unit_obj = getattr(prop_def, "unit", None)
            if unit_obj is not None:
                unit_name = getattr(unit_obj, "name", None) or str(unit_obj)
                row["unit_name"].add(unit_name)

            row["measurement_value_count"] += value_count_by_property.get(
                property_id, 0
            )

    rows: List[Dict[str, Any]] = []
    for data in property_summary.values():
        rows.append(
            {
                "propertyID": data["propertyID"],
                "property_name": (
                    ", ".join(sorted(data["property_name"]))
                    if data["property_name"]
                    else "unknown"
                ),
                "unit_name": (
                    ", ".join(sorted(data["unit_name"]))
                    if data["unit_name"]
                    else "unknown"
                ),
                "fluid_count": len(data["fluid_ids"]),
                "measurement_value_count": data["measurement_value_count"],
            }
        )

    rows = sorted(rows, key=lambda x: x["propertyID"])

    if return_dataframe:
        result = pd.DataFrame(rows)
    else:
        result = rows

    if print_output:
        print(f"Found {len(rows)} unique properties across {len(doc.fluid)} fluid(s).")
        if rows:
            preview_df = pd.DataFrame(rows)[
                [
                    "propertyID",
                    "property_name",
                    "fluid_count",
                    "measurement_value_count",
                ]
            ]
            print(preview_df.to_string(index=False))

    return result
