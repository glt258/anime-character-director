# Wiki Log

## 2026-09-14

- Updated `wiki/experiments/benchmark-status.md` with the Rendering Style Repair Benchmark v1 result: A/C/E/F/H passed repair-v1 in one attempt each, no repair-v2, style convergence not detected, final status `PASS_PENDING_HUMAN_REVIEW`.
- Source artifact: `D:/benchmark/outputs/rendering_style_repair_v1_20260914/rendering_style_repair_report.md`.

## 2026-09-14 — Design Direction Reset

- Recorded the reclassification of A/C/E/F/H as `DESIGN_DIRECTION_FAILURE` and the rollback of active visual variables to `unresolved`.
- Recorded 20 text-only Art Explore directions, four per case, with no automatic selection and no image generation.
- Source artifact: `D:/benchmark/outputs/design_direction_reset_benchmark_v1_20260914/design_direction_reset_report.md`.

## 2026-09-14 — Human Art Reselection and Visual Preference Review

- Recorded human selections A4, C3, E1, F1 and H4; E1 overrides the AI recommendation E2.
- Recorded transition of all five cases to `AWAITING_VISUAL_PREFERENCE_SELECTION` with 15 preference groups per case, global rendering style locked by product default, and no generation started.
- Source artifact: `D:/benchmark/outputs/visual_preference_review_after_art_selection_v1_20260914/visual_preference_review_report.md`.

## 2026-09-14 — Human Visual Preference Selection v1

- Recorded all A/C/E/F/H visual preference selections with `human_override: true`; E1 remains the explicit override of AI recommendation E2.
- Recorded runtime transition to `FINAL_DESIGNED`, five `VALID` Playable Character Design Gate results, `LOW` genericness risk, `STRONG` player appeal, and five passing Prompt Audits.
- Recorded explicit independent-leg and no-crossed-leg constraints; no image generation was started.
- Source artifact: `D:/benchmark/outputs/human_visual_preference_selection_v1_20260914/final_design_pipeline_report.md`.

## 2026-09-14 — Final Generation Acceptance Benchmark v1

- Recorded five actual first-pass generations for A/C/E/F/H from the locked Final Design and compiled prompts.
- Recorded one bounded repair for F and one for H; A/C/E passed directly, F remains borderline on body/outfit grounding, and H passes with a minor fashion-forward note.
- Recorded cross-case actual-image diversity, generation biases, anatomy gates, gacha-style gates, genericness reviews, and final state `GENERATED_PENDING_HUMAN_REVIEW`.
- Source artifact: `D:/benchmark/outputs/final_generation_acceptance_v1_20260914/final_generation_acceptance_report.md`.

## 2026-09-14 — Human Visual Revision v1

- Recorded direct human feedback on A/C/E/F/H actual images.
- Recorded A's new slim covered lower-body generation, C carried forward unchanged, E/F full new generations, and H's conservative barefoot edit.
- Source artifact: `D:/benchmark/outputs/final_generation_acceptance_revision_v1_20260914/human_visual_revision_report.md`.

## 2026-09-14 — Human Visual Revision v2

- Recorded A's supplied open-foot hosiery reference, C's black hosiery revision, and E's full regeneration with a Japanese-anime face, slimmer legs, and full-body fitted suit.
- Recorded F as user-passed and H as unchanged in this review round.
- Source artifact: `D:/benchmark/outputs/final_generation_acceptance_revision_v2_20260914/human_visual_revision_v2_report.md`.

## 2026-09-14 — Human Visual Correction v3

- Corrected the attachment mapping: first image received the black-stocking-only edit; second image received a full power-oriented bodysuit regeneration.
- Recorded C, F and H as untouched in this correction round.
- Source artifact: `D:/benchmark/outputs/final_generation_acceptance_revision_v3_20260914/human_visual_correction_v3_report.md`.

## 2026-09-14 — Final Five Character Set Export

- Archived the canonical five-image set for A/C/E/F/H without overwriting historical generations.
- Recorded the E black-stocking tailored image as an alternate and the power-bodysuit regeneration as the canonical E image.
- Source artifact: `D:/benchmark/outputs/final_five_character_set_20260914/final_five_character_set_report.md`.

## 2026-09-14 — F Character Bodysuit Rebuild

- Rebuilt F as a full-body fitted bodysuit character with stronger athletic structure and grounded power stance.
- Replaced the canonical F in the five-image archive and preserved the previous F as an alternate.
- Source artifact: `D:/benchmark/outputs/final_generation_acceptance_revision_v4_20260914/f_character_bodysuit_rebuild_report.md`.

## 2026-09-14 — F Full Visual Reset + E Outfit Redesign

- Recorded F's western-superhero/bodysuit convergence as a design-direction regression and rolled back the active branch.
- Scored four F Outfit/Visual Directions, selected `Draped Strength`, and generated `F-redesign-v2` from a fresh Final Design and PromptCompiler bundle without image references.
- Preserved E's character direction, scored three outfit directions, selected `Subtle Asymmetric Everyday Gacha`, and generated `E-outfit-redesign-v2` without image references.
- Recorded actual-image QA as passing for the requested style, anatomy, body/proportion, template-regression, grounding and hand checks; state remains `PENDING_HUMAN_REVIEW`.
- Source artifact: `D:/benchmark/outputs/f_full_visual_reset_e_outfit_redesign_v1_20260914/f_full_visual_reset_e_outfit_redesign_report.md`.

## 2026-09-14 — Freeze F / Full Reset E v3

- Formally froze F as `HUMAN_ACCEPTED`; no F Character Direction, Art Direction, Final Design or Generated Image changes were made.
- Reclassified both E visual branches as `DESIGN_DIRECTION_FAILURE` and `NEGATIVE_REFERENCES`, rolled back to Character Core, and reopened the requested visual variables.
- Recorded five new E Art Directions and provisional Playable Character Design Gate results; AI recommendation remains advisory and no Human selection was inferred.
- Confirmed no old image reference, no Final Design, no PromptCompiler run and no `$imagegen` call; runtime remains `AWAITING_ART_RESELECTION`.
- Source artifact: `D:/benchmark/outputs/freeze_f_full_reset_e_v3_20260914/human_review_report.md`.

## 2026-09-14 — E-V3-D4 Sensual Oddity Generation

- Recorded Human selection of E-V3-D4 `Sensual Oddity` and the downstream Visual Preference Sheet with explicit AI implementation sources.
- Completed Final Design and PromptCompiler, then generated a new E from scratch with no image reference; F remained frozen as `HUMAN_ACCEPTED`.
- Actual-image QA passed Gacha Style, playable design, template regression, anatomy, body proportion, grounding and hand checks; Sensual Oddity QA is `PASS_WITH_NOTE` for slight regal flavor.
- Runtime state is `PENDING_HUMAN_REVIEW`; no automatic next round was started.
- Source artifact: `D:/benchmark/outputs/e_v3_d4_sensual_oddity_20260914/e_v3_d4_sensual_oddity_report.md`.

## 2026-09-14 — E-V3-D4 Full Visual Reconstruction v2

- Recorded Human feedback that the previous E background/composition converged with frozen F.
- Rebuilt E from the D4 character core with a cool blue-hour waterfront, off-center 3/4 composition, short asymmetric outfit and open-foot low flats; no previous image was passed as a reference.
- Background Regression QA against F and focused actual-image QA passed; distant skyline/bridge remains a human-review note.
- F remained `HUMAN_ACCEPTED`; runtime is `PENDING_HUMAN_REVIEW` with no automatic next round.
- Source artifact: `D:/benchmark/outputs/e_v3_d4_sensual_oddity_reconstruction_v2_20260914/e_v3_d4_full_reconstruction_report.md`.

## 2026-09-14 — Character Archetype Generalization Benchmark v1

- Added `[[experiments/character-archetype-generalization-v1]]` with the six-case AI-delegated benchmark result and evidence scope.
- Updated `[[experiments/benchmark-status]]`, `[[roadmap/current]]`, and the Wiki index with the new `PASS_WITH_FINDINGS` 6/6 result.
- Source artifact: `2026-09-14/character_archetype_generalization_v1_report.md`.

## 2026-09-14 — Regional Visual Language Layer

- Added the three-layer style architecture, `RegionalVisualLanguage`, policy default/explicit override/migration semantics, structured PromptCompiler, actual-image RegionalStyleCritic, StyleGateResult, drift taxonomy, outfit-family collapse diagnostic, and negative fixture metadata.
- Updated Skill/runtime architecture and regional style constraint pages; no image generation or benchmark rerun was performed.
- Source artifact: `2026-09-14/regional_visual_language_layer_request.md`.

## 2026-09-14 — Regional Wiki evidence links

- Added the immutable regional-style request and runtime/config paths to the modified Wiki page frontmatter.

## 2026-09-14 — Lower-Body Diversity Layer

- Added explicit lower-body variables, adult/minor age handling, actual-image grounding diagnostics, lower-body ledger repetition penalties, and negative regression coverage for conservative convergence.
- Created [[constraints/lower-body-diversity]] and updated regional architecture, style constraints, roadmap, and index; no images or benchmark runs were performed.
- Source artifact: `2026-09-14/lower_body_diversity_patch_request.md`.
## [2026-09-14] update | Regional Visual Language hardening
- updated `wiki/architecture/regional-visual-language.md` — added provenance audit, richer RegionalStyleReview, archetype/body and presentation diagnostics
- updated `wiki/constraints/anime-style-and-identity.md` — recorded age/archetype preservation and soft drift diagnostics
- updated `wiki/roadmap/current.md` — recorded implementation status and fresh-image A/B next step

## [2026-09-14] experiment | Character Archetype Regional Style A/B Regression v2
- created wiki/experiments/regional-style-ab-regression-v2.md — captured six fresh first-pass images, actual-image findings, cross-case diversity, and pending Human Review state
- updated wiki/experiments/benchmark-status.md — recorded 4/6 blind regional YES, B/C residual drift, and no-v3 stop condition
- updated wiki/roadmap/current.md — set next step to gallery/report Human Review

## [2026-09-14] review | Regional Style A/B Regression v2 Human Review
- created sources/2026-09-14/regional_style_ab_regression_v2_human_review.md and outputs/character_archetype_regional_ab_v2_20260914/human_review_override.json — recorded the user's authoritative direct-image review
- updated the A/B report, gallery, per-case anatomy/global/archetype/genericness artifacts, benchmark summary, and human review summary — superseded incorrect generation-stage anatomy conclusions
- set the disposition to E accepted, A/B/C/D correction required, and F ground-up design rebuild required; no image generation was started

## [2026-09-15] experiment | Regional Style A/B Correction v1
- created sources/2026-09-15/regional_style_ab_correction_v1_request.md and wiki/experiments/regional-style-ab-correction-v1.md
- recorded one bounded candidate edit each for A-D, carried E forward, and generated one no-reference ground-up F rebuild
- recorded the safety-rejected F prompt without output and the successful safe-equivalent generation; candidates remain pending Human Review

## [2026-09-15] experiment | Case C + Case E Targeted Reconstruction v1
- created the immutable request source, C/E reconstruction experiment page, output manifest/report/gallery, and per-case actual-image QA artifacts
- rebuilt only C and E from fresh design-layer inputs with no old-image references; C selected `Clean-Line Tailoring`, E selected `Aquatic glassfin humanoid` after three species proposals
- generated one first pass per case and stopped at `C_E_RECONSTRUCTED_PENDING_HUMAN_REVIEW`; A/B/D/F, Regional Visual Language, Lower-Body Diversity and Skill remain unchanged
- source artifact: `2026-09-15/regional_style_ce_reconstruction_v1_request.md`

## [2026-09-15] correction | Case C + Case E Correction v1
- recorded Human Review that C was too conservatively dressed and C/E both had crossed-leg reads
- created the immutable correction request, C/E correction experiment page, output manifest/report/gallery, and actual-image QA artifacts
- rebuilt only C/E from fresh no-reference prompts; C uses `Open-Edge Tailoring`, E retains `Aquatic glassfin humanoid` with a square separated stance
- recorded one C safety-rejected prompt with no output, one safe-equivalent C success, and one E success; candidates remain pending Human Review
- source artifact: `2026-09-15/regional_style_ce_correction_v1_request.md`

## [2026-09-15] hardening | HARD NO-CROSSED-LEGS Invariant v1
- created the immutable request source and Wiki experiment page
- added `LegSeparationContract`, pose-family risk/forbidden validation, positive and negative PromptCompiler geometry, centerline lane logic, `LegSeparationGate`, candidate promotion blocking, migration, and bounded pose-only repair
- updated policy, schema, Skill, workflow, character-design, anatomy, pose-diversity and Wiki architecture/constraint pages; no image generation or Regional/Lower-Body/Fanservice rule changes
- added targeted regression coverage; direct affected tests pass
- source artifact: `2026-09-15/hard_no_crossed_legs_invariant_v1_request.md`

## [2026-09-15] implementation | Pose Intent Preservation v1
- created `wiki/architecture/pose-intent-preservation.md` and copied the immutable request source
- added independent `PoseIntentContract`, actual-image `PoseIntentGate`, pose-intent-only repair planning, migration, and `PoseDiversityLedger`
- integrated `POSE INTENT` compilation before the unchanged hard leg-geometry block; added backward-compatible schema fields and 22 focused tests
- updated Skill, workflow, Anime Style Contract, anatomy/pose constraint, architecture, and roadmap pages; no image generation or next benchmark started

## [2026-09-15] acceptance | Pose System v1
- recorded Human Review acceptance for the real-image hard-invariant stress benchmark and Pose Intent A/B re-test
- updated the hard-invariant and Pose Intent experiment states to `ACCEPTED`; recorded `POSE_SYSTEM_V1_ACCEPTED` / `ACCEPTED / FROZEN`
- added `docs/POSE_SYSTEM_V1_ACCEPTANCE.md`, `CHANGELOG.md`, the immutable acceptance source, and the Pose Intent A/B experiment page
- preserved the local benchmark images and reports; no new image generation, repair, cherry-pick, or benchmark was started
