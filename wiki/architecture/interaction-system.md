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

`CreativeInteractionSession` persists the current stage, current gate, status, explicit constraints, choices, resolved preferences, final design, prompt, audit, and interaction history. `InteractionEvent` is the resume boundary: a valid selection mutates the current session and automatically continues until the next unresolved gate. `gate_id` rejects late replies, and `event_id` makes retries idempotent.

The first phase stops at `GENERATION_READY`. Existing Visual Preference, Regional Visual Language, Lower-Body, Leg Separation, Pose Intent, and Prompt Audit contracts remain authoritative; Pose System v1 remains `ACCEPTED / FROZEN`. Human Review accepted this interaction contract as `THREE_MODE_INTERACTION_SYSTEM_V1_ACCEPTED` / `ACCEPTED / FROZEN`, with the natural-language layer at `INTERACTION_NL_V1_ACCEPTED`. No image is generated and `$imagegen` is not called.

## Related

- [[skill-and-runtime]] — runtime ownership and the shared design workflow
- [[../decisions/human-authority]] — provenance and human override priority
- [[../roadmap/current]] — current implementation state and next review boundary
