# Changelog

## Pose System v1 — 2026-09-15

Status: `ACCEPTED / FROZEN`

- Stabilized the hard `NO_CROSSED_LEGS_HARD_INVARIANT` and `LegSeparationContract`.
- Preserved distinct pose intent through `PoseIntentContract`, `PoseIntentGate`, PromptCompiler integration, migration, bounded pose-only repair, and safe-pose diversity diagnostics.
- Recorded Human Review of the real-image stress benchmark and pose-intent A/B benchmark: 6/6 Leg Safety PASS, 6/6 no crossed legs, pose intent retained, and no obvious safe-pose homogenization.
- Accepted as the current production baseline for fast generation. Detailed pose refinement remains a later, explicitly scoped mode.
- No generated benchmark PNGs, caches, credentials, or local logs are part of this release.
