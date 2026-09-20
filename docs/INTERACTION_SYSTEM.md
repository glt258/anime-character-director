---
title: Interaction System v1
description: Persistent three-mode orchestration for Anime Character Director.
type: architecture
status: ACCEPTED / FROZEN (base); Persistent Runner ACCEPTED / FROZEN
confidence: high
created: 2026-09-15
updated: 2026-09-15
tags: [interaction, session, modes, gates, architecture]
sources: ["[[SKILL.md]]", "[[references/creative-modes.md]]", "[[references/workflow.md]]"]
related: ["[[architecture/skill-and-runtime]]", "[[decisions/human-authority]]"]
---

# Interaction System v1

The resolver/session contract described here remains the accepted base layer. The product-level continuation wrapper is documented in [Persistent Interactive Workflow Runner v1](PERSISTENT_INTERACTIVE_WORKFLOW.md).

## Scope

This phase adds a persistent orchestration layer to the existing Codex Skill. It is not a GUI, Web UI, standalone agent, external chat product, or image API. The phase ends at `GENERATION_READY`; it does not call `$imagegen` or generate images.

The default mode is `AI_DECIDE`. Explicit modes and obvious natural-language hints are preferred; unreliable or ambiguous hints fall back to the default. Interaction System v1 is `ACCEPTED / FROZEN` for the current scope.

## Three modes

- `QUICK` is speed-first. It explores at low depth, does not show intermediate gates, fills missing values with `quick_ai_fill`, and still runs every hard contract.
- `AI_DECIDE` is quality-first. It runs the full deterministic Character and Art Explore, compares alternatives, resolves Visual Preferences, and records `delegated_ai`.
- `USER_DECIDE` runs the same pipeline but waits only at Character Direction, Art Direction, and Visual Preference gates. A single Visual Preference Sheet gathers high-impact user-facing variables; implementation variables never become chat questions.

The difference is only gate resolution strategy. The pipeline never branches on mode.

## Shared pipeline

```text
INPUT → CHARACTER_EXPLORE → CHARACTER_DIRECTION_RESOLUTION
 → CHARACTER_PLANNING → ART_EXPLORE → ART_DIRECTION_RESOLUTION
 → VISUAL_PREFERENCE_RESOLUTION → FINAL_DESIGN
 → PLAYABLE_CHARACTER_DESIGN_GATE → PROMPT_COMPILATION
 → GENERATION_READY
```

`GateResolver` is the seam. Its implementations are `QuickGateResolver`, `AIDecideGateResolver`, and `UserDecideGateResolver`. Each returns a `GateResolution` rather than making the pipeline aware of the mode.

## Session model

`CreativeInteractionSession` stores the session id, mode, current stage/gate/status, original input, explicit constraints, delegated and locked fields, Visual Context Firewall state, unresolved fields, Character Explore and selection, Character Plan, Art Explore and selection, Visual Preference Sheet and resolved values, Final Design, Playable Character Design result, compiled prompt, audit log, interaction history, timestamps, and `interaction_session_version`. `WorkflowRun` adds one logical task lifecycle around this session; each User Decide gate becomes an `InteractionCheckpoint` and does not terminate the run.

The Visual Context Firewall defaults to `inherit_previous_visuals = false`. Prior-run visual artifacts stay available for replay/logging and future anti-repetition analysis, but are not generation context. Explicit inheritance requests are limited to the named visual fields.

The runtime writes `sessions/<session_id>/session.json`, appends `events.jsonl`, and reserves `artifacts/`. Session JSON is saved atomically after a gate resolution and before the next pipeline stage. Post-generation repair attempts, exact prompts, reviews, outcomes, and `best_artifact` are also persisted under `artifacts/repair/`; replay reads them without invoking ImageGen. A legacy `creative_session.json` can still be loaded in memory with `AI_DECIDE` as the default; the old file is never rewritten.

## Events and gate results

`InteractionEvent` contains `event_id`, `session_id`, `gate_id`, `action`, `payload`, and `timestamp`. The current gate id is persisted and regenerated on rollback. Old events return `STALE_GATE_EVENT`; duplicate event ids return the original response without applying the event twice.

`GateResolution` contains `gate_id`, `gate_type`, `resolution_status`, `selected_values`, `decision_source`, `human_override`, `delegated`, `unresolved_fields`, `rationale`, and `timestamp`. Rationale is concise audit text, never hidden chain-of-thought.

`InteractiveResponse` is the Codex-facing layer: session, mode, status, stage, human message, compact options, recommendation, unresolved fields, allowed actions, progress labels, and internal artifact references. The user does not receive the full session JSON by default.

## User Decide actions

The natural-language layer maps ordinary replies onto the same actions: `B`, `我选第二个`, and `最后一个` select candidates; `A 和 C 混一下` creates a MIX; field phrases such as `发色选 C` or `鞋子裸足` become field updates; `你来决定` delegates; `其他推荐` accepts recommendations without becoming delegation. The parser is deterministic and gate-aware; it does not mutate state or invent a selection.

`SELECT B` resolves one candidate. `MIX A+C` combines candidates without rerunning Explore. `CUSTOM` stores a human-authored direction. `DELEGATE` resolves the current gate with AI. `PARTIAL_DELEGATE` stores named human values and delegates unresolved fields. `USE_RECOMMENDED` accepts one proposed value; `USE_ALL_RECOMMENDED` accepts all remaining recommendations in one event. A recommendation alone remains unresolved.

Question-only replies such as `为什么推荐 B？` return an explanation while keeping the current gate, selections, locks, and provenance unchanged. Ambiguous replies such as `中间那个` request the smallest clarification instead of guessing. `CANCEL`, `CONTINUE`, `BACK`, mode-switch language, and `REGENERATE_OPTIONS` are also parsed at this seam.

Explicit requirements are extracted before exploration and stored as `explicit_user`. If a requirement targets a later visual field while Character or Art Direction is open, it is stored in `pending_constraint_updates`, applied when the Visual Preference Sheet opens, and removed from future questions. Positive and negative constraints both reach Final Design and PromptCompiler; recommendations and defaults cannot overwrite them.

After a selection, the Persistent Runner's `continue_workflow(run_id, user_message)` invokes the underlying `resume_session` seam and automatically runs Character Planning, Art Explore, or Final Design as appropriate, stopping only at the next unresolved checkpoint. No new user task or “continue” message is required.

## Rollback and invalidation

`BACK` records a rollback event and preserves original input, previous choices, and interaction history. Returning to Character invalidates Character Plan, Art Explore, Art selection, Visual Preferences, Final Design, and Prompt. Returning to Art invalidates Visual Preferences, Final Design, and Prompt. Changing one Visual Preference invalidates only affected Final Design fields plus Final Design and Prompt.

Mode changes record `from_mode`, `to_mode`, `stage`, `reason`, and `timestamp`. A forward switch from User Decide to AI Decide resolves the current gate and continues the same session; switching back can reopen the most recent recoverable gate.

## Provenance and hard-rule priority

The runtime distinguishes `explicit_user`, `quick_ai_fill`, `policy_default`, `delegated_ai`, `human_select`, `human_mix`, `human_custom`, and `human_accept_recommended`. Explicit user requirements always outrank recommendations and defaults. Accepting a recommendation is not delegation, including the all-recommended shortcut. All modes retain the Global Rendering Style, Regional Visual Language, Lower-Body rules, Playable Character Design Gate, Prompt Audit, and the frozen Pose System.

## Failure policy

Final Design failure never reaches PromptCompiler. Quick and AI Decide may perform one bounded automatic retry. User Decide receives the reason and returns to Art Direction so a human can choose again, request a new direction, or delegate. A second failure becomes `BLOCKED`; the runtime never loops indefinitely.

After an image review, an explicitly authorized targeted repair consumes only the current run's critic targets and contract. Passing HARD fields are locked, the original prompt remains unchanged, and an external ImageGen regeneration must be re-reviewed before acceptance. Regression keeps the original best artifact; two repair attempts are the maximum.

## Demo boundary

Deterministic Quick, AI Decide, and User Decide transcripts live under `examples/interaction_demos/`. They verify the runtime contract without images. The existing regional, lower-body, leg, and pose tests remain separate regressions.
