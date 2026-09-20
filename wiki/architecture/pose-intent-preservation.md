---
title: Pose Intent Preservation
description: Separate body-language intent from hard leg safety and validate both on actual-image evidence.
tags: [architecture, pose, runtime, gate]
sources: ["runtime/pose_intent_runtime.py", "runtime/regional_style_runtime.py", "SKILL.md"]
updated: 2026-09-15
type: architecture
status: ACCEPTED / FROZEN
related: ["[[architecture/skill-and-runtime]]", "[[constraints/anatomy-pose-and-footwear]]"]
---

# Pose Intent Preservation

The project now separates body-language meaning from leg safety. `LegSeparationContract` and `LegSeparationGate` remain the hard invariant for independent thighs, knees, calves, ankles, feet, centerline lanes, and readable negative space. `PoseIntentContract` records what the requested pose should communicate and cannot disable the leg contract.

Supported intent types are `ELEGANT`, `SENSUAL`, `RELAXED_ASYMMETRIC`, `LOW_ENERGY`, `NARROW_STANCE`, `ONE_FOOT_FORWARD`, `OPEN_STANCE`, `WIDE_ACTIVE`, `STABLE_OPEN`, and `CUSTOM`. Legacy artifacts are mapped only when the old pose family is reliable; ambiguous values become `UNKNOWN_LEGACY_POSE_INTENT` instead of inventing a user choice.

`PromptCompiler` emits a `POSE INTENT` block before `LEG GEOMETRY / ANATOMY CONSTRAINT`. The block expands intent into observable signals and preserves requirements for stance width, foot depth, asymmetry, energy, torso, arms, and head. The six high-risk cases have distinct checks: elegant needs controlled intentional body language, sensual needs body confidence beyond clothing, relaxed-asymmetric needs visible asymmetry, low-energy needs at least two low-energy signals, narrow needs actual narrow width, and one-foot-forward needs actual depth.

`PoseIntentGate` consumes actual-image observations and returns `STRONG`, `ACCEPTABLE`, `WEAK`, or `FAIL`. Overall `POSE_VALID` requires `LegSeparationGate = PASS` and a passing pose-intent result. Semantic erosion is reported with pose-intent failure types such as `NARROW_STANCE_EXPANDED`, `ONE_FOOT_FORWARD_DEPTH_MISSING`, and `LOW_ENERGY_READ_MISSING`; it is not relabeled as anatomy failure.

If leg safety passes but intent fails, a bounded pose-intent-only repair may change body language, stance width, foot depth, torso, shoulders, arms, head, and energy only. It preserves character identity, outfit, palette, body build, footwear, regional style, and background direction, then reruns the leg gate. `PoseDiversityLedger` records actual pose features and reports non-blocking `SAFE_POSE_HOMOGENIZATION` when different names resolve to materially identical body language.

## Scope boundary

The combined pose system is part of the current fast-generation production baseline. This is a contract boundary, not a claim that every future pose problem is completely solved.

Future detailed pose refinement belongs to an explicitly requested Detailed Design / Repair stage. Ordinary character-design experiments must not casually alter the crossed-leg policy, leg contract, pose-intent semantics, gate thresholds, or diversity logic unless a clear regression or blocker is found.

## Related

- [[architecture/skill-and-runtime]] — overall Skill/runtime boundary.
- [[constraints/anatomy-pose-and-footwear]] — hard leg safety and pose review boundary.
