# Anatomy Integrity QA

Anatomy Integrity Check is mandatory technical generation QA after S1 Anime 2D Hard Gate and before normal Human Review. It is not an aesthetic Gate, commercial Gate, identity Gate, or style Gate. S1 remains the only visual style hard Gate, and this phase does not modify S1.

## Inspect what is visible

Create `generation/anatomy_report.json` or the equivalent runtime `AnatomyIntegrityReport` for every generated character image. Inspect only visible evidence; occlusion, crop, hair, cloth, weapons, gloves, and VFX may produce `UNCERTAIN`. Do not invent hidden fingers or mechanically require five visible fingers when the hand is cropped or naturally closed.

### Hands

Inspect every visible hand independently:

- hand count, thumb existence and plausible placement
- visible finger count, separation, fusion, duplication, length, joints, and bend direction
- palm/back-of-hand orientation
- wrist and hand-to-forearm connection
- weapon/object grip: fingers wrap around the object, thumb is on a plausible side, and the object does not pass through the palm

Open hands, weapon grips, hands near the face, overlapping hands, and gloved hands are high-risk. Gloves hide detail but do not excuse impossible finger structure, thumb placement, joints, or hand volume. A hair strand must not become an extra finger.

### Arms, legs, feet, and whole body

Inspect intended arm and leg count and continuity:

- shoulder → upper arm → elbow → forearm → wrist → hand
- hip → thigh → knee → calf → ankle → foot
- foot silhouette, ankle connection, weight-bearing plausibility, and shoe/foot continuity
- neck/head, shoulders, torso, pelvis, limb count, and duplicated body parts

Blocking examples include an extra or missing limb, duplicated hand, broken wrist, impossible arm connection, severe foot deformation, weapon-through-palm, duplicated primary body part, or obvious extra head/torso structure. If shoes cover the toes, inspect the foot silhouette and ankle rather than inventing toe detail.

## PASS, FAIL, and UNCERTAIN

Use the lightweight report shape:

```json
{
  "status": "PASS",
  "confidence": "HIGH",
  "primary_character": {
    "head": "PASS",
    "torso": "PASS",
    "left_arm": "PASS",
    "right_arm": "PASS",
    "left_hand": "PASS",
    "right_hand": "PASS",
    "left_leg": "PASS",
    "right_leg": "PASS",
    "left_foot": "PASS",
    "right_foot": "PASS"
  },
  "issues": [],
  "repair_required": false
}
```

`PASS` means no clear blocking anatomy defect. `FAIL` is blocking for obvious extra/missing visible fingers, fused fingers, duplicated hands, extra arms/legs, broken wrists, impossible limb connections, severe foot deformation, weapon-through-palm, or duplicated primary anatomy. `UNCERTAIN` is used when the visible evidence cannot reliably decide; it is held for explicit Human Review and is never silently converted to PASS.

## Temporal echoes and Same Character Mode

For the future-self hunter, distinguish the complete `PRIMARY CHARACTER` from an intended partial temporal echo. A displaced hair strand, repeated garment edge, or partial echo hand may be intentional, but it cannot excuse six physical fingers, a third arm attached to the torso, a duplicated primary leg, or a second physical wrist. Temporal presentation may distort the image; it may not excuse malformed primary anatomy.

Same Character Mode does not bypass this check. Portrait, half-body, expression, combat, side, back, setting-sheet, promotional, and skill-showcase renderings are inspected for the anatomy that is actually visible. A head/shoulders expression sheet has no hand check to invent. Combat poses receive heightened attention to both hands, wrists, elbows, weapon grip, limb count, and foot direction.

## Technical Repair

After `FAIL`, repair only fingers, hands, wrists, limb connections, feet, or accidental duplicated anatomy. Preserve Character Canon, face identity, hairstyle, body type, bust proportion, costume architecture, colors, primary anchor, and pose concept. Do not reopen Art Explore or use an anatomy repair as a creative redesign.

Prefer localized repair when the host can reliably edit the affected region. If localized repair is unavailable or fails, regenerate the same approved design using the same Canon, Final Visual Direction, and composition intent. Do not rerun Art Explore. Limit automatic technical repair to a maximum of 2 attempts:

```text
Generation → Anatomy FAIL → Repair 1 → Re-check S1 → Re-check Anatomy
                         → Repair 2 → Re-check S1 → Re-check Anatomy
                         → still FAIL → STOP with failure report for Human Review
```

The runtime states are `GENERATED → STYLE_CHECKED → ANATOMY_CHECKED → ACCEPTED`; a blocking defect becomes `ANATOMY_REJECTED`. An uncertain report remains at `ANATOMY_CHECKED` with an explicit review-required error. `ACCEPTED` is technical completion, not aesthetic approval.

## Prompt guidance

Keep the generation guidance short; post-generation inspection is the primary safeguard:

```text
Anatomically coherent hands and limbs.
Each visible hand has plausible structure with one thumb and four fingers unless naturally occluded by pose or object.
No extra or missing visible fingers, fused fingers, duplicated hands, extra limbs, broken wrists, malformed arm connections, duplicated legs or feet.
Hands interact naturally with weapons and objects.
```

Do not turn the prompt into an anatomy negative-prompt dump. Do not add an anatomy aesthetic score, face classifier, silhouette classifier, similarity threshold, ML model, external vision API, or training step.
