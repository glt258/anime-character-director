---
title: Current Roadmap
description: Explicit next steps and blockers for the character director workflow.
tags: [roadmap, future-work]
sources: ["[[README.md]]", "[[SKILL.md]]", "[[reports]]", "2026-09-14/regional_visual_language_layer_request.md"]
updated: 2026-09-15
type: roadmap
related: ["[[00-overview]]", "[[experiments/benchmark-status]]"]
---

# Current Roadmap

Near-term work is to strengthen head and costume identity, integrate fantasy elements without losing identity anchors, make anatomy and identity artifacts repeatable, and control visual diversity without erasing user choice.

The runtime should continue to expose hashes, lineage, checkpoints, and retry scope. Current blockers are image-generation variability and human review capacity. External autonomous agents and unverified API behavior remain outside the project contract.

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
