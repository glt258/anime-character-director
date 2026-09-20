# Reference Conditioning Integration v1

This release adds optional local character-art references to the existing
`Final Design → PromptCompiler → GENERATION_READY` handoff. The feature is an
enhancement, not a replacement: without a local library the original
text-only/YAML-only path remains valid.

## Runtime contract

The resolver is the only component that reads `manifest.json` or constructs
reference paths. It returns a `StyleConditioningContext` containing the YAML
style profile, `ReferenceConditioningPayload`, mode, drift policy, explicit
constraints, and fallback state.

Supported conditioning IDs are `genshin_impact`, `zenless_zone_zero`,
`wuthering_waves`, and `neverness_to_everness`. Selection is deterministic,
prefers overall/face/body/costume/material roles, prefers different canonical
characters, uses three images by default, and caps the request at four.

`QUICK` defaults to `yaml_plus_local_references` with `style_forward`; its
purpose is visible game-style character packaging. `AI_DECIDE` uses the same
conditioning mode with `balanced` drift. `disabled`, `yaml_only`, unsupported
styles, missing files, invalid manifests, empty selections, and resolver
errors all produce a YAML-only fallback with a recorded reason.

The prompt compiler states that references are game-character illustration
style references. They can influence rendering and visual design space the
user did not lock. Explicit user constraints always win, and the prompt
contains the anti-copy contract: do not reproduce a reference character's
identity, exact face, hairstyle, outfit, emblem, accessory combination, or
silhouette.

`runtime/image_request.py` emits `CompiledImageRequest`. It attaches the
resolver's validated absolute paths only when the effective mode is
`yaml_plus_local_references`; the later ImageGen caller can pass the object to
a backend without opening the manifest itself.

## Configuration

Copy `anime-character-director.local.example.yaml` to the user-local Codex
configuration path and edit the asset root. Environment variables with the
`ANIME_CHARACTER_DIRECTOR_` prefix override local settings. Real artwork and
the real config are intentionally outside Git.

## Observability

`prompt_bundle.json` and `image_request` record the selected game style, YAML
profile usage, effective conditioning mode, drift policy, selected IDs,
absolute paths, roles, library version, selection reason, and fallback reason.

## Boundary

No reference artwork is distributed or tracked by this repository. The C
runtime/skill copy, release metadata, tags, pushes, and external ImageGen
execution are outside this v1 change.
