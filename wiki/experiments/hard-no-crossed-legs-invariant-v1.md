---
type: experiment
title: HARD NO-CROSSED-LEGS Invariant v1
description: Runtime hardening that turns leg separation from prompt advice into a blocking generation invariant.
aliases: [Leg Separation Contract, No Crossed Legs Hardening]
tags: [architecture, anatomy, pose, runtime, invariant]
sources: [2026-09-15/hard_no_crossed_legs_invariant_v1_request.md]
status: NO_CROSSED_LEGS_HARDENED_ACCEPTED
confidence: high
created: 2026-09-15
updated: 2026-09-15
related: [architecture/skill-and-runtime, constraints/anatomy-pose-and-footwear, experiments/benchmark-status]
---

# HARD NO-CROSSED-LEGS Invariant v1

The former soft `NO CROSSED LEGS` wording is now a runtime hard invariant for normal two-legged humanoid anatomy. `NO_CROSSED_LEGS_HARD_INVARIANT = true`; there is no user-facing override. It applies to thighs, knees, calves, ankles, feet, centerline crossing, and leg-occlusion crossing.

## Runtime contract

`runtime/leg_separation_runtime.py` owns `LegSeparationContract`, pose-family risk classification, forbidden-pose validation, positive/negative geometry wording, `LegSeparationGate`, candidate promotion, migration, and bounded pose-only repair. `PromptCompiler` emits a dedicated `LEG GEOMETRY / ANATOMY CONSTRAINT` block and rewrites or rejects conflicting pose language.

Safe pose diversity remains available through open-parallel, offset non-overlapping, asymmetric-weight, wide-active, narrow-separated, low-energy-separated, and forward-step-non-crossing families. Crossed, scissored, ankle-cross, leg-over-leg, closed-leg-twist, coy-leg, and fashion-model-crossed families are forbidden. The body centerline separates left and right leg lanes; forward/back depth is allowed only without lateral crossover.

## Actual-image gate and promotion

`LegSeparationGate` checks thighs, knees, calves, ankles, feet, centerline crossing, and negative space. Results are `PASS`, `FAIL`, or `UNCERTAIN`; `UNCERTAIN` is non-promotable. Any crossing produces `LEG_CROSSING_BLOCKING_FAIL` plus the most specific failure type. Only `PASS` returns `PROMOTED_TO_CANDIDATE`. Normal production permits one pose-only regeneration that keeps identity, outfit, palette, body, accessories, regional style, fanservice, and background; a second failure becomes `LEG_GEOMETRY_UNRESOLVED`. First-pass benchmarks preserve failures as labeled samples without counting them as PASS.

The leg feature ledger records `stance_family`, `thigh_relation`, `knee_relation`, `calf_relation`, `ankle_relation`, `foot_relation`, `centerline_crossing`, `leg_negative_space`, and the serialized `leg_separation_gate` result. `SAFE_POSE_PRIOR_OVERRIDE_FAIL` marks a return to a crossed-leg prior despite an otherwise safe pose specification.

## Compatibility and evidence

Legacy artifacts receive the all-true contract and a safe pose-family default in memory without rewriting historical files. Visual Preference pose options are prevalidated. The schema exposes `leg_separation_contract`, `leg_separation_gate`, `pose_family`, `leg_crossing_risk`, `centerline_crossing`, `candidate_promotion_status`, and `pose_repair_count`. No image was generated and no Regional/Lower-Body/Fanservice rule was changed in this implementation round.

Implementation evidence: targeted runtime and direct dependency tests pass; the full regression suite was not run because the user requested a bounded hardening change and the global test policy forbids unnecessary full-suite runs.

## Human acceptance and freeze

Human Review accepted this invariant after the real-image stress benchmark: 6/6 first-pass images had no crossed legs and all six passed `LegSeparationGate`, with no automatic repair or cherry-pick. The invariant is now frozen as the fast-generation baseline. This acceptance is scoped to the current production baseline and does not claim that all future pose problems are completely solved; detailed refinement remains a separate future mode.
