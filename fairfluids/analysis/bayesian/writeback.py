"""Write Bayesian fit results back into a ``FAIRFluidsDocument``.

This mirrors
:meth:`fairfluids.analysis.regression.result.ParameterStack.to_fairfluids_document`,
but expresses uncertainties from the posterior rather than from a frequentist
covariance: every parameter carries a posterior point estimate (mean or median),
its posterior standard deviation as the standard uncertainty, and a credible
interval at the requested coverage probability.

Each ``(model, group)`` fit becomes one
:class:`fairfluids.core.lib.FittedModel`:

- ``method = FitMethod.BAYESIAN_MCMC``
- per parameter: ``uncertainty_evaluation = UncertaintyEvaluation.POSTERIOR`` and
  ``distribution = DistributionType.POSTERIOR`` with ``interval_low``/``interval_high``
  set from posterior quantiles.
- the fitted group's composition is preserved in ``applied_parameters`` so the
  model stays self-describing regardless of the fluid it is attached to.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional

import numpy as np

if TYPE_CHECKING:
    from .inference import BayesianFit, GroupFit

PointEstimate = Literal["mean", "median"]

# Parameter name -> standardized Properties vocabulary entry (string value).
# Only parameters that map onto a known physical quantity are linked.
_PARAM_PROPERTY: dict[str, str] = {
    "Ea": "activationEnergy",
    "Ea_J_mol": "activationEnergy",
}


def _model_equation(model: Any) -> Optional[str]:
    """First non-empty line of the model class docstring, used as ``model_equation``."""
    doc = type(model).__doc__
    if not doc:
        return None
    for line in doc.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def _temperature_bounds(group: Any) -> tuple[Optional[float], Optional[float]]:
    """Return ``(min, max)`` of the temperature feature, if present."""
    features = group.features
    arr = features.get("temperature")
    if arr is None:
        return None, None
    values = np.asarray(arr, dtype=float)
    if values.size == 0:
        return None, None
    return float(np.min(values)), float(np.max(values))


def _composition_applied_parameters(group: Any) -> list[Any]:
    """Build ``ParameterValue`` mole-fraction entries from the group's metadata.

    The grouped DataFrame stores parallel ``fluid_compounds`` / ``mole_fractions``
    sequences (see :func:`fairfluids.core.functionalities.extract_property_dataframe`);
    each compound becomes one ``ParameterValue`` so the fit is pinned to a specific
    composition.
    """
    from ...core.lib import Parameters, ParameterValue

    metadata = group.metadata or {}
    compounds = metadata.get("fluid_compounds")
    fractions = metadata.get("mole_fractions")
    if not isinstance(compounds, (list, tuple, np.ndarray)) or not isinstance(
        fractions, (list, tuple, np.ndarray)
    ):
        return []

    applied: list[Any] = []
    for compound, fraction in zip(compounds, fractions):
        try:
            value = float(fraction)
        except (TypeError, ValueError):
            continue
        applied.append(
            ParameterValue(
                parameters=Parameters.MOLE_FRACTION,
                parameterID=str(compound),
                paramValue=value,
            )
        )
    return applied


def _source_measurement_ids(group: Any) -> list[str]:
    """Best-effort provenance: collect measurement identifiers from the group frame."""
    df = getattr(group, "dataframe", None)
    if df is None:
        return []
    for col in ("measurement_id", "measurementID", "measurement_ids"):
        if col in df.columns:
            return [str(m) for m in df[col].tolist() if m is not None]
    return []


def _fitted_property(model: Any) -> Optional[Any]:
    """Map ``model.property_name`` onto the standardized ``Properties`` enum."""
    from ...core.lib import Properties

    name = getattr(model, "property_name", "") or ""
    if not name:
        return None
    try:
        return Properties(name)
    except ValueError:
        return None


def _group_fit_to_fitted_model(
    gfit: "GroupFit",
    *,
    coverage_probability: float,
    point_estimate: PointEstimate,
    include_model_sigma: bool,
) -> Any:
    """Convert a single :class:`GroupFit` into a ``FittedModel``."""
    from ...core.lib import (
        DistributionType,
        FitMethod,
        FittedModel,
        FittedParameter as LibFittedParameter,
        Properties,
        UncertaintyEvaluation,
    )
    from .models import get_model

    model = get_model(gfit.model_name, **gfit.model_kwargs)
    samples = gfit.samples()

    # Which sites to report: the model's primary parameters, plus the noise scale.
    param_sites = [p for p in model.param_names if p in samples]
    if include_model_sigma and "model_sigma" in samples:
        param_sites.append("model_sigma")

    lower_q = 0.5 * (1.0 - coverage_probability)
    upper_q = 1.0 - lower_q

    parameters: list[Any] = []
    for name in param_sites:
        arr = np.asarray(samples[name], dtype=float).reshape(-1)
        if arr.size == 0:
            continue
        value = float(np.median(arr) if point_estimate == "median" else np.mean(arr))
        std = float(np.std(arr, ddof=1)) if arr.size > 1 else None
        low = float(np.quantile(arr, lower_q))
        high = float(np.quantile(arr, upper_q))
        prop = _PARAM_PROPERTY.get(name)
        parameters.append(
            LibFittedParameter(
                name=name,
                value=value,
                unit=None,
                standard_uncertainty=std,
                uncertainty_evaluation=UncertaintyEvaluation.POSTERIOR,
                distribution=DistributionType.POSTERIOR,
                coverage_probability=coverage_probability,
                interval_low=low,
                interval_high=high,
                properties=Properties(prop) if prop else None,
            )
        )

    t_lower, t_upper = _temperature_bounds(gfit.group)

    priors = gfit.priors
    method_bits = [
        "fairfluids.analysis.bayesian; NUTS",
        f"point_estimate={point_estimate}",
        f"likelihood={priors.likelihood}",
        f"sigma_scale={priors.sigma_scale:g}",
        f"num_divergences={gfit.num_divergences}",
    ]
    if priors.likelihood == "student_t":
        method_bits.append(f"student_t_df={priors.student_t_df:g}")
    if gfit.model_kwargs:
        anchors = ", ".join(f"{k}={v}" for k, v in gfit.model_kwargs.items())
        method_bits.append(f"anchors: {anchors}")
    source_doi = (gfit.group.metadata or {}).get("source_doi")
    if source_doi:
        method_bits.append(f"source_doi={source_doi}")

    return FittedModel(
        model_name=gfit.model_name,
        model_equation=_model_equation(model),
        method=FitMethod.BAYESIAN_MCMC,
        method_description="; ".join(method_bits),
        fitted_property=_fitted_property(model),
        parameter=parameters,
        r_squared=None,
        n_points=gfit.group.n_points,
        temperature_lower=t_lower,
        temperature_upper=t_upper,
        applied_parameters=_composition_applied_parameters(gfit.group),
        source_measurement_ids=_source_measurement_ids(gfit.group),
    )


def fit_to_fitted_models(
    fit: "BayesianFit",
    *,
    coverage_probability: float = 0.95,
    point_estimate: PointEstimate = "median",
    include_model_sigma: bool = True,
) -> list[Any]:
    """Map every ``(model, group)`` fit onto a ``FittedModel`` document object.

    Args:
        fit: The :class:`~fairfluids.analysis.bayesian.inference.BayesianFit`.
        coverage_probability: Probability mass of the reported credible interval
            (default ``0.95`` -> equal-tailed 2.5 %/97.5 % posterior quantiles).
        point_estimate: Posterior summary used for ``FittedParameter.value``;
            ``"median"`` (default, robust to skew) or ``"mean"``.
        include_model_sigma: Also report the observation-noise scale
            ``model_sigma`` as a fitted parameter (provenance of the fit's spread).

    Returns:
        One :class:`fairfluids.core.lib.FittedModel` per fitted ``(model, group)``,
        in the fit's insertion order.
    """
    return [
        _group_fit_to_fitted_model(
            gfit,
            coverage_probability=coverage_probability,
            point_estimate=point_estimate,
            include_model_sigma=include_model_sigma,
        )
        for gfit in fit.fits.values()
    ]


def fit_to_fairfluids_document(
    fit: "BayesianFit",
    document: Any,
    *,
    fluid_index: int = 0,
    coverage_probability: float = 0.95,
    point_estimate: PointEstimate = "median",
    include_model_sigma: bool = True,
) -> Any:
    """Write the posterior summaries back into a ``FAIRFluidsDocument``.

    Every ``(model, group)`` fit is converted to a ``FittedModel`` (see
    :func:`fit_to_fitted_models`) and appended to
    ``document.fluid[fluid_index].fitted_model``. Each model carries the fitted
    group's composition in ``applied_parameters``, so all fits of one run can
    safely live on a single fluid. The (mutated) ``document`` is returned for
    chaining.
    """
    if not document.fluid:
        raise ValueError(
            "Cannot write fitted models back: the document has no fluids."
        )
    if not -len(document.fluid) <= fluid_index < len(document.fluid):
        raise IndexError(
            f"fluid_index {fluid_index} out of range for document with "
            f"{len(document.fluid)} fluid(s)."
        )
    models = fit_to_fitted_models(
        fit,
        coverage_probability=coverage_probability,
        point_estimate=point_estimate,
        include_model_sigma=include_model_sigma,
    )
    document.fluid[fluid_index].fitted_model.extend(models)
    return document


__all__ = [
    "fit_to_fitted_models",
    "fit_to_fairfluids_document",
]
