---
title: Anime Style and Identity Constraints
description: Style and identity rules that prevent visual drift and keep high-impact choices auditable.
tags: [constraint, style, identity]
sources: ["[[SKILL.md]]", "[[references/visual-preference-model.md]]", "[[references/benchmark-spec.md]]", "2026-09-14/regional_visual_language_layer_request.md", "config/anime_style_policy.yaml"]
updated: 2026-09-14
type: constraint
related: ["[[architecture/skill-and-runtime]]", "[[experiments/benchmark-status]]"]
---

# Anime Style and Identity

The target is 2D anime character design. Photo-realistic, semi-realistic, and 3D drift are failures unless explicitly requested. Black hair is not a default identity value.

High-impact variables must be auditable through identity anchors and preference records. The default Global Rendering Style is `CONTEMPORARY_COMMERCIAL_GACHA_ANIME`. Character Visual Style may be diverse, but does not replace that medium unless the user explicitly requests a rendering override. S1 checks Anime 2D; the separate Gacha Rendering Style Gate checks commercial playable-character rendering. Visual quality claims must stay within the artifact and benchmark that produced them.

The default regional layer is `EAST_ASIAN_CONTEMPORARY_GACHA`. It constrains anime-first facial abstraction, stylized coherent anatomy, commercial material/light hierarchy, and playable-character presentation. It is not character ethnicity, nationality, skin tone, occupation, setting, or costume culture; dark/tan skin, fantasy ethnicity, western-looking fictional worlds, and non-East-Asian costume concepts remain valid. Explicit user requests may override the regional layer and must record the source and reason.

Regional review must also preserve age and archetype specificity: mature men remain anime-abstracted rather than westernized or infantilized; strong women are checked against superhero/bodybuilder massing; male body types remain open. Generic fantasy RPG recipes, pseudo-oriental defaults, character-sheet presentation, background circles/platforms, and archetype shortcut replacements are diagnostics, while user-directed repetition remains allowed.

Regional review is actual-image evidence, not prompt-keyword matching. Global PASS with Regional FAIL remains a style failure. Mature men must not be infantilized to avoid western facial anatomy, and strong women must not be collapsed into western superhero/bodybuilder anatomy. See [[architecture/regional-visual-language]].

Coverage is also not a default identity solution. Adult lower-body exposure, stockings/tights, leg accessories, open footwear, and barefoot construction remain valid design tools; male characters receive the same range. Clearly juvenile characters are protected from sexualized leg framing. See [[constraints/lower-body-diversity]].
