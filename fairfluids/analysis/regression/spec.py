"""Model specifications and a registry for regression fit kernels.

The :mod:`.bridge` module synthesises one :class:`RegressionModelSpec` per
symbolic model, pairs it with a low-level ``fit`` kernel and registers both via
:func:`register_model`. The engine looks models up by name through
:func:`get_model` and stays completely model-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np


@dataclass(frozen=True)
class RawFit:
    """Low-level output of a fit kernel for a single group.

    ``params`` maps each parameter name to ``(value, std)`` where ``std`` may be
    ``None`` when the kernel cannot estimate it. ``success`` is ``False`` when a
    (typically nonlinear) fit failed to converge; such groups are skipped by the
    engine.
    """

    params: dict[str, tuple[float, Optional[float]]]
    r_squared: Optional[float] = None
    success: bool = True


# A fit kernel maps (T, y, sigma) -> RawFit. ``sigma`` carries per-point
# uncertainties on the (transformed) observation scale, or ``None``.
FitKernel = Callable[[np.ndarray, np.ndarray, Optional[np.ndarray]], RawFit]


@dataclass(frozen=True)
class RegressionModelSpec:
    """Declarative metadata describing one regression model.

    Mirrors the spirit of ``fairfluids.analysis.bayesian`` model metadata:
    ``param_names`` plus units fully describe the parameters a model emits,
    while ``observation``/``y_transform`` describe the data it consumes.
    """

    name: str
    kind: str  # "linear" | "nonlinear"
    param_names: tuple[str, ...]
    observation: str = "viscosity"
    property: str = "viscosity"
    """Physical property the model describes (e.g. ``"viscosity"`` or ``"density"``)."""
    y_transform: str = "log"  # "log" | "identity"
    min_points: int = 2
    n_fitted: int = 0
    """Number of primary fitted coefficients (design columns for ``linear``,
    free parameters for ``nonlinear``). Used to derive the residual degrees of
    freedom ``n_points - n_fitted`` for GUM uncertainty reporting."""
    param_units: dict[str, Optional[str]] = field(default_factory=dict)
    description: str = ""

    def unit(self, param_name: str) -> Optional[str]:
        """Unit string for ``param_name`` (``None`` when dimensionless/unknown)."""
        return self.param_units.get(param_name)


class _ModelRegistry:
    """Module-private registry of regression model specs and their kernels."""

    def __init__(self) -> None:
        self._specs: dict[str, RegressionModelSpec] = {}
        self._kernels: dict[str, FitKernel] = {}

    def register(self, spec: RegressionModelSpec, kernel: FitKernel) -> None:
        name = spec.name
        if not name:
            raise ValueError("RegressionModelSpec.name must be non-empty.")
        if name in self._specs and self._specs[name] is not spec:
            raise ValueError(
                f"Regression model name collision: {name!r} is already registered."
            )
        self._specs[name] = spec
        self._kernels[name] = kernel

    def get_spec(self, name: str) -> RegressionModelSpec:
        if name not in self._specs:
            raise KeyError(
                f"No regression model registered under {name!r}. "
                f"Available: {sorted(self._specs)}"
            )
        return self._specs[name]

    def get_kernel(self, name: str) -> FitKernel:
        if name not in self._kernels:
            raise KeyError(
                f"No regression model registered under {name!r}. "
                f"Available: {sorted(self._kernels)}"
            )
        return self._kernels[name]

    def names(self) -> list[str]:
        return sorted(self._specs)


ModelRegistry = _ModelRegistry()


def register_model(spec: RegressionModelSpec, kernel: FitKernel) -> None:
    """Register a model spec together with its fit kernel."""
    ModelRegistry.register(spec, kernel)


def get_model(name: str) -> tuple[RegressionModelSpec, FitKernel]:
    """Return ``(spec, kernel)`` for a registered model name."""
    return ModelRegistry.get_spec(name), ModelRegistry.get_kernel(name)


def get_spec(name: str) -> RegressionModelSpec:
    """Return the :class:`RegressionModelSpec` for a registered model name."""
    return ModelRegistry.get_spec(name)


def list_models() -> list[str]:
    """Return the names of all currently registered regression models."""
    return ModelRegistry.names()


__all__ = [
    "RawFit",
    "FitKernel",
    "RegressionModelSpec",
    "ModelRegistry",
    "register_model",
    "get_model",
    "get_spec",
    "list_models",
]
