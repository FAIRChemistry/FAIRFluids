"""NIST ThermoML Cordra API client for search, filter, and XML download."""

from __future__ import annotations

from .client import (
    API_BASE,
    XML_BASE,
    build_lucene_query,
    compounds_of,
    doi_of,
    poms_of,
    search_all,
)
from .components import ResolvedComponent, resolve_components
from .download import DownloadResult, bundle_zip, download_xmls
from .enum_loader import get_property_options, load_enums
from .filters import FilterConfig, MixtureMode, MixtureType, apply_filters

__all__ = [
    "API_BASE",
    "XML_BASE",
    "DownloadResult",
    "FilterConfig",
    "MixtureMode",
    "MixtureType",
    "ResolvedComponent",
    "apply_filters",
    "build_lucene_query",
    "bundle_zip",
    "compounds_of",
    "doi_of",
    "download_xmls",
    "get_property_options",
    "load_enums",
    "poms_of",
    "resolve_components",
    "search_all",
]
