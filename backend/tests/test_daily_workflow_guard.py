"""Guard the Daily blind-suite workflow's model-profile wiring.

The 2026-08-11 outage was a scheduled run silently exercising a model
contract nobody had pinned. This file pins the pieces a later edit could
drop without any deterministic test noticing: the manual
``deepseek_profile`` input, its fallback, and the ``BLIND_DEEPSEEK_PROFILE``
hand-off into the runner (review thread PRRT_kwDORoeoE86fOjE5).
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DAILY_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "daily.yml"
RUNNER = REPO_ROOT / "backend" / "scripts" / "blind_test_cosmology_m0" / "runner.py"
DEFAULT_PROFILE = "deepseek:v4-pro"


def _workflow() -> dict:
    return yaml.safe_load(DAILY_WORKFLOW.read_text(encoding="utf-8"))


def _triggers(workflow: dict) -> dict:
    # PyYAML reads the bare ``on:`` key as the boolean True.
    return workflow.get("on") or workflow.get(True) or {}


def test_daily_dispatch_exposes_the_deepseek_profile_input_with_the_cron_default() -> None:
    inputs = _triggers(_workflow())["workflow_dispatch"]["inputs"]
    assert "deepseek_profile" in inputs, "manual dispatch lost the deepseek_profile input"
    assert inputs["deepseek_profile"]["default"] == DEFAULT_PROFILE


def test_daily_run_step_hands_the_profile_to_the_runner_with_the_same_fallback() -> None:
    workflow = _workflow()
    mappings = [
        str(step["env"]["BLIND_DEEPSEEK_PROFILE"])
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        if isinstance(step.get("env"), dict) and "BLIND_DEEPSEEK_PROFILE" in step["env"]
    ]
    assert mappings, "no step exports BLIND_DEEPSEEK_PROFILE to the runner"
    for mapping in mappings:
        assert "inputs.deepseek_profile" in mapping, mapping
        assert DEFAULT_PROFILE in mapping, f"fallback must stay {DEFAULT_PROFILE}: {mapping}"


def test_runner_reads_the_profile_from_the_same_variable_with_the_same_default() -> None:
    source = RUNNER.read_text(encoding="utf-8")
    assert 'os.environ.get("BLIND_DEEPSEEK_PROFILE", "deepseek:v4-pro")' in source


def _publish_step_script() -> str:
    for job in _workflow()["jobs"].values():
        for step in job.get("steps", []):
            if step.get("name") == "Publish evidence log":
                return str(step["run"])
    raise AssertionError("daily.yml lost the 'Publish evidence log' step")


def test_publish_step_resolves_fetch_head_before_entering_the_worktree() -> None:
    """FETCH_HEAD is per-worktree: only the checkout that ran ``git fetch`` has
    it. Every scheduled run from 2026-09-05 to 2026-09-08 failed with
    "'FETCH_HEAD' is not a commit" because the step created a fresh worktree
    and then read FETCH_HEAD inside it. The tip must be resolved to a commit
    first and the worktree created from that commit."""
    lines = [
        line.strip()
        for line in _publish_step_script().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    worktree_lines = [line for line in lines if "git worktree add" in line]
    assert worktree_lines, "publish step no longer creates the evidence-log worktree"
    for line in worktree_lines:
        assert "FETCH_HEAD" not in line, f"worktree must be created from a resolved commit: {line}"
    assert not any("checkout" in line and "FETCH_HEAD" in line for line in lines), (
        "no checkout may reference FETCH_HEAD inside the evidence-log worktree"
    )
    assert any("rev-parse" in line and "FETCH_HEAD" in line for line in lines), (
        "the fetched evidence-log tip must be resolved with rev-parse before the worktree exists"
    )
