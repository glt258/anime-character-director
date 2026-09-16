---
title: Interaction System v1
description: Durable three-mode session orchestration and gate resolution contract.
tags: [architecture, interaction, session, gates]
sources: ["[[../docs/INTERACTION_SYSTEM.md]]", "[[SKILL.md]]", "runtime/interaction_runtime.py"]
updated: 2026-09-15
type: architecture
status: ACCEPTED / FROZEN
related: ["[[skill-and-runtime]]", "[[../decisions/human-authority]]", "[[../roadmap/current]]"]
---

# Interaction System v1

The project now has exactly three top-level creation modes: `QUICK`, `AI_DECIDE`, and `USER_DECIDE`. They share one pipeline and differ only in `GateResolver` strategy. Quick is low-depth and non-blocking; AI Decide performs full exploration and records `delegated_ai`; User Decide waits at Character Direction, Art Direction, and one consolidated Visual Preference Sheet.

`CreativeInteractionSession` persists the current stage, current gate, status, explicit constraints, choices, resolved preferences, final design, prompt, audit, and interaction history. `InteractionEvent` remains the deterministic resume boundary, while [[persistent-interactive-workflow]] provides the product-level `WorkflowRun` and `InteractionCheckpoint` lifecycle. A valid ordinary user reply mutates the same run and automatically continues until the next checkpoint. `gate_id` rejects late replies, and `event_id` makes retries idempotent.

The accepted base interaction contract remains `THREE_MODE_INTERACTION_SYSTEM_V1_ACCEPTED` / `ACCEPTED / FROZEN`, with the natural-language layer at `INTERACTION_NL_V1_ACCEPTED`. The Persistent Runner is also `ACCEPTED / FROZEN` for v1.0.0. Existing Visual Preference, Regional Visual Language, Lower-Body, Leg Separation, Pose Intent, and Prompt Audit contracts remain authoritative; Pose System v1 remains `ACCEPTED / FROZEN`. The runner's local boundary is `GENERATION_READY`; Skill orchestration owns the later `$imagegen` handoff and quality audit.

## Related

- [[skill-and-runtime]] — runtime ownership and the shared design workflow
- [[../decisions/human-authority]] — provenance and human override priority
- [[../roadmap/current]] — current implementation state and next review boundary
