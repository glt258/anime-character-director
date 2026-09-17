---
title: Interaction System v1
description: Durable three-mode session orchestration and gate resolution contract.
tags: [architecture, interaction, session, gates]
sources: ["[[../docs/INTERACTION_SYSTEM.md]]", "[[SKILL.md]]", "runtime/interaction_runtime.py"]
updated: 2026-09-16
type: architecture
status: ACCEPTED / FROZEN
related: ["[[skill-and-runtime]]", "[[../decisions/human-authority]]", "[[../roadmap/current]]"]
---

# Interaction System v1

The project now has exactly three top-level creation modes: `QUICK`, `AI_DECIDE`, and `USER_DECIDE`. They share one pipeline and differ only in `GateResolver` strategy. Quick is low-depth and non-blocking; AI Decide performs full exploration and records `delegated_ai`; User Decide waits at Character Direction, Art Direction, and one consolidated Visual Preference Sheet.

`CreativeInteractionSession` persists the current stage, current gate, status, explicit constraints, choices, resolved preferences, final design, prompt, audit, and interaction history. `InteractionEvent` remains the deterministic resume boundary, while [[persistent-interactive-workflow]] provides the product-level `WorkflowRun` and `InteractionCheckpoint` lifecycle. A valid ordinary user reply mutates the same run and automatically continues until the next checkpoint. `gate_id` rejects late replies, and `event_id` makes retries idempotent.

New runs also persist the `Visual Context Firewall`: historical visual design is blocked from positive generation context by default (`inherit_previous_visuals = false`). Replay and candidate history remain retained, while future similarity analysis receives a separate `anti_repetition_only` path. Explicit user requests can enable only the named inherited visual fields; current-run gate outputs remain valid generation context.

`CrossRunNoveltyGuard` is the consumer of that one-way history path. It extracts a structured `DesignSignature` from Final Design/DesignDNA after design assembly and before prompt compilation, compares only recent completed fresh runs, and persists a `NoveltyReview` plus its first history snapshot. Structural fields dominate cosmetic fields; explicit inheritance is `EXEMPT`, and repair attempts do not create new signatures. No signature, prompt, image description, or critic prose is returned to Character Direction, Art Direction, Visual Preference, PromptCompiler, or repair prompts.

At `GENERATION_READY`, the host records the externally generated original image through `record_generation_artifact`. New sessions remain `strict_pending_generation` until this succeeds, then persist a `strict_complete` `GenerationArtifact` containing image/prompt hashes, prompt/manifest/contract references, run identity, mode, seed, and timestamp. Reviews, repair plans, repair generations, and `best_artifact` carry the corresponding generation identity; source hash/id mismatches block repair. Sessions without this metadata remain readable as `legacy_incomplete` and are not eligible for strict repair planning.

The accepted base interaction contract remains `THREE_MODE_INTERACTION_SYSTEM_V1_ACCEPTED` / `ACCEPTED / FROZEN`, with the natural-language layer at `INTERACTION_NL_V1_ACCEPTED`. The Persistent Runner is also `ACCEPTED / FROZEN` for v1.0.0. Existing Visual Preference, Regional Visual Language, Lower-Body, Leg Separation, Pose Intent, and Prompt Audit contracts remain authoritative; Pose System v1 remains `ACCEPTED / FROZEN`. The runner's local boundary is `GENERATION_READY`; Skill orchestration owns the later `$imagegen` handoff and quality audit.

## Related

- [[skill-and-runtime]] — runtime ownership and the shared design workflow
- [[../decisions/human-authority]] — provenance and human override priority
- [[../roadmap/current]] — current implementation state and next review boundary
