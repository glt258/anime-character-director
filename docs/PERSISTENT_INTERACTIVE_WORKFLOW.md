---
title: Persistent Interactive Workflow Runner v1
description: One logical character-creation workflow across multiple interaction turns and process restarts.
type: architecture
status: ACCEPTED / FROZEN
confidence: high
created: 2026-09-15
updated: 2026-09-15
tags: [interaction, workflow, persistence, checkpoints, locale]
sources: ["[[SKILL.md]]", "[[../references/workflow.md]]", "runtime/workflow_runner.py"]
related: ["[[INTERACTION_SYSTEM]]"]
---

# Persistent Interactive Workflow Runner v1

## Purpose

`WorkflowRun` is the product-level lifecycle above `CreativeInteractionSession`. One character creation remains one logical run even when the conversation pauses at Character Direction, Art Direction, Visual Preferences, or a Custom Input checkpoint. A process restart or a new model turn reloads the same run; it does not create a new character task.

The runner is a continuation seam, not a blocking process. It persists state, returns a user-facing checkpoint, and resumes when the next conversation message arrives. It never busy-waits, sleeps for input, or requires the user to type `resume`, `continue`, a session id, or an event name.

## Models

`WorkflowRun` stores `run_id`, the underlying `session_id`, `creation_mode`, original input, status, current stage and checkpoint, checkpoint history, timestamps, generation intent, continuation expectation, interaction locale, and schema version. The persisted file is `sessions/<session_id>/workflow_run.json`; the existing `session.json` and `events.jsonl` remain the source of pipeline facts.

`InteractionCheckpoint` stores a stable checkpoint id, run and gate identity, stage, localized prompt payload, localized options, custom-input capability, stable `__CUSTOM__` option id, user-facing action hints, lifecycle status, and resolution metadata. Checkpoint transitions are append-only in `checkpoints.jsonl`; a resolved checkpoint is never resolved again.

`InteractionOption` separates stable internal `option_id` and `internal_label` from locale-specific display title and description. The Codex-native adapter exposes up to three real candidates, keeps the recommended candidate first, and lets the client provide `Other`; the adapter never adds a visible Custom option to the native request. `__CUSTOM__` remains the internal id for the client's free-form Other result. Letter aliases remain compatibility-only.

## Continuation

`start_workflow(...)` creates one run and delegates the shared pipeline to `InteractionRuntime`. QUICK and AI_DECIDE normally return `GENERATION_READY` with zero human checkpoints. USER_DECIDE returns the first open checkpoint and persists the run as `WAITING_FOR_INTERACTION`.

`continue_workflow(run_id, user_message)` remains the fallback text seam. `continue_native_workflow(run_id, answer, checkpoint_id=...)` loads the current open checkpoint, maps the Codex answer through `runtime/codex_interaction_adapter.py`, validates checkpoint/revision scope, resolves it, saves atomically, and advances the same pipeline until the next checkpoint or a terminal boundary. A missing, stale, duplicated, or unmappable native answer leaves the run waiting. `continue_active_workflow(user_message)` remains the compatibility path for ordinary text controls.

The runner also supports an explicit `checkpoint_id` for deterministic integrations and stale-reply tests. A reply for a resolved, superseded, or non-current checkpoint returns a user-facing stale message and cannot mutate the run. Existing event idempotency, gate id validation, provenance, BACK, mode switching, regeneration, explicit constraints, recommendation separation, and partial delegation remain owned by `InteractionRuntime`.

## Custom input

Candidate gates expose all real candidates plus an extra Custom option. Selecting Custom resolves only the presentation checkpoint and opens a `CUSTOM_INPUT_GATE` in the same run. The next natural-language message becomes `human_custom`, is sent to the underlying gate, and automatically continues to the next checkpoint. Direct phrases such as `我想自己定：整体偏慵懒，但有一点危险感` are also parsed as Custom without first selecting the displayed Custom option. Visual Preference accepts field-level custom values and one-message overrides such as `发色银白，鞋子裸足，其他按推荐`.

`都不喜欢，再来一批` remains `REGENERATE_OPTIONS`; `都不喜欢，我想要……` remains `CUSTOM`. These paths create no new WorkflowRun.

## Locale

The runner determines `interaction_locale` once at creation from an explicit locale or a small Chinese/English request-language heuristic, defaulting to English when uncertain. The locale stays stable across checkpoints unless a future explicit language-switch command updates it. Localized titles, descriptions, recommendation labels, action hints, custom prompts, and progress copy are rendered by `InteractionLocalizer`; internal ids and enums remain unchanged.

Native users see three localized dynamic candidate labels followed by Codex's client-owned `Other`. The stable internal ids are persisted separately from display labels; the native answer mapping is scoped to the current checkpoint and candidate revision. Chinese/English letter labels remain only for the natural-language compatibility parser.

## Native Skill integration

The Skill treats an active waiting `WorkflowRun` as the default target for the next interaction. In the normal USER_DECIDE path it builds a `NativeInteractionSpec`, calls Codex `request_user_input`, maps the real answer with the adapter, and calls `continue_native_workflow` directly. A short text choice remains a compatibility continuation, not the native happy path. Only explicit cancellation plus a new-role request, or a clearly unrelated task, leaves the current run. The Skill layer does not expose session ids, checkpoint ids, resolver names, raw status enums, or provenance labels in normal conversation text.

The native adapter is a presentation/orchestration boundary: Python owns checkpoint state, stable ids, persistence, resolution, and continuation; the host owns the selection UI. It does not import `request_user_input`. Visual Preference emits multiple native questions, and native `Other` carries custom text into the existing same-run Custom path.

`GENERATION_READY` remains the local runtime boundary. After it, the Codex Skill orchestration may continue with built-in `$imagegen` only after the design is valid, then run the existing Style and Anatomy quality audit before Human Review.

An explicitly authorized targeted visual repair is a post-generation action on the same run. It uses the current `VisualAdherenceCritic.repair_targets`, locks passing HARD fields, compiles a separate `RepairPromptBundle`, and requires a fresh external observation/critic review. The runtime has no image-edit or mask backend, so the first version uses bounded full-image regeneration with a maximum of two idempotent attempts; repair artifacts and `best_artifact` are replayable without calling ImageGen.

## Persistence and restart

The runner uses temporary-file replacement for `workflow_run.json`, while the existing session runtime uses the same atomic-save pattern for `session.json`. A fresh `PersistentWorkflowRunner` pointed at the same session root can load the run and continue it without any user-visible restart ceremony.

## Boundary

Persistent Interactive Workflow v1 ends at `GENERATION_READY`. It owns checkpoint persistence and continuation; image generation and post-generation review remain separate Skill stages.

## Related

- [[INTERACTION_SYSTEM]] — shared pipeline, resolver, provenance, and hard-rule ownership
