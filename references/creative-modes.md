# Three Creation Modes

`anime-character-director` is one Codex Skill with three top-level creation modes. Repair, variant, same-character, and critique are post-generation actions, not creation modes.

Interaction System v1 and Persistent Interactive Workflow Runner v1 are the documented production baseline for the current interaction scope. Their contracts are described in [Interaction System](../docs/INTERACTION_SYSTEM.md) and [Persistent Interactive Workflow](../docs/PERSISTENT_INTERACTIVE_WORKFLOW.md).

| Mode | Goal | Exploration | Gate strategy | End state |
|---|---|---|---|---|
| `QUICK` | Fast first pass | Low depth; few candidates | AI fills missing values without waiting | `GENERATION_READY` |
| `AI_DECIDE` | Best complete design | Full Character and Art Explore, preference reasoning, diversity and genericness checks | AI selects and records `delegated_ai` | `GENERATION_READY` |
| `USER_DECIDE` | Human owns high-impact choices | Full candidate exploration and one consolidated Visual Preference Sheet | Wait at Character, Art, and Visual Preference gates | Next gate or `GENERATION_READY` |

## Routing

Explicit mode names win. Natural-language hints are intentionally small:

- Quick: `快速生成`, `直接来`, `不用问我`, `快一点`.
- AI Decide: `你来决定`, `你帮我完整设计`, `都交给你`, `你选最好的`.
- User Decide: `给我几个方案`, `我来选`, `每一步让我选`, `先给方案`, `我自己选`.

If no reliable hint exists, use `AI_DECIDE`. Do not infer a new mode from a post-generation request.

## Shared pipeline

```text
INPUT
 → CHARACTER_EXPLORE
 → CHARACTER_DIRECTION_RESOLUTION
 → CHARACTER_PLANNING
 → ART_EXPLORE
 → ART_DIRECTION_RESOLUTION
 → VISUAL_PREFERENCE_RESOLUTION
 → FINAL_DESIGN
 → PLAYABLE_CHARACTER_DESIGN_GATE
 → PROMPT_COMPILATION
 → GENERATION_READY
```

The pipeline asks a `GateResolver` to resolve a gate. It does not contain `if mode == ...` branches. The resolver owns only the resolution strategy.

## User Decide interaction

Natural-language replies map to the same actions: `B`, `第二个`, `A 和 C 混一下`, field-level updates, `你来决定`, `其他按推荐`, `返回上一步`, and `都不喜欢，换一批`. Questions do not select or advance, and ambiguous input asks for a minimal clarification.

`SELECT B` locks one candidate and immediately resumes the same WorkflowRun. `MIX A+C` creates a composite direction without rerunning exploration. `CUSTOM` stores a human-written direction; the runner exposes it as an extra option after every real candidate and opens a same-run Custom Input checkpoint. Direct custom language is also accepted. `DELEGATE` delegates the current gate; `PARTIAL_DELEGATE` keeps named fields human-owned and delegates the rest. `USE_RECOMMENDED` accepts one proposal, while `USE_ALL_RECOMMENDED` accepts the whole visible sheet in one event.

Explicit positive and negative constraints are extracted before exploration. Later-field constraints remain pending until the Visual Preference Sheet opens, then lock with `explicit_user` provenance and are not re-asked.

Recommendations remain unresolved until accepted. User-facing output is localized natural language with compact options; the persisted sheet, audit, WorkflowRun, and checkpoints remain structured JSON. `A/B/C/D/E` are display positions; `__CUSTOM__` is the stable internal custom option id.

`BACK` creates a rollback event. Moving from Art to Character invalidates Character Plan, Art Explore, Art Selection, Visual Preferences, Final Design, and Prompt, while retaining the original input, interaction history, and previous choices. A visual-preference-only change invalidates Final Design and Prompt only.

## Provenance

Important sources are `explicit_user`, `quick_ai_fill`, `delegated_ai`, `policy_default`, `human_select`, `human_mix`, `human_custom`, and `human_accept_recommended`. Human acceptance of a recommendation is not the same as AI delegation.

## Boundary

All three modes retain the default Global Rendering Style, Regional Visual Language, Lower-Body rules, hard no-crossed-legs Pose System, and Prompt Audit. The local runner stops at `GENERATION_READY`; the Codex Skill then owns the validated handoff to built-in `$imagegen` and post-generation quality audit.
