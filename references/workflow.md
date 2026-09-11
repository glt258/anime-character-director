# Multi-Mode Workflow

`$anime-character-director` is one Skill with six Human-facing creative modes. Route explicit mode first; otherwise infer intent and default to `explore` when ambiguous.

## Mode map

```text
$anime-character-director
  ├── quick
  ├── directed
  ├── explore
  ├── variants
  ├── same-character
  └── critique
        ↓ Human Authority Layer
        ↓ $imagegen
        ↓ Technical QA
        ↓ Human Final Review
```

`auto` remains an internal benchmark/automation path and records `AUTO_RECOMMENDED`, never `HUMAN_APPROVED`.

## Modes

- `quick`: Few-line idea → minimal brief → generation → S1 → Anatomy QA → Human Review. Do not run Character Explore or Art Explore; preserve explicit requirements.
- `directed`: AI designs premise, art direction, and Identity Pass → generation → S1 → Anatomy QA → optional AI Review → Human Review. Label the result AI Recommended Design.
- `explore` (default): 5 Character Directions → Human select/mix → Character Planning → 4 Art Directions → Human select/mix → Identity Pass → generation → S1 → Anatomy QA → Human Review.
- `variants`: Existing version → 3–4 meaningful alternatives for one dimension → AI comparison/recommendation → Human select/mix/keep both/request more → optional generation and QA.
- `same-character`: Character Canon + approved Master + new asset request → generation → S1 → Anatomy QA → Identity Drift Review → Human Review. Do not rerun Explore or redesign without Human instruction.
- `critique`: Original → AI Critique → Revision B/C/D branches → comparison → Human Review. Never overwrite Original.

Variants must differ structurally, not only by shade or ornament. Explore keeps Human Mix as a first-class action. Same Character treats new permanent details as `PROPOSED CANON ADDITION` until explicit approval; `CONTEXT_ONLY` can approve a motif for named contexts.

## Shared technical boundary

Every image-producing mode runs:

```text
Generation → S1 Anime 2D Hard Gate → Anatomy Integrity Check → Human Review
```

Same Character additionally runs Identity Drift Review. Technical failure may block delivery or enter bounded Anatomy Repair while preserving the source in lineage. `UNCERTAIN` remains explicit for Human Review. S1 remains the only visual-style hard Gate; this is not a new hard gate.

## Output labels

Use `AI ANALYSIS`, `AI RECOMMENDATION`, `HUMAN OPTIONS`, and `HUMAN DECISION: pending`. Persist `creative_session.json` plus one version record for every meaningful branch. See [creative-modes.md](creative-modes.md) and [human-authority.md](human-authority.md).
