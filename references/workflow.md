# Multi-Mode Workflow

`$anime-character-director` is one Skill with six Human-facing creative modes. Route explicit mode first; otherwise infer intent and default to `explore` when ambiguous.

## Mode map

```text
$anime-character-director
  ├── quick
  ├── directed
  ├── explore
  ├── variants
  ├── same-character
  └── critique
        ↓ Human Authority Layer
        ↓ Visual Preference Gate
        ↓ $imagegen
        ↓ Technical QA
        ↓ Human Final Review
```

`auto` remains an internal benchmark/automation path and records `AUTO_RECOMMENDED`, never `HUMAN_APPROVED`.

## Modes

- `quick`: Few-line idea → minimal brief → generation → S1 → Gacha Style → Anatomy QA → Human Review. Do not run Character Explore or Art Explore; preserve explicit requirements.
- `directed`: AI designs premise, art direction, and Identity Pass → generation → S1 → Gacha Style → Anatomy QA → optional AI Review → Human Review. Label the result AI Recommended Design.
- `explore` (default): 5 Character Directions → Human select/mix → Character Planning → 4 Art Directions → Human select/mix → Visual Preference Proposal → explicit identity decisions → Human Audit → Identity Pass → Design Review → generation → S1 → Gacha Style → Anatomy QA → Human Review.
- `variants`: Existing version → 3–4 meaningful alternatives for one dimension → Human select/mix/keep both/request more → optional generation and QA. For `standee_pose_variant`, plan exactly four text-only standee poses before generation, then stop for Human selection.
- `same-character`: Character Canon + approved Master + new asset request → generation → S1 → Gacha Style → Anatomy QA → Identity Drift Review → Human Review. Do not rerun Explore or redesign without Human instruction.
- `critique`: Original → AI Critique → Revision B/C/D branches → comparison → Human Review. Never overwrite Original.

Variants must differ structurally, not only by shade or ornament. Explore keeps Human Mix as a first-class action. Same Character treats new permanent details as `PROPOSED CANON ADDITION` until explicit approval; `CONTEXT_ONLY` can approve a motif for named contexts.

## Shared technical boundary

Every image-producing mode runs:

```text
Generation → LegSeparationGate → PoseIntentGate → S1 Anime 2D Hard Gate → Gacha Rendering Style Gate → Anatomy Integrity Check → Human Review
```

Same Character additionally runs Identity Drift Review. Technical failure or default rendering drift may block delivery or enter bounded repair while preserving the source in lineage. `UNCERTAIN` remains explicit for Human Review. S1 and Gacha are separate gates: S1 checks Anime 2D medium, while Gacha checks commercial rendering and presentation.

## Visual Preference Gate

After `AWAITING_ART_SELECTION`, the runtime writes `visual_preference_sheet.json` and `visual_preference_report.md`, enters `VISUAL_PREFERENCES_PROPOSED`, then opens `AWAITING_VISUAL_PREFERENCE_SELECTION`. The eight `USER_OWNED_IDENTITY_VARIABLES` must each receive one of `user`, `mix`, `custom`, or explicit `ai_delegate`. A recommendation without a decision source is not a decision and cannot be locked.

`VISUAL_PREFERENCES_LOCKED` is the only state that can enter Final Design. Optional AI proposals remain visible and overridable without becoming blocking questions. The Human Audit records each identity variable, selected value, source, and lock status. This gate protects creative ownership; it does not score novelty or reject an aesthetic choice.

## Regional Style Layer

The style order is fixed: `Global Rendering Style` → `Regional Visual Language` → `Character Visual Style` → identity and implementation. The default regional value is `EAST_ASIAN_CONTEMPORARY_GACHA`; it describes anime abstraction, illustration grammar, rendering hierarchy, costume-design grammar, and commercial presentation, not ethnicity or costume culture. An explicit user request may override it and must record `regional_visual_language_source: explicit_user_override` plus a reason. Old artifacts without the field are read with the policy default and recorded as `migrated_default` in the in-memory migration event.

Regional provenance also supports `explicit_user_selection` and `benchmark_delegation`. `RegionalStyleCritic` consumes actual-image human-labeled observations; its gate is composed with the Global gate, while generic RPG, pseudo-oriental, character-sheet, background, and archetype-shortcut replacement findings remain explicit diagnostics. Specialized strong-female and male-body reviews protect anime-proportioned diversity without converting user-selected fashion into a hard ban.

`PromptCompiler` emits the three layers in fixed order as structured natural-language constraints. `RegionalStyleCritic` reviews actual image evidence, and the extended `GachaStyleCritic` requires both Global PASS and Regional PASS-equivalent. `Global PASS + Regional FAIL` is still `FAIL`. Regional review does not infer ethnicity, whiten skin, force black hair, or add pseudo-oriental costume.

The Outfit Family Ledger records actual-image outfit family, neckline, upper/lower structure, outer layer, waist, hanging cloth, cape, sash, trim, and footwear. Repetition across four or more images reports `OUTFIT_FAMILY_COLLAPSE` without becoming a hard gate unless a uniform was explicitly requested. The current six archetype images are negative regression fixtures only and are never future ImageGen references.

## Lower-body design and grounding

Lower-body choices are explicit design variables, separate from fanservice: exposure strategy, legwear, leg accessories, footwear, foot visibility, visual reason, relationship to style, relationship to pose, and repetition risk. Adult characters may use stockings, tights, thigh rings, straps, bare thighs, barefoot construction, sandals, flats, heels, sneakers, boots, or asymmetry when coherent. Male characters receive the same space; do not default them to trousers plus boots. Clearly juvenile characters may use ordinary socks, tights, sandals, sneakers, or barefoot choices, but not fetishized or erotic leg framing.

`LowerBodyDesignReview` adds a genericness note for an unmotivated pants-plus-boots fallback; it does not ban coverage or require exposure. `PromptCompiler` preserves selected lower-body values and foot visibility as a dedicated section. After generation, actual-image grounding compares the Final Design with the image and reports `FOOTWEAR_GROUNDING_FAIL`, `LEGWEAR_GROUNDING_FAIL`, or `LOWER_BODY_ANCHOR_MISS` when applicable.

## Soft pose and footwear guidance

Read [pose-and-footwear-diversity.md](pose-and-footwear-diversity.md) when selecting a pose, leg arrangement, hosiery, footwear, sensuality language, local asymmetry, or portfolio-level variation. Stilettos, black stockings, symmetric coverage, and asymmetric coverage remain open design choices. Crossed legs are excluded by the separate global `LegSeparationContract` and `LegSeparationGate`; repetition of other costume choices may produce an `AESTHETIC_NOTE` or Human-requested alternatives only. Same Character preserves Canon identity before applying diversity suggestions.

## Hard leg invariant pipeline

All image-producing modes run `Generation → LegSeparationGate → S1 Anime 2D → Gacha Rendering Style (Global + Regional) → Anatomy Integrity → Candidate Promotion`. PromptCompiler emits both positive leg geometry and explicit negative constraints. Final Design and visible pose options reject forbidden crossed/scissored language. `UNCERTAIN` is treated as non-promotable, and only `PASS` may become `PROMOTED_TO_CANDIDATE`. Normal production permits one pose-only regeneration; first-pass benchmarks save failures but never count them as PASS.

## Pose intent preservation

`PoseIntentContract` is a separate contract from `LegSeparationContract`. It preserves the requested body-language intent and its resolved safe pose family, required signals, minimum signal count, width/depth/asymmetry/energy/torso/arm/head requirements, and forbidden semantic shortcuts. The leg contract remains responsible only for independent leg geometry and cannot flatten the requested body language into a generic stance.

`PromptCompiler` emits `POSE INTENT` before the hard leg block. `PoseIntentGate` reviews actual-image labels for stance width, foot depth, weight distribution, knee state, torso, shoulders, arms, head angle, energy, and matched/missing signals. `LegSeparationGate = PASS` and `PoseIntentGate = STRONG` or `ACCEPTABLE` are both required for `POSE_VALID`; a semantic miss is reported as `POSE_INTENT_FAIL`, not anatomy failure.

The six high-risk intent families have explicit checks: elegant requires controlled and intentional body language; sensual requires body confidence and torso/waist/hip/head/arm language rather than outfit-only appeal; relaxed-asymmetric requires visible asymmetry; low-energy requires a low energy read plus at least two quiet signals; narrow requires actual narrow width; one-foot-forward requires actual front/back depth. `PoseDiversityLedger` and `SAFE_POSE_HOMOGENIZATION` provide a non-blocking repetition diagnostic. Pose-intent-only repair may change body language fields only and must rerun the leg gate.

## Hand anatomy versus glove coverage

Anatomy QA must distinguish a missing or malformed finger from an intentional costume choice. If all fingers are anatomically present and a glove exposes some of them, record `Anatomy: PASS` plus `Glove Coverage: ASYMMETRIC_PARTIAL_COVERAGE` and note that the uncovered fingers are costume detail. Only an actually missing, extra, fused, broken, or impossibly connected finger is an anatomy issue. This clarifies the existing Anatomy Integrity Check; it adds no new hard gate or validator beyond the separately documented global leg-separation invariant.

## Costume coverage variants

The existing `variants` mode may explore `glove_coverage_variant` and `legwear_asymmetry_variant` when Human asks for them. Symmetric gloves or legwear remain valid, and an asymmetry must serve identity, silhouette, rhythm, color balance, or a simple aesthetic preference. Do not apply a new coverage pattern to Human-approved Canon without an explicit variant request. A standard standee should keep both sides readable when the selected asymmetry is part of the design.

## Output labels

Use `AI ANALYSIS`, `AI RECOMMENDATION`, `HUMAN OPTIONS`, and `HUMAN DECISION: pending`. Persist `creative_session.json` plus one version record for every meaningful branch. See [creative-modes.md](creative-modes.md), [design-ownership.md](design-ownership.md), and [human-authority.md](human-authority.md).

## Standee-first scope and change reporting

Unless the Human explicitly requests another `presentation_type`, the workflow is Standee-first and defaults to `standard_standee`. Combat, ultimate, promotional, and story outputs remain optional presentation extensions, not additional modes. See [standee-first-scope.md](standee-first-scope.md).

Every development response ends with: **这次在干什么**, **为什么要改**, **这次具体改了什么**, **这次没动什么**, **检查结果**, **现在项目到哪了**, and **下一步**. Keep the report factual and separate AI recommendation from Human decision.

Use plain Chinese in the Human-facing report. Explain the effect first, then name files or technical terms. On first use, write a Chinese explanation with the English name in parentheses, such as 角色基准档（Character Canon）, 同角色模式（Same Character）, or 标准立绘（Standee）. 文件名、JSON 字段、命令、模式名和正式状态名可以保留英文。
