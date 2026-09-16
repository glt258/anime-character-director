# Changelog

## v1.0.0 — 2026-09-16

Status: `ANIME_CHARACTER_DIRECTOR_V1_0_0 = RELEASED`

### Added

- QUICK, AI_DECIDE, and USER_DECIDE as the three public creation modes.
- Codex native interactive selection UI, persistent workflow continuation, restart continuation, Custom / Other, recommendation/delegation, BACK, and bounded regeneration.
- Dynamic contextual candidates, explicit positive/negative constraints, compound negation parsing, contemporary commercial gacha anime style contract, pose diversity rules, anatomy quality audit, and built-in `$imagegen` integration.

### Fixed

- Static placeholder interaction candidates and the scripted USER_DECIDE benchmark path.
- Negation scope parsing, including `不要粉色长发` as one same-entity prohibited compound rather than positive hair fields.
- Natural-language handling for `其他按推荐`, recommendation provenance, and mode switching.
- Black-stockings, high-heels, and crossed-leg default drift.

### Release evidence

- Generation Quality Benchmark v2: `COMPLETE_WITH_REPLAYED_USER_DECIDE_DISCLOSURE`.
- 12 comparable primary generations across QUICK / AI_DECIDE / USER_DECIDE; the four USER_DECIDE comparison rows replay previously recorded real-human selections under the frozen runtime and are not new live UI sessions.
- `LORA_NOT_PRIMARY_BOTTLENECK`; step1000 and broader diversity research are post-v1 work.

## Persistent Interactive Workflow Runner v1 — 2026-09-15

Historical status at the time of this entry: `IMPLEMENTED / PENDING HUMAN ACCEPTANCE`.

- Terminated the in-progress Generation Quality Benchmark for an orchestration fix; retained all 8 existing QUICK / AI_DECIDE first-pass artifacts and images.
- Added one logical `WorkflowRun` across User Decide checkpoints, process restarts, Custom Input, direct custom language, and active-run continuation.
- Added stable `__CUSTOM__` options, localized Chinese/English gate copy, and `InteractionCheckpoint` persistence without changing internal enums.
- Added focused persistent-runner, Custom, locale, restart, stale, cancellation, and regression tests. No imagegen call and no commit were performed.

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
