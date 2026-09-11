# P7 — Multi-Mode Creative Skill Architecture Report

## Result

`anime-character-director` remains one Codex Skill with one Human Authority Layer and six Human-facing creative modes. `auto` remains an internal benchmark/automation path. No image was generated and no external API was called in P7.

## Required answers

1. Human-facing creative modes: **6**.
2. Modes: **quick**, **directed**, **explore**, **variants**, **same-character**, **critique**.
3. Default mode: **explore**.
4. Does Quick execute Character Explore? **NO**.
5. Can AI recommend a version? **YES**.
6. Can AI delete another version for aesthetic reasons? **NO**.
7. Does Revision overwrite Original? **NO**.
8. Can Human choose an AI-unrecommended version? **YES**.
9. Is `KEEP_BOTH` supported? **YES**.
10. Is `MIX` supported? **YES**.
11. Is `CONTEXT_ONLY` motif approval supported? **YES**.
12. Can Technical QA block delivery? **YES**.
13. Does Aesthetic Review have final veto authority? **NO**.
14. Is Character Canon still Human-approved? **YES**.
15. Does Same Character still use Canon + Master? **YES**.
16. Is version lineage retained? **YES**.
17. Are familiar motifs automatically forbidden? **NO**.
18. Are unusual motifs automatically preferred? **NO**.
19. Did P7 generate images? **NO**.
20. Tests: see the targeted test result below.

## Human Authority contract

AI may create, expand, compare, critique, rank, recommend, revise, regenerate, and propose alternatives. AI may not delete meaningful creative history, hide branches, silently replace approved work, promote revisions into Canon, or turn a recommendation into a Human decision. Technical integrity may block delivery; aesthetic disagreement may only be analyzed or recommended.

Every meaningful branch is represented by a lightweight version record. `creative_session.json` records mode, source, branches, AI recommendation, and Human decision. Individual records preserve parent lineage, artifact paths, creation type, reason, and Human status. Technical repairs remain children of the technical parent and declare creative identity preservation.

## Six-mode text dry-run

Input: “设计一个成年女性角色，与‘梦境被别人偷走’有关。”

### Quick

Minimal brief: adult anime woman, dream-theft premise, one necessary visual hook, and a readable first-pass pose. Codex fills only unspecified details, generates one first pass, runs S1 → Anatomy QA, then presents the result for Human Review. No Character Explore or Art Explore.

### Directed

Codex creates one complete AI Recommended Design: a woman whose stolen dreams manifest as missing future memories and a power that temporarily borrows another person’s sleep. Codex explains the design thesis, identity, silhouette, costume, and gameplay fantasy, then offers APPROVE / REVISE / REQUEST VARIANTS / SWITCH TO EXPLORE. Human approval is still pending.

### Explore

Codex produces five genuinely different Character Directions, for example: the dream’s former owner, a woman who hunts stolen dreams, a relationship-centered dream exchange, a world-scale dream archive anomaly, and a wildcard who is secretly made from discarded dreams. Codex stops at `AWAITING_CHARACTER_SELECTION`; Human may select, mix, request wilder options, or restart.

### Variants

Assume Human selected a dream-hunter direction and asks for three hair candidates. Codex keeps the source and creates: A compact asymmetric silhouette, B long split “stolen frame” layers, and C tied high-back negative-space shape. Codex compares portrait readability and concept strength, may recommend B, and shows A/B/C plus MIX and KEEP_BOTH. No candidate is deleted.

### Same Character

Assume a Human-approved Canon + Master already exists and the request is “用她画一张梦境战斗图”. Codex uses Canon + Master + the new presentation request. It does not rerun Explore, Planning, or Identity Pass. After generation it runs S1 → Anatomy QA → Identity Drift Review, reports any new dream motif as optional or `PROPOSED CANON ADDITION`, and waits for Human Review.

### Critique

Given Original A, Codex reports possible issues without treating taste as fact, then branches: Revision B strengthens head identity; Revision C simplifies costume architecture. A, B, and C remain visible with lineage. Codex may recommend C, but Human Options are A / B / C / A+B mix / KEEP_BOTH / REQUEST_MORE. Original is never overwritten.

## Shared pipeline

```text
Mode-specific creative workflow
        ↓
Human Authority Layer
        ↓
Generation → S1 Anime 2D Hard Gate → Anatomy Integrity Check
        ↓
Human Review (Same Character also runs Identity Drift Review)
```

S1 remains the only visual-style hard Gate. Anatomy is technical integrity. Aesthetic Review is advisory. Familiar and unusual motifs remain available for Human judgment unless explicitly rejected.

## Files

- `src/anime_art_director/planning/modes.py` — explicit modes, Human decisions, and intent routing.
- `src/anime_art_director/planning/lineage.py` — lightweight creative session/version lineage and Human decisions.
- `skills/anime-character-director/references/creative-modes.md` — mode workflows and routing examples.
- `skills/anime-character-director/references/human-authority.md` — authority contract, review boundary, and lineage rules.
- `skills/anime-character-director/references/workflow.md` — shared workflow and output labels.

## Test result

Targeted P7 routing, lineage, existing planning, style, identity, and anatomy tests: **94 passed in 1.26s**.

Final status: **P7 COMPLETE — NO IMAGE GENERATION**
