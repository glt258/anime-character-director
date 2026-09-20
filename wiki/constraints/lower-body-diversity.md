---
type: constraint
title: Lower-Body Diversity and Grounding
description: Lower-body coverage, legwear, accessories, footwear, age appropriateness, and actual-image grounding rules.
aliases: [lower-body design, legwear diversity, footwear diversity]
tags: [constraint, diversity, anatomy, grounding]
sources: ["runtime/regional_style_runtime.py", "references/pose-and-footwear-diversity.md"]
updated: 2026-09-14
related: ["[[architecture/regional-visual-language]]", "[[constraints/anime-style-and-identity]]"]
---

# Lower-Body Diversity and Grounding

Lower body is a real character-design space. Coverage, exposure, legwear, leg accessories, foot visibility, and footwear participate in silhouette, personality, movement, sensuality, elegance, fantasy, and identity. Modesty is not the automatic solution, and anti-fanservice guidance must not become anti-exposure.

The formal variables are `exposure_strategy`, `legwear_family`, `leg_accessory_family`, `footwear_family`, `foot_visibility`, `visual_reason`, style/pose relationships, and `repetition_risk`. Adult characters may use stockings, tights, bare legs, leg rings, straps, barefoot systems, open footwear, heels, flats, sneakers, boots, and asymmetry. Male characters have the same space and must not default to trousers plus boots. Fanservice level remains independent from coverage.

Clearly juvenile characters may use age-appropriate socks, tights, sandals, sneakers, or barefoot designs, but not fetishized accessories or erotic leg framing. `LowerBodyDesignReview` rejects that unsafe combination and otherwise treats an unmotivated pants-plus-boots fallback as a genericness note rather than a hard failure.

`PromptCompiler` preserves selected lower-body values and foot visibility. Actual-image grounding reports `FOOTWEAR_GROUNDING_FAIL`, `LEGWEAR_GROUNDING_FAIL`, or `LOWER_BODY_ANCHOR_MISS` when the rendered image loses locked intent. Portfolio repetition reports `CONSERVATIVE_COVERAGE_COLLAPSE`, `LEGWEAR_FAMILY_COLLAPSE`, or `FOOTWEAR_FAMILY_COLLAPSE` as soft diagnostics; an explicitly requested uniform remains allowed.

## Related

- [[architecture/regional-visual-language]] — Regional style architecture that carries this design space.
- [[constraints/anime-style-and-identity]] — Global style and identity constraints.
