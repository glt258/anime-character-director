# Identity Pass and Same-Character Consistency

This document defines the smallest useful identity lock around the existing CREATE workflow. It does not add an Agent, hard Gate, complex validator, model training step, or external service.

## Identity Pass

The pass runs after Human Art Selection and the approved Final Visual Direction, before `CharacterDesignSpec`:

```text
Human Art Selection
    ↓
Final Visual Direction
    ↓
Identity Pass
    ↓
CharacterDesignSpec
    ↓
PromptCompiler
    ↓
$imagegen
```

It does not rerun Character Explore, Character Planning, Art Explore, Human Art Selection, or Identity Explore. It only strengthens the selected direction's identity.

Record six short decisions:

1. **Head:** head silhouette, bang structure, left/right side hair masses, back hair mass, face/hair negative space, signature asymmetry, and one head-level anchor.
2. **Face:** keep 2D anime abstraction while defining eye geometry, brow relationship, eye-spacing impression, face contour, mouth attitude, and default emotional read.
3. **Silhouette:** describe what remains in a pure black silhouette: head, shoulders, torso, waist rhythm, hips, legs, outer asymmetry, and the primary anchor.
4. **Costume:** define torso architecture, bust/chest framing, waist transition, hip framing, leg system, stocking integration, outer asymmetry, and closure/fastening logic.
5. **Primary anchor:** exactly one main anchor, with no more than one or two supporting motifs; it must survive pose/crop changes and simplified rendering.
6. **Without effects:** if glow, particles, ghosts, shards, and background effects vanish, strengthen head, silhouette, costume, body framing, or anchor instead of adding effects.

Small facial marks, eye colors, jewelry, tattoos, and VFX can support identity, but none may be the sole identity mechanism. This is creative review, not an automatic score or hard Gate.

## Identity Summary artifact

Write `identity/identity_summary.json` during the Identity Pass. Keep it descriptive and human-readable; it is not a new complex schema or validator.

```json
{
  "character_id": "",
  "identity_version": "1.0",
  "head_identity": {},
  "face_identity": {},
  "silhouette_identity": {},
  "costume_identity": {},
  "primary_iconic_anchor": "",
  "supporting_motifs": [],
  "must_preserve": [],
  "may_vary": [],
  "must_not_drift_into": []
}
```

`must_preserve` is the consistency core. It records the face/head read, body proportions, costume construction, key color/material placement, and primary anchor that future renderings must retain. `may_vary` records deliberate presentation changes. `must_not_drift_into` records recognizable failure modes.

## Character Canon

Do not establish a formal Canon before Human approval. After a Human explicitly approves a master image and confirms “freeze this as Character Canon v1,” create a simple lineage-preserving directory:

```text
character_canon/
  v1/
    character_canon.json
    master_character.png
```

The Canon is the source of truth for later renderings. Its minimum structure is:

```json
{
  "character_id": "",
  "character_name": "",
  "canon_version": "v1",
  "approval_status": "APPROVED",
  "identity": {
    "age_category": "adult",
    "gender_presentation": "woman",
    "overall_visual_fantasy": ""
  },
  "face": {},
  "hair": {},
  "body": {},
  "costume": {},
  "color_architecture": {},
  "material_hierarchy": {},
  "primary_iconic_anchor": "",
  "supporting_motifs": [],
  "fantasy_integration": {},
  "must_preserve": [],
  "may_vary": [],
  "must_not_invent": [],
  "master_reference": "references/master_character.png",
  "lineage": {"previous_canon": null}
}
```

The Canon must record identity, face, hair, confirmed body proportions, costume construction, color names and placement logic, material hierarchy and placement, primary anchor, supporting motifs, and how the fantasy enters hair, body, silhouette, costume, or negative space. `must_not_invent` prevents the model from silently adding permanent hair, costume, weapon, accessory, palette, or anchor changes.

Use simple versions only: `v1`, `v1.1`, `v2`. A later Human-approved redesign creates a new directory and preserves the old Canon and master reference lineage. A version change is never inferred from an image.

## Master Reference and Same Character Mode

Once approved, a Same Character request uses:

```text
Character Canon
    +
Approved Master Reference
    +
New Presentation Request
    ↓
Consistency-aware Visual Brief
    ↓
$imagegen
    ↓
Human Review
```

Requests for an avatar, half-body, new expression, combat pose, side/back view, setting sheet, promotional image, or skill showcase are Same Character Rendering, not New Character Creation. Do not rerun Explore or Identity Pass unless Human explicitly asks to redesign the character.

Default consistency priority is:

1. face identity
2. hair identity
3. primary iconic anchor
4. costume architecture
5. body proportions
6. color placement
7. material placement
8. stocking/footwear identity
9. new pose
10. new composition
11. temporary VFX

New pose adapts to the character; the character does not redesign itself to fit the pose.

### Immutable by default

Face identity, hairstyle architecture and color, body type and confirmed bust proportion, torso costume architecture, stocking design, primary anchor, key color placement, and key material placement.

### Flexible

Pose, expression, hand gesture, hair/cloth motion, camera crop, VFX intensity, and temporary combat effects.

### Human approval required

Haircut, hair color, body type, bust size, major costume redesign, stocking redesign, weapon redesign, primary anchor replacement, palette replacement, and any new permanent accessory.

## First consistency benchmark: future-self hunter

Use the current Human-approved front-facing master. Plan, but do not generate, these five checks:

- **Portrait:** head + shoulders; test face identity, hair identity, and head silhouette.
- **Half body:** waist-up with a different hand gesture; test face, hair, torso architecture, bust framing, primary anchor, and color placement.
- **Expression sheet:** neutral, smirk, angry, and briefly vulnerable; expression changes while the face remains the same.
- **Combat pose:** allow weight transfer, attack action, ability use, changed arms, and VFX while preserving face, hair, body, costume, stockings, anchor, and color placement.
- **Side/back reference:** complete rear hair, back costume, side silhouette, stockings, footwear, and outer structure without inventing large permanent design elements; those require Human Review.

## Human review and drift report

Human review may inspect a head crop, 128×128 thumbnail, black silhouette, and no-VFX version. Ask “Do I recognize her?” and “Does the structure survive?” Do not auto-score or auto-reject.

After a Same Character rendering, Codex may report face, hair, body, costume, color, material, or anchor drift. The default result is `REPORT`; Human chooses `APPROVE`, `REVISE`, or `REJECT`. Do not auto-redraw, auto-regenerate, or silently modify the approved Canon.

The current phase tests Skill + Character Canon + Master Reference only. It does not train LoRA, DreamBooth, embeddings, fine-tuning, classifiers, similarity thresholds, or external consistency APIs.
