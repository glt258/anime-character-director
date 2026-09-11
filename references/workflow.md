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
Final Design handoff (front-facing full-body character standee) → existing Runtime → PromptCompiler → $imagegen
    ↓
S1 Anime 2D Hard Gate
    ↓
Present image and stop for human review

`auto` mode retains the previous automatic pipeline for explicit automation/benchmark requests only.
```

Failure rules:

- A schema or style-invariant failure stops before prompt compilation and image generation.
- Interactive exploration does not reject directions for genericness, NPC risk, overdesign, supernatural intensity, or commercial viability. Those may be shown as analysis after selection, never as creative filters.
- Human selection is required at both checkpoints; Codex must not silently select, redesign, or converge the work.
- Standard character standees use a stable frontal body axis with face, chest, pelvis, hips, and legs primarily facing the viewer. Motion comes from secondary elements; the front costume remains readable.
- Contemporary gacha guidance is structural, not a second gate: establish head identity, 3–5 macro shapes, costume architecture, negative space, controlled color blocking, detail islands, one primary anchor, and a limited material hierarchy before micro ornament. Preserve Human-selected adult sensuality without relying on browser-game/MMORPG luxury stacking.
- For temporal concepts, prefer structural contour displacement, frame offsets, impossible overlaps, and one or two partial echoes over decorative shards, glowing crystals, torn capes, or rows of transparent clones.
- A PromptBundle integrity or anti-realism failure stops before `$imagegen`.
- ImageGen output is not accepted until the S1 Anime 2D Hard Gate passes; S2 Commercial Gacha Profile is not a hard gate.
- Multiple proposed designs are text-only until the user selects or mixes them.
