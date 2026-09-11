# P4 Identity and Consistency Report

## Scope

This phase modifies the existing Skill/workflow and documents a lightweight Canon structure. It does not add an Agent, hard Gate, complex validator, model training, or external API.

1. **Identity Pass position:** Human Art Selection → Final Visual Direction → Identity Pass → CharacterDesignSpec → PromptCompiler → `$imagegen`.
2. **Does Identity Pass redo Character Explore?** NO.
3. **Does Identity Pass redo Art Explore?** NO.
4. **When is Character Canon established?** After a Human explicitly approves the master image and confirms that it should be frozen as Canon v1.
5. **Is the master image a reference?** YES. Same Character Mode uses Character Canon + approved master reference + the new presentation request.
6. **Does Same Character Mode redesign the character?** NO. It renders a new presentation of the approved character.
7. **Default immutable:** face identity, hairstyle architecture/color, confirmed body type and bust proportion, torso costume architecture, stocking design, primary anchor, key color placement, and key material placement.
8. **Default flexible:** pose, expression, hand gesture, hair/cloth motion, crop, VFX intensity, and temporary combat effects.
9. **Human approval required:** haircut, hair color, body type, bust size, major costume or stocking redesign, weapon redesign, anchor replacement, palette replacement, and new permanent accessories.
10. **Canon versioning:** YES — simple `v1`, `v1.1`, `v2` directories with preserved lineage.
11. **New hard Identity Gate:** NO. Identity and drift checks are Human Review.
12. **LoRA training:** NO.
13. **Image generated in this phase:** NO.
14. **External API or `$imagegen` called:** NO.

## Future-self hunter Identity Dry-Run

The existing Human-approved front-facing master remains the source. The Identity Pass records:

- **Head:** compact asymmetric smoke ink-blue-black head wedge, diagonal bang, close left side mass, longer right back mass, clear face/hair gap, and one phase-shifted strand group.
- **Face:** mature tapered anime oval, sharp medium almond eyes, close deliberate brows, balanced spacing, small firm chin, and restrained one-sided mouth lift; default read is calmly impatient.
- **Silhouette:** adult hourglass, frontal bust shell, narrow waist, clear hips, long twin-leg columns, asymmetric shoulder-to-thigh outer structure, waist opening, and repeated contour fracture.
- **Costume:** one frontal torso shell, clean bust-to-waist transition, integrated hip framing, intentional stocking/leg system, one asymmetric outer panel, and closure logic following the shell/fracture.
- **Primary anchor:** one structural temporal fracture repeated through diagonal bang, torso edge, waist opening, and stocking boundary.
- **Supporting motifs:** compact asymmetric head silhouette; frontal bust-waist-hip rhythm with clean stocking boundary.
- **Without VFX:** identity remains in the head wedge, face read, body rhythm, costume shell, waist gap, stocking boundary, and structural fracture; effects are not the identity source.
- **Must preserve:** face/head read, adult proportions, torso shell and waist opening, asymmetric outer structure, controlled smoke ink-blue-black color architecture, and the primary fracture.
- **May vary:** crop, expression, gesture, combat action, visible side/back surfaces, and restrained temporal effects.
- **Must not drift into:** generic pretty face, generic long black/white hair, generic sexy bodysuit, random armor/accessories, or VFX-dependent identity.

## First benchmark plan

Plan five Human Review cases without generating images: portrait, waist-up alternate gesture, four-expression sheet (neutral/smirk/angry/briefly vulnerable), dynamic combat pose, and side/back reference. Review head crop, 128×128 thumbnail, black silhouette, and no-VFX versions. The output is a report, not an automatic score or rejection.

## Targeted tests

The benchmark test `tests/test_identity_consistency.py` checks workflow ordering, no re-exploration rules, lightweight artifact fields, approval-before-Canon language, master references, immutable/flexible/approval classes, versioning, Human Review, no-VFX non-gate behavior, and the no-image/no-external-API boundary. The current temporal hunter artifact is parsed as the dry-run fixture.

Result: **24 targeted assertions passed; no image was generated.**
