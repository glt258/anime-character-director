---
name: anime-character-director
description: Direct original commercial 2D anime-game character creation through quick, directed, explore, variants, same-character, and critique modes, with Human-owned decisions and technical QA before $imagegen.
---

# Anime Character Director

This skill is an Anime Character Art Director.

It does NOT simply expand prompts.

Its job is to transform a user's character idea into a coherent commercial 2D anime-game character design, validate that design, and only then request image generation.

The image model is an executor, not the character designer.

## STANDEE-FIRST PRINCIPLE

Anime Character Director is a Codex-native, human-in-the-loop Skill for designing original 2D anime / gacha character standees and maintaining character identity across controlled visual variations.

The primary goal is a clear, recognizable, reusable character standee. Default work prioritizes character design, front-facing readability, head identity, silhouette, costume architecture, body framing, pose identity, Character Canon, and Same-Character consistency. Combat art, promotional key art, ultimate art, story illustration, and cinematic compositions are optional presentation extensions and must not silently become the default workflow.

Use the light `presentation_type` concept to distinguish an explicitly requested asset; the default is `standard_standee`. Read [standee-first-scope.md](references/standee-first-scope.md) for Tier 1 core assets, Tier 2 optional extensions, mode defaults, and P8 scope conclusions.

## CHANGE REPORTING CONTRACT

Every development task that changes this Skill or its benchmark artifacts must end with a concise, plain-Chinese Human-facing report containing: **这次在干什么**, **为什么要改**, **这次具体改了什么**, **这次没动什么**, **检查结果**, **现在项目到哪了**, and **下一步**. This is a reporting contract, not a new runtime gate; explain the effect before listing file names, translate technical English on first use, and keep AI recommendation separate from Human decision.

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

## Mode architecture and scope

- The product remains one Skill: `$anime-character-director`. Human-facing modes are `quick`, `directed`, `explore`, `variants`, `same-character`, and `critique`.
- Default product scope is Standee-first: `quick` and `directed` default to `standard_standee`; `explore` aims at a strong standee; `variants` prioritizes controlled standee dimensions; `same-character` defaults to Canon-preserving standee/reference assets; `critique` is usually for character/standee design. Combat, ultimate, promotional, and story assets use explicit `presentation_type` requests and remain optional extensions, not new modes.
- `standee_pose_variant` is a sub-type of `variants`, not a seventh mode. Its default is four text-only pose directions → Human selection or Mix → one selected generation → S1 → Anatomy QA → Identity Drift Review → Human Review.
- Route an explicit mode first, then obvious natural-language intent. Default to `explore`; ask one short question only when ambiguity changes the workflow. `auto` remains internal to benchmark/automation and is never a Human-facing default.
- Every meaningful branch writes lightweight `creative_session.json` and version records. Revisions branch; they do not overwrite Original. Human rejection preserves the artifact.
- Codex performs the design reasoning; do not call another LLM API, add another design agent, or invent random field combinations.
- Do not generate an image, call `$imagegen`, compile a final prompt, or create `prompt_bundle.json` unless the selected mode and its Human checkpoints permit generation.
- The anime constitution is immutable. Always follow `docs/ANIME_STYLE_CONTRACT.md` and `config/anime_style_policy.yaml`. “More realistic” may only increase material, light, or age expression inside anime abstraction.
- Never target or imitate a named existing character, game, artist, or recognizable style. Replace it with project-owned descriptors such as `modern urban anime action game` or `high-budget commercial 2D anime game`.
- Do not generate an image in this skill until Runtime validation passes. A `REJECT` result must never reach `$imagegen`.

## Explore mode workflow (default)

1. **User intent** — Extract immutable requirements, preferences, forbidden traits, and under-specified areas. Fill reasonable gaps yourself; ask only when a real conflict changes the user's intent.
2. **Character Explore** — Codex produces 4–6 short, genuinely different directions; default is 5. Cover at least one obvious direction, one high-upside unusual direction, one relationship-centered direction, one world/fantasy-heavy direction, and one wildcard. Vary identity structure, world position, relationship, specialness, emotional/gameplay fantasy, social role, and mystery structure. Do not create five profession substitutions. Do not write detailed clothing, stockings, heels, coat, skirt, armor, hair accessories, face geometry, or final prompt unless inseparable from the premise.
3. **Human Selection Checkpoint 1** — Persist `human_selection.json`, then stop at `AWAITING_CHARACTER_SELECTION`. The user may select one, delete several, mix directions, request a wilder version, or restart exploration. Do not auto-select and do not enter Character Planning without a human selection, except in explicit `auto` mode.
4. **Character Planning** — After selection, write only `CharacterPlanningBrief`: premise, player fantasy, identity layers, relationship hook, conflict/pressure, gameplay fantasy, design thesis, and open questions. A mix such as “A's identity + C's relationship + E's ability” is normal. Do not force an ordinary character to become supernatural or a profession to become the whole concept.
5. **Art Explore** — After the CharacterPlanningBrief exists, Codex produces four visual directions. They must differ structurally in silhouette, body framing, costume structure, hair identity, material language, pose, fantasy intrusion, or visual density—not merely palette, accessory, or weapon. Each Art Direction must identify head identity, 3–5 macro shapes, costume architecture, negative-space strategy, detail islands, color/material architecture, one primary iconic anchor, and a natural-language `frontal_pose_solution`. The pose solution explains how arms, hands, hair, cloth, weapon, VFX, fantasy structures, asymmetry, one leg forward, or a mild weight shift create motion around a stable frontal torso; do not use body rotation as the main dynamic solution. Read the S2 Profile as vocabulary expansion, never as a checklist, scorecard, hard gate, or creativity filter.
6. **Human Selection Checkpoint 2** — Persist `human_art_selection.json`, then stop at `AWAITING_ART_SELECTION`. The user may select one, mix several, preserve a silhouette while changing body framing, or request another set. Do not enter Visual Preference Proposal without this selection.
7. **Visual Preference Proposal** — After Art Direction selection, create `visual_preference_sheet.json` and `visual_preference_report.md`. Show all `USER_OWNED_IDENTITY_VARIABLES`, recommendations, reasons, alternatives, diversity risk, Custom, and explicit AI delegation. Do not lock identity variables from lore, profession, personality, or generic anime defaults.
8. **Visual Preference Gate** — Enter `AWAITING_VISUAL_PREFERENCE_SELECTION`. The Human may choose one option, Mix, provide Custom input, or explicitly delegate each identity variable to AI. The runtime must reject implicit decisions and remain fail-closed until every identity variable has a decision source.
9. **Human Audit and lock** — Persist the source of every identity decision (`user`, `mix`, `custom`, or `ai_delegate`) and an audit result, then enter `VISUAL_PREFERENCES_LOCKED`. Only now may Codex create the approved `VisualDirectionBrief` and `Final Design`.
10. **Identity Pass and Final Design** — Apply the six creative checks, persist `identity/identity_summary.json`, and create the `CharacterDesignSpec` from the locked preferences plus the selected direction. Implementation variables remain AI-owned and must not become extra blocking questions.
11. **Design Review and Runtime handoff** — Run the non-destructive Design Review, validate the Final Design pose against the `LegSeparationContract`, keep AI recommendation separate from Human decision, then allow `PromptCompiler` and `GENERATION_READY`. The bundled reference runtime validates the ownership gate; a host Runtime may add hashes, lineage, and artifact checks. State flow is `... → ART_SELECTED → VISUAL_PREFERENCES_PROPOSED → AWAITING_VISUAL_PREFERENCE_SELECTION → VISUAL_PREFERENCES_LOCKED → FINAL_DESIGNED → DESIGN_REVIEWED → GENERATION_READY → GENERATED → LEG_SEPARATION_CHECKED → STYLE_CHECKED → ANATOMY_CHECKED → CANDIDATE_PROMOTED`; leg crossing or uncertainty is `REJECTED_BY_HARD_ANATOMY_GATE`.

12. **After generation** — Run S1 Anime 2D, then the Gacha Rendering Style Gate, then the mandatory Anatomy Integrity Check, then normal Human Review only after the technical checks pass. S1 and Gacha are separate gates: S1 checks anime 2D medium, while Gacha checks commercial rendering and presentation. Anatomy `FAIL` enters Technical Repair or stops with a report; `UNCERTAIN` is explicitly reported for Human Review. Do not automatically redesign or inflate ornament density.

## Other modes and optional auto mode

Use [creative-modes.md](references/creative-modes.md) for the mode-specific workflow. `quick` skips Explore and fills only necessary gaps; `directed` may design a complete AI Recommended Design; `variants` creates 3–4 meaningful alternatives for one dimension, including the four-direction `standee_pose_variant` flow; `same-character` uses Canon + approved Master and adds Identity Drift Review; `critique` creates revision branches without overwriting the source.

Use `auto` only for explicit benchmark/automation requests such as “你帮我选”, “自动继续”, or “全自动”. It preserves the existing automatic PlanningPipeline path and records `AUTO_RECOMMENDED`, never `HUMAN_APPROVED`. `genericness`, `npc_risk`, `overdesign_risk`, `supernatural_inflation`, `literal_translation_risk`, `safe_selection`, `commercial_viability_score`, and `featured_playable_score` may be recorded as later analysis, but never filter directions in Human-facing Explore.

The future CREATE continuation is intentionally out of scope: only after a later approved Final Character Design stage may the existing `CharacterDesignSpec`, `PromptCompiler`, and `$imagegen` flow run.

If the user explicitly requests multiple designs first, keep them as direction summaries until selection. Do not create multiple `CharacterDesignSpec` objects or images automatically. AI Review may recommend or rank, but must show Human Options and leave `HUMAN DECISION: pending`. The historical S2 Commercial Gacha Profile remains vocabulary/reference material; the runtime default now also has a separate Gacha Rendering Style Gate. S1 Anime 2D remains a separate medium check.

## Shared technical pipeline and runtime boundary

All image-producing modes share `Generation → LegSeparationGate → S1 Anime 2D Hard Gate → Gacha Rendering Style Gate (Global + Regional) → Anatomy Integrity Check → Candidate Promotion → Human Review`; Same Character additionally runs Identity Drift Review. `LEG_CROSSING_BLOCKING_FAIL` is the same blocking class as missing, extra, or fused anatomy. Technical failure or default rendering drift may block delivery or enter bounded repair while preserving the source in lineage. Human review still owns aesthetic approval, and an explicit rendering override is recorded rather than silently inferred.

The Skill owns intent interpretation, possibility expansion, human selection/mix interpretation, Character Planning, Art Planning, Design Ownership guidance, Visual Preference reporting, Identity/Canon guidance, Anatomy QA guidance, optional review, and artifact naming. `runtime/visual_preference_runtime.py` owns the fail-closed Visual Preference Gate, selection sources, Human Audit Policy, pose-option prevalidation, report artifacts, and state transitions; `runtime/leg_separation_runtime.py` owns the hard contract, pose-family validation, PromptCompiler geometry vocabulary, actual-image gate, candidate promotion, migration, and bounded pose-only repair flow. A host Runtime may add hashes, lineage, artifact paths, revision limits, Anime Style Constitution checks, and post-generation Anatomy Integrity. `anime-character-imagegen` remains the later image execution seam; it is not used before the visual preferences are locked.

## Front-facing pose dry-run — current temporal hunter

Text-only pose guidance for the current test character: a full-body adult woman stands directly front-facing with face, chest, pelvis, both hips, both thighs, and both legs readable on one stable frontal axis. One leg is slightly forward and the weight shifts only mildly. One arm extends outward with the compact phase blade while the other hand is raised in an asymmetric attack gesture. Her head may tilt a few degrees toward the deleted-future space, but the torso does not turn. Dark hair, fitted garment edges, sheer black stocking transitions, and at most three faint incomplete future echoes create the motion around her; no torso twist, look-back pose, or chest/pelvis counter-rotation.

## References

- [character-design-guide.md](references/character-design-guide.md) — concise design rules; read during Stage 2–3.
- [workflow.md](references/workflow.md) — CREATE state flow and failure paths; read when executing or troubleshooting.
- [identity-and-consistency.md](references/identity-and-consistency.md) — Identity Pass, Character Canon, master reference, Same Character Mode, and consistency benchmark.
- [anatomy-integrity.md](references/anatomy-integrity.md) — mandatory post-generation anatomy inspection, repair policy, and report artifact.
- [creative-modes.md](references/creative-modes.md) — six Human-facing modes, routing, and shared technical pipeline.
- [human-authority.md](references/human-authority.md) — Human Authority Contract, technical/aesthetic review, lineage, and decisions.
- [design-ownership.md](references/design-ownership.md) — Design Ownership Policy, variable classes, Visual Preference Gate, diversity rules, and Human Audit Policy.
- [../docs/VISUAL_PREFERENCE_REPORT.md](../docs/VISUAL_PREFERENCE_REPORT.md) — JSON/report artifact format.
- [pose-and-footwear-diversity.md](references/pose-and-footwear-diversity.md) — soft pose, leg, footwear, hosiery, sensuality, portfolio, asset-role, and Human-authority guidance.
- [standee-variants.md](references/standee-variants.md) — four-direction same-character standee pose planning, Human selection/Mix, and Canon-preserving generation boundary.
- [standee-first-scope.md](references/standee-first-scope.md) — core standee assets, optional extensions, presentation types, mode scope, and P8 boundary.
- [P4_IDENTITY_AND_CONSISTENCY_REPORT.md](P4_IDENTITY_AND_CONSISTENCY_REPORT.md) — current phase report and future-self hunter dry-run.
- [P5_ANATOMY_INTEGRITY_REPORT.md](P5_ANATOMY_INTEGRITY_REPORT.md) — anatomy QA boundary, runtime states, and targeted test report.
- [basic.md](examples/basic.md) and [advanced.md](examples/advanced.md) — dry-run examples only; neither calls `$imagegen`.
