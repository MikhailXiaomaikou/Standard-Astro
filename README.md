# Standard Astro

> An auditable AI research workbench for observational cosmology.

**Research alpha · Cosmology only**

Standard Astro turns cosmology questions into controlled retrieval,
likelihood, fitting, audit, and export workflows. Its differentiator is not
fitting power — it is provable non-fabrication: every numerical claim must
trace to current-run server evidence, versioned data with pinned checksums,
provenance records, and real citations. When the evidence is insufficient,
the system returns `WITHHELD` or `CAPABILITY_GAP` instead of guessing.

This is not a "reproduce any paper" machine, and it does not replace peer
review.

## Real demo

[![Claim Audit real-case demo](./docs/demo/poster.png)](./docs/demo/standard-astro-claim-audit-demo.mp4)

This 32-second storyboard is made from UI captures of a real local run. Given
a strong DESI DR2 evolving-dark-energy claim, the job completes while the
scientific verdict independently becomes `CAPABILITY_GAP`: no result is
guessed, and the signed Evidence Pack verifies.

[Case, limits, and rebuild instructions](./docs/demo/README.md)

## Quick start

Requires Python 3.11 and Node.js 20+. These commands are for a fresh clone.

```bash
# Terminal 1: backend
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install --require-hashes -r requirements.lock
./venv/bin/uvicorn app.main:app --reload --port 8000
```

```bash
# Terminal 2: frontend
cd frontend
npm ci
npm run dev
```

Open the [app](http://localhost:5173/chat),
[health check](http://localhost:8000/health), or
[API docs](http://localhost:8000/docs). Local development defaults to SQLite;
add your own model API key under Account. Full asynchronous and production
operation also requires PostgreSQL, Redis, a worker, and durable object
storage. See the [detailed quick start](./docs/QUICKSTART.md).

## What works today

- **Lightweight, source-checked scalar verification** for bounded paper-table
  calculations: ratio, difference, product, and generalized
  inverse-covariance weighted mean. The backend validates units and covariance,
  resolves the cited source separately from the arithmetic, and returns a
  hashed receipt with `full`, `limited`, `abstention`, or `refusal` semantics.
- **Executable cosmology likelihoods** over registered, checksum-pinned
  datasets (BAO, SNe Ia, CMB, H0 priors, chronometers, and more), with
  claim validation, provenance banners, and dataset-overlap guards.
- **Anti-fabrication gates under scheduled blind testing** — fake tool
  transcripts, invented bibcodes, and pasted numbers are hard gates in the
  scheduled blind suite (`daily.yml`, 18 cases), and clean runs must not be
  falsely blocked either. Each run appends its summary and per-file sha256
  hashes to the append-only
  [`evidence-log`](https://github.com/MikhailXiaomaikou/Standard-Astro/tree/evidence-log)
  branch (`log/<date>-<run_id>/`). The current pass state lives on the
  repository's Actions tab and in the dated status line of
  [Honesty evidence §3](./docs/HONESTY_EVIDENCE.md), not in this sentence.
- **Claim Audit with signed Evidence Packs** — a real local run produces a
  verifiable evidence bundle (see the demo above).
- **A fixed 13-section research report** (since 2026-09-05) — every
  section is printed even when empty, so "looked and found nothing" reads
  differently from "never looked"; a Failed Attempts section lists every
  failed tool, every matrix cell below publication quality with its reason
  code, and every missing capability; "Why it matters" and "Alternative
  Explanations" stay blank for a human to fill, because the platform cannot
  produce that content without inventing it; and the Draft Scientific Claim
  is derived only from findings whose own result is claimable.

Measured evidence (2026-08-06 campaign; five models, natural researcher
phrasings, `LIGHTWEIGHT_VERIFICATION_ENABLED=1` forced by the evaluator
while production defaults it off): on the four tasks where the model was in
the loop (V02_03–V02_06, n=60 post-fix) the in-platform score was 90.4%
versus 46.6% for the same models bare; 8/120 samples received a lower
disposition than expected (V02_03: 6/15, V02_04: 2/15); false blocks of
clean answers 1/60. The other four tasks (V02_01/02/07/08) ran through the
deterministic pipeline with no model call and are reported separately
(720/720, n=60); the pasted fake "tool result" number that was repeated
0/15 times in-platform (rule-of-three upper bound < 20%) versus 15/15 bare
belongs to that pipeline stratum (V02_08, `llm_calls=0`). An earlier
1440/1440 headline was retracted because that pipeline self-check never had
the model in the loop — the honest framing above is the one this project
reports. These are pre-merge snapshot numbers; HEAD has no rerun baseline,
so this paragraph does not describe the current revision until
`rerun_<rev>_summary.json` exists for it. Stratified numbers: the
[post-fix summary](./docs/research/formal_report_package_2026-08-06/evidence/standard_astro_v02_natural_postfix_summary.json)
and the [experiment reports index](./docs/research/standard_astro_v02_experiment_reports/README.md).
Full record:
[campaign report](./docs/research/STANDARD_ASTRO_V02_CAMPAIGN_REPORT_2026-08-06.md)
([Chinese original](./docs/research/STANDARD_ASTRO_V02_CAMPAIGN_REPORT_2026-08-06.zh-CN.md)).

## What it does not do yet

- The strict DESI w0waCDM v1 reproduction remains `WITHHELD`: its chains and
  independent recomputation do not yet form a publishable evidence pack.
- Two measurements are pre-registered but not yet run (as of 2026-09-09):
  the v0.3 exploration-depth harness
  ([tasks](./docs/research/standard_astro_v03_exploration_tasks.json),
  [commitment](./docs/research/standard_astro_v03_exploration_tasks_commitment.json),
  status `FROZEN_NOT_YET_RUN`, frozen 2026-09-03 with a committed sha256),
  which decides whether the platform stops too early on open tasks; and the
  platform-exact Planck 2018 ΛCDM H0 chain
  ([pre-registration](./backend/scripts/cobaya/platform_h0_prereg.json)),
  whose acceptance thresholds are committed but whose formal run has not
  been executed. Neither has a result to report.
- Claim Audit, Workflow Foundry (AI-drafted candidate workflows), and the
  DESI DR2 matrix are engineering-complete but dark-launched: their feature
  flags default to off, candidates can never output `SUPPORTED` without
  human review plus a signed registry release, and none of it is a
  production feature yet. Foundry has been frozen in that state since
  2026-07-24 with no further investment, and new anti-fabrication
  wall-hardening is under a moratorium until the first real external-user
  event (see the [backlog](./plan/cosmology-completion-backlog.md)).
- Lightweight scalar verification is also dark-launched
  (`LIGHTWEIGHT_VERIFICATION_ENABLED=0` by default). Its automated matrices
  and adversarial regression suite are green, but the current code still
  requires a fresh end-to-end demo rerun plus independent expert review before
  an Alpha v0.2 claim.
- Rubin / Euclid / Roman entries are schema fixtures only — not executable
  and not evidence for any measurement claim.
- Product validation is pending: the platform has not yet completed its
  planned continuous-operation record or real-user validation. Even a
  `SUPPORTED` verdict does not mean "peer reviewed".

The full, current honesty record — including known limits and daily
blind-test evidence — lives in
[Honesty evidence and known limits](./docs/HONESTY_EVIDENCE.md).

## Verify

```bash
cd backend
./venv/bin/pip install ruff==0.15.13   # the CI-pinned linter; not in requirements.lock
./venv/bin/ruff check app/ --select E,W,F --ignore E501
./venv/bin/pytest tests -q
```

```bash
cd frontend
npm run lint
npm run test
npm run build
```

## Verify an Evidence Pack offline

Signed Evidence Packs can be verified on any machine without installing the
platform:

```bash
pip install cryptography
python scripts/verify_evidence_pack.py pack.zip --keyring keys/evidence-keyring.json
```

The committed [`keys/evidence-keyring.json`](./keys/evidence-keyring.json) is
the out-of-band trust root (public keys only). As of 2026-09-09 it holds no
keys, so the command above exits 1 with `keyring contains no keys`: no pack
can be verified offline until the first signing key is published and
committed there (see the
[key rotation runbook](./docs/runbooks/EVIDENCE_V2_KEY_ROTATION.md)). A hosted
deployment's served `/.well-known/standard-astro-evidence-keys.json` must
match the committed file before it is trusted. A valid signature proves
origin and integrity, not scientific truth.

## Cite

Use the metadata in [`CITATION.cff`](./CITATION.cff) (GitHub renders it as
"Cite this repository"). No DOI has been minted; Evidence Packs carry
`doi: null` with `doi_status: not_minted` and identify themselves by
`urn:sha256` digests rather than a fabricated identifier.

## Documentation

- [Honesty evidence and known limits](./docs/HONESTY_EVIDENCE.md)
- [Architecture](./ARCHITECTURE.md) · [Source mapping](./docs/SOURCE_MAPPING.md)
- [Detailed quick start](./docs/QUICKSTART.md)
- [v0.2 evaluation](./docs/research/STANDARD_ASTRO_V02_EVALUATION_2026-08-04.md) · [campaign and post-review record](./docs/research/STANDARD_ASTRO_V02_CAMPAIGN_REPORT_2026-08-06.md) (English; Chinese originals: [评测](./docs/research/STANDARD_ASTRO_V02_EVALUATION_2026-08-04.zh-CN.md) · [战役](./docs/research/STANDARD_ASTRO_V02_CAMPAIGN_REPORT_2026-08-06.zh-CN.md))
- [Deployment](./DEPLOYMENT.md) · [Production cutover checklist](./docs/PRODUCTION_CUTOVER_CHECKLIST.md)
- [Privacy](./PRIVACY.md) · [Security](./SECURITY.md) · [Data licences](./docs/DATA_LICENSES.md)
- [Contributing](./CONTRIBUTING.md) · [Changelog](./CHANGELOG.md) · [API reference](./docs/API_REFERENCE.md)
- Current direction (Chinese): [direction review, 2026-09-02](./docs/research/STANDARD_ASTRO_REVIEW_2026-09-02.zh-CN.md) · [execution plan, 2026-09-02](./plan/2026-09-02-execution-plan.md) · [cosmology completion backlog](./plan/cosmology-completion-backlog.md)
- [Blind research testing log](./docs/BLIND_RESEARCH_TESTING_LOG.md) · [Evidence-key rotation runbook](./docs/runbooks/EVIDENCE_V2_KEY_ROTATION.md)
- Historical plan, superseded by the 2026-09-02 documents: [P0 + P1 roadmap, 2026-07-17](./docs/roadmaps/P0_P1_COMPLETE_PLAN.zh-CN.md) (Chinese)
- Workflow Foundry, frozen dark-launched since 2026-07-24 with no further investment (Chinese): [design](./docs/roadmaps/AI_WORKFLOW_FOUNDRY_V1.zh-CN.md) · [release and activation runbook](./docs/runbooks/FOUNDRY_RELEASE_AND_ACTIVATION.zh-CN.md) · [candidate source materialization](./docs/runbooks/FOUNDRY_SOURCE_MATERIALIZATION.zh-CN.md)

## Licence

Project source code is licensed under the [Apache License 2.0](./LICENSE).
Data, papers, and third-party services retain their own licence, citation,
and acknowledgement requirements; Apache-2.0 does not override those terms.
Contributions also follow the [DCO](./docs/DCO.md).
