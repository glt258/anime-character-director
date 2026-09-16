---
title: Generation Quality Benchmark v2 Summary
description: Internal release evidence for the three public creation modes.
type: benchmark-summary
status: COMPLETE_WITH_REPLAYED_USER_DECIDE_DISCLOSURE
updated: 2026-09-16
---

# Generation Quality Benchmark v2 Summary

This is internal release evidence for the public `anime-character-director v1.1.0` documentation release. It is not required knowledge for normal Skill use.

## Scope

- Four benchmark characters: A, B, C, and D.
- Three public modes: `QUICK`, `AI_DECIDE`, and `USER_DECIDE`.
- Twelve comparable primary generations: four characters × three modes.
- Style contract: contemporary commercial gacha anime; the style lock remained stable.
- Runtime: frozen after the compound-negation parser and propagation fix.
- QUICK / AI_DECIDE were fresh autonomous runs; USER_DECIDE rows replayed previously recorded real-human selections under the frozen runtime.
- No benchmark regeneration was used.

## Results

- Crossed-leg findings: `0/12`.
- Black-stockings findings: `0/12`.
- High-heels findings: `0/12`.
- C non-human constraint failure: `0/3`.
- Major generation failures: `0/12`.
- Hand audit limitation: `4/12` were not fully auditable because of occlusion; occlusion was not counted as PASS.
- No single mode dominates every dimension. QUICK has the lowest interaction cost, AI_DECIDE is strongest overall on the comparable scores, and USER_DECIDE is strongest where human intervention supplied meaningful B/C direction.

## Mode averages

| Mode | Style | Appeal | Identity | Coherence | Commercial | Pose | Anatomy | Fidelity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| QUICK | 9.00 | 8.50 | 8.50 | 8.50 | 8.25 | 8.25 | 7.25 | 9.00 |
| AI_DECIDE | 9.00 | 9.00 | 8.75 | 9.00 | 8.75 | 8.25 | 7.50 | 9.25 |
| USER_DECIDE | 9.00 | 8.75 | 9.00 | 9.00 | 8.50 | 8.00 | 7.75 | 9.00 |

## USER_DECIDE disclosure

The four USER_DECIDE comparison rows use `replayed previously recorded real-human selections under the frozen runtime`. They are not four new live native-UI sessions in this release run. Native UI authenticity is covered by the separate interaction acceptance evidence and runtime tests.

## Constraint evidence

The fixed parser represents `不要粉色长发` as one same-entity prohibited compound:

```text
NOT (pink AND long hair)
```

It does not promote `pink` or `long hair` into positive character fields. Positive constraints, atomic prohibitions, archetype prohibitions, pose, footwear, and species constraints remain supported.

## LoRA and research boundary

`LORA_NOT_PRIMARY_BOTTLENECK`. v1.1.0 does not automatically resume step1000, retrain, recollect data, or change captions. Global diversity, hair/outfit prior analysis, pose vocabulary expansion, and broader 20–30 character benchmarks are `POST_V1` research.

## Source artifacts

- Full report: `D:/benchmark/outputs/three_mode_generation_quality_v2_20260915/GENERATION_QUALITY_BENCHMARK_V2_REPORT.md`
- Mode comparison: `D:/benchmark/outputs/three_mode_generation_quality_v2_20260915/mode_comparison.md`
- Constraint audit: `D:/benchmark/outputs/three_mode_generation_quality_v2_20260915/post_fix_mode_comparison_20260916/audit/USER_DECIDE_POST_FIX_COMPARABILITY_AUDIT.md`
- Runtime freeze: `D:/benchmark/outputs/three_mode_generation_quality_v2_20260915/post_fix_mode_comparison_20260916/benchmark_runtime_freeze_20260916.md`
