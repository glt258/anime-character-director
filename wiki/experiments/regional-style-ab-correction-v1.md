---
type: experiment
title: Character Archetype Regional Style A/B Correction v1
description: User-authorized correction candidates for the six-case Regional Style A/B benchmark.
aliases: [Regional A/B Correction v1]
tags: [experiment, benchmark, correction, imagegen]
sources: [2026-09-15/regional_style_ab_correction_v1_request.md]
status: correction-candidates-pending-human-review
confidence: medium
created: 2026-09-15
updated: 2026-09-15
related: [experiments/regional-style-ab-regression-v2, experiments/benchmark-status, architecture/regional-visual-language]
---

# Character Archetype Regional Style A/B Correction v1

The user authorized this correction round after direct review of the six v2 images. A, B, C, and D received one bounded edit each focused on the reported lower-body issue. E was carried forward unchanged because the user accepted it. F was rebuilt from the ground up with no image reference to address the NPC rather than 二游 playable-character read.

The successful outputs are stored at D:/benchmark/outputs/character_archetype_regional_ab_correction_v1_20260915. A-D are correction candidates, E is a carried-forward acceptance, and F is a fresh rebuild candidate. One initial F prompt was blocked by the safety filter without output; one safety-adjusted equivalent prompt succeeded, and no further attempt was made.

Assistant spot-check found improved leg separation for A-C, a targeted left-foot redraw for D, and a clearer high-rarity gacha direction for F. These are provisional observations only. Current status is CORRECTION_CANDIDATES_PENDING_HUMAN_REVIEW.

## Related

- [[experiments/regional-style-ab-regression-v2]]
- [[experiments/benchmark-status]]
- [[architecture/regional-visual-language]]
