---
name: cosmology-smoke
description: Run a cosmology science-regression smoke check. Verifies ΛCDM BAO+CMB recovers H0≈67.4 at chain_tier=exploratory (the in-process compressed path never reaches publication), wCDM BAO+CMB recovers a numerical w near -1 through the emcee fallback (a blocked chain is a regression), the blocked tier triggers on inline rows, and distance_modulus_model stays within 1e-3 mag of astropy. Use after any change to backend/app/services/cosmology_*.py or backend/app/services/cosmology_likelihoods.py to confirm no science regression.
---

# Cosmology science-regression smoke

This skill runs four cheap science checks against the cosmology stack. Total wall-clock: ~30-60s.

## Checks

### 1. ΛCDM BAO+CMB → H0 anchor
DESI DR1 BAO + Planck18 compressed → flat-ΛCDM should give H0 within 66.5–68.5 km/s/Mpc
(67.7 with the 2026-09-09 CHW2019 compression recipe; r_d is a free nuisance parameter,
so H0 is set by the CMB geometry) with ESS > 400.
Tier must be `exploratory`: every compressed-likelihood chain carries the
`compressed_or_approximate_likelihood` gate reason and can never reach `publication`
in-process (cosmology_likelihoods/verification.py). A `publication` tier here is a regression.

### 2. wCDM BAO+CMB → DESI 2024 reproduction
Same datasets with model=`wcdm`, run with `allow_emcee_fallback=True` (what the chat tool
uses): the plain importance sampler collapses on the broad w prior (ESS ~2), so the fallback
emcee chain is the one that carries the science. The check REQUIRES a numerical posterior:
tier `exploratory` (the off-anchor frontier guard keeps w off the publication tier by design)
and w within (-1.5, -0.5) (DESI 2024 reports w ≈ -0.95 ± 0.20). A `blocked` chain, a missing
`parameters` block, or a `publication` tier is a regression here — never a pass — so a broken
likelihood or proposal cannot hide behind the always-present compressed/off-anchor gate reasons.

### 3. chain_tier trigger matrix
The in-process runner exposes only two of the three tiers (publication is reserved for
verified full-likelihood, independent-chain runs on the external path):
- (lcdm + registered compressed datasets) → `exploratory` + `__exploratory_warning__` set (asserted on check 1's result)
- (any model + inline_unverified rows) → `blocked` + `__do_not_claim__=True`

### 4. distance_modulus_model precision vs astropy
For z ∈ {0.1, 0.5, 1.0, 2.3} and the 3 models (flat_lcdm, flat_wcdm, flat_w0wa_cdm), max |μ_ours − μ_astropy| must be < 1e-3 mag.

## Run

```bash
cd "$(git rev-parse --show-toplevel)/backend" && ./venv/bin/python3 - <<'PY'
import numpy as np, json
from app.services.cosmology_likelihoods import run_likelihood_chain
from app.services.cosmology_mcmc import distance_modulus_model
from astropy.cosmology import FlatLambdaCDM, FlatwCDM, Flatw0waCDM

results = {}

# Check 1: ΛCDM BAO+CMB
r = run_likelihood_chain(model="lcdm", dataset_keys=["desi_dr1_bao", "planck2018_compressed"], n_samples=4000, random_seed=42)
h0 = r["parameters"]["H0"]["median"]
results["lcdm_h0_anchor"] = {
    # Compressed-likelihood chains carry the compressed_or_approximate_likelihood
    # reason and must never reach chain_tier="publication"
    # (cosmology_likelihoods/verification.py); a "publication" tier here is a
    # scientific-tier regression, so the check pins exploratory exactly.
    # ... and the exploratory envelope must carry its __exploratory_warning__ contract.
    "pass": 66.5 < h0 < 68.5 and r["chain_tier"] == "exploratory" and bool(r.get("__exploratory_warning__")),
    "h0_median": h0,
    "tier": r["chain_tier"],
    "ess": r["chain_diagnostics"].get("proposal_ess"),
}

# Check 2: wCDM BAO+CMB — emcee fallback, numerical w REQUIRED (blocked == regression)
r2 = run_likelihood_chain(model="wcdm", dataset_keys=["desi_dr1_bao", "planck2018_compressed"], n_samples=4000, random_seed=42, allow_emcee_fallback=True)
w = (r2.get("parameters") or {}).get("w", {}).get("median")
results["wcdm_w_near_minus_one"] = {
    "pass": r2["chain_tier"] == "exploratory" and w is not None and -1.5 < w < -0.5,
    "w_median": w,
    "tier": r2["chain_tier"],
    "sampler": r2.get("sampler"),
    "ess": r2["chain_diagnostics"].get("proposal_ess"),
    "gate_reasons": r2.get("publication_gate", {}).get("reasons"),
}

# Check 3: chain_tier triggers
results["chain_tier_blocked_inline"] = {"pass": False, "tier": None}
from app.services.cosmology_mcmc import fit_cosmology_emcee
rng = np.random.default_rng(0)
z = np.linspace(0.05, 1.0, 20)
mu = 5*np.log10(z*3000) + 25 + rng.normal(0, 0.1, 20)
rows = [{"z": float(zi), "mu": float(mi), "sigma_mu": 0.1} for zi, mi in zip(z, mu)]
r3 = fit_cosmology_emcee(rows, n_walkers=16, n_steps=200, n_burn=50)
results["chain_tier_blocked_inline"] = {
    "pass": r3["chain_tier"] == "blocked" and r3.get("__do_not_claim__") is True,
    "tier": r3["chain_tier"],
}

# Check 4: distance_modulus precision
worst = 0.0
for z_val in (0.1, 0.5, 1.0, 2.3):
    z_arr = np.array([z_val])
    ours = distance_modulus_model(z_arr, "flat_lcdm", {"H0": 67.4, "Om0": 0.315})
    astro = FlatLambdaCDM(H0=67.4, Om0=0.315, Tcmb0=2.7255).distmod(z_arr).value
    worst = max(worst, abs(ours[0] - astro[0]))
    ours_w = distance_modulus_model(z_arr, "flat_wcdm", {"H0": 70.0, "Om0": 0.30, "w0": -0.9})
    astro_w = FlatwCDM(H0=70.0, Om0=0.30, w0=-0.9, Tcmb0=2.7255).distmod(z_arr).value
    worst = max(worst, abs(ours_w[0] - astro_w[0]))
    ours_w0wa = distance_modulus_model(z_arr, "flat_w0wa_cdm", {"H0": 70.0, "Om0": 0.30, "w0": -0.9, "wa": 0.1})
    astro_w0wa = Flatw0waCDM(H0=70.0, Om0=0.30, w0=-0.9, wa=0.1, Tcmb0=2.7255).distmod(z_arr).value
    worst = max(worst, abs(ours_w0wa[0] - astro_w0wa[0]))
results["distmod_precision_mag"] = {
    "pass": worst < 1e-3,
    "worst_diff_mag": worst,
}

print(json.dumps(results, indent=2, default=float))
all_pass = all(c["pass"] for c in results.values())
import sys; sys.exit(0 if all_pass else 1)
PY
```

## Interpretation

- All four `pass=true` → safe to push.
- `lcdm_h0_anchor.pass=false` → check `_flat_de_distances_at_z` or `_desi_dr1_bao_predictions` for regressions.
- `wcdm_w_near_minus_one.pass=false` → the chain is `blocked` (emcee fallback failed or its ESS collapsed), lands on a `publication` tier, or w sits outside (-1.5, -0.5); check w prior bounds, `_desi_dr1_bao_predictions` w extraction, `_run_emcee_chain`, or the off-anchor / ESS guards.
- `chain_tier_blocked_inline.pass=false` → check `CLAIMABLE_INPUT_ORIGINS` filter in `fit_cosmology_emcee`.
- `distmod_precision_mag.pass=false` → check Gauss-Legendre node order in `distance_modulus_model`; should not regress past 32.
