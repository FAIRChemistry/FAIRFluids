"""Load the framework-provided symbolic models into the registry.

The unified model store lives as plain JSON under ``store/`` (one file per
property, e.g. ``viscosity.json`` / ``density.json``) in the *same*
``{"models": [...]}`` shape a user would author by hand. Importing
:mod:`fairfluids.analysis.models` calls :func:`load_builtin_models` once so the
standard Arrhenius / VFT / Litovitz / density models are immediately available
to both fit backends and to the regression/Bayesian bridges — there is no
codegen step and no generated package to keep in sync.
"""

from __future__ import annotations

from pathlib import Path

from .io import load_models
from .registry import registry

STORE_DIR = Path(__file__).parent / "store"


def load_builtin_models(*, overwrite: bool = True) -> list[str]:
    """Register every model in ``store/*.json`` and return their names.

    ``overwrite=True`` (the default) makes this idempotent so re-importing the
    package — or calling it again after a registry ``clear()`` — simply refreshes
    the built-ins rather than raising on name collisions.
    """
    loaded: list[str] = []
    for path in sorted(STORE_DIR.glob("*.json")):
        for model in load_models(path):
            registry.register(model, overwrite=overwrite)
            loaded.append(model.name)
    return loaded


__all__ = ["load_builtin_models", "STORE_DIR"]
