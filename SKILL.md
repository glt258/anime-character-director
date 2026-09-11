---
name: anime-character-director
description: Design and validate original commercial 2D anime-game characters, then prepare a style-locked prompt for $imagegen. Use for CREATE requests; do not use for image-only edits, canonization, or realistic art.
---

# Anime Character Director

This skill is an Anime Character Art Director.

It does NOT simply expand prompts.

Its job is to transform a user's character idea into a coherent commercial 2D anime-game character design, validate that design, and only then request image generation.

The image model is an executor, not the character designer.

## CREATIVE AUTHORITY PRINCIPLE

**Codex expands. Human selects.**

During creative exploration, do not prematurely reject a direction because it is strange, exaggerated, supernatural, theatrical, provocative, impractical, unconventional, difficult to justify, visually aggressive, or conceptually risky. Unless it violates a user hard requirement, safety boundary, or the S1 Anime 2D Hard Gate, show the possibility and name its risk. Human review owns taste.

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

## CONTEMPORARY GACHA DESIGN PRINCIPLE

A modern high-end anime gacha character must not rely on ornament density, cleavage, stockings, glowing crystals, tattered cloth, metallic armor, or excessive VFX to signal rarity. Premium presence should come primarily from identity, silhouette, shape language, controlled body framing, graphic costume architecture, recognizable hair design, deliberate color blocking, one or two iconic anchors, and character-specific fantasy logic—not generic visual luxury.

Avoid drifting into old browser-game or MMORPG promotional aesthetics. Warning signs include a generic sexy assassin silhouette; deep cleavage plus thigh-high stockings and stilettos as the whole identity; black/red/gold fantasy palette; cyan crystal accents everywhere; ornate metallic trim on every edge; random sharp armor fragments, belts, straps, gemstones, or torn cloth; giant trailing cape fragments; excessive floating shards; a row of transparent clones; a decorative fantasy dagger with no character-specific meaning; every material trying to look luxurious; and over-rendered detail density without a strong graphic concept. These elements are not permanently forbidden, but several together without a character-specific structural reason create pagegame drift.

Do not remove a Human-selected adult woman's prominent bust, narrow waist, strong waist-to-hip contrast, long legs, black sheer stockings, or sensual body framing. Express sensuality through proportion, clean costume cuts, negative space, stocking/skin contrast, confident posture, and controlled material contrast. Do not use a huge generic cleavage window, micro lingerie-like bodice, fantasy corset, lingerie armor, random garter straps, generic stiletto assassin boots, or ornamental sexy armor as the automatic solution.

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

## Scope and hard boundary

- Default CREATE mode is `interactive`: one user idea becomes five Character Directions, then stops at `AWAITING_CHARACTER_SELECTION`.
- `auto` remains available for benchmark/automation and retains the existing PlanningPipeline path; it is never the default.
- `VARIANT`, `REFINE`, and `CANONIZE` are reserved and not implemented.
- Codex performs the design reasoning; do not call another LLM API, add another design agent, or invent random field combinations.
- Do not generate an image, call `$imagegen`, compile a final prompt, or create `prompt_bundle.json` during P0.
- The anime constitution is immutable. Always follow `docs/ANIME_STYLE_CONTRACT.md` and `config/anime_style_policy.yaml`. “More realistic” may only increase material, light, or age expression inside anime abstraction.
- Never target or imitate a named existing character, game, artist, or recognizable style. Replace it with project-owned descriptors such as `modern urban anime action game` or `high-budget commercial 2D anime game`.
- Do not generate an image in this skill until Runtime validation passes. A `REJECT` result must never reach `$imagegen`.

## Default interactive CREATE workflow

1. **User intent** — Extract immutable requirements, preferences, forbidden traits, and under-specified areas. Fill reasonable gaps yourself; ask only when a real conflict changes the user's intent.
2. **Character Explore** — Codex produces 4–6 short, genuinely different directions; default is 5. Cover at least one obvious direction, one high-upside unusual direction, one relationship-centered direction, one world/fantasy-heavy direction, and one wildcard. Vary identity structure, world position, relationship, specialness, emotional/gameplay fantasy, social role, and mystery structure. Do not create five profession substitutions. Do not write detailed clothing, stockings, heels, coat, skirt, armor, hair accessories, face geometry, or final prompt unless inseparable from the premise.
3. **Human Selection Checkpoint 1** — Persist `human_selection.json`, then stop at `AWAITING_CHARACTER_SELECTION`. The user may select one, delete several, mix directions, request a wilder version, or restart exploration. Do not auto-select and do not enter Character Planning without a human selection, except in explicit `auto` mode.
4. **Character Planning** — After selection, write only `CharacterPlanningBrief`: premise, player fantasy, identity layers, relationship hook, conflict/pressure, gameplay fantasy, design thesis, and open questions. A mix such as “A's identity + C's relationship + E's ability” is normal. Do not force an ordinary character to become supernatural or a profession to become the whole concept.
5. **Art Explore** — After the CharacterPlanningBrief exists, Codex produces four visual directions. They must differ structurally in silhouette, body framing, costume structure, hair identity, material language, pose, fantasy intrusion, or visual density—not merely palette, accessory, or weapon. Each Art Direction must identify head identity, 3–5 macro shapes, costume architecture, negative-space strategy, detail islands, color/material architecture, one primary iconic anchor, and a natural-language `frontal_pose_solution`. The pose solution explains how arms, hands, hair, cloth, weapon, VFX, fantasy structures, asymmetry, one leg forward, or a mild weight shift create motion around a stable frontal torso; do not use body rotation as the main dynamic solution. Read the S2 Profile as vocabulary expansion, never as a checklist, scorecard, hard gate, or creativity filter.
6. **Human Selection Checkpoint 2** — Persist `human_art_selection.json`, then stop at `AWAITING_ART_SELECTION`. The user may select one, mix several, preserve a silhouette while changing body framing, or request another set. Do not enter Final Design without this selection.
7. **Final Design handoff** — Only after both human selections may Codex create the approved `VisualDirectionBrief`/existing `CharacterDesignSpec` handoff and enter the existing generation path. The handoff must state head identity, 3–5 macro shapes, costume architecture, body framing, black stocking integration when selected, one primary iconic anchor, temporal structural language, color architecture, material hierarchy, detail islands, footwear, and `frontal_pose_solution`. For standard standees, include `presentation_mode: front-facing full-body character standee` and state that the character is presented from the front with the full front costume design readable. A slight head turn is allowed; do not specify a turning body, twisting torso, looking back, or three-quarter pose. Do not silently replace the selected concept. Do not run Design Review by default; human review owns creative approval. Optional Codex review is analysis only and requires an explicit request.
8. **Runtime Preflight** — When the host project provides a local planning Runtime, use that host's documented preflight to validate schemas, versions, selected-direction lineage, hashes, artifact paths, revision count, and the Anime Style Constitution reference. This Skill package does not assume that benchmark-only `src/`, `schemas/`, `config/`, or `outputs/` paths exist inside the Skill repository. Interactive state names are `IDEA_RECEIVED → CHARACTER_EXPLORED → AWAITING_CHARACTER_SELECTION → CHARACTER_SELECTED → CHARACTER_PLANNED → ART_EXPLORED → AWAITING_ART_SELECTION → ART_SELECTED → FINAL_DESIGNED → GENERATION_READY → GENERATED → STYLE_CHECKED → ACCEPTED`. `ACCEPTED` means technical completion, not human aesthetic approval.

9. **After generation** — Keep S1 Anime 2D Hard Gate as the only current visual hard gate. Present the image and brief artifact summary, then stop. Do not automatically score, redesign, regenerate, or optimize; the human decides what to change.

## Optional auto mode

Use `auto` only when the user explicitly asks “你帮我选”, “直接选一个”, “自动继续”, “全自动”, or “直接做完”. It preserves the existing automatic PlanningPipeline path for benchmark and automation. `genericness`, `npc_risk`, `overdesign_risk`, `supernatural_inflation`, `literal_translation_risk`, `safe_selection`, `commercial_viability_score`, and `featured_playable_score` may be recorded as later analysis, but never filter directions in interactive Explore.

The future CREATE continuation is intentionally out of scope: only after a later approved Final Character Design stage may the existing `CharacterDesignSpec`, `PromptCompiler`, and `$imagegen` flow run.

If the user explicitly requests multiple designs first, keep them as direction summaries until selection. Do not create multiple `CharacterDesignSpec` objects or images automatically. S2 Commercial Gacha Profile expands vocabulary only; it is not a runtime hard gate. S1 Anime 2D Hard Gate remains the sole current visual hard gate.

## Runtime boundary

The Skill owns intent interpretation, possibility expansion, human selection/mix interpretation, Character Planning, Art Planning, optional review, and artifact naming. Python Runtime owns planning schema validation, versions, hashes, lineage, state transitions, artifact paths, revision limits, and Anime Style Constitution reference checks. The existing automatic path still allows at most one Art Planning revision and ends at `PLANNING_READY`; interactive exploration may restart only when the human asks for another set. `anime-character-imagegen` remains the later image execution seam; it is not used before both interactive selections.

## Front-facing pose dry-run — current temporal hunter

Text-only pose guidance for the current test character: a full-body adult woman stands directly front-facing with face, chest, pelvis, both hips, both thighs, and both legs readable on one stable frontal axis. One leg is slightly forward and the weight shifts only mildly. One arm extends outward with the compact phase blade while the other hand is raised in an asymmetric attack gesture. Her head may tilt a few degrees toward the deleted-future space, but the torso does not turn. Dark hair, fitted garment edges, sheer black stocking transitions, and at most three faint incomplete future echoes create the motion around her; no torso twist, look-back pose, or chest/pelvis counter-rotation.

## References

- [character-design-guide.md](references/character-design-guide.md) — concise design rules; read during Stage 2–3.
- [workflow.md](references/workflow.md) — CREATE state flow and failure paths; read when executing or troubleshooting.
- [basic.md](examples/basic.md) and [advanced.md](examples/advanced.md) — dry-run examples only; neither calls `$imagegen`.
