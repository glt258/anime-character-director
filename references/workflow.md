# CREATE Workflow (default: interactive)

```text
User Request
    ↓
Character Explore: 5 directions
    ↓
AWAITING_CHARACTER_SELECTION
    ↓
Human selects / mixes
    ↓
CharacterPlanningBrief
    ↓
Art Explore: 4 directions
    ↓
AWAITING_ART_SELECTION
    ↓
Human selects / mixes
    ↓
Final Visual Direction (front-facing full-body character standee)
    ↓
Identity Pass → identity/identity_summary.json (Character Canon)
    ↓
CharacterDesignSpec → existing Runtime → PromptCompiler → $imagegen
    ↓
S1 Anime 2D Hard Gate
    ↓
Anatomy Integrity Check → generation/anatomy_report.json
    ↓
PASS → Human Review
FAIL → Technical Repair / Regeneration → Re-check S1 → Re-check Anatomy
UNCERTAIN → Hold and explicitly report the uncertain region to Human

`auto` mode retains the previous automatic pipeline for explicit automation/benchmark requests only.
```

The formal Canon is created only after a Human-approved master image and explicit freeze confirmation:

```text
Image generated
    ↓
Human: APPROVED + “freeze as Character Canon v1”
    ↓
character_canon/v1/character_canon.json
    +
master_character.png
```

Same-character consistency for later variants uses the saved Character Canon:

```text
identity/identity_summary.json
    ↓
Avatar / half-body / expression / combat / side / back request
    ↓
Character Canon + approved master reference + new presentation request
    ↓
Preserve must_preserve; vary only may_vary
    ↓
Human visual review against the Canon
    ↓
Accept the variant or mark drift and return to the identity handoff
```

The consistency review is a creative comparison, not a new hard gate or automated validator. A variant may change framing, pose, expression, visible garment surfaces, and restrained effects, but it must retain the locked head and face read, body proportions, costume construction, color placement, and primary anchor.

Every Same Character rendering uses the same post-generation path. Master Reference and Canon do not bypass Anatomy Integrity Check. A portrait with only head/shoulders is inspected only for the visible anatomy; a combat pose receives the highest-risk hand, wrist, weapon-grip, limb-count, and foot review.

Failure rules:

- A schema or style-invariant failure stops before prompt compilation and image generation.
- Interactive exploration does not reject directions for genericness, NPC risk, overdesign, supernatural intensity, or commercial viability. Those may be shown as analysis after selection, never as creative filters.
- Human selection is required at both checkpoints; Codex must not silently select, redesign, or converge the work.
- Standard character standees use a stable frontal body axis with face, chest, pelvis, hips, and legs primarily facing the viewer. Motion comes from secondary elements; the front costume remains readable.
- Contemporary gacha guidance is structural, not a second gate: establish head identity, 3–5 macro shapes, costume architecture, negative space, controlled color blocking, detail islands, one primary anchor, and a limited material hierarchy before micro ornament. Preserve Human-selected adult sensuality without relying on browser-game/MMORPG luxury stacking.
- Identity Pass is a post-selection clarification: it strengthens the selected direction's head, face, silhouette, costume, and one primary anchor without reopening Art Explore or silently selecting a replacement.
- `identity/identity_summary.json` is a lightweight descriptive artifact. Use `must_preserve`, `may_vary`, and `must_not_drift_into` as the practical Character Canon for future views and poses; do not build a separate schema or validator system for it.
- Formal Character Canon is not frozen before Human approval. Same Character Mode must not rerun Explore or silently redesign the approved character.
- Anatomy Integrity Check is a technical generation QA step after S1, not an aesthetic or commercial Gate. Only anatomy `PASS` proceeds as a technically complete result; `FAIL` is `ANATOMY_REJECTED`, and `UNCERTAIN` remains explicitly held for review.
- For temporal concepts, prefer structural contour displacement, frame offsets, impossible overlaps, and one or two partial echoes over decorative shards, glowing crystals, torn capes, or rows of transparent clones.
- A PromptBundle integrity or anti-realism failure stops before `$imagegen`.
- ImageGen output is not accepted until the S1 Anime 2D Hard Gate passes; S2 Commercial Gacha Profile is not a hard gate.
- Multiple proposed designs are text-only until the user selects or mixes them.
