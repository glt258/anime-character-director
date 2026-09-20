---
title: Skill and Runtime Architecture
description: Current staged workflow and division of responsibility between Skill, runtime, human, and image generation.
tags: [architecture, workflow, runtime]
sources: ["[[SKILL.md]]", "runtime/regional_style_runtime.py", "runtime/pose_intent_runtime.py", "runtime/interaction_runtime.py", "[[../docs/INTERACTION_SYSTEM.md]]"]
updated: 2026-09-15
type: architecture
related: ["[[decisions/human-authority]]", "[[constraints/anatomy-pose-and-footwear]]", "[[architecture/pose-intent-preservation]]"]
---

# Skill and Runtime Architecture

The workflow is: Explore → Character Planning → Art Planning → Visual Preference Proposal → human selection/mix/audit → Final Design → Review → runtime execution → image generation → LegSeparationGate → S1 Anime 2D gate → default Gacha Rendering Style gate → anatomy gate → candidate promotion → human review.

The Skill owns orchestration, evidence boundaries, checkpoints, and user-facing decisions. The local runtime owns deterministic validation, source lineage, locks, mode handling, and reportable state. `$imagegen` supplies visual output; it does not replace the gates or human authority.

Post-generation adherence is a separate reporting seam. `VisualAdherenceCritic` consumes an actual image plus the persisted `PromptAdherenceManifest` and labeled observations, then persists a stable field/anatomy report through `InteractionRuntime.record_visual_adherence_review`. It is detection-only: no prompt rewrite, DesignDNA mutation, regeneration, best-of-N, or similarity scoring.

Repair disposition is intentionally separate from strict adherence truth: `VisualAdherenceCritic → AdherenceDispositionPolicy → RepairTriggerDecision → actionable_repair_targets → VisualRepairPlan`. `overall_result` remains strict design fidelity. Ownership and repair importance are orthogonal: `HUMAN_EXPLICIT` / `HUMAN_SELECTION` failures can require repair, `SYSTEM_INVARIANT` failures can require repair, while `AI_RESOLVED` / `SYSTEM_DEFAULT` deviations remain review-visible without automatic repair by default. Disposition and actionable targets are persisted for replay; explicit user repair requests may promote an informational target.

Generation is blocked when required planning, lock, identity, or review checkpoints are not satisfied.

Global Rendering Style is a runtime-owned default: `CONTEMPORARY_COMMERCIAL_GACHA_ANIME`. Character Visual Style remains character-owned design language and cannot replace the rendering medium unless the user explicitly supplies a rendering override. S1 checks the anime 2D medium; Gacha checks commercial playable-character rendering and presentation; the two reports remain separate.

The style system now has a third explicit layer: `Regional Visual Language`, default `EAST_ASIAN_CONTEMPORARY_GACHA`. It governs illustration grammar rather than ethnicity or costume. `PromptCompiler`, `RegionalStyleCritic`, `GachaStyleCritic`, `StyleGateResult`, migration helpers, and the Outfit Family Ledger are implemented in `runtime/regional_style_runtime.py`. The global `NO_CROSSED_LEGS_HARD_INVARIANT` and `LegSeparationGate` are implemented in `runtime/leg_separation_runtime.py`; they block candidate promotion before normal style/anatomy acceptance. See [[regional-visual-language]].

Pose meaning is now a separate runtime concern. `PoseIntentContract` and `PoseIntentGate` preserve requested body language—such as elegant, sensual, low-energy, narrow, asymmetric, or one-foot-forward—while leaving the hard leg contract unchanged. `PromptCompiler` emits `POSE INTENT` before leg geometry; `POSE_VALID` requires both gates. `PoseDiversityLedger` detects non-blocking safe-pose homogenization, and pose-intent-only repair preserves identity and reruns leg safety. See [[architecture/pose-intent-preservation]].

Interaction System v1 now adds `CreativeInteractionSession` as the single durable state container for the three creation modes `QUICK`, `AI_DECIDE`, and `USER_DECIDE`. `runtime/interaction_runtime.py` owns the shared pipeline, `InteractionEvent`, `GateResolution`, `InteractiveResponse`, persistence, stale-gate protection, idempotency, rollback, and mode switching. The pipeline delegates all three creation gates to `QuickGateResolver`, `AIDecideGateResolver`, or `UserDecideGateResolver`; it does not branch on mode. `runtime/codex_interaction_adapter.py` is the separate Codex-native presentation boundary: it converts an open checkpoint into three dynamic native choices, maps the host answer back to a checkpoint-scoped stable id, and fails closed on stale or ambiguous answers. `PersistentWorkflowRunner.continue_native_workflow` resolves and advances the same run; the Python runtime does not import the host tool. The phase ends at `GENERATION_READY` without calling `$imagegen`. See [[interaction-system]] and [[persistent-interactive-workflow]].

Before mode resolution, the runtime extracts current-run explicit constraints into structured, human-owned records. Those records lock identity, costume, body proportion, props, non-human features, lower-body details, palette, pose, background, composition, and quantity fields against QUICK/AI defaults and AI candidate divergence. The post-compiler `ExplicitConstraintCoverageGate` is the final fail-closed check before `GENERATION_READY`; historical sessions remain replayable but do not become positive design evidence.
