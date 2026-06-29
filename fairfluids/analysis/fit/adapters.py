"""Convenience adapters: fit a :class:`SymbolicModel` straight from prepared data.

The fitting backends (:mod:`.least_squares`, :mod:`.mcmc`) take plain feature
dicts plus a *raw* observation array. In practice the data already lives in
``BayesianGroup`` / ``BayesianDataset`` containers produced by
:mod:`fairfluids.analysis.bayesian.data`. These adapters bridge the two without
importing those classes — they are **duck-typed**, so anything exposing the same
attributes works (and the ``symbolic`` package keeps its zero-coupling promise).

Two traps are handled here so callers never hit them:

* **Double log.** A group stores both ``observation`` (already log-transformed
  when ``log_observation`` is set) and ``raw_observation`` (linear). The symbolic
  backends apply the log *internally* according to ``model.log_observation``, so
  these adapters must feed the **raw** array — never the pre-transformed one. We
  also assert that the group's and the model's ``log_observation`` agree, because
  a silent mismatch would corrupt the fit.
* **Feature-name aliasing.** A model may call a feature ``T`` while the group's
  column is ``temperature``. Pass ``feature_map={"T": "temperature"}`` to bridge
  the names; otherwise the model's own feature names are used verbatim and a
  missing column raises a clear error.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

import numpy as np

from ..models.model import SymbolicModel

# Backend aliases accepted by the ``backend`` argument.
_LSQ_BACKENDS = {"least_squares", "lsq", "regression", "scipy"}
_MCMC_BACKENDS = {"mcmc", "bayesian", "numpyro", "nuts"}


def _aligned_features(
    model: SymbolicModel,
    group: Any,
    feature_map: Optional[Mapping[str, str]],
) -> dict[str, np.ndarray]:
    """Pull the model's feature arrays out of a group, honouring name aliases."""
    group_features = getattr(group, "features", None)
    if not isinstance(group_features, Mapping):
        raise TypeError(
            "Group object has no 'features' mapping; expected a BayesianGroup-like "
            f"container, got {type(group).__name__}."
        )
    fmap = dict(feature_map or {})
    aligned: dict[str, np.ndarray] = {}
    missing: list[str] = []
    for fname in model.features:
        column = fmap.get(fname, fname)
        if column not in group_features:
            missing.append(f"{fname!r} (looked up as column {column!r})")
        else:
            aligned[fname] = np.asarray(group_features[column], dtype=float)
    if missing:
        raise KeyError(
            f"Model {model.name!r} needs feature(s) {missing} but the group only "
            f"provides columns {sorted(group_features)}. Pass feature_map=... to "
            "bridge differing names."
        )
    return aligned


def _check_log_observation(model: SymbolicModel, group: Any) -> None:
    """Guard against a model/group disagreement on the log scale."""
    group_log = getattr(group, "log_observation", None)
    if group_log is not None and bool(group_log) != bool(model.log_observation):
        label = getattr(group, "group_label", "?")
        raise ValueError(
            f"log_observation mismatch: model {model.name!r} uses "
            f"log_observation={model.log_observation}, but group {label!r} was "
            f"prepared with log_observation={group_log}. The symbolic backend "
            "applies the log itself from the model flag, so the two must agree. "
            "Rebuild the dataset with the matching flag (or flip the model's)."
        )


def _raw_observation(group: Any) -> tuple[np.ndarray, Optional[np.ndarray]]:
    """Return the *linear* observation (and uncertainty) — never the log-scaled one."""
    if not hasattr(group, "raw_observation"):
        raise AttributeError(
            "Group object has no 'raw_observation'; the symbolic backends need the "
            "linear (untransformed) values to apply the log themselves."
        )
    raw_obs = np.asarray(group.raw_observation, dtype=float)
    raw_unc = getattr(group, "raw_observation_uncertainty", None)
    if raw_unc is not None:
        raw_unc = np.asarray(raw_unc, dtype=float)
    return raw_obs, raw_unc


def fit_group(
    model: SymbolicModel,
    group: Any,
    *,
    backend: str = "least_squares",
    feature_map: Optional[Mapping[str, str]] = None,
    **backend_kwargs: Any,
):
    """Fit ``model`` to a single prepared group.

    Args:
        model: The symbolic model to fit.
        group: A ``BayesianGroup``-like object exposing ``features``,
            ``raw_observation``, ``raw_observation_uncertainty`` and
            ``log_observation``.
        backend: ``"least_squares"`` (SciPy, default) or ``"mcmc"`` (NumPyro).
        feature_map: Optional ``{model_feature: group_column}`` aliases.
        **backend_kwargs: Forwarded to :func:`.regression.fit` or
            :func:`.bayesian.fit_mcmc` (e.g. ``priors=...`` for MCMC).

    Returns:
        A :class:`.regression.SymbolicFit` for least squares, or the
        ``numpyro.infer.MCMC`` object for the Bayesian backend.
    """
    _check_log_observation(model, group)
    feats = _aligned_features(model, group, feature_map)
    raw_obs, raw_unc = _raw_observation(group)

    key = backend.lower()
    if key in _LSQ_BACKENDS:
        from .least_squares import fit as _fit

        return _fit(model, feats, raw_obs, observation_uncertainty=raw_unc, **backend_kwargs)
    if key in _MCMC_BACKENDS:
        from .mcmc import fit_mcmc as _fit_mcmc

        return _fit_mcmc(
            model, feats, raw_obs, observation_uncertainty=raw_unc, **backend_kwargs
        )
    raise ValueError(
        f"Unknown backend {backend!r}. Use one of {sorted(_LSQ_BACKENDS)} or "
        f"{sorted(_MCMC_BACKENDS)}."
    )


@dataclass(frozen=True)
class DatasetFit:
    """Per-group results of fitting one model across a whole dataset.

    ``fits`` maps each fitted group's label to its backend result; ``failures``
    maps the label of any group that errored (or, for least squares, returned
    ``success=False``) to a short reason string.
    """

    model_name: str
    backend: str
    fits: dict[str, Any] = field(default_factory=dict)
    failures: dict[str, str] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.fits)

    def __iter__(self):
        return iter(self.fits.items())

    def __getitem__(self, label: str) -> Any:
        return self.fits[label]

    @property
    def n_failed(self) -> int:
        return len(self.failures)

    def to_frame(self):
        """One-row-per-group parameter table (least-squares fits only).

        Builds a tidy ``pandas`` DataFrame with a column per parameter value, its
        ``*_std`` companion, ``r_squared`` and the resolved constants. Returns an
        empty frame when there is nothing tabular to show (e.g. MCMC results).
        """
        import pandas as pd

        rows: list[dict[str, Any]] = []
        for label, result in self.fits.items():
            params = getattr(result, "params", None)
            if not isinstance(params, Mapping):
                continue  # not a SymbolicFit (e.g. an MCMC object)
            row: dict[str, Any] = {"group_label": label}
            for name, value in params.items():
                val, std = value
                row[name] = val
                row[f"{name}_std"] = std
            for name, value in getattr(result, "derived", {}).items():
                val, std = value
                row[name] = val
                row[f"{name}_std"] = std
            for cname, cval in getattr(result, "constants", {}).items():
                row[f"const_{cname}"] = cval
            row["r_squared"] = getattr(result, "r_squared", None)
            rows.append(row)
        return pd.DataFrame(rows)


def fit_dataset(
    model: SymbolicModel,
    dataset: Any,
    *,
    backend: str = "least_squares",
    feature_map: Optional[Mapping[str, str]] = None,
    on_error: str = "collect",
    **backend_kwargs: Any,
) -> DatasetFit:
    """Fit ``model`` to every group in a dataset.

    Args:
        model: The symbolic model to fit.
        dataset: A ``BayesianDataset``-like object: either iterable of groups or
            exposing a ``groups`` list.
        backend: ``"least_squares"`` (default) or ``"mcmc"``.
        feature_map: Optional ``{model_feature: group_column}`` aliases.
        on_error: ``"collect"`` (default) records failures and continues;
            ``"raise"`` re-raises the first exception.
        **backend_kwargs: Forwarded to the per-group fit.

    Returns:
        A :class:`DatasetFit` aggregating the per-group results and failures.
    """
    if on_error not in ("collect", "raise"):
        raise ValueError(f"on_error must be 'collect' or 'raise', got {on_error!r}.")

    groups = getattr(dataset, "groups", dataset)
    result = DatasetFit(model_name=model.name, backend=backend)

    for index, group in enumerate(groups):
        label = getattr(group, "group_label", f"group_{index}")
        try:
            fit_result = fit_group(
                model, group, backend=backend, feature_map=feature_map, **backend_kwargs
            )
        except Exception as exc:  # noqa: BLE001 — surfaced via failures / re-raised
            if on_error == "raise":
                raise
            result.failures[label] = f"{type(exc).__name__}: {exc}"
            continue

        # Least-squares reports non-convergence via success=False rather than raising.
        if getattr(fit_result, "success", True) is False:
            result.failures[label] = "fit did not converge (success=False)"
            continue
        result.fits[label] = fit_result

    return result


__all__ = ["fit_group", "fit_dataset", "DatasetFit"]
