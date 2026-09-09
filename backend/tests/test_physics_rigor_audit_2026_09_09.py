"""Behavioural pins for the 2026-09-09 physics-rigor audit fixes.

A3  BAO+CMB compressed runs declare that r_d is a free nuisance parameter and
    are no longer mislabelled "BAO-only" (planck2018_compressed has probe
    "cmb_compressed", which the old probe == "cmb" test missed).
B2  An unverified ESS is a named publication-gate reason and an explicit
    chain_diagnostics flag; the tier stays exploratory by design.
B4  A posterior that merely fills its flat prior (rd in a BAO-only run) is
    flagged by the prior-dominance screen.
B6  emcee runs label whether the autocorrelation estimate is reliable
    (walkers >= 50 autocorrelation times long).
"""
from __future__ import annotations

import numpy as np
import pytest

import app.services.cosmology_likelihoods as cl
from app.services.cosmology_likelihoods.sampling import _prior_dominance_screen


def _bao_cmb():
    return cl.run_likelihood_chain(
        model="lcdm",
        dataset_keys=["desi_dr1_bao", "planck2018_compressed"],
        n_samples=2000,
        random_seed=42,
    )


def test_bao_cmb_declares_free_rd_and_is_not_called_bao_only():
    r = _bao_cmb()
    joined = "\n".join(r["warnings"])
    assert "BAO+CMB modelling choice" in joined
    assert "free nuisance parameter" in joined
    assert "NOT tied to the CMB" in joined
    # Fail-before: the old probe == "cmb" test fired the BAO-only caveat here.
    assert "BAO-only H0 and rd constraints" not in joined
    assert "rd" in r["parameters"]


def test_bao_only_still_carries_the_bao_only_caveat_and_flags_rd_as_prior_filled():
    r = cl.run_likelihood_chain(
        model="lcdm", dataset_keys=["desi_dr1_bao"], n_samples=3000, random_seed=3
    )
    joined = "\n".join(r["warnings"])
    assert "BAO-only H0 and rd constraints" in joined
    assert "BAO+CMB modelling choice" not in joined
    screen = r["prior_dominance_screen"]
    # Only H0*rd is measured by BAO alone: rd fills its flat prior box.
    assert "rd" in screen["flagged_parameters"], screen
    rd = screen["parameters"]["rd"]
    assert "posterior_indistinguishable_from_flat_prior" in rd["reasons"]
    assert rd["hdi94_width_fraction_of_prior"] >= 0.9
    assert "prior_dominance_screen_failed" in r["preliminary_reasons"]
    # A genuinely constrained parameter is not flagged by the new rule.
    om = screen["parameters"]["omegam"]
    assert "posterior_indistinguishable_from_flat_prior" not in om["reasons"]


def test_prior_dominance_screen_flags_flat_posterior_only():
    rng = np.random.default_rng(0)
    flat = rng.uniform(130.0, 170.0, 5000)
    peaked = np.clip(rng.normal(150.0, 3.0, 5000), 130.0, 170.0)
    samples = np.column_stack([flat, peaked])
    out = _prior_dominance_screen(
        samples, ["rd", "H0"], {"rd": (130.0, 170.0), "H0": (130.0, 170.0)}
    )
    assert out["flagged_parameters"] == ["rd"]
    assert out["parameters"]["rd"]["reasons"] == ["posterior_indistinguishable_from_flat_prior"]
    assert out["parameters"]["H0"]["status"] == "screen_passed"
    assert out["parameters"]["H0"]["hdi94_width_fraction_of_prior"] < 0.5


def test_unverified_ess_is_a_named_gate_reason_and_flag(monkeypatch):
    import emcee

    def boom(self, **kw):
        raise RuntimeError("chain too short")

    monkeypatch.setattr(emcee.EnsembleSampler, "get_autocorr_time", boom)
    r = cl._run_sampling_likelihood_chain(
        model_key="lcdm", entries=[cl.get_cosmology_dataset("union3")],
        priors=None, seed=42, sample_count=1500, allow_emcee_fallback=True,
    )
    assert r["sampler"] == "sn_emcee"
    assert r["chain_tier"] == "exploratory"  # unchanged by design (see sampling.py)
    assert "effective_sample_size_unverified" in r["publication_gate"]["reasons"]
    assert "effective_sample_size_unverified" in r["preliminary_reasons"]
    d = r["chain_diagnostics"]
    assert d["ess_verified"] is False
    assert d["ess_source"] == "autocorr_failed"
    assert d["autocorr_estimate_reliable"] is None
    assert d["autocorr_chain_length_in_tau"] is None


def test_emcee_run_labels_autocorr_reliability():
    r = cl._run_sampling_likelihood_chain(
        model_key="lcdm", entries=[cl.get_cosmology_dataset("union3")],
        priors=None, seed=42, sample_count=1500, allow_emcee_fallback=True,
    )
    d = r["chain_diagnostics"]
    assert r["sampler"] == "sn_emcee"
    assert d["ess_verified"] is True
    assert "effective_sample_size_unverified" not in r["publication_gate"]["reasons"]
    assert isinstance(d["autocorr_chain_length_in_tau"], float)
    # ess / n_walkers (union3 lcdm: 3 parameters -> 32 walkers); field is rounded to 2 dp.
    assert d["autocorr_chain_length_in_tau"] == pytest.approx(
        d["proposal_ess"] / max(2 * 3 + 2, 32), abs=0.006
    )
    assert d["autocorr_estimate_reliable"] is (d["autocorr_chain_length_in_tau"] >= 50.0)
    if not d["autocorr_estimate_reliable"]:
        assert any("autocorrelation-time estimate" in w for w in r["warnings"])


def test_importance_runs_do_not_carry_emcee_autocorr_fields_as_true():
    r = _bao_cmb()
    d = r["chain_diagnostics"]
    assert d["ess_source"] == "importance_weights"
    assert d["ess_verified"] is True
    assert d["autocorr_estimate_reliable"] is None


def test_unreliable_autocorr_estimate_marks_ess_unverified(monkeypatch):
    """Codex review on #81: an emcee ESS whose autocorrelation time rests on
    walkers shorter than the required chain length is explicitly unreliable
    and must not be reported as verified (flag + named gate reason)."""
    from app.services.cosmology_likelihoods import sampling as sampling_mod

    monkeypatch.setattr(sampling_mod, "_EMCEE_AUTOCORR_RELIABLE_CHAIN_LENGTHS", 1e9)
    r = cl._run_sampling_likelihood_chain(
        model_key="lcdm", entries=[cl.get_cosmology_dataset("union3")],
        priors=None, seed=42, sample_count=1500, allow_emcee_fallback=True,
    )
    d = r["chain_diagnostics"]
    assert r["sampler"] == "sn_emcee"
    assert d["autocorr_estimate_reliable"] is False
    assert d["ess_verified"] is False
    assert d["proposal_ess"] is not None  # the estimate itself is still reported
    assert "effective_sample_size_unverified" in r["publication_gate"]["reasons"]
    assert r["publication_ready"] is False
    assert r["chain_tier"] == "exploratory"
    assert any("optimistic estimate" in w for w in r["warnings"])

