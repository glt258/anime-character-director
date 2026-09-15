---
title: Pose System v1 Human Acceptance
type: source
created: 2026-09-15
updated: 2026-09-15
ingested: 2026-09-15
wiki_pages:
  - wiki/architecture/pose-intent-preservation.md
  - wiki/experiments/hard-no-crossed-legs-invariant-v1.md
  - wiki/experiments/pose-intent-ab-v2.md
  - wiki/experiments/benchmark-status.md
  - wiki/roadmap/current.md
---

# Pose System v1 Human Acceptance

Human Review approved Pose System v1 as the current production baseline for fast generation. The real-image checks were performed without automatic repair or cherry-pick: 6/6 first-pass images had no crossed legs, 6/6 passed Leg Safety, Pose Intent remained readable, and no obvious safe-pose homogenization was observed.

The approval is deliberately scoped. It means `ACCEPTED / FROZEN` for the current baseline, not that all future pose problems are completely solved. Detailed pose refinement remains a future, explicitly requested mode.

The accepted benchmark artifacts are `D:/benchmark/outputs/pose_hard_invariant_stress_v1_20260915/` and `D:/benchmark/outputs/pose_intent_ab_v2_20260915/`. Their generated images remain local artifacts and are not release files.
