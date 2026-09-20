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
related: ["[[interaction-system]]", "[[../../docs/PERSISTENT_INTERACTIVE_WORKFLOW.md]]"]
---

# Persistent Interactive Workflow Runner v1

The product lifecycle now separates one logical `WorkflowRun` from the underlying `CreativeInteractionSession`. User Decide Character, Art, Visual Preference, and Custom Input pauses are `InteractionCheckpoint` boundaries inside the same run. The runner persists `workflow_run.json`, `checkpoints.jsonl`, and the existing session artifacts; a new process can route a normal reply such as `B` to the active waiting run without asking for `resume`, `continue`, or an id.

QUICK and AI_DECIDE resolve the shared pipeline with zero human checkpoints. USER_DECIDE usually creates three gate checkpoints and continues automatically after each reply. A Custom choice adds a same-run Custom Input checkpoint, and direct custom language maps to `human_custom`. `REGENERATE_OPTIONS`, BACK, mode switching, explicit constraints, recommendation separation, partial delegation, stale protection, and idempotency remain owned by the accepted base interaction runtime.

`InteractionLocalizer` renders Chinese or English display titles, descriptions, recommendation labels, custom prompts, and progress copy while preserving stable internal option ids and enum values. The custom option is always appended after all real candidates with internal id `__CUSTOM__`; visible letters are positional.

The implementation keeps one logical run across checkpoints and process restarts. The public contract ends at `GENERATION_READY`; image generation, visual review, and benchmark execution remain outside this persistence layer.

## Related

- [[interaction-system]] — accepted shared gate and pipeline contract
- [[../../docs/PERSISTENT_INTERACTIVE_WORKFLOW.md]] — implementation details and API
