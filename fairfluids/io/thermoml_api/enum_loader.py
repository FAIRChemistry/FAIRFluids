"""Load ThermoML enumeration values from specifications/ThermoML.md."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from fairfluids.io.thermoml_to_fairfluids.mappers.property_mapper import PROPERTY_MAP

_ENUM_BLOCK_RE = re.compile(
    r"^###\s+(e\w+)\s*\n+```python\n(.*?)```",
    re.MULTILINE | re.DOTALL,
)
_ENUM_VALUE_RE = re.compile(r"=\s*['\"](.+?)['\"]")

_DEFAULT_SPEC = (
    Path(__file__).resolve().parents[3] / "specifications" / "ThermoML.md"
)


def _spec_path(spec_path: Path | None = None) -> Path:
    return spec_path if spec_path is not None else _DEFAULT_SPEC


@lru_cache(maxsize=4)
def load_enums(spec_path: str | None = None) -> dict[str, list[str]]:
    """Parse enumeration blocks from the ThermoML specification markdown."""
    path = Path(spec_path) if spec_path is not None else _DEFAULT_SPEC
    text = path.read_text(encoding="utf-8")
    enums: dict[str, list[str]] = {}
    for match in _ENUM_BLOCK_RE.finditer(text):
        name = match.group(1)
        block = match.group(2)
        values = [m.group(1) for m in _ENUM_VALUE_RE.finditer(block)]
        if values:
            enums[name] = values
    return enums


def get_property_options(spec_path: str | None = None) -> list[str]:
    """
    Return deduplicated ThermoML property name strings for UI multiselects.

    Combines spec enums (``eMiscellaneous``, ``ePropName``) with keys from
    the FAIRFluids property mapper, because transport/volumetric property enums
    are not fully listed in the markdown spec.
    """
    enums = load_enums(spec_path)
    options: set[str] = set()
    for enum_name in ("eMiscellaneous", "ePropName"):
        options.update(enums.get(enum_name, []))
    options.update(PROPERTY_MAP.keys())
    return sorted(options)
