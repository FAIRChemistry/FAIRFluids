# Migration – Paketstruktur `fairfluids`

## ThermoML-Pipelines

| Alt | Neu |
|-----|-----|
| `fairfluids.thermoml_to_fairfluids` (entfernt) | `fairfluids.io.thermoml_to_fairfluids` |
| `fairfluids.fairfluids_to_thermoml` (entfernt) | `fairfluids.io.fairfluids_to_thermoml` |
| `fairfluids.ThermoMLMapping.ThermoMLMapper` (entfernt) | `from fairfluids.io.thermoml_to_fairfluids import convert` und `FAIRFluidsDocument.model_validate(convert(...))` |

CLI-Beispiel:

- `python -m fairfluids.io.fairfluids_to_thermoml.main …`
- `python -m fairfluids.io.thermoml_to_fairfluids.main …`

## `FluidIO`

| Alt | Neu |
|-----|-----|
| `from fairfluids.core.fluid_io import FluidIO` | `from fairfluids.io import FluidIO` |

`fairfluids.core.fluid_io` re-exportiert weiterhin `FluidIO` (Kompatibilität).

## Visualisierung

| Alt | Neu (empfohlen) |
|-----|-----------------|
| `fairfluids.core.visualization` | `fairfluids.visualization` |

Thematische Untermodule: `fairfluids.visualization.composition`, `.dataframe_api`, `.filters`.

## PubChem

`fetch_compound_from_pubchem` liegt in `fairfluids.io.pubchem` und wird weiterhin aus `fairfluids.core.functionalities` re-exportiert, solange der Monolith besteht.

## CML

| Alt | Neu (empfohlen) |
|-----|------------------|
| `from fairfluids.core.functionalities import FAIRFluidsCMLParser` | `from fairfluids.io import FAIRFluidsCMLParser` oder `from fairfluids.io.cml_parser import FAIRFluidsCMLParser` |

`fairfluids.core.functionalities` re-exportiert den Parser weiterhin; `from fairfluids import FAIRFluidsCMLParser` bleibt unverändert.

## Analyse / Inspektion

- **Analyse (Fits, Aktivierungsenergie, DataFrames):** `fairfluids.analysis`
- **Inspektion:** `fairfluids.inspection`

## Entfernte API

- `fit_extendet_arrhebius` wurde entfernt; verwenden Sie `fit_extended_arrhenius`.
- Die Paket-Shims `fairfluids.thermoml_to_fairfluids` und `fairfluids.fairfluids_to_thermoml` (außerhalb von `fairfluids.io`) sowie das Modul `fairfluids.ThermoMLMapping` wurden entfernt. Bitte nur noch die Imports unter `fairfluids.io.*` verwenden.
