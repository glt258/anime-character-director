# Changelog

## Three-Mode Interaction System v1 — 2026-09-15

Status: `ACCEPTED / FROZEN`

- Added shared-session `QUICK`, `AI_DECIDE`, and `USER_DECIDE` orchestration with Character, Art, and Visual Preference gates.
- Added natural-language gate actions, recommendation/delegation separation, explicit constraint locking, pending constraints, resume/rollback/restart, mode switching, regeneration, and provenance.
- Preserved the first UX evidence (`10 PASS / 33 FAIL`) and recorded the post-fix rerun at `43/43 PASS`.
- Human Review accepted `THREE_MODE_INTERACTION_SYSTEM_V1_ACCEPTED` and `INTERACTION_NL_V1_ACCEPTED` as the stable production baseline for the current interaction scope.
- No image generation, benchmark start, or push was performed.

## Pose System v1 — 2026-09-15

Status: `ACCEPTED / FROZEN`

- Stabilized the hard `NO_CROSSED_LEGS_HARD_INVARIANT` and `LegSeparationContract`.
- Preserved distinct pose intent through `PoseIntentContract`, `PoseIntentGate`, PromptCompiler integration, migration, bounded pose-only repair, and safe-pose diversity diagnostics.
- Recorded Human Review of the real-image stress benchmark and pose-intent A/B benchmark: 6/6 Leg Safety PASS, 6/6 no crossed legs, pose intent retained, and no obvious safe-pose homogenization.
- Accepted as the current production baseline for fast generation. Detailed pose refinement remains a later, explicitly scoped mode.
- No generated benchmark PNGs, caches, credentials, or local logs are part of this release.
