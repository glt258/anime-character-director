# Creative Modes

`anime-character-director` remains one Skill with six Human-facing creative modes. The mode is explicit when the user names it and otherwise inferred from intent. If the request is genuinely ambiguous, default to `explore`; ask one short question only when the ambiguity changes the workflow.

| Mode | Use when | Creative workflow | Human checkpoint |
|---|---|---|---|
| `quick` | A few concrete traits and a fast first pass are wanted | Minimal brief → Standard Character Standee by default → generation → S1 → Gacha Style → Anatomy QA → Human Review | Final Human Review |
| `directed` | The user asks Codex to design the complete character | AI design → Standee Art Direction by default → Identity Pass → generation → technical QA → optional AI review | Human chooses the result |
| `explore` | The user wants meaningful alternatives and selection | 5 Character Directions → Human selection/mix → planning → 4 standee-oriented Art Directions → Human selection/mix → Visual Preference Sheet → explicit identity decisions → Human Audit → Identity Pass → Design Review → generation | Two selection checkpoints plus the Visual Preference Gate, then Final Review |
| `variants` | An existing character needs controlled standee alternatives for one dimension | 3–4 controlled standee design alternatives → comparison → Human selection/mix → optional generation; `standee_pose_variant` uses exactly four text-only pose directions before generation | Human chooses, mixes, keeps both, or requests more |
| `same-character` | A Canon character needs a new standee or reference presentation | Canon + approved Master + new standee/reference request → generation → S1 → Gacha Style → Anatomy QA → Identity Drift Review → Human Review | Human reviews consistency; no silent redesign |
| `critique` | A character or standee version needs analysis or revision branches | Original → AI critique → one or more revision branches → comparison; optional presentation assets only when explicitly requested | Human chooses the branch or keeps the original |

Unless the user explicitly requests another `presentation_type`, all six modes are Standee-first. `standard_standee` is the default; `promotional_key_art`, `combat_art`, `ultimate_art`, and `story_illustration` are optional extensions, not additional modes.

## Mode commands and intent routing

The user may invoke `quick`, `directed`, `explore`, `variants`, `same-character`, or `critique` after `$anime-character-director`, or use natural language. Typical routing is:

- “快点直接生成” → `quick`
- “你直接帮我完整设计” → `directed`
- “给我几个方向，我自己挑” → `explore`
- “给这个角色四种发型” → `variants`
- “给她四个不同的立绘站姿方案” → `variants` with `standee_pose_variant`, then stop for Human selection
- “用 Canon 里的她画战斗图” → `same-character`
- “这张哪里不好，帮我改一版” → `critique`

Explicit mode always wins. `auto` is an internal benchmark/automation mode, not a Human-facing creative mode, and its outcome is `AUTO_RECOMMENDED`, never `HUMAN_APPROVED`.

## Shared technical boundary

All image-producing modes share:

```text
Visual Preference Gate → Final Design → Design Review → Generation → S1 Anime 2D Hard Gate → Gacha Rendering Style Gate (Global + Regional) → Anatomy Integrity Check → Human Review
```

Same Character additionally runs Identity Drift Review. Technical failures may block delivery or enter a bounded repair loop. Aesthetic concerns remain analysis and recommendation; they are not a second hard Gate.

`quick` is low-friction, not permission to ignore explicit user requirements. `directed` grants Codex design freedom, but its result is still an AI Recommended Design. `explore` remains the default high-control workflow and keeps Human Mix as a first-class action. `variants` and `critique` always retain the source and every meaningful branch.

For `standee_pose_variant`, read [standee-variants.md](standee-variants.md). It is a sub-type of `variants`, not a new mode: use Character Canon plus the approved Master Reference, output four text-only directions, wait at `AWAITING_HUMAN_STANDEE_POSE_SELECTION`, and generate only the Human-selected result by default.
