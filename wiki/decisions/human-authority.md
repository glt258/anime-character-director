---
title: Human Authority and Lineage
description: Decision record for keeping final visual selection and approval under explicit human control.
tags: [decision, human-in-loop, lineage]
sources: ["[[SKILL.md]]", "[[src]]", "[[references/skill-runtime-contract.md]]"]
updated: 2026-09-14
type: decision
related: ["[[architecture/skill-and-runtime]]", "[[experiments/benchmark-status]]"]
---

# Human Authority

Codex may expand options and the runtime may validate them, but the human selects, mixes, locks, and approves the final design. Runtime sources are explicit: user input, human mix, custom content, or an AI-delegated proposal.

Lineage and lock state must remain visible. `HUMAN_APPROVED` cannot be emitted without an actual human approval event. When evidence is ambiguous, the workflow stops or requests review rather than silently promoting a generated choice.
