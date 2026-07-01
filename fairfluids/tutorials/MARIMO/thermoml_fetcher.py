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
    # ThermoML Fetcher

    Interactive search in the [NIST ThermoML API](https://trc.nist.gov/ThermoML-API/),
    local filtering by mixture type, properties, pressure, and temperature, followed by
    download of matching XML files.

    **App workflow**

    1. Enter components as common names, then click **Resolve via PubChem**
    2. Choose properties and filters
    3. Click **Search & download**
    4. Convert XML files to FAIRFluids documents and save as JSON (optional)
    5. Select a JSON folder, load individual files, inspect, and plot
    """)
    return


@app.cell
def _():
    import json
    from pathlib import Path

    import matplotlib.pyplot as plt
    import pandas as pd

    from fairfluids.core.lib import FAIRFluidsDocument
    from fairfluids.io.thermoml_api import (
        FilterConfig,
        MixtureMode,
        MixtureType,
        apply_filters,
        build_lucene_query,
        bundle_zip,
        download_xmls,
        get_property_options,
        resolve_components,
        search_all,
    )
    from fairfluids.io import from_thermoml

    default_outdir = Path(__file__).resolve().parent / "thermoml_downloads"
    default_ff_outdir = default_outdir / "fairfluids_json"
    property_options = get_property_options()
    return (
        FAIRFluidsDocument,
        FilterConfig,
        MixtureMode,
        MixtureType,
        Path,
        apply_filters,
        build_lucene_query,
        bundle_zip,
        default_ff_outdir,
        default_outdir,
        download_xmls,
        json,
        pd,
        plt,
        from_thermoml,
        property_options,
        resolve_components,
        search_all,
    )


@app.cell
def _(mo):
    mo.md(r"""
    ## 1) Components
    """)
    return


@app.cell
def _(mo):
    n_components_ui = mo.ui.slider(1, 5, value=2, label="Number of components")
    mixture_type_ui = mo.ui.dropdown(
        options={
            "Pure (1 component)": "pure",
            "Binary (2 components)": "binary",
            "Ternary (3 components)": "ternary",
            "Custom (count from slider)": "custom",
        },
        value="Binary (2 components)",
        label="Mixture type",
    )
    mode_ui = mo.ui.dropdown(
        options={
            "strict — exact compound list": "strict",
            "lenient — matching POM block": "lenient",
        },
        value="lenient — matching POM block",
        label="Filter mode",
    )

    mo.hstack([n_components_ui, mixture_type_ui, mode_ui], justify="start", gap=1)
    return mixture_type_ui, mode_ui, n_components_ui


@app.cell
def _(mo):
    _component_defaults = ["water", "methanol", "urea", "glycerol", "ethanol"]
    component_inputs_all = [
        mo.ui.text(
            value=_component_defaults[i],
            label=f"Component {i + 1}",
            full_width=True,
        )
        for i in range(5)
    ]
    return (component_inputs_all,)


@app.cell
def _(component_inputs_all, mo, n_components_ui):
    component_inputs = component_inputs_all[: n_components_ui.value]
    mo.vstack(component_inputs)
    return (component_inputs,)


@app.cell
def _(mo):
    resolve_components_button = mo.ui.run_button(
        label="Resolve components via PubChem",
    )
    resolve_components_button
    return (resolve_components_button,)


@app.cell
def _(component_inputs, mo, resolve_components, resolve_components_button):
    component_names = [ui.value.strip() for ui in component_inputs]
    resolved = []

    if not resolve_components_button.value:
        resolution_output = mo.md(
            "> Enter names and click **Resolve components via PubChem**."
        )
    elif not any(component_names):
        resolution_output = mo.md("> Enter at least one component.")
    else:
        resolved = resolve_components(component_names)
        if not resolved:
            resolution_output = mo.md("> Enter at least one component.")
        else:
            rows = []
            for item in resolved:
                if item.inchikey:
                    status = f"✓ `{item.inchikey}` (CID {item.pubchem_cid})"
                else:
                    status = f"⚠ {item.lookup_error or 'no InChIKey'}"
                rows.append(f"- **{item.common_name}**: {status}")
            resolution_output = mo.md(
                f"""
                ### PubChem resolution

                {chr(10).join(rows)}
                """
            )

    resolution_output
    return component_names, resolved


@app.cell
def _(mo):
    mo.md(r"""
    ## 2) Properties & state filters
    """)
    return


@app.cell
def _(mo, property_options):
    property_filter_active_ui = mo.ui.checkbox(
        value=True,
        label="Property filter enabled",
    )
    properties_ui = mo.ui.multiselect(
        options=property_options,
        value=[
            name
            for name in ("Mass density, kg/m3", "Viscosity, Pa*s")
            if name in property_options
        ],
        label="ThermoML properties (ePropName)",
    )

    pressure_active_ui = mo.ui.checkbox(value=False, label="Pressure filter enabled")
    pressure_target_ui = mo.ui.number(value=101.0, label="Target pressure (kPa)")
    pressure_tol_ui = mo.ui.number(value=2.0, label="Pressure tolerance (kPa)")

    temperature_active_ui = mo.ui.checkbox(value=False, label="Temperature filter enabled")
    temperature_target_ui = mo.ui.number(value=298.15, label="Target temperature (K)")
    temperature_tol_ui = mo.ui.number(value=1.0, label="Temperature tolerance (K)")

    mo.vstack(
        [
            mo.hstack([property_filter_active_ui, properties_ui], justify="start", gap=1),
            mo.hstack(
                [pressure_active_ui, pressure_target_ui, pressure_tol_ui],
                justify="start",
                gap=1,
            ),
            mo.hstack(
                [
                    temperature_active_ui,
                    temperature_target_ui,
                    temperature_tol_ui,
                ],
                justify="start",
                gap=1,
            ),
        ]
    )
    return (
        pressure_active_ui,
        pressure_target_ui,
        pressure_tol_ui,
        properties_ui,
        property_filter_active_ui,
        temperature_active_ui,
        temperature_target_ui,
        temperature_tol_ui,
    )


@app.cell
def _(mo):
    mo.md(r"""
    ## 3) Download
    """)
    return


@app.cell
def _(default_outdir, mo):
    outdir_ui = mo.ui.text(
        value=str(default_outdir),
        label="Output directory",
        full_width=True,
    )
    download_button = mo.ui.run_button(label="Search & download")
    mo.vstack([outdir_ui, download_button])
    return download_button, outdir_ui


@app.cell
def _(
    FilterConfig,
    MixtureMode,
    MixtureType,
    Path,
    apply_filters,
    build_lucene_query,
    bundle_zip,
    component_names,
    download_button,
    download_xmls,
    mixture_type_ui,
    mode_ui,
    mo,
    n_components_ui,
    outdir_ui,
    pressure_active_ui,
    pressure_target_ui,
    pressure_tol_ui,
    properties_ui,
    property_filter_active_ui,
    resolved,
    search_all,
    temperature_active_ui,
    temperature_target_ui,
    temperature_tol_ui,
):
    mo.stop(
        not download_button.value,
        mo.md("> Configure filters and click **Search & download**."),
    )

    names_for_query = [name for name in component_names if name]
    if not names_for_query:
        mo.stop(mo.md("**Error:** Enter at least one component."))

    if not resolved:
        mo.stop(
            mo.md(
                "**Error:** In section 1, click **Resolve components via PubChem** first."
            )
        )

    query = build_lucene_query(names_for_query)
    hits = search_all(query)

    filter_config = FilterConfig(
        components=resolved,
        mixture_type=MixtureType(mixture_type_ui.value),
        custom_component_count=n_components_ui.value,
        mode=MixtureMode(mode_ui.value),
        property_names=list(properties_ui.value),
        require_properties=property_filter_active_ui.value
        and bool(properties_ui.value),
        target_pressure_kpa=pressure_target_ui.value
        if pressure_active_ui.value
        else None,
        pressure_tolerance_kpa=float(pressure_tol_ui.value),
        target_temperature_k=temperature_target_ui.value
        if temperature_active_ui.value
        else None,
        temperature_tolerance_k=float(temperature_tol_ui.value),
    )
    selected = apply_filters(hits, filter_config)

    outdir = Path(outdir_ui.value)
    download_result = download_xmls(selected, outdir)

    zip_path = None
    if download_result.files:
        zip_path = bundle_zip(
            download_result.files,
            outdir / "thermoml_download.zip",
        )

    summary_lines = [
        f"- **API hits:** {len(hits)}",
        f"- **After filter:** {len(selected)}",
        f"- **Saved:** {download_result.saved}",
        f"- **Skipped (existing):** {download_result.skipped}",
        f"- **HTTP errors:** {download_result.miss}",
        f"- **Other errors:** {download_result.errors}",
        f"- **Output directory:** `{outdir}`",
    ]
    if zip_path is not None:
        summary_lines.append(f"- **ZIP:** `{zip_path}`")

    doi_rows = "\n".join(
        f"| {i} | `{path.stem}` |"
        for i, path in enumerate(download_result.files, 1)
    )
    log_tail = "\n".join(f"    {line}" for line in download_result.messages[-20:])

    xml_zip_download_widgets = []
    if zip_path is not None and zip_path.is_file():
        xml_zip_download_widgets.append(
            mo.download(
                data=zip_path.read_bytes(),
                filename=zip_path.name,
                label="Download ZIP",
            )
        )

    mo.vstack(
        [
            mo.md(
                f"""
                ### Result

                {chr(10).join(summary_lines)}

                | # | File |
                |---|------|
                {doi_rows or "| — | no files |"}

                <details><summary>Download log (latest entries)</summary>

                ```
                {log_tail or "(empty)"}
                ```

                </details>
                """
            ),
            *xml_zip_download_widgets,
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---

    ## 4) FAIRFluids conversion

    ThermoML XML files from the download folder are converted to `FAIRFluidsDocument`
    JSON using the unified `fairfluids.io.from_thermoml` entry point, which returns a
    list of documents (one per source DOI; ThermoML carries a single citation, so the
    list has exactly one element).
    """)
    return


@app.cell
def _(default_ff_outdir, mo, outdir_ui):
    xml_dir_ui = mo.ui.text(
        value=str(outdir_ui.value),
        label="XML input directory",
        full_width=True,
    )
    ff_outdir_ui = mo.ui.text(
        value=str(default_ff_outdir),
        label="JSON output directory",
        full_width=True,
    )
    fetch_pubchem_ui = mo.ui.checkbox(
        value=True,
        label="PubChem enrichment during conversion",
    )
    convert_button = mo.ui.run_button(label="Convert to FAIRFluids")
    mo.vstack([xml_dir_ui, ff_outdir_ui, fetch_pubchem_ui, convert_button])
    return convert_button, fetch_pubchem_ui, ff_outdir_ui, xml_dir_ui


@app.cell
def _(
    FAIRFluidsDocument,
    Path,
    convert_button,
    fetch_pubchem_ui,
    ff_outdir_ui,
    from_thermoml,
    mo,
    xml_dir_ui,
):
    converted_docs: dict[str, FAIRFluidsDocument] = {}
    conversion_errors: dict[str, str] = {}
    saved_json_paths: list[Path] = []

    if not convert_button.value:
        mo.output.replace(
            mo.md("> Choose an XML folder and click **Convert to FAIRFluids**.")
        )
    else:
        xml_dir = Path(xml_dir_ui.value)
        ff_outdir = Path(ff_outdir_ui.value)
        ff_outdir.mkdir(parents=True, exist_ok=True)

        if not xml_dir.is_dir():
            mo.output.replace(
                mo.md(f"**Error:** XML directory does not exist: `{xml_dir}`")
            )
        else:
            xml_files = sorted(xml_dir.glob("*.xml"))
            if not xml_files:
                mo.output.replace(
                    mo.md(f"**No XML files** found in `{xml_dir}`.")
                )
            else:
                for xml_path in xml_files:
                    try:
                        # from_thermoml returns a list (one document per source
                        # DOI); a ThermoML file carries a single citation, so the
                        # list has exactly one element.
                        _ff_document = from_thermoml(
                            xml_path,
                            fetch_from_pubchem=fetch_pubchem_ui.value,
                        )[0]
                        converted_docs[xml_path.name] = _ff_document
                        out_path = ff_outdir / f"{xml_path.stem}.json"
                        out_path.write_text(
                            _ff_document.model_dump_json(indent=2), encoding="utf-8"
                        )
                        saved_json_paths.append(out_path)
                    except Exception as exc:  # noqa: BLE001
                        conversion_errors[xml_path.name] = str(exc)

                converted_names = sorted(converted_docs)
                error_rows = "\n".join(
                    f"- `{name}`: {msg}" for name, msg in conversion_errors.items()
                )

                mo.output.replace(
                    mo.md(
                        f"""
                        ### Conversion complete

                        - **XML files:** {len(xml_files)}
                        - **Successful:** {len(converted_docs)}
                        - **Errors:** {len(conversion_errors)}
                        - **JSON output:** `{ff_outdir}`

                        {f"Converted files ({len(converted_names)}):" if converted_names else ""}
                        {chr(10).join(f"- `{name}`" for name in converted_names) or "_No successful conversions._"}

                        {"**Errors:**" + chr(10) + error_rows if error_rows else ""}

                        > JSON files are in `{ff_outdir}` — scan the folder in **section 5**.
                        """
                    )
                )

    return conversion_errors, converted_docs, saved_json_paths


@app.cell
def _(mo):
    mo.md(r"""
    ## 5) Inspect documents

    Choose a JSON folder with FAIRFluids documents, load a single file, and visualize.
    Independent of section 4 — e.g. previously converted files in `fairfluids_json12`.
    """)
    return


@app.cell
def _(default_ff_outdir, mo):
    inspect_json_dir_ui = mo.ui.text(
        value=str(default_ff_outdir),
        label="JSON directory (FAIRFluids documents)",
        full_width=True,
    )
    inspect_scan_button = mo.ui.run_button(label="Scan directory")
    mo.vstack([inspect_json_dir_ui, inspect_scan_button])
    return inspect_json_dir_ui, inspect_scan_button


@app.cell
def _(Path, inspect_json_dir_ui, inspect_scan_button, mo):
    inspect_json_files: list[Path] = []

    if not inspect_scan_button.value:
        mo.output.replace(
            mo.md("> Enter a JSON directory and click **Scan directory**.")
        )
    else:
        json_dir = Path(inspect_json_dir_ui.value)
        if not json_dir.is_dir():
            mo.output.replace(
                mo.md(f"**Error:** Directory does not exist: `{json_dir}`")
            )
        else:
            inspect_json_files = sorted(json_dir.glob("*.json"))
            if not inspect_json_files:
                mo.output.replace(
                    mo.md(f"**No JSON files** found in `{json_dir}`.")
                )
            else:
                mo.output.replace(
                    mo.md(
                        f"**{len(inspect_json_files)}** JSON files found in `{json_dir}`."
                    )
                )

    return (inspect_json_files,)


@app.cell
def _(inspect_json_files, mo):
    mo.stop(
        not inspect_json_files,
        mo.md("> Scan a JSON directory first."),
    )

    inspect_file_options = {path.name: path.name for path in inspect_json_files}
    inspect_file_ui = mo.ui.dropdown(
        options=inspect_file_options,
        value=next(iter(inspect_file_options)),
        label="JSON file",
        full_width=True,
    )
    inspect_load_button = mo.ui.run_button(label="Load selected document")
    mo.vstack(
        [
            mo.md("### Select file"),
            inspect_file_ui,
            inspect_load_button,
        ]
    )
    return inspect_file_ui, inspect_load_button


@app.cell
def _(
    FAIRFluidsDocument,
    Path,
    inspect_file_ui,
    inspect_json_dir_ui,
    inspect_json_files,
    inspect_load_button,
    mo,
):
    mo.stop(not inspect_json_files)

    inspect_selected_name = None
    inspect_selected_doc = None
    inspect_json_path = None

    if not inspect_load_button.value:
        mo.output.replace(
            mo.md("> Select a file and click **Load selected document**.")
        )
    else:
        inspect_selected_name = inspect_file_ui.value
        inspect_json_path = Path(inspect_json_dir_ui.value) / inspect_selected_name
        try:
            inspect_selected_doc = FAIRFluidsDocument.model_validate_json(
                inspect_json_path.read_text(encoding="utf-8")
            )
        except Exception as exc:  # noqa: BLE001
            mo.output.replace(
                mo.md(f"**Error loading** `{inspect_selected_name}`: {exc}")
            )
        else:
            mo.output.replace(
                mo.md(
                    f"""
                    **Loaded:** `{inspect_selected_name}`
                    — {len(inspect_selected_doc.compound)} compounds,
                    {len(inspect_selected_doc.fluid)} fluids
                    """
                )
            )

    return inspect_json_path, inspect_selected_doc, inspect_selected_name


@app.cell
def _(fluid_compound_names, inspect_load_button, inspect_selected_doc, mo):
    inspect_fluid_ui = mo.ui.dropdown(
        options={"—": 0},
        value="—",
        label="Fluid",
        full_width=True,
    )
    inspect_fluid_options: dict[str, int] = {}

    if inspect_load_button.value and inspect_selected_doc is not None:
        inspect_fluid_options = {
            f"Fluid {index}: {fluid_compound_names(inspect_selected_doc, fluid)}": index
            for index, fluid in enumerate(inspect_selected_doc.fluid)
        }
        inspect_fluid_ui = mo.ui.dropdown(
            options=inspect_fluid_options,
            value=next(iter(inspect_fluid_options)),
            label="Fluid",
            full_width=True,
        )

    inspect_fluid_ui
    return inspect_fluid_options, inspect_fluid_ui


@app.cell
def _(pd):
    def compound_lookup(doc) -> dict[str, object]:
        lookup: dict[str, object] = {}
        for compound in doc.compound:
            for key in (compound.compoundID, compound.ld_id, compound.commonName):
                if key:
                    lookup[key] = compound
        return lookup

    def compounds_for_fluid(doc, fluid) -> list[dict]:
        lookup = compound_lookup(doc)
        rows: list[dict] = []
        for ref in fluid.compounds:
            compound = lookup.get(ref)
            if compound is None:
                rows.append(
                    {
                        "reference": ref,
                        "compoundID": None,
                        "commonName": None,
                        "name_IUPAC": None,
                        "standard_InChI_key": None,
                        "pubChemID": None,
                        "molar_weigth": None,
                        "smiles_code": None,
                    }
                )
            else:
                rows.append(
                    {
                        "compoundID": compound.compoundID,
                        "commonName": compound.commonName,
                        "name_IUPAC": compound.name_IUPAC,
                        "standard_InChI_key": compound.standard_InChI_key,
                        "pubChemID": compound.pubChemID,
                        "molar_weigth": compound.molar_weigth,
                        "smiles_code": compound.smiles_code,
                    }
                )
        return rows

    def fluid_compound_names(doc, fluid) -> str:
        lookup = compound_lookup(doc)
        names: list[str] = []
        for ref in fluid.compounds:
            compound = lookup.get(ref)
            if compound is not None and compound.commonName:
                names.append(compound.commonName)
            else:
                names.append(ref)
        return ", ".join(names)

    def fluid_to_dataframe(fluid) -> pd.DataFrame:
        prop_enum_by_id = {
            prop.propertyID: (
                prop.properties.value if prop.properties is not None else prop.propertyID
            )
            for prop in fluid.property
        }
        param_enum_by_id = {
            param.parameterID: (
                param.parameters.value if param.parameters is not None else param.parameterID
            )
            for param in fluid.parameter
        }

        inspect_rows = []
        for meas in fluid.sample.measurement if fluid.sample else []:
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
            inspect_rows.append(row)
        return pd.DataFrame(inspect_rows)

    return compounds_for_fluid, fluid_compound_names, fluid_to_dataframe


@app.cell
def _(
    compounds_for_fluid,
    fluid_compound_names,
    fluid_to_dataframe,
    inspect_fluid_options,
    inspect_fluid_ui,
    inspect_selected_doc,
    pd,
):
    inspect_df = pd.DataFrame()
    inspect_compound_df = pd.DataFrame()
    inspect_fluid_summary = ""

    if inspect_selected_doc is not None and inspect_fluid_options:
        fluid_index = inspect_fluid_options.get(
            inspect_fluid_ui.value,
            inspect_fluid_ui.value,
        )
        inspect_fluid = inspect_selected_doc.fluid[fluid_index]
        inspect_compound_df = pd.DataFrame(
            compounds_for_fluid(inspect_selected_doc, inspect_fluid)
        )
        inspect_df = fluid_to_dataframe(inspect_fluid)
        inspect_fluid_summary = (
            f"**Fluid {fluid_index}** — "
            f"{fluid_compound_names(inspect_selected_doc, inspect_fluid)}"
            f" — **{len(inspect_df)}** measurements"
        )

    return inspect_compound_df, inspect_df, inspect_fluid_summary


@app.cell
def _(inspect_fluid_summary, mo):
    inspect_summary_output = mo.md(inspect_fluid_summary) if inspect_fluid_summary else mo.md("")
    inspect_summary_output
    return


@app.cell
def _(inspect_compound_df, inspect_fluid_summary, mo):
    inspect_compound_heading = (
        mo.md("#### Compounds (from `compound` block)")
        if inspect_fluid_summary and not inspect_compound_df.empty
        else mo.md("")
    )
    inspect_compound_heading
    return


@app.cell
def _(inspect_compound_df, inspect_fluid_summary, mo):
    inspect_compound_table_output = mo.md("")
    if inspect_fluid_summary and not inspect_compound_df.empty:
        inspect_compound_table_output = mo.ui.table(
            inspect_compound_df,
            selection=None,
            show_column_summaries=False,
            pagination=False,
        )
    inspect_compound_table_output
    return


@app.cell
def _(inspect_df, inspect_fluid_summary, mo):
    inspect_measurements_heading = (
        mo.md("#### Measurements")
        if inspect_fluid_summary and not inspect_df.empty
        else mo.md("")
    )
    inspect_measurements_heading
    return


@app.cell
def _(inspect_df, inspect_fluid_summary, mo):
    inspect_measurements_output = mo.md("")
    if inspect_fluid_summary and not inspect_df.empty:
        inspect_measurements_output = mo.ui.dataframe(inspect_df, page_size=25)
    inspect_measurements_output
    return


@app.cell
def _(inspect_df, inspect_selected_doc, mo):
    inspect_prop_cols = [
        col for col in inspect_df.columns if col.startswith("prop_") and not col.endswith("_unc")
    ]
    inspect_param_cols = [col for col in inspect_df.columns if col.startswith("param_")]

    inspect_x_ui = mo.ui.dropdown(
        options=inspect_param_cols or ["—"],
        value=inspect_param_cols[0] if inspect_param_cols else "—",
        label="X axis",
    )
    inspect_y_ui = mo.ui.dropdown(
        options=inspect_prop_cols or ["—"],
        value=inspect_prop_cols[0] if inspect_prop_cols else "—",
        label="Y axis",
    )
    inspect_arrhenius_ui = mo.ui.switch(value=False, label="Arrhenius: ln(Y) vs 1/X")

    inspect_plot_controls_output = mo.md("")
    if inspect_selected_doc is not None and not inspect_df.empty:
        inspect_plot_controls_output = mo.hstack(
            [inspect_x_ui, inspect_y_ui, inspect_arrhenius_ui],
            justify="start",
            wrap=True,
        )

    inspect_plot_controls_output
    return inspect_arrhenius_ui, inspect_x_ui, inspect_y_ui


@app.cell
def _(
    inspect_arrhenius_ui,
    inspect_df,
    inspect_json_path,
    inspect_selected_doc,
    inspect_x_ui,
    inspect_y_ui,
    mo,
    plt,
):
    import math

    inspect_plot_output = mo.md("")
    if inspect_selected_doc is not None:
        if inspect_df.empty:
            inspect_plot_output = mo.md("> No measurements to plot.")
        elif not inspect_x_ui.value or not inspect_y_ui.value or inspect_x_ui.value == "—":
            inspect_plot_output = mo.md("> Select property and parameter columns for the plot.")
        else:
            inspect_fig, inspect_ax = plt.subplots(figsize=(9, 5.5))
            inspect_plot_df = inspect_df[[inspect_x_ui.value, inspect_y_ui.value]].dropna()
            if inspect_plot_df.empty:
                inspect_plot_output = mo.md("> No valid data points for the selected axes.")
            else:
                inspect_x = inspect_plot_df[inspect_x_ui.value]
                inspect_y = inspect_plot_df[inspect_y_ui.value]
                if inspect_arrhenius_ui.value:
                    inspect_x = 1.0 / inspect_x
                    inspect_y = inspect_y.apply(lambda val: math.log(val))
                    inspect_x_label = f"1 / ({inspect_x_ui.value})"
                    inspect_y_label = f"ln({inspect_y_ui.value})"
                else:
                    inspect_x_label = inspect_x_ui.value
                    inspect_y_label = inspect_y_ui.value

                inspect_ax.scatter(inspect_x, inspect_y, alpha=0.7)
                inspect_ax.set_xlabel(inspect_x_label)
                inspect_ax.set_ylabel(inspect_y_label)
                inspect_ax.grid(True, alpha=0.3)

                inspect_download_widgets = []
                if inspect_json_path is not None and inspect_json_path.is_file():
                    inspect_download_widgets.append(
                        mo.download(
                            data=inspect_json_path.read_bytes(),
                            filename=inspect_json_path.name,
                            label=f"Download JSON ({inspect_json_path.name})",
                        )
                    )

                inspect_plot_output = mo.vstack([inspect_fig, *inspect_download_widgets])

    inspect_plot_output


if __name__ == "__main__":
    app.run()
