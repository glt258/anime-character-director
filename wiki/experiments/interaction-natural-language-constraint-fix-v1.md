---
type: experiment
title: Interaction Natural Language Layer and Constraint Preservation Fix v1
status: accepted
confidence: high
created: 2026-09-15
updated: 2026-09-15
tags: [interaction, natural-language, constraints, provenance, regression]
related: ["[[architecture/interaction-system]]", "[[roadmap/current]]", "[[experiments/three-mode-interaction-ux-acceptance-v1]]"]
sources: ["[[docs/INTERACTION_SYSTEM]]", "[[SKILL]]", "[[runtime/interaction_runtime.py]]", "[[runtime/natural_language_interaction.py]]", "[[scripts/run_three_mode_ux_acceptance_v1.py]]"]
---

# Interaction Natural Language Layer and Constraint Preservation Fix v1

## Scope

This fix adds a deterministic, gate-aware natural-language parser at the interaction seam. It maps short candidate replies, ordinal replies, MIX, field-level visual updates, delegation, partial delegation, recommendation acceptance, cancellation, regeneration, questions, ambiguity, and natural mode switches onto the existing `InteractionEvent` runtime. The parser describes intent; runtime state transitions and gate legality remain in `InteractionRuntime`.

## Constraint contract

Explicit positive and negative requirements are extracted before exploration. A requirement aimed at a later visual field is stored in `pending_constraint_updates`, applied with `explicit_user` provenance when the Visual Preference Sheet opens, and excluded from later questions. Explicit constraints reach Final Design and PromptCompiler and outrank AI recommendations, defaults, and quick fills.

`human_accept_recommended` remains distinct from `delegated_ai`. Questions do not advance or lock a gate, and ambiguous phrases request the smallest clarification. Regeneration keeps the same session and records the prior and new option ids.

## Evidence

- Focused parser/runtime regression tests cover the new intent types, provenance, pending constraints, no-reask behavior, mode switching, cancellation, regeneration, stale events, idempotency, and legacy loading.
- The prior 43-scenario UX run remains the baseline evidence: 10 PASS and 33 FAIL before this implementation. The post-fix exact-scenario rerun is the acceptance evidence for this page.
- No image generation or `$imagegen` call is part of this change.

## Disposition

`THREE_MODE_INTERACTION_SYSTEM_V1_ACCEPTED` / `ACCEPTED / FROZEN`: Human Review accepted the exact 43-scenario rerun at 43/43, including the defined core set. See [[../../docs/THREE_MODE_INTERACTION_V1_ACCEPTANCE]].
