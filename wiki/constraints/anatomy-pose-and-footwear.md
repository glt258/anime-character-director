---
title: Anatomy, Pose, and Footwear Constraints
description: Current hard constraints and review outcomes for pose, anatomy, and footwear.
tags: [constraint, anatomy, pose, review]
sources: ["[[SKILL.md]]", "[[tests]]", "runtime/pose_intent_runtime.py"]
updated: 2026-09-15
type: constraint
related: ["[[architecture/skill-and-runtime]]"]
---

# Anatomy, Pose, and Footwear

The workflow enforces `NO_CROSSED_LEGS_HARD_INVARIANT = true` for normal two-legged humanoids. A front-facing axis, stable joint relationships, readable hands and feet, and explicit footwear checks are required for review. Hip twists, stockings, heels, and other costume choices remain separate design dimensions; none can override leg separation.

`LegSeparationContract` requires separate thighs, knees, calves, ankles, and feet, no centerline crossing, no leg-occlusion crossing, and readable negative space. `LegSeparationGate` returns `PASS`, `FAIL`, or `UNCERTAIN`; only `PASS` can promote a candidate. `FAIL` and `UNCERTAIN` are blocking, and one pose-only regeneration is allowed before `LEG_GEOMETRY_UNRESOLVED`.

`FAIL` triggers targeted repair or a stop; `UNCERTAIN` requires human review. These checks are guardrails for evidence-backed iteration, not a claim that generated images are anatomically perfect.

Pose semantics are reviewed separately from anatomy. `PoseIntentContract` preserves the requested body-language target and `PoseIntentGate` checks actual-image stance width, foot depth, weight side, knee state, torso, shoulders, arms, head angle, energy, and visible intent signals. `LegSeparationGate = PASS` alone is insufficient: `POSE_VALID` requires a `STRONG` or `ACCEPTABLE` pose-intent result as well. Semantic erosion remains `POSE_INTENT_FAIL`, not `ANATOMY_FAIL`.

The intent layer specifically protects elegant controlled asymmetry, sensual body confidence beyond clothing, relaxed asymmetry, low-energy signals, genuine narrow stance, and genuine one-foot-forward depth. A bounded pose-intent-only repair may change body language fields only and must rerun `LegSeparationGate`. `PoseDiversityLedger` records actual pose features and reports `SAFE_POSE_HOMOGENIZATION` as a soft diagnostic.
