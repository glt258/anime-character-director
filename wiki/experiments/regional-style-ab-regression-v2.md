---
type: experiment
title: Character Archetype Regional Style A/B Regression v2
description: Six fresh first-pass images measuring whether the Regional Visual Language layer changes actual generation outcomes.
aliases: [Regional Style A/B v2, Regional Visual Language Regression]
tags: [experiment, benchmark, regional-style, imagegen]
sources: [2026-09-14/regional_style_ab_regression_v2_request.md]
status: pending-human-review
confidence: medium
created: 2026-09-14
updated: 2026-09-14
related: [experiments/benchmark-status, experiments/character-archetype-generalization-v1, architecture/regional-visual-language]
---

# Character Archetype Regional Style A/B Regression v2

Human Review approved this regression after the prior Regional layer implementation and hardening. The six high-level inputs A-F were kept unchanged. Each case received exactly one fresh first-pass image generated without old-image references; the prior six images were consulted only as post-generation negative metadata.

All six cases passed the Global Gacha gate. Blind Regional reads were A YES, B BORDERLINE, C BORDERLINE, D YES, E YES, and F YES: 4/6 YES, which satisfies the benchmark PASS threshold but is not a STRONG PASS. B retains generic fantasy-RPG coat and ornament drift. C retains pseudo-oriental sash/tassel and fashion-editorial drift. A, D, E, and F pass the deterministic Regional review.

Outfit-family and background-family collapse were not detected. Lower-body coverage remains diverse, but only 4/6 cases combine covered legs with closed shoes, below the conservative 5/6 observation threshold; no quota was applied. No crossed legs, safe-stance collapse, or same-face collapse were observed. Face diversity is moderate.

D reads as a petite adult with a mild youthful edge but passes the maturity gate. E reads as a commercial adult utility design, but its intended partial-beast trait is not legible in the image, so the archetype result is partial. The prompt audit found all required section headers, while the literal phrase restrained realistic facial planes is absent from the current compiled prompt; this was recorded as a benchmark finding and not patched mid-run.

Runtime state is REGIONAL_AB_GENERATED_PENDING_HUMAN_REVIEW. Human review of the gallery and report is the next step. No repair, retry, regeneration, image cherry-pick, or v3 benchmark was started.

## Human Review Override

The user reviewed the six actual images on 2026-09-14. This direct evidence supersedes the generation-stage anatomy notes: A has crossed legs and a possible left/right foot reversal; B has malformed or tangled legs; C has crossed legs; D has four visible toes on the left foot; E is accepted; and F reads as an NPC rather than a 二游 playable character and requires a ground-up design rebuild. Current human disposition is HUMAN_REVIEWED_PENDING_CORRECTION. No repair or regeneration has started.

The user then authorized Correction v1 on 2026-09-15. A-D received one bounded edit each, E was carried forward unchanged, and F received one ground-up no-reference rebuild. The candidates are stored in [[experiments/regional-style-ab-correction-v1]] and remain pending Human Review; no v3 benchmark was started.

## Case C + Case E Targeted Reconstruction

On 2026-09-15, only C and E were reconstructed from the design layer after the user's direct review. A/B/D/F remain frozen. C selected `Clean-Line Tailoring` to establish a clearly adult, handsome, strongly androgynous woman without the previous fashion-editorial drift. E compared three species directions and selected `Aquatic glassfin humanoid`, integrating fin-ears, a throat scale patch, and ankle fins into the silhouette and outfit so the partial-beast read survives normal full-body scale. Each case received one fresh no-reference first pass and remains pending Human Review. See [[experiments/regional-style-ce-reconstruction-v1]].

## Related

- [[experiments/benchmark-status]]
- [[experiments/character-archetype-generalization-v1]]
- [[architecture/regional-visual-language]]
