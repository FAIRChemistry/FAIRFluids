"""Document-centric data preparation for Bayesian fitting.

:class:`BayesianDataset` takes one or more :class:`FAIRFluidsDocument` instances,
extracts a chosen property and any requested features via
:func:`fairfluids.core.functionalities.extract_property_dataframe`, groups rows
into :class:`BayesianGroup` objects, and prepares JAX arrays for downstream
inference.

The grouping schema (``group_by``) and the feature columns (``features``) are
fully user-configurable: this is what makes the framework generic across
``viscosity-vs-T``, ``density-vs-composition`` and similar workflows without
re-writing the data pipeline.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any, Callable, Iterable, Mapping

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from fairfluids.core.functionalities import extract_property_dataframe
from fairfluids.core.lib import FAIRFluidsDocument

if TYPE_CHECKING:
    import jax


def _to_jax_array(arr: np.ndarray) -> "jax.Array":
    import jax.numpy as jnp

    return jnp.asarray(arr)


def _group_key_to_str(key: tuple[Any, ...]) -> str:
    return " | ".join(
        f"{x:.6g}" if isinstance(x, float) else str(x) for x in key
    )


class BayesianGroup(BaseModel):
    """A single fit-ready measurement group.

    A group corresponds to one combination of ``group_by`` values (e.g. one DOI
    at one composition) and holds the prepared feature arrays plus the (optionally
    log-transformed) observation and its propagated uncertainty.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=False)

    group_id: tuple[Any, ...]
    group_label: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    features: dict[str, np.ndarray]
    observation: np.ndarray
    observation_uncertainty: np.ndarray | None = None
    raw_observation: np.ndarray
    raw_observation_uncertainty: np.ndarray | None = None
    log_observation: bool = True
    dataframe: pd.DataFrame

    @property
    def n_points(self) -> int:
        return int(self.observation.shape[0])

    def features_jax(self) -> dict[str, "jax.Array"]:
        return {name: _to_jax_array(arr) for name, arr in self.features.items()}

    def observation_jax(self) -> "jax.Array":
        return _to_jax_array(self.observation)

    def observation_uncertainty_jax(self) -> "jax.Array | None":
        if self.observation_uncertainty is None:
            return None
        return _to_jax_array(self.observation_uncertainty)

    def __repr__(self) -> str:
        return (
            f"BayesianGroup(label={self.group_label!r}, n={self.n_points}, "
            f"features={list(self.features)}, log_observation={self.log_observation})"
        )


class BayesianDataset(BaseModel):
    """Collection of :class:`BayesianGroup` objects with shared schema.

    Construct via :meth:`from_documents`; iterate with :meth:`groups` or filter
    with :meth:`select`. The dataset is immutable conceptually but stored as a
    regular Pydantic model so users can attach additional metadata.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=False)

    property: str
    feature_names: tuple[str, ...]
    group_by: tuple[str, ...]
    log_observation: bool = True
    groups: list[BayesianGroup]
    dropped_groups: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def uncertainty_coverage(self) -> float:
        """Fraction of groups that have an attached observation uncertainty (0.0-1.0)."""
        if not self.groups:
            return 0.0
        n = sum(1 for g in self.groups if g.observation_uncertainty is not None)
        return n / len(self.groups)

    @classmethod
    def from_documents(
        cls,
        documents: Mapping[str, FAIRFluidsDocument] | Iterable[FAIRFluidsDocument],
        *,
        property: str,
        features: Iterable[str] = ("temperature",),
        group_by: Iterable[str] = ("source_doi",),
        min_points: int = 3,
        log_observation: bool = True,
        extract_kwargs: dict[str, Any] | None = None,
        composition_filter: Mapping[str, tuple[float, float]] | None = None,
        system_label_key: str = "system_name",
    ) -> "BayesianDataset":
        """Build a dataset from one or more FAIRFluids documents.

        Args:
            documents: A mapping ``system_label -> FAIRFluidsDocument`` (preferred) or
                a plain iterable of documents. When a mapping is supplied, the keys
                are attached to each row as ``system_label_key``.
            property: Property to extract (e.g. ``"viscosity"``, ``"density"``).
            features: Column names from the extracted DataFrame to use as model features
                (must match the chosen model's ``feature_names``).
            group_by: Columns to group rows by. Typically includes ``source_doi`` and one
                or more composition columns (``mole_fraction_water`` etc.).
            min_points: Drop groups with fewer than this many points.
            log_observation: Apply ``log`` to the observation column before fitting and
                propagate its uncertainty through ``sigma / value``.
            extract_kwargs: Extra keyword arguments forwarded to
                :func:`extract_property_dataframe` for every document.
            composition_filter: Optional inclusive ranges
                ``{column: (low, high)}`` applied to the concatenated DataFrame.
            system_label_key: Column name to use for the per-document label when
                ``documents`` is a mapping.
        """
        feature_names = tuple(features)
        group_by_cols = tuple(group_by)
        extra = dict(extract_kwargs or {})

        if isinstance(documents, Mapping):
            doc_iter = list(documents.items())
        else:
            doc_iter = [(None, doc) for doc in documents]

        frames: list[pd.DataFrame] = []
        for label, doc in doc_iter:
            df = extract_property_dataframe(
                doc, property_type=property, **extra
            )
            if df.empty:
                continue
            if label is not None:
                df = df.copy()
                df[system_label_key] = label
            frames.append(df)

        if not frames:
            raise ValueError(
                f"No data extracted for property={property!r} from supplied documents."
            )

        df_all = pd.concat(frames, ignore_index=True)

        if composition_filter:
            for col, (low, high) in composition_filter.items():
                if col not in df_all.columns:
                    raise KeyError(
                        f"composition_filter references unknown column {col!r}. "
                        f"Available: {list(df_all.columns)}"
                    )
                col_num = pd.to_numeric(df_all[col], errors="coerce")
                mask = (col_num >= low) & (col_num <= high)
                df_all = df_all[mask].reset_index(drop=True)

        property_value_col = f"{property}_value"
        property_unc_col = f"{property}_uncertainty"
        if property_value_col not in df_all.columns:
            raise KeyError(
                f"Extracted DataFrame is missing {property_value_col!r}. "
                f"Available columns: {list(df_all.columns)}"
            )
        missing_features = [c for c in feature_names if c not in df_all.columns]
        if missing_features:
            raise KeyError(
                f"Extracted DataFrame is missing requested feature columns: {missing_features}. "
                f"Available: {list(df_all.columns)}"
            )
        missing_group = [c for c in group_by_cols if c not in df_all.columns]
        if missing_group:
            raise KeyError(
                f"Extracted DataFrame is missing group_by columns: {missing_group}. "
                f"Available: {list(df_all.columns)}"
            )

        # Drop rows with NaN in critical columns
        critical_cols = [property_value_col, *feature_names]
        df_all = df_all.dropna(subset=critical_cols).reset_index(drop=True)

        sort_cols = [c for c in (*group_by_cols, *feature_names) if c in df_all.columns]
        if sort_cols:
            df_all = df_all.sort_values(sort_cols).reset_index(drop=True)

        groups: list[BayesianGroup] = []
        dropped: list[dict[str, Any]] = []
        for raw_key, sub in df_all.groupby(list(group_by_cols), dropna=False, sort=False):
            key = raw_key if isinstance(raw_key, tuple) else (raw_key,)
            n_points = len(sub)
            if n_points < min_points:
                dropped.append({"group_id": key, "n_points": n_points, "reason": "min_points"})
                continue

            features_arrays = {
                col: np.asarray(sub[col].to_numpy(), dtype=float) for col in feature_names
            }
            raw_obs = np.asarray(sub[property_value_col].to_numpy(), dtype=float)
            if log_observation:
                obs = np.log(np.clip(raw_obs, 1e-300, None))
            else:
                obs = raw_obs

            raw_unc: np.ndarray | None = None
            obs_unc: np.ndarray | None = None
            if property_unc_col in sub.columns:
                raw_unc_arr = pd.to_numeric(sub[property_unc_col], errors="coerce").to_numpy(
                    dtype=float
                )
                if np.any(~np.isnan(raw_unc_arr)):
                    raw_unc = raw_unc_arr
                    if log_observation:
                        with np.errstate(divide="ignore", invalid="ignore"):
                            propagated = raw_unc_arr / np.where(raw_obs > 0, raw_obs, np.nan)
                        if np.all(np.isnan(propagated)):
                            obs_unc = None
                        else:
                            obs_unc = propagated
                    else:
                        obs_unc = raw_unc_arr

            metadata = {col: sub[col].iloc[0] for col in sub.columns if col not in feature_names}
            metadata["group_by"] = dict(zip(group_by_cols, key))

            groups.append(
                BayesianGroup(
                    group_id=key,
                    group_label=_group_key_to_str(key),
                    metadata=metadata,
                    features=features_arrays,
                    observation=obs,
                    observation_uncertainty=obs_unc,
                    raw_observation=raw_obs,
                    raw_observation_uncertainty=raw_unc,
                    log_observation=log_observation,
                    dataframe=sub.reset_index(drop=True),
                )
            )

        if not groups:
            raise ValueError(
                f"No groups passed min_points={min_points}; dropped {len(dropped)} groups."
            )

        n_with_unc = sum(1 for g in groups if g.observation_uncertainty is not None)
        coverage = n_with_unc / len(groups)
        if coverage < 1.0:
            missing = len(groups) - n_with_unc
            warnings.warn(
                f"Measurement uncertainty missing for {missing}/{len(groups)} groups "
                f"({100 * (1 - coverage):.0f} %). Those groups will rely solely on "
                f"model_sigma. Check whether {property!r}_uncertainty is present in the "
                f"source documents if you expected per-point sigmas.",
                UserWarning,
                stacklevel=2,
            )

        return cls(
            property=property,
            feature_names=feature_names,
            group_by=group_by_cols,
            log_observation=log_observation,
            groups=groups,
            dropped_groups=dropped,
        )

    def select(
        self,
        predicate: Callable[[BayesianGroup], bool] | tuple[Any, ...],
    ) -> "BayesianDataset":
        """Return a new dataset keeping only groups for which ``predicate(group)`` is True.

        Pass a callable for arbitrary filtering or a ``group_id`` tuple to keep a
        single group.
        """
        if callable(predicate):
            kept = [g for g in self.groups if predicate(g)]
        else:
            kept = [g for g in self.groups if g.group_id == predicate]
        return self.model_copy(update={"groups": kept})

    def to_overview(self) -> pd.DataFrame:
        """Return a one-row-per-group summary DataFrame for quick inspection."""
        rows: list[dict[str, Any]] = []
        for grp in self.groups:
            row: dict[str, Any] = {
                "group_label": grp.group_label,
                "n_points": grp.n_points,
                "has_uncertainty": grp.observation_uncertainty is not None,
            }
            for col, val in zip(self.group_by, grp.group_id):
                row[col] = val
            for feat in self.feature_names:
                values = grp.features[feat]
                row[f"{feat}_min"] = float(np.min(values))
                row[f"{feat}_max"] = float(np.max(values))
            row["obs_min"] = float(np.min(grp.observation))
            row["obs_max"] = float(np.max(grp.observation))
            rows.append(row)
        return pd.DataFrame(rows)

    def iter_groups(self) -> Iterable[BayesianGroup]:
        return iter(self.groups)

    def __len__(self) -> int:
        return len(self.groups)


__all__ = ["BayesianDataset", "BayesianGroup"]
