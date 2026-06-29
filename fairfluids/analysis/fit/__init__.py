"""Fitting backends for :class:`~fairfluids.analysis.models.SymbolicModel`.

A model declares the mathematics once (in :mod:`fairfluids.analysis.models`);
this package fits it. Two backends share the same compiled mean function:

- :func:`fit_least_squares` — SciPy ``curve_fit`` (the light path; needs only
  numpy + SciPy).
- :func:`fit_mcmc` — NumPyro NUTS (the ``[bayesian]`` extra; JAX/NumPyro are
  imported lazily so importing this package never requires them).

The :func:`fit_group` / :func:`fit_dataset` adapters bridge prepared data
containers (``BayesianGroup`` / ``BayesianDataset``-like) to either backend.
"""

from __future__ import annotations

from .adapters import DatasetFit, fit_dataset, fit_group
from .derived import evaluate_derived, scalar_derived_names
from .least_squares import SymbolicFit
from .least_squares import fit as fit_least_squares
from .mcmc import build_numpyro_model, fit_mcmc

__all__ = [
    # backends
    "fit_least_squares",
    "SymbolicFit",
    "fit_mcmc",
    "build_numpyro_model",
    # convenience adapters (group / dataset)
    "fit_group",
    "fit_dataset",
    "DatasetFit",
    # derived-quantity propagation
    "evaluate_derived",
    "scalar_derived_names",
]
