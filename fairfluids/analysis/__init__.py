"""Analysis: Arrhenius/VFT fits, activation energy, measurement tables.

Bayesian workflows live in :mod:`fairfluids.analysis.bayesian` and require the
``[bayesian]`` extra. Importing this module never imports the Bayesian stack;
users must explicitly ``from fairfluids.analysis import bayesian`` (or call
:func:`get_bayesian`).
"""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any

from fairfluids.analysis import fluids
from fairfluids.core.functionalities import (
    extract_property_dataframe,
    group_and_filter_measurements,
)
from fairfluids.analysis.regression import (
    ParameterStack,
    fit_arrhenius,
    fit_documents,
    fit_extended_arrhenius,
    fit_model,
    fit_vft,
)


def get_bayesian() -> ModuleType:
    """Return the :mod:`fairfluids.analysis.bayesian` module, raising a clear error
    when the ``[bayesian]`` extra is not installed.
    """
    try:
        return importlib.import_module("fairfluids.analysis.bayesian")
    except ImportError as exc:
        raise ImportError(
            "fairfluids.analysis.bayesian requires the [bayesian] extra. "
            "Install with: pip install fairfluids[bayesian]"
        ) from exc


def __getattr__(name: str) -> Any:
    if name == "bayesian":
        return get_bayesian()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "extract_property_dataframe",
    "fit_arrhenius",
    "fit_extended_arrhenius",
    "fit_vft",
    "fit_model",
    "fit_documents",
    "ParameterStack",
    "group_and_filter_measurements",
    "get_bayesian",
    "fluids",
]
