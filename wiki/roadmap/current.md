---
title: Current Roadmap
description: Explicit next steps and blockers for the character director workflow.
tags: [roadmap, future-work]
sources: ["[[README.md]]", "[[SKILL.md]]", "[[reports]]", "2026-09-14/regional_visual_language_layer_request.md"]
updated: 2026-09-16
type: roadmap
related: ["[[00-overview]]", "[[experiments/benchmark-status]]"]
---

# Current Roadmap

`ANIME_CHARACTER_DIRECTOR_V1_0_0 = RELEASED`. The v1.0.0 public surface is frozen to `QUICK`, `AI_DECIDE`, and `USER_DECIDE`; the default is `AI_DECIDE`. The items below are retained implementation history and post-v1 research context, not release blockers.

## Post-v1 roadmap

Post-v1 work may address global design diversity, silver/white-hair bias, outfit-template bias, pose-vocabulary expansion, base-model visual-prior analysis, LoRA step1000 evaluation, a broader 20–30 character diversity benchmark, stronger memory anchors, more aggressive silhouette diversity, and splash-art montage shortcuts. None is part of the v1.0.0 release gate.

The runtime should continue to expose hashes, lineage, checkpoints, and retry scope. Image-generation variability and human review capacity remain known research risks; external autonomous agents and unverified API behavior remain outside the project contract.

The Regional Visual Language Layer is now implemented and the six archetype images are registered as negative regression metadata rather than positive references. Next: complete Human Review of the six-case [[experiments/character-archetype-generalization-v1]] result, then run a separately approved regression benchmark using fresh images and independently labeled regional/style observations. Do not use the current negative fixtures as ImageGen references.

The lower-body patch is implemented without generating images: new choices are explicit, actual-image grounding is testable, and coverage/legwear/footwear repetition is a soft diagnostic. The next benchmark should separately test adult choice, minor safety, male lower-body diversity, and exact footwear/legwear grounding.

Regional layer hardening is implemented without regenerating the six cases: provenance now covers selection and delegation, migration emits an audit record, RegionalStyleReview exposes richer actual-image evidence, and archetype/body/outfit/background shortcut diagnostics are available. The next approved A/B benchmark should exercise these labels with fresh images.

The approved Regional Style A/B Regression v2 is complete through generation and awaits Human Review of the six-image gallery and report. The unchanged A-F inputs produced one fresh first-pass image per case; the result is 4/6 blind Regional YES, with B generic-RPG drift and C pseudo-oriental/fashion-editorial drift. Global gates pass, outfit/background and safe-stance collapse are absent, and lower-body covered-leg plus closed-shoe coverage is 4/6. Do not start v3 until Human Review explicitly authorizes it.

Human Review is now recorded for the Regional Style A/B v2 images. E is accepted; A, B, C, and D require anatomy corrections; F requires a ground-up design rebuild because it reads as an NPC rather than a 二游 playable character. No generation has started after review. The next action is an explicitly authorized correction/rebuild plan, not an automatic v3.

Correction v1 is now generated under explicit user authorization: A-D have one bounded candidate edit, E is carried forward, and F has one fresh no-reference rebuild candidate. Next step is Human Review of these candidates; do not start another retry or v3 automatically.

The 2026-09-15 C + E Targeted Reconstruction is complete through one fresh no-reference first pass per case. C uses `Clean-Line Tailoring`; E uses `Aquatic glassfin humanoid` selected from three species directions. Both remain `C_E_RECONSTRUCTED_PENDING_HUMAN_REVIEW`. Next step is direct Human Review of the C/E gallery; do not generate another retry automatically. A/B/D/F remain frozen.

Human Review found C too conservatively dressed and both C/E cross-legged. Correction v1 is complete with one successful candidate per case: C uses more fashion-forward `Open-Edge Tailoring`, and E retains the glassfin design with a square separated stance. Current state is `C_E_CORRECTED_PENDING_HUMAN_REVIEW`; next step is user review only. Do not generate another retry automatically. A/B/D/F remain frozen.

The 2026-09-15 hardening pass promotes no-crossed-legs from prompt advice to the global `LegSeparationContract` and actual-image `LegSeparationGate`. Next implementation step is Human Review of the invariant documentation and later rerun approval; no image generation or automatic experiment starts from this change.

Pose Intent Preservation v1 is now implemented without image generation. `PoseIntentContract` and `PoseIntentGate` preserve requested body language independently from leg safety; PromptCompiler emits intent signals before the hard leg block; legacy artifacts migrate conservatively; pose-intent-only repair is bounded and reruns leg safety; `PoseDiversityLedger` detects non-blocking safe-pose homogenization. Targeted and full regression are required before the state moves beyond `POSE_INTENT_PRESERVATION_IMPLEMENTED_PENDING_HUMAN_REVIEW`; do not start another image benchmark automatically.

Pose System v1 is now `POSE_SYSTEM_V1_ACCEPTED` and `ACCEPTED / FROZEN`. Human Review accepted the real-image stress and Pose Intent A/B evidence: 6/6 no-crossed-legs, 6/6 Leg Safety PASS, Pose Intent retained, and no obvious safe-pose homogenization without repair or cherry-pick. Do not continue Pose System development or start another pose benchmark. Future work may address higher-fidelity Detailed Design / Repair only after an explicit request or a clear regression/blocker.

Interaction System + Three Creation Modes v1 is accepted and frozen as `THREE_MODE_INTERACTION_SYSTEM_V1_ACCEPTED` / `ACCEPTED / FROZEN`. `QUICK`, `AI_DECIDE`, and `USER_DECIDE` share one pipeline and use resolver-specific gate strategy; `CreativeInteractionSession` persists state, `InteractionEvent` resumes the same session, and the runtime covers rollback, mode switching, stale-gate protection, idempotency, restart loading, and legacy artifact migration. Deterministic text-only demo fixtures and focused tests are included. The generation boundary is `GENERATION_READY`; no image generation or `$imagegen` call was made.

The 2026-09-15 Three Mode Interaction UX Acceptance v1 baseline remains historical: 43 scenarios, 10 PASS and 33 FAIL before the natural-language fix. The fix adds a deterministic parser, pending later-field constraints, no-reask locking, recommendation-vs-delegation provenance, cancellation, regeneration, and natural mode switches. The exact 43-scenario post-fix rerun passed and Human Review accepted the interaction contract; no image generation was started.

The post-fix exact 43-scenario rerun passed 43/43, and Human Review accepted the interaction contract as `THREE_MODE_INTERACTION_SYSTEM_V1_ACCEPTED` / `ACCEPTED / FROZEN`. Focused parser/runtime regression passed 47 tests. The next stage is recorded as `THREE_MODE_GENERATION_QUALITY_BENCHMARK`, but it must not start automatically.

The Generation Quality Benchmark v1 was intentionally aborted after 8/8 QUICK and AI_DECIDE first-pass images because USER_DECIDE gates were being treated as task termination points. The eight images and artifacts are retained; the old Brief A USER_DECIDE run is marked superseded. Persistent Interactive Workflow Runner v1 keeps one `WorkflowRun` across checkpoints, restarts, Custom Input, and localized continuation. Human Acceptance v1 passed HA-01 through HA-15 plus the required exception scenarios on 2026-09-15, with zero observed image-generation calls. The project state is now `PERSISTENT_INTERACTIVE_WORKFLOW_V1_ACCEPTED`; `GENERATION_QUALITY_BENCHMARK_UNBLOCKED` is the next-stage recommendation and requires explicit authorization before starting.

Codex-native interaction integration v1 is released as a presentation/orchestration adapter. `runtime/codex_interaction_adapter.py` converts persisted USER_DECIDE checkpoints to three-choice `request_user_input` specs, keeps stable candidate ids separate from localized labels, maps native Other to `__CUSTOM__`, and fails closed for invalid or stale answers. `PersistentWorkflowRunner.continue_native_workflow` continues the same WorkflowRun to the next checkpoint or `GENERATION_READY`.

The 2026-09-16 `NEGATION_SCOPE_AND_RECOMMENDATION_REGRESSION_FIX_V1` passed its full regression gate: `不要粉色长发` is one same-entity prohibited combination, Character A/B/C boundaries and atomic rules are retained, and recommendation aliases apply only to unresolved fields. Generation Quality Benchmark v2 is now `COMPLETE_WITH_REPLAYED_USER_DECIDE_DISCLOSURE`; its remaining research is post-v1.
