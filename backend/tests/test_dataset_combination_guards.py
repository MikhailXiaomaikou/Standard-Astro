"""Double-count guards for overlapping cosmology datasets (2026-07-07).

Three confirmed do_not_combine_with holes let the same raw data enter one
joint fit twice without even a warning (live-verified SILENT via
_combination_warnings before the fix):

(a) planck2018_compressed is a compression of the SAME Planck 2018 data the
    full clik-free stack fits natively (CHW2019 distance priors compress
    TT,TE,EE+lowE; its parameter-summary/S8 rows come from the Planck VI
    Table 2 TT,TE,EE+lowE+lensing column).  Co-adding it with
    planck_2018_highl_TTTEEE_lite / planck_2018_lowl_TT / planck_2018_lowl_EE /
    planck_2018_lensing (or the PR4 reprocessing) counts Planck twice.
(b) act_dr6_lensing's executed compressed numbers are hand-typed from the
    ACT DR6 lensing paper's joint ACT+Planck-lensing results — co-adding with
    planck_2018_lensing / planck_pr4_lensing counts Planck lensing twice
    (and the entry is not a standalone ACT constraint at all).
(c) eboss_dr16_lrg_fsbao contains the BOSS z=0.38/0.51 galaxy sample plus
    eBOSS LRGs at z=0.698 — the same BOSS/eBOSS LRGs DESI re-observes.  The
    DESI key papers partition SDSS vs DESI at z=0.6 instead of co-adding
    (the exact rationale already recorded on sdss_dr12_consensus_bao); the
    FSBAO 9-vector is indivisible, so it must not be co-added with DESI BAO.

The lists are reciprocal by project convention so the _combination_warnings
guard fires regardless of which side of the pair is iterated first.
"""
from __future__ import annotations

import pytest

from app.services import cosmology_likelihoods as cl
from app.services.cosmology_likelihoods import run_likelihood_chain
from app.services.cosmology_likelihoods.config_builder import (
    _combination_warnings,
    build_likelihood_config,
)


def _warns(*keys: str) -> bool:
    entries = [cl.get_cosmology_dataset(key) for key in keys]
    return bool(_combination_warnings(entries))


def test_desi_dr1_and_dr2_cannot_enter_one_likelihood_config():
    with pytest.raises(ValueError, match="overlapping releases"):
        build_likelihood_config(
            model="lcdm",
            dataset_keys=["desi_dr1_bao", "desi_dr2_bao"],
        )


# ── (a) Planck 2018 compressed vs the full clik-free Planck 2018 stack ──────

PLANCK_FULL_STACK = (
    "planck_2018_highl_TTTEEE_lite",
    "planck_2018_lowl_TT",
    "planck_2018_lowl_EE",
    "planck_2018_lensing",
    "planck_pr4_lensing",
)


@pytest.mark.parametrize("full_key", PLANCK_FULL_STACK)
def test_planck_compressed_excludes_full_planck_stack_reciprocally(full_key):
    compressed = cl.get_cosmology_dataset("planck2018_compressed")
    assert full_key in compressed.do_not_combine_with, full_key
    other = cl.get_cosmology_dataset(full_key)
    assert "planck2018_compressed" in other.do_not_combine_with, full_key
    assert _warns("planck2018_compressed", full_key)


def test_planck_compressed_plus_full_stack_chain_is_not_publication_ready():
    result = run_likelihood_chain(
        model="lcdm",
        dataset_keys=["planck2018_compressed", "planck_2018_lensing"],
        random_seed=123,
        n_samples=512,
    )
    assert result["publication_ready"] is False
    joined = " ".join(result["warnings"])
    assert "must not be co-added" in joined
    assert "planck2018_compressed" in joined and "planck_2018_lensing" in joined


# ── (b) ACT DR6 lensing (ACT+Planck joint numbers) vs Planck lensing ────────

@pytest.mark.parametrize("planck_key", ["planck_2018_lensing", "planck_pr4_lensing"])
def test_act_dr6_lensing_excludes_planck_lensing_reciprocally(planck_key):
    act = cl.get_cosmology_dataset("act_dr6_lensing")
    assert planck_key in act.do_not_combine_with, planck_key
    other = cl.get_cosmology_dataset(planck_key)
    assert "act_dr6_lensing" in other.do_not_combine_with, planck_key
    assert _warns("act_dr6_lensing", planck_key)


def test_act_dr6_lensing_entry_is_honest_about_joint_act_planck_numbers():
    """The executed compressed numbers are hand-typed from the ACT+Planck
    JOINT summary — the entry must say so and must not present itself as a
    statistically standalone ACT constraint."""
    act = cl.get_cosmology_dataset("act_dr6_lensing")
    notes = act.notes.lower()
    assert "act+planck joint" in notes
    assert "standalone act" in notes
    spec = act.compressed_likelihood
    assert spec is not None
    assert "act+planck" in spec.approximation.lower()
    assert "standalone" in spec.approximation.lower()


def test_act_plus_planck_lensing_chain_is_not_publication_ready():
    result = run_likelihood_chain(
        model="lcdm",
        dataset_keys=["act_dr6_lensing", "planck_2018_lensing"],
        random_seed=123,
        n_samples=512,
    )
    assert result["publication_ready"] is False
    assert result["analysis_status"] == "NO_COMPRESSED_LIKELIHOOD"
    assert result["chain_tier"] == "blocked"
    assert result["__do_not_claim__"] is True
    assert result["datasets_used"] == []
    assert {entry["key"] for entry in result["datasets_not_run"]} == {
        "act_dr6_lensing",
        "planck_2018_lensing",
    }
    assert "parameters" not in result
    assert "context-only" in " ".join(result["warnings"])


# ── (c) eBOSS DR16 LRG FSBAO (BOSS z=0.38/0.51 + eBOSS z=0.698) vs DESI ─────

@pytest.mark.parametrize("desi_key", ["desi_dr1_bao", "desi_dr2_bao"])
def test_eboss_lrg_fsbao_excludes_desi_reciprocally(desi_key):
    lrg = cl.get_cosmology_dataset("eboss_dr16_lrg_fsbao")
    assert desi_key in lrg.do_not_combine_with, desi_key
    other = cl.get_cosmology_dataset(desi_key)
    assert "eboss_dr16_lrg_fsbao" in other.do_not_combine_with, desi_key
    assert _warns("eboss_dr16_lrg_fsbao", desi_key)


def test_eboss_lrg_fsbao_notes_no_longer_claim_desi_independence():
    lrg = cl.get_cosmology_dataset("eboss_dr16_lrg_fsbao")
    assert "No survey overlap with DESI BAO" not in lrg.notes


def test_eboss_lrg_fsbao_plus_desi_chain_is_not_publication_ready():
    result = run_likelihood_chain(
        model="lcdm",
        dataset_keys=["eboss_dr16_lrg_fsbao", "desi_dr1_bao"],
        random_seed=123,
        n_samples=1024,
    )
    assert result["publication_ready"] is False
    assert result["chain_tier"] != "publication"
    joined = " ".join(result["warnings"])
    assert "must not be co-added" in joined


# ── (d) eBOSS DR16 QSO FSBAO (z=1.48, re-observed by DESI) vs DESI ──────────

@pytest.mark.parametrize("desi_key", ["desi_dr1_bao", "desi_dr2_bao"])
def test_eboss_qso_fsbao_excludes_desi_reciprocally(desi_key):
    qso = cl.get_cosmology_dataset("eboss_dr16_qso_fsbao")
    assert desi_key in qso.do_not_combine_with, desi_key
    other = cl.get_cosmology_dataset(desi_key)
    assert "eboss_dr16_qso_fsbao" in other.do_not_combine_with, desi_key
    assert _warns("eboss_dr16_qso_fsbao", desi_key)


def test_eboss_qso_fsbao_notes_no_longer_claim_desi_independence():
    qso = cl.get_cosmology_dataset("eboss_dr16_qso_fsbao")
    assert "No DESI overlap" not in qso.notes


def test_eboss_qso_fsbao_plus_desi_chain_is_not_publication_ready():
    result = run_likelihood_chain(
        model="lcdm",
        dataset_keys=["eboss_dr16_qso_fsbao", "desi_dr1_bao"],
        random_seed=123,
        n_samples=1024,
    )
    assert result["publication_ready"] is False
    assert result["chain_tier"] != "publication"


# ── Existing pairs must keep warning (regression control) ───────────────────

@pytest.mark.parametrize(
    ("key_a", "key_b"),
    [
        ("planck_2018_lensing", "planck_pr4_lensing"),
        ("eboss_dr16_lrg_fsbao", "sdss_dr12_consensus_bao"),
        ("eboss_dr16_lrg_fsbao", "eboss_dr16_rsd"),
    ],
)
def test_previously_declared_overlaps_still_warn(key_a, key_b):
    assert _warns(key_a, key_b)


# ── (e) planck2018_compressed vs act_dr6_lensing (both carry Planck lensing) ─
# Adversarial-review find (2026-07-07): the compressed Planck entry's S8 row
# quotes the lensing-included Planck VI column, and act_dr6_lensing's
# executed numbers are the ACT+Planck JOINT summary — co-adding counts
# Planck lensing twice, same class as pairs (a)-(d).

def test_planck_compressed_and_act_dr6_lensing_mutually_excluded():
    planck = cl.get_cosmology_dataset("planck2018_compressed")
    assert "act_dr6_lensing" in planck.do_not_combine_with
    act = cl.get_cosmology_dataset("act_dr6_lensing")
    assert "planck2018_compressed" in act.do_not_combine_with
    assert _warns("planck2018_compressed", "act_dr6_lensing")


def test_planck_compressed_plus_act_lensing_chain_is_not_publication_ready():
    result = run_likelihood_chain(
        model="lcdm",
        dataset_keys=["planck2018_compressed", "act_dr6_lensing"],
        random_seed=123,
        n_samples=1024,
    )
    assert result["publication_ready"] is False
    assert result["chain_tier"] != "publication"


# ── (f) 2026-09-09 physics-rigor audit: undeclared overlaps + reciprocity ───
# sdss_6df_bao's MGS z=0.15 point comes from the same galaxies as the
# eboss_dr16_rsd MGS fσ8 point (no vendored cross-covariance), and the MGS /
# eBOSS tracers behind both entries are re-observed by DESI (the key papers
# replace SDSS rather than co-add).  Union3 and SH0ES also carried no reverse
# edges at all — harmless for _combination_warnings (which checks both
# directions) but a registry that documents an overlap on one side only is a
# maintenance trap, so every edge is now required to be reciprocal.

AUDIT_2026_09_09_PAIRS = [
    ("sdss_6df_bao", "eboss_dr16_rsd"),
    ("sdss_6df_bao", "desi_dr1_bao"),
    ("sdss_6df_bao", "desi_dr2_bao"),
    ("eboss_dr16_rsd", "desi_dr1_bao"),
    ("eboss_dr16_rsd", "desi_dr2_bao"),
    ("union3", "pantheon_plus"),
    ("union3", "des_sn5yr"),
    ("union3", "pantheon18"),
    ("shoes_h0_riess22", "pantheon_plus"),
    ("shoes_h0_riess22", "trgb_h0_freedman19"),
    ("shoes_h0_riess22", "cchp_h0_freedman24"),
    ("trgb_h0_freedman19", "cchp_h0_freedman24"),
]


@pytest.mark.parametrize(("key_a", "key_b"), AUDIT_2026_09_09_PAIRS)
def test_audit_overlap_pairs_are_declared_reciprocally(key_a, key_b):
    a = cl.get_cosmology_dataset(key_a)
    b = cl.get_cosmology_dataset(key_b)
    assert key_b in a.do_not_combine_with, (key_a, key_b)
    assert key_a in b.do_not_combine_with, (key_b, key_a)
    assert _warns(key_a, key_b)


def test_every_do_not_combine_edge_is_reciprocal_and_resolvable():
    from app.services.cosmology_likelihoods.registry import _REGISTRY

    broken = []
    for key, entry in _REGISTRY.items():
        for other in entry.do_not_combine_with:
            if other not in _REGISTRY:
                broken.append(f"{key} -> {other}: unknown key")
            elif key not in _REGISTRY[other].do_not_combine_with:
                broken.append(f"{key} -> {other}: not reciprocated")
            if other == key:
                broken.append(f"{key}: lists itself")
    assert broken == [], broken


def test_sdss_6df_plus_desi_chain_is_not_publication_ready():
    result = run_likelihood_chain(
        model="lcdm",
        dataset_keys=["sdss_6df_bao", "desi_dr1_bao"],
        random_seed=123,
        n_samples=1024,
    )
    assert result["publication_ready"] is False
    assert result["chain_tier"] != "publication"
    assert "overlapping_dataset_combination" in result["preliminary_reasons"]
