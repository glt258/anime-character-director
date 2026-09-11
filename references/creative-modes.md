# Creative Modes

`anime-character-director` remains one Skill with six Human-facing creative modes. The mode is explicit when the user names it and otherwise inferred from intent. If the request is genuinely ambiguous, default to `explore`; ask one short question only when the ambiguity changes the workflow.

| Mode | Use when | Creative workflow | Human checkpoint |
|---|---|---|---|
| `quick` | A few concrete traits and a fast first pass are wanted | Minimal brief → generation → S1 → Anatomy QA → Human Review | Final Human Review |
| `directed` | The user asks Codex to design the complete character | AI design → AI art direction → Identity Pass → generation → technical QA → optional AI review | Human chooses the result |
| `explore` | The user wants meaningful alternatives and selection | 5 Character Directions → Human selection/mix → planning → 4 Art Directions → Human selection/mix → Identity Pass → generation | Two selection checkpoints, then Final Review |
| `variants` | An existing character needs controlled alternatives for one dimension | 3–4 meaningful alternatives → comparison → Human selection/mix → optional generation | Human chooses, mixes, keeps both, or requests more |
| `same-character` | A Canon character needs a new presentation | Canon + approved Master + new asset request → generation → S1 → Anatomy QA → Identity Drift Review → Human Review | Human reviews consistency; no silent redesign |
| `critique` | An existing version needs analysis or revision branches | Original → AI critique → one or more revision branches → comparison | Human chooses the branch or keeps the original |

## Mode commands and intent routing

The user may invoke `quick`, `directed`, `explore`, `variants`, `same-character`, or `critique` after `$anime-character-director`, or use natural language. Typical routing is:

- “快点直接生成” → `quick`
- “你直接帮我完整设计” → `directed`
- “给我几个方向，我自己挑” → `explore`
- “给这个角色四种发型” → `variants`
- “用 Canon 里的她画战斗图” → `same-character`
- “这张哪里不好，帮我改一版” → `critique`

Explicit mode always wins. `auto` is an internal benchmark/automation mode, not a Human-facing creative mode, and its outcome is `AUTO_RECOMMENDED`, never `HUMAN_APPROVED`.

## Shared technical boundary

All image-producing modes share:

```text
Generation → S1 Anime 2D Hard Gate → Anatomy Integrity Check → Human Review
```

Same Character additionally runs Identity Drift Review. Technical failures may block delivery or enter a bounded repair loop. Aesthetic concerns remain analysis and recommendation; they are not a second hard Gate.

`quick` is low-friction, not permission to ignore explicit user requirements. `directed` grants Codex design freedom, but its result is still an AI Recommended Design. `explore` remains the default high-control workflow and keeps Human Mix as a first-class action. `variants` and `critique` always retain the source and every meaningful branch.
