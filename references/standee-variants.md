# Standee Pose Variants

## Purpose

`standee_pose_variant` is a sub-type inside the existing `variants` mode. It explores how one approved character stands while preserving the same woman, not how to redesign her.

The invariant is simple: face, hair, body, costume, stockings, footwear, palette, and primary identity stay locked; stance, weight, arms, legs, small head attitude, cloth or hair motion, and restrained ability expression may vary. A glove-coverage or legwear change is outside a normal pose variant unless Human explicitly requests that costume dimension.

## Routing and inputs

Route requests such as “给她四个不同的立绘站姿方案” to:

```text
mode: variants
variant_type: standee_pose_variant
```

Start from `Character Canon + approved Master Reference`. Read the character's personality, default emotional read, body language, costume structure, outer asymmetry, footwear, and any weapon relationship before proposing poses. Ask: “这个人平时会怎么站？” rather than “漂亮女性应该怎么站？”.

## Planning phase

The default planning set is exactly four text-only pose directions. Do not generate four images before Human selection. Each direction must be a real structural alternative, not a foot moved a few centimeters or a hand moved slightly.

Across the set, vary several of: weight distribution, leg distance, load-bearing leg, arm state, open or closed body language, alertness, weapon relationship, restrained ability expression, head attitude, and outer-contour direction. Keep every option a readable standard character standee, not a combat illustration.

The following vocabulary is a starting vocabulary, not a fixed template:

- **A — Stable Front:** clear frontal body, natural leg separation, grounded weight, and mild arm asymmetry.
- **B — Open Confidence:** shoulders open, one deliberate hand action, uncrossed legs, and a controlled one-sided weight shift.
- **C — Alert Hunter:** readable frontal axis, one hand near the weapon or ability, slight forward readiness, and a subtly sharper outer contour.
- **D — Relaxed Asymmetry:** looser shoulders, one leg lightly back, natural balance, and a non-combat side of the character.

Choose the four directions from the character, not from this lettering. Do not force extreme S-curves, three-quarter torsos, look-back poses, exaggerated hip twists, giant effects, jumps, lunges, attacks, or cinematic perspective into a standard standee.

Crossed legs, one knee over the other, inward crossed knees, and leg-over-leg poses are forbidden by the global `LegSeparationContract`. Stilettos and black stockings remain allowed creative choices, but they are not defaults. Do not let three or four options collapse into one separated-leg pose family; use open, narrow, offset, asymmetric-weight, active, and forward-step non-crossing alternatives. Novelty is not an automatic quality score.

## Costume asymmetry variants

Keep these inside the existing `variants` mode; do not create a new mode. When Human explicitly asks to explore costume coverage, useful `variant_type` labels include:

- `glove_coverage_variant`: complete gloves, partial finger exposure, mismatched glove structures, or one-hand-only coverage;
- `legwear_asymmetry_variant`: symmetric hosiery, one-leg hosiery, bare-leg contrast, mismatched sock lengths, or different boot heights.

These are optional design branches. Explain how the asymmetry improves identity, silhouette, rhythm, or color balance, while allowing “it simply looks better” as a valid reason. Human selects the result; do not apply it automatically to Canon or to an unrelated pose request. For a standard standee, keep both sides visible enough that the selected glove or legwear difference can be read.

## Required output per direction

```text
variant_id
name
pose_intent
body_axis
weight_distribution
leg_arrangement
arm_arrangement
head_attitude
silhouette_effect
costume_interaction
character_read
risk
```

`character_read` must explain why the pose belongs to this character. `costume_interaction` must explain how hair, skirt or outer structure, waist architecture, weapon, stockings, footwear, glove coverage, legwear asymmetry, or other locked construction participates in the pose. `risk` records likely anatomy, readability, repetition, or identity-drift concerns without automatically deleting the option.

## Human checkpoint

After the four text directions, stop at:

```text
AWAITING_HUMAN_STANDEE_POSE_SELECTION
```

Show `A`, `B`, `C`, `D`, `A+C MIX`, `B+D MIX`, `KEEP_MULTIPLE`, `REQUEST_MORE`, and `REJECT_ALL`. AI may compare and recommend one, but Human decides. Do not generate an image before that decision.

## Generation phase

After Human selection, default to one generated result. Generate multiple images only when Human explicitly asks for a comparison. A Human Mix such as “A 的腿 + C 的手 + B 的重心” becomes a branch such as `Human Mix Pose HM-01`; it does not reopen Character Explore or redesign the character.

Run the existing post-generation sequence:

```text
S1 → Anatomy Integrity Check → Identity Drift Review → Human Review
```

The pose variant is not a combat-art shortcut. If the request asks for a jump, sprint, large attack, ultimate effect, dramatic perspective, or scene composition, route it to an explicitly requested optional presentation extension instead.

## Identity and Canon boundary

Default preservation is:

```text
face, hair, body proportions, bust/waist/hip structure, costume architecture,
stockings, footwear, palette, primary anchor, Character Canon
```

Default variation is:

```text
pose, weight, arms, legs, small head attitude, hair/cloth motion,
and restrained temporary ability expression
```

Pose variants do not update Canon. A Human may identify one as `PROPOSED_CANON_POSE`; it still requires explicit approval. Multiple approved poses are allowed and should be labeled `Primary Standee Pose`, `Alternate Standee Pose 01`, and so on by Human decision.

## Technical and portfolio boundaries

Anatomy QA pays extra attention to hands, wrists, limb connections, knees, ankles, feet, and whether the character can plausibly stand on the visible ground. This remains the existing Anatomy Integrity Check; the separate global `LegSeparationGate` is the hard gate for leg crossing and occlusion.

Recent pose repetition may be reported as an `AESTHETIC_NOTE` or used to suggest alternatives. It cannot hard-reject a familiar pose, override Human preference, hide the Original, or force novelty.
