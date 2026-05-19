"""CLI entry point for FAIRFluids -> ThermoML conversion."""

from __future__ import annotations

import sys
from pathlib import Path

from .converter import convert


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: python -m fairfluids.io.fairfluids_to_thermoml.main <fairfluids.json> [output.xml]"
        )
        sys.exit(1)

    in_path = Path(sys.argv[1])
    if not in_path.exists():
        print(f"Error: file not found: {in_path}")
        sys.exit(1)

    xml = convert(in_path)
    if len(sys.argv) >= 3:
        out_path = Path(sys.argv[2])
        out_path.write_text(xml, encoding="utf-8")
        print(f"Written to {out_path}")
    else:
        print(xml)


if __name__ == "__main__":
    main()
