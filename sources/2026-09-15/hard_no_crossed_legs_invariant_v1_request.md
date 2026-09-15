---
title: HARD NO-CROSSED-LEGS Invariant v1 Request
ingested: 2026-09-15
wiki_pages: wiki/architecture/skill-and-runtime.md, wiki/constraints/anatomy-pose-and-footwear.md, wiki/experiments/hard-no-crossed-legs-invariant-v1.md, wiki/experiments/benchmark-status.md, wiki/roadmap/current.md
---

# Request

Upgrade the repeated soft `NO CROSSED LEGS` prompt wording into a global `NO_CROSSED_LEGS_HARD_INVARIANT = true` for all normal two-legged humanoids. Do not call image generation or start another experiment in this implementation round.

Add a backward-compatible `LegSeparationContract`, positive leg geometry plus negative constraints in PromptCompiler, pose-family risk classification and forbidden crossed families, body-centerline lane logic, Final Design and Visual Preference validation, actual-image `LegSeparationGate` with `PASS`/`FAIL`/`UNCERTAIN`, blocking candidate promotion, one bounded pose-only repair, first-pass benchmark failure labeling, migration defaults, schemas, tests, Skill/docs, and Wiki updates.

Do not modify Regional Style, Lower-Body Diversity, Fanservice, Hair, Body Proportion, Outfit Diversity, historical artifacts, or images. Crossed-leg output remains a negative fixture and is never an ImageGen reference.
