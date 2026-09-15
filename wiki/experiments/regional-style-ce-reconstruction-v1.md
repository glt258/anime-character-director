---
type: experiment
title: Case C + Case E Targeted Reconstruction v1
description: Fresh design-layer reconstruction for the androgynous female and partial-beast adult cases after Regional Style A/B v2 Human Review.
aliases: [C/E Targeted Reconstruction, Regional Style C/E Reconstruction]
tags: [experiment, benchmark, regional-style, imagegen, human-review]
sources: [2026-09-15/regional_style_ce_reconstruction_v1_request.md]
status: C_E_RECONSTRUCTED_PENDING_HUMAN_REVIEW
confidence: medium
created: 2026-09-15
updated: 2026-09-15
related: [experiments/regional-style-ab-regression-v2, experiments/regional-style-ab-correction-v1, experiments/benchmark-status, architecture/regional-visual-language]
---

# Case C + Case E Targeted Reconstruction v1

This is a two-case reconstruction only. A/B/D/F are frozen and unchanged. No prior image was used as an ImageGen reference; old images are negative-review metadata only. The global rendering gate remains `CONTEMPORARY_COMMERCIAL_GACHA_ANIME`, and the regional layer remains `EAST_ASIAN_CONTEMPORARY_GACHA`.

## Case C

The selected Art Direction is `Clean-Line Tailoring`. It uses medium-long ash-brown low-tied hair, a direct handsome adult-female face, moderate straight shoulders, restrained waist/hips, a long sleeveless tailored vest, an asymmetric half-skirt panel over straight trousers, loafers, and a stable front-facing stance with one foot slightly forward. Actual-image spot-check: clearly adult female, strong handsome/androgynous read, low traditional mature-御姐 drift, no techwear shortcut, no obvious crossed legs, and readable feet. Final Human Review is pending.

## Case E

Three species directions were proposed: `Aquatic glassfin humanoid`, `Opal crest drakekin`, and `Mothglass humanoid`. `Aquatic glassfin humanoid` was selected. Its three main anchors are translucent fin-ears, an iridescent throat scale patch, and paired translucent ankle fins that do not replace normal feet. The open collar, split lower wrap, mantle, and pose are adapted around those anchors. Actual-image spot-check: human-dominant, visibly partial-beast at normal full-body scale, low generic cat/fox/wolf risk, no furry conversion, no techwear action-woman shortcut, and provisional anatomy pass. Final Human Review is pending.

## Pipeline and stop condition

Each case received exactly one first-pass image through Skill → Final Design → current `runtime.regional_style_runtime.PromptCompiler` → built-in `image_gen` → actual-image QA. Prompt audits found all four required section headers and empty source-image lists. The current compiler's facial-plane wording remains an existing finding; no runtime or Skill patch was made in this round. Status stops at `C_E_RECONSTRUCTED_PENDING_HUMAN_REVIEW`; no further generation is authorized automatically.

Artifact report: `D:/benchmark/outputs/character_archetype_ce_reconstruction_v1_20260915/ce_reconstruction_report.md`.

Human Review then found C too conservatively dressed and both C/E cross-legged. These targeted corrections are recorded in [[experiments/regional-style-ce-correction-v1]]; the original reconstruction remains preserved as prior negative-review evidence.
