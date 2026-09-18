# Changelog

## v1.3.0 — 2026-09-18

Status: `ANIME_CHARACTER_DIRECTOR = RELEASED`

Theme: `Constraint Fidelity & Intelligent Repair`

### Added

- Face Aesthetic Contract with an East Asian commercial-gacha default for fresh runs, plus explicit Western-inspired and neutral face options.
- Explicit User Constraint Contract and coverage gate for ordinary natural-language requirements across role, presentation, costume, proportions, props, non-human features, hair, legwear, footwear, palette, pose, background, composition, and quantity.
- Ownership-aware adherence disposition and repair-trigger policy separating strict visual fidelity from repair necessity.

### Changed

- QUICK and AI_DECIDE resolve only fields not explicitly owned by the user.
- AI/default-only adherence deviations remain visible to review but do not automatically trigger repair.
- Face-style inheritance is disabled by default for fresh runs.
- Visual repair consumes policy-approved actionable targets rather than every raw critic suggestion.

### Fixed

- Cross-run Western-inspired facial-style leakage.
- Explicit Chinese character-design requirements being dropped before prompt compilation.
- Defaults such as unwanted horns, boots, or conflicting costume topology replacing explicit requirements.
- UX U6 provenance false-positive classification.

## [1.1.0] — 2026-09-16

Status: `ANIME_CHARACTER_DIRECTOR = RELEASED`

Previous version: `v1.0.0` (real Git tag; no separate GitHub Release object was present). This release is a public README, asset, benchmark-summary, and release-documentation rewrite; it does not add a new creation mode or experimental runtime feature.

### Added

- User-facing README hero, four-image v2 Gallery, three-mode explanations, bilingual Quick Start, architecture overview, quality boundaries, and Known Limitations.
- Clean public image assets under `docs/assets/readme/` plus two explicitly labeled historical evolution images.
- Expanded Generation Quality Benchmark v2 Summary with mode averages, replay disclosure, constraint results, and post-v1 research boundary.

### Fixed

- Removed development-log ordering and stale release wording from the public README.
- Clarified that USER_DECIDE benchmark rows replay previously recorded real-human selections rather than claiming four new live UI sessions.
- Moved diversity, visual-prior, pose-vocabulary, and LoRA step1000 work into `POST_V1_RESEARCH` instead of presenting it as a release blocker.

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
