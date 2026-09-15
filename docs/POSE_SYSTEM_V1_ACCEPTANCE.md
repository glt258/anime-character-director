# Pose System v1 Acceptance

Date: 2026-09-15
Status: `POSE_SYSTEM_V1_ACCEPTED`
Freeze: `FROZEN`

## Human acceptance

Pose System v1 passed Human Review under fast-generation conditions:

> Pose System v1 在快速生成、无 repair、无 cherry-pick 条件下完成实际图片验证。
>
> 6/6 首发图未出现交叉腿；Pose Intent 仍然能够保留；没有观察到明显的安全姿势同质化。
>
> 当前质量足以作为快速生成模式的默认稳定版本。更高要求的姿势精修留给 Detailed Design / Repair 阶段处理。

This is an accepted production baseline, not a claim that every future pose problem is completely solved.

## Frozen scope

The frozen v1 scope covers:

- `NO_CROSSED_LEGS_HARD_INVARIANT`, `LegSeparationContract`, `LegSeparationGate`, pose-family risk classification, positive/negative leg geometry, Final Design validation, Prompt Audit, candidate blocking, and bounded pose-only repair.
- `PoseIntentContract`, `PoseIntentGate`, the `POSE INTENT` PromptCompiler section, migration/backward compatibility, `PoseDiversityLedger`, and `SAFE_POSE_HOMOGENIZATION` diagnostics.
- Regional/compiler integration, Visual Preference integration, schemas, regression tests, Skill guidance, reference docs, and Wiki records.

Unless a clear regression or blocker appears, do not change crossed-leg policy, leg geometry, pose-intent semantics, gate thresholds, or pose-diversity logic as part of ordinary character-design experiments.

## Validation evidence

- Pose Hard-Invariant Stress Benchmark v1: `POSE_HARD_INVARIANT_STRESS_ACCEPTED`.
- Pose Intent A/B Re-test v2: `POSE_INTENT_AB_ACCEPTED`.
- Local benchmark images remain under `D:/benchmark/outputs/` and are not Git release assets.
- Full regression: `py -3 -m pytest -q` — `94 passed`.
- Static/runtime checks: `py_compile`, YAML parse, Draft 2020-12 JSON Schema checks, and import smoke — all passed.

## Future boundary

Fast generation uses this frozen baseline by default. More exact pose shaping belongs to a future Detailed Design / Repair stage and requires its own explicit request and validation; it is not part of Pose System v1.
