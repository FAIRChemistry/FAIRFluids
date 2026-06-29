"""Tests for the symbolic models (``analysis.models``) and fit backends
(``analysis.fit``).

These never touch the codegen-based ``analysis.bayesian`` / ``analysis.regression``
model registries. The Bayesian test is skipped when the ``[bayesian]`` extra
(jax/numpyro) is unavailable.
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest
import sympy as sp

from fairfluids.analysis import fit as _fit_pkg
from fairfluids.analysis import models as _models_pkg

# The model authoring/registry API lives in ``analysis.models`` and the fit
# backends in ``analysis.fit``; this test exercises both, so merge their public
# namespaces into one handle.
fx = SimpleNamespace(**{**vars(_models_pkg), **vars(_fit_pkg)})


# --- fixtures -----------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_registry():
    fx.registry.clear()
    yield
    fx.registry.clear()


def _vft_model():
    T, A, B, T0 = sp.symbols("T A B T0")
    return fx.define_model(
        "vft", property="viscosity",
        expr=sp.exp(A + B / (T - T0)), features=["T"],
        p0={"A": -5.0, "B": 700.0, "T0": 150.0},
        overwrite=True,
    )


# --- role detection -----------------------------------------------------------


def test_role_detection_partitions_symbols():
    m = _vft_model()
    assert m.features == ("T",)
    assert m.param_names == ("A", "B", "T0")
    assert m.constant_names == ()
    assert m.arg_order == ("T", "A", "B", "T0")


def test_mean_expr_collapses_log_of_exp():
    m = _vft_model()
    T, A, B, T0 = sp.symbols("T A B T0")
    assert sp.simplify(m.mean_expr - (A + B / (T - T0))) == 0


def test_unknown_feature_raises():
    A, B = sp.symbols("A B")
    with pytest.raises(ValueError, match="do not appear"):
        fx.define_model("bad", property="x", expr=A + B, features=["Z"], register=False)


def test_no_free_parameters_raises():
    T = sp.symbols("T")
    with pytest.raises(ValueError, match="no free parameters"):
        fx.define_model("bad", property="x", expr=2 * T, features=["T"], register=False)


# --- compile ------------------------------------------------------------------


def test_compile_numpy_matches_manual():
    m = _vft_model()
    fn = fx.compile_numpy(m)
    T = np.array([300.0, 320.0])
    got = fn(T, -5.0, 700.0, 150.0)  # arg_order: T, A, B, T0
    expected = -5.0 + 700.0 / (T - 150.0)
    np.testing.assert_allclose(got, expected)


# --- registry / authoring -----------------------------------------------------


def test_define_model_registers_and_overwrite():
    _vft_model()
    assert "vft" in fx.list_models()
    with pytest.raises(ValueError, match="already registered"):
        _vft_model_no_overwrite()


def _vft_model_no_overwrite():
    T, A, B, T0 = sp.symbols("T A B T0")
    return fx.define_model(
        "vft", property="viscosity",
        expr=sp.exp(A + B / (T - T0)), features=["T"],
    )


def test_define_model_from_string_expr():
    m = fx.define_model(
        "vft_str", property="viscosity",
        expr="exp(A + B/(T - T0))", features=["T"], overwrite=True,
    )
    assert m.param_names == ("A", "B", "T0")


# --- JSON round-trip ----------------------------------------------------------


def test_json_round_trip_preserves_expression_and_roles():
    m = _vft_model()
    data = fx.to_dict(m)
    m2 = fx.from_dict(data)
    assert m2.param_names == m.param_names
    assert m2.features == m.features
    assert m2.log_observation == m.log_observation
    assert sp.simplify(m2.expr - m.expr) == 0


def test_parse_expression_rejects_unknown_function():
    with pytest.raises(ValueError, match="unknown function"):
        fx.parse_expression("foo(A + B)")


# --- constants (the density-anchored case) ------------------------------------


def _density_anchored_model():
    T, T0, rho0, A1, A2 = sp.symbols("T T0 rho0 A1 A2")
    expr = rho0 * sp.exp(-(A1 * (T - T0) + sp.Rational(1, 2) * A2 * (T**2 - T0**2)))
    return fx.define_model(
        "rho_anchored", property="density", expr=expr, features=["T"],
        constants={"T0": {"kind": "mean", "feature": "T"},
                   "rho0": {"kind": "interp", "feature": "T"}},
        p0={"A1": 7e-4, "A2": 1e-6}, overwrite=True,
    )


def test_constants_shrink_params_and_resolve_from_data():
    m = _density_anchored_model()
    assert m.param_names == ("A1", "A2")
    assert m.constant_names == ("T0", "rho0")

    T = np.array([283.15, 293.15, 303.15, 313.15])
    rho = np.array([998.0, 996.0, 992.0, 988.0])
    consts = fx.resolvers.resolve_constants(m.constants, {"T": T}, rho)
    assert consts["T0"] == pytest.approx(np.mean(T))
    # rho0 interpolated at the mean temperature (298.15) -> between 996 and 992
    assert 992.0 < consts["rho0"] < 996.0


# --- regression recovery ------------------------------------------------------


def test_least_squares_recovers_known_vft_parameters():
    m = _vft_model()
    A_true, B_true, T0_true = -5.0, 700.0, 150.0
    T = np.linspace(280.0, 360.0, 40)
    eta = np.exp(A_true + B_true / (T - T0_true))

    fit = fx.fit_least_squares(m, {"T": T}, eta)
    assert fit.success
    vals = fit.values()
    assert vals["A"] == pytest.approx(A_true, abs=1e-3)
    assert vals["B"] == pytest.approx(B_true, rel=1e-3)
    assert vals["T0"] == pytest.approx(T0_true, abs=1e-2)
    assert fit.r_squared > 0.999


def test_least_squares_with_fixed_constant():
    T, T0, rho0, A1 = sp.symbols("T T0 rho0 A1")
    m = fx.define_model(
        "rho_lin", property="density",
        expr=rho0 * sp.exp(-A1 * (T - T0)), features=["T"],
        constants={"T0": 298.15, "rho0": 997.0}, p0={"A1": 3e-4},
        overwrite=True,
    )
    A1_true = 3.5e-4
    Tarr = np.linspace(283.0, 333.0, 30)
    rho = 997.0 * np.exp(-A1_true * (Tarr - 298.15))
    fit = fx.fit_least_squares(m, {"T": Tarr}, rho)
    assert fit.success
    assert fit.constants == {"T0": 298.15, "rho0": 997.0}
    assert fit.values()["A1"] == pytest.approx(A1_true, rel=1e-4)


# --- convenience adapters (fit_group / fit_dataset) ---------------------------


def _fake_group(label="g", feature_col="T", log=True):
    """A duck-typed BayesianGroup: just the attributes the adapters read."""
    from types import SimpleNamespace

    A_true, B_true, T0_true = -5.0, 700.0, 150.0
    T = np.linspace(280.0, 360.0, 40)
    eta = np.exp(A_true + B_true / (T - T0_true))
    return SimpleNamespace(
        group_label=label,
        features={feature_col: T},
        raw_observation=eta,
        raw_observation_uncertainty=None,
        log_observation=log,
        observation=np.log(eta),  # the trap: log-scaled; adapter must ignore it
    )


def test_fit_group_recovers_parameters_from_raw_observation():
    m = _vft_model()
    fit = fx.fit_group(m, _fake_group())
    assert fit.success
    vals = fit.values()
    assert vals["A"] == pytest.approx(-5.0, abs=1e-3)
    assert vals["B"] == pytest.approx(700.0, rel=1e-3)
    assert fit.r_squared > 0.999


def test_fit_group_honours_feature_map_alias():
    m = _vft_model()
    grp = _fake_group(feature_col="temperature")
    fit = fx.fit_group(m, grp, feature_map={"T": "temperature"})
    assert fit.success
    assert fit.r_squared > 0.999


def test_fit_group_missing_feature_raises_helpful_error():
    m = _vft_model()
    grp = _fake_group(feature_col="temperature")  # model wants 'T', no map given
    with pytest.raises(KeyError, match="feature_map"):
        fx.fit_group(m, grp)


def test_fit_group_log_mismatch_is_rejected():
    m = _vft_model()  # log_observation=True
    grp = _fake_group(log=False)
    with pytest.raises(ValueError, match="log_observation mismatch"):
        fx.fit_group(m, grp)


def test_fit_group_unknown_backend_raises():
    m = _vft_model()
    with pytest.raises(ValueError, match="Unknown backend"):
        fx.fit_group(m, _fake_group(), backend="nope")


def test_fit_dataset_aggregates_and_tabulates():
    from types import SimpleNamespace

    m = _vft_model()
    ds = SimpleNamespace(groups=[_fake_group("a"), _fake_group("b")])
    res = fx.fit_dataset(m, ds)
    assert len(res) == 2
    assert res.n_failed == 0
    frame = res.to_frame()
    assert set(frame["group_label"]) == {"a", "b"}
    assert {"A", "A_std", "B", "r_squared"}.issubset(frame.columns)


def test_fit_dataset_collects_failures_without_raising():
    from types import SimpleNamespace

    m = _vft_model()
    broken = SimpleNamespace(group_label="broken")  # no features/raw_observation
    ds = SimpleNamespace(groups=[_fake_group("ok"), broken])
    res = fx.fit_dataset(m, ds)
    assert len(res) == 1
    assert "broken" in res.failures


def test_fit_dataset_on_error_raise_propagates():
    from types import SimpleNamespace

    m = _vft_model()
    broken = SimpleNamespace(group_label="broken")
    ds = SimpleNamespace(groups=[broken])
    with pytest.raises((AttributeError, TypeError)):
        fx.fit_dataset(m, ds, on_error="raise")


# --- jax gradient parity (light, no MCMC) -------------------------------------


def test_jax_mean_is_differentiable_and_matches_sympy():
    jax = pytest.importorskip("jax")
    m = _vft_model()
    fn = fx.compile_jax(m)

    def loss(A, B, T0):
        return fn(300.0, A, B, T0).sum()

    grad = jax.grad(loss, argnums=(0, 1, 2))(-5.0, 700.0, 150.0)
    T, A, B, T0 = sp.symbols("T A B T0")
    subs = {T: 300, A: -5.0, B: 700.0, T0: 150.0}
    exact = [float(sp.diff(m.mean_expr, s).subs(subs)) for s in (A, B, T0)]
    np.testing.assert_allclose([float(g) for g in grad], exact, rtol=1e-5)


# --- bayesian (skipped without [bayesian]) ------------------------------------


def test_mcmc_recovers_vft_parameters():
    pytest.importorskip("numpyro")
    from fairfluids.analysis.bayesian.priors import (
        NormalPriorSpec,
        TruncatedNormalPriorSpec,
        UniformPriorSpec,
    )

    m = _vft_model()
    A_true, B_true, T0_true = -5.0, 700.0, 150.0
    T = np.linspace(280.0, 360.0, 40)
    eta = np.exp(A_true + B_true / (T - T0_true))

    priors = {
        "A": NormalPriorSpec(loc=-5.0, scale=3.0),
        "B": TruncatedNormalPriorSpec(loc=700.0, scale=400.0, low=0.0),
        "T0": UniformPriorSpec(low=50.0, high=200.0),
    }
    mcmc = fx.fit_mcmc(
        m, {"T": T}, eta, priors=priors,
        num_warmup=400, num_samples=400, num_chains=1, seed=0,
    )
    samples = mcmc.get_samples()
    assert float(np.median(samples["A"])) == pytest.approx(A_true, abs=0.5)
    assert float(np.median(samples["B"])) == pytest.approx(B_true, rel=0.15)
