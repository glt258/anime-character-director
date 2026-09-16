# Standee-First Product Scope

## Product definition

Anime Character Director is a Codex-native, human-in-the-loop Skill for designing original 2D anime / gacha character standees and maintaining character identity across controlled visual variations.

The default product question is: can this become a clear, recognizable, reusable character standee? Identity, head shape, silhouette, costume architecture, body framing, pose identity, Canon, and Same-Character consistency come before cinematic presentation.

## Core assets — Tier 1

The primary product surface is the reusable character asset system:

- Standard Full-Body Standee
- Portrait
- Half Body
- Expression Sheet
- Front Reference
- Side Reference
- Back Reference
- Standee Pose Variant
- Hair Variant
- Costume Variant
- Footwear Variant
- Character Canon Master
- Same-Character Standee

## Optional presentation extensions — Tier 2

These are supported when the user explicitly requests them, but they are not the default product path:

- Promotional Key Art
- Combat Illustration
- Ultimate Art
- Story Illustration
- Event Illustration
- Cinematic Character Art

Do not silently expand a character-design request into a complete game-art asset system. Optional presentation types do not become new Human-facing modes.

## Presentation type

Use the light concept `presentation_type` to distinguish the requested asset without adding a new mode or complex schema:

```text
standard_standee
portrait
half_body
expression_sheet
front_reference
side_reference
back_reference
standee_pose_variant
promotional_key_art
combat_art
ultimate_art
story_illustration
```

The default is `standard_standee`. An explicit user request may select `combat_art`, `ultimate_art`, or another extension. A Human-approved Canon remains authoritative across presentation types.

## Mode scope

- **QUICK:** few-line idea → Standard Character Standee by default, with low-depth automatic resolution;
- **AI_DECIDE:** full Character and Art Explore → AI-selected Standard Character Standee by default;
- **USER_DECIDE:** full Character and Art Explore → Human selection/mix → one consolidated Visual Preference Sheet → Standard Character Standee by default;
- **post-generation actions:** controlled variants, same-character assets, critique, and repair remain actions on an existing design, not top-level creation modes.

## Front-facing rule

Front-facing is the default Standard Standee presentation, not an absolute rule for every image. Slight torso deviation, head turn, asymmetric weight, arm motion, and leg changes are allowed while the character still reads as a standee. Combat, ultimate, promotional, and story extensions may use a different composition only when explicitly requested.

## P8 boundary

P8 Combat Critique was a Human Authority and lineage benchmark. It verified Original preservation, revision branches, Human decisions, and `CONTEXT_ONLY` motif scope. It does not redefine the product as Combat Art generation. In the recorded result, B is an optional ultimate/high-intensity reference, C is an alternate combat revision, and A remains the kept Original.

## Priority

```text
User Explicit Presentation Request
↓
Human-approved Canon
↓
Core Standee Product Scope
↓
Asset Role
↓
AI Recommendation
```
