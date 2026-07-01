import marimo

__generated_with = "0.23.10"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(r"""
    # CML → FAIRFluids (interactive)

    Interactive variant of the CML tutorial, ported to the new, unified IO API.
    The workflow:

    1. **Select CML files** – scan a folder and pick files
    2. **Define components** – order = mole-fraction order in the CML
    3. **Citation** – resolve every document's citation online from its DOI, or
       (toggle off) enter a template by hand
    4. **Convert** with `fairfluids.io.from_cml(...)` – parses density, viscosity,
       electrical conductivity and water activity, converting each to SI (assumed
       input units are configurable)
    5. **Inspect, plot** and export JSON

    **New in the API:** `from_cml(...)` returns a **list** of
    `FAIRFluidsDocument` – **one document per source DOI** (each `des:DOI` measurement
    block is assigned to its publication). Measurement blocks without a usable DOI
    (`"NO"`/`"NG"`/empty) end up in a single collective document, attributed only via
    the template citation.

    **DOI resolution:** with `fetch_from_doi=True` (default) each document's
    citation block is looked up online from its DOI via **Crossref → OpenAlex →
    Semantic Scholar**, filling title/authors/journal/year/volume/pages. Anything
    you type into the template below stays authoritative; the lookup only fills the
    blanks and degrades gracefully to the template when offline.
    """)
    return


@app.cell
def _():
    import json
    from pathlib import Path

    import matplotlib.pyplot as plt
    import pandas as pd

    from fairfluids.core.lib import Citation, FAIRFluidsDocument, LitType
    from fairfluids.io import from_cml

    # Default search folder for CML files (searched recursively).
    default_cml_dir = Path("/home/sga/Code/FAIRFluids/Workflows/data/cml_xml")
    default_out_dir = (
        Path(__file__).resolve().parent / "cml_downloads" / "fairfluids_json"
    )
    return (
        Citation,
        FAIRFluidsDocument,
        LitType,
        Path,
        default_cml_dir,
        default_out_dir,
        from_cml,
        json,
        pd,
        plt,
    )


@app.cell
def _(mo):
    mo.md(r"""
    ## 1) Select CML files
    """)
    return


@app.cell
def _(default_cml_dir, mo):
    cml_dir_ui = mo.ui.text(
        value=str(default_cml_dir),
        label="CML directory (searched recursively for *.xml)",
        full_width=True,
    )
    scan_button = mo.ui.run_button(label="Scan directory")
    mo.vstack([cml_dir_ui, scan_button])
    return cml_dir_ui, scan_button


@app.cell
def _(Path, cml_dir_ui, mo, scan_button):
    cml_files: list[Path] = []

    mo.stop(
        not scan_button.value,
        mo.md("> Enter a directory and click **Scan directory**."),
    )

    _dir = Path(cml_dir_ui.value)
    mo.stop(
        not _dir.is_dir(),
        mo.md(f"**Error:** directory does not exist: `{_dir}`"),
    )

    cml_files = sorted(_dir.rglob("*.xml"), key=lambda p: str(p).lower())
    mo.stop(
        not cml_files,
        mo.md(f"> No `*.xml` files found in `{_dir}`."),
    )

    mo.md(f"**{len(cml_files)}** CML file(s) found.")
    return (cml_files,)


@app.cell
def _(cml_files, mo):
    mo.stop(not cml_files, mo.md(""))

    # Label = parent folder / file name (unique across subfolders).
    _opts = {f"{p.parent.name}/{p.name}": str(p) for p in cml_files}
    file_select_ui = mo.ui.multiselect(
        options=_opts,
        value=[next(iter(_opts))],
        label="Files to convert",
    )
    mo.vstack([mo.md("### Select files"), file_select_ui])
    return (file_select_ui,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 2) Define components

    CML files contain no substance metadata – it is provided here.
    **The order is decisive:** it corresponds to the mole-fraction order in the
    CML (component 1 = first DES component, component 2 = second DES component,
    component 3 = water). The default is the DES example ChCl / Glycerol / Water.
    """)
    return


@app.cell
def _(mo, pd):
    _default_compounds = pd.DataFrame(
        [
            {
                "commonName": "Choline chloride",
                "pubChemID": 6209,
                "standard_InChI": "InChI=1S/C5H11ClNO2/c1",
                "standard_InChI_key": "",
            },
            {
                "commonName": "Glycerol",
                "pubChemID": 753,
                "standard_InChI": "InChI=1S/C3H8O3/c1-2-3-4/h2-3H,1H3",
                "standard_InChI_key": "",
            },
            {
                "commonName": "Water",
                "pubChemID": 962,
                "standard_InChI": "InChI=1S/H2O/h1H2",
                "standard_InChI_key": "XLYOFNOQVPJJNP-UHFFFAOYSA-N",
            },
        ]
    )
    compounds_editor = mo.ui.data_editor(data=_default_compounds)
    compounds_editor
    return (compounds_editor,)


@app.cell
def _(compounds_editor, mo, pd):
    # Editor rows -> list of compound dicts (empty fields are dropped).
    _df = pd.DataFrame(compounds_editor.value)
    compounds_list: list[dict] = []
    for _rec in _df.to_dict("records"):
        _name = str(_rec.get("commonName") or "").strip()
        if not _name:
            continue
        _entry: dict = {"commonName": _name}
        _cid = _rec.get("pubChemID")
        if _cid not in (None, ""):
            try:
                _entry["pubChemID"] = int(_cid)
            except (TypeError, ValueError):
                pass
        _inchi = str(_rec.get("standard_InChI") or "").strip()
        if _inchi:
            _entry["standard_InChI"] = _inchi
        _ikey = str(_rec.get("standard_InChI_key") or "").strip()
        if _ikey:
            _entry["standard_InChI_key"] = _ikey
        compounds_list.append(_entry)

    mo.md(
        f"**{len(compounds_list)} component(s)** defined: "
        + ", ".join(f"`{c['commonName']}`" for c in compounds_list)
    )
    return (compounds_list,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 3) Citation / metadata

    Each generated document is attributed by the real DOI of its `des:DOI`
    measurement block (written into `citation.doi` and every `source_doi`).
    """)
    return


@app.cell
def _(mo):
    resolve_doi_ui = mo.ui.switch(
        value=True,
        label="Resolve citation from DOI (Crossref/OpenAlex/Semantic Scholar)",
    )
    mo.vstack(
        [
            resolve_doi_ui,
            mo.md(
                "_When **on**, every document's full citation block (title, authors, "
                "journal, year, volume, pages) is resolved online from its DOI — the "
                "manual form is hidden. Turn **off** to enter citation metadata by hand._"
            ),
        ]
    )
    return (resolve_doi_ui,)


@app.cell
def _(LitType, mo, resolve_doi_ui):
    cit_littype = mo.ui.dropdown(
        [e.value for e in LitType], value="journal", label="Type"
    )
    cit_title = mo.ui.text(label="Title", full_width=True)
    cit_pubname = mo.ui.text(label="Journal / source", full_width=True)
    cit_year = mo.ui.text(label="Year")
    cit_volume = mo.ui.text(label="Volume")
    cit_page = mo.ui.text(label="Pages")
    cit_authors = mo.ui.text_area(
        label="Authors — one per line: given name ; family name ; ORCID ; affiliation",
        placeholder="Gudrun ; Gygli ; ;",
        full_width=True,
    )

    # The UI elements are always defined (downstream cells read their values),
    # but the form is only shown when DOI resolution is off — otherwise the user
    # never has to touch it.
    _form = mo.vstack(
        [
            mo.md("**Citation template** (fills gaps; DOI is set automatically per document):"),
            mo.hstack([cit_littype, cit_year, cit_volume, cit_page], wrap=True),
            cit_title,
            cit_pubname,
            cit_authors,
        ]
    )
    mo.md("") if resolve_doi_ui.value else _form
    return (
        cit_authors,
        cit_littype,
        cit_page,
        cit_pubname,
        cit_title,
        cit_volume,
        cit_year,
    )


@app.cell
def _(
    Citation,
    FAIRFluidsDocument,
    cit_authors,
    cit_littype,
    cit_page,
    cit_pubname,
    cit_title,
    cit_volume,
    cit_year,
    mo,
    resolve_doi_ui,
):
    _fields = {
        "litType": cit_littype.value or None,
        "title": cit_title.value.strip() or None,
        "pub_name": cit_pubname.value.strip() or None,
        "publication_year": cit_year.value.strip() or None,
        "lit_volume_num": cit_volume.value.strip() or None,
        "page": cit_page.value.strip() or None,
    }
    citation = Citation(**{k: v for k, v in _fields.items() if v})

    for _line in cit_authors.value.splitlines():
        if not _line.strip():
            continue
        _parts = [p.strip() for p in _line.split(";")] + [None, None, None, None]
        citation.add_to_author(
            given_name=_parts[0] or None,
            family_name=_parts[1] or None,
            orcid=_parts[2] or None,
            affiliation=_parts[3] or None,
        )

    # Only attach as a template if something beyond the default type was entered.
    _has_content = (
        any(v for k, v in _fields.items() if k != "litType") or bool(citation.author)
    )
    citation_doc = FAIRFluidsDocument(citation=citation) if _has_content else None

    _author_str = (
        ", ".join(
            " ".join(p for p in [a.given_name, a.family_name] if p)
            for a in citation.author
        )
        or "—"
    )
    _preview = mo.md(
        f"""
        **Citation preview** {"(active)" if citation_doc else "(empty – only the DOI per block is set)"}

        - Type: `{_fields['litType']}`
        - Title: {_fields['title'] or '—'}
        - Source: {_fields['pub_name'] or '—'} {_fields['lit_volume_num'] or ''} {_fields['page'] or ''}
        - Year: {_fields['publication_year'] or '—'}
        - Authors: {_author_str}
        """
    )
    # Hidden while DOI resolution is on (the form is hidden too).
    mo.md("") if resolve_doi_ui.value else _preview
    return (citation_doc,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 4) Convert
    """)
    return


@app.cell
def _(default_out_dir, mo):
    visc_unit_ui = mo.ui.dropdown(
        options=["cP", "mPa·s", "Pa·s"],
        value="cP",
        label="Viscosity input unit",
    )
    density_unit_ui = mo.ui.dropdown(
        options=["g/cm3", "kg/m3", "g/L"],
        value="g/cm3",
        label="Density input unit",
    )
    cond_unit_ui = mo.ui.dropdown(
        options=["uS/cm", "mS/cm", "S/cm", "S/m"],
        value="uS/cm",
        label="Conductivity input unit",
    )
    pubchem_ui = mo.ui.switch(value=False, label="PubChem enrichment")
    out_dir_ui = mo.ui.text(
        value=str(default_out_dir),
        label="JSON output folder",
        full_width=True,
    )
    convert_button = mo.ui.run_button(label="Convert to FAIRFluids")
    mo.vstack(
        [
            mo.md(
                "**Input units** — CML carries no unit metadata, so assume the unit "
                "each property is stored in (converted to SI: Pa·s, kg/m³, S/m; "
                "water activity is dimensionless). Values outside a plausible range "
                "raise a warning."
            ),
            mo.hstack([visc_unit_ui, density_unit_ui, cond_unit_ui], justify="start", wrap=True),
            pubchem_ui,
            out_dir_ui,
            convert_button,
        ]
    )
    return (
        cond_unit_ui,
        convert_button,
        density_unit_ui,
        out_dir_ui,
        pubchem_ui,
        visc_unit_ui,
    )


@app.cell
def _(
    Path,
    citation_doc,
    compounds_list,
    cond_unit_ui,
    convert_button,
    density_unit_ui,
    file_select_ui,
    from_cml,
    mo,
    out_dir_ui,
    pubchem_ui,
    resolve_doi_ui,
    visc_unit_ui,
):
    mo.stop(
        not convert_button.value,
        mo.md("> Check the options and click **Convert to FAIRFluids**."),
    )

    _selected = list(file_select_ui.value) if file_select_ui.value else []
    mo.stop(not _selected, mo.md("> Select at least one file in section 1."))
    mo.stop(
        not compounds_list,
        mo.md("> Define at least one component in section 2."),
    )

    out_dir = Path(out_dir_ui.value)
    out_dir.mkdir(parents=True, exist_ok=True)

    # List of (source file, FAIRFluidsDocument) — one entry per DOI per file.
    cml_docs: list[tuple] = []
    convert_errors: dict[str, str] = {}
    saved_paths: list[Path] = []

    for _spath in _selected:
        _p = Path(_spath)
        try:
            _file_docs = from_cml(
                str(_p),
                compounds=compounds_list,
                document=citation_doc,
                viscosity_input_unit=visc_unit_ui.value,
                input_units={
                    "density": density_unit_ui.value,
                    "conductivity": cond_unit_ui.value,
                },
                fetch_from_pubchem=pubchem_ui.value,
                fetch_from_doi=resolve_doi_ui.value,
            )
        except Exception as _exc:  # noqa: BLE001
            convert_errors[_p.name] = str(_exc)
            continue

        for _doc in _file_docs:
            cml_docs.append((_p.name, _doc))
            _doi = _doc.citation.doi if _doc.citation else None
            _stem = (
                _doi.replace("/", "_").replace(".", "_") if _doi else "no_doi"
            )
            _outp = out_dir / f"{_p.stem}__{_stem}.json"
            _outp.write_text(_doc.model_dump_json(indent=2), encoding="utf-8")
            saved_paths.append(_outp)

    _err_md = "\n".join(f"- `{n}`: {m}" for n, m in convert_errors.items())
    mo.md(
        f"""
        ### Conversion complete

        - **Files:** {len(_selected)}
        - **Documents (per DOI):** {len(cml_docs)}
        - **JSON saved:** {len(saved_paths)} → `{out_dir}`
        - **Errors:** {len(convert_errors)}

        {("**Errors:**" + chr(10) + _err_md) if _err_md else ""}
        """
    )
    return (cml_docs,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 5) Inspect & plot documents
    """)
    return


@app.cell
def _(cml_docs, mo):
    mo.stop(not cml_docs, mo.md("> Convert first (section 4)."))

    doc_options = {}
    for _i, (_fname, _doc) in enumerate(cml_docs):
        _doi = (_doc.citation.doi if _doc.citation else None) or "(no DOI)"
        doc_options[f"{_i}: {_fname} | {_doi} ({len(_doc.fluid)} fluids)"] = _i

    doc_ui = mo.ui.dropdown(
        options=doc_options,
        value=next(iter(doc_options)),
        label="Document",
        full_width=True,
    )
    doc_ui
    return (doc_ui,)


@app.cell
def _(pd):
    def compound_lookup(doc) -> dict:
        lookup: dict = {}
        for compound in doc.compound:
            for key in (compound.compoundID, compound.ld_id, compound.commonName):
                if key:
                    lookup[key] = compound
        return lookup

    def fluid_compound_names(doc, fluid) -> str:
        lookup = compound_lookup(doc)
        names = []
        for ref in fluid.compounds:
            compound = lookup.get(ref)
            names.append(
                compound.commonName if (compound and compound.commonName) else ref
            )
        return ", ".join(names)

    def fluid_to_dataframe(fluid) -> "pd.DataFrame":
        prop_enum_by_id = {
            p.propertyID: (
                p.properties.value if p.properties is not None else p.propertyID
            )
            for p in fluid.property
        }
        param_enum_by_id = {
            p.parameterID: (
                p.parameters.value if p.parameters is not None else p.parameterID
            )
            for p in fluid.parameter
        }

        rows = []
        for meas in (fluid.sample.measurement if fluid.sample else []):
            row = {
                "measurement_id": meas.measurement_id,
                "source_doi": meas.source_doi,
                "method": meas.method.value if meas.method else None,
            }
            for pv in meas.propertyValue:
                key = prop_enum_by_id.get(pv.propertyID, pv.propertyID)
                row[f"prop_{key}"] = pv.propValue
                if pv.uncertainty is not None:
                    row[f"prop_{key}_unc"] = pv.uncertainty
            for par in meas.parameterValue:
                key = param_enum_by_id.get(par.parameterID, par.parameterID)
                row[f"param_{key}"] = par.paramValue
            rows.append(row)
        return pd.DataFrame(rows)

    return fluid_compound_names, fluid_to_dataframe


@app.cell
def _(cml_docs, doc_ui, fluid_compound_names, mo):
    selected_doc = cml_docs[doc_ui.value][1]
    mo.stop(not selected_doc.fluid, mo.md("> This document contains no fluids."))

    fluid_ui = mo.ui.dropdown(
        options={
            f"Fluid {i}: {fluid_compound_names(selected_doc, f)}": i
            for i, f in enumerate(selected_doc.fluid)
        },
        value=f"Fluid 0: {fluid_compound_names(selected_doc, selected_doc.fluid[0])}",
        label="Fluid",
        full_width=True,
    )
    fluid_ui
    return fluid_ui, selected_doc


@app.cell
def _(fluid_compound_names, fluid_to_dataframe, fluid_ui, mo, selected_doc):
    fluid0 = selected_doc.fluid[fluid_ui.value]
    df0 = fluid_to_dataframe(fluid0)

    mo.vstack(
        [
            mo.md(
                f"**Components:** {fluid_compound_names(selected_doc, fluid0)} "
                f"— {len(df0)} measurements"
            ),
            mo.ui.table(df0, selection=None),
        ]
    )
    return (df0,)


@app.cell
def _(df0, mo):
    prop_cols = [
        c for c in df0.columns if c.startswith("prop_") and not c.endswith("_unc")
    ]
    param_cols = [c for c in df0.columns if c.startswith("param_")]

    x_ui = mo.ui.dropdown(
        options=param_cols or ["—"],
        value=param_cols[0] if param_cols else "—",
        label="X axis",
    )
    y_ui = mo.ui.dropdown(
        options=prop_cols or ["—"],
        value=prop_cols[0] if prop_cols else "—",
        label="Y axis",
    )
    arrhenius_ui = mo.ui.switch(value=False, label="Arrhenius: ln(Y) vs 1/X")
    mo.hstack([x_ui, y_ui, arrhenius_ui], justify="start", wrap=True)
    return arrhenius_ui, x_ui, y_ui


@app.cell
def _(arrhenius_ui, df0, mo, plt, x_ui, y_ui):
    import numpy as np

    mo.stop(
        not x_ui.value or not y_ui.value or x_ui.value == "—" or y_ui.value == "—",
        mo.md("> No plottable property/parameter columns present."),
    )

    _plot_df = df0[[x_ui.value, y_ui.value]].dropna()
    mo.stop(_plot_df.empty, mo.md("> No valid data points for the chosen axes."))

    fig, ax = plt.subplots(figsize=(9, 5.5))
    _x, _y = _plot_df[x_ui.value], _plot_df[y_ui.value]
    if arrhenius_ui.value:
        _mask = (_x > 0) & (_y > 0)
        _x, _y = 1.0 / _x[_mask], np.log(_y[_mask])
        ax.set_xlabel(f"1 / {x_ui.value}")
        ax.set_ylabel(f"ln({y_ui.value})")
        ax.set_title(f"ln({y_ui.value}) vs 1/{x_ui.value}")
    else:
        ax.set_xlabel(x_ui.value)
        ax.set_ylabel(y_ui.value)
        ax.set_title(f"{y_ui.value} vs {x_ui.value}")
    ax.scatter(_x, _y, alpha=0.7)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    ax
    return


if __name__ == "__main__":
    app.run()
