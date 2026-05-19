"""ThermoML -> FAIRFluids converter package exports."""

from __future__ import annotations

# Keep imports robust when execution context changes (e.g. moved directories,
# notebook paths, or direct script execution from repository root).
from .converter import convert

__all__ = ["convert"]
