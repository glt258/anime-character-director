# Scripts boundary

The source benchmark contains Python benchmark and Runtime helpers under its `skills/anime-character-director/scripts/` directory. They import the benchmark-level `src/`, planning `schemas/`, and `benchmarks/` trees, so they are intentionally not shipped in this standalone Skill package.

The reusable product is the Codex Skill layer: `SKILL.md`, the bundled `docs/` and `config/` style contract, its references, the Codex agent metadata, and the example assets. A host project may provide its own local Runtime preflight; the Skill does not require a bundled external Agent, server, LLM API, image API, or ComfyUI pipeline.
