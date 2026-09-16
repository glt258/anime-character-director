# Interaction Workflow

The Skill owns the conversation; `runtime/interaction_runtime.py` owns the shared resumable state machine, and `runtime/workflow_runner.py` owns the product-level continuation lifecycle. A character creation is one `WorkflowRun`, persisted across turns and process restarts. A Gate is an `InteractionCheckpoint`, not a task termination.

## Lifecycle

```text
start_workflow(input, mode?)
  → create one WorkflowRun and one underlying session
  → choose QUICK / AI_DECIDE / USER_DECIDE
  → run shared pipeline
  → return an InteractionCheckpoint or GENERATION_READY

continue_workflow(run_id, user_message)
  → load the active WorkflowRun and open checkpoint
  → parse ordinary language and validate the checkpoint
  → resolve, persist, and continue the same pipeline
  → return the next checkpoint or GENERATION_READY
```

The underlying `create_session` and `resume_session` APIs remain available for deterministic integrations. Normal Skill conversation uses the runner so the user never needs to mention `resume`, `session_id`, `gate_id`, or `continue`.

The persisted directory is `sessions/<session_id>/` with `workflow_run.json`, `session.json`, `events.jsonl`, `checkpoints.jsonl`, and an `artifacts/` directory reserved for handoff artifacts. Workflow and session JSON use temporary files followed by replacement so a process interruption does not lose a resolved gate.

`WorkflowRun.status = WAITING_FOR_INTERACTION` means the run is still active. `continue_active_workflow(message)` routes a short reply to the most recently updated waiting run. Explicit cancellation plus a new-role request cancels the old run before starting a new one.

## Gates and statuses

The only creation gates are `CHARACTER_DIRECTION_GATE`, `ART_DIRECTION_GATE`, and `VISUAL_PREFERENCE_GATE`. The corresponding waiting statuses are `AWAITING_CHARACTER_DIRECTION`, `AWAITING_ART_DIRECTION`, and `AWAITING_VISUAL_PREFERENCES`.

The session also uses `CREATED`, `RUNNING`, `FINAL_DESIGNING`, `DESIGN_VALIDATING`, `PROMPT_COMPILING`, `GENERATION_READY`, `BLOCKED`, and `FAILED`. A gate has `RESOLVED`, `WAITING_FOR_USER`, `PARTIALLY_RESOLVED`, `INVALID`, or `CANCELLED` resolution status. Interaction System v1 is `ACCEPTED / FROZEN` for the current scope.

## Actions

Candidate gates accept `SELECT`, `MIX`, `CUSTOM`, `DELEGATE`, `PARTIAL_DELEGATE`, `USE_RECOMMENDED`, `USE_ALL_RECOMMENDED`, `REGENERATE_OPTIONS`, and `BACK`. The Visual Preference Sheet additionally accepts field-level versions of `SELECT`, `MIX`, `CUSTOM`, `USE_RECOMMENDED`, `CONSTRAINT_UPDATE`, and the batch `USE_ALL_RECOMMENDED` form. Natural-language parsing maps ordinary user replies to these actions; `QUESTION_ONLY` never advances or locks a gate.

The runner adds an extra `__CUSTOM__` option after all real candidates; selecting it opens a Custom Input checkpoint in the same WorkflowRun. Direct custom language is accepted without selecting the option.

An event for an old `gate_id` returns `STALE_GATE_EVENT` and cannot mutate the session. A repeated `event_id` returns its original response and is not appended to `events.jsonl` again. Invalid actions are rolled back from an in-memory snapshot and return `INVALID_INTERACTION`.

## Mode switches and failures

An explicit `to_mode` or a phrase such as `后面你决定吧` records a `ModeSwitchEvent` and continues the current session. Explicit later-field constraints are held in `pending_constraint_updates` and applied with `explicit_user` provenance when the Visual Preference Sheet opens. Automatic retries are capped at one per high-level design phase. Quick may retry internally once; User Decide returns to the Art gate with the failure reason instead of silently replacing a human choice. A second failure becomes `BLOCKED`.

## Existing gates

The orchestration layer does not redefine the existing Visual Preference, Regional Style, Lower-Body, Leg Separation, Pose Intent, or Prompt Audit contracts. Before prompt compilation it delegates to the existing Visual Preference runtime and `PromptCompiler`. Pose System v1 remains `ACCEPTED / FROZEN`.

## Generation boundary

`GENERATION_READY` means the compiled `PromptBundle` passed the current runtime checks. No image is generated and `$imagegen` is not called in this phase. Post-generation repair, variants, same-character outputs, and critique are future actions on a completed design, not new creation modes.

The existing `variants` action remains available for controlled post-generation work; it must preserve a Human-approved Canon and never silently redesign it. Optional glove or hosiery asymmetry is an aesthetic choice, not a hard gate or validator. This interaction layer adds no new hard gate or validator.
