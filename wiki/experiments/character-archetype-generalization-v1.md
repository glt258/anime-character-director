---
type: experiment
title: Character Archetype Generalization Benchmark v1
description: Six-case AI-delegated benchmark measuring gender, maturity, body, face, partial-beast, and gacha-style generalization.
aliases: [Archetype Generalization v1, 角色原型泛化基准 v1]
tags: [experiment, benchmark, generalization, imagegen]
sources: [2026-09-14/character_archetype_generalization_v1_report.md]
status: current
confidence: medium
created: 2026-09-14
updated: 2026-09-14
related: ["[[experiments/benchmark-status]]", "[[constraints/anime-style-and-identity]]", "[[constraints/anatomy-pose-and-footwear]]", "[[roadmap/current]]"]
---

# Character Archetype Generalization Benchmark v1

The 2026-09-14 benchmark tested six independent standard standees in `AI_DECIDE_BENCHMARK_MODE`: young adult male social trickster, mature adult male pressure, androgynous adult female, petite adult female, partial-beast adult, and strong adult female. All identity variables were explicitly recorded with `selection_source: benchmark_ai_delegation`; Global Rendering Style remained `CONTEMPORARY_COMMERCIAL_GACHA_ANIME`.

The result is `PASS_WITH_FINDINGS` at 6/6 archetypes established. All six final images passed Anime 2D and Gacha Style checks, and all final images passed the no-crossed-legs requirement. Case C required one bounded lower-body repair after the first image produced a crossed-leg read. Case D passed the dedicated `ADULT_MATURITY_GATE`. Case E passed human dominance, trait count, and trait integration with a note that its translucent membrane became larger than planned. Case F passed the strong-female body gate with a note that musculature and shoulder/cape emphasis were stronger than planned without collapsing into fat-by-default or bodybuilder shorthand.

Cross-case review found no `MALE_HOST_CONVERGENCE`, `MATURE_MALE_SUIT_CONVERGENCE`, `ANDROGYNOUS_TECHWEAR_CONVERGENCE`, `PETITE_INFANTILIZATION`, `BEAST_CATGIRL_CONVERGENCE`, `STRONG_FEMALE_BODY_MASS_COLLAPSE`, `SAME_FACE_ACROSS_GENDER`, `SAME_BODY_ACROSS_ARCHETYPE`, `DARK_PALETTE_CONVERGENCE`, or `GACHA_STYLE_DRIFT`. The main observed ImageGen tendencies were crossed-leg pose drift on the first pass, scale inflation of membranes/capes, and stronger-than-planned muscle emphasis.

This is measurement evidence, not a new Skill rule set. The report classifies findings into Skill Problem, ImageGen Problem, and Benchmark Design Problem; no confirmed core Skill or PromptCompiler problem was found. The artifact remains pending human review, especially for Case B's muscle/pressure intensity, Case E's partial-trait scale, Case F's strength/curve balance, and portfolio-level face diversity.

Primary artifact: `D:/benchmark/outputs/character_archetype_generalization_v1_20260914/character_archetype_generalization_report.md`.

## Related

- [[experiments/benchmark-status]] — current benchmark history and evidence scope.
- [[constraints/anime-style-and-identity]] — global Anime 2D and gacha rendering constraints.
- [[constraints/anatomy-pose-and-footwear]] — no-crossed-leg and anatomy review boundary.
- [[roadmap/current]] — next human-review and broader-corpus work.
