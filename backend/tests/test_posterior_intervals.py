"""hdi_low_94 / hdi_high_94 must be a highest-density interval, not the 3rd/97th
percentiles (2026-09-09 physics-rigor audit, finding B1).

Fail-before: on a skewed posterior the percentile pair is wider than the HDI
and does not match ArviZ; every runner that filled the fields with
np.percentile(values, [3, 97]) therefore mislabelled an equal-tailed interval
as an HDI."""
from __future__ import annotations

import numpy as np
import pytest

from app.services.posterior_intervals import equal_tailed_interval, hdi_interval

az = pytest.importorskip("arviz")


def _skewed(n: int = 20000, seed: int = 3) -> np.ndarray:
    return np.random.default_rng(seed).lognormal(mean=0.0, sigma=0.9, size=n)


def test_hdi_matches_arviz_on_skewed_samples():
    x = _skewed()
    low, high = hdi_interval(x, 0.94)
    ref = az.hdi(x, hdi_prob=0.94)
    assert abs(low - float(ref[0])) < 1e-9
    assert abs(high - float(ref[1])) < 1e-9


def test_hdi_is_narrower_than_equal_tailed_interval_when_skewed():
    x = _skewed()
    hlo, hhi = hdi_interval(x, 0.94)
    elo, ehi = equal_tailed_interval(x, 0.94)
    assert (hhi - hlo) < 0.9 * (ehi - elo)
    # The HDI of a right-skewed posterior hugs the mode: it starts lower than
    # the 3rd percentile and ends below the 97th.
    assert hlo < elo and hhi < ehi


def test_hdi_close_to_eti_when_symmetric():
    x = np.random.default_rng(0).normal(5.0, 2.0, 40000)
    hlo, hhi = hdi_interval(x)
    elo, ehi = equal_tailed_interval(x)
    assert abs(hlo - elo) < 0.1 and abs(hhi - ehi) < 0.1
    # N(5, 2): 94% interval ≈ 5 ± 1.881*2
    assert 1.0 < hlo < 1.4 and 8.6 < hhi < 9.0


def test_hdi_contains_requested_mass_and_handles_degenerate_input():
    x = np.random.default_rng(1).uniform(130.0, 170.0, 10000)
    low, high = hdi_interval(x, 0.94)
    inside = np.mean((x >= low) & (x <= high))
    assert 0.935 <= inside <= 0.945
    assert 0.92 * 40.0 < (high - low) < 0.96 * 40.0
    assert hdi_interval([]) == pytest.approx((np.nan, np.nan), nan_ok=True)
    assert hdi_interval([1.5]) == (1.5, 1.5)
    assert hdi_interval([2.0, np.nan, 1.0]) == (1.0, 2.0)
    with pytest.raises(ValueError):
        hdi_interval(x, 1.0)


def test_sampling_posterior_summary_reports_true_hdi():
    from app.services.cosmology_likelihoods.sampling import _posterior_summary

    x = _skewed(5000, seed=11)
    summary = _posterior_summary(x)
    ref = az.hdi(x, hdi_prob=0.94)
    assert summary["hdi_low_94"] == pytest.approx(float(ref[0]), abs=1e-5)
    assert summary["hdi_high_94"] == pytest.approx(float(ref[1]), abs=1e-5)
    assert summary["hdi_94"] == [summary["hdi_low_94"], summary["hdi_high_94"]]
    p3, p97 = np.percentile(x, [3.0, 97.0])
    assert summary["hdi_high_94"] < p97 - 0.05


def test_chain_diagnostics_reports_true_hdi():
    from app.services.chain_diagnostics import evaluate_chain_diagnostics

    rng = np.random.default_rng(5)
    chains = [rng.lognormal(0.0, 0.9, 3000) for _ in range(4)]
    # The tool takes JSON-style nested lists (one list per chain).
    out = evaluate_chain_diagnostics(chains={"x": [c.tolist() for c in chains]})
    assert out["success"] is True, out.get("error")
    flat = np.concatenate(chains)
    ref = az.hdi(flat, hdi_prob=0.94)
    item = out["parameters"]["x"]
    assert item["hdi_low_94"] == pytest.approx(float(ref[0]), abs=1e-5)
    assert item["hdi_high_94"] == pytest.approx(float(ref[1]), abs=1e-5)
