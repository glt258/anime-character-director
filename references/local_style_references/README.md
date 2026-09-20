# Local Character Art Reference Library

This is an optional, local-only visual reference interface. The repository
contains the schema, example, resolver contract, and tests; it does not
distribute game artwork. Real images belong under the separately configured
`game_style_references` directory and are never required for the text/YAML
workflow.

Use the local configuration example as a starting point, or set
`ANIME_CHARACTER_DIRECTOR_ASSET_ROOT`:

```powershell
python -m runtime.style_references inspect genshin_impact
python -m runtime.style_references inspect-all
```

Resolver priority is explicit `asset_root` argument, environment variable,
`%USERPROFILE%\.codex\anime-character-director.local.yaml`, then the default
discovery directory. A missing library, missing image, unreadable image, or
hash/dimension mismatch falls back to text-only references with diagnostics;
it does not break the normal Skill runtime.

Reference conditioning is enabled by default in `auto` mode for the four
reviewed IDs: `genshin_impact`, `zenless_zone_zero`, `wuthering_waves`, and
`neverness_to_everness`. `QUICK` uses `style_forward`; `AI_DECIDE` uses
`balanced`. The resolver supplies three images by default and never more than
four. `disabled` and `yaml_only` remain supported for A/B comparisons.

The compiler tells the backend that these are game-character illustration
style references. They may shape rendering and otherwise-unlocked visual
design space, while explicit user constraints always win. The contract also
forbids copying a reference character's identity, exact face, hairstyle,
outfit, emblem, accessory combination, or silhouette.

The v1 local manifest may declare future game IDs for library inspection, but
conditioning only enables the four reviewed profiles above. The initial local selection contains six curated references
for each of the four reviewed profiles, while one resolution returns three by
default and never more than four.
