---
title: Three-Mode Interaction System v1 Acceptance
description: Human acceptance record for the frozen three-mode interaction baseline.
type: acceptance
status: ACCEPTED / FROZEN
created: 2026-09-15
updated: 2026-09-15
tags: [interaction, acceptance, frozen-baseline]
sources: ["[[docs/INTERACTION_SYSTEM]]", "[[scripts/run_three_mode_ux_acceptance_v1.py]]", "[[wiki/experiments/interaction-natural-language-constraint-fix-v1]]"]
---

# Three-Mode Interaction System v1 Acceptance

## Status

`THREE_MODE_INTERACTION_SYSTEM_V1_ACCEPTED`

`ACCEPTED / FROZEN`

Natural Language Interaction Layer: `INTERACTION_NL_V1_ACCEPTED`.

This is an accepted production baseline for the current interaction scope. It does not claim that arbitrary multilingual, very long, or highly ambiguous input is completely solved.

## Validation

- Full regression: `141 passed`.
- Parser/runtime directed regression: `47 passed`.
- Original 43-scenario UX acceptance rerun: `43 PASS / 0 FAIL`.
- Static validation: Python `py_compile`, JSON schema parse, and `git diff --check` passed.
- Wiki synchronization: `llm-wiki sync` passed.
- Pose System remains `ACCEPTED / FROZEN`.
- No image generation or `$imagegen` call was made; all interaction flows stop at or before `GENERATION_READY`.

The first UX acceptance result remains preserved as historical evidence: `10 PASS / 33 FAIL`. Its main findings were natural-language action parsing, recommendation auto-lock, delegation misclassification, explicit constraint loss, provenance remapping, mode-switch and restart wording failures, and Quick/AI Decide collapse.

## Human Review

> Three-Mode Interaction System v1 已通过真实自然语言多轮交互验收。
>
> Quick、AI Decide 与 User Decide 均具有明确、可观察的行为差异。
>
> User Decide 不再依赖内部结构化命令，普通自然语言短回复、选择、混合、自定义、推荐接受、委托、返回、模式切换与恢复均可正常工作。
>
> 显式用户约束能够跨 Pipeline 保留，并具有正确 provenance。
>
> 当前版本足以作为后续角色生成实验的稳定交互基线。

## Frozen scope

Unless a confirmed regression, blocker, or production integration bug appears, do not casually change the three mode definitions, shared pipeline, GateResolver behavior, Session lifecycle, provenance semantics, recommendation/delegation distinction, parser action semantics, explicit constraint priority, resume/rollback rules, or mode-switch rules.

Future extensions may cover more complex ambiguity, additional languages, extreme long input, and UI polish. These do not block v1.

## Next stage

`THREE_MODE_GENERATION_QUALITY_BENCHMARK`

This stage is recorded only as the next roadmap item. It was not started by this acceptance.
