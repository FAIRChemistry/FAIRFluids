"""Generate the FAIRFluids analysis tutorial notebooks.

Run with::

    uv run python transition_water/tutorials/_build_notebooks.py

This writes (and overwrites) the tutorial ``.ipynb`` files using ``nbformat``.
Execution / output population is handled separately by ``_run_notebooks.py`` so
that authoring stays fast and deterministic.
"""

from __future__ import annotations

import os

import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))  # repo root
WALKTHROUGH = os.path.join(ROOT, "transition_water", "Walkthrough_Symbolic_Models.ipynb")


def md(text: str):
    return new_markdown_cell(text.strip("\n"))


def code(src: str):
    return new_code_cell(src.strip("\n"))


def write(path: str, cells: list) -> None:
    nb = new_notebook(cells=cells)
    nb.metadata.update(
        {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
        }
    )
    with open(path, "w", encoding="utf-8") as fh:
        nbf.write(nb, fh)
    print("wrote", os.path.relpath(path, ROOT))


# Common preamble that pins JAX to CPU and keeps MCMC small + reproducible.
PREAMBLE = """
import os
os.environ.setdefault("JAX_PLATFORM_NAME", "cpu")

import numpy as np
import pandas as pd
import sympy as sp

# Absolute data paths so the notebook runs from anywhere.
ROOT = "{root}"
DENSITY = os.path.join(ROOT, "transition_water", "data", "Density")
VISCOSITY = os.path.join(ROOT, "transition_water", "data", "Viscosity")
""".format(root=ROOT)


# ---------------------------------------------------------------------------
# 0. Adapted walkthrough (overwrites the original, new models/fit API)
# ---------------------------------------------------------------------------

def build_walkthrough():
    cells = [
        md(r"""
# Walkthrough — declare a property model *once*, fit it two ways, select fluids cleanly

This is the original walkthrough, updated for the **consolidated** `analysis` package. The three
old sub-packages now share **one symbolic model store**:

| concept | new home |
|---|---|
| declare / inspect / serialise models | `fairfluids.analysis.models` (alias `fm`) |
| fit a model (least squares **or** NUTS) | `fairfluids.analysis.fit` (alias `ff`) |
| pick fluid systems out of documents | `fairfluids.analysis.fluids` (alias `flu`) |

Write the physics **once** as a single sympy expression; the same object drives a frequentist
SciPy least-squares fit **and** a Bayesian NumPyro/NUTS fit, so the two pipelines can never drift.

**What you'll see**
1. **Declare** a model — symbols auto-classified into *features / constants / parameters*.
2. **Fit two ways** from that one declaration (least squares + MCMC) — and watch them agree.
3. **Adapters** `ff.fit_group` / `ff.fit_dataset` straight from a `BayesianDataset`.
4. **Fluid selectors** — pick one system, a union of systems, or pin a sub-ratio.
5. **JSON round-trip** — author once, persist, reload.
"""),
        code("""
import os
os.environ.setdefault("JAX_PLATFORM_NAME", "cpu")

import jax
import numpyro
numpyro.set_host_device_count(4)

import numpy as np
import pandas as pd
import sympy as sp

from fairfluids import FAIRFluidsDocument
from fairfluids.analysis import models as fm   # declare / compile / serialise models
from fairfluids.analysis import fit as ff      # least-squares + NUTS backends
from fairfluids.analysis import fluids as flu  # fluid-system selectors
from fairfluids.analysis.bayesian import BayesianDataset

ROOT = "{root}"
DENSITY = os.path.join(ROOT, "transition_water", "data", "Density") + os.sep

print("models already registered:", fm.list_models())
""".format(root=ROOT)),
        md(r"""
## 1. Declare a model once

`fm.define_model` takes a single sympy expression and a list of **features** (the data columns).
Every other free symbol becomes a **parameter** to fit — unless you mark it as a **constant**
(resolved from each group's data before fitting). Below: the VFT viscosity law.

Because `log_observation=True` (the default) the model is fitted on `ln(property)`, and
`log(exp(...))` collapses to the clean additive `mean_expr` automatically.
"""),
        code("""
T, A, B, T0 = sp.symbols("T A B T0")

vft = fm.define_model(
    "vft_viscosity", property="viscosity",
    expr=sp.exp(A + B / (T - T0)), features=["T"],
    p0={"A": -5.0, "B": 700.0, "T0": 150.0},
    overwrite=True,
)

print("features   :", vft.features)
print("parameters :", vft.param_names)
print("constants  :", vft.constant_names)
print("mean_expr  :", vft.mean_expr)

# Compile the mean to a plain numpy kernel (arg order = features, constants, params).
fn = fm.compile_numpy(vft)
print("eta(300 K) :", float(np.exp(fn(np.array([300.0]), -5.0, 700.0, 150.0))[0]))
"""),
        md(r"""
### The third role: constants resolved from data

Hand-written density models often *anchor* the fit to the data — centre temperature on the group
mean `T0 = mean(T)` and pin `rho0` to the density interpolated at that mean. Declaring those two
symbols as **constants** shrinks the free parameters to just the curvature coefficients `A1, A2`,
exactly like the framework's built-in `density_exp_poly_t0_mean_centered` — but here it's a one-liner.
"""),
        code("""
T, T0, rho0, A1, A2 = sp.symbols("T T0 rho0 A1 A2")
rho_expr = rho0 * sp.exp(-(A1 * (T - T0) + sp.Rational(1, 2) * A2 * (T**2 - T0**2)))

rho_model = fm.define_model(
    "rho_exp_poly", property="density", expr=rho_expr, features=["T"],
    constants={"T0":  {"kind": "mean",   "feature": "T"},
               "rho0": {"kind": "interp", "feature": "T"}},
    p0={"A1": 7e-4, "A2": 1e-6}, log_observation=True, overwrite=True,
)

print("parameters :", rho_model.param_names)     # only A1, A2 are fitted
print("constants  :", rho_model.constant_names)  # T0, rho0 resolved per group
print("mean_expr  :", rho_model.mean_expr)
"""),
        md(r"""
## 2. Load real data into a `BayesianDataset`

The `BayesianDataset` is just a **fit-ready data container** (it does not require you to do Bayesian
inference — both backends consume it). Grouping by `source_doi` and `mole_fraction_water` gives one
density-vs-temperature curve per source and composition.
"""),
        code("""
documents = {
    "Glycerol + Water": FAIRFluidsDocument.model_validate_json(
        open(DENSITY + "WaterGlycerol_egorov_density.json").read()
    ),
}

dataset = BayesianDataset.from_documents(
    documents, property="density", features=["temperature"],
    group_by=["source_doi", "mole_fraction_water"], min_points=4, log_observation=True,
)
print(f"groups: {len(dataset)}  (dropped {len(dataset.dropped_groups)})")
dataset.to_overview().head()
"""),
        md(r"""
## 3. Fit the *same declaration* two ways

`ff.fit_group` bridges a `BayesianGroup` to either backend. Two things it handles for you:

* **No double-log.** It always feeds the *raw* (linear) observation; the model applies the log
  itself, and it asserts the group and model agree on `log_observation`.
* **Feature aliasing.** The model calls its feature `T`; the group column is `temperature`. Bridge
  them with `feature_map={"T": "temperature"}`.
"""),
        code("""
from fairfluids.analysis.bayesian.priors import UniformPriorSpec

group = max(dataset.groups, key=lambda g: g.n_points)
print("group:", group.group_label, " n =", group.n_points)

# (1) frequentist — SciPy least squares
lsq = ff.fit_group(rho_model, group, feature_map={"T": "temperature"})
print("LSQ : A1 = %.4e   A2 = %.4e   r2 = %.5f"
      % (lsq.values()["A1"], lsq.values()["A2"], lsq.r_squared))

# (2) Bayesian — NumPyro NUTS on the SAME model object
priors = {
    "A1": UniformPriorSpec(low=-50e-4, high=50e-4),
    "A2": UniformPriorSpec(low=-70e-7, high=145e-7),
    "sigma_scale": 0.0005,
}
mcmc = ff.fit_group(
    rho_model, group, backend="mcmc", feature_map={"T": "temperature"},
    priors=priors, num_warmup=1000, num_samples=1000, num_chains=1, seed=0,
)
post = mcmc.get_samples()
print("MCMC: A1 = %.4e   A2 = %.4e"
      % (float(np.median(post["A1"])), float(np.median(post["A2"]))))
print("\\n-> both backends land on the same parameters (same maths, no drift).")
"""),
        code("""
import matplotlib.pyplot as plt

Tg = group.features["temperature"]
rho_obs = group.raw_observation
Tline = np.linspace(Tg.min(), Tg.max(), 100)

kernel = fm.compile_numpy(rho_model)           # arg order: T, T0, rho0, A1, A2
c = lsq.constants                              # resolved T0, rho0
rho_line = np.exp(kernel(Tline, c["T0"], c["rho0"], lsq.values()["A1"], lsq.values()["A2"]))

plt.figure(figsize=(7, 4))
plt.scatter(Tg, rho_obs, s=28, label="data")
plt.plot(Tline, rho_line, "r-", lw=2, label="declare-once fit (LSQ)")
plt.xlabel("T / K"); plt.ylabel("density")
plt.title(str(group.group_label)[:60]); plt.legend(); plt.tight_layout()
plt.show()
"""),
        md(r"""
## 4. Fit the whole dataset in one call

`ff.fit_dataset` runs the per-group fit across every group, collecting failures rather than
crashing, and `to_frame()` tabulates the parameters, their std-errors, the resolved constants and
each group's r-squared.
"""),
        code("""
result = ff.fit_dataset(rho_model, dataset, feature_map={"T": "temperature"})
print(f"fitted {len(result)} groups, {result.n_failed} failed")
result.to_frame().round(6).head(10)
"""),
        md(r"""
## 5. Selecting fluid systems in multi-system documents

A single document often mixes systems. The Methanol file below actually contains **Ethanol+Water**
*and* **Methanol+Water** rows. `fairfluids.analysis.fluids` turns "which system" into a composable
**row mask** built on the `mole_fraction_<compound>` columns.
"""),
        code("""
from fairfluids.core.functionalities import extract_property_dataframe

corpus = {
    "Methanol/Ethanol + Water": DENSITY + "Methanol_water_10.1021_je700300y.json",
    "Glycerol + Water":         DENSITY + "WaterGlycerol_egorov_density.json",
    "Urea + Water":             DENSITY + "UreaWater_jct_density.json",
}
multi_docs = {k: FAIRFluidsDocument.model_validate_json(open(v).read()) for k, v in corpus.items()}

frames = [extract_property_dataframe(d, property_type="density",
                                     keep_only_relevant_columns=False) for d in multi_docs.values()]
big = pd.concat(frames, ignore_index=True)

def systems_kept(selector):
    sub = big[selector(big)]
    return sorted({tuple(sorted(c)) for c in sub["fluid_compounds"].dropna() if isinstance(c, list)})

print("all systems in corpus     :", systems_kept(lambda df: pd.Series(True, index=df.index)))
print("exact Methanol + Water    :", systems_kept(flu.system("Methanol", "Water")))
print("exact Ethanol + Water     :", systems_kept(flu.system("Ethanol", "Water")))
print("union Methanol | Glycerol :", systems_kept(flu.system("Methanol","Water") | flu.system("Glycerol","Water")))
print("contains Urea             :", systems_kept(flu.contains("Urea")))
"""),
        md(r"""
### Plugging a selector straight into `from_documents`

Any selector is callable as `selector(df) -> mask`, so it drops directly into the `row_filter` hook.
"""),
        code("""
methanol_water = BayesianDataset.from_documents(
    multi_docs, property="density", features=["temperature"],
    group_by=["source_doi", "mole_fraction_water"], min_points=4,
    row_filter=flu.system("Methanol", "Water"),
)
print("methanol-water groups kept:", len(methanol_water))
methanol_water.to_overview().head()
"""),
        md(r"""
## 6. JSON round-trip — author once, persist, reload

Models serialise to a `{"models": [...]}` file. The expression is stored as a **mathematical
string** (parsed back with a safe whitelist), so the file is human-authorable and cannot smuggle in
arbitrary code.
"""),
        code("""
import tempfile

path = os.path.join(tempfile.gettempdir(), "my_fairfluids_models.json")
fm.save_models([vft, rho_model], path)

reloaded = {m.name: m for m in fm.load_models(path)}
rt = reloaded["rho_exp_poly"]
print("reloaded models      :", list(reloaded))
print("expression preserved :", sp.simplify(rt.expr - rho_model.expr) == 0)
print("roles preserved      :", rt.param_names, rt.constant_names, rt.features)
"""),
        md(r"""
## Recap

* One sympy expression → `features / constants / parameters` auto-classified.
* The **same** model object fits via SciPy least squares **and** NumPyro NUTS — they agree.
* `ff.fit_group` / `ff.fit_dataset` bridge prepared `BayesianGroup`s (no double-log, feature aliasing).
* `flu.system / contains / ratio / where` + `| & ~` compose into a `row_filter`.
* `fm.save_models` / `fm.load_models` make declarations portable.

For a deeper, topic-by-topic tour see the `tutorials/` folder next to this notebook.
"""),
    ]
    write(WALKTHROUGH, cells)


# ---------------------------------------------------------------------------
# Tutorial 01 — Declare a property model once (the `models` package)
# ---------------------------------------------------------------------------

def build_t01():
    cells = [
        md(r"""
# Tutorial 01 — Declare a property model *once*

`fairfluids.analysis.models` (alias **`fm`**) is the single source of truth for every property
model in the framework. A model is **one sympy expression** whose free symbols are classified into
three roles:

* **features** — data columns supplied per group (`T`, `p`, `x` …);
* **constants** — fixed before the fit (a literal, or resolved from each group's data);
* **parameters** — everything else: the quantities to fit / sample.

Both fitting backends (`fit.fit_least_squares` for SciPy and `fit.fit_mcmc` for NumPyro) derive
their kernels from this one object, so a model can **never drift** between the frequentist and
Bayesian pipelines.

This tutorial only needs sympy + numpy — no JAX/NumPyro.
"""),
        code(PREAMBLE + """
from fairfluids.analysis import models as fm

print("built-in models:")
for name in fm.list_models():
    m = fm.get_model(name)
    print(f"  {name:38s}  property={m.property:9s}  params={m.param_names}")
"""),
        md(r"""
## 1. Inspect a built-in model

The framework ships a small library (viscosity: Arrhenius/VFT/Litovitz; density: exp-poly variants).
Every model exposes the same introspection surface.
"""),
        code("""
vft = fm.get_model("vft")
print("name        :", vft.name)
print("expr        :", vft.expr)          # natural form: exp(A + B/(T - T0))
print("mean_expr   :", vft.mean_expr)     # observation scale (ln applied): A + B/(T - T0)
print("features    :", vft.features)
print("parameters  :", vft.param_names)
print("constants   :", vft.constant_names)
print("arg_order   :", vft.arg_order)     # canonical kernel arg order
print("param_units :", dict(vft.param_units))
print("derived     :", vft.derived_names)
"""),
        md(r"""
## 2. Declare your own model

`fm.define_model` classifies the symbols for you. Anything that is neither a declared *feature* nor
a declared *constant* becomes a fitted *parameter*. Pass `overwrite=True` so re-running the cell is
idempotent.
"""),
        code("""
T, Ea, logA = sp.symbols("T Ea logA")
R = 8.314

arr = fm.define_model(
    "tut_arrhenius", property="viscosity",
    expr=sp.exp(logA + Ea / (R * T)), features=["T"],
    p0={"logA": -10.0, "Ea": 15000.0},
    param_units={"logA": None, "Ea": "J/mol"},
    overwrite=True,
)
print("features   :", arr.features)
print("parameters :", arr.param_names)   # ('Ea', 'logA') — sorted, role-classified
print("mean_expr  :", arr.mean_expr)
"""),
        md(r"""
## 3. Constants resolved from the data

A *constant* is a symbol fixed before fitting. Three resolver kinds ship out of the box:

| kind | meaning |
|---|---|
| `fixed` | a literal value (or just pass a number) |
| `mean` | the arithmetic mean of a feature column, e.g. `T0 = mean(T)` |
| `interp` | the observation linearly interpolated at an anchor, e.g. `rho0 = rho(mean T)` |

Declaring `T0` and `rho0` as constants leaves only the curvature coefficients to fit.
"""),
        code("""
T, T0, rho0, A1, A2 = sp.symbols("T T0 rho0 A1 A2")
rho_expr = rho0 * sp.exp(-(A1 * (T - T0) + sp.Rational(1, 2) * A2 * (T**2 - T0**2)))

rho_model = fm.define_model(
    "tut_rho_centered", property="density", expr=rho_expr, features=["T"],
    constants={"T0":  {"kind": "mean",   "feature": "T"},
               "rho0": {"kind": "interp", "feature": "T"}},
    p0={"A1": 7e-4, "A2": 1e-6}, overwrite=True,
)
print("parameters :", rho_model.param_names)     # only A1, A2 fitted
print("constants  :", rho_model.constant_names)  # T0, rho0 resolved per group

# Resolve them by hand to see what a fit would compute internally:
from fairfluids.analysis.models.resolvers import resolve_constants
T_arr = np.linspace(280.0, 340.0, 7)
rho_arr = 1000.0 - 0.4 * (T_arr - 298.15)
consts = resolve_constants(rho_model.constants, {"T": T_arr}, rho_arr)
print("resolved   :", {k: round(v, 4) for k, v in consts.items()})
"""),
        md(r"""
## 4. Derived quantities — reparametrisations in one declarative place

`derived=` lets you compute quantities *from* the fitted parameters/constants (e.g. activation
energy in kJ/mol, or a pre-exponential factor). The least-squares backend evaluates these **and
propagates their uncertainty** via the parameter covariance (delta method), so you never hand-derive
error formulas.
"""),
        code("""
T, Ea, logA = sp.symbols("T Ea logA")
R = 8.314
arr2 = fm.define_model(
    "tut_arrhenius_derived", property="viscosity",
    expr=sp.exp(logA + Ea / (R * T)), features=["T"],
    p0={"logA": -10.0, "Ea": 15000.0},
    derived={"Ea_kJ_mol": "Ea / 1000", "A": "exp(logA)"},
    derived_units={"Ea_kJ_mol": "kJ/mol", "A": "Pa*s"},
    overwrite=True,
)
print("derived names :", arr2.derived_names)
print("derived exprs :", {k: str(v) for k, v in arr2.derived_exprs.items()})
"""),
        md(r"""
## 5. Compile the mean to numpy *and* JAX — same maths

`compile_numpy` / `compile_jax` lambdify `mean_expr` with the canonical `arg_order`
(features, then constants, then parameters). The two backends share this expression, so they agree
to floating-point.
"""),
        code("""
np_kernel = fm.compile_numpy(arr)
jx_kernel = fm.compile_jax(arr)            # imports jax lazily

T_eval = np.array([280.0, 300.0, 320.0])
# arg order for arr: features (T), then params sorted (Ea, logA)
y_np = np_kernel(T_eval, 15000.0, -10.0)
y_jx = np.asarray(jx_kernel(T_eval, 15000.0, -10.0))
print("numpy mean_expr :", np.round(y_np, 6))
print("jax   mean_expr :", np.round(y_jx, 6))
print("max abs diff    :", float(np.max(np.abs(y_np - y_jx))))
"""),
        md(r"""
## 6. JSON round-trip — author once, persist, reload

Models serialise to a `{"models": [...]}` file. The expression is stored as a **math string**
parsed back through a safe whitelist (no arbitrary code). This is the exact same shape as the
built-in `models/store/*.json` files.
"""),
        code("""
import tempfile, json

path = os.path.join(tempfile.gettempdir(), "tut01_models.json")
fm.save_models([arr2, rho_model], path)

reloaded = {m.name: m for m in fm.load_models(path)}
rt = reloaded["tut_rho_centered"]
print("reloaded         :", list(reloaded))
print("expr preserved   :", sp.simplify(rt.expr - rho_model.expr) == 0)
print("roles preserved  :", rt.param_names, rt.constant_names, rt.features)

# Peek at the on-disk form of one model:
on_disk = json.loads(open(path).read())["models"][0]
print("stored expr      :", on_disk["expr"])
print("stored constants :", on_disk["constants"])
"""),
        md(r"""
## Recap

* `fm.define_model` turns one sympy expression into a `SymbolicModel`, auto-classifying symbols
  into **features / constants / parameters**.
* **Constants** can be literals or resolved per-group (`mean`, `interp`) — this is how
  data-anchored density models stay one-liners.
* **Derived quantities** centralise reparametrisations; their uncertainty is propagated for you.
* `compile_numpy` / `compile_jax` guarantee the two backends share identical maths.
* `fm.save_models` / `fm.load_models` make declarations portable.

**Next:** `02_frequentist_fitting.ipynb` — fit these models with SciPy.
"""),
    ]
    write(os.path.join(HERE, "01_declare_models.ipynb"), cells)


# ---------------------------------------------------------------------------
# Tutorial 02 — Frequentist fitting (`fit` + `regression`)
# ---------------------------------------------------------------------------

def build_t02():
    cells = [
        md(r"""
# Tutorial 02 — Frequentist fitting

Two complementary entry points fit a model with SciPy least squares:

1. **`fairfluids.analysis.regression`** — a high-level, document-oriented engine. Give it a model
   *name* and FAIRFluids documents; it groups the data, fits every group, and returns a universal
   `ParameterStack` (plus backward-compatible `fit_arrhenius` / `fit_vft` DataFrame wrappers).
2. **`fairfluids.analysis.fit`** (alias `ff`) — the low-level backend that fits *any*
   `SymbolicModel` you declared yourself, from a prepared `BayesianDataset`.

Both share the **same** compiled kernels from the symbolic store, so they agree.
"""),
        code(PREAMBLE + """
import glob
from fairfluids import FAIRFluidsDocument
from fairfluids.analysis import regression as reg
from fairfluids.analysis import models as fm
from fairfluids.analysis import fit as ff

visc_file = os.path.join(VISCOSITY, "Glycerol", "glycerol_water.json")
doc = FAIRFluidsDocument.model_validate_json(open(visc_file).read())
print("regression models:", reg.list_models())
"""),
        md(r"""
## 1. High-level: fit a named model across documents

`reg.fit_documents` returns a `ParameterStack` — a list of per-group `FitResult`s with a tidy
`to_dataframe()` view. Each row carries the fitted parameters, their std-errors, derived quantities
and the group's R².
"""),
        code("""
stack = reg.fit_documents("vft", {"Glycerol + Water": doc},
                          property_type="viscosity", min_points=4)
df = stack.to_dataframe()
print(f"{len(df)} groups fitted with VFT")
df.round(4).head()
"""),
        md(r"""
### Backward-compatible DataFrame wrappers

`fit_arrhenius`, `fit_extended_arrhenius` and `fit_vft` keep the old call signature (a DataFrame in,
a DataFrame out) for existing analysis scripts. They read straight from an extracted property frame.
"""),
        code("""
from fairfluids.analysis import extract_property_dataframe

vdf = extract_property_dataframe(doc, property_type="viscosity",
                                 keep_only_relevant_columns=False)
arr_df = reg.fit_arrhenius(vdf, viscosity_col="viscosity_value", min_points=4)
print("Arrhenius columns:", [c for c in arr_df.columns if c in
      ("Ea_J_mol", "Ea_kJ_mol", "lnA", "R_squared")])
arr_df[[c for c in ("source_doi", "Ea_kJ_mol", "lnA", "R_squared") if c in arr_df.columns]].round(3).head()
"""),
        md(r"""
## 2. Low-level: fit a model you declared yourself

Declare a custom Arrhenius model and fit it through the shared backend. We use a `BayesianDataset`
purely as a **fit-ready data container** (no Bayesian inference involved here).
"""),
        code("""
from fairfluids.analysis.bayesian import BayesianDataset

T, Ea, logA = sp.symbols("T Ea logA")
R = 8.314
arr = fm.define_model(
    "tut02_arrhenius", property="viscosity",
    expr=sp.exp(logA + Ea / (R * T)), features=["T"],
    p0={"logA": -10.0, "Ea": 15000.0},
    derived={"Ea_kJ_mol": "Ea / 1000"}, derived_units={"Ea_kJ_mol": "kJ/mol"},
    overwrite=True,
)

ds = BayesianDataset.from_documents(
    {"Glycerol + Water": doc}, property="viscosity", features=["temperature"],
    group_by=["source_doi", "mole_fraction_water"], min_points=4, log_observation=True,
)
print("groups:", len(ds))

group = max(ds.groups, key=lambda g: g.n_points)
fit = ff.fit_group(arr, group, feature_map={"T": "temperature"})
print("success :", fit.success, " r2 =", round(fit.r_squared, 5))
print("params  :", {k: (round(v, 4), None if s is None else round(s, 4))
                    for k, (v, s) in fit.params.items()})
print("derived :", {k: (round(v, 2), None if s is None else round(s, 2))
                    for k, (v, s) in fit.derived.items()})
"""),
        md(r"""
### Derived-quantity error propagation

The `Ea_kJ_mol` value above already carries a **propagated** standard error (delta method on the
parameter covariance). You declare the reparametrisation once; the backend does the calculus.
"""),
        code("""
ea_val, ea_std = fit.derived["Ea_kJ_mol"]
print(f"Activation energy: {ea_val:.2f} +/- {ea_std:.2f} kJ/mol")
"""),
        md(r"""
## 3. Fit the whole dataset at once

`ff.fit_dataset` fits every group, collecting failures instead of crashing, and `to_frame()`
tabulates the result.
"""),
        code("""
res = ff.fit_dataset(arr, ds, feature_map={"T": "temperature"})
print(f"fitted {len(res)} groups, {res.n_failed} failed")
res.to_frame().round(4).head()
"""),
        md(r"""
## 4. Plot a fit

Compile the kernel and overlay the least-squares curve on the data. Remember the model is fitted on
`ln(viscosity)`, so we exponentiate for a linear-scale plot.
"""),
        code("""
import matplotlib.pyplot as plt

kernel = fm.compile_numpy(arr)        # arg order: T, Ea, logA
Tg = np.asarray(group.features["temperature"], float)
eta = np.asarray(group.raw_observation, float)
Tline = np.linspace(Tg.min(), Tg.max(), 100)
eta_line = np.exp(kernel(Tline, fit.values()["Ea"], fit.values()["logA"]))

fig, ax = plt.subplots(figsize=(7, 4))
ax.scatter(Tg, eta, s=28, label="data")
ax.plot(Tline, eta_line, "r-", lw=2, label="Arrhenius (LSQ)")
ax.set_yscale("log")
ax.set_xlabel("T / K"); ax.set_ylabel("viscosity / Pa s")
ax.set_title(str(group.group_label)[:60]); ax.legend(); fig.tight_layout()
plt.show()
"""),
        md(r"""
## Recap

* `reg.fit_documents(name, docs)` → `ParameterStack.to_dataframe()` is the quick, document-driven path.
* `reg.fit_arrhenius / fit_vft / fit_extended_arrhenius` keep the legacy DataFrame interface.
* `ff.fit_group` / `ff.fit_dataset` fit **your own** declared models through the same kernels.
* Declared **derived quantities** come back with propagated uncertainties — no manual error algebra.

**Next:** `03_bayesian_inference.ipynb` — the same models, full posterior.
"""),
    ]
    write(os.path.join(HERE, "02_frequentist_fitting.ipynb"), cells)


# ---------------------------------------------------------------------------
# Tutorial 03 — Bayesian inference & the workflow facade
# ---------------------------------------------------------------------------

def build_t03():
    cells = [
        md(r"""
# Tutorial 03 — Bayesian inference & the workflow

`fairfluids.analysis.bayesian` runs NumPyro NUTS on the **same** symbolic models, with priors you
supply at fit time. Two layers:

* **building blocks** — `BayesianDataset`, `PriorSet`, and `ff.fit_group(..., backend="mcmc")`;
* **`BayesianWorkflow`** — a facade that orchestrates prior exploration → MCMC → diagnostics →
  model comparison → plots → write-back.

Requires the `[bayesian]` extra (JAX / NumPyro / ArviZ). MCMC here is kept small for speed.
"""),
        code(PREAMBLE + """
import numpyro
numpyro.set_host_device_count(2)

from fairfluids import FAIRFluidsDocument
from fairfluids.analysis import models as fm
from fairfluids.analysis import fit as ff
from fairfluids.analysis import bayesian as bayes
from fairfluids.analysis.bayesian import (
    BayesianDataset, BayesianWorkflow, PriorSet, UniformPriorSpec,
)

doc = FAIRFluidsDocument.model_validate_json(
    open(os.path.join(DENSITY, "WaterGlycerol_egorov_density.json")).read()
)
ds = BayesianDataset.from_documents(
    {"Glycerol + Water": doc}, property="density", features=["temperature"],
    group_by=["source_doi", "mole_fraction_water"], min_points=4, log_observation=True,
)
# Keep just a few groups so the tutorial runs quickly.
ds.groups[:] = ds.groups[:3]
print("groups used:", len(ds))
print("registered Bayesian models:", bayes.list_models())
"""),
        md(r"""
## 1. Priors

There are **no hidden prior presets** — you state them explicitly with a `PriorSet`. Each parameter
gets a typed `PriorSpec` (Uniform / Normal / HalfNormal / LogNormal / TruncatedNormal); the
`sigma_scale` sets the HalfNormal scale of the observation-noise term.
"""),
        code("""
priors = PriorSet(
    parameters={
        "A1": UniformPriorSpec(low=-5e-3, high=5e-3),
        "A2": UniformPriorSpec(low=-7e-6, high=1.45e-5),
    },
    sigma_scale=5e-4,
)
print(priors)
"""),
        md(r"""
## 2. Frequentist vs Bayesian on one group — they agree

`ff.fit_group` drives either backend off the same model object. The NUTS posterior median lands on
the least-squares optimum (same maths, no drift).
"""),
        code("""
rho_model = fm.get_model("density_exp_poly_t0_mean_centered")
group = max(ds.groups, key=lambda g: g.n_points)

# The builtin model calls its feature ``T``; the dataset column is ``temperature``.
fmap = {"T": "temperature"}
lsq = ff.fit_group(rho_model, group, feature_map=fmap)
mcmc = ff.fit_group(rho_model, group, backend="mcmc", feature_map=fmap, priors=priors,
                    num_warmup=400, num_samples=400, num_chains=1, seed=0)
post = mcmc.get_samples()
print("LSQ  A1=%.4e  A2=%.4e" % (lsq.values()["A1"], lsq.values()["A2"]))
print("NUTS A1=%.4e  A2=%.4e" % (float(np.median(post["A1"])), float(np.median(post["A2"]))))
"""),
        md(r"""
## 3. The workflow facade

`BayesianWorkflow.from_names` ties a dataset, a list of model names, and priors together. From there
the whole lifecycle is method calls.
"""),
        code("""
wf = BayesianWorkflow.from_names(
    ds, ["density_exp_poly_t0_mean_centered"], priors=priors,
)

# Phase 1 — prior predictive sanity check (quantiles per model)
wf.explore_priors(n_samples=2000, seed=0)
"""),
        code("""
# Phase 2 — fit every (model, group) pair
fit = wf.fit(num_warmup=400, num_samples=400, num_chains=2, seed=0)
print("fitted pairs:", len(fit.fits))
"""),
        md(r"""
### Convergence diagnostics & posterior summary
"""),
        code("""
wf.diagnostics().round(4).head()
"""),
        code("""
wf.posterior_summary().round(5).head(10)
"""),
        md(r"""
## 4. Compare competing models

Fit two density models and let ArviZ rank them by LOO (leave-one-out cross-validation). The
comparison returns three tidy tables: per-group best, per-group-per-model, and a global ranking.
"""),
        code("""
wf2 = BayesianWorkflow.from_names(
    ds,
    ["density_exp_poly_t0_mean_centered", "density_exp_poly_t0"],
    priors={
        "density_exp_poly_t0_mean_centered": priors,
        "density_exp_poly_t0": PriorSet(
            parameters={
                "A1": UniformPriorSpec(low=-5e-3, high=5e-3),
                "A2": UniformPriorSpec(low=-7e-6, high=1.45e-5),
                "rho0": UniformPriorSpec(low=900.0, high=1400.0),
            },
            sigma_scale=5e-4,
        ),
    },
)
wf2.fit(num_warmup=400, num_samples=400, num_chains=2, seed=0)
cmp = wf2.compare()
cmp.global_ranking.round(3)
"""),
        md(r"""
## 5. Plots

The workflow exposes plotting facades (matplotlib). A couple of common ones:
"""),
        code("""
import matplotlib
matplotlib.use("Agg")  # headless rendering for notebook execution

fig1, ax1 = wf.plot_dataset_overview()
fig1.suptitle("Dataset overview")
fig1.tight_layout()

fig2, ax2 = wf.plot_posterior_predictive(
    "density_exp_poly_t0_mean_centered", group_id=group.group_id, feature="temperature",
)
fig2.tight_layout()
print("rendered overview + posterior-predictive figures")
"""),
        md(r"""
## 6. Write the posterior back into a FAIRFluids document

`fit_to_fairfluids_document` (or `workflow.to_fairfluids_document`) records each group's posterior
summary back into a document so the fit is FAIR-archived alongside the data.
"""),
        code("""
from fairfluids.analysis.bayesian import fit_to_fairfluids_document

enriched = fit_to_fairfluids_document(fit, doc, point_estimate="median")
print("write-back returned a", type(enriched).__name__)
"""),
        md(r"""
## Recap

* Priors are **explicit** (`PriorSet` + typed `PriorSpec`s) — no hidden defaults.
* `ff.fit_group(..., backend="mcmc")` runs NUTS on the same model the least-squares path uses; the
  posterior median matches the LSQ optimum.
* `BayesianWorkflow` orchestrates the full lifecycle: `explore_priors` → `fit` → `diagnostics` /
  `posterior_summary` → `compare` → `plot_*` → `to_fairfluids_document`.
* Model comparison uses LOO and returns ready-to-read ranking tables.

**Next:** `04_fluid_selectors.ipynb` — slice multi-system documents cleanly.
"""),
    ]
    write(os.path.join(HERE, "03_bayesian_inference.ipynb"), cells)


# ---------------------------------------------------------------------------
# Tutorial 04 — Fluid-system selectors
# ---------------------------------------------------------------------------

def build_t04():
    cells = [
        md(r"""
# Tutorial 04 — Selecting fluid systems

Real documents mix systems: a single file may hold Methanol+Water *and* Ethanol+Water rows, or a
ternary where you only want one sub-ratio. `fairfluids.analysis.fluids` (alias **`flu`**) turns
"which system" into a composable **row mask** over the `mole_fraction_<compound>` columns.

A selector is just a callable `selector(df) -> boolean mask`, so it composes with `& | ~` and drops
straight into `BayesianDataset.from_documents(..., row_filter=...)`.
"""),
        code(PREAMBLE + """
from fairfluids import FAIRFluidsDocument
from fairfluids.analysis import fluids as flu
from fairfluids.analysis import extract_property_dataframe

corpus = {
    "Methanol/Ethanol + Water": os.path.join(DENSITY, "Methanol_water_10.1021_je700300y.json"),
    "Glycerol + Water":         os.path.join(DENSITY, "WaterGlycerol_egorov_density.json"),
    "Urea + Water":             os.path.join(DENSITY, "UreaWater_jct_density.json"),
}
docs = {k: FAIRFluidsDocument.model_validate_json(open(v).read()) for k, v in corpus.items()}

frames = [extract_property_dataframe(d, property_type="density",
                                     keep_only_relevant_columns=False) for d in docs.values()]
big = pd.concat(frames, ignore_index=True)
print("total rows:", len(big))
"""),
        md(r"""
## 1. The building blocks

* `flu.system(*compounds)` — rows whose fluid system is **exactly** that set of compounds.
* `flu.contains(compound)` — rows that include a given compound (system may be larger).
* `flu.where(**ranges)` — inclusive range filter on `mole_fraction_<compound>` columns.
* `flu.system(...).ratio(**parts)` — pin a fixed ratio *within* named components (others free).
"""),
        code("""
def systems_kept(selector):
    sub = big[selector(big)]
    return sorted({tuple(sorted(c)) for c in sub["fluid_compounds"].dropna()
                   if isinstance(c, list)})

print("everything             :", systems_kept(lambda df: pd.Series(True, index=df.index)))
print("exact Methanol + Water :", systems_kept(flu.system("Methanol", "Water")))
print("exact Ethanol + Water  :", systems_kept(flu.system("Ethanol", "Water")))
print("contains Urea          :", systems_kept(flu.contains("Urea")))
"""),
        md(r"""
## 2. Compose with `& | ~`

Selectors are boolean-algebra citizens: union (`|`), intersection (`&`), negation (`~`).
"""),
        code("""
union = flu.system("Methanol", "Water") | flu.system("Glycerol", "Water")
print("Methanol | Glycerol    :", systems_kept(union))

not_urea = ~flu.contains("Urea")
print("everything but Urea    :", systems_kept(not_urea))
"""),
        md(r"""
## 3. Pin a sub-ratio while a third component varies

For a ternary you might want Glycerol:Methanol fixed at **1:2** while water is free. `.ratio(...)`
normalises *within* the named components, so water can take any value. (Shown on a tiny synthetic
frame, since the density files above are binaries.)
"""),
        code("""
demo = pd.DataFrame({
    "mole_fraction_glycerol": [0.10, 0.20, 0.05, 0.00],
    "mole_fraction_methanol": [0.20, 0.30, 0.10, 0.40],
    "mole_fraction_water":    [0.70, 0.50, 0.85, 0.60],
    "label": ["G:M = 1:2", "G:M = 2:3", "G:M = 1:2", "no glycerol"],
})
sel = flu.system("glycerol", "methanol", "water").ratio(glycerol=1, methanol=2)
print("kept (G:M = 1:2, water free):", demo[sel(demo)]["label"].tolist())
"""),
        md(r"""
## 4. Plug a selector into dataset construction

`row_filter` accepts any selector and is applied after extraction, before grouping — a strict
superset of the older `composition_filter`.
"""),
        code("""
from fairfluids.analysis.bayesian import BayesianDataset

methanol_water = BayesianDataset.from_documents(
    docs, property="density", features=["temperature"],
    group_by=["source_doi", "mole_fraction_water"], min_points=4,
    row_filter=flu.system("Methanol", "Water"),
)
print("Methanol+Water groups kept:", len(methanol_water))
methanol_water.to_overview().head()
"""),
        md(r"""
## Recap

* `flu.system / contains / where / ratio` build readable row masks over composition columns.
* They compose with `& | ~` and are plain callables, so they slot into
  `BayesianDataset.from_documents(row_filter=...)` and any pandas filtering.
* `.ratio(...)` pins a ratio *within* named components while leaving the rest free — ideal for
  isolating one cut of a ternary.

That completes the analysis-package tour: **declare** (T01) → **fit frequentist** (T02) →
**fit Bayesian** (T03) → **select systems** (T04).
"""),
    ]
    write(os.path.join(HERE, "04_fluid_selectors.ipynb"), cells)


if __name__ == "__main__":
    build_walkthrough()
    build_t01()
    build_t02()
    build_t03()
    build_t04()
    print("done — all notebooks generated")
