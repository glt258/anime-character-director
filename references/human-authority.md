# Human Authority Layer

## Contract

AI may create, expand, compare, critique, rank, recommend, revise, regenerate, and propose alternatives. AI may not permanently discard meaningful candidates, hide meaningful history, silently replace a Human-approved design, promote a revision into Canon, turn an aesthetic preference into objective truth, or convert an AI recommendation into a Human decision.

AI judgment is useful; AI authority is limited. AI may recommend. Human selection is authoritative.

## Technical review versus aesthetic review

Technical Review covers observable integrity: S1 Anime 2D Hard Gate failure, malformed or corrupt files, invalid schemas or required artifacts, Canon integrity corruption, extra/missing/fused visible fingers, duplicated hands, extra limbs, broken wrists, malformed body connections, severe foot defects, and weapon-through-palm. Technical QA may fail, repair, regenerate, or stop delivery. The original remains in history/lineage even when blocked.

Aesthetic Review covers pagegame association, genericness, sexiness preference, motif preference, detail density, hairstyle preference, color preference, player appeal, commercial gacha feeling, pullability, and unusualness. AI may report, compare, warn, rank, and recommend. It may not automatically delete, reject, or replace a version for those reasons.

```text
AI ANALYSIS → AI RECOMMENDATION → HUMAN OPTIONS → HUMAN DECISION
```

Example:

```text
AI RECOMMENDATION
Prefer Version B for stronger thumbnail readability.

HUMAN OPTIONS
A — Original
B — Revision
A+B — Mix
Keep both
Generate more
```

## Version lineage

Every meaningful creative branch keeps a small `version record` with `version_id`, `parent_version` (and, for a mix, all `parent_versions`), `creation_type`, `artifact_paths`, `reason`, optional `ai_review`, and `human_status`. Use `creative_session.json` for the session-level mode, source, branch list, AI recommendation, and Human decision; store individual records under `versions/`.

Supported creation types are `original`, `ai_revision`, `human_revision`, `human_mix`, `variant`, `same_character_asset`, `canon_candidate`, `canon_approved`, and `technical_repair`. Supported Human statuses are `pending`, `approved`, `rejected`, `superseded`, and `archived`. `rejected` means Human did not choose the version; it never means delete its artifact.

Revisions branch; they do not overwrite Original. Revision does not overwrite Original. A Technical Repair is a special child with `technical_parent` and `creative_identity_preserved: true`; it may fix anatomy only and must preserve the creative identity. A repair is not a new creative redesign.

## Human decisions and Canon

Use the shared decisions `APPROVE`, `REJECT`, `REVISE`, `MIX`, `KEEP_BOTH`, `CONTEXT_ONLY`, and `REQUEST_MORE`. Canon decisions additionally use `APPROVE_AS_CANON` and `APPROVE_AS_CANON_UPDATE`.

New permanent hair, costume, weapon, accessory, palette, anchor, or rear-surface information is only a `PROPOSED CANON ADDITION` until Human approval. `CONTEXT_ONLY` can approve a motif for named contexts such as `ultimate_art` without adding it to the standard Character Canon.

Familiar is not automatically bad. Unusual is not automatically good. Common motifs remain available unless Human explicitly rejects them; unusual motifs remain subject to readability and coherence analysis, not automatic priority.

## P6 carry-forward lesson

Different presentation contexts can introduce clocks, fractured structures, stronger echoes, or other new visual language. Record those as proposed, optional, or context-only motifs. Do not automatically approve them, and do not automatically ban them.
