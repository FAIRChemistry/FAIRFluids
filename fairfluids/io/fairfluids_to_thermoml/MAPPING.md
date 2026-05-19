# FAIRFluids-to-ThermoML Mapping (minimal)

Dieses Modul implementiert einen minimalen Reverse-Flow:

`FAIRFluids JSON -> RawFairFluids -> CanonicalDataset -> ThermoML XML`

## Scope

- Nur der bereits durch `thermoml_to_fairfluids` abgedeckte Kernbereich wird rueckwaerts erzeugt.
- Fokus liegt auf `Citation`, `Compound`, `PureOrMixtureData`, `Property`, `Variable`/`Constraint` und `NumValues`.
- Nicht gemappte Spezialfaelle bleiben unveraendert als Textwerte, statt implizit umgedeutet zu werden.

## Mapping-Regeln

- Properties: FAIRFluids `properties` wird ueber Reverse-Tabellen auf ThermoML `ePropName` gemappt.
- Parameter: FAIRFluids `parameters` wird auf ThermoML Variable-/Constraint-Typnamen gemappt.
- Units: FAIRFluids `unit.name` wird (wenn bekannt) als Unit-Suffix in den ThermoML-Typnamen eingebaut.
- Messzeilen:
  - Konstante Parameter ueber alle Zeilen werden als `Constraint` modelliert.
  - Variierende Parameter werden als `Variable` modelliert.
  - Unsicherheiten werden als `VarUncertainty` bzw. `PropUncertainty` geschrieben.

## Grenzen

- Nur ein minimaler Satz an Property-/Parameter-/Unit-Mappings ist fuer den Start vorgesehen.
- Erweiterte ThermoML-Elemente (z. B. umfangreiche Methodik, spezielle Unsicherheitsformen) sind initial nicht vollstaendig abgebildet.
