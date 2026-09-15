# Runtime boundary

The Skill now ships a small dependency-free runtime under `runtime/visual_preference_runtime.py`. It owns the Visual Preference Gate, explicit selection sources, Human Audit Policy, state transitions, and the two preference artifacts. It does not call an image model.

The reusable product remains the Skill layer: `SKILL.md`, the bundled `docs/`, `config/`, `schemas/`, `runtime/`, references, Codex agent metadata, tests, and example assets. A host project may add hashes, lineage, generation QA, or a larger planning Runtime around this gate; no external Agent, server, LLM API, image API, or ComfyUI pipeline is required.
