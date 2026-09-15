# Soft Creative Guidance — Pose / Legs / Footwear / Sensuality Diversity

This reference prevents repeated attractive-character templates without turning taste into a runtime rule. These are creative preferences, not hard prohibitions.

## Boundary: hard versus soft

Hard requirements include the S1 Anime 2D category, blocking anatomy failure, an explicit user requirement, and a Human-approved Canon identity. They may block or redirect a workflow.

Soft guidance includes pose diversity, footwear, hosiery, repeated pin-up composition, generic sexy defaults, and portfolio-level convergence. Crossed-leg geometry is excluded from this soft layer and is handled by the global hard `LegSeparationContract` and `LegSeparationGate`. Other soft guidance may influence generation, add an `AESTHETIC_NOTE`, suggest alternatives, or create a Human-requested revision branch.

## Pose diversity

Do not use crossed legs, one knee over the other, inward crossed knees, or any centerline-crossing leg silhouette. The global hard invariant forbids these even when they fit an elegant, sexy, feminine, fashion, or Human-requested pose. Exaggerated hip shift, extreme S-curve, hand-on-hip fashion posing, and twisted pin-up posing remain separate design choices subject to anatomy and style review.

Before choosing a pose, ask what the character does with her body when nobody is asking her to pose. Character-specific body language is the goal, not generic attractive-female posing.

### Crossed legs

Crossed legs are forbidden by the current hard invariant. Do not derive `female + attractive + stockings + heels + sitting` into crossed legs automatically; sitting poses must also keep thighs, knees, calves, ankles, and feet separately readable.

### Seated vocabulary

Use these as optional prompts, not a checklist:

- open relaxed sit: thighs naturally separated, knees at different heights, one leg slightly forward;
- forward lean: elbows or hands near a thigh, suggesting alertness;
- side-weight sit: weight toward one hip while both legs remain readable;
- one-leg extended: one leg extended and one withdrawn for an asymmetric silhouette;
- elevated foot: one foot on a lower step or structure for confidence;
- edge sit: legs naturally drop while hands interact with the seat or environment;
- combat rest: relaxed but ready, with the role still legible.

The pose must still be anatomically plausible. Do not force novelty into an awkward stance.

### Standing vocabulary

For standees, retain the Front-Facing Standee Principle while varying body language: parallel unequal weight, one leg forward, wider grounded stance, asymmetric arm gesture, one heel slightly lifted, relaxed open stance, weapon-supported stance, a foot turned slightly outward, calm frontal stance, or tension-ready stance. Front-facing does not mean rigid; it means the main body and front costume remain readable.

## Footwear diversity

Do not automatically translate an attractive adult woman into stiletto heels. Choose footwear from costume architecture, leg silhouette, body framing, combat logic, personality, faction, movement style, and visual identity.

Possible vocabulary includes stilettos, block heels, wedges, ankle boots, knee boots, thigh-high boots, platforms, combat boots, sleek game-world sneakers, split-toe structures, sandals, strapped footwear, flats, hybrid armored footwear, fantasy structural shoes, asymmetrical footwear, and barefoot or partial-foot structures when conceptually appropriate. This list is a reminder, not a checklist and not a novelty target.

High heels remain fully valid. Familiar footwear is not automatically a problem when it strengthens the character.

## Stockings and hosiery

Black stockings remain valid, including sheer black stockings as an elegant and high-value leg-framing tool. Do not make them the automatic answer for every attractive adult female character. Consider opaque tights, patterned hosiery, an asymmetric stocking system, one-leg hosiery, socks, bare legs, layered leg fabric, colored stockings, or structural legwear when the concept benefits from them.

This guidance does not remove a Human-selected or Canon-frozen hosiery system. The current `future-self hunter` already has Human-approved black sheer stockings, mature voluptuous proportions, and long legs; those remain higher priority than diversity suggestions.

## Local costume asymmetry

Gloves, sleeves, arm accessories, stockings, socks, boots, garters, leg straps, thigh accessories, shoulder structures, and translucent fantasy structures may be designed as controlled left/right differences. The purpose is a stronger identity rhythm, silhouette, or color balance—not random unevenness and not a requirement for every character.

Both symmetric and asymmetric treatment are valid:

- symmetric gloves, sleeves, hosiery, or footwear when the character benefits from order or visual weight;
- different glove structures, partial finger coverage, one-leg hosiery, mismatched sock lengths, or different boot heights when the contrast belongs to the character;
- a single asymmetric treatment supported by otherwise stable costume architecture, rather than asymmetry added to every body part.

Use a simple reason when useful: an uncovered finger may support direct contact with an ability, or one bare leg may lighten the side opposite a heavy temporal structure. A purely visual reason such as a more memorable contour or better color balance is also sufficient. Do not force a lore explanation for an aesthetic choice.

### Partial finger glove coverage

A glove does not have to cover all five fingers. It may expose the thumb, index finger, index and middle fingers, two or three fingers, or use a half-finger, metal finger-cap, or one-hand-only coverage system. This is `Costume Design` when the fingers themselves are present.

Hand review must keep two questions separate:

```text
Hand Anatomy: are the fingers and palm anatomically present and connected?
Glove Coverage: which fingers does the costume cover or expose?
```

If the fingers are present, record `Anatomy: PASS` and a detail such as `Glove Coverage: ASYMMETRIC_PARTIAL_COVERAGE`. A dark glove edge, exposed skin, occlusion, or small rendering gap is not by itself evidence of a missing finger. Only actual missing, extra, fused, broken, or impossibly connected fingers belong to `ANATOMY ISSUE`; uncertainty stays explicit for Human Review.

### Asymmetric legwear

One-leg hosiery, one bare leg, different sock lengths, one stocking paired with a leg guard or strap, and different boot heights are all optional legwear directions. Ask whether both sides remain readable in the intended asset, especially in a standard standee. Do not let a pose hide the very asymmetry being explored.

Asymmetric legwear may be sensual, structural, practical, or purely aesthetic. It does not replace the existing front-facing standee requirement, and it must not be forced when the Human wants fully symmetric legwear. A Canon-frozen system such as the current `future-self hunter` double black sheer stockings remains unchanged unless Human explicitly requests a variant.

## Sexuality is not one template

Sensuality may come from fitted silhouette, exposed back, strong shoulders, waist or thigh framing, confident or soft posture, controlled skin exposure, long leg line, material contrast, facial attitude, elegant movement, dominant or gentle body language, costume tension, or negative space. The combination of large bust, deep cleavage, black stockings, and stilettos remains a valid pattern among many; crossed-leg geometry is excluded by the global hard invariant.

Do not remove an explicit Human preference such as large bust, black stockings, high heels, deep V, or long legs. Crossed legs are the explicit hard-invariant exception: they cannot be selected or preserved as a pose.

## Combination and portfolio diversity

At portfolio level, notice repeated combinations such as black long hair, large bust, black stockings, stilettos, and a long coat. Repetition may trigger an `AESTHETIC_NOTE` and an offer to explore another leg or footwear treatment. It is never a portfolio diversity hard gate; the separate leg-separation gate remains blocking for actual crossing.

Familiar combinations are not automatically bad. Novelty alone does not make a design better. Avoid strange shoes, awkward stances, random asymmetry, incoherent legwear, or uncomfortable poses merely to score as different.

## Asset role

Pose language should follow the asset role:

- **Standard Standee:** readability, silhouette, and front costume take priority;
- **Promotional Key Art:** cinematic perspective and stronger motion are available;
- **Story Illustration:** contextual body language and environmental interaction are available;
- **Combat Art:** stronger action and controlled body rotation are available;
- **Portrait:** face and head identity take priority;
- **Relaxed Asset:** natural body language takes priority over fashion posing.

Do not apply one pose template to every asset role.

## AI review and revision behavior

If a pose falls back into a common `stockings + heels + crossed-leg pin-up` pattern, label the actual crossing `LEG_CROSSING_BLOCKING_FAIL` and reject promotion. Suggest a separated-thigh, one-leg-forward, open, or naturally shifted alternative through the bounded pose-only repair flow.

If a revision is requested, preserve the Original and create a new branch. A crossed-leg Original is a negative fixture under the hard invariant; alternatives must use open, separated seated pose or one-leg-forward-without-crossing. Human reviews the result after the hard gate.

AI may detect repetition, compare poses, recommend footwear, and suggest alternatives. AI may not force novelty, but the global leg-separation invariant must reject crossed-leg geometry and cannot be overridden by the Human.

## Same Character priority

Same Character Mode preserves identity first: `Character Canon + approved Master Reference + new presentation`. Pose diversity may vary the presentation only within the Canon and explicit request. Same Character identity outranks a new diversity suggestion. A Canon-fixed stocking, footwear, hair, body, or costume system is not removed to create variety.

## Current seated case study

The current `future-self hunter` seated asset demonstrates that Character Canon consistency and pose diversity are separate concerns. Its overlapping/crossed-leg arrangement is a negative anatomy fixture under the current invariant, not an approved candidate. Future Same Character work should preserve identity while keeping seated thighs, knees, calves, ankles, and feet independently readable.

## Decision priority

## Standee Pose Variant relationship

When `variants` is explicitly used for `standee_pose_variant`, the diversity reminder becomes a planning aid: propose four genuinely different text-only standee poses, all prevalidated against the hard leg contract, and wait for Human selection before generation. Do not use novelty to justify a broken stance, an extreme torso twist, a combat composition, or a change to the approved character. Read [standee-variants.md](standee-variants.md) for the complete four-pose workflow.

```text
User Explicit Requirement
↓
Human-approved Canon
↓
Asset Role
↓
Character Identity
↓
Soft Pose / Footwear Diversity Guidance
↓
AI Recommendation
```

This guidance does not add a vision model. The runtime now provides a pose validator, positive/negative leg contract, and actual-image `LegSeparationGate`; it intentionally adds no footwear detector, stocking-frequency detector, diversity score, or sexy-template classifier. Costume asymmetry guidance remains non-blocking, while leg crossing is a separate hard gate.

## Formal lower-body variables

When a Final Design makes lower-body choices explicit, use `exposure_strategy`, `legwear_family`, `leg_accessory_family`, `footwear_family`, `foot_visibility`, `visual_reason`, `relationship_to_character_style`, `relationship_to_pose`, and `repetition_risk`. The vocabulary is open-ended and includes deliberate barefoot systems, toe-loop or open footwear, colored or patterned tights, leg rings, straps, and asymmetry. None is a default; none is prohibited for clearly adult characters solely because it is sensual.

`LowerBodyDesignReview` is a design review, not a novelty gate. It keeps fanservice independent from coverage, gives generic pants-plus-boots a genericness note when unmotivated, and protects age-appropriate handling for minors. `check_lower_body_grounding` is the actual-image check: expected barefoot versus boots is `FOOTWEAR_GROUNDING_FAIL`, expected legwear versus bare legs is `LEGWEAR_GROUNDING_FAIL`, and a missing selected leg accessory is `LOWER_BODY_ANCHOR_MISS`.
