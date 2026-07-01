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
    # Spreadsheet → FAIRFluids (interactive)

    Interactive variant of the CSV/XLSX tutorial. The workflow:

    1. **Create template** – parser-compatible `csv`/`xlsx` via `create_datasheet(...)`
    2. **Fill the spreadsheet** (outside the notebook) and select it here
    3. **Import** with `data_from_spreadsheet(...)` including global units
    4. **PubChem enrichment** and **DOI citation resolution** (optional)
    5. **Validate, inspect, plot** and export JSON

    One document is produced **per `source_doi`** in the spreadsheet. With DOI
    resolution on (default), each document's citation block is looked up online
    from its own DOI via **Crossref → OpenAlex → Semantic Scholar**, so you rarely
    need to type citation metadata by hand.

    Every cell reacts automatically to changes of the controls. Compute-intensive
    steps (template creation, import with PubChem / DOI lookup) are guarded behind
    buttons.
    """)
    return


@app.cell
def _():
    from pathlib import Path
    import json
    import os

    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt

    from fairfluids.io import FluidIO
    from fairfluids.core.lib import FAIRFluidsDocument, Properties, Parameters
    from fairfluids.operations import calculate_ratio_of_solvent

    fio = FluidIO()

    # Working directory for templates / spreadsheets
    workflows_dir = Path("/home/sga/Code/FAIRFluids/transition_water/xslx")
    workflows_dir.mkdir(parents=True, exist_ok=True)
    return Path, fio, np, os, pd, plt, workflows_dir


@app.cell
def _(fio, mo):
    prop_keywords = fio.get_parsable_property_keywords()
    param_keywords = fio.get_parsable_parameter_keywords()

    mo.md(
        f"""
        ### Parser keywords

        **Properties:** {", ".join(f"`{k}`" for k in prop_keywords)}

        **Parameters:** {", ".join(f"`{k}`" for k in param_keywords)}
        """
    )
    return (prop_keywords,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 1) Create template
    """)
    return


@app.cell
def _(mo, prop_keywords):
    properties_ui = mo.ui.multiselect(
        options=sorted(set(prop_keywords)),
        value=["density"],
        label="Properties",
    )
    n_compounds_ui = mo.ui.slider(1, 5, value=3, label="Number of components")
    n_rows_ui = mo.ui.number(1, 1000, value=30, label="Number of data rows")
    file_format_ui = mo.ui.dropdown(["xlsx", "csv"], value="xlsx", label="Format")
    template_name_ui = mo.ui.text(value="my_template", label="File name (without extension)")
    create_button = mo.ui.run_button(label="Create template")

    mo.vstack(
        [
            mo.hstack([properties_ui, file_format_ui], justify="start"),
            mo.hstack([n_compounds_ui, n_rows_ui], justify="start"),
            mo.hstack([template_name_ui, create_button], justify="start"),
        ]
    )
    return (
        create_button,
        file_format_ui,
        n_compounds_ui,
        n_rows_ui,
        properties_ui,
        template_name_ui,
    )


@app.cell
def _(
    create_button,
    file_format_ui,
    fio,
    mo,
    n_compounds_ui,
    n_rows_ui,
    properties_ui,
    template_name_ui,
    workflows_dir,
):
    mo.stop(
        not create_button.value,
        mo.md("> Set the controls and click **Create template**."),
    )

    template_path = workflows_dir / f"{template_name_ui.value}.{file_format_ui.value}"
    written = fio.create_datasheet(
        output_path=str(template_path),
        file_format=file_format_ui.value,
        properties=list(properties_ui.value),
        n_compounds=n_compounds_ui.value,
        n_rows=n_rows_ui.value,
    )

    mo.md(
        f"""
        Template written:

        ```
        {written}
        ```

        Now fill it in the spreadsheet and select it below for import.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 1b) Fill a template from unstructured data via LLM

    Unstructured tables from a paper (copy-paste **or** screenshot) are translated by an
    LLM into the parser-compatible template schema. The model acts purely as a
    **format translator**: it invents nothing, leaves unknowns as `null`, and reports
    ambiguities as *open questions*. Afterwards, correct in the form, edit in the table,
    and save as a template.
    """)
    return


@app.cell
def _(mo, os):
    # Persistent storage for the extraction result. Without state the result
    # would be lost as soon as the LLM cell re-runs without another button click
    # (run_button.value falls back to False after one cycle), which would collapse
    # the form back to the placeholder.
    get_extraction, set_extraction = mo.state(None)

    _env_present = bool(os.environ.get("ANTHROPIC_API_KEY"))
    api_key_ui = mo.ui.text(
        label="ANTHROPIC_API_KEY (leave empty if set as environment variable)",
        kind="password",
        full_width=True,
    )
    llm_text_ui = mo.ui.text_area(
        label="Paste table as text (copy-paste from PDF/Excel)",
        placeholder="T/K   x_ChCl   x_Gly   density / g·cm-3\n298.15  0.33  0.67  1.187 ...",
        full_width=True,
    )
    llm_image_ui = mo.ui.file(
        filetypes=[".png", ".jpg", ".jpeg"],
        kind="button",
        label="… or upload a screenshot of the table",
    )
    extract_button = mo.ui.run_button(label="Extract with LLM")
    llm_save_template_button = mo.ui.run_button(label="Save as template")

    mo.vstack(
        [
            mo.md(
                "**API key:** "
                + (
                    "found in environment ✓"
                    if _env_present
                    else "not in environment – please enter below"
                )
            ),
            api_key_ui,
            llm_text_ui,
            mo.hstack([llm_image_ui, extract_button], justify="start"),
        ]
    )
    return (
        api_key_ui,
        extract_button,
        get_extraction,
        llm_image_ui,
        llm_save_template_button,
        llm_text_ui,
        set_extraction,
    )


@app.cell
def _(
    api_key_ui,
    extract_button,
    fio,
    llm_image_ui,
    llm_text_ui,
    mo,
    os,
    set_extraction,
):
    import base64 as _base64
    import anthropic as _anthropic

    _msg = mo.md(
        "> Paste text or upload a screenshot, then click **Extract with LLM**."
    )

    if extract_button.value:
        _key = api_key_ui.value.strip() or os.environ.get("ANTHROPIC_API_KEY", "")
        _has_text = bool(llm_text_ui.value.strip())
        _has_img = bool(llm_image_ui.value)
        if not _key:
            _msg = mo.md(
                "> **No API key.** Enter it in the password field or set `ANTHROPIC_API_KEY`."
            )
        elif not (_has_text or _has_img):
            _msg = mo.md("> **No input.** Paste text or upload a screenshot.")
        else:
            _prop_kw = sorted(set(fio.get_parsable_property_keywords().keys()))
            _param_kw = sorted(
                set(fio.get_parsable_parameter_keywords().keys())
                - {"temperature", "pressure"}
            )
            _schema = {
                "type": "object",
                "properties": {
                    "components": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": ["string", "null"]},
                                "confidence": {
                                    "type": "string",
                                    "enum": ["high", "medium", "low"],
                                },
                            },
                            "required": ["name", "confidence"],
                        },
                    },
                    "property_keywords": {"type": "array", "items": {"type": "string"}},
                    "extra_parameter_keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "detected_units": {
                        "type": "object",
                        "additionalProperties": {"type": ["string", "null"]},
                    },
                    "rows": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "mole_fractions": {
                                    "type": "array",
                                    "items": {"type": ["number", "null"]},
                                },
                                "temperature_value": {"type": ["number", "null"]},
                                "pressure_value": {"type": ["number", "null"]},
                                "property_values": {
                                    "type": "object",
                                    "additionalProperties": {"type": ["number", "null"]},
                                },
                                "extra_parameter_values": {
                                    "type": "object",
                                    "additionalProperties": {"type": ["number", "null"]},
                                },
                                "comment": {"type": ["string", "null"]},
                            },
                            "required": [
                                "mole_fractions",
                                "temperature_value",
                                "pressure_value",
                                "property_values",
                                "extra_parameter_values",
                            ],
                        },
                    },
                    "open_questions": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "components",
                    "property_keywords",
                    "extra_parameter_keywords",
                    "detected_units",
                    "rows",
                    "open_questions",
                ],
            }
            _instruction = (
                "Extract the tabular measurement data into the record_extraction tool. "
                "Rules: (1) Act ONLY as a format translator. Never invent or guess numbers, "
                "component names, or units not present in the source. Use null for anything "
                "missing or unreadable. (2) `components` lists the chemical components in a "
                "fixed order; every row's `mole_fractions` array MUST follow that same order. "
                f"(3) Use ONLY these property keywords as keys in property_values: {_prop_kw}. "
                f"(4) Use ONLY these extra parameter keywords in extra_parameter_values: {_param_kw} "
                "(temperature and pressure have their own dedicated fields — never duplicate them). "
                "(5) `detected_units` maps a quantity name (temperature, pressure, or a property "
                "keyword) to the unit string exactly as written in the source, or null. "
                "(6) If anything is ambiguous — e.g. the table does not say which component a "
                "mole-fraction column refers to — DO NOT assume: add a specific question to "
                "`open_questions` and set the affected fields to null."
            )
            _system = (
                "You are a precise scientific-data extraction tool. You convert messy, "
                "copy-pasted or screenshotted physico-chemical data tables into a strict "
                "structured form. You never fabricate data; when unsure you leave fields null "
                "and raise questions."
            )
            _content = []
            if _has_img:
                _f = llm_image_ui.value[0]
                _b64 = _base64.standard_b64encode(_f.contents).decode()
                _media = (
                    "image/png" if _f.name.lower().endswith("png") else "image/jpeg"
                )
                _content.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": _media,
                            "data": _b64,
                        },
                    }
                )
            if _has_text:
                _content.append(
                    {
                        "type": "text",
                        "text": "Source table (verbatim):\n" + llm_text_ui.value.strip(),
                    }
                )
            _content.append({"type": "text", "text": _instruction})
            try:
                _client = _anthropic.Anthropic(api_key=_key)
                _resp = _client.messages.create(
                    model="claude-opus-4-7",
                    max_tokens=8192,
                    system=_system,
                    tools=[
                        {
                            "name": "record_extraction",
                            "description": "Record the structured data extracted from the source table.",
                            "input_schema": _schema,
                        }
                    ],
                    tool_choice={"type": "tool", "name": "record_extraction"},
                    messages=[{"role": "user", "content": _content}],
                )
                _tool = next(
                    (b for b in _resp.content if b.type == "tool_use"), None
                )
                _extraction = _tool.input if _tool is not None else None
                if _extraction is None:
                    _msg = mo.md("> The LLM did not return a structured response.")
                else:
                    set_extraction(_extraction)
                    _nrows = len(_extraction.get("rows") or [])
                    _nq = len(_extraction.get("open_questions") or [])
                    _msg = mo.md(
                        f"**Extraction complete** — {_nrows} rows, {_nq} open question(s). "
                        "Review in the form below."
                    )
            except Exception as _e:
                _msg = mo.md(f"> **Error during LLM call:** `{_e}`")
    _msg
    return


@app.cell
def _(fio, get_extraction, mo):
    _extraction = get_extraction()
    mo.stop(
        _extraction is None,
        mo.md("_No extraction yet – run **Extract with LLM** above._"),
    )

    _comp = _extraction.get("components") or []
    _names = "\n".join((c.get("name") or "") for c in _comp)
    llm_components_ui = mo.ui.text_area(
        value=_names,
        label="Components (one per line; order = mole-fraction order)",
        full_width=True,
    )

    _allprop = sorted(set(fio.get_parsable_property_keywords().keys()))
    _detprop = [p for p in (_extraction.get("property_keywords") or []) if p in _allprop]
    llm_props_ui = mo.ui.multiselect(options=_allprop, value=_detprop, label="Properties")

    _allparam = sorted(
        set(fio.get_parsable_parameter_keywords().keys()) - {"temperature", "pressure"}
    )
    _detparam = [
        p for p in (_extraction.get("extra_parameter_keywords") or []) if p in _allparam
    ]
    llm_params_ui = mo.ui.multiselect(
        options=_allparam, value=_detparam, label="Additional parameters"
    )

    _du = _extraction.get("detected_units") or {}
    u_temp = mo.ui.text(value=_du.get("temperature") or "K", label="Temperature unit")
    u_press = mo.ui.text(value=_du.get("pressure") or "Pa", label="Pressure unit")
    u_density = mo.ui.text(value=_du.get("density") or "g/cm3", label="density unit")
    u_visc = mo.ui.text(value=_du.get("viscosity") or "mPa.s", label="viscosity unit")
    u_cond = mo.ui.text(
        value=_du.get("conductivity") or _du.get("electrical_conductivity") or "mS/cm",
        label="conductivity unit",
    )
    llm_template_name_ui = mo.ui.text(
        value="llm_filled", label="Template file name (without extension)"
    )

    _oq = _extraction.get("open_questions") or []
    _oq_md = "\n".join(f"- {q}" for q in _oq) if _oq else "_none_"
    _lowconf = [
        c.get("name") or "(unbenannt)"
        for c in _comp
        if c.get("confidence") in {"low", "medium"}
    ]
    _conf_md = (
        f"\n\n**Uncertain components:** {', '.join(_lowconf)} — please check."
        if _lowconf
        else ""
    )
    mo.vstack(
        [
            mo.md("### Clarification form"),
            mo.md(f"**Open questions from the model:**\n\n{_oq_md}{_conf_md}"),
            llm_components_ui,
            mo.hstack([llm_props_ui, llm_params_ui], justify="start", wrap=True),
            mo.hstack(
                [u_temp, u_press, u_density, u_visc, u_cond],
                justify="start",
                wrap=True,
            ),
            llm_template_name_ui,
        ]
    )
    return (
        llm_components_ui,
        llm_params_ui,
        llm_props_ui,
        llm_template_name_ui,
        u_cond,
        u_density,
        u_press,
        u_temp,
        u_visc,
    )


@app.cell
def _(
    get_extraction,
    llm_components_ui,
    llm_params_ui,
    llm_props_ui,
    mo,
    pd,
    u_cond,
    u_density,
    u_press,
    u_temp,
    u_visc,
):
    _extraction = get_extraction()
    mo.stop(_extraction is None, mo.md(""))

    _names = [n.strip() for n in llm_components_ui.value.splitlines() if n.strip()]
    _props = list(llm_props_ui.value)
    _params = list(llm_params_ui.value)
    _punits = {
        "density": u_density.value,
        "viscosity": u_visc.value,
        "conductivity": u_cond.value,
        "electrical_conductivity": u_cond.value,
        "thermal_conductivity": "W/m/K",
    }

    _cols = []
    for _i in range(len(_names)):
        _cols += [f"Compound {_i + 1}", f"pubchemID {_i + 1}", f"Molar Fraction {_i + 1}"]
    _cols += [
        "temperature_value",
        "temperature_unit",
        "temperature_uncertainty",
        "temperature_uncertainty_unit",
        "pressure_value",
        "pressure_unit",
        "pressure_uncertainty",
        "pressure_uncertainty_unit",
    ]
    for _p in _params:
        _cols += [f"{_p}_value", f"{_p}_unit", f"{_p}_uncertainty", f"{_p}_uncertainty_unit"]
    for _p in _props:
        _cols += [f"{_p}_value", f"{_p}_unit", f"{_p}_uncertainty", f"{_p}_uncertainty_unit"]
    _cols += ["Storage", "Comment", "source_doi"]

    _rows_out = []
    for _r in _extraction.get("rows") or []:
        _row = {_c: "" for _c in _cols}
        _mf = _r.get("mole_fractions") or []
        for _i in range(len(_names)):
            _row[f"Compound {_i + 1}"] = _names[_i]
            _row[f"Molar Fraction {_i + 1}"] = _mf[_i] if _i < len(_mf) else None
        _row["temperature_value"] = _r.get("temperature_value")
        _row["temperature_unit"] = u_temp.value
        _row["temperature_uncertainty_unit"] = u_temp.value
        _row["pressure_value"] = _r.get("pressure_value")
        _row["pressure_unit"] = u_press.value
        _row["pressure_uncertainty_unit"] = u_press.value
        _pv = _r.get("extra_parameter_values") or {}
        for _p in _params:
            _row[f"{_p}_value"] = _pv.get(_p)
        _prv = _r.get("property_values") or {}
        for _p in _props:
            _row[f"{_p}_value"] = _prv.get(_p)
            _row[f"{_p}_unit"] = _punits.get(_p, "")
            _row[f"{_p}_uncertainty_unit"] = _punits.get(_p, "")
        _row["Comment"] = _r.get("comment") or ""
        _rows_out.append(_row)

    llm_built_df = pd.DataFrame(_rows_out, columns=_cols)
    mo.md(
        f"**Preview** — {len(llm_built_df)} rows, {len(_cols)} columns "
        f"({len(_names)} components). Editable below."
    )
    return (llm_built_df,)


@app.cell
def _(get_extraction, llm_built_df, mo):
    mo.stop(get_extraction() is None, mo.md(""))
    llm_editor = mo.ui.data_editor(data=llm_built_df)
    llm_editor
    return (llm_editor,)


@app.cell
def _(
    get_extraction,
    llm_editor,
    llm_save_template_button,
    llm_template_name_ui,
    mo,
    pd,
    workflows_dir,
):
    _extraction = get_extraction()
    llm_saved_path = None
    if _extraction is None:
        _out = mo.md("")
    elif not llm_save_template_button.value:
        _out = mo.vstack(
            [
                llm_save_template_button,
                mo.md(
                    "> Review/edit the table above, then click **Save as template**."
                ),
            ]
        )
    else:
        _df = pd.DataFrame(llm_editor.value)
        _errors = []

        _comp_cols = [c for c in _df.columns if c.startswith("Compound ")]
        _mf_cols = [c for c in _df.columns if c.startswith("Molar Fraction ")]
        _val_cols = [c for c in _df.columns if c.endswith("_value")]
        _prop_param_val_cols = [
            c for c in _val_cols if c not in {"temperature_value", "pressure_value"}
        ]

        if not _comp_cols:
            _errors.append("No component columns present.")
        else:
            for _c in _comp_cols:
                if _df[_c].astype(str).str.strip().eq("").any():
                    _errors.append(f"Empty cell in component column `{_c}`.")
                    break

        if not _mf_cols:
            _errors.append("No mole-fraction columns present.")
        elif not any(
            pd.to_numeric(_df[_c], errors="coerce").notna().any() for _c in _mf_cols
        ):
            _errors.append("No numeric mole fractions found.")

        if not _prop_param_val_cols:
            _errors.append("No property/parameter column present.")
        elif not any(
            pd.to_numeric(_df[_c], errors="coerce").notna().any()
            for _c in _prop_param_val_cols
        ):
            _errors.append("No numeric measurement values (property/parameter) found.")

        for _c in _val_cols + _mf_cols:
            _coerced = pd.to_numeric(_df[_c], errors="coerce")
            _bad = _df[_c].astype(str).str.strip().ne("") & _coerced.isna()
            if _bad.any():
                _errors.append(f"Non-numeric values in `{_c}` (row(s) {list(_df.index[_bad])}).")

        if _errors:
            _out = mo.vstack(
                [
                    llm_save_template_button,
                    mo.md(
                        "**Validation failed:**\n\n"
                        + "\n".join(f"- {e}" for e in _errors)
                    ),
                ]
            )
        else:
            _path = workflows_dir / f"{llm_template_name_ui.value}.xlsx"
            _df.to_excel(_path, index=False)
            llm_saved_path = str(_path)
            _out = mo.vstack(
                [
                    llm_save_template_button,
                    mo.md(
                        f"**Saved:** `{_path}` — available below in the spreadsheet selection."
                    ),
                ]
            )
    _out
    return (llm_saved_path,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 2) Select the filled spreadsheet
    """)
    return


@app.cell
def _(create_button, llm_saved_path, mo, workflows_dir):
    # create_button & llm_saved_path referenced so the list refreshes after
    # template creation or LLM save
    create_button
    llm_saved_path
    sheet_files = sorted(
        [p for p in workflows_dir.glob("*") if p.suffix.lower() in {".xlsx", ".csv"}],
        key=lambda p: p.name.lower(),
    )

    mo.stop(
        not sheet_files,
        mo.md(f"> No `.xlsx`/`.csv` files found in `{workflows_dir}`."),
    )

    sheet_ui = mo.ui.dropdown(
        options={p.name: str(p) for p in sheet_files},
        value=sheet_files[0].name,
        label="Spreadsheet",
    )
    sheet_ui
    return (sheet_ui,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 3) Citation / metadata, units & import
    """)
    return


@app.cell
def _(mo):
    from fairfluids.core.lib import LitType

    cit_littype = mo.ui.dropdown(
        [e.value for e in LitType], value="journal", label="Type"
    )
    cit_title = mo.ui.text(label="Title", full_width=True)
    cit_pubname = mo.ui.text(label="Journal / source", full_width=True)
    cit_doi = mo.ui.text(label="DOI")
    cit_year = mo.ui.text(label="Year")
    cit_volume = mo.ui.text(label="Volume")
    cit_page = mo.ui.text(label="Pages")
    cit_url = mo.ui.text(label="URL", full_width=True)
    cit_authors = mo.ui.text_area(
        label="Authors — one per line: given name ; family name ; ORCID ; affiliation",
        placeholder="Jane ; Doe ; 0000-0002-1825-0097 ; Uni X",
        full_width=True,
    )

    mo.vstack(
        [
            mo.md(
                "**Citation template** (fields you leave blank are filled per "
                "document from its `source_doi` when DOI resolution is on; values "
                "you enter here always win):"
            ),
            mo.hstack([cit_littype, cit_doi, cit_year, cit_volume, cit_page], wrap=True),
            cit_title,
            cit_pubname,
            cit_url,
            cit_authors,
        ]
    )
    return (
        cit_authors,
        cit_doi,
        cit_littype,
        cit_page,
        cit_pubname,
        cit_title,
        cit_url,
        cit_volume,
        cit_year,
    )


@app.cell
def _(
    cit_authors,
    cit_doi,
    cit_littype,
    cit_page,
    cit_pubname,
    cit_title,
    cit_url,
    cit_volume,
    cit_year,
    mo,
):
    from fairfluids.core.lib import Citation as _Citation
    from fairfluids.core.lib import FAIRFluidsDocument as _FAIRFluidsDocument

    _fields = {
        "litType": cit_littype.value or None,
        "title": cit_title.value.strip() or None,
        "pub_name": cit_pubname.value.strip() or None,
        "doi": cit_doi.value.strip() or None,
        "publication_year": cit_year.value.strip() or None,
        "lit_volume_num": cit_volume.value.strip() or None,
        "page": cit_page.value.strip() or None,
        "url_citation": cit_url.value.strip() or None,
    }
    citation = _Citation(**{k: v for k, v in _fields.items() if v})

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

    # Only attach if something beyond the default type was entered
    _has_content = (
        any(v for k, v in _fields.items() if k != "litType") or bool(citation.author)
    )
    citation_doc = _FAIRFluidsDocument(citation=citation) if _has_content else None

    _author_str = (
        ", ".join(
            " ".join(p for p in [a.given_name, a.family_name] if p)
            for a in citation.author
        )
        or "—"
    )
    mo.md(
        f"""
        **Citation preview** {"(active)" if citation_doc else "(empty – not attached)"}

        - Type: `{_fields['litType']}`
        - Title: {_fields['title'] or '—'}
        - Source: {_fields['pub_name'] or '—'} {_fields['lit_volume_num'] or ''} {_fields['page'] or ''}
        - DOI: {_fields['doi'] or '—'} · Year: {_fields['publication_year'] or '—'}
        - Authors: {_author_str}
        """
    )
    return (citation_doc,)


@app.cell
def _(mo):
    # Global units at read time (as in the tutorial). Freely editable.
    unit_fields = {
        "temperature": mo.ui.text(value="K", label="temperature"),
        "pressure": mo.ui.text(value="bar", label="pressure"),
        "viscosity": mo.ui.text(value="cP", label="viscosity"),
        "density": mo.ui.text(value="g/cm3", label="density"),
        "conductivity": mo.ui.text(value="mS/cm", label="conductivity"),
    }
    units_ui = mo.ui.dictionary(unit_fields)

    pubchem_ui = mo.ui.switch(value=True, label="PubChem enrichment")
    resolve_doi_ui = mo.ui.switch(
        value=True, label="Resolve citation from DOI (Crossref/OpenAlex/Semantic Scholar)"
    )
    import_button = mo.ui.run_button(label="Import")

    mo.vstack(
        [
            mo.md("**Units** (applied globally on read):"),
            mo.hstack(list(units_ui.elements.values()), justify="start", wrap=True),
            mo.hstack([pubchem_ui, resolve_doi_ui, import_button], justify="start", wrap=True),
        ]
    )
    return import_button, pubchem_ui, resolve_doi_ui, units_ui


@app.cell
def _(
    citation_doc,
    fio,
    import_button,
    mo,
    pubchem_ui,
    resolve_doi_ui,
    sheet_ui,
    units_ui,
):
    mo.stop(
        not import_button.value,
        mo.md("> Check the units and click **Import**."),
    )

    units = {k: v for k, v in units_ui.value.items() if v}

    docs = fio.data_from_spreadsheet(
        spreadsheet_path=sheet_ui.value,
        document=citation_doc,
        fetch_from_pubchem=pubchem_ui.value,
        fetch_from_doi=resolve_doi_ui.value,
        units=units,
        uncertainty_units=units,
    )

    mo.md(
        f"""
        **Import complete.**

        - Documents: `{len(docs)}`
        - Fluids in the first document: `{len(docs[0].fluid) if docs else 0}`
        """
    )
    return (docs,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 4) Validate & inspect documents
    """)
    return


@app.cell
def _(docs, mo):
    _summary_rows = []
    for _i, _d in enumerate(docs):
        _n_meas = (
            len(_d.fluid[0].sample.measurement)
            if _d.fluid and _d.fluid[0].sample and _d.fluid[0].sample.measurement
            else 0
        )
        _summary_rows.append(
            {
                "doc": _i,
                "compounds": len(_d.compound),
                "fluids": len(_d.fluid),
                "measurements (fluid 0)": _n_meas,
            }
        )

    mo.ui.table(_summary_rows, selection=None)
    return


@app.cell
def _(docs, mo):
    doc_ui = mo.ui.dropdown(
        options={f"Document {i}": i for i in range(len(docs))},
        value="Document 0",
        label="Document",
    )
    doc_ui
    return (doc_ui,)


@app.cell
def _(doc_ui, docs, mo):
    selected_doc = docs[doc_ui.value]

    fluid_ui = mo.ui.dropdown(
        options={
            f"Fluid {i}: {', '.join(f.compounds)}": i
            for i, f in enumerate(selected_doc.fluid)
        },
        value=f"Fluid 0: {', '.join(selected_doc.fluid[0].compounds)}",
        label="Fluid",
    )
    fluid_ui
    return fluid_ui, selected_doc


@app.cell
def _(pd):
    def fluid_to_dataframe(fluid) -> "pd.DataFrame":
        prop_enum_by_id = {
            p.propertyID: (p.properties.value if p.properties is not None else p.propertyID)
            for p in fluid.property
        }
        param_enum_by_id = {
            p.parameterID: (p.parameters.value if p.parameters is not None else p.parameterID)
            for p in fluid.parameter
        }

        rows = []
        for meas in fluid.sample.measurement:
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

    return (fluid_to_dataframe,)


@app.cell
def _(fluid_to_dataframe, fluid_ui, mo, selected_doc):
    fluid0 = selected_doc.fluid[fluid_ui.value]
    df0 = fluid_to_dataframe(fluid0)

    mo.vstack(
        [
            mo.md(f"**Components:** {', '.join(fluid0.compounds)} — {len(df0)} measurements"),
            mo.ui.table(df0, selection=None),
        ]
    )
    return (df0,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 5) Plot
    """)
    return


@app.cell
def _(df0, mo):
    prop_cols = [c for c in df0.columns if c.startswith("prop_") and not c.endswith("_unc")]
    param_cols = [c for c in df0.columns if c.startswith("param_")]

    x_ui = mo.ui.dropdown(
        options=param_cols,
        value=param_cols[0] if param_cols else None,
        label="X axis",
    )
    y_ui = mo.ui.dropdown(
        options=prop_cols,
        value=prop_cols[0] if prop_cols else None,
        label="Y axis",
    )
    arrhenius_ui = mo.ui.switch(value=False, label="Arrhenius: ln(Y) vs 1/X")
    all_fluids_ui = mo.ui.switch(value=False, label="Overlay all fluids of the document")

    mo.hstack([x_ui, y_ui, arrhenius_ui, all_fluids_ui], justify="start", wrap=True)
    return all_fluids_ui, arrhenius_ui, x_ui, y_ui


@app.cell
def _(
    all_fluids_ui,
    arrhenius_ui,
    fluid_to_dataframe,
    mo,
    np,
    plt,
    selected_doc,
    x_ui,
    y_ui,
):
    mo.stop(
        x_ui.value is None or y_ui.value is None,
        mo.md("> No plottable property/parameter columns present."),
    )

    _fluids = selected_doc.fluid if all_fluids_ui.value else [selected_doc.fluid[0]]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    _plotted = False
    for _i, _f in enumerate(_fluids):
        _d = fluid_to_dataframe(_f)
        if x_ui.value not in _d.columns or y_ui.value not in _d.columns:
            continue
        _x, _y = _d[x_ui.value], _d[y_ui.value]
        if arrhenius_ui.value:
            _mask = (_x > 0) & (_y > 0)
            if not _mask.any():
                continue
            _x, _y = 1.0 / _x[_mask], np.log(_y[_mask])
        _label = f"Fluid {_i}: {', '.join(_f.compounds)}" if all_fluids_ui.value else None
        ax.scatter(_x, _y, alpha=0.7, label=_label)
        _plotted = True

    if arrhenius_ui.value:
        ax.set_xlabel(f"1 / {x_ui.value}")
        ax.set_ylabel(f"ln({y_ui.value})")
        ax.set_title(f"ln({y_ui.value}) vs 1/{x_ui.value}")
    else:
        ax.set_xlabel(x_ui.value)
        ax.set_ylabel(y_ui.value)
        ax.set_title(f"{y_ui.value} vs {x_ui.value}")
    ax.grid(True, alpha=0.3)
    if all_fluids_ui.value:
        ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    fig.tight_layout()

    mo.stop(not _plotted, mo.md("> No matching data points to plot."))
    ax
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 6) Export JSON
    """)
    return


@app.cell
def _(mo, workflows_dir):
    out_dir_ui = mo.ui.text(
        value=str(workflows_dir / "outputs_from_spreadsheet"),
        label="Output folder",
        full_width=True,
    )
    save_button = mo.ui.run_button(label="Save JSON")
    mo.vstack([out_dir_ui, save_button])
    return out_dir_ui, save_button


@app.cell
def _(Path, doc_ui, docs, mo, out_dir_ui, save_button):
    mo.stop(
        not save_button.value,
        mo.md("> Set the folder and click **Save JSON**."),
    )

    out_dir = Path(out_dir_ui.value)
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = docs[doc_ui.value]
    compounds = "_".join(c.commonName or c.pubChemID or "compound" for c in doc.compound)
    out_path = out_dir / f"{compounds or 'document'}_{doc_ui.value}.json"
    out_path.write_text(doc.model_dump_json(indent=2))

    mo.md(f"Saved: `{out_path}`")
    return


if __name__ == "__main__":
    app.run()
