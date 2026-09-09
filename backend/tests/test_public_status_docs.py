"""Public-facing status prose must not drift from the repository state.

Phase 0 (2026-09-02): the project handbook points at the direction review and
the execution plan, and carries the instrument-first rule. Phase 0.3 extends
this file with README / HONESTY_EVIDENCE assertions once the scheduled-suite
status wording is rewritten.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_claude_md_points_at_direction_review_and_execution_plan() -> None:
    handbook = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    for pointer in (
        "docs/research/STANDARD_ASTRO_REVIEW_2026-09-02.zh-CN.md",
        "plan/2026-09-02-execution-plan.md",
    ):
        assert pointer in handbook, pointer
        assert (REPO_ROOT / pointer).is_file(), pointer


def test_claude_md_carries_instrument_first_and_measure_first_rules() -> None:
    handbook = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Instrument-first" in handbook
    assert "Measure before engineering behaviour" in handbook
    assert "gh run list --workflow=daily.yml" in handbook
    assert "Weekly Scientific Validation" in handbook


# Phase 0.3 (2026-09-09): the public status prose carries its task scope and
# dated status lines instead of undated claims that rot silently.

_README = REPO_ROOT / "README.md"
_HONESTY = REPO_ROOT / "docs" / "HONESTY_EVIDENCE.md"
_CASES = REPO_ROOT / "backend" / "scripts" / "blind_test_cosmology_m0" / "cases.yaml"


def _one_line(text: str) -> str:
    return " ".join(text.split())


def test_readme_states_the_task_scope_of_the_headline_numbers() -> None:
    readme = _one_line(_README.read_text(encoding="utf-8"))
    assert "hard-blocked in CI every day" not in readme
    for token in ("V02_03", "V02_06", "8/120", "LIGHTWEIGHT_VERIFICATION_ENABLED=1"):
        assert token in readme, token


def test_honesty_evidence_status_lines_are_dated() -> None:
    import re

    import yaml

    honesty = _HONESTY.read_text(encoding="utf-8")
    for stale in ("As of 2026-07-09, 8 of the last 15", "as of 2026-07-10", "has 16"):
        assert stale not in honesty, stale
    section_3 = honesty.split("## 3.", 1)[1].split("\n## ", 1)[0]
    assert re.search(r"[Ss]tatus as of 20\d\d-\d\d-\d\d", section_3), "dated status line"
    cases = yaml.safe_load(_CASES.read_text(encoding="utf-8"))
    assert f"has {len(cases)} cases" in _one_line(honesty)
