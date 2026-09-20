---
type: architecture
title: Regional Visual Language Layer
description: Three-layer style architecture and actual-image regional critic for commercial anime character design.
aliases: [RegionalVisualLanguage, regional style]
tags: [architecture, style, critic, prompt-compiler]
sources: ["SKILL.md", "config/anime_style_policy.yaml", "runtime/regional_style_runtime.py"]
updated: 2026-09-14
related: ["[[architecture/skill-and-runtime]]", "[[constraints/anime-style-and-identity]]"]
---

# Regional Visual Language Layer

The style architecture is deliberately three-layered: `Global Rendering Style` controls the 2D anime/gacha medium and finish; `Regional Visual Language` controls commercial illustration grammar; `Character Visual Style` controls the individual character's language. The order is explicit user style override → Global Rendering Style → Regional Visual Language → Character Visual Style → identity and implementation. The default regional value is `EAST_ASIAN_CONTEMPORARY_GACHA`.

`RegionalVisualLanguage` is a runtime model with `EAST_ASIAN_CONTEMPORARY_GACHA`, `WESTERN_ANIME_INSPIRED`, `REGION_NEUTRAL_ANIME`, and `CUSTOM`. Defaults record `default_style_policy`; explicit user changes record `explicit_user_override` and a reason. Old artifacts are copied and migrated in memory to the policy default with `migrated_default`; source files are not rewritten.

The default contract is anime-first facial abstraction, restrained facial planes, stylized coherent anatomy, controlled muscle definition, varied character-design-first outfit families, premium material separation, polished anime game lighting, and finished playable-character presentation. It is not an ethnicity, skin-tone, nationality, occupation, world-setting, or costume lock.

`PromptCompiler` emits Rendering Foundation, Regional Visual Language, and Character Visual Style in fixed order as natural-language positive and negative constraints. `RegionalStyleCritic` requires an existing actual image plus labeled observations; prompt keywords alone cannot pass. `GachaStyleCritic` keeps the Global stage and requires Global PASS and Regional PASS-equivalent in the final `StyleGateResult`.

The regional diagnostic vocabulary includes western-anime, western-fantasy-concept, western-superhero-anatomy, pseudo-oriental-default, generic-fantasy-RPG, character-sheet-presentation, outfit-family, background-presentation, infantilization, and archetype-shortcut drift. The Outfit Family Ledger records actual-image features and reports repeated grammar across four or more images as a non-blocking diagnostic. Regression fixtures are metadata-only and are never future image references.

The same ledger now covers lower-body design: exposure strategy, legwear family, leg accessories, foot visibility, footwear, stocking material, heel height, open-toe status, barefoot status, and lower-body asymmetry. Lower-body coverage is not coupled to fanservice. `LowerBodyDesignReview` and actual-image grounding protect adult choice, minor age appropriateness, and fidelity to selected barefoot/legwear/accessory decisions. See [[constraints/lower-body-diversity]].

Leg separation is a separate global anatomy invariant, not a Regional Style rule. `PromptCompiler` adds positive leg geometry and hard negative constraints for every regional language. Regional Style, Character Visual Style, Fanservice, and Lower-Body choices cannot disable `LegSeparationContract` or `LegSeparationGate`.

The RegionalStyleReview contract now carries expected/perceived language, face/body/outfit/material/presentation match, pseudo-oriental detection, rationale, and explicit drift types. `StrongFemaleRegionalStyleReview` and `MaleRegionalBodyReview` provide archetype-specific body checks; outfit and background ledgers remain repetition penalties, while generic RPG and archetype-shortcut replacement diagnostics catch cliché swaps without overriding user intent.

Provenance is explicit: `default_style_policy`, `explicit_user_selection`, `explicit_user_override`, `benchmark_delegation`, and `migrated_default`. Migration emits `REGIONAL_VISUAL_LANGUAGE_DEFAULT_MIGRATION` metadata with the old artifact version, effective value, timestamp, and later-override flag. Negative regression fixtures are not style references.

## Related

- [[architecture/skill-and-runtime]] — Skill/runtime division and generation gates.
- [[constraints/anime-style-and-identity]] — Global anime and identity constraints.
- [[experiments/character-archetype-generalization-v1]] — Six-case evidence that motivated this layer.
