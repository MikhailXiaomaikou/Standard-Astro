"""Compressed CMB distance priors and compressed-Gaussian chi^2.

Split verbatim out of the pre-2026-07-03 single-file
app/services/cosmology_likelihoods.py (7,757 lines). Import the package
``app.services.cosmology_likelihoods`` — it re-exports every pre-split name
and keeps the original one-namespace monkeypatch semantics.
"""

from __future__ import annotations


import hashlib
import pathlib
from typing import Any

import numpy as np

from app.services.cosmology_likelihoods.core import (
    CosmologyDatasetEntry,
    compressed_rows_are_executable,
    _derived_s8_from_samples,
    _s8_is_derived,
)

from app.services.cosmology_likelihoods.distances import (
    _GL64_NODES,
    _GL64_WEIGHTS,
)



# ── CMB distance priors (Chen, Huang & Wang 2019, arXiv:1808.05724, Eqs 1-10) ──
# Compressed Planck 2018 TT,TE,EE+lowE geometry as (R, l_A, Omega_b h^2). The
# paper validates these base-LCDM priors against wCDM and CPL, so they remain
# valid in extended dark-energy models — unlike a hard H0/Omega_m Gaussian, which
# forbids the geometric slide along theta*=const that IS the dark-energy signal.
_T_CMB_K = 2.7255
_T_CMB_RATIO4 = (_T_CMB_K / 2.7) ** 4
# Eq (3): 3/(4 Omega_gamma h^2) = 31500 (T_CMB/2.7)^-4 ; baryon loading of `a`.
_RS_BARYON_COEF = 31500.0 / _T_CMB_RATIO4
# Hu & Sugiyama 1996 (ApJ 471, 542, Eq. E-1) photon-decoupling redshift fit,
# reproduced as CHW2019 Eqs 8-10 and Komatsu et al. 2009 (ApJS 180, 330,
# Eqs 66-68).  The g1 prefactor is 0.0783 in every one of those sources.  A
# transcription slip (0.0738) lived here until 2026-09-09; it lowered z* by
# 1.3 and, combined with the sound-horizon matter term below, left the kernel
# +0.10 (+1.1 sigma of the Table-I error) high in l_A at the Planck means.
# Do NOT "correct" this fit toward CAMB's z* (1089.9 vs the fit's 1091.9 at
# Planck 2018 values): the ~0.2% fitting-formula offset is part of the
# recipe the published priors absorb — see test_recipe_reproduces_table1.
_HS96_G1_COEF = 0.0783
# Planck 2018 baseline neutrino sector: one massive eigenstate with
# sum(m_nu) = 0.06 eV, omega_nu h^2 = sum(m_nu)/(93.14 eV) (Planck 2018 VI,
# Sec. 2.1).  The Table-I priors come from base-LCDM chains that carry this
# fixed mass, and the sampled `omegam` follows the Planck convention
# Omega_m = Omega_b + Omega_c + Omega_nu.  At z* the neutrino is still
# relativistic (T_nu ~ 0.19 eV >> m_nu), so it must not enter the pressureless
# matter term of the sound-horizon integral; it is matter-like only at the
# late times that R and D_M(z*) are dominated by.  Excluding it from r_s is
# what closes the last ~0.09% of l_A against Table I (verified 2026-09-09
# against a CAMB 1.6.6 reference at both Planck 2018 base-LCDM columns).
_PLANCK18_BASELINE_OMNU_H2 = 0.06 / 93.14


def _hs96_decoupling_redshift(ombh2, omh2):
    """Hu & Sugiyama 1996 Eq. E-1 fit for z* (CHW2019 Eqs 8-10)."""
    g1 = _HS96_G1_COEF * ombh2 ** -0.238 / (1.0 + 39.5 * ombh2 ** 0.763)
    g2 = 0.560 / (1.0 + 21.1 * ombh2 ** 1.81)
    return 1048.0 * (1.0 + 0.00124 * ombh2 ** -0.738) * (1.0 + g1 * omh2 ** g2)


def _cmb_distance_priors(omegam, h0, ombh2, w0=-1.0, wa=0.0):
    """(R, l_A, Omega_b h^2) CMB distance priors for flat (w0,wa)CDM, per
    Chen-Huang-Wang 2019.  Inputs scalar or broadcastable arrays.  R and l_A are
    H0-independent except through z*/radiation/omega_nu (the c/H0 cancels).

    Compression recipe (must match how the Table-I numbers were produced, or
    the prior is biased even when every input is exact):
      * z*      — Hu & Sugiyama 1996 fit, g1 prefactor 0.0783;
      * Omega_r — CHW2019 Eq 6, Omega_m/(1+z_eq) with z_eq = 2.5e4 omega_m
                  Theta_2.7^-4 (omega_r h^2 = 4.15e-5 at Planck values, 0.7%
                  below CAMB's 4.18e-5 — swapping it alone shifts l_A by ~+0.5);
      * r_s     — matter term is baryons + CDM only: omega_m minus the Planck
                  baseline omega_nu h^2 = 0.06/93.14 (relativistic at z*);
      * D_M, R  — full Planck-convention Omega_m (neutrino matter-like today).
    Self-check at the Planck 2018 TT,TE,EE+lowE means (Om=0.3166, H0=67.27,
    ombh2=0.02236): R = 1.7504, l_A = 301.457 against Table I
    1.7502 +- 0.0046, 301.471 +- 0.090 (pinned by tests/test_planck_distance_prior.py).
    """
    scalar = np.ndim(omegam) == 0
    om = np.atleast_1d(np.asarray(omegam, float))
    obh2 = np.atleast_1d(np.asarray(ombh2, float))
    h2 = (np.atleast_1d(np.asarray(h0, float)) / 100.0) ** 2
    w0a = np.atleast_1d(np.asarray(w0, float))
    waa = np.atleast_1d(np.asarray(wa, float))
    om, obh2, h2, w0a, waa = np.broadcast_arrays(om, obh2, h2, w0a, waa)
    omh2 = om * h2
    zstar = _hs96_decoupling_redshift(obh2, omh2)
    # Radiation density incl. neutrinos (CHW2019 Eq 6); flat closes Omega_de.
    omr = om / (1.0 + 2.5e4 * omh2 / _T_CMB_RATIO4)
    omde = 1.0 - om - omr
    # Sound-horizon matter term: baryons + CDM only (see _PLANCK18_BASELINE_OMNU_H2).
    omcb = om - _PLANCK18_BASELINE_OMNU_H2 / h2
    omde_rs = 1.0 - omcb - omr
    omc, omrc, omdec = om[:, None], omr[:, None], omde[:, None]
    omcbc, omdersc = omcb[:, None], omde_rs[:, None]
    w0c, wac, obc = w0a[:, None], waa[:, None], obh2[:, None]
    node = (_GL64_NODES + 1.0) * 0.5  # (64,) in [0,1]

    def _rho_de(z):
        x = 1.0 + z
        return x ** (3.0 * (1.0 + w0c + wac)) * np.exp(-3.0 * wac * z / x)

    def inv_E(z):  # z shape (N, 64); late-time expansion history for D_M
        x = 1.0 + z
        return 1.0 / np.sqrt(omrc * x ** 4 + omc * x ** 3 + omdec * _rho_de(z))

    def inv_E_rs(z):  # pre-decoupling expansion history for r_s (no massive nu)
        x = 1.0 + z
        return 1.0 / np.sqrt(omrc * x ** 4 + omcbc * x ** 3 + omdersc * _rho_de(z))

    # I = int_0^{z*} dz/E, in u=ln(1+z) so the low-z-peaked integrand is smooth.
    ustar = np.log(1.0 + zstar)[:, None]
    u = ustar * node
    i_dc = np.sum(_GL64_WEIGHTS * (ustar * 0.5) * np.exp(u) * inv_E(np.exp(u) - 1.0), axis=-1)
    # J = int_0^{a*} da / (a^2 E sqrt(3(1 + Rb a))).  c/H0 cancels in l_A = pi*I/J.
    astar = (1.0 / (1.0 + zstar))[:, None]
    a = astar * node
    rb = _RS_BARYON_COEF * obc * a
    integ = inv_E_rs(1.0 / a - 1.0) / (a ** 2 * np.sqrt(3.0 * (1.0 + rb)))
    i_rs = np.sum(_GL64_WEIGHTS * (astar * 0.5) * integ, axis=-1)

    big_r = np.sqrt(om) * i_dc
    l_a = np.pi * i_dc / i_rs
    if scalar:
        return float(big_r[0]), float(l_a[0]), float(obh2[0])
    return big_r, l_a, obh2


# Planck 2018 TT,TE,EE+lowE distance priors, base-LCDM block (the paper validates
# this block for wCDM/CPL too).  Chen-Huang-Wang 2019, arXiv:1808.05724, Table I
# (visually verified against the published PDF, 2026-07-07):
#   R      = 1.7502  +- 0.0046
#   l_A    = 301.471 +0.089/-0.090  (symmetrized to 0.090, the conservative side)
#   ombh2  = 0.02236 +- 0.00015
#   n_s    = 0.9649  +- 0.0043
# with the printed 4x4 correlation matrix.  Self-check: inverting the
# (R, l_A, ombh2) sub-covariance reproduces the paper's appendix
# Distance_invcov.txt to table-rounding precision (pinned by
# tests/test_planck_distance_prior.py).  Used as the executed CMB term for ALL
# flat models — LCDM included (2026-07-07; previously extended-DE only, while
# LCDM ran a diagonal (H0, Om, sigma8, S8) parameter Gaussian that did not
# match the entry's claimed observables).
_PLANCK18_DP_MEAN = np.array([1.7502, 301.471, 0.02236, 0.9649])
_PLANCK18_DP_SIGMA = np.array([0.0046, 0.090, 0.00015, 0.0043])
_PLANCK18_DP_CORR = np.array([
    [1.00, 0.46, -0.66, -0.74],
    [0.46, 1.00, -0.33, -0.35],
    [-0.66, -0.33, 1.00, 0.46],
    [-0.74, -0.35, 0.46, 1.00],
])
_PLANCK18_DP_INVCOV = np.linalg.inv(
    _PLANCK18_DP_SIGMA[:, None] * _PLANCK18_DP_SIGMA[None, :] * _PLANCK18_DP_CORR
)

# Proposal-anchor moments for the distance-prior axes that carry no Gaussian
# row in any CompressedLikelihoodSpec (their constraint lives only in the
# nonlinear prior above).  Consumed by the importance sampler's proposal
# builder; the proposal density is exactly divided back out, so target
# correctness never depends on these — they only keep the ESS from collapsing
# against a tight target inside a wide uniform prior box.
PLANCK18_DP_PROPOSAL_MOMENTS: dict[str, tuple[float, float]] = {
    "ombh2": (float(_PLANCK18_DP_MEAN[2]), float(_PLANCK18_DP_SIGMA[2])),
    "ns": (float(_PLANCK18_DP_MEAN[3]), float(_PLANCK18_DP_SIGMA[3])),
}


def _planck_dp_lcdm_proposal_moments() -> tuple[tuple[str, ...], np.ndarray, np.ndarray] | None:
    """Linearized ΛCDM importance-proposal moments implied by the CHW2019
    distance priors: names ("H0", "omegam", "ombh2", "ns"), the parameter
    point mapping onto the Table-I means, and the implied parameter-space
    covariance J^-1 C J^-T.

    PROPOSAL ONLY: the importance sampler divides this density back out
    exactly, so posterior correctness never depends on it — it exists because
    an axis-independent proposal cannot cover the strongly correlated
    (R, l_A) ridge (measured ESS 21 vs the 400 publication floor).  Returns
    None if the solve/linearization fails; callers must fall back to the
    generic proposal.  Cached after the first call (deterministic).
    """
    global _PLANCK18_DP_LCDM_PROPOSAL_CACHE
    if _PLANCK18_DP_LCDM_PROPOSAL_CACHE is not None:
        return _PLANCK18_DP_LCDM_PROPOSAL_CACHE

    r_mean, la_mean, obh2_mean, ns_mean = (float(x) for x in _PLANCK18_DP_MEAN)

    def _rl(om: float, h0: float, obh2: float) -> np.ndarray:
        big_r, l_a, _ = _cmb_distance_priors(om, h0, obh2)
        return np.array([big_r, l_a])

    try:
        # 2-dim Newton for (omegam, H0) matching the (R, l_A) means at the
        # ombh2 mean (LCDM, w0=-1, wa=0). Start at the Planck 2018 baseline.
        om, h0 = 0.3153, 67.36
        target = np.array([r_mean, la_mean])
        for _ in range(20):
            f = _rl(om, h0, obh2_mean) - target
            if float(np.max(np.abs(f / target))) < 1e-10:
                break
            d_om, d_h0 = 1e-5, 1e-3
            j = np.column_stack([
                (_rl(om + d_om, h0, obh2_mean) - _rl(om - d_om, h0, obh2_mean)) / (2 * d_om),
                (_rl(om, h0 + d_h0, obh2_mean) - _rl(om, h0 - d_h0, obh2_mean)) / (2 * d_h0),
            ])
            om, h0 = np.array([om, h0]) - np.linalg.solve(j, f)
        # Jacobian of v=(R, l_A, ombh2, ns) wrt u=(H0, omegam, ombh2, ns).
        d_h0, d_om, d_ob = 1e-3, 1e-5, 1e-7
        jac = np.zeros((4, 4))
        jac[0:2, 0] = (_rl(om, h0 + d_h0, obh2_mean) - _rl(om, h0 - d_h0, obh2_mean)) / (2 * d_h0)
        jac[0:2, 1] = (_rl(om + d_om, h0, obh2_mean) - _rl(om - d_om, h0, obh2_mean)) / (2 * d_om)
        jac[0:2, 2] = (_rl(om, h0, obh2_mean + d_ob) - _rl(om, h0, obh2_mean - d_ob)) / (2 * d_ob)
        jac[2, 2] = 1.0
        jac[3, 3] = 1.0
        dp_cov = _PLANCK18_DP_SIGMA[:, None] * _PLANCK18_DP_SIGMA[None, :] * _PLANCK18_DP_CORR
        jac_inv = np.linalg.inv(jac)
        implied_cov = jac_inv @ dp_cov @ jac_inv.T
        np.linalg.cholesky(implied_cov)  # must be positive definite
        mean = np.array([h0, om, obh2_mean, ns_mean])
    except Exception:  # pragma: no cover - defensive; callers fall back
        return None
    _PLANCK18_DP_LCDM_PROPOSAL_CACHE = (("H0", "omegam", "ombh2", "ns"), mean, implied_cov)
    return _PLANCK18_DP_LCDM_PROPOSAL_CACHE


_PLANCK18_DP_LCDM_PROPOSAL_CACHE: tuple[tuple[str, ...], np.ndarray, np.ndarray] | None = None


def _planck_distance_prior_chi2(samples: np.ndarray, parameter_order: list[str]) -> np.ndarray:
    """Per-sample chi2 of the Planck 2018 compressed CMB distance priors
    (R, l_A, ombh2, ns) with the full CHW2019 Table-I correlation matrix, for
    any FLAT (w0,wa)CDM-family chain."""
    required = ("omegam", "H0", "ombh2", "ns")
    missing = [name for name in required if name not in parameter_order]
    if missing:
        raise ValueError(
            "Planck 2018 distance prior needs sampled axes "
            f"{list(required)}; missing {missing} from {list(parameter_order)}"
        )
    om = samples[:, parameter_order.index("omegam")]
    h0 = samples[:, parameter_order.index("H0")]
    obh2 = samples[:, parameter_order.index("ombh2")]
    ns = samples[:, parameter_order.index("ns")]
    if "w0" in parameter_order:
        w0 = samples[:, parameter_order.index("w0")]
    elif "w" in parameter_order:
        w0 = samples[:, parameter_order.index("w")]
    else:
        w0 = -1.0
    wa = samples[:, parameter_order.index("wa")] if "wa" in parameter_order else 0.0
    big_r, l_a, _ = _cmb_distance_priors(om, h0, obh2, w0=w0, wa=wa)
    resid = np.column_stack([big_r, l_a, obh2, ns]) - _PLANCK18_DP_MEAN
    return np.einsum("ni,ij,nj->n", resid, _PLANCK18_DP_INVCOV, resid)


def compressed_entry_row_count(
    entry: CosmologyDatasetEntry, parameter_order: list[str]
) -> int:
    """Executed Gaussian rows for a compressed entry in the SAMPLING path.

    The dp_flat branch executes only the 4 correlated CHW2019 distance-prior
    rows. The registry's H0/Omega_m/sigma8/S8 parameter rows are published
    posterior summaries used for proposal/context and are not multiplied as a
    second likelihood. BIC's ln(N) must count what was actually executed;
    keep this in lockstep with the branches of _compressed_chi2_samples."""
    spec = entry.compressed_likelihood
    if spec is None:
        return 0
    if entry.key == "planck2018_compressed" and "omegak" not in parameter_order:
        return 4
    if not compressed_rows_are_executable(entry):
        return 0
    return len(spec.parameters)


def _compressed_chi2_samples(
    samples: np.ndarray,
    parameter_order: list[str],
    compressed_entries: list[CosmologyDatasetEntry],
) -> tuple[np.ndarray, list[str]]:
    total = np.zeros(samples.shape[0], dtype=float)
    invalid_specs: list[str] = []
    # S8 = σ8·√(Ωm/0.3) is derived (not a sampled column) whenever σ8 and Ωm are
    # both sampled; its Gaussian then applies on the derived per-sample value.
    derived_s8 = (
        _derived_s8_from_samples(samples, parameter_order)
        if _s8_is_derived(parameter_order)
        else None
    )
    for entry in compressed_entries:
        spec = entry.compressed_likelihood
        if spec is None:
            continue
        # Every FLAT model (LCDM included, 2026-07-07): execute the entry's
        # CLAIMED observables — the correlated CHW2019 (R, l_A, ombh2, ns)
        # compressed CMB distance priors. The registered Planck parameter rows
        # are posterior summaries and must not be multiplied as an independent
        # growth-amplitude likelihood.
        # Rationale unchanged from the extended-DE-only version this
        # generalizes: a hard H0/omegam parameter Gaussian pins the LCDM
        # projection and (for DE models) forbids the geometric slide along
        # theta*=const that IS the w0/wa signal.  Curved (ok_*) models keep
        # the parameter-summary path (a FLAT distance prior would be wrong;
        # the curved prior is deferred) — defensively only: the in-process
        # runner refuses ok_* models upstream.
        dp_flat = (
            entry.key == "planck2018_compressed"
            and "omegak" not in parameter_order
        )
        if dp_flat:
            try:
                total += _planck_distance_prior_chi2(samples, parameter_order)
            except Exception as exc:
                invalid_specs.append(f"{entry.key}: {exc}")
            continue
        if not compressed_rows_are_executable(entry):
            invalid_specs.append(
                f"{entry.key}: statistical_role={spec.statistical_role!r}, "
                f"execution_mode={entry.execution_mode!r} is context-only and "
                "cannot enter a joint likelihood"
            )
            continue
        try:
            params = list(spec.parameters)
            names = [
                name
                for name in params
                if name in parameter_order
                or (name == "S8" and derived_s8 is not None)
            ]
            if not names:
                # B2: none of this dataset's parameters are in the sampled set,
                # so it can contribute no chi2. Record it as an invalid spec —
                # which flips publication_ready off and surfaces a blocked
                # reason — instead of silently dropping it to chi2=0 while it
                # still appears in datasets_used as if it had constrained the
                # fit (e.g. a BBN ombh2 prior selected alongside a chain that
                # samples only H0/omegam/rd, where ombh2 is never sampled).
                invalid_specs.append(
                    f"{entry.key}: none of its parameters {params} are in the "
                    f"sampled parameter set {list(parameter_order)}, so it "
                    f"contributed no constraint — not applied as run."
                )
                continue
            local_idx = [params.index(name) for name in names]
            mean = np.asarray(spec.mean, dtype=float)[local_idx]
            cov = np.asarray(spec.covariance, dtype=float)[np.ix_(local_idx, local_idx)]
            columns = [
                derived_s8
                if name == "S8" and name not in parameter_order
                else samples[:, parameter_order.index(name)]
                for name in names
            ]
            residual = np.column_stack(columns) - mean
            total += np.einsum("ni,ij,nj->n", residual, np.linalg.inv(cov), residual)
        except Exception as exc:
            invalid_specs.append(f"{entry.key}: {exc}")
    return total, invalid_specs


# Primary-CMB external-cobaya likelihoods that sample the full CMB parameter set
# (ombh2, omch2, H0, ns, As, tau), rather than the geometric (H0, Omega_m, rd)
# set the compressed/in-process probes use.
CMB_COBAYA_EXECUTABLE_KEYS = frozenset({
    "planck_2018_highl_TTTEEE_lite",
    "planck_2018_lowl_TT",
    "planck_2018_lowl_EE",
    "planck_2018_lensing",
})

# A_planck is sampled only when plik_lite or the 2018 lensing likelihood is
# selected (lensing's params include the planck_calib defaults, so it consumes
# the shared calibration). The native low-l likelihoods CAN consume it (cobaya
# get_can_support_params), but their default is calib=1 and a 0.25%
# calibration uncertainty is negligible against l<=29 cosmic variance — so a
# lowl-only run deliberately fixes it. In the full stack cobaya shares the one
# sampled A_planck across all likelihoods, matching official Planck practice.
CMB_APLANCK_KEYS = frozenset({
    "planck_2018_highl_TTTEEE_lite",
    "planck_2018_lensing",
})


# ── ACT DR6 lensing (act_dr6_lenslike) vendored-data verification gate ──────
# The act_baseline lens_only file set act_dr6_lenslike.load_data() reads,
# vendored under the InstallableLikelihood get_path convention
# (packages_path/data/ACT_dr6_likelihood/<version>/) by
# scripts/fetch_act_dr6_lenslike.py and sha256-pinned in the registry entry's
# data_products. covmat_act.txt is loaded UNCONDITIONALLY by load_data (an
# internal consistency test), so it is pinned even though the lens_only
# covariance is covmat_act_cmbmarg.txt.
ACT_DR6_LENSLIKE_VERSION = "v1.2"
ACT_DR6_LENSLIKE_DATA_DIR = (
    pathlib.Path(__file__).resolve().parents[3]
    / "data" / "cobaya_packages" / "data" / "ACT_dr6_likelihood"
    / ACT_DR6_LENSLIKE_VERSION
)
# role (registry data_products) -> filename act_dr6_lenslike.load_data reads.
ACT_DR6_LENSLIKE_FILES: dict[str, str] = {
    "measurement_vector": "clkk_bandpowers_act.txt",
    "binning_matrix": "binning_matrix_act.txt",
    "covariance_cmbmarg": "covmat_act_cmbmarg.txt",
    "covariance": "covmat_act.txt",
    # The fiducial spectra are chi2 anchor inputs — tampering with them moves
    # the likelihood just as surely as tampering with the bandpowers, so the
    # gate's "EVERY pinned file" contract includes them.
    "fiducial_lensed_cls": "like_corrs/cosmo2017_10K_acc3_lensedCls.dat",
    "fiducial_lenspotential_cls": "like_corrs/cosmo2017_10K_acc3_lenspotentialCls.dat",
}


def load_verified_act_dr6_lenslike_data() -> dict[str, Any]:
    """Verify the vendored ACT DR6 lensing data subset against the registry
    sha256 pins.  Returns {data_directory, files_sha256, hash_verified,
    cov_fidelity, issues}: cov_fidelity is 'full' only when EVERY pinned file
    is present and byte-identical to its pin; any missing/tampered file →
    'unverified' with the issue listed (blocks publication; a future
    cobaya_runner wiring must refuse to run on hash_verified=False).  Never
    raises."""
    from app.services.cosmology_likelihoods.registry import get_cosmology_dataset

    entry = get_cosmology_dataset("act_dr6_lensing")
    pins = {p.role: p.sha256 for p in entry.data_products if p.sha256}
    files_sha256: dict[str, str] = {}
    issues: list[str] = []
    for role, filename in ACT_DR6_LENSLIKE_FILES.items():
        pin = pins.get(role)
        if not pin:
            issues.append(f"{role}: no sha256 pin registered for {filename}")
            continue
        path = ACT_DR6_LENSLIKE_DATA_DIR / filename
        if not path.is_file():
            issues.append(
                f"{role}: vendored file missing ({filename}); run "
                "scripts/fetch_act_dr6_lenslike.py"
            )
            continue
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except Exception as exc:  # unreadable file — degrade, never crash
            issues.append(f"{role}: unreadable ({exc})")
            continue
        files_sha256[filename] = digest
        if digest != pin:
            issues.append(f"{role}: sha256 mismatch for {filename}")
    verified = not issues
    return {
        "data_directory": str(ACT_DR6_LENSLIKE_DATA_DIR),
        "files_sha256": files_sha256,
        "hash_verified": verified,
        "cov_fidelity": "full" if verified else "unverified",
        "issues": issues,
    }
