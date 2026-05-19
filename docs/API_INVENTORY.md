# Öffentliche API (Phase 0 – Inventar)

Die folgenden Symbole werden über **`fairfluids`** (Root) exportiert (`fairfluids/__init__.py`):

| Symbol | Herkunftsmodul (kanonisch) |
|--------|----------------------------|
| `FAIRFluidsDocument`, `Version`, `Citation`, … | `fairfluids.core.lib` / `fairfluids.core.fairfluids` |
| `FluidIO` | `fairfluids.io.fluid_io` |
| `FAIRFluidsCMLParser` | `fairfluids.io.cml_parser` (Root: `from fairfluids.io import …`) |
| `filter_fluid_compounds_by_mole_fractions`, … | `fairfluids.core.functionalities` |
| `filter_fluid_measurements` | `fairfluids.visualization` (über `fairfluids.core.visualization`) |
| `save_plot_as_svg`, `reset_plot_counter` | `fairfluids.core.plot_utils` |

Zusätzliche **kanonische Pakete** (explizite Imports empfohlen):

| Bereich | Import |
|---------|--------|
| I/O | `from fairfluids.io import FluidIO, FAIRFluidsCMLParser` |
| ThermoML → FF | `from fairfluids.io.thermoml_to_fairfluids import convert` |
| FF → ThermoML | `from fairfluids.io.fairfluids_to_thermoml import convert` |
| Inspektion | `from fairfluids.inspection import show_available_parameters` |
| Analyse (Fits, Tabellen) | `from fairfluids.analysis import fit_arrhenius, …` |
| Visualisierung | `from fairfluids.visualization import …` |

## `save_to_json`

`FAIRFluidsDocument.save_to_json` wird in `fairfluids.core.fairfluids` definiert. Zusätzlich hängt `fairfluids/__init__.py` aus Kompatibilitätsgründen eine Fallback-Methode an, falls die generierte Basisklasse keine `save_to_json` hätte.
