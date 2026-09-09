/**
 * Mock E2E — fixture-driven full-flow regression without an LLM call.
 *
 * Why this layer exists: real Chat UI tests are gated by LLM latency,
 * key availability, and prompt-driven nondeterminism. This file takes a
 * canned ThinkingEvent stream (recorded in fixtures/) and feeds the
 * recorded tool_result + agent_text events into the SAME production
 * renderers ChatPage uses — the panel AutoToolResult selects for the
 * tool name (CosmologyMCMCPanel for chain runners, CosmologyLikelihoodPanel
 * for dataset/build tools), MarkdownText for the visible agent message —
 * then asserts on the rendered DOM. It catches UI regressions (e.g. an internal
 * __do_not_claim__ / __message_to_model__ marker leaking into the
 * visible message) without paying the LLM cost or accepting LLM jitter.
 *
 * Fixture format is intentionally simple JSON so future fixtures (one
 * per failure mode the docx test-plan map flags — executed_not_ready,
 * honest_abstention, synthetic-blocked, etc.) are just new JSON files.
 *
 * This is the scaffold; the first fixture covers the cosmology
 * golden path. Extend by dropping more JSON into fixtures/ and adding
 * its name to the parametrize list.
 */
import fs from "fs";
import path from "path";
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import CosmologyLikelihoodPanel from "../../components/chat/CosmologyLikelihoodPanel";
import CosmologyMCMCPanel from "../../components/chat/CosmologyMCMCPanel";
import MarkdownText from "../../components/chat/MarkdownText";

interface ThinkingEventLike {
  type: string;
  tool?: string;
  text?: string;
  result?: Record<string, unknown>;
  payload?: Record<string, unknown>;
}

interface Fixture {
  name: string;
  description: string;
  input: { messages: Array<{ role: string; content: string }>; focus: string };
  thinking_events: ThinkingEventLike[];
  expected_ui: {
    tool_card_visible?: string;
    tool_card_status?: string;
    tool_card_tier_badge?: string;
    agent_text_contains?: string[];
    agent_text_not_contains?: string[];
    do_not_claim_marker_leak?: boolean;
    tool_message_to_model_leak?: boolean;
  };
}

const FIXTURES_DIR = path.resolve(__dirname, "fixtures");
const FIXTURE_NAMES = ["cosmology_main_flow"];

// Internal anti-fabrication scaffolding that the backend prepends to
// tool_result dicts so the LLM reads it first. None of it may surface in
// the human-visible rendered message. We match on the underscore-stripped
// core token (e.g. "do_not_claim") so a leak is still caught even when the
// surrounding "__" gets consumed as Markdown bold delimiters by the
// MarkdownText renderer.
const INTERNAL_MARKER_TOKENS = [
  "do_not_claim",
  "message_to_model",
  "tool_status",
  "exploratory_warning",
  "suggested_next_step",
];

// Tool names AutoToolResult routes to CosmologyMCMCPanel (keep in sync with
// src/pages/Chat/AutoToolResult.tsx). Everything else cosmology-shaped goes
// to CosmologyLikelihoodPanel.
const MCMC_PANEL_TOOLS = new Set([
  "fit_cosmology_mcmc",
  "run_cobaya_cosmology",
  "get_cosmology_run_status",
  "run_cosmology_likelihood_chain",
  "run_cmb_rotation_likelihood",
  "run_nested_sampler",
  "evaluate_chain_diagnostics",
]);

// Visible tier badge text CosmologyMCMCPanel renders for each chain_tier
// (TIER_STYLE labels in CosmologyMCMCPanel.tsx).
const MCMC_TIER_LABEL: Record<string, string> = {
  publication: "publication-ready",
  exploratory: "exploratory",
  blocked: "blocked — do not cite",
};

function renderProductionToolCard(toolName: string, result: Record<string, unknown>) {
  if (MCMC_PANEL_TOOLS.has(toolName)) {
    // AutoToolResult unwraps a nested `result` envelope before rendering.
    const nested = result.result && typeof result.result === "object"
      ? result.result as Record<string, unknown>
      : result;
    return render(<CosmologyMCMCPanel result={nested} />);
  }
  return render(<CosmologyLikelihoodPanel result={result} />);
}

function loadFixture(name: string): Fixture {
  const p = path.join(FIXTURES_DIR, `${name}.json`);
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

describe("mockE2E chatFlow", () => {
  it.each(FIXTURE_NAMES)("%s — fixture is well-formed", (name) => {
    const f = loadFixture(name);
    expect(f.name).toBe(name);
    expect(f.thinking_events.length).toBeGreaterThan(0);
    expect(f.input.focus).toMatch(/^cosmology$/);
  });

  it.each(FIXTURE_NAMES)("%s — tool_result events carry the expected anti-fabrication fields", (name) => {
    const f = loadFixture(name);
    const toolResults = f.thinking_events.filter((e) => e.type === "tool_result");
    expect(toolResults.length).toBeGreaterThan(0);
    for (const tr of toolResults) {
      const r = tr.result || {};
      // Every tool_result must carry an explicit success / status flag
      // so the UI can render the correct badge.
      const hasStatus = "__tool_status__" in r || "success" in r;
      expect(hasStatus).toBe(true);
      // publication_ready is required (true / false) so the panel can
      // gate "ready" vs "executed_not_ready" vs "config_only".
      expect("publication_ready" in r).toBe(true);
    }
  });

  it.each(FIXTURE_NAMES)("%s — agent_text renders through MarkdownText without leaking internal markers", (name) => {
    const f = loadFixture(name);
    const agentTexts = f.thinking_events.filter((e) => e.type === "agent_text");
    expect(agentTexts.length).toBeGreaterThan(0);

    for (const at of agentTexts) {
      const text = at.text || "";
      // Feed the recorded agent text through the SAME renderer ChatPage
      // uses for the visible assistant message.
      const { container } = render(<MarkdownText content={text} />);
      const rendered = container.textContent || "";
      // The anti-fabrication invariant the comment promises: no internal
      // marker may appear in the human-visible rendered output.
      for (const token of INTERNAL_MARKER_TOKENS) {
        expect(rendered).not.toContain(token);
      }
    }
  });

  it.each(FIXTURE_NAMES)("%s — expected_ui assertions hold against the rendered output", (name) => {
    const f = loadFixture(name);
    const exp = f.expected_ui || {};
    const toolEvents = f.thinking_events.filter((e) => e.type === "tool_result");
    const agentTexts = f.thinking_events.filter((e) => e.type === "agent_text");

    // ── Tool card: render the recorded tool_result through the panel
    // AutoToolResult selects in production for this tool name
    // (CosmologyMCMCPanel for run_cosmology_likelihood_chain) and assert
    // on the DOM. ──
    if (exp.tool_card_visible) {
      const evt = toolEvents.find((e) => e.tool === exp.tool_card_visible);
      expect(evt, `tool_card_visible '${exp.tool_card_visible}' not in events`).toBeTruthy();
      const result = (evt?.result || {}) as Record<string, unknown>;
      const { container } = renderProductionToolCard(exp.tool_card_visible, result);
      const cardText = container.textContent || "";

      // The model name the result declared must surface in the card.
      if (typeof result.model === "string") {
        expect(cardText).toContain(result.model);
      }
      // Internal anti-fabrication scaffolding must never render as visible
      // card text (do_not_claim_marker_leak / tool_message_to_model_leak
      // are both expected false in the golden fixture).
      for (const token of INTERNAL_MARKER_TOKENS) {
        expect(cardText).not.toContain(token);
      }
      // The fixture's own expectations must agree with the recorded result:
      // a fixture cannot promise a publication badge on an exploratory chain
      // (the in-process compressed path never reaches publication).
      if (exp.tool_card_tier_badge) {
        expect(result.chain_tier).toBe(exp.tool_card_tier_badge);
      }
      if (exp.tool_card_status) {
        expect(String(result.__tool_status__ ?? result.analysis_status)).toBe(exp.tool_card_status);
      }
      // The rendered badge must show the tier the fixture expects, and a
      // non-publication chain must not be presented as publication-ready.
      if (exp.tool_card_tier_badge && MCMC_PANEL_TOOLS.has(exp.tool_card_visible)) {
        const label = MCMC_TIER_LABEL[exp.tool_card_tier_badge];
        expect(label, `unknown tier badge '${exp.tool_card_tier_badge}'`).toBeTruthy();
        expect(cardText).toContain(label);
        if (exp.tool_card_tier_badge !== "publication") {
          expect(cardText).not.toContain(MCMC_TIER_LABEL.publication);
        }
        if (exp.tool_card_tier_badge === "exploratory") {
          // The exploratory banner carries the backend's own warning text.
          const warning = String(result.__exploratory_warning__ || "");
          expect(warning.length).toBeGreaterThan(0);
          expect(cardText).toContain(warning);
        }
      }
      if (exp.tool_card_tier_badge && exp.tool_card_tier_badge !== "publication") {
        expect(result.publication_ready).toBe(false);
        expect(cardText).not.toContain("publication-ready numerical result");
      }
      // Status text: the panel shows a status chip only for states other
      // than COMPLETED / EXPLORATORY, so an EXPLORATORY fixture must not
      // surface a bare status token (the tier badge carries the state).
      if (exp.tool_card_status && MCMC_PANEL_TOOLS.has(exp.tool_card_visible)) {
        const status = exp.tool_card_status.toUpperCase();
        if (status === "COMPLETED" || status === "EXPLORATORY") {
          expect(cardText).not.toContain(status);
        } else {
          expect(cardText).toContain(status);
        }
      }
    }

    // ── Agent message: the cited values the fixture expects must appear
    // in the rendered MarkdownText DOM. ──
    const combined = agentTexts
      .map((e) => {
        const { container } = render(<MarkdownText content={e.text || ""} />);
        return container.textContent || "";
      })
      .join("\n");
    for (const needle of exp.agent_text_contains || []) {
      expect(combined, `rendered agent text expected to contain '${needle}'`).toContain(needle);
    }
    // Exploratory posterior numbers must stay inside the tool card: the
    // reply prose may not quote them (the __exploratory_warning__ contract).
    for (const needle of exp.agent_text_not_contains || []) {
      expect(combined, `rendered agent text must not contain '${needle}'`).not.toContain(needle);
    }
  });
});
