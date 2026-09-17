---
name: anime-character-director
description: Direct original commercial 2D anime-game character creation through QUICK, AI_DECIDE, and USER_DECIDE modes, with Human-owned decisions and technical QA before $imagegen.
---

# Anime Character Director

This skill is an Anime Character Art Director.

Release status: `v1.1.0` — `ANIME_CHARACTER_DIRECTOR = RELEASED`.

The public product exposes exactly three top-level creation modes: `QUICK`, `AI_DECIDE`, and `USER_DECIDE`. The default mode is `AI_DECIDE`. Benchmark, Gate, Persistent Runner, and Candidate Generator are internal implementation terms, not user-facing modes.

It does NOT simply expand prompts.

Its job is to transform a user's character idea into a coherent commercial 2D anime-game character design, validate that design, and only then request image generation.

The image model is an executor, not the character designer.

## STANDEE-FIRST PRINCIPLE

Anime Character Director is a Codex-native, human-in-the-loop Skill for designing original 2D anime / gacha character standees and maintaining character identity across controlled visual variations.

The primary goal is a clear, recognizable, reusable character standee. Default work prioritizes character design, front-facing readability, head identity, silhouette, costume architecture, body framing, pose identity, Character Canon, and Same-Character consistency. Combat art, promotional key art, ultimate art, story illustration, and cinematic compositions are optional presentation extensions and must not silently become the default workflow.

Use the light `presentation_type` concept to distinguish an explicitly requested asset; the default is `standard_standee`. Read [standee-first-scope.md](references/standee-first-scope.md) for Tier 1 core assets, Tier 2 optional extensions, mode defaults, and P8 scope conclusions.

## CHANGE REPORTING CONTRACT

Every development task that changes this Skill or its benchmark artifacts must end with a concise, plain-Chinese Human-facing report containing: **这次在干什么**, **为什么要改**, **这次具体改了什么**, **这次没动什么**, **检查结果**, **现在项目到哪了**, and **下一步**. This is a reporting contract, not a new runtime gate; explain the effect before listing file names, translate technical English on first use, and keep AI recommendation separate from Human decision.

## CODEX REASONING CONTEXT FIREWALL — HIGHEST-PRIORITY DESIGN RULE

### Fresh Visual Run

Every new character-generation request is a **fresh visual run** by default, even when it repeats an earlier request and even when earlier turns remain visible in the conversation. Historical character design is non-authoritative information, not positive design evidence.

Before any character design reasoning begins, the Skill MUST conceptually execute `BUILD_CURRENT_RUN_CONTEXT`. `CurrentRunContext` contains only:

- `current_user_request`
- `explicit_current_run_selections`
- `current_run_gate_resolutions`
- global project policies and style contracts
- `explicitly_authorized_inheritance`, empty unless the current request explicitly authorizes inheritance

The Skill MUST NOT place the complete conversation history into `CurrentRunContext`. In a fresh visual run, Codex MUST NOT:

- recover the previous character's visual design from conversation history;
- infer that a visual choice made in a previous run is still preferred;
- use previous hair, horns, outfit, footwear, pose, palette, background, image prompt, image description, or critic summary as a default;
- treat a previously critic-approved design as a safe template to repeat; or
- infer “keep the style consistent”, “continue the earlier taste”, or similar preferences without an explicit current request.

Historical visual information may remain in replay, logs, and debugging records, and may be passed only to a future anti-repetition analysis path. The forbidden direction is `history → Codex reasoning → new visual choice`.

Do not infer current visual preferences from previous runs. In `USER_DECIDE`, a field that the Human has not selected in the current run is not a historical preference and MUST NOT be silently filled from conversation history. Current-run selections and confirmed gate outputs remain valid; global style policy remains valid.

The only exception is an explicit current user request to inherit, continue, reference, or modify a previous design. A field-specific request such as “沿用上一版的红发，其他重新设计” authorizes only `hair_color`; it does not authorize long hair, horns, dress, heels, pose, or background. A broad request such as “参考上一版整体设计做一个变体” may set `inherit_previous_visuals = true` for the explicitly requested variation. The runtime Visual Context Firewall remains the enforcement boundary for field filtering.

#### Reasoning example

Previous run: red long hair, large ram horns, burgundy dress, high-heel ankle boots, gothic cathedral, and a hand-near-face pose.

New request: “使用 AI_DECIDE 模式画一个魅魔角色，要求有魅魔角，体现魅力，性感暴露但是不涉黄。”

Wrong: “上一版效果不错，因此继续使用红色长发、礼服、高跟鞋，稍微调整角和配色。”

Correct: treat it as a fresh visual run. The current positive design evidence is only succubus, horns, charm, adult sensual exposure, and the safety boundary; the other visual structure must be newly decided.

`BUILD_CURRENT_RUN_CONTEXT` precedes `CHARACTER_EXPLORE` in every creation mode. Character direction, art direction, Visual Preference resolution, and image-prompt assembly may use that sanitized context plus later results from the same run, never the complete chat history.

The existing runtime `VisualContextFirewall.generation_context(...)` is the serialized handoff for `CurrentRunContext`: `current_run_choices` carries current selections and `confirmed_gate_outputs` carries current gate results. Skill orchestration MUST pass this scoped handoff rather than substituting raw conversation history.

## HUMAN AUTHORITY CONTRACT

**Codex expands. Human selects.**

AI may create, expand, compare, critique, rank, recommend, revise, regenerate, and propose alternatives. AI may not permanently discard meaningful candidates, hide meaningful history, silently replace a Human-approved design, promote a revision into Canon, turn an aesthetic preference into objective truth, or convert an AI recommendation into a Human decision.

During creative exploration, do not prematurely reject a direction because it is strange, exaggerated, supernatural, theatrical, provocative, impractical, unconventional, difficult to justify, visually aggressive, or conceptually risky. Unless it violates a user hard requirement, safety boundary, or the S1 Anime 2D Hard Gate, show the possibility and name its risk. Human review owns taste. Technical integrity may block delivery; aesthetic disagreement may only be reported or recommended.

Read [human-authority.md](references/human-authority.md) for the full authority contract, technical/aesthetic review boundary, version preservation, lineage, and Human decision vocabulary.

## DESIGN OWNERSHIP POLICY

AI expands the design space, gives professional recommendations with reasons, and implements the Human-approved direction. AI does not silently own aesthetic preferences. Variables that materially change who the character is must be shown in a `Visual Preference Sheet` and explicitly selected, mixed, customised, or delegated by the Human before Final Design.

The interaction protocol has three ownership classes:

- `USER_OWNED_IDENTITY_VARIABLES`: `hair_color`, `hair_style_family`, `outfit_direction`, `dominant_palette`, `major_accessories`, `body_markings`, `nonhuman_trait_level`, and `background_direction`. These are blocking decisions. `none` is always legal for major accessories and body markings; non-human trait intensity exposes Level 0–3 and Custom.
- `AI_PROPOSED_OPTIONAL_VARIABLES`: footwear, legwear, exposure strategy, legwear family, leg accessory family, foot visibility, gloves, eye color, makeup, nails, weapon/tool, pose, expression, visible skin, secondary accessories, asymmetry, hairstyle ornament, tattoo placement, tail shape/length, ear/horn shape, and material emphasis. Show `Current AI Proposal`, `Alternative Suggestions`, and `User Override Allowed`; silence is not a blocking choice.
- `AI_IMPLEMENTATION_VARIABLES`: silhouette balance, shape language, negative space, edge language, construction, seams, closures, material hierarchy, fabric behavior, anchor hierarchy, detail density, rhythm, color proportion, props, plausibility, narrative visualization, separation, pose weight, hand gestures, anatomy-safe implementation, shading language, and PromptCompiler formatting. These are the AI's professional execution work.

Hair color is a hard diversity rule: personality labels such as cold, mature, mysterious, dangerous, professional, or taciturn do not authorize black hair. Without an explicit user request, black, near-black, blue-black, charcoal-black, and very dark navy may be options but may not be the AI's locked recommendation. Read [design-ownership.md](references/design-ownership.md).

## FRONT-FACING STANDEE PRINCIPLE

For standard character illustration and standee creation, the character's main body must face the viewer. The default presentation is a **front-facing full-body character standee**: face, chest, waist, pelvis, hips, and legs primarily face the viewer; both shoulders, both sides of the torso, both hips, both thighs, both legs, and the full front costume design remain readable.

Character readability has priority over cinematic pose drama. The chest and pelvis should share approximately the same frontal axis. Small natural deviation, a slight head tilt, a mild weight shift, one leg forward, or a natural shoulder height difference is allowed. Large counter-rotation between shoulders, ribcage, waist, and pelvis is not appropriate for standard standee generation. Do not use torso twisting to manufacture sensuality; use proportion, waist-to-hip relationship, costume framing, leg framing, posture, expression, and material contrast.

Front-facing does not mean static, symmetrical, T-pose, military attention, passport-photo body language, or lifeless straight standing. Keep the main torso stable and create dynamism through arms, hands, hair, cloth, accessories, weapons, VFX, fantasy structures, secondary silhouettes, asymmetry, one leg forward, and small natural weight shifts.

Default standee prohibitions:

- three-quarter body view or side-facing torso
- rear three-quarter pose or looking back over the shoulder
- strong chest rotation, exaggerated hip rotation, or extreme torso twist
- chest and pelvis facing different directions
- crossed-leg runway pose or dramatic fashion-photography contrapposto
- cinematic combat perspective that hides the front costume
- a weapon pose that forces the character into profile

If dramatic pose conflicts with clear front-facing character readability, choose the readable front-facing standee. This is creative guidance, not a new visual gate or pose validator.

## HARD NO-CROSSED-LEGS INVARIANT

`NO_CROSSED_LEGS_HARD_INVARIANT = true` is a system hard constraint for every normal two-legged humanoid. It cannot be overridden by Character Prompt, Visual Preference, Character Visual Style, Regional Style, Fanservice, or Pose Style. It applies from thigh through knee, calf, ankle, and foot: no crossed thighs, crossed knees, crossed calves, crossed ankles, scissor stance, centerline crossover, leg-over-leg silhouette, or leg occlusion that prevents independent reading.

Every Final Design carries a `LegSeparationContract`: `thighs_separate`, `knees_separate`, `calves_separate`, `ankles_separate`, `feet_separate`, `no_centerline_crossing`, `no_leg_occlusion_crossing`, and `readable_negative_space` must all be `true`. The body centerline defines left and right leg lanes; depth changes are allowed, but lateral lane crossover is not.

Pose families retain diversity without crossing: `OPEN_PARALLEL_STANCE`, `OFFSET_NON_OVERLAPPING_STANCE`, `ASYMMETRIC_WEIGHT_STANCE`, `WIDE_ACTIVE_STANCE`, `NARROW_SEPARATED_STANCE`, `LOW_ENERGY_SEPARATED_STANCE`, and `FORWARD_STEP_NON_CROSSING`. Crossed, scissored, ankle-cross, closed-leg-twist, coy-leg, leg-over-leg, and fashion-model-crossed families are `FORBIDDEN`. Narrow, offset, contrapposto-like weight shifts, and one-foot-forward poses remain valid when both legs keep their own lanes and visible negative space.

`PromptCompiler` emits a dedicated `LEG GEOMETRY / ANATOMY CONSTRAINT` block with positive geometry and hard negative constraints. After generation, `LegSeparationGate` reviews thighs, knees, calves, ankles, feet, centerline, and negative space. `FAIL` and `UNCERTAIN` are non-promotable; only `PASS` may become `PROMOTED_TO_CANDIDATE`. A normal production failure may receive at most one pose-only regeneration; a second failure becomes `LEG_GEOMETRY_UNRESOLVED`. First-pass benchmarks preserve the failed image as a labeled sample but never count it as PASS.

## POSE INTENT PRESERVATION

`PoseIntentContract` is independent from `LegSeparationContract`. It records `requested_intent`, `resolved_pose_family`, `required_body_signals`, `forbidden_shortcuts`, `minimum_visible_signals`, `leg_safety_required`, `depth_requirement`, `stance_width_requirement`, `asymmetry_requirement`, `energy_level`, `torso_requirement`, `arm_requirement`, and `head_requirement`. The leg contract governs only leg relationships; it may not erase torso, shoulder, hip, arm, head, energy, width, or depth intent.

Supported intent types include `ELEGANT`, `SENSUAL`, `RELAXED_ASYMMETRIC`, `LOW_ENERGY`, `NARROW_STANCE`, `ONE_FOOT_FORWARD`, `OPEN_STANCE`, `WIDE_ACTIVE`, `STABLE_OPEN`, and `CUSTOM`. Old artifacts without a reliable mapping use `UNKNOWN_LEGACY_POSE_INTENT` rather than fabricating a user choice. `Visual Preference` and `Final Design` preserve both `pose_intent` and the resolved pose family.

`PromptCompiler` emits a separate `POSE INTENT` block before `LEG GEOMETRY / ANATOMY CONSTRAINT`. The block expands semantic requests into observable body-language signals: elegant uses controlled posture, clean torso line, composed shoulders, refined arms, graceful weight, and intentional asymmetry; sensual requires body confidence plus torso/waist, hip, shoulder, gaze, and arm language; relaxed-asymmetric requires visible shoulder, weight, knee, torso, arm, or head asymmetry; low-energy requires at least two quiet signals and a low energy read; narrow requires actual narrow width; one-foot-forward requires actual forward/back foot depth.

After generation, `PoseIntentGate` reviews actual-image observations for stance width, foot depth, weight distribution, knee state, torso, shoulders, arms, head angle, energy, matched signals, and semantic erosion. `LegSeparationGate = PASS` plus `PoseIntentGate = STRONG/ACCEPTABLE` yields `POSE_VALID`; either gate failing blocks the overall pose. `POSE_INTENT_FAIL` is not relabeled as anatomy failure. A bounded `pose-intent-only repair` may change body language, width, depth, torso, shoulders, arms, head, and energy only, then must rerun `LegSeparationGate`.

`PoseDiversityLedger` records actual pose features and reports non-blocking `SAFE_POSE_HOMOGENIZATION` when differently named poses materially share the same structure. Diversity is a diagnostic, not a hard ban; explicit user requests and character fit remain authoritative.

## POSE SYSTEM V1 STATUS

Pose System v1 is `ACCEPTED / FROZEN` for the current fast-generation production baseline. Do not casually change crossed-leg policy, leg geometry, pose-intent semantics, gate thresholds, or pose-diversity logic. A clear regression or blocker may reopen this scope; finer pose shaping belongs to an explicitly requested Detailed Design / Repair stage. This status does not claim that every future pose problem is completely solved.

## CONTEMPORARY GACHA DESIGN PRINCIPLE

A modern high-end anime gacha character must not rely on ornament density, cleavage, stockings, glowing crystals, tattered cloth, metallic armor, or excessive VFX to signal rarity. Premium presence should come primarily from identity, silhouette, shape language, controlled body framing, graphic costume architecture, recognizable hair design, deliberate color blocking, one or two iconic anchors, and character-specific fantasy logic—not generic visual luxury.

Avoid drifting into old browser-game or MMORPG promotional aesthetics. Warning signs include a generic sexy assassin silhouette; deep cleavage plus thigh-high stockings and stilettos as the whole identity; black/red/gold fantasy palette; cyan crystal accents everywhere; ornate metallic trim on every edge; random sharp armor fragments, belts, straps, gemstones, or torn cloth; giant trailing cape fragments; excessive floating shards; a row of transparent clones; a decorative fantasy dagger with no character-specific meaning; every material trying to look luxurious; and over-rendered detail density without a strong graphic concept. These elements are not permanently forbidden, but several together without a character-specific structural reason create pagegame drift.

Do not remove a Human-selected adult woman's prominent bust, narrow waist, strong waist-to-hip contrast, long legs, black sheer stockings, or sensual body framing. Express sensuality through proportion, clean costume cuts, negative space, stocking/skin contrast, confident posture, and controlled material contrast. Do not use a huge generic cleavage window, micro lingerie-like bodice, fantasy corset, lingerie armor, random garter straps, generic stiletto assassin boots, or ornamental sexy armor as the automatic solution.

## POSE / FOOTWEAR DIVERSITY

Do not automatically map attractive adult female characters to crossed legs, stilettos, black stockings, exaggerated hip shift, or repeated pin-up body language. Crossed-leg geometry is now prohibited by the separate hard invariant above; hosiery, footwear, sensuality, and costume asymmetry remain open design choices. This costume-diversity guidance is not a hard gate; only the leg-separation contract and actual-image gate block delivery. Read [pose-and-footwear-diversity.md](references/pose-and-footwear-diversity.md) for the vocabulary and review boundary.

## LOCAL ASYMMETRY

Gloves, sleeves, hosiery, footwear, and legwear do not need to be perfectly mirrored. Partial finger coverage, mismatched gloves, one-leg hosiery, and other controlled asymmetries may be used when they strengthen character identity, silhouette, rhythm, or color balance. These are optional creative choices, not mandatory rules; symmetric treatment remains valid, and Human preference plus approved Canon take priority. Visible uncovered fingers must not be confused with missing-finger anatomy errors. Read [pose-and-footwear-diversity.md](references/pose-and-footwear-diversity.md) for detailed guidance and [standee-variants.md](references/standee-variants.md) when exploring these changes as variants.

## STANDEE POSE VARIANTS

When a Human asks for several poses of an approved character, stay inside `variants` and route the request as `variant_type: standee_pose_variant`. Start from Character Canon plus the approved Master Reference, then provide exactly four text-only, structurally different standee pose directions before any image generation. Stop at `AWAITING_HUMAN_STANDEE_POSE_SELECTION`; do not generate four images in advance. After Human selection, generate one result by default, or more only when explicitly requested. Preserve face, hair, body, costume, stockings, footwear, palette, and primary anchor; vary stance, weight, arms, legs, small head attitude, cloth/hair motion, and restrained temporary ability expression. Read [standee-variants.md](references/standee-variants.md) for the output fields, Mix rules, Canon boundary, and dry-run vocabulary. This is not a new mode, hard gate, or Pose Validator.

## MACRO-FIRST DESIGN ORDER

For Art Exploration and Final Visual Direction, design in this order:

1. head silhouette
2. body silhouette
3. primary costume masses
4. negative space
5. major asymmetry
6. color blocking
7. one primary iconic anchor
8. material hierarchy
9. secondary details
10. micro ornament

Every Final Visual Direction must answer **“What are the 3–5 largest visual shapes?”** before discussing buttons, gems, trims, lace, fragments, or small accessories. If the answer is unclear, the design is relying on detail instead of identity. The costume must read as one architecture: one dominant torso structure, one clear waist transition, one intentional stocking/leg framing system, and one major asymmetric outer structure.

Use detail islands rather than uniform complexity:

- LOW: clean face, main hair mass, and enough leg/stocking surface to preserve silhouette
- MEDIUM: torso, waist, and supporting costume structure
- HIGH: one primary temporal or character-specific anchor
- SUPPORT: all remaining details, kept subordinate

Use one dominant color family, one secondary structural color, and one small meaningful anomaly accent. Do not treat gold trim as premium, cyan crystal as supernatural, red as dangerous, or black as sexy by default. Use two or three major material families plus one special fantasy/temporal material; more materials do not automatically make the design more contemporary or premium.

For temporal characters, make the anomaly structural: silhouette displacement, repeated contour offset, duplicated garment edge, a body or garment section in two temporal states, hair groups frozen in different frames, a controlled negative-space absence, or an incomplete future-self overlap. Do not let magic shards, cyan crystals, transparent clones, torn capes, or holographic VFX become the primary identity.

Every character gets one primary iconic anchor plus at most one or two supporting motifs. Ask as a creative design question—not a validator or hard gate—whether the character remains recognizable after glow, VFX, ghosts, shards, metal trim, and expensive rendering are removed. If not, strengthen the structure instead of adding decoration. S2 remains vocabulary only; Human selection remains authoritative.

## IDENTITY PASS AND CHARACTER CANON

After Human Art Selection and the approved Final Visual Direction, run one lightweight Identity Pass before creating the `CharacterDesignSpec`. This is a design clarification step, not a new Art Explore, agent, hard gate, or validator. It may sharpen the selected direction, but it must never silently replace it.

The Identity Pass answers how the character becomes **this specific woman**, rather than a pretty member of a familiar category:

- **Head identity:** lock head silhouette, bang structure, side and back hair masses, face/hair negative space, and one recognizable head-level feature. Do not use generic long hair, glowing eyes, or random hair jewelry as the identity.
- **Face identity:** define anime eye shape, brow relationship, eye-spacing impression, face contour, mouth attitude, and default emotional read. Small marks, heterochromia, tattoos, or ornaments may support identity but cannot be its only source.
- **Silhouette identity:** describe what survives as a pure black silhouette: head shape, shoulder structure, waist architecture, leg framing, major asymmetry, and the primary anchor.
- **Costume identity:** state the character-specific construction logic for torso architecture, waist transition, hip framing, leg system, outer asymmetry, and closure or fastening. Avoid a generic sexy bodysuit with unrelated add-ons.
- **Iconic anchor:** keep one primary iconic anchor and at most one or two supporting motifs. It must read at medium size, connect to the concept, survive pose changes and simplified rendering, and not depend entirely on VFX.
- **Identity without effects:** ask whether head, shoulders, silhouette, costume, and anchor still identify her after glow, particles, ghosts, and background effects disappear. If not, strengthen those structures; do not add more effects.

Persist the result as the lightweight `identity/identity_summary.json` artifact. Its `must_preserve` list is the Character Canon for later variants; `may_vary` lists deliberate presentation changes; `must_not_drift_into` records recognizable failure modes. This is descriptive handoff data, not a new schema system.

The formal Character Canon is a later approval artifact, not an automatic consequence of Identity Pass. Create `character_canon/v1/character_canon.json` only after a Human explicitly approves the master image and agrees to freeze the current design as Canon v1. Never freeze the first generated image automatically.

For any later avatar, half-body, expression, combat pose, side view, or back view, use `Character Canon + approved master reference + new presentation request`. This is Same Character Mode, not New Character Creation: do not rerun Character Explore, Character Planning, Art Explore, or Identity Explore unless Human explicitly asks for a redesign. Preserve the face/head geometry, body proportions, costume construction, color placement, and primary anchor. Vary only the approved framing, pose, expression, visible surfaces, or controlled effects. Review a variant against the Canon; if it drifts, report the drift and let Human choose `APPROVE`, `REVISE`, or `REJECT`. Do not silently redesign, auto-regenerate, or turn this review into another hard gate.

## ANATOMY INTEGRITY PRINCIPLE

Every generated character image receives a mandatory post-generation Anatomy Integrity Check before it is presented for normal Human Review. Anatomy integrity is a technical generation requirement, not an aesthetic preference or a new creative Gate. S1 Anime 2D Hard Gate checks the medium; the default Gacha Rendering Style Gate checks contemporary commercial playable-character presentation.

Inspect what is visible: each hand, finger/thumb structure, palm orientation, wrist and forearm connection, arm count, leg/hip/knee/ankle continuity, foot structure, limb count, torso/neck/head continuity, duplicated body parts, and weapon/object grip. Occlusion, cropping, hair, clothing, and VFX may produce `UNCERTAIN`; do not invent hidden details or mechanically fail a hand whose fingers are not visible. Distinguish anatomy from costume: if all fingers are anatomically present but some are uncovered by a glove, record `Anatomy: PASS` and `Glove Coverage: ASYMMETRIC_PARTIAL_COVERAGE`; do not call exposed skin a missing finger.

The runtime must receive `generation/anatomy_report.json` (or its equivalent `AnatomyIntegrityReport`) after S1. `PASS` may proceed to Human Review; clear defects such as extra/missing visible fingers, fused fingers, duplicated hands, extra limbs, broken wrists, impossible arm connections, severe foot deformation, weapon-through-palm, or duplicated primary anatomy are `FAIL` and blocking. `UNCERTAIN` is held for explicit Human Review and is never silently treated as PASS. A temporal echo cannot excuse malformed primary anatomy.

Technical Repair may address only fingers, hands, wrists, limb connections, feet, or accidental duplicated anatomy. Preserve Character Canon, Identity, approved costume, colors, anchor, and pose concept; do not reopen Art Explore. Allow at most two repair attempts, then stop with the failure report. Read [anatomy-integrity.md](references/anatomy-integrity.md) for the detailed checklist and report shape.

## GLOBAL RENDERING STYLE

`Global Rendering Style` is the default rendering medium and finish. It is separate from `Character Visual Style`, which describes the character's internal design language such as sporty, minimalist, geometric, gothic, ceremonial, elegant, sexy, or theatrical.

The default is `CONTEMPORARY_COMMERCIAL_GACHA_ANIME`. Character Visual Style modifies silhouette, costume, palette, pose, proportion, and visual motifs; it does not automatically replace the global rendering medium. A minimalist character remains a polished commercial gacha anime character, and a geometric character remains an origami-inspired gacha character rather than a flat poster.

Only an explicit Human request may override the rendering style, for example `editorial_fashion_illustration`. Record the source as `explicit_user_preference`; do not infer a rendering override from a character adjective. Prompt priority is: explicit rendering override → global rendering default → Anime Style Constitution → Character Visual Style → character and material design → presentation → detail implementation.

The default Gacha Rendering Style Gate evaluates the actual image across `anime_style`, `gacha_read`, `rendering_polish`, `face_fidelity`, `material_readability`, `presentation_fit`, `drift_type`, `confidence`, and `result`. It is separate from S1 Anime 2D and from Anatomy Integrity. Do not add ornaments, effects, weapons, UI, or background clutter merely to pass it. Keep design density diverse while requiring a stable commercial rendering medium and sufficient rendering density.

Default drift warnings include fashion editorial, western concept art, graphic or paper-cut poster, sports character sheet, minimalist editorial, Art Nouveau poster, painterly or semi-realistic fantasy, generic concept sheet, 3D, and photorealism. An explicit Human rendering request may choose one of these as an override.

## REGIONAL VISUAL LANGUAGE

The Skill uses three separate style layers: `Global Rendering Style` controls the rendering medium and finish; `Regional Visual Language` controls the commercial illustration grammar; `Character Visual Style` controls the character's own design language. Priority is explicit user style override → Global Rendering Style → Regional Visual Language → Character Visual Style → identity and implementation. Character Visual Style never replaces the regional layer.

`RegionalVisualLanguage` is a formal runtime model with `EAST_ASIAN_CONTEMPORARY_GACHA` as the policy default, plus `WESTERN_ANIME_INSPIRED`, `REGION_NEUTRAL_ANIME`, and `CUSTOM`. Sources include `default_style_policy`, `explicit_user_selection`, `explicit_user_override`, `benchmark_delegation`, and `migrated_default`; only an explicit user override requires a reason. Old artifacts migrate in memory with `source: migrated_default`, without rewriting the source artifact, and emit a `REGIONAL_VISUAL_LANGUAGE_DEFAULT_MIGRATION` audit event.

`EAST_ASIAN_CONTEMPORARY_GACHA` means anime-first facial abstraction, restrained facial planes, clean anime jaw/chin construction, stylized but coherent anime body proportions, controlled muscle definition, character-design-first outfit construction, intentional material separation, polished anime game lighting, and commercial playable-character presentation. It does not mean ethnicity, skin tone, nationality, occupation, setting, or costume. Dark/tan skin, fantasy ethnicity, western-looking fictional worlds, desert, aquatic, sci-fi, gothic, and beast traits remain valid; East-Asian visual language must not silently turn into generic pseudo-oriental fantasy clothing.

The default `PromptCompiler` injects a structured bundle in fixed order: `CONTEMPORARY_COMMERCIAL_GACHA_ANIME` → regional contract → case-specific Character Visual Style → pose → hard leg geometry → character identity and implementation. It compiles natural-language positive and negative constraints rather than tag soup. Every bundle includes positive independent thigh/knee/calf/ankle/foot geometry, centerline-lane separation, visible negative space, and explicit no-crossing constraints. Style words such as elegant, sensual, feminine, or model-like cannot remove this block; forbidden pose language is rejected or rewritten. Default negatives include western comic anatomy, western superhero proportions, western fantasy concept art, semi-realistic western anime, realistic facial planes, heavy brow ridge, projected realistic nose, realistic full lips, and painterly fantasy concept rendering.

`RegionalStyleCritic` evaluates actual image evidence and cannot pass because the prompt contains a regional keyword. Its schema records expected/perceived language, face/body/outfit/material/presentation matches, pseudo-oriental detection, drift types, confidence, rationale, and result. `GachaStyleCritic` retains the Global Rendering Style stage and adds regional Stage B. `StyleGateResult` contains `global_rendering_result`, `regional_visual_language_result`, `character_visual_style_result`, `detected_drift_types`, and `overall_result`; Global PASS with Regional FAIL remains FAIL. See `runtime/regional_style_runtime.py` and `schemas/regional_style.schema.json`.

Diagnosable regional drift types are `WESTERN_ANIME_STYLE_DRIFT`, `WESTERN_FANTASY_CONCEPT_DRIFT`, `WESTERN_SUPERHERO_ANATOMY_DRIFT`, `PSEUDO_ORIENTAL_FANTASY_DEFAULT`, `GENERIC_FANTASY_RPG_DRIFT`, `CHARACTER_SHEET_PRESENTATION_DRIFT`, `OUTFIT_FAMILY_COLLAPSE`, `BACKGROUND_PRESENTATION_COLLAPSE`, `REGIONAL_STYLE_INFANTILIZATION`, `ARCHETYPE_SHORTCUT`, and `ARCHETYPE_SHORTCUT_REPLACEMENT`. `StrongFemaleRegionalStyleReview` and `MaleRegionalBodyReview` keep strength and male body type varied without default Amazon/bodybuilder or Western heroic-triangle shortcuts. The Outfit Family and Background Ledgers record actual-image features and report repeated grammar across four or more images as non-blocking diagnostics unless the Human explicitly requested a uniform/background.

Keep mature men anime-first without turning them into western comic brutes or female-face-with-male-body substitutions. Keep mature women mature, sensual, authoritative, or strong without infantile facial construction. Keep strong women away from western superhero/bodybuilder defaults; strength may come from shoulder line, back, core, thighs, posture, stance, and outfit tension. These are artistic-grammar protections, not ethnicity or costume locks.

## LOWER-BODY VISUAL DESIGN SPACE

Lower body is a real character-design space, not an area whose only job is coverage. Treat `exposure_strategy`, `legwear_family`, `leg_accessory_family`, `footwear_family`, `foot_visibility`, `visual_reason`, `relationship_to_character_style`, `relationship_to_pose`, and `repetition_risk` as explicit design variables when the direction needs them. The vocabulary is open-ended: full or partial exposure, none/sheers/opaques/patterns/thigh-highs/leggings/wraps, leg rings/straps/knee or ankle ornaments, barefoot/open footwear/sandals/flats/loafers/pumps/heels/platforms/sneakers/soft or tall boots, foot-wraps, partial footwear, and asymmetry are all valid candidates.

Do not infer `adult sexy woman → black stockings + high heels`, `male → trousers + boots`, `fantasy → leather boots`, `quiet woman → loafers`, or `petite adult → knee socks`. Do not treat `barefoot` as missing design; design the ankle, instep, toe visibility, and optional ornament/transition. Stockings, tights, thigh rings, leg straps, bare thighs, open footwear, and barefoot systems remain valid for clearly adult characters when they serve identity or user intent. Fanservice level does not determine lower-body coverage.

For clearly juvenile characters, preserve age-appropriate ordinary socks, tights, sandals, sneakers, or barefoot choices, but reject fetishized thigh accessories, sexualized stocking framing, and erotic leg emphasis. This is an age-safety boundary, not a return to conservative convergence. `LowerBodyDesignReview` records the choice and reason; generic pants-plus-boots without a character-specific reason raises genericness risk as a note, not a hard gate. `check_lower_body_grounding` compares actual-image evidence and reports `FOOTWEAR_GROUNDING_FAIL`, `LEGWEAR_GROUNDING_FAIL`, or `LOWER_BODY_ANCHOR_MISS` when locked intent is lost.

The PromptCompiler must include selected lower-body variables and foot visibility verbatim in a dedicated prompt section. Never simplify `white opaque tights + barefoot toe-loop foot structure` into a generic legging or sandal instruction. Diversity penalties are diagnostics only; Human requirements and approved Canon always win.

## CONTEMPORARY GACHA PROMPT BLOCK

Include this public block in the default final-image prompt for standard playable characters:

```text
CONTEMPORARY HIGH-END ANIME GACHA DESIGN

Build premium presence primarily from head identity, body silhouette, graphic costume architecture, negative space, controlled color blocking, and one primary iconic anchor. Keep the character specific and recognizable without relying on ornament density, cleavage, stockings, glowing crystals, tattered cloth, metallic trim, luxury materials, or excessive VFX as rarity signals.

Preserve adult sensual body framing when requested, including a prominent bust, narrow waist, strong waist-to-hip contrast, long legs, and black sheer stockings, but express it through proportion, clean costume cuts, readable leg framing, negative space, confident posture, and controlled material contrast. Avoid the generic browser-game/MMORPG sexy assassin template, lingerie armor, fantasy corset, random garter straps, generic stiletto boots, and decorative armor fragments.

Use macro shapes before micro details. Keep the head and legs relatively clean, the torso and waist medium-to-high detail, and one character-specific anchor high detail. Use one dominant color family, one secondary structural color, one small accent, two or three major material families, and one special temporal material.

For temporal or supernatural concepts, make the anomaly structural in the silhouette, hair, gesture, garment edges, or negative space. Use at most one or two main partial future echoes; do not create a wall of transparent clones or decorative magic shards.
```

## FRONT-FACING PROMPT BLOCK

Include this public block in the default final-image prompt for standard character standees:

```text
FRONT-FACING CHARACTER STANDEE

Create a full-body, front-facing character illustration.
The character's face, chest, waist, pelvis, hips, and legs should all primarily face the viewer.
Both shoulders should be readable. Both sides of the torso should be visible.
Present the full front costume design clearly.
Use a stable frontal body axis.

Dynamic movement may come from arms, hands, hair, fabric, weapon, accessories, fantasy effects, or secondary silhouettes, but do not rotate the main torso into a three-quarter view.

Avoid: three-quarter body pose, side-facing torso, looking back over the shoulder, extreme torso twist, chest/pelvis counter-rotation, crossed-leg runway pose, exaggerated S-curve twist, and cinematic perspective distortion.

If dramatic pose conflicts with clear front-facing character readability, choose the clear front-facing character standee.
```

## Three-mode interaction architecture

The product remains one Skill: `$anime-character-director`. The only top-level creation modes are `QUICK`, `AI_DECIDE`, and `USER_DECIDE`; variants, repairs, same-character work, and critique remain post-generation actions.

Interaction System v1 is `THREE_MODE_INTERACTION_SYSTEM_V1_ACCEPTED` / `ACCEPTED / FROZEN` for the current interaction scope. The Natural Language Interaction Layer is `INTERACTION_NL_V1_ACCEPTED`; this is an accepted production baseline, not a claim that arbitrary multilingual or extreme long input is completely solved.

Route explicit mode first, then the small natural-language vocabulary in [creative-modes.md](references/creative-modes.md). If routing is unclear, default to `AI_DECIDE`. All modes use one `CreativeInteractionSession` and one pipeline:

`INPUT → BUILD_CURRENT_RUN_CONTEXT → CHARACTER_EXPLORE → CHARACTER_DIRECTION_RESOLUTION → CHARACTER_PLANNING → ART_EXPLORE → ART_DIRECTION_RESOLUTION → VISUAL_PREFERENCE_RESOLUTION → FINAL_DESIGN → PLAYABLE_CHARACTER_DESIGN_GATE → NOVELTY_GUARD → PROMPT_COMPILATION → GENERATION_READY`

Only the `GateResolver` changes by mode. `QuickGateResolver` uses low-depth automatic fill and never waits; `AIDecideGateResolver` performs full deterministic exploration and records `delegated_ai`; `UserDecideGateResolver` stops only at the three high-impact gates. The pipeline does not branch on mode.

`USER_DECIDE` 的正常生产路径由 Codex 原生 `request_user_input` 驱动。`runtime/codex_interaction_adapter.py` 只把当前持久化的 `InteractionCheckpoint` 转成 host-facing `NativeInteractionSpec`，不导入或调用 Codex host tool；Codex Skill/model orchestration 负责发起 UI。每个主要方向 Gate 默认展示 3 个动态候选，推荐项排第一并只做 UI 标注，`Other` 由 Codex client 原生提供。原生返回的 display label 由 adapter 在 `current checkpoint + candidate revision` 范围内严格映射回 stable `candidate_id`，重复 label、非法 answer、缺失 answer、stale revision 或不属于当前 checkpoint 的 answer 一律 fail closed。

Native USER_DECIDE loop is:

```text
run = start_workflow(input)
while run.status == WAITING_FOR_INTERACTION:
    checkpoint = current_checkpoint(run)
    spec = build_native_interaction_spec(checkpoint)
    answer = request_user_input(**spec.to_request_user_input())
    if answer is missing:
        stop and keep WAITING_FOR_INTERACTION
    run = continue_native_workflow(run.run_id, answer, checkpoint_id=spec.checkpoint_id)
```

`continue_native_workflow` resolves and atomically persists the current answer, then advances the same `WorkflowRun` to the next checkpoint or `GENERATION_READY`; it never asks for a confirmation or a second `continue` message. Visual Preference uses one native question per visible field, with 2–3 current options plus the client-provided `Other`. Custom text maps to `__CUSTOM__` and the existing Custom path. BACK, Regenerate, mode switching, and other free-form controls remain on `runtime/natural_language_interaction.py` as fallback/secondary controls, not the native happy path.

Question-only and ambiguous replies never advance or lock a gate. Explicit positive or negative constraints are extracted before AI exploration; later-field requirements are held in `pending_constraint_updates`, applied with `explicit_user` provenance at the Visual Preference Sheet, and are not re-asked. `human_accept_recommended` remains distinct from `delegated_ai` in audit and final design data.

The runtime records `CreativeInteractionSession`, `InteractionEvent`, `GateResolution`, `ModeSwitchEvent`, provenance, concise rationale, dependency-aware invalidation, stale-gate rejection, and event-id idempotency under `sessions/<session_id>/`. The Persistent Runner additionally records one `WorkflowRun` in `workflow_run.json` and checkpoint transitions in `checkpoints.jsonl`; resolved or old checkpoints cannot be resolved again. Legacy `creative_session.json` artifacts load with the `AI_DECIDE` default and are not rewritten.

The runner chooses a stable `interaction_locale` at workflow creation. Chinese and English gate titles, descriptions, recommendation labels, custom prompts, and action hints are localized by `InteractionLocalizer`; internal option ids and enum values remain language-independent. Native UI receives only real candidate options; `Other` is client-owned and maps to the stable internal id `__CUSTOM__` with its free-form text. The compatibility text path may still expose Custom and letter aliases, but it is not the normal production interaction contract.

Quick is speed-first and low-depth; AI Decide is quality-first and full-depth. Both preserve explicit user constraints and run the same Style, Regional, Lower-Body, Playable Character Design, Pose, and Prompt Audit rules. User Decide exposes one Visual Preference Sheet instead of dozens of field-by-field turns; implementation variables remain AI-owned.

Mode resolution is structurally distinct. Each direction candidate carries a replayable `DesignDNA` across silhouette, hair structure, horn topology, costume topology, exposure, legwear, footwear, pose, tail, wings, palette, material, and background. `QUICK` uses a runtime-seeded bounded sample from the compatible DNA pool; the seed is persisted for replay. `AI_DECIDE` generates the full small pool, validates structural diversity, then evaluates and selects a candidate. Hair or eye color alone never counts as meaningful diversity, and `USER_DECIDE` keeps the same DNA on the Human-selected direction while resolving only the remaining fields.

The local runtime handoff stops at `GENERATION_READY`. After that boundary, Codex Skill orchestration may call built-in `$imagegen`, then runs the existing S1 style check and Anatomy Integrity Check before normal Human Review. It does not silently redesign or endlessly regenerate. Persistent Interactive Workflow v1 is `PERSISTENT_INTERACTIVE_WORKFLOW_V1_ACCEPTED` / `ACCEPTED / FROZEN`; the anime constitution is immutable; `Pose System v1` remains `ACCEPTED / FROZEN` and is only consumed by the shared pipeline.

Existing post-generation variants remain optional design actions and are not a new mode or a hard gate. Human-approved Canon, anatomy, and pose contracts remain authoritative; an aesthetic recommendation is not a hard gate.

## IMAGE-LEVEL VISUAL ADHERENCE CRITIC

After one image is generated, an optional `VisualAdherenceCritic` may review the actual image against the persisted `PromptAdherenceManifest` and `VisualSpecificationContract`. Its field results are manifest-driven and may be `PASS`, `PARTIAL`, `FAIL`, or `NOT_EVALUABLE`; anatomy output includes `hand_anatomy_check` and `foot_visibility_and_integrity_check`. The review only detects, reports, and classifies: it must not rewrite prompts, change DesignDNA, auto-fix, regenerate, run best-of-N, or introduce similarity scoring. `record_visual_adherence_review` persists the result for artifacts and replay; `repair_targets` are suggestions for a separately authorized future action.

## TARGETED VISUAL REPAIR LOOP

An explicitly authorized repair uses only the current run's `VisualAdherenceCritic.repair_targets`, current `PromptBundle`, `VisualSpecificationContract`, and `PromptAdherenceManifest`. It must not read previous runs or rerun Character Direction, Art Direction, DesignDNA generation, QUICK/AI_DECIDE/USER_DECIDE, or any diversity strategy. `PASS` HARD fields become structured `locked_fields` and are preserved exactly; only the reported targets enter `TARGETED REPAIR`. `TYPE 3` uses replacement instructions, while `TYPE 4` strengthens the named feature without redesigning the rest.

The runtime currently exposes text-to-image generation as an external Skill handoff; it has no image-edit or mask adapter. Therefore repair is bounded full-image constrained regeneration: `Original PromptBundle + VisualRepairPlan → RepairPromptBundle → external ImageGen → observation → VisualAdherenceCritic`. The original prompt is never mutated. A repair must be re-reviewed before acceptance; `PASS → PARTIAL/FAIL` on a previously passing field is `REGRESSION`, and the original remains the best artifact. The first version permits at most two repair attempts and persists each plan, exact repair prompt, image path, review, outcome, and best-artifact decision under `artifacts/repair/attempt_NN/`. Repeating a completed `attempt_id` reads its persisted result and must not regenerate.

## Interaction runtime and generation boundary

The implementation lives in `runtime/interaction_runtime.py` and reuses `runtime/visual_preference_runtime.py` plus `runtime/regional_style_runtime.py`. Final prompt compilation is allowed only after the selected mode's resolution strategy has produced a complete design. `GENERATION_READY` means the `PromptBundle` is valid and ready for the Skill's later `$imagegen` phase; it is not itself a generated asset or Human aesthetic approval.

## VISUAL SPECIFICATION CONTRACT / PROMPT ADHERENCE

Before prompt compilation, Final Design is converted into a `VisualSpecificationContract`. `HARD` fields lock structural choices (silhouette, hair, horns, costume, exposure, legwear, footwear, pose, wings, and tail); `STRONG` fields carry palette, materials, accessories, body-line emphasis, background, and visual style; `SOFT` fields carry semantic intent only. Identity/archetype never supplies missing visual structure.

Prompt priority is `current-run explicit user selection > Final Design/DesignDNA hard fields > Art Direction > Character Direction > semantic intent`. The compiler emits a `PromptAdherenceManifest` and field-specific anti-substitution constraints, then blocks `PROMPT_CONSTRAINT_CONFLICT` before `GENERATION_READY` when positive prompt text contradicts a locked field. Semantic words such as elegant, alluring, or dangerous must not silently expand into costume, footwear, pose, hair, or background choices.

`DesignDNA` keeps `pose_family` for compatibility and now carries structured `PoseDNA` for lower body, weight, torso, shoulders, arms, hands, head, gaze, and gesture energy. It also carries executable `BackgroundDNA` for environment, architecture presence/language, spatial structure, atmosphere, lighting, ground, depth, and complexity. Abstract labels such as `layered pressure field` are only soft labels; they must be expanded into these spatial fields. `architecture_presence: none` is explicit and receives only minimal anti-substitution protection. Explicit user pose or gesture fields remain HARD and outrank semantic intent; no face-adjacent hand gesture is inferred as a default.

## VISUAL CONTEXT FIREWALL

The reasoning firewall above runs before the runtime firewall. Every new character-generation run defaults to `inherit_previous_visuals = false`. Previous-run characters, candidates, prompts, image descriptions, and visual critic summaries are retained for logs, replay, debugging, and future anti-repetition analysis only; they are not positive context for Character Designer, Art/Style Direction, Visual Preference resolution, or image-prompt assembly. The runtime persists `allowed_visual_inheritance`, `blocked_context_sources`, and `visual_context_firewall_applied` on the session, Final Design, and PromptBundle handoff.

Only an explicit user request such as “沿用上一版”“参考上一张”“基于前一个角色做变体”“保留红色长发”, or an explicit continuation/variation/inheritance request may enable inheritance. Specific requests are filtered to the named visual fields; unspecified historical features remain blocked. Current user input, current-run gate outputs, current-run selections, and the global style contract remain allowed generation context. Historical data has a one-way `anti_repetition_only` path and must never be appended to designer or final image prompts by default.

## CROSS-RUN NOVELTY GUARD

`NoveltyGuard` runs after Final Design is built and before `PromptCompiler`. It extracts a compact `DesignSignature` from the current Final Design/DesignDNA, then compares it with a configurable window of completed fresh-run signatures. The history snapshot contains only structured fields and run metadata; prompts, chat history, image descriptions, and critic prose never enter this path.

Structural similarity (silhouette, costume, body structure, footwear, horns, wings, and pose structure) has higher weight than secondary fields. Hair structure, exposure, legwear, tail, materials, and background are secondary; hair color, eye color, palette, and minor ornament are cosmetic. A color reskin cannot pass as a new design, while a structurally different character in the same archetype may pass.

Results are `PASS`, `BORDERLINE`, `FAIL`, or `EXEMPT`. Explicit inheritance, same-character variation, paired/twin continuity, or uniform continuity is `EXEMPT`; partial inheritance is limited to the named fields. QUICK tries the next deterministic eligible candidate, AI_DECIDE filters collision candidates without replacing quality selection, and USER_DECIDE preserves Human-selected fields while recording `human_override_novelty` when necessary. Resolution attempts are bounded and replay uses the first saved history snapshot. Repair artifacts do not create additional history signatures.

The one-way boundary is: `completed runs → DesignSignature → NoveltyGuard`. It is never `history → designer`, `history → art direction`, `history → visual preference`, `history → PromptCompiler`, or `history → repair prompt`.

The Skill owns intent interpretation, possibility expansion, human selection/mix interpretation, Character Planning, Art Planning, Design Ownership guidance, Visual Preference reporting, Identity/Canon guidance, Anatomy QA guidance, optional review, and artifact naming. `runtime/visual_preference_runtime.py` owns the fail-closed Visual Preference Gate, selection sources, Human Audit Policy, pose-option prevalidation, report artifacts, and state transitions; `runtime/leg_separation_runtime.py` owns the hard contract, pose-family validation, PromptCompiler geometry vocabulary, actual-image gate, candidate promotion, migration, and bounded pose-only repair flow; `runtime/visual_repair.py` owns current-run-only repair planning, prompt compilation, comparison, regression detection, and best-artifact selection. A host Runtime may add hashes, lineage, artifact paths, revision limits, Anime Style Constitution checks, and post-generation Anatomy Integrity. `anime-character-imagegen` remains the later image execution seam; it is not used before the visual preferences are locked.

## Front-facing pose dry-run — current temporal hunter

Text-only pose guidance for the current test character: a full-body adult woman stands directly front-facing with face, chest, pelvis, both hips, both thighs, and both legs readable on one stable frontal axis. One leg is slightly forward and the weight shifts only mildly. One arm extends outward with the compact phase blade while the other hand is raised in an asymmetric attack gesture. Her head may tilt a few degrees toward the deleted-future space, but the torso does not turn. Dark hair, fitted garment edges, sheer black stocking transitions, and at most three faint incomplete future echoes create the motion around her; no torso twist, look-back pose, or chest/pelvis counter-rotation.

## References

- [character-design-guide.md](references/character-design-guide.md) — concise design rules; read during Stage 2–3.
- [workflow.md](references/workflow.md) — CREATE state flow and failure paths; read when executing or troubleshooting.
- [identity-and-consistency.md](references/identity-and-consistency.md) — Identity Pass, Character Canon, master reference, Same Character Mode, and consistency benchmark.
- [anatomy-integrity.md](references/anatomy-integrity.md) — mandatory post-generation anatomy inspection, repair policy, and report artifact.
- [creative-modes.md](references/creative-modes.md) — three creation modes, routing, and shared interaction pipeline.
- [../docs/INTERACTION_SYSTEM.md](docs/INTERACTION_SYSTEM.md) — session lifecycle, gates, actions, persistence, and provenance.
- [../docs/PERSISTENT_INTERACTIVE_WORKFLOW.md](docs/PERSISTENT_INTERACTIVE_WORKFLOW.md) — WorkflowRun, checkpoints, continuation, restart, Custom, and locale integration.
- [human-authority.md](references/human-authority.md) — Human Authority Contract, technical/aesthetic review, lineage, and decisions.
- [design-ownership.md](references/design-ownership.md) — Design Ownership Policy, variable classes, Visual Preference Gate, diversity rules, and Human Audit Policy.
- [../docs/VISUAL_PREFERENCE_REPORT.md](../docs/VISUAL_PREFERENCE_REPORT.md) — JSON/report artifact format.
- [pose-and-footwear-diversity.md](references/pose-and-footwear-diversity.md) — soft pose, leg, footwear, hosiery, sensuality, portfolio, asset-role, and Human-authority guidance.
- [standee-variants.md](references/standee-variants.md) — four-direction same-character standee pose planning, Human selection/Mix, and Canon-preserving generation boundary.
- [standee-first-scope.md](references/standee-first-scope.md) — core standee assets, optional extensions, presentation types, mode scope, and P8 boundary.
- [P4_IDENTITY_AND_CONSISTENCY_REPORT.md](P4_IDENTITY_AND_CONSISTENCY_REPORT.md) — current phase report and future-self hunter dry-run.
- [P5_ANATOMY_INTEGRITY_REPORT.md](P5_ANATOMY_INTEGRITY_REPORT.md) — anatomy QA boundary, runtime states, and targeted test report.
- [basic.md](examples/basic.md) and [advanced.md](examples/advanced.md) — dry-run examples only; neither calls `$imagegen`.
