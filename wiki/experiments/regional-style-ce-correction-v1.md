---
type: experiment
title: Case C + Case E Correction v1
description: Targeted clothing and crossed-leg correction after Human Review of the C/E reconstruction.
aliases: [C/E Correction, Regional Style C/E Correction]
tags: [experiment, benchmark, regional-style, imagegen, human-review]
sources: [2026-09-15/regional_style_ce_correction_v1_request.md]
status: C_E_CORRECTED_PENDING_HUMAN_REVIEW
confidence: medium
created: 2026-09-15
updated: 2026-09-15
related: [experiments/regional-style-ce-reconstruction-v1, experiments/regional-style-ab-regression-v2, experiments/benchmark-status, architecture/regional-visual-language]
---

# Case C + Case E Correction v1

The user identified two direct-image issues: C was too conservatively dressed, and both C and E showed crossed-leg reads. Only C and E were corrected; A/B/D/F remain frozen. Old images were not passed as ImageGen references.

## Case C

`Open-Edge Tailoring` replaces the previous formal longline tailoring with a cropped open jacket, asymmetric neckline, short teal skirt panel over fitted shorts, and sleek knee-high fashion boots. The result is more visibly premium gacha-fashion-forward while remaining non-sexual and preserving a clearly adult, handsome, strongly androgynous woman. Actual-image spot-check finds both legs and boots separately readable, with feet shoulder-width apart on one ground line and no crossed-leg read.

## Case E

The selected `Aquatic glassfin humanoid` direction is unchanged. The pose now requires a square front-facing stance: both feet separately planted on the same ground line, shoulder width apart, parallel legs, a visible gap from knees to ankles, toes forward, and no front/back overlap. Actual-image spot-check finds the glassfin ears, throat scales, ankle fins, legs and feet readable without the previous crossed-leg read.

## Provenance and stop condition

Both cases used the current Skill → Final Design → `runtime.regional_style_runtime.PromptCompiler` → built-in `image_gen` → actual-image QA pipeline. C's first more-open prompt was safety-rejected with no output; one safer non-sexual fashion equivalent succeeded. E succeeded on its first generation attempt. No old image reference, inpainting or further retry was used. Runtime state is `C_E_CORRECTED_PENDING_HUMAN_REVIEW`; the next action is Human Review only.

Artifact report: `D:/benchmark/outputs/character_archetype_ce_correction_v1_20260915/ce_correction_report.md`.
