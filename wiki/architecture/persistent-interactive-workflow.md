---
title: Persistent Interactive Workflow Runner v1
description: One logical character creation run across User Decide checkpoints, restarts, Custom input, and localized conversation.
type: architecture
status: ACCEPTED / FROZEN
confidence: high
created: 2026-09-15
updated: 2026-09-15
tags: [architecture, interaction, workflow, persistence, locale]
sources: ["[[../../docs/PERSISTENT_INTERACTIVE_WORKFLOW.md]]", "[[../../SKILL.md]]", "runtime/workflow_runner.py"]
related: ["[[interaction-system]]", "[[../../roadmap/current]]", "[[../../docs/THREE_MODE_INTERACTION_V1_ACCEPTANCE.md]]"]
---

# Persistent Interactive Workflow Runner v1

The product lifecycle now separates one logical `WorkflowRun` from the underlying `CreativeInteractionSession`. User Decide Character, Art, Visual Preference, and Custom Input pauses are `InteractionCheckpoint` boundaries inside the same run. The runner persists `workflow_run.json`, `checkpoints.jsonl`, and the existing session artifacts; a new process can route a normal reply such as `B` to the active waiting run without asking for `resume`, `continue`, or an id.

QUICK and AI_DECIDE resolve the shared pipeline with zero human checkpoints. USER_DECIDE usually creates three gate checkpoints and continues automatically after each reply. A Custom choice adds a same-run Custom Input checkpoint, and direct custom language maps to `human_custom`. `REGENERATE_OPTIONS`, BACK, mode switching, explicit constraints, recommendation separation, partial delegation, stale protection, and idempotency remain owned by the accepted base interaction runtime.

`InteractionLocalizer` renders Chinese or English display titles, descriptions, recommendation labels, custom prompts, and progress copy while preserving stable internal option ids and enum values. The custom option is always appended after all real candidates with internal id `__CUSTOM__`; visible letters are positional.

The implementation passed Human Acceptance v1 and is now `PERSISTENT_INTERACTIVE_WORKFLOW_V1_ACCEPTED` / `ACCEPTED / FROZEN`. Pose System v1 remains `ACCEPTED / FROZEN`. The Generation Quality Benchmark was intentionally aborted for this orchestration fix, not failed for image quality; its eight existing QUICK/AI images remain retained as benchmark evidence.

The final acceptance evidence is stored under `outputs/persistent_interactive_workflow_human_acceptance_v1_20260915/`: HA-01 through HA-15 and the required exception scenarios passed, real restart continuation used two Python processes, one WorkflowRun was maintained per scenario, and observed image-generation calls were zero. `GENERATION_QUALITY_BENCHMARK_UNBLOCKED` is the next-stage recommendation only; no benchmark was started by this validation.

## Related

- [[interaction-system]] — accepted shared gate and pipeline contract
- [[../../roadmap/current]] — next acceptance boundary
- [[../../docs/PERSISTENT_INTERACTIVE_WORKFLOW.md]] — implementation details and API
