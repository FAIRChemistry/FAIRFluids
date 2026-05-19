"""
CLI entry point for ThermoML → FAIRFluids conversion.

Usage::

    python -m fairfluids.io.thermoml_to_fairfluids.main path/to/thermoml.xml [output.json]
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from .converter import convert


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s",
    )

    if len(sys.argv) < 2:
        print(
            "Usage: python -m fairfluids.io.thermoml_to_fairfluids.main <thermoml.xml> [output.json] [--fetch-from-pubchem]"
        )
        sys.exit(1)

    fetch_from_pubchem = "--fetch-from-pubchem" in sys.argv[1:]
    positional = [arg for arg in sys.argv[1:] if arg != "--fetch-from-pubchem"]
    if not positional:
        print(
            "Usage: python -m fairfluids.io.thermoml_to_fairfluids.main <thermoml.xml> [output.json] [--fetch-from-pubchem]"
        )
        sys.exit(1)

    xml_path = Path(positional[0])
    if not xml_path.exists():
        print(f"Error: file not found: {xml_path}")
        sys.exit(1)

    result = convert(xml_path, fetch_from_pubchem=fetch_from_pubchem)

    if len(positional) >= 2:
        out_path = Path(positional[1])
        out_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        print(f"Written to {out_path}")
    else:
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
