---
title: Case C and Case E Targeted Reconstruction v1 Request
ingested: 2026-09-15
wiki_pages: wiki/experiments/regional-style-ce-reconstruction-v1.md, wiki/experiments/benchmark-status.md, wiki/roadmap/current.md
---

# Request

Reconstruct only Case C and Case E after direct Human Review of the Regional Style A/B v2 images. A/B/D/F remain frozen for this round. The two cases must be rebuilt from the design layer; prior images are negative-review fixtures only and must not be passed to ImageGen as references.

Continue `CONTEMPORARY_COMMERCIAL_GACHA_ANIME` and `EAST_ASIAN_CONTEMPORARY_GACHA`. C must read as a clearly adult, handsome, strongly androgynous woman without default short black hair, flat-chest masculinity, techwear, cargo, combat or military shortcuts. E must remain human-dominant while being visibly partial-beast at ordinary full-body scale; propose at least three species directions, select one, and integrate two or three main biological traits into silhouette, clothing and pose. Use one first-pass image per case and stop pending Human Review.

Implementation selected `Clean-Line Tailoring` for C and selected `Aquatic glassfin humanoid` for E after three proposals. The pipeline was Skill → Final Design → PromptCompiler → built-in image generation → actual-image QA. No Skill, Regional Visual Language, or Lower-Body Diversity changes were requested or made.
