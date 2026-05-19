"""
Flache Sicht auf Messungen direkt aus ``FAIRFluidsDocument``-Instanzen.

Intern wird die Extraktionslogik aus ``fairfluids.visualization.core_plots``
pro Fluid wiederverwendet (Mini-Dokument mit einem Fluid), damit Indizes
und Auflösung der Parameter mit dem Hauptprojekt übereinstimmen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Optional, Sequence, Union

from fairfluids import FAIRFluidsDocument

from fairfluids.visualization.core_plots import _extract_measurements_with_all_parameters


def _normalize_document_list(
    docs: Union[FAIRFluidsDocument, Sequence[FAIRFluidsDocument]],
) -> list[FAIRFluidsDocument]:
    """
    Akzeptiert ein einzelnes Dokument oder eine Sequenz.

    Ein einzelnes ``FAIRFluidsDocument`` würde sonst bei ``enumerate(docs)``
    fälschlich über Modell-Felder (Tupel) iterieren.
    """
    if isinstance(docs, FAIRFluidsDocument):
        return [docs]
    return list(docs)


@dataclass(frozen=True)
class MeasurementView:
    """Eine Messung in tabellarisch nutzbarer Form, ohne pandas."""

    document_index: int
    fluid_index: int
    measurement_id: Optional[str]
    source_doi: Optional[str]
    property_type: Any
    property_value: Optional[float]
    temperature: Optional[float]
    mole_fractions: list[Any]
    fluid_compounds: list[str]
    uncertainty: Optional[float] = None
    extra_parameters: dict[str, Any] = field(default_factory=dict)


def _mini_doc(parent: FAIRFluidsDocument, fluid: Any) -> FAIRFluidsDocument:
    """Ein-Fluid-Dokument: gleiche ``compound``-Liste, ein ``fluid``."""
    return FAIRFluidsDocument(
        version=parent.version,
        citation=parent.citation,
        compound=list(parent.compound),
        fluid=[fluid],
    )


def iter_measurement_views(
    doc: FAIRFluidsDocument,
    *,
    document_index: int = 0,
    property_types: Optional[Sequence[str]] = None,
    fluid_compounds: Optional[Union[str, Sequence[str]]] = None,
    required_compounds: Optional[Union[str, Sequence[str]]] = None,
) -> Iterator[MeasurementView]:
    """
    Iteriert alle extrahierbaren Messungen eines Dokuments.

    Args:
        doc: Validiertes FAIRFluids-Dokument.
        document_index: Index bei Multi-Dokument-Workflows (für Provenance).
        property_types: Optional, z. B. ``("viscosity",)`` — gleiche Semantik
            wie in ``_extract_measurements_with_all_parameters``.
        fluid_compounds / required_compounds: Filter wie im Hauptprojekt.
    """
    for fluid_index, fluid in enumerate(doc.fluid):
        mini = _mini_doc(doc, fluid)
        rows = _extract_measurements_with_all_parameters(
            mini,
            property_types=property_types,
            fluid_compounds=fluid_compounds,
            required_compounds=required_compounds,
        )
        reserved = {
            "fluid_compounds",
            "property_type",
            "property_value",
            "uncertainty",
            "temperature",
            "mole_fractions",
            "measurement_id",
            "source_doi",
        }
        for row in rows:
            extra = {k: v for k, v in row.items() if k not in reserved}
            yield MeasurementView(
                document_index=document_index,
                fluid_index=fluid_index,
                measurement_id=row.get("measurement_id"),
                source_doi=row.get("source_doi"),
                property_type=row.get("property_type"),
                property_value=row.get("property_value"),
                temperature=row.get("temperature"),
                mole_fractions=list(row.get("mole_fractions") or []),
                fluid_compounds=list(row.get("fluid_compounds") or []),
                uncertainty=row.get("uncertainty"),
                extra_parameters=extra,
            )


def iter_measurement_views_from_documents(
    docs: Union[FAIRFluidsDocument, Sequence[FAIRFluidsDocument]],
    *,
    property_types: Optional[Sequence[str]] = None,
    fluid_compounds: Optional[Union[str, Sequence[str]]] = None,
    required_compounds: Optional[Union[str, Sequence[str]]] = None,
) -> Iterator[MeasurementView]:
    """Wie :func:`iter_measurement_views`, für ein Dokument oder eine Sequenz."""
    for document_index, doc in enumerate(_normalize_document_list(docs)):
        yield from iter_measurement_views(
            doc,
            document_index=document_index,
            property_types=property_types,
            fluid_compounds=fluid_compounds,
            required_compounds=required_compounds,
        )


def list_measurement_views(
    doc: FAIRFluidsDocument,
    **kwargs: Any,
) -> list[MeasurementView]:
    """Materialisierte Liste — praktisch für kleine Datenmengen."""
    return list(iter_measurement_views(doc, **kwargs))


def list_measurement_views_from_documents(
    docs: Union[FAIRFluidsDocument, Sequence[FAIRFluidsDocument]],
    **kwargs: Any,
) -> list[MeasurementView]:
    return list(iter_measurement_views_from_documents(docs, **kwargs))


def load_documents_json(
    *paths: Union[str, Path],
    encoding: str = "utf-8",
) -> list[FAIRFluidsDocument]:
    """Lädt eine oder mehrere FAIRFluids-JSON-Dateien zu validierten Dokumenten."""
    out: list[FAIRFluidsDocument] = []
    for p in paths:
        path = Path(p)
        out.append(
            FAIRFluidsDocument.model_validate_json(path.read_text(encoding=encoding))
        )
    return out


def compound_display_names(doc: FAIRFluidsDocument) -> list[str]:
    """Anzeige-Namen der ``compound``-Einträge (``commonName`` oder ``compoundID``)."""
    labels: list[str] = []
    for c in getattr(doc, "compound", []) or []:
        name = getattr(c, "commonName", None) or getattr(c, "compoundID", None)
        labels.append(str(name) if name is not None else "?")
    return labels
