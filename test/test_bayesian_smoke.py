"""Smoke tests for ``fairfluids.analysis.bayesian``.

These tests are skipped automatically when the optional ``[bayesian]`` extra
(``numpyro``, ``jax``, ``arviz``) is not installed. They exercise the public
API end-to-end on synthetic Arrhenius data with very small MCMC chains so they
finish in seconds.

Priors are always supplied explicitly via :class:`PriorSet` (there are no
presets and no hierarchical models any more).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
import pytest

bayesian = pytest.importorskip(
    "fairfluids.analysis.bayesian",
    reason="Bayesian extras (numpyro / jax / arviz) not installed.",
)

from fairfluids.analysis.bayesian import (  # noqa: E402
    BayesianDataset,
    BayesianGroup,
    BayesianWorkflow,
    HalfNormalPriorSpec,
    NormalPriorSpec,
    PriorSet,
    UniformPriorSpec,
    get_model,
    list_models,
    sample_prior,
)
from fairfluids.analysis.bayesian.bridge import R_GAS  # noqa: E402


# ---------------------------------------------------------------------------
# Prior factories (no presets — every fit defines its own PriorSet)
# ---------------------------------------------------------------------------


def _arrhenius_priors(
    *,
    likelihood: str = "normal",
    student_t_df: float = 4.0,
    logA: tuple[float, float] = (-30.0, -10.0),
    Ea: tuple[float, float] = (10000.0, 60000.0),
) -> PriorSet:
    return PriorSet(
        parameters={
            "logA": UniformPriorSpec(low=logA[0], high=logA[1]),
            "Ea": UniformPriorSpec(low=Ea[0], high=Ea[1]),
        },
        sigma_scale=0.1,
        likelihood=likelihood,
        student_t_df=student_t_df,
    )


def _litovitz_priors() -> PriorSet:
    return PriorSet(
        parameters={
            "a": UniformPriorSpec(low=-30.0, high=10.0),
            "b": UniformPriorSpec(low=-1.0e9, high=1.0e9),
        },
        sigma_scale=0.1,
    )


def _synth_arrhenius(
    logA: float,
    Ea: float,
    *,
    n: int = 10,
    sigma: float = 0.05,
    seed: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    T = np.linspace(280.0, 360.0, n)
    log_eta = logA + Ea / (R_GAS * T) + rng.normal(0.0, sigma, n)
    return T, np.exp(log_eta)


def _make_synthetic_dataset() -> BayesianDataset:
    T1, eta1 = _synth_arrhenius(-20.0, 30000.0, seed=1)
    T2, eta2 = _synth_arrhenius(-22.0, 35000.0, seed=2)

    groups = []
    for T, eta, doi, w in (
        (T1, eta1, "10.x/a", 0.3),
        (T2, eta2, "10.x/b", 0.7),
    ):
        df = pd.DataFrame(
            {
                "temperature": T,
                "viscosity_value": eta,
                "source_doi": doi,
                "mole_fraction_water": w,
            }
        )
        obs = np.log(eta)
        groups.append(
            BayesianGroup(
                group_id=(doi, w),
                group_label=f"{doi} w={w}",
                metadata={
                    "source_doi": doi,
                    "mole_fraction_water": w,
                    "system_name": "synthetic",
                    "group_by": {"source_doi": doi, "mole_fraction_water": w},
                },
                features={"temperature": T.astype(float)},
                observation=obs.astype(float),
                observation_uncertainty=None,
                raw_observation=eta.astype(float),
                log_observation=True,
                dataframe=df,
            )
        )

    return BayesianDataset(
        property="viscosity",
        feature_names=("temperature",),
        group_by=("source_doi", "mole_fraction_water"),
        log_observation=True,
        groups=groups,
    )


# ---------------------------------------------------------------------------
# Registry / model metadata
# ---------------------------------------------------------------------------


def test_builtin_models_registered() -> None:
    names = list_models()
    for expected in (
        "arrhenius",
        "vft",
        "litovitz",
        "litovitz_extended",
        "density_exp_poly",
        "density_exp_poly_t0",
        "density_exp_poly_t0_mean_centered",
        "density_exp_poly_t0_anchored",
    ):
        assert expected in names


def test_get_model_returns_bayesian_model() -> None:
    arr = get_model("arrhenius")
    assert arr.name == "arrhenius"
    assert arr.property_name == "viscosity"
    assert "temperature" in arr.feature_names
    assert set(arr.param_names) == {"logA", "Ea"}


def test_density_models_carry_property() -> None:
    assert get_model("density_exp_poly").property_name == "density"
    assert get_model("density_exp_poly_t0").property_name == "density"


def test_priorset_is_frozen_and_validates() -> None:
    priors = _arrhenius_priors()
    with pytest.raises(Exception):
        priors.sigma_scale = 0.5  # frozen

    # Missing a required parameter must fail validation.
    incomplete = PriorSet(parameters={"logA": UniformPriorSpec(low=-30.0, high=10.0)})
    with pytest.raises(ValueError, match="missing required parameters"):
        get_model("arrhenius").validate_priors(incomplete)


def test_density_exp_poly_t0_mean_centered_bind_and_mean() -> None:
    """Anchored density model: T0 = mean(T), rho0 interpolated; ln rho mean."""
    import jax.numpy as jnp

    T = np.array([300.0, 310.0, 320.0])
    rho = np.array([1000.0, 995.0, 990.0])
    df = pd.DataFrame({"temperature": T, "density_value": rho, "source_doi": "10.x"})
    group = BayesianGroup(
        group_id=("10.x",),
        group_label="test",
        metadata={},
        features={"temperature": T.astype(float)},
        observation=np.log(rho.astype(float)),
        observation_uncertainty=None,
        raw_observation=rho.astype(float),
        log_observation=True,
        dataframe=df,
    )
    proto = get_model("density_exp_poly_t0_mean_centered")
    bound = proto.bind_group(group)
    consts = bound.resolved_constants
    t0 = consts["T0"]
    rho0 = consts["rho0"]
    assert t0 == float(np.mean(T))
    assert rho0 == pytest.approx(float(np.interp(np.mean(T), T, rho)))
    assert bound.log_observation is True

    A1 = jnp.array(1.0e-4)
    A2 = jnp.array(1.0e-6)
    ln_pred = bound.mean({"temperature": jnp.asarray(T)}, {"A1": A1, "A2": A2})
    i0 = int(np.argmin(np.abs(T - t0)))
    assert jnp.allclose(ln_pred[i0], jnp.log(rho0), rtol=1e-5)

    poly = A1 * (T - t0) + 0.5 * A2 * (T**2 - t0**2)
    ln_ref = jnp.log(rho0) - poly
    assert jnp.allclose(ln_pred, ln_ref)

    rho_lin = bound.transform_mean_for_display(np.asarray(ln_pred))
    assert np.allclose(rho_lin, np.exp(np.asarray(ln_pred)))
    assert bound.observation_axis_label() == r"$\rho$ / kg m$^{-3}$"
    assert bound.observation_axis_label(plot_scale="likelihood") == (
        r"$\ln(\rho\,/\,\mathrm{kg\,m^{-3}})$"
    )
    assert np.allclose(
        bound.observation_for_display(group),
        group.raw_observation,
    )


def test_density_exp_poly_centered_ln_mean() -> None:
    """Centered ln model matches rho = rho0 * exp[-(0.5*A2*Tc^2 + A1*Tc)]."""
    import jax.numpy as jnp

    model = get_model("density_exp_poly_t0")
    t_ref = model.static_constants["T0"]
    T = jnp.array([280.0, 300.0, 320.0])
    rho0, A1, A2 = 1100.0, 1.0e-3, 1.0e-6

    ln_pred = model.mean({"temperature": T}, {"rho0": rho0, "A1": A1, "A2": A2})
    rho_pred = jnp.exp(ln_pred)
    poly = A1 * (T - t_ref) + 0.5 * A2 * (T**2 - t_ref**2)
    rho_ref = rho0 * jnp.exp(-poly)
    assert jnp.allclose(rho_pred, rho_ref)

    flat = model.mean(
        {"temperature": jnp.array([t_ref])},
        {"rho0": rho0, "A1": 0.0, "A2": 0.0},
    )
    assert jnp.allclose(jnp.exp(flat), rho0)


def test_density_exp_poly_simple_mean() -> None:
    """Generated DensityExpPoly (no reference T): ln rho = ln rho0 - A1*T - 0.5*A2*T^2."""
    import jax.numpy as jnp

    model = get_model("density_exp_poly")
    assert set(model.param_names) == {"rho0", "A1", "A2"}
    T = jnp.array([280.0, 300.0, 320.0])
    rho0, A1, A2 = 1100.0, 1.0e-4, 1.0e-7
    ln_pred = model.mean({"temperature": T}, {"rho0": rho0, "A1": A1, "A2": A2})
    expected = jnp.log(rho0) - (A1 * T + 0.5 * A2 * T**2)
    assert jnp.allclose(ln_pred, expected)


# ---------------------------------------------------------------------------
# Progress / dataset helpers (no MCMC)
# ---------------------------------------------------------------------------


def test_total_mcmc_steps() -> None:
    from fairfluids.analysis.bayesian.progress import total_mcmc_steps

    assert total_mcmc_steps(num_jobs=27, num_warmup=2000, num_samples=2000, num_chains=3) == 324_000


def test_unified_mcmc_progress_advances_on_main_thread() -> None:
    from fairfluids.analysis.bayesian.progress import unified_mcmc_progress

    with unified_mcmc_progress(total_steps=100, description="test") as progress:
        progress.configure_job(steps_per_job=40)
        progress.complete_job(group="a")
        assert progress._bar.n == 40
        progress.complete_job(group="b")
        assert progress._bar.n == 80


def test_dataset_to_overview() -> None:
    ds = _make_synthetic_dataset()
    overview = ds.to_overview()
    assert len(overview) == 2
    assert {"n_points", "obs_min", "obs_max"}.issubset(overview.columns)


def test_dataset_select_callable() -> None:
    ds = _make_synthetic_dataset()
    subset = ds.select(lambda g: g.group_id[1] > 0.5)
    assert len(subset) == 1
    assert math.isclose(subset.groups[0].group_id[1], 0.7)


def test_uncertainty_coverage_property() -> None:
    ds = _make_synthetic_dataset()
    assert ds.uncertainty_coverage == 0.0

    df = pd.DataFrame({"temperature": [300.0, 310.0], "viscosity_value": [1.1, 1.2]})
    with_unc = BayesianGroup(
        group_id=("doi", 0.5),
        group_label="x",
        metadata={},
        features={"temperature": np.array([300.0, 310.0])},
        observation=np.array([0.1, 0.2]),
        observation_uncertainty=np.array([0.01, 0.01]),
        raw_observation=np.array([1.1, 1.2]),
        log_observation=False,
        dataframe=df,
    )
    ds2 = BayesianDataset(
        property="viscosity",
        feature_names=("temperature",),
        group_by=("source_doi",),
        log_observation=False,
        groups=[with_unc, ds.groups[0]],
    )
    assert 0.0 < ds2.uncertainty_coverage < 1.0


# ---------------------------------------------------------------------------
# Prior specs (no MCMC)
# ---------------------------------------------------------------------------


def test_uniform_prior_spec_validation() -> None:
    with pytest.raises(ValueError):
        UniformPriorSpec(low=1.0, high=0.5)


def test_sample_prior_returns_finite_array() -> None:
    spec = NormalPriorSpec(loc=0.0, scale=1.0)
    samples = sample_prior(spec, n_samples=512, seed=42)
    assert samples.shape == (512,)
    assert np.all(np.isfinite(samples))
    assert abs(samples.mean()) < 0.3


def test_prior_specs_to_numpyro_smoke() -> None:
    import jax.random as random

    key = random.PRNGKey(0)
    for spec in (
        UniformPriorSpec(low=-1.0, high=1.0),
        NormalPriorSpec(loc=0.0, scale=2.0),
        HalfNormalPriorSpec(scale=1.5),
    ):
        d = spec.to_numpyro()
        s = d.sample(key, sample_shape=(8,))
        assert s.shape == (8,)
    from fairfluids.analysis.bayesian import TruncatedNormalPriorSpec

    tn = TruncatedNormalPriorSpec(loc=10.0, scale=2.0, low=0.0)
    s = tn.to_numpyro().sample(key, sample_shape=(16,))
    assert (np.asarray(s) >= 0.0).all()


# ---------------------------------------------------------------------------
# Workflow end-to-end (small MCMC)
# ---------------------------------------------------------------------------


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_workflow_end_to_end() -> None:
    import numpyro

    numpyro.set_host_device_count(1)

    ds = _make_synthetic_dataset()
    wf = BayesianWorkflow(
        dataset=ds,
        models=[get_model("arrhenius"), get_model("litovitz")],
        priors={"arrhenius": _arrhenius_priors(), "litovitz": _litovitz_priors()},
    )

    # One row per model.
    explore = wf.explore_priors(n_samples=100, seed=0)
    assert {"model", "q50"}.issubset(explore.columns)
    assert len(explore) == 2

    fit = wf.fit(num_warmup=100, num_samples=100, num_chains=1, progress_bar=False)
    assert set(fit.model_names) == {"arrhenius", "litovitz"}
    assert len(fit.group_ids) == 2

    diag = wf.diagnostics()
    assert {"parameter", "rhat", "ess_bulk"}.issubset(diag.columns)

    summary = wf.posterior_summary()
    assert {"parameter", "median", "q05", "q95"}.issubset(summary.columns)

    comp = wf.compare()
    assert not comp.global_ranking.empty
    assert {"model", "sum_elpd", "n_groups"}.issubset(comp.global_ranking.columns)
    assert comp.global_ranking.iloc[0]["model"] == "arrhenius"


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_workflow_accepts_single_priorset_for_all_models() -> None:
    import numpyro

    numpyro.set_host_device_count(1)

    ds = _make_synthetic_dataset()
    wf = BayesianWorkflow(
        dataset=ds,
        models=[get_model("arrhenius")],
        priors=_arrhenius_priors(),
    )
    fit = wf.fit(num_warmup=80, num_samples=80, num_chains=1, progress_bar=False)
    assert "arrhenius" in fit.model_names
    summary = wf.posterior_summary()
    assert {"logA", "Ea"}.issubset(set(summary["parameter"]))


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_workflow_with_normal_priors_runs() -> None:
    import numpyro

    numpyro.set_host_device_count(1)

    normal_priors = PriorSet(
        parameters={
            "logA": NormalPriorSpec(loc=-21.0, scale=4.0),
            "Ea": NormalPriorSpec(loc=30000.0, scale=8000.0),
        },
        sigma_scale=0.1,
    )

    ds = _make_synthetic_dataset()
    wf = BayesianWorkflow(
        dataset=ds,
        models=[get_model("arrhenius")],
        priors=normal_priors,
    )
    fit = wf.fit(num_warmup=80, num_samples=80, num_chains=1, progress_bar=False)
    assert "arrhenius" in fit.model_names

    samples = wf.posterior_samples("arrhenius")
    assert {"logA", "Ea", "model_sigma"}.issubset(set(samples))
    assert samples["logA"].ndim == 1
    assert samples["logA"].size == 80

    idata = wf.inference_data("arrhenius")
    assert hasattr(idata, "posterior")


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_student_t_likelihood_runs() -> None:
    import numpyro

    numpyro.set_host_device_count(1)

    ds = _make_synthetic_dataset()
    wf = BayesianWorkflow(
        dataset=ds,
        models=[get_model("arrhenius")],
        priors=_arrhenius_priors(likelihood="student_t", student_t_df=4.0),
    )
    fit = wf.fit(num_warmup=80, num_samples=80, num_chains=1, progress_bar=False)
    assert "arrhenius" in fit.model_names


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_predict_and_predict_averaged() -> None:
    import numpyro

    numpyro.set_host_device_count(1)

    ds = _make_synthetic_dataset()
    wf = BayesianWorkflow(
        dataset=ds,
        models=[get_model("arrhenius"), get_model("litovitz")],
        priors={"arrhenius": _arrhenius_priors(), "litovitz": _litovitz_priors()},
    )
    wf.fit(num_warmup=80, num_samples=80, num_chains=1, progress_bar=False)

    T_new = np.linspace(285.0, 355.0, 12)
    pred = wf.predict("arrhenius", {"temperature": T_new})
    assert pred["mean"].shape == (12,)
    assert pred["q05"].shape == (12,)
    assert pred["q95"].shape == (12,)
    assert (pred["q05"] <= pred["q95"]).all()

    pred_avg = wf.predict_averaged({"temperature": T_new}, weights={"arrhenius": 0.6, "litovitz": 0.4})
    assert pred_avg["mean"].shape == (12,)
    assert abs(sum(pred_avg["weights"].values()) - 1.0) < 1e-6


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_energy_diagnostics_and_bayesian_p_values() -> None:
    import numpyro

    numpyro.set_host_device_count(1)

    ds = _make_synthetic_dataset()
    wf = BayesianWorkflow(
        dataset=ds,
        models=[get_model("arrhenius")],
        priors=_arrhenius_priors(),
    )
    wf.fit(num_warmup=80, num_samples=80, num_chains=1, progress_bar=False)

    energy = wf.energy_diagnostics()
    assert {"model", "group_label", "ebfmi", "warning"}.issubset(energy.columns)
    assert (energy["ebfmi"] > 0).all() or energy["ebfmi"].isna().all()

    pvals = wf.bayesian_p_values(statistics=("mean", "rmse"))
    assert {"statistic", "p_value"}.issubset(pvals.columns)
    assert ((pvals["p_value"] >= 0.0) & (pvals["p_value"] <= 1.0)).all()


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_refit_without_influential_drop_log_schema() -> None:
    import numpyro

    numpyro.set_host_device_count(1)

    ds = _make_synthetic_dataset()
    wf = BayesianWorkflow(
        dataset=ds,
        models=[get_model("arrhenius")],
        priors=_arrhenius_priors(),
    )
    wf.fit(num_warmup=80, num_samples=80, num_chains=1, progress_bar=False)
    wf.compare()

    _, drop_log = wf.refit_without_influential(
        k_threshold=999.0,
        num_warmup=60,
        num_samples=60,
        num_chains=1,
        progress_bar=False,
    )
    assert list(drop_log.columns) == [
        "model", "group_id", "group_label", "n_dropped", "n_remaining",
    ]


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_prior_sensitivity_runs() -> None:
    import numpyro

    numpyro.set_host_device_count(1)

    ds = _make_synthetic_dataset()
    wf = BayesianWorkflow(
        dataset=ds,
        models=[get_model("arrhenius")],
        priors=_arrhenius_priors(),
    )
    df = wf.prior_sensitivity(
        scales=(0.75, 1.0, 1.5),
        num_warmup=60,
        num_samples=60,
        num_chains=1,
        progress_bar=False,
    )
    assert {"scale", "parameter", "median"}.issubset(df.columns)
    assert set(df["scale"].unique()) == {0.75, 1.0, 1.5}


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_group_selectors_resolve_to_same_fit() -> None:
    """All selector forms (None / int / str / dict / tuple) must address the same group."""
    import numpyro

    numpyro.set_host_device_count(1)

    ds = _make_synthetic_dataset()
    wf = BayesianWorkflow(
        dataset=ds,
        models=[get_model("arrhenius")],
        priors=_arrhenius_priors(),
    )
    wf.fit(num_warmup=60, num_samples=60, num_chains=1, progress_bar=False)

    overview = wf.groups_overview("arrhenius")
    assert {"index", "group_label", "group_id", "n_points"}.issubset(overview.columns)
    assert "mole_fraction_water" in overview.columns
    assert len(overview) == 2

    target = overview.iloc[1]
    target_gid = target["group_id"]

    cases: list[Any] = [
        1,
        -1,
        target["group_label"],
        {"mole_fraction_water": target["mole_fraction_water"]},
        target_gid,
    ]
    for selector in cases:
        s_int = wf.posterior_samples("arrhenius", group_id=selector)
        s_ref = wf.posterior_samples("arrhenius", group_id=target_gid)
        np.testing.assert_array_equal(s_int["logA"], s_ref["logA"])

    label = target["group_label"]
    fragment = label.split()[0]
    s_sub = wf.posterior_samples("arrhenius", group_id=fragment)
    np.testing.assert_array_equal(s_sub["logA"], s_int["logA"])

    with pytest.raises(IndexError):
        wf.posterior_samples("arrhenius", group_id=99)
    with pytest.raises(KeyError):
        wf.posterior_samples("arrhenius", group_id={"mole_fraction_water": -1.0})
    with pytest.raises(KeyError):
        wf.posterior_samples("arrhenius", group_id="this label does not exist")


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_plot_functions_return_handles(tmp_path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ds = _make_synthetic_dataset()
    wf = BayesianWorkflow(
        dataset=ds,
        models=[get_model("arrhenius")],
        priors=_arrhenius_priors(),
    )
    wf.fit(num_warmup=100, num_samples=100, num_chains=1, progress_bar=False)
    wf.compare()

    fig, _ = wf.plot_posterior_predictive("arrhenius")
    assert fig is not None
    plt.close(fig)

    fig, _ = wf.plot_posterior_predictive("arrhenius", x_axis="feature")
    plt.close(fig)

    fig, _ = wf.plot_posterior_predictive("arrhenius", x_axis="inverse_temperature")
    plt.close(fig)

    fig, _ = wf.plot_posterior_predictive("arrhenius", group_id=0)
    assert fig is not None
    plt.close(fig)

    fig, _ = wf.plot_parameter_vs_feature(
        "arrhenius", parameter="Ea", feature="mole_fraction_water"
    )
    plt.close(fig)

    fig, _ = wf.plot_model_comparison()
    plt.close(fig)

    fig, _ = wf.plot_residuals_and_pareto_k()
    plt.close(fig)

    fig, _ = wf.plot_dataset_overview()
    plt.close(fig)


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_plot_posterior_inspection_helpers(tmp_path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    mixed_priors = PriorSet(
        parameters={
            "logA": NormalPriorSpec(loc=-21.0, scale=4.0),
            "Ea": UniformPriorSpec(low=10000.0, high=50000.0),
        },
        sigma_scale=0.1,
    )

    ds = _make_synthetic_dataset()
    wf = BayesianWorkflow(
        dataset=ds,
        models=[get_model("arrhenius")],
        priors=mixed_priors,
    )
    wf.fit(num_warmup=80, num_samples=80, num_chains=1, progress_bar=False)

    fig, _ = wf.plot_posterior("arrhenius")
    assert fig is not None
    plt.close(fig)

    fig, _ = wf.plot_trace("arrhenius")
    assert fig is not None
    plt.close(fig)

    fig, _ = wf.plot_pair("arrhenius")
    assert fig is not None
    plt.close(fig)

    fig, _ = wf.plot_prior_predictive("arrhenius")
    assert fig is not None
    plt.close(fig)

    fig, _ = wf.plot_prior_vs_posterior("arrhenius", "logA")
    assert fig is not None
    plt.close(fig)

    fig, _ = wf.plot_prior_vs_posterior("arrhenius", "Ea")
    assert fig is not None
    plt.close(fig)
