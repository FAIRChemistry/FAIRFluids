"""Converter orchestration for FAIRFluids -> ThermoML."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .canonical_builder import build_canonical
from .parser import parse
from .thermoml_builder import build_thermoml


def convert(source: str | Path | Dict[str, Any]) -> str:
    """Convert FAIRFluids JSON (path or dict) to ThermoML XML."""
    raw = parse(source)
    canonical = build_canonical(raw)
    return build_thermoml(raw, canonical)
