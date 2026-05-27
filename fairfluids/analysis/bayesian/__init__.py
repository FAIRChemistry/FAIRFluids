"""Bayesian analysis subpackage built on NumPyro, JAX and ArviZ.

Requires the ``[bayesian]`` extra:

    pip install fairfluids[bayesian]

Typical entry points:

- :class:`BayesianDataset` — build a fit-ready dataset from FAIRFluids documents.
- :func:`get_model` / :func:`list_models` — access the registered model library.
- :class:`BayesianWorkflow` — orchestrate prior exploration, MCMC, evaluation, comparison.
"""

from __future__ import annotations

_BAYESIAN_EXTRA_HINT = (
    "fairfluids.analysis.bayesian requires the [bayesian] extra. "
    "Install with: pip install fairfluids[bayesian]"
)

try:
    import arviz  # noqa: F401
    import jax  # noqa: F401
    import numpyro  # noqa: F401
except ImportError as exc:
    raise ImportError(_BAYESIAN_EXTRA_HINT) from exc

from .comparison import ModelComparison, compare_models, posterior_summary
from .data import BayesianDataset, BayesianGroup
from .hierarchical import (
    HierarchicalArrhenius,
    HierarchicalBayesianModel,
    HierarchicalFit,
    fit_hierarchical,
    get_hierarchical_model,
    list_hierarchical_models,
)
from .inference import BayesianFit, GroupFit, fit_groups, predict, predict_averaged
from .models import BayesianModel, ModelRegistry, get_model, list_models

# Importing the built-in models registers them via __init_subclass__.
from . import models_builtin  # noqa: F401
from .models_builtin import Arrhenius, Litovitz, LitovitzExtended, VFT
from .priors import (
    HalfNormalPriorSpec,
    LogNormalPriorSpec,
    NormalPriorSpec,
    PriorPreset,
    PriorSpec,
    TruncatedNormalPriorSpec,
    UniformPriorSpec,
    prior_predictive_quantiles,
    sample_prior,
)
from .workflow import BayesianWorkflow

# Plots are exposed as a submodule to avoid pulling matplotlib at import time
# unless the user actually uses plotting helpers.
from . import plots  # noqa: F401

__all__ = [
    "BayesianDataset",
    "BayesianGroup",
    "BayesianModel",
    "BayesianFit",
    "GroupFit",
    "BayesianWorkflow",
    "ModelComparison",
    "ModelRegistry",
    "HierarchicalArrhenius",
    "HierarchicalBayesianModel",
    "HierarchicalFit",
    "PriorPreset",
    "PriorSpec",
    "UniformPriorSpec",
    "NormalPriorSpec",
    "HalfNormalPriorSpec",
    "LogNormalPriorSpec",
    "TruncatedNormalPriorSpec",
    "Arrhenius",
    "VFT",
    "Litovitz",
    "LitovitzExtended",
    "compare_models",
    "fit_groups",
    "fit_hierarchical",
    "get_hierarchical_model",
    "get_model",
    "list_hierarchical_models",
    "list_models",
    "plots",
    "posterior_summary",
    "predict",
    "predict_averaged",
    "prior_predictive_quantiles",
    "sample_prior",
]
