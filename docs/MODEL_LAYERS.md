# Modell-Schichten (Phase 1)

## `fairfluids/core/lib.py` (generiert)

- Wird vom Codegenerator erzeugt; **nicht** manuell mit Erweiterungslogik vermischen.
- Enthält die Pydantic-Basismodelle für das FAIRFluids-JSON-Schema.

## `fairfluids/core/fairfluids.py` (manuell)

- Bewusst von `lib.py` getrennt: hier liegen Subklassen / Methoden wie `save_to_json`, die bei Regenerierung von `lib.py` erhalten bleiben sollen.
- **Regel:** Neue domänenspezifische Methoden am Dokument gehören hierher, nicht in die generierte `lib.py`.
