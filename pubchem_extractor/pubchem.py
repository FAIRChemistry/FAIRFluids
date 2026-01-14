"""
Extrahiert alle Compound-Bloecke aus den bereitgestellten ThermoML-Ordnern,
ruft falls moeglich PubChem-Daten ab und schreibt eine zusammengefasste
JSON-Liste.
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Iterable, List, Optional
from urllib.parse import quote
import xml.etree.ElementTree as ET

import requests

# Fortschrittsbalken; falls tqdm nicht installiert ist, als No-Op verwenden
try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover - Fallback fuer Umgebungen ohne tqdm

    def tqdm(iterable, **kwargs):
        return iterable


# Ordner mit den ThermoML-XML-Dateien
DEFAULT_DIRECTORIES = [
    Path("/home/sga/Downloads/ThermoML.v2020-09-30/10.1016/xml/"),
    Path("/home/sga/Downloads/ThermoML.v2020-09-30/10.1007/xml/"),
    Path("/home/sga/Downloads/ThermoML.v2020-09-30/10.1021/xml/"),
]

PUBCHEM_PROPERTIES = (
    "IUPACName,MolecularFormula,MolecularWeight,SMILES,InChI,InChIKey,Title"
)
MAX_RETRIES = 3
RETRY_DELAY = 1.0


def _safe_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _first_or_none(items: List[str]) -> Optional[str]:
    return items[0] if items else None


@dataclass
class XmlCompound:
    compound_id: Optional[str]
    pubchem_cid: Optional[int]
    common_names: List[str]
    standard_inchi: Optional[str]
    standard_inchikey: Optional[str]
    formula: Optional[str]


def _iter_xml_files(directories: Iterable[Path]) -> Iterable[Path]:
    for base in directories:
        if not base.exists():
            logging.warning("Ordner nicht gefunden: %s", base)
            continue
        yield from sorted(base.rglob("*.xml"))


def _text(elem: ET.Element, tag: str) -> Optional[str]:
    node = elem.find(f".//{{*}}{tag}")
    if node is not None and node.text:
        return node.text.strip()
    return None


def _collect_compounds_from_xml(xml_path: Path) -> List[XmlCompound]:
    compounds: List[XmlCompound] = []
    tree = ET.parse(xml_path)
    root = tree.getroot()

    for compound in root.findall(".//{*}Compound"):
        names = [
            n.text.strip()
            for n in compound.findall(".//{*}sCommonName")
            if n.text and n.text.strip()
        ]
        compounds.append(
            XmlCompound(
                compound_id=_text(compound, "nOrgNum") or _text(compound, "compoundID"),
                pubchem_cid=_safe_int(_text(compound, "nPubChemCID")),
                common_names=names,
                standard_inchi=_text(compound, "sStandardInChI"),
                standard_inchikey=_text(compound, "sStandardInChIKey"),
                formula=_text(compound, "sFormulaMolec"),
            )
        )
    return compounds


def _warn_if_mismatch(
    label: str, xml_value: Optional[str], pc_value: Optional[str], src: str
) -> bool:
    """Gibt True zurueck, falls Werte abweichen (und loggt Warnung)."""
    if xml_value and pc_value and xml_value.strip() != pc_value.strip():
        logging.warning("%s stimmt nicht ueberein (XML vs PubChem) fuer %s", label, src)
        return True
    return False


def _search_cid_by_name(compound_name: str) -> Optional[int]:
    """
    Sucht nach einem Compound-Namen in PubChem und gibt die CID zurueck.
    Verwendet den zweistufigen Ansatz: zuerst Name-Suche, dann CID-Extraktion.
    """
    encoded_name = quote(compound_name)
    search_url = (
        f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_name}/JSON"
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(search_url, timeout=30)

            if resp.status_code == 200:
                data = resp.json()
                if "PC_Compounds" in data and len(data["PC_Compounds"]) > 0:
                    cid = data["PC_Compounds"][0]["id"]["id"]["cid"]
                    return cid
                logging.warning(
                    "Keine CID in PubChem-Antwort fuer Name '%s'", compound_name
                )
                return None

            if resp.status_code in {429, 503, 502}:
                logging.warning(
                    "PubChem verweigert Zugriff (%s) Versuch %s/%s, erneut in %.1fs",
                    resp.status_code,
                    attempt,
                    MAX_RETRIES,
                    RETRY_DELAY,
                )
                time.sleep(RETRY_DELAY)
                continue

            if resp.status_code in {404, 400}:
                # 404 = nicht gefunden, 400 = ungültige Anfrage
                return None

            logging.warning(
                "PubChem Suche fehlgeschlagen (%s) fuer Name '%s': %s",
                resp.status_code,
                compound_name,
                resp.text[:200],
            )
            return None

        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES:
                logging.warning(
                    "Timeout bei PubChem-Suche fuer '%s', Versuch %s/%s",
                    compound_name,
                    attempt,
                    MAX_RETRIES,
                )
                time.sleep(RETRY_DELAY)
                continue
            return None
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES:
                logging.warning(
                    "Request-Fehler bei PubChem-Suche fuer '%s', Versuch %s/%s: %s",
                    compound_name,
                    attempt,
                    MAX_RETRIES,
                    e,
                )
                time.sleep(RETRY_DELAY)
                continue
            return None

    return None


def _fetch_properties_by_cid(cid: int) -> Optional[dict]:
    """
    Holt Compound-Properties von PubChem ueber CID.
    """
    url = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/"
        f"cid/{cid}/property/{PUBCHEM_PROPERTIES}/JSON"
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, timeout=30)

            if resp.status_code == 200:
                data = resp.json()
                props = data.get("PropertyTable", {}).get("Properties", [])
                if props:
                    prop_data = props[0]
                    # Fuege CID hinzu, falls nicht vorhanden
                    prop_data["CID"] = cid
                    return prop_data
                logging.warning("Keine Properties in PubChem-Antwort fuer CID %s", cid)
                return None

            if resp.status_code in {429, 503, 502}:
                logging.warning(
                    "PubChem verweigert Zugriff (%s) Versuch %s/%s, erneut in %.1fs",
                    resp.status_code,
                    attempt,
                    MAX_RETRIES,
                    RETRY_DELAY,
                )
                time.sleep(RETRY_DELAY)
                continue

            logging.warning(
                "PubChem Properties-Anfrage fehlgeschlagen (%s) fuer CID %s: %s",
                resp.status_code,
                cid,
                resp.text[:200],
            )
            return None

        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES:
                logging.warning(
                    "Timeout bei PubChem-Properties fuer CID %s, Versuch %s/%s",
                    cid,
                    attempt,
                    MAX_RETRIES,
                )
                time.sleep(RETRY_DELAY)
                continue
            return None
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES:
                logging.warning(
                    "Request-Fehler bei PubChem-Properties fuer CID %s, Versuch %s/%s: %s",
                    cid,
                    attempt,
                    MAX_RETRIES,
                    e,
                )
                time.sleep(RETRY_DELAY)
                continue
            return None

    return None


def _fetch_pubchem(
    pubchem_cid: Optional[int], common_names: List[str]
) -> Optional[dict]:
    """
    Holt PubChem-Daten fuer ein Compound.
    Verwendet CID falls vorhanden, sonst versucht es alle Common Names.
    """
    # Wenn CID vorhanden, direkt Properties holen
    if pubchem_cid is not None:
        return _fetch_properties_by_cid(pubchem_cid)

    # Ansonsten alle Common Names durchprobieren
    if common_names:
        for idx, name in enumerate(common_names):
            cid = _search_cid_by_name(name)
            if cid is not None:
                props = _fetch_properties_by_cid(cid)
                if props is not None:
                    return props
            logging.info(
                "Kein CID fuer CommonName '%s' (Index %s), versuche naechsten falls vorhanden",
                name,
                idx,
            )

    return None


def _build_compound_entry(
    xml_entry: XmlCompound, pubchem: Optional[dict], source_file: Path
) -> dict:
    pubchem_cid = pubchem.get("CID") if pubchem else None
    inchi = pubchem.get("InChI") if pubchem else None
    inchikey = pubchem.get("InChIKey") if pubchem else None

    mismatch_inchi = _warn_if_mismatch(
        "sStandardInChI",
        xml_entry.standard_inchi,
        inchi,
        f"{source_file} (CID {pubchem_cid or xml_entry.pubchem_cid})",
    )
    mismatch_inchikey = _warn_if_mismatch(
        "sStandardInChIKey",
        xml_entry.standard_inchikey,
        inchikey,
        f"{source_file} (CID {pubchem_cid or xml_entry.pubchem_cid})",
    )

    status = "ok"
    if pubchem is None:
        status = "none_found"
    elif mismatch_inchi or mismatch_inchikey:
        status = "inchi_mismatch"

    return {
        "compoundID": xml_entry.compound_id,
        "pubChemID": pubchem_cid or xml_entry.pubchem_cid,
        "commonName": _first_or_none(xml_entry.common_names),
        "commonNamesAll": xml_entry.common_names,
        "SELFIE": None,
        "name_IUPAC": pubchem.get("IUPACName") if pubchem else None,
        "standard_InChI": inchi or xml_entry.standard_inchi,
        "standard_InChI_key": inchikey or xml_entry.standard_inchikey,
        "molar_weigth": pubchem.get("MolecularWeight") if pubchem else None,
        "smiles_code": pubchem.get("SMILES") if pubchem else None,
        "sigma_profile": None,
        "formula": xml_entry.formula,
        "source_xml": str(source_file),
        "status": status,
    }


def process_directories(
    directories: Iterable[Path],
    stream_file: Optional[IO[str]] = None,
) -> list[dict]:
    compounds: list[dict] = []

    xml_files = list(_iter_xml_files(directories))
    for xml_file in tqdm(xml_files, desc="XML-Dateien", unit="file"):
        try:
            xml_compounds = _collect_compounds_from_xml(xml_file)
        except Exception as exc:  # pragma: no cover - defensiv fuer kaputte XML
            logging.exception("Kann Datei %s nicht parsen: %s", xml_file, exc)
            continue

        for xml_entry in tqdm(
            xml_compounds,
            desc=f"Compounds in {xml_file.name}",
            leave=False,
            unit="cmpd",
        ):
            pubchem_data = _fetch_pubchem(xml_entry.pubchem_cid, xml_entry.common_names)
            entry = _build_compound_entry(xml_entry, pubchem_data, xml_file)
            compounds.append(entry)

            if stream_file is not None:
                stream_file.write(json.dumps(entry) + "\n")
                stream_file.flush()

    return compounds


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Erzeuge eine JSON-Liste aller Molekuele aus ThermoML-Dateien und ergaenze PubChem-Daten."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("compound_list.json"),
        help="Pfad fuer die ausgegebene JSON-Datei",
    )
    parser.add_argument(
        "-s",
        "--stream-output",
        type=Path,
        default=None,
        help="Pfad fuer NDJSON-Streaming-Ausgabe (fortlaufend beschreibbar). Standard: <output>.ndjson",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        nargs="*",
        default=DEFAULT_DIRECTORIES,
        help="Ordner mit ThermoML-XML-Dateien",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Ausfuehrliche Logausgabe aktivieren",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    stream_path = (
        args.stream_output
        if args.stream_output is not None
        else args.output.with_suffix(".ndjson")
    )

    with stream_path.open("w", encoding="utf-8") as stream_file:
        compounds = process_directories(args.input, stream_file=stream_file)

    args.output.write_text(json.dumps(compounds, indent=2), encoding="utf-8")
    logging.info(
        "Fertig: %s Eintraege in %s (Streaming-Datei: %s)",
        len(compounds),
        args.output,
        stream_path,
    )


if __name__ == "__main__":
    main()
