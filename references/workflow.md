# Interaction Workflow

The Skill owns the conversation; `runtime/interaction_runtime.py` owns the shared resumable state machine, and `runtime/workflow_runner.py` owns the product-level continuation lifecycle. A character creation is one `WorkflowRun`, persisted across turns and process restarts. A Gate is an `InteractionCheckpoint`, not a task termination.

## Lifecycle

```text
start_workflow(input, mode?)
  → create one WorkflowRun and one underlying session
  → build sanitized CurrentRunContext from the current request and current-run state
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

## Visual Context Firewall

Each new run is a fresh visual run and sets `inherit_previous_visuals = false`. Before character exploration, Skill reasoning builds a sanitized `CurrentRunContext` from `current_user_request`, explicit current-run selections, current-run gate resolutions, global policies/style contracts, and explicitly authorized inheritance. The full conversation history is not a design input. Earlier character designs, candidates, prompts, image descriptions, and critic summaries remain available to replay/logging and the future anti-repetition path, but are excluded from current-run designer, art/style, Visual Preference, and PromptCompiler inputs.

Do not infer current visual preferences from previous runs. In `USER_DECIDE`, an unselected field stays unselected or AI-proposed according to the current gate; history cannot fill it. Only an explicit current request such as “沿用上一版的红发” or “参考上一版整体设计做一个变体” enables inheritance. The first authorizes only the named hair-color field; the second authorizes the explicitly requested overall variation. Unspecified historical visuals remain blocked, and the forbidden path is `history → Codex reasoning → new visual choice`.

### Face Aesthetic Contract

Fresh runs use `EAST_ASIAN_COMMERCIAL_GACHA_FACE` by default and record the profile, source, guardrails, and `NO_FACE_AESTHETIC_INHERITANCE` policy in the current-run contract. Previous facial structure or regional face language is excluded from designer, Visual Preference, and PromptCompiler inputs. A current explicit face request may select `WESTERN_INSPIRED_GACHA_FACE` or `NEUTRAL_GACHA_FACE`; historical face information otherwise remains replay/anti-repetition data only.

## Cross-run Novelty Guard

After `FINAL_DESIGN` is assembled and before `PROMPT_COMPILATION`, `NoveltyGuard` compares the current structured `DesignSignature` with a configurable recent snapshot of completed fresh runs. This is post-design evaluation, not positive context: history contains no prompt, chat text, image description, or critic prose and cannot flow into Character Direction, Art Direction, Visual Preference, PromptCompiler, or repair prompts. Structural fields outweigh cosmetic fields, so recoloring alone fails while a structurally different design in the same archetype can pass. Explicit inheritance/variation is `EXEMPT`; QUICK uses a deterministic alternate, AI_DECIDE filters collision candidates after quality validation, and USER_DECIDE preserves Human choices with an auditable override. Repair attempts never add another signature, and replay reuses the saved snapshot.

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

## Image-level adherence review

After the Skill's one explicit image-generation call, the host may call `record_visual_adherence_review` with the generated image path and human/model-labeled observations. `VisualAdherenceCritic` reads required fields only from the persisted `PromptAdherenceManifest`, records field results plus hand/foot anatomy checks, and writes `artifacts/visual_adherence_review.json`; `replay_session` exposes the same report. It only detects, reports, and classifies. It does not rewrite prompts, alter DesignDNA, regenerate, run best-of-N, or score similarity.

## Targeted visual repair

An authorized repair is a separate bounded action after review. `build_visual_repair_plan` consumes only the current review's `repair_targets`; passing HARD fields become `locked_fields`, and the plan carries source image/prompt/review linkage, attempt number, target instructions, preservation fields, and anti-regression constraints. `compile_repair_prompt` creates a new `RepairPromptBundle` and leaves the original `PromptBundle` unchanged. It emits a concise preservation block plus targeted `TYPE 3` replacement or `TYPE 4` strengthen-only instructions; it does not add unrelated creative decisions or read historical runs.

The runtime has no image-edit/mask backend, so the Skill may pass the exact repair prompt to external `$imagegen` for one constrained full-image regeneration, then record the image and re-run the external observation/critic seam. A repair cannot be accepted without re-review. Regression preserves the original best artifact; adherence-only comparison may update it only when strictly better. Two attempts are the hard limit. Each attempt is persisted under `artifacts/repair/attempt_NN/`, and replay returns the original review, repair plans/prompts/reviews, outcomes, status, and selected best artifact without invoking ImageGen.
