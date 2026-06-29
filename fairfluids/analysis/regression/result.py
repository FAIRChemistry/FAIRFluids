"""Universal, model-agnostic result objects for regression fits.

These containers generalise the model-specific bundles from
``thin_layer.fit_types`` (``ArrheniusGroupKey`` -> :class:`GroupKey`,
``ArrheniusFitBundle`` -> :class:`FitResult`) so that *any* regression model
(Arrhenius, extended Arrhenius, VFT, future models) writes its derived
quantities into the same structure.

The design goal is a single "derived quantities" object (:class:`ParameterStack`)
that serialises back into a ``FAIRFluidsDocument`` via
:meth:`ParameterStack.to_fairfluids_document` (and the lower-level
:meth:`ParameterStack.to_fitted_models`), expressing uncertainties according to
the GUM (Guide to the Expression of Uncertainty in Measurement).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

import pandas as pd


@dataclass(frozen=True)
class FittedParameter:
    """A single fitted (or derived) quantity with optional uncertainty and unit.

    ``std`` is the standard deviation of the parameter when the underlying fit
    can estimate it (e.g. from the OLS covariance or ``curve_fit`` ``pcov``);
    otherwise it is ``None``.
    """

    name: str
    value: float
    std: Optional[float] = None
    unit: Optional[str] = None


@dataclass(frozen=True)
class GroupKey:
    """Grouping key for a fitted group.

    ``fluid_compounds`` and ``mole_fractions`` are parallel-indexed, matching the
    convention used throughout the extraction pipeline. This generalises
    ``thin_layer.fit_types.ArrheniusGroupKey``.
    """

    source_doi: Optional[str]
    fluid_compounds: tuple[str, ...] = ()
    mole_fractions: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        if self.fluid_compounds and self.mole_fractions:
            if len(self.fluid_compounds) != len(self.mole_fractions):
                raise ValueError(
                    "fluid_compounds and mole_fractions must have equal length: "
                    f"{len(self.fluid_compounds)} vs. {len(self.mole_fractions)}"
                )

    def mole_fraction(self, *name_substrings: str) -> Optional[float]:
        """Mole fraction of the first compound whose normalised name contains all
        ``name_substrings`` (case-insensitive, whitespace-insensitive)."""
        for comp, x in zip(self.fluid_compounds, self.mole_fractions):
            cn = str(comp).strip().lower().replace(" ", "")
            if all(sub.lower().replace(" ", "") in cn for sub in name_substrings):
                return float(x)
        return None


@dataclass(frozen=True)
class FitResult:
    """Result of fitting one model to one group.

    The fitted/derived quantities live in :attr:`parameters` keyed by name, so
    different models contribute their own parameter sets to the same container.
    """

    model_name: str
    group_key: GroupKey
    parameters: dict[str, FittedParameter]
    n_points: int
    r_squared: Optional[float] = None
    t_min: Optional[float] = None
    t_max: Optional[float] = None
    measurement_ids: tuple[str, ...] = field(default_factory=tuple)
    meta: dict[str, Any] = field(default_factory=dict)

    def value(self, name: str) -> Optional[float]:
        """Convenience accessor for a parameter value (``None`` if absent)."""
        param = self.parameters.get(name)
        return None if param is None else param.value

    def std(self, name: str) -> Optional[float]:
        """Convenience accessor for a parameter standard deviation."""
        param = self.parameters.get(name)
        return None if param is None else param.std


@dataclass
class ParameterStack:
    """A collection of :class:`FitResult` objects across groups and/or models.

    This is the universal "derived quantities" object returned by the fitting
    engine. It is intentionally model-agnostic: each :class:`FitResult` carries
    its own named parameters, so heterogeneous models can coexist in one stack.
    """

    results: list[FitResult] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.results)

    def __iter__(self):
        return iter(self.results)

    def model_names(self) -> list[str]:
        """Sorted unique model names present in the stack."""
        return sorted({r.model_name for r in self.results})

    def filter(
        self,
        *,
        model_name: Optional[str] = None,
        source_doi: Optional[str] = None,
    ) -> "ParameterStack":
        """Return a new stack keeping only results matching the given filters."""
        kept = [
            r
            for r in self.results
            if (model_name is None or r.model_name == model_name)
            and (source_doi is None or r.group_key.source_doi == source_doi)
        ]
        return ParameterStack(results=kept)

    def to_dataframe(self) -> pd.DataFrame:
        """Flatten the stack to one row per :class:`FitResult`.

        Each parameter ``p`` contributes a ``p`` column (value) and a ``p_std``
        column (standard deviation). Group metadata, goodness of fit and
        temperature range are included as well.
        """
        rows: list[dict[str, Any]] = []
        for res in self.results:
            row: dict[str, Any] = {
                "model_name": res.model_name,
                "source_doi": res.group_key.source_doi,
                "fluid_compounds": res.group_key.fluid_compounds,
                "mole_fractions": res.group_key.mole_fractions,
                "n_points": res.n_points,
                "R_squared": res.r_squared,
                "T_min": res.t_min,
                "T_max": res.t_max,
            }
            for name, param in res.parameters.items():
                row[name] = param.value
                row[f"{name}_std"] = param.std
            row.update(res.meta)
            rows.append(row)
        return pd.DataFrame(rows)

    def to_fitted_models(
        self,
        *,
        coverage_probability: Optional[float] = None,
    ) -> list[Any]:
        """Map every :class:`FitResult` onto a ``FittedModel`` document object.

        The result is a list of ``fairfluids.core.lib.FittedModel`` instances
        (one per fit) carrying GUM-style uncertainties. Each derived quantity
        becomes a ``FittedParameter`` with its value, unit and standard
        uncertainty; the composition of the fitted group is preserved in
        ``applied_parameters`` so a model stays self-describing regardless of the
        fluid it is attached to.

        Parameters
        ----------
        coverage_probability:
            If given (e.g. ``0.95``), an expanded uncertainty is derived from the
            standard uncertainty using a Student-t coverage factor based on the
            residual degrees of freedom. Requires SciPy; if unavailable, only the
            standard uncertainty is reported.
        """
        return [
            self._result_to_fitted_model(res, coverage_probability=coverage_probability)
            for res in self.results
        ]

    def to_fairfluids_document(
        self,
        document: Any,
        *,
        fluid_index: int = 0,
        coverage_probability: Optional[float] = None,
    ) -> Any:
        """Write the derived quantities back into a ``FAIRFluidsDocument``.

        Every :class:`FitResult` is converted to a ``FittedModel`` (see
        :meth:`to_fitted_models`) and appended to
        ``document.fluid[fluid_index].fitted_model``. The fitted group's
        composition is stored on each model, so all fits of a stack can safely
        live on a single fluid. The (mutated) ``document`` is returned for
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
        fluid = document.fluid[fluid_index]
        models = self.to_fitted_models(coverage_probability=coverage_probability)
        fluid.fitted_model.extend(models)
        return document

    @staticmethod
    def _result_to_fitted_model(
        result: "FitResult",
        *,
        coverage_probability: Optional[float] = None,
    ) -> Any:
        """Convert a single :class:`FitResult` into a ``FittedModel``."""
        from ...core.lib import (
            DistributionType,
            FitMethod,
            FittedModel,
            FittedParameter as LibFittedParameter,
            Parameters,
            ParameterValue,
            Properties,
            UncertaintyEvaluation,
            UnitDefinition,
        )
        from .spec import get_spec

        try:
            spec = get_spec(result.model_name)
            kind = spec.kind
            n_fitted = spec.n_fitted
            equation = spec.description or None
            observation = spec.observation
        except Exception:
            kind, n_fitted, equation, observation = None, 0, None, None

        method = (
            FitMethod.REGRESSION_NLS
            if kind == "nonlinear"
            else FitMethod.REGRESSION_OLS
        )

        fitted_property = None
        if observation is not None:
            try:
                fitted_property = Properties(observation)
            except ValueError:
                fitted_property = None

        dof: Optional[float] = None
        if result.n_points and n_fitted and result.n_points > n_fitted:
            dof = float(result.n_points - n_fitted)

        coverage_factor = _student_t_coverage_factor(coverage_probability, dof)

        param_property = {
            "Ea_J_mol": Properties.ACTIVATION_ENERGY,
            "Ea_kJ_mol": Properties.ACTIVATION_ENERGY,
        }

        parameters: list[Any] = []
        for name, param in result.parameters.items():
            unit = UnitDefinition(name=param.unit) if param.unit else None
            lib_param = LibFittedParameter(
                name=name,
                value=param.value,
                unit=unit,
                standard_uncertainty=param.std,
                uncertainty_evaluation=UncertaintyEvaluation.STATISTICAL,
                degrees_of_freedom=dof,
                distribution=DistributionType.STUDENT_T,
                properties=param_property.get(name),
            )
            if param.std is not None and coverage_factor is not None:
                expanded = coverage_factor * param.std
                lib_param.coverage_factor = coverage_factor
                lib_param.expanded_uncertainty = expanded
                lib_param.coverage_probability = coverage_probability
                lib_param.interval_low = param.value - expanded
                lib_param.interval_high = param.value + expanded
            parameters.append(lib_param)

        applied_parameters = [
            ParameterValue(
                parameters=Parameters.MOLE_FRACTION,
                parameterID=str(compound),
                paramValue=float(fraction),
            )
            for compound, fraction in zip(
                result.group_key.fluid_compounds, result.group_key.mole_fractions
            )
        ]

        method_description = f"fairfluids.analysis.regression; {kind or 'unknown'} fit"
        if result.group_key.source_doi:
            method_description += f"; source_doi={result.group_key.source_doi}"

        return FittedModel(
            model_name=result.model_name,
            model_equation=equation,
            method=method,
            method_description=method_description,
            fitted_property=fitted_property,
            parameter=parameters,
            r_squared=result.r_squared,
            n_points=result.n_points,
            temperature_lower=result.t_min,
            temperature_upper=result.t_max,
            applied_parameters=applied_parameters,
            source_measurement_ids=list(result.measurement_ids),
        )


def _student_t_coverage_factor(
    coverage_probability: Optional[float],
    dof: Optional[float],
) -> Optional[float]:
    """Student-t coverage factor ``k`` for a two-sided coverage interval.

    Returns ``None`` when no coverage probability/degrees of freedom are given
    or when SciPy is unavailable.
    """
    if coverage_probability is None or dof is None or dof <= 0:
        return None
    try:
        from scipy.stats import t as _student_t
    except Exception:
        return None
    return float(_student_t.ppf(0.5 * (1.0 + coverage_probability), dof))


def stack_from_results(results: Sequence[FitResult]) -> ParameterStack:
    """Build a :class:`ParameterStack` from any sequence of :class:`FitResult`."""
    return ParameterStack(results=list(results))


__all__ = [
    "FittedParameter",
    "GroupKey",
    "FitResult",
    "ParameterStack",
    "stack_from_results",
]
