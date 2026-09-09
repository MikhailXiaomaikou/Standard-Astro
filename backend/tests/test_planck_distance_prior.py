"""planck2018_compressed correlated distance-prior execution (2026-07-07).

Before this upgrade the entry CLAIMED observables (R, l_A, ombh2, ns) but on
ΛCDM chains EXECUTED a diagonal (H0, Omega_m, sigma8, S8) parameter Gaussian.
Now every flat model (ΛCDM included) executes only the Chen-Huang-Wang 2019
(arXiv:1808.05724) Table-I 4-dim correlated distance prior. The registry's
H0/Omega_m/sigma8/S8 rows are posterior summaries used for proposals/context,
never additional likelihood factors. These tests fail on the pre-fix code:

- ΛCDM chi2 was the diagonal Gaussian, insensitive to ombh2/ns (tests 2, 3);
- the sampled axes had no ombh2/ns for ΛCDM (test 4);
- the extended-DE branch used a 3-dim (R, l_A, ombh2) prior without ns
  (test 6's ns sensitivity);
- missing distance-prior axes silently fell back to the diagonal Gaussian
  instead of failing loud (test 5).

Expected values are pinned to the paper table (source note below), per the
no-uncited-magic-numbers rule.
"""
from __future__ import annotations

import numpy as np

from app.services.cosmology_likelihoods.cmb import (
    _HS96_G1_COEF,
    _PLANCK18_BASELINE_OMNU_H2,
    _PLANCK18_DP_CORR,
    _PLANCK18_DP_MEAN,
    _PLANCK18_DP_SIGMA,
    _cmb_distance_priors,
    _compressed_chi2_samples,
    _hs96_decoupling_redshift,
)
from app.services.cosmology_likelihoods.registry import _REGISTRY

# ── Fixture: Chen, Huang & Wang 2019 (arXiv:1808.05724, JCAP 02 028) Table I,
# Planck 2018 TT,TE,EE+lowE, base ΛCDM. Visually verified against the
# published PDF (2026-07-07): R = 1.7502 ± 0.0046, l_A = 301.471 +0.089/-0.090
# (production symmetrizes to 0.090), ombh2 = 0.02236 ± 0.00015,
# n_s = 0.9649 ± 0.0043, with the printed correlation matrix.
CHW2019_TABLE1_MEAN = (1.7502, 301.471, 0.02236, 0.9649)
CHW2019_TABLE1_SIGMA = (0.0046, 0.090, 0.00015, 0.0043)
CHW2019_TABLE1_CORR = (
    (1.00, 0.46, -0.66, -0.74),
    (0.46, 1.00, -0.33, -0.35),
    (-0.66, -0.33, 1.00, 0.46),
    (-0.74, -0.35, 0.46, 1.00),
)
# CHW2019 appendix (~/cosmomc/data/Distance_invcov.txt): the UNNORMALIZED
# inverse covariance of the (R, l_A, ombh2) sub-block, machine precision.
CHW2019_APPENDIX_INVCOV3 = (
    (94392.3971, -1360.4913, 1664517.2916),
    (-1360.4913, 161.4349, 3671.6180),
    (1664517.2916, 3671.6180, 79719182.5162),
)


def _planck_entry():
    return _REGISTRY["planck2018_compressed"]


def _dp_chi2_reference(samples: np.ndarray, order: list[str], w0=-1.0, wa=0.0) -> np.ndarray:
    """Independent re-computation of the CHW2019 4-dim distance-prior chi2."""
    sigma = np.asarray(CHW2019_TABLE1_SIGMA)
    cov = sigma[:, None] * sigma[None, :] * np.asarray(CHW2019_TABLE1_CORR)
    inv = np.linalg.inv(cov)
    om = samples[:, order.index("omegam")]
    h0 = samples[:, order.index("H0")]
    obh2 = samples[:, order.index("ombh2")]
    ns = samples[:, order.index("ns")]
    big_r, l_a, _ = _cmb_distance_priors(om, h0, obh2, w0=w0, wa=wa)
    resid = np.column_stack([big_r, l_a, obh2, ns]) - np.asarray(CHW2019_TABLE1_MEAN)
    return np.einsum("ni,ij,nj->n", resid, inv, resid)


# ── 1. Production constants pinned to the paper ─────────────────────────────

def test_chw2019_table1_constants_pinned_to_paper():
    assert np.allclose(_PLANCK18_DP_MEAN, CHW2019_TABLE1_MEAN)
    assert np.allclose(_PLANCK18_DP_SIGMA, CHW2019_TABLE1_SIGMA)
    assert np.allclose(_PLANCK18_DP_CORR, CHW2019_TABLE1_CORR)
    # Correlation matrix must be symmetric positive definite.
    assert np.allclose(_PLANCK18_DP_CORR, np.asarray(_PLANCK18_DP_CORR).T)
    np.linalg.cholesky(np.asarray(_PLANCK18_DP_CORR))


def test_table1_reproduces_paper_appendix_inverse_covariance():
    """Provenance cross-check: inverting the (R, l_A, ombh2) sub-covariance
    built from Table I sigmas+correlations reproduces the machine-precision
    inverse the paper ships in its CosmoMC appendix.  Tolerances reflect the
    2-digit rounding of the printed correlations; the (l_A, ombh2) element is
    the rounding-dominated small one."""
    sigma3 = np.asarray(CHW2019_TABLE1_SIGMA[:3])
    corr3 = np.asarray(CHW2019_TABLE1_CORR)[:3, :3]
    inv3 = np.linalg.inv(sigma3[:, None] * sigma3[None, :] * corr3)
    paper = np.asarray(CHW2019_APPENDIX_INVCOV3)
    ratio = inv3 / paper
    for i in range(3):
        assert abs(ratio[i, i] - 1.0) < 0.05, (i, ratio[i, i])
    assert abs(ratio[0, 1] - 1.0) < 0.10
    assert abs(ratio[0, 2] - 1.0) < 0.10
    assert abs(ratio[1, 2] - 1.0) < 0.25  # tiny element, rounding-dominated


# ── 2/3. ΛCDM executes the correlated prior (fail-before: diagonal Gaussian) ─

LCDM_ORDER = ["H0", "omegam", "rd", "sigma8", "ombh2", "ns"]


def _lcdm_samples() -> np.ndarray:
    # Around the Planck 2018 baseline, with deliberate offsets on every axis.
    return np.array([
        [67.36, 0.3153, 147.0, 0.8111, 0.02236, 0.9649],
        [68.20, 0.3050, 148.0, 0.8000, 0.02260, 0.9700],
        [66.50, 0.3300, 146.0, 0.8250, 0.02200, 0.9580],
    ])


def test_lcdm_chi2_is_only_the_correlated_distance_prior():
    samples = _lcdm_samples()
    chi2, errors = _compressed_chi2_samples(samples, LCDM_ORDER, [_planck_entry()])
    assert errors == []
    expected = _dp_chi2_reference(samples, LCDM_ORDER)
    assert np.allclose(chi2, expected, rtol=1e-10), (chi2, expected)
    moved_sigma8 = samples.copy()
    moved_sigma8[:, LCDM_ORDER.index("sigma8")] += 0.2
    moved_chi2, moved_errors = _compressed_chi2_samples(
        moved_sigma8, LCDM_ORDER, [_planck_entry()]
    )
    assert moved_errors == []
    assert np.allclose(moved_chi2, chi2, rtol=1e-12)


def test_lcdm_chi2_responds_to_ombh2_and_ns():
    base = _lcdm_samples()[:1]
    moved_obh2 = base.copy()
    moved_obh2[0, LCDM_ORDER.index("ombh2")] += 3 * CHW2019_TABLE1_SIGMA[2]
    moved_ns = base.copy()
    moved_ns[0, LCDM_ORDER.index("ns")] += 3 * CHW2019_TABLE1_SIGMA[3]
    chi2_base, _ = _compressed_chi2_samples(base, LCDM_ORDER, [_planck_entry()])
    chi2_obh2, _ = _compressed_chi2_samples(moved_obh2, LCDM_ORDER, [_planck_entry()])
    chi2_ns, _ = _compressed_chi2_samples(moved_ns, LCDM_ORDER, [_planck_entry()])
    assert chi2_obh2[0] > chi2_base[0] + 1.0
    assert chi2_ns[0] > chi2_base[0] + 1.0


# ── 4. ΛCDM sampled axes include the distance-prior columns ─────────────────

def test_lcdm_sampling_parameter_order_includes_dp_axes():
    from app.services.cosmology_likelihoods.sampling import _sampling_parameter_order

    order = _sampling_parameter_order(
        [_REGISTRY["desi_dr1_bao"]], [_planck_entry()]
    )
    assert "ombh2" in order and "ns" in order, order
    assert "sigma8" not in order and "S8" not in order


# ── 5. Missing distance-prior axes fail loud, never silently degrade ────────

def test_missing_dp_axes_fail_loud_not_silent():
    order = ["H0", "omegam", "rd", "sigma8"]  # no ombh2 / ns
    samples = np.array([[67.36, 0.3153, 147.0, 0.8111]])
    chi2, errors = _compressed_chi2_samples(samples, order, [_planck_entry()])
    assert len(errors) == 1
    assert "ombh2" in errors[0] and "ns" in errors[0]
    # The failed entry contributes nothing rather than a silently different
    # likelihood (the caller demotes the chain on any invalid spec).
    assert np.allclose(chi2, 0.0)


# ── 6. Extended flat-DE keeps the prior and now carries the ns axis ─────────

def test_w0wa_chi2_uses_4dim_prior_with_ns():
    order = ["H0", "omegam", "rd", "w0", "wa", "sigma8", "ombh2", "ns"]
    samples = np.array([
        [67.0, 0.316, 147.5, -0.9, -0.3, 0.81, 0.02236, 0.9649],
        [68.0, 0.300, 148.5, -1.1, 0.2, 0.80, 0.02250, 0.9700],
    ])
    chi2, errors = _compressed_chi2_samples(samples, order, [_planck_entry()])
    assert errors == []
    w0 = samples[:, order.index("w0")]
    wa = samples[:, order.index("wa")]
    expected = _dp_chi2_reference(samples, order, w0=w0, wa=wa)
    assert np.allclose(chi2, expected, rtol=1e-10)
    # ns sensitivity (the pre-fix DE branch ran a 3-dim prior without ns).
    moved = samples.copy()
    moved[:, order.index("ns")] += 3 * CHW2019_TABLE1_SIGMA[3]
    chi2_moved, _ = _compressed_chi2_samples(moved, order, [_planck_entry()])
    assert np.all(chi2_moved > chi2 + 0.5)


# ── 7. Curved models keep the parameter-summary path (defensive control) ────

def test_curved_model_refuses_proposal_only_parameter_summary_path():
    order = ["H0", "omegam", "sigma8", "omegak"]
    samples = np.array([[67.36, 0.3153, 0.8111, 0.01]])
    chi2, errors = _compressed_chi2_samples(samples, order, [_planck_entry()])
    assert len(errors) == 1
    assert "proposal_only" in errors[0] and "context-only" in errors[0]
    assert np.allclose(chi2, 0.0)


# ── 8. Proposal moments are physically sensible (proposal-only helper) ──────

def test_dp_lcdm_proposal_moments_match_planck_lcdm_shape():
    # Imported lazily so the pre-fix code fails this test alone (helper
    # missing) instead of killing the whole module at collection.
    from app.services.cosmology_likelihoods.cmb import _planck_dp_lcdm_proposal_moments

    moments = _planck_dp_lcdm_proposal_moments()
    assert moments is not None
    names, mean, cov = moments
    assert names == ("H0", "omegam", "ombh2", "ns")
    sig = np.sqrt(np.diag(cov))
    corr = cov / np.outer(sig, sig)
    # The linearized image of the CHW2019 prior must look like the Planck
    # ΛCDM posterior: H0 ~ 67.3 ± 0.6, Om ~ 0.316 ± 0.009, strong H0-Om
    # anticorrelation. Loose windows — this is a proposal sanity check.
    assert 66.5 < mean[0] < 68.5
    assert 0.30 < mean[1] < 0.33
    assert 0.3 < sig[0] < 1.2
    assert corr[0, 1] < -0.9
    np.linalg.cholesky(cov)


# ── 9. Integration: ΛCDM BAO+CMB anchor stays numerically correct/preliminary ─

def test_lcdm_bao_cmb_recovers_h0_preliminary_tier():
    from app.services.cosmology_likelihoods import run_likelihood_chain

    r = run_likelihood_chain(
        model="lcdm",
        dataset_keys=["desi_dr1_bao", "planck2018_compressed"],
        n_samples=4000,
        random_seed=42,
    )
    assert r["chain_tier"] == "exploratory"
    assert r["publication_ready"] is False
    assert r["preliminary_ready"] is True
    assert "compressed_or_approximate_likelihood" in r["preliminary_reasons"]
    ess = float(r["chain_diagnostics"]["proposal_ess"])
    assert ess >= 400.0, ess
    h0 = float(r["parameters"]["H0"]["median"])
    assert 66.5 < h0 < 68.5, h0
    # The distance-prior axes are now real sampled posteriors.
    assert "ombh2" in r["parameters"] and "ns" in r["parameters"]
    obh2 = float(r["parameters"]["ombh2"]["median"])
    assert 0.0215 < obh2 < 0.0232, obh2
    ns = float(r["parameters"]["ns"]["median"])
    assert 0.95 < ns < 0.98, ns
    # Distance priors carry geometry/baryon/tilt information, not a growth
    # amplitude. The Planck VI sigma8/S8 posterior rows are context-only.
    assert "sigma8" not in r["parameters"]
    assert "S8" not in r["derived_params"]


# ── 10. Compression recipe reproduces Table I at the Planck 2018 means ───────
#
# Planck 2018 VI (arXiv:1807.06209) Table 2, base ΛCDM 68% means:
#   TT,TE,EE+lowE          Omega_m = 0.3166, H0 = 67.27, omega_b h^2 = 0.02236
#   TT,TE,EE+lowE+lensing  Omega_m = 0.3153, H0 = 67.36, omega_b h^2 = 0.02237
# CHW2019 Table I was derived from the TT,TE,EE+lowE base-ΛCDM chain, so the
# kernel evaluated at that column's means must land on the Table-I means to
# well inside one sigma (the mean of a smooth function of the chain differs
# from the function of the means only at second order, ~0.01 in l_A).
# The +lensing column is a second anchor of the same recipe.
#
# Recipe audit (2026-09-09, CAMB 1.6.6 reference, see cmb.py constants):
# the pre-fix kernel (Hu-Sugiyama g1 prefactor 0.0738, massive neutrino inside
# the sound-horizon matter term) sat at l_A = 301.554 / 301.549 — +0.08
# (+0.9 sigma) above Table I at both columns. With the published 0.0783 and
# the Planck-baseline neutrino removed from r_s the kernel gives 301.457 /
# 301.452 (-0.15 / -0.22 sigma). A 0.03 tolerance (one third of sigma_lA)
# therefore fails before the fix and passes after it.
PLANCK18_BASE_LCDM_MEANS = {
    "TT,TE,EE+lowE": (0.3166, 67.27, 0.02236),
    "TT,TE,EE+lowE+lensing": (0.3153, 67.36, 0.02237),
}
RECIPE_TOL_R = 0.0015  # ~1/3 of sigma_R = 0.0046
RECIPE_TOL_LA = 0.03   # ~1/3 of sigma_lA = 0.090


def test_recipe_reproduces_table1_at_planck_means():
    for label, (om, h0, obh2) in PLANCK18_BASE_LCDM_MEANS.items():
        big_r, l_a, _ = _cmb_distance_priors(om, h0, obh2)
        assert abs(big_r - CHW2019_TABLE1_MEAN[0]) < RECIPE_TOL_R, (label, big_r)
        assert abs(l_a - CHW2019_TABLE1_MEAN[1]) < RECIPE_TOL_LA, (label, l_a)


def test_recipe_constants_pinned_to_sources():
    # Hu & Sugiyama 1996 Eq. E-1 / Komatsu+2009 Eq. 66 / CHW2019 Eq. 9 prefactor.
    assert _HS96_G1_COEF == 0.0783
    # Planck 2018 baseline: sum m_nu = 0.06 eV, omega_nu h^2 = sum(m_nu)/93.14 eV.
    assert abs(_PLANCK18_BASELINE_OMNU_H2 - 0.06 / 93.14) < 1e-12
    # Independent evaluation of the fit at the TT,TE,EE+lowE means.  The
    # fitting formula sits ~2 above CAMB's z* = 1089.92 (Planck 2018 Table 2);
    # that offset is part of the published recipe and must not be "corrected".
    obh2, omh2 = 0.02236, 0.3166 * (67.27 / 100.0) ** 2
    g1 = 0.0783 * obh2 ** -0.238 / (1.0 + 39.5 * obh2 ** 0.763)
    g2 = 0.560 / (1.0 + 21.1 * obh2 ** 1.81)
    expected = 1048.0 * (1.0 + 0.00124 * obh2 ** -0.738) * (1.0 + g1 * omh2 ** g2)
    zstar = float(_hs96_decoupling_redshift(obh2, omh2))
    assert abs(zstar - expected) < 1e-9
    assert 1091.5 < zstar < 1092.5, zstar


def test_recipe_neutrino_term_only_touches_sound_horizon():
    """Removing the Planck-baseline neutrino from the r_s matter term must
    raise l_A (smaller H before decoupling -> larger r_s -> smaller l_A...
    the sign is fixed by physics: less matter at z* means a LARGER sound
    horizon and hence a SMALLER l_A) while leaving R, which only sees the
    late-time D_M, untouched to first order."""
    from app.services.cosmology_likelihoods import cmb as cmb_mod

    om, h0, obh2 = PLANCK18_BASE_LCDM_MEANS["TT,TE,EE+lowE"]
    r_with, la_with, _ = _cmb_distance_priors(om, h0, obh2)
    saved = cmb_mod._PLANCK18_BASELINE_OMNU_H2
    try:
        cmb_mod._PLANCK18_BASELINE_OMNU_H2 = 0.0
        r_without, la_without, _ = _cmb_distance_priors(om, h0, obh2)
    finally:
        cmb_mod._PLANCK18_BASELINE_OMNU_H2 = saved
    assert abs(r_with - r_without) < 1e-9
    assert la_without > la_with + 0.2  # ~+0.36 at Planck values
