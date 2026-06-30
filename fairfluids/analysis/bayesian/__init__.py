"""Bayesian analysis subpackage built on NumPyro, JAX and ArviZ.

Requires the ``[bayesian]`` extra:

    pip install fairfluids[bayesian]

Typical entry points:

- :class:`BayesianDataset` — build a fit-ready dataset from FAIRFluids documents.
- :func:`get_model` / :func:`list_models` — access the registered model library.
- :class:`PriorSet` — define priors at fit time (there are no presets).
- :class:`BayesianWorkflow` — orchestrate prior exploration, MCMC, evaluation, comparison.

Models are no longer rendered by a codegen pipeline. Every ``BayesianModel`` is
*synthesised at import time* from the single source of truth — the
:class:`~fairfluids.analysis.models.SymbolicModel` instances in
:data:`fairfluids.analysis.models.registry` — via :mod:`.bridge`. The
data-anchored density variants (``T0 = mean(T)``, ``rho0 = rho(T0)``) fall out of
the shared constant-resolver machinery rather than bespoke subclasses.
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
from .inference import BayesianFit, GroupFit, fit_groups, predict, predict_averaged
from .models import BayesianModel, ModelRegistry, get_model, list_models

# Synthesise and register a NumPyro model for every symbolic model on import.
from . import bridge

bridge.register_all()

from .priors import (
    HalfNormal,
    LogNormal,
    Normal,
    Prior,
    PriorSet,
    PriorSpec,
    TruncatedNormal,
    Uniform,
    prior_predictive_quantiles,
    sample_prior,
)
from .setup import enable_x64, set_host_count, set_platform
from .workflow import BayesianWorkflow
from .writeback import fit_to_fairfluids_document, fit_to_fitted_models

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
    "Prior",
    "PriorSet",
    "PriorSpec",
    "Uniform",
    "Normal",
    "HalfNormal",
    "LogNormal",
    "TruncatedNormal",
    "compare_models",
    "enable_x64",
    "fit_groups",
    "fit_to_fairfluids_document",
    "fit_to_fitted_models",
    "get_model",
    "list_models",
    "plots",
    "posterior_summary",
    "predict",
    "predict_averaged",
    "prior_predictive_quantiles",
    "sample_prior",
    "set_host_count",
    "set_platform",
]
