---
type: experiment
title: Three Mode Interaction UX Acceptance v1
status: historical
confidence: high
created: 2026-09-15
updated: 2026-09-15
tags: [interaction, ux, natural-language, acceptance]
related: ["[[architecture/interaction-system]]", "[[roadmap/current]]"]
sources: ["[[../../outputs/three_mode_interaction_ux_acceptance_v1_20260915/three_mode_ux_acceptance_report]]", "[[../../scripts/run_three_mode_ux_acceptance_v1.py]]"]
---

# Three Mode Interaction UX Acceptance v1

The baseline acceptance run executed 43 scenarios against the pre-fix `QUICK`, `AI_DECIDE`, and `USER_DECIDE` runtime on 2026-09-15. It did not call image generation and did not modify production code. Results were 10 PASS and 33 FAIL, with the generation boundary held at `GENERATION_READY` or earlier. This page is retained as historical evidence; the post-fix acceptance is recorded in [[../interaction-natural-language-constraint-fix-v1]] and [[../../docs/THREE_MODE_INTERACTION_V1_ACCEPTANCE]].

The shared pipeline, structured rollback, stale-gate protection, duplicate-event idempotency, structured restart resume, three-gate shape, concise user messages, and generation boundary passed their direct checks. The primary blocker is the user-facing natural-language surface: short replies (`B`, `第二个`), natural MIX/CUSTOM, recommendation questions, delegation, partial delegation, all-recommended, cancellation, mode-switch wording, and multi-field visual instructions are not reliably mapped by the current coercion path. Some malformed natural inputs are accepted as `human_custom` instead of being held safely.

Additional findings include inconsistent Quick-mode phrase detection and explicit-constraint extraction, `CANCEL` being enumerated but not handled, and field-level recommendation provenance being remapped during final locking. `REGENERATE_OPTIONS` remained a UX gap in that baseline. The result at that time was `THREE_MODE_INTERACTION_UX_ACCEPTANCE_FAILED`; the findings were subsequently fixed and accepted in the post-fix review.

Evidence: the immutable per-scenario transcripts, session snapshots, event logs, and UX reviews are under `outputs/three_mode_interaction_ux_acceptance_v1_20260915/`.
