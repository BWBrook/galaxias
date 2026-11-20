import math

import numpy as np
import pytest

from galaxias_model.age_joint_proposal import (
    DEFAULT_JOINT_KAPPAS,
    draw_joint_beta,
    fit_joint_beta,
    joint_log_density_ratio,
)


def test_fit_preserves_positive_centres_and_serializable_normalized_weights():
    fit = fit_joint_beta([[0.1, 0.2], [0.3, 0.4], [0.1, 0.2]], [2, 0, 1])
    assert fit["dimension"] == 2
    assert fit["kappas"] == list(DEFAULT_JOINT_KAPPAS)
    assert fit["centres"] == [[0.1, 0.2], [0.1, 0.2]]
    assert fit["weights"] == pytest.approx([2 / 3, 1 / 3])
    assert isinstance(fit["centres"], list)
    assert all(isinstance(value, float) for row in fit["centres"] for value in row)
    assert all(isinstance(value, float) for value in fit["weights"])


def test_one_dimensional_edge_centre_has_analytic_endpoint_density():
    fit = fit_joint_beta([[0.0]], [1.0], kappas=(1.0,))
    # Beta(1, 2) has density 2 at zero and zero at one.
    assert joint_log_density_ratio(fit, [0.0]) == pytest.approx(math.log(0.5 + 0.5 * 2.0))
    assert joint_log_density_ratio(fit, [1.0]) == pytest.approx(math.log(0.5))


def test_joint_mixture_is_not_coordinatewise_mixture():
    fit = fit_joint_beta([[0.0, 0.0], [1.0, 1.0]], [1.0, 1.0])
    unit = np.array([0.25, 0.75])
    actual = math.exp(joint_log_density_ratio(fit, unit))
    # The joint mixture averages products; a coordinatewise mixture multiplies
    # averaged marginals and therefore gives a different dependence structure.
    def beta_pdf(x, a, b):
        return math.exp((a - 1) * math.log(x) + (b - 1) * math.log1p(-x)
                        - math.lgamma(a) - math.lgamma(b) + math.lgamma(a + b))

    kernel_joint = sum(
        0.5 * (
            beta_pdf(unit[0], 1.0, 1.0 + kappa)
            * beta_pdf(unit[1], 1.0, 1.0 + kappa)
            + beta_pdf(unit[0], 1.0 + kappa, 1.0)
            * beta_pdf(unit[1], 1.0 + kappa, 1.0)
        )
        for kappa in DEFAULT_JOINT_KAPPAS
    ) / len(DEFAULT_JOINT_KAPPAS)
    kernel_coordinatewise = (
        0.5 * sum(beta_pdf(unit[0], 1.0, 1.0 + kappa) for kappa in DEFAULT_JOINT_KAPPAS) / len(DEFAULT_JOINT_KAPPAS)
        + 0.5 * sum(beta_pdf(unit[0], 1.0 + kappa, 1.0) for kappa in DEFAULT_JOINT_KAPPAS) / len(DEFAULT_JOINT_KAPPAS)
    ) * (
        0.5 * sum(beta_pdf(unit[1], 1.0, 1.0 + kappa) for kappa in DEFAULT_JOINT_KAPPAS) / len(DEFAULT_JOINT_KAPPAS)
        + 0.5 * sum(beta_pdf(unit[1], 1.0 + kappa, 1.0) for kappa in DEFAULT_JOINT_KAPPAS) / len(DEFAULT_JOINT_KAPPAS)
    )
    assert actual == pytest.approx(0.5 + 0.5 * kernel_joint)
    assert actual != pytest.approx(0.5 + 0.5 * kernel_coordinatewise)


def test_density_normalizes_under_deterministic_one_dimensional_quadrature():
    fit = fit_joint_beta([[0.35]], [1.0])
    grid = (np.arange(200_000, dtype=float) + 0.5) / 200_000
    densities = np.exp([joint_log_density_ratio(fit, [value]) for value in grid])
    assert float(np.mean(densities)) == pytest.approx(1.0, abs=2e-5)


def test_boundaries_are_finite_and_uniform_component_gives_g_over_q_bound():
    fit = fit_joint_beta([np.zeros(16), np.ones(16)], [1.0, 1.0])
    for unit in (np.zeros(16), np.ones(16), np.r_[np.zeros(15), 1.0]):
        log_ratio = joint_log_density_ratio(fit, unit)
        assert math.isfinite(log_ratio)
        assert math.exp(-log_ratio) <= 2.0 + 1e-12


def test_zero_weights_use_uniform_fallback():
    fit = fit_joint_beta(np.empty((0, 3)), [])
    assert fit["fallback_uniform"]
    assert fit["centres"] == []
    assert fit["weights"] == []
    assert joint_log_density_ratio(fit, [0.0, 0.5, 1.0]) == 0.0
    unit, log_ratio, component = draw_joint_beta(fit, np.random.default_rng(7))
    assert unit.shape == (3,)
    assert component == "uniform"
    assert log_ratio == 0.0


def test_weighted_centre_selection_and_reproducibility():
    fit = fit_joint_beta([[0.1], [0.9]], [9.0, 1.0])
    rng_a = np.random.default_rng(1234)
    draws_a = [draw_joint_beta(fit, rng_a) for _ in range(8_000)]
    selected = [component for _, _, component in draws_a if component != "uniform"]
    assert selected
    assert sum("centre_0" in component for component in selected) / len(selected) == pytest.approx(0.9, abs=0.025)

    rng_b = np.random.default_rng(99)
    rng_c = np.random.default_rng(99)
    for _ in range(30):
        draw_b = draw_joint_beta(fit, rng_b)
        draw_c = draw_joint_beta(fit, rng_c)
        np.testing.assert_array_equal(draw_b[0], draw_c[0])
        assert draw_b[1:] == draw_c[1:]


def test_malformed_inputs_are_rejected():
    with pytest.raises(ValueError):
        fit_joint_beta([[0.0, 0.5]], [1.0, 2.0])
    with pytest.raises(ValueError):
        fit_joint_beta([[0.0, np.nan]], [1.0])
    with pytest.raises(ValueError):
        fit_joint_beta([[0.0, 1.1]], [1.0])
    with pytest.raises(ValueError):
        fit_joint_beta([[0.0]], [-1.0])

    fit = fit_joint_beta([[0.25, 0.75]], [1.0])
    with pytest.raises(ValueError):
        joint_log_density_ratio(fit, [0.5])
    with pytest.raises(ValueError):
        joint_log_density_ratio(fit, [0.5, math.inf])
    with pytest.raises(ValueError):
        joint_log_density_ratio({**fit, "kappas": []}, [0.25, 0.75])
    with pytest.raises(TypeError):
        draw_joint_beta(fit, rng=np.random.RandomState(1))
