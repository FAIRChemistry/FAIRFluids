"""Download ThermoML XML files from the NIST web archive."""

from __future__ import annotations

import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

from .client import DEFAULT_DELAY_SEC, DEFAULT_TIMEOUT, USER_AGENT, XML_BASE, doi_of


@dataclass
class DownloadResult:
    saved: int = 0
    skipped: int = 0
    miss: int = 0
    errors: int = 0
    files: list[Path] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


def download_xmls(
    selected: list[dict[str, Any]],
    outdir: Path,
    *,
    skip_existing: bool = True,
    delay_sec: float = DEFAULT_DELAY_SEC,
    timeout: int = DEFAULT_TIMEOUT,
    session: requests.Session | None = None,
) -> DownloadResult:
    """Download XML files for filtered API hits into ``outdir``."""
    outdir.mkdir(parents=True, exist_ok=True)
    sess = session or requests.Session()
    sess.headers.setdefault("User-Agent", USER_AGENT)

    result = DownloadResult()
    for index, obj in enumerate(selected, 1):
        doi = doi_of(obj)
        if not doi:
            result.errors += 1
            result.messages.append(f"[{index}] no DOI on object, skipping")
            continue

        out_path = outdir / f"{doi.replace('/', '_')}.xml"
        if skip_existing and out_path.exists():
            result.skipped += 1
            result.files.append(out_path)
            continue

        url = f"{XML_BASE}/{doi}.xml"
        try:
            response = sess.get(url, timeout=timeout)
            if response.status_code == 200:
                out_path.write_bytes(response.content)
                result.saved += 1
                result.files.append(out_path)
                result.messages.append(
                    f"[{index}/{len(selected)}] {doi} ({len(response.content)} B)"
                )
            else:
                result.miss += 1
                result.messages.append(
                    f"[{index}/{len(selected)}] {doi} HTTP {response.status_code}"
                )
        except Exception as exc:  # noqa: BLE001 - surface per-file download errors
            result.errors += 1
            result.messages.append(f"[{index}/{len(selected)}] {doi} error: {exc}")

        time.sleep(delay_sec)

    return result


def bundle_zip(files: list[Path], zip_path: Path) -> Path:
    """Bundle downloaded XML files into a zip archive for browser download."""
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in files:
            if file_path.is_file():
                archive.write(file_path, arcname=file_path.name)
    return zip_path
