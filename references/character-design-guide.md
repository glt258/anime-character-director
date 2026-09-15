# Character Design Guide — Player Appeal First

1. Make the player want the character.
2. Identity before generic beauty.
3. Attraction can be sensual, cool, cute, dangerous, elegant, dominant, mysterious, protective, or another explicit fantasy.
4. Common gacha appeal language is allowed; the failure is repeating it without identity.
5. Never confuse modesty with originality.
6. Never confuse realism or practicality with good design.
7. Profession serves fantasy.
8. Functional logic supports design; it does not lead it.
9. Every major visual choice should strengthen desire, identity, or emotional fantasy.
10. If the character feels like an NPC, redesign before generation.

## Regional visual grammar

Use the three-layer style architecture: `Global Rendering Style` controls the rendering medium, `Regional Visual Language` controls the commercial illustration grammar, and `Character Visual Style` controls the character's own design language. The default regional language is `EAST_ASIAN_CONTEMPORARY_GACHA`; it favors anime-first facial abstraction, stylized coherent anatomy, premium material separation, and finished playable-character presentation.

Regional style is not ethnicity or costume culture. Build outfit families from character-specific appeal before world integration; detect robe/sash/trim/boot recipes as generic RPG drift only when they lack a reason. Preserve mature and strong archetypes through anime abstraction, and use `StrongFemaleRegionalStyleReview` / `MaleRegionalBodyReview` for actual-image evidence rather than hard-coded body stereotypes.

Regional visual language is not ethnicity or costume. Keep dark/tan skin, fantasy ethnicity, contemporary, sci-fi, desert, aquatic, gothic, western-looking fictional worlds, and beast traits available. Do not silently add hanfu, kimono, qipao, sashes, tassels, robe coats, or gold-trim fantasy RPG clothing merely because the default regional language is East Asian.

For mature men, preserve maturity while staying anime-first; do not use western superhero anatomy as a shortcut. For strong women, preserve strength through shoulder/back/core/thigh structure, posture, stance, and outfit tension without defaulting to a bodybuilder, amazon, or western comic heroine. A regional critic must judge the actual image, not the presence of style words in the prompt.

## Lower-body design

Treat legs, feet, legwear, accessories, and footwear as identity-bearing design areas. Coverage, stockings/tights, bare legs, barefoot construction, open footwear, heels, flats, sneakers, boots, and asymmetry are all valid adult options; none is the automatic answer. Male characters receive the same range and must not be reduced to trousers plus boots. Fanservice and coverage are separate variables.

Use a lower-body reason: how the choice supports silhouette, character style, movement, pose, sensuality, elegance, fantasy, or identity. If the actual image changes selected barefoot to boots, selected tights to bare legs, or removes a selected leg accessory, record the corresponding grounding failure instead of silently accepting the substitution. Clearly juvenile characters remain age-appropriate and do not receive erotic leg emphasis or fetishized accessories.

## Player Desire Check

Before Runtime validation, answer:

- Why would a player pull this character?
- What fantasy does she/he sell?
- What is attractive about the face?
- What is attractive about the silhouette and body framing?
- What is attractive about the costume besides its plausibility?
- What visual tension keeps the design emotionally alive?
- What personality fantasy or emotional hook creates a relationship with the player?

## Hard leg-separation invariant

All normal two-legged humanoids use the global `LegSeparationContract`: thighs, knees, calves, ankles, and feet stay separately readable; neither leg crosses the body centerline or occludes the other as a crossing silhouette. `elegant`, `sensual`, `feminine`, `model-like`, and fanservice language cannot override this. Preserve pose diversity with open parallel, narrow separated, asymmetric weight, offset non-overlapping, wide active, low-energy separated, or forward-step non-crossing families. Crossed, scissored, ankle-cross, leg-over-leg, and fashion-model-crossed families are forbidden.
- Does the design feel like a featured playable character?
- Does it risk feeling like an NPC, engineer, background worker, or concept-sheet character?

If these answers are vague, redesign the spec before Runtime validation.

## Design structure

- `character_concept` includes `commercial_fantasy` and `visualized_narrative_hook`.
- `face_identity` answers “this is her”; `player_appeal.face_appeal` answers “why the player enjoys looking at her.”
- `outfit_design` leads with `base_layer`, `silhouette_layer`, `appeal_layer`, `identity_layer`, then functional logic. It must answer both why the player enjoys seeing the outfit and why it belongs specifically to the character.
- `visual_anchors` includes `anchor_appeal_role`; a memorable anchor must also be desirable in stillness or motion.
- `player_appeal.exposure_strategy` may be `none`, `minimal`, `controlled`, `moderate`, or `bold`, but exposure is never a substitute for identity. Adult sensuality stays inside anime abstraction; underage characters receive no adult sensual or body-emphasis strategy.

## Generic template rule

Do not penalize `crop top`, short bottoms, stockings, thigh straps, exposed waist, fitted clothing, high boots, asymmetric exposure, or oversized outerwear in isolation. Evaluate the combination, its character-specific context, and repetition across designs. A common element is acceptable when it improves desire, serves the fantasy, strengthens silhouette, reinforces an anchor, or creates personality tension.

