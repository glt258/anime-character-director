# Interaction Workflow

The Skill owns the conversation; `runtime/interaction_runtime.py` owns the resumable state machine. A session is created once, persisted after every gate resolution, and resumed by `InteractionEvent`.

## Lifecycle

```text
create_session(input, mode?)
  → choose QUICK / AI_DECIDE / USER_DECIDE
  → run shared pipeline
  → wait at a User Decide gate or return GENERATION_READY

resume_session(session_id, event)
  → validate session and current gate_id
  → deduplicate event_id
  → apply action
  → save session before continuing
  → run until next unresolved gate or GENERATION_READY
```

The persisted directory is `sessions/<session_id>/` with `session.json`, `events.jsonl`, and an `artifacts/` directory reserved for handoff artifacts. Saves use a temporary file followed by replacement so a process interruption does not lose a resolved gate.

## Gates and statuses

The only creation gates are `CHARACTER_DIRECTION_GATE`, `ART_DIRECTION_GATE`, and `VISUAL_PREFERENCE_GATE`. The corresponding waiting statuses are `AWAITING_CHARACTER_DIRECTION`, `AWAITING_ART_DIRECTION`, and `AWAITING_VISUAL_PREFERENCES`.

The session also uses `CREATED`, `RUNNING`, `FINAL_DESIGNING`, `DESIGN_VALIDATING`, `PROMPT_COMPILING`, `GENERATION_READY`, `BLOCKED`, and `FAILED`. A gate has `RESOLVED`, `WAITING_FOR_USER`, `PARTIALLY_RESOLVED`, `INVALID`, or `CANCELLED` resolution status. Interaction System v1 is `ACCEPTED / FROZEN` for the current scope.

## Actions

Candidate gates accept `SELECT`, `MIX`, `CUSTOM`, `DELEGATE`, `PARTIAL_DELEGATE`, `USE_RECOMMENDED`, `USE_ALL_RECOMMENDED`, `REGENERATE_OPTIONS`, and `BACK`. The Visual Preference Sheet additionally accepts field-level versions of `SELECT`, `MIX`, `CUSTOM`, `USE_RECOMMENDED`, `CONSTRAINT_UPDATE`, and the batch `USE_ALL_RECOMMENDED` form. Natural-language parsing maps ordinary user replies to these actions; `QUESTION_ONLY` never advances or locks a gate.

An event for an old `gate_id` returns `STALE_GATE_EVENT` and cannot mutate the session. A repeated `event_id` returns its original response and is not appended to `events.jsonl` again. Invalid actions are rolled back from an in-memory snapshot and return `INVALID_INTERACTION`.

## Mode switches and failures

An explicit `to_mode` or a phrase such as `后面你决定吧` records a `ModeSwitchEvent` and continues the current session. Explicit later-field constraints are held in `pending_constraint_updates` and applied with `explicit_user` provenance when the Visual Preference Sheet opens. Automatic retries are capped at one per high-level design phase. Quick may retry internally once; User Decide returns to the Art gate with the failure reason instead of silently replacing a human choice. A second failure becomes `BLOCKED`.

## Existing gates

The orchestration layer does not redefine the existing Visual Preference, Regional Style, Lower-Body, Leg Separation, Pose Intent, or Prompt Audit contracts. Before prompt compilation it delegates to the existing Visual Preference runtime and `PromptCompiler`. Pose System v1 remains `ACCEPTED / FROZEN`.

## Generation boundary

`GENERATION_READY` means the compiled `PromptBundle` passed the current runtime checks. No image is generated and `$imagegen` is not called in this phase. Post-generation repair, variants, same-character outputs, and critique are future actions on a completed design, not new creation modes.

The existing `variants` action remains available for controlled post-generation work; it must preserve a Human-approved Canon and never silently redesign it. Optional glove or hosiery asymmetry is an aesthetic choice, not a hard gate or validator. This interaction layer adds no new hard gate or validator.
