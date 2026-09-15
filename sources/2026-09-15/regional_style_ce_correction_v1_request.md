---
title: Case C and Case E Correction v1 Request
ingested: 2026-09-15
wiki_pages: wiki/experiments/regional-style-ce-correction-v1.md, wiki/experiments/benchmark-status.md, wiki/roadmap/current.md
---

# Request

Direct Human Review found two issues in the C/E reconstruction: C's clothing was too conservative, and both C and E still read as cross-legged. Correct only C and E. A/B/D/F remain frozen.

Rebuild from the design layer with no old-image reference. Keep `CONTEMPORARY_COMMERCIAL_GACHA_ANIME` and `EAST_ASIAN_CONTEMPORARY_GACHA`. Give C more visible but non-sexual premium gacha fashion tension while preserving a clearly adult handsome androgynous woman. Keep E's selected `Aquatic glassfin humanoid` direction and change only the stance constraints. Both cases need separate feet, a clear gap between legs, the same ground line, and no front/back foot overlap.

Use the current Skill → Final Design → PromptCompiler → built-in image generation → actual-image QA pipeline. Record any safety rejection and stop after the bounded correction candidates are produced.
