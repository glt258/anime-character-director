---
type: experiment
title: Pose Intent Preservation A/B Re-test v2
description: Human-accepted real-image A/B validation of pose intent preservation alongside hard leg safety.
aliases: [Pose Intent A/B v2, Pose Intent Preservation Re-test]
tags: [experiment, benchmark, pose, anatomy, runtime]
sources: [2026-09-15/pose_system_v1_human_acceptance.md, runtime/pose_intent_runtime.py, runtime/leg_separation_runtime.py]
status: POSE_INTENT_AB_ACCEPTED
confidence: high
created: 2026-09-15
updated: 2026-09-15
related: [architecture/pose-intent-preservation, experiments/hard-no-crossed-legs-invariant-v1, experiments/benchmark-status, roadmap/current]
---

# Pose Intent Preservation A/B Re-test v2

Six unchanged high-level cases were generated from text only, one first-pass image per case, with no repair, reroll, image reference, or cherry-pick. The current pipeline was used end to end: pose parsing, Final Design, PromptCompiler, image generation, actual-image review, `LegSeparationGate`, and `PoseIntentGate`.

Human Review accepted the result: 6/6 images had no crossed legs, 6/6 passed Leg Safety, all six pose-intent results were `STRONG`, and the six cases retained distinct semantic reads. A, B, D, E, and F improved against the previous run; C retained its already-successful relaxed asymmetry.

The benchmark establishes a fast-generation baseline. It does not claim that pose rendering is completely solved, and it does not authorize another Pose System experiment.

## Evidence

- Report: `D:/benchmark/outputs/pose_intent_ab_v2_20260915/pose_intent_ab_report.md`
- Gallery: `D:/benchmark/outputs/pose_intent_ab_v2_20260915/pose_intent_gallery.md`
- Status: `POSE_INTENT_AB_ACCEPTED`

## Related

- [[architecture/pose-intent-preservation]] — runtime separation of pose intent from leg safety.
- [[experiments/hard-no-crossed-legs-invariant-v1]] — hard leg invariant and actual-image gate.
- [[experiments/benchmark-status]] — consolidated benchmark evidence.
- [[roadmap/current]] — frozen baseline and future boundary.
