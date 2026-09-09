# Contributing to Standard Astro

Standard Astro is a cosmology-only research alpha, so proposed changes must
preserve the distinction between model suggestions and backend-verified
evidence. Source code is licensed under Apache-2.0. Contributions are accepted under
the Developer Certificate of Origin described in `docs/DCO.md`.

## Before starting

- Read `CLAUDE.md`, `README.md`, and the relevant architecture/science document.
- Search existing issues and pull requests before beginning a large change.
- For security vulnerabilities, follow `SECURITY.md` instead of opening a
  detailed public issue.
- Sign off each commit with `git commit -s` to certify the DCO. As of
  2026-09-09 no CI check enforces the trailer and the maintainers' own commits
  on `main` do not carry it; the sign-off is still requested for external
  contributions. Only submit material you have the right to contribute.
- Treat scientific data separately from source code. Follow
  `docs/DATA_LICENSES.md` and the upstream provider's terms.

## Local setup

Use Python 3.11 and Node 20, the versions `.github/workflows/ci.yml` runs:

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install --require-hashes -r requirements.lock
# ruff is not in requirements.lock; use the same pin as the CI lint job and
# .claude/hooks/ruff-check.py
pip install ruff==0.15.13

cd ../frontend
npm ci
```

Run the backend and frontend as described in `README.md`. Never commit `.env`,
provider credentials, database URLs, unpublished data, or generated local
artifacts.

## Scientific contract

Changes must not turn unavailable or config-only data into executable evidence,
weaken provenance freshness, accept fabricated tool transcripts, or report a
numerical/citation claim that is unsupported by a current backend result.

When adding a dataset, likelihood, connector, or scientific tool, include:

- source and release/version metadata;
- exact claim scope and known limitations;
- deterministic tests, including a fail-closed negative case;
- licensing/redistribution information for any data product;
- provenance and acknowledgement behavior where applicable.

Do not weaken a scientific gate merely to make a test or demonstration pass.
Document a real capability gap instead.

## Code and database changes

- Keep one logical change per pull request and avoid unrelated formatting.
- Add or update tests for every behavior change.
- Production schema changes require an Alembic revision. Application startup
  must not create or alter production tables directly.
- Preserve the cosmology-only runtime allowlist unless a separately reviewed
  repository-scope decision changes it.
- Treat client IPs, user prompts, API keys, audit trails, and unpublished
  research records as sensitive data.
- Keep `CITATION.cff` in step with project metadata (title, license,
  repository URL, authorship). `tests/test_doi_metadata.py` checks its
  required keys and rejects a `doi` entry: no DOI has been minted, and a
  fabricated identifier must not reappear through the citation file.

## Validation

Run focused tests while developing, then the relevant broad checks before
requesting review. The normal minimum is:

```bash
cd backend
./venv/bin/ruff check app/ --select E,W,F --ignore E501
./venv/bin/python -m pytest tests/<relevant_test>.py -q --no-cov   # focused
./venv/bin/python -m pytest tests -q   # full suite; pytest.ini enforces --cov-fail-under=55

cd ../frontend
npx tsc -b --noEmit
npm run lint
npm run test
npm run build
npm run test:e2e   # Playwright browser journeys (CI job frontend-e2e)
```

`--no-cov` is for focused runs only; the coverage floor requires the full
suite, which is the pre-commit gate for backend/runtime changes. CI also runs
the PR-gating `benchmarks` job
(`scripts/benchmarks/run_cosmology_benchmarks.py`, `scripts/audit_registry.py`)
and `migration-and-recovery`; run the matching commands locally for
data/likelihood or Alembic changes. Also run the Docker/Compose, registry,
citation-audit, or scientific validation commands required by the
`CLAUDE.md` "Verification" table for the files you changed. If an
environment-dependent check cannot be run, state exactly what remains
unverified and why.

### Scheduled suites and behaviour changes

The `Daily` and `Weekly Scientific Validation` workflows are measurement
instruments. A change that alters runtime behaviour (prompts, guardrails,
tool dispatch, likelihoods, model routing) merges only when the latest run of
both suites is green and the branch head has a rerun baseline at
`.local/standard-astro-v02-natural/rerun_<rev>_summary.json`. The one
exception is a fix to the failing instrument itself: focused and full
deterministic tests must pass, and the next scheduled run is its acceptance.
Changes to a scheduled workflow's checkout, provider, model, or secret
configuration need a guard test following
`backend/tests/test_scientific_validation_guard.py`. See `CLAUDE.md`
"Verification".

## Branches and pull requests

`main` is protected: work on a feature branch and open a pull request. A PR
must be up to date with `main` and pass every CI job (`backend-test`,
`frontend-test`, `frontend-e2e`, `lint`, `container-build`,
`migration-and-recovery`, `benchmarks`) before it can merge.

Fill in `.github/PULL_REQUEST_TEMPLATE.md`: a short summary; for fixes that
address a blind-test finding, the failure category from
`docs/BLIND_RESEARCH_TESTING_LOG.md` (never paste hidden paper answers); the
regression test that fails before the change and passes after; and the
anti-hardcoding checklist for research-tool fixes. Also explain the chosen
boundary, migration or deployment impact, data/licensing impact, and any
remaining risk. Screenshots are useful for visible UI changes, but they do
not replace tests.
