# Scripts boundary

The source benchmark contains Python benchmark and Runtime helpers under its `skills/anime-character-director/scripts/` directory. They import the benchmark-level `src/`, `schemas/`, `config/`, and `benchmarks/` trees, so they are intentionally not shipped in this standalone Skill package.

The reusable product is the Codex Skill layer: `SKILL.md`, `agents/`, `references/`, and `examples/`. A host project may provide its own local Runtime preflight; the Skill does not require a bundled external Agent, server, LLM API, image API, or ComfyUI pipeline.
