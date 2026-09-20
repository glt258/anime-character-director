# Reference Conditioning v1 — 8-Case A/B Matrix

This is a preparation artifact. It does not claim that B is visually better;
only a Human can accept or reject the generated images.

## Fixed variables

- Mode: `QUICK`
- User prompt: `画一个粉毛御姐，体现角色魅力，XXX角色立绘风格，快速模式。`
- A: `reference_conditioning_mode=yaml_only`
- B: `reference_conditioning_mode=yaml_plus_local_references`
- B policy: `style_drift_policy=style_forward`
- A and B use the same game style, YAML profile, seed/configuration, and user constraints.
- B must attach the resolver-selected absolute paths; an empty attachment is `INVALID`.

## Cases

| Case | Game style | A case | B case | Output path |
|---|---|---|---|---|
| RC-GEN-A/B | `genshin_impact` / 原神 | `RC-GEN-A` | `RC-GEN-B` | pending ImageGen |
| RC-NTE-A/B | `neverness_to_everness` / 异环 | `RC-NTE-A` | `RC-NTE-B` | pending ImageGen |
| RC-WUWA-A/B | `wuthering_waves` / 鸣潮 | `RC-WUWA-A` | `RC-WUWA-B` | pending ImageGen |
| RC-ZZZ-A/B | `zenless_zone_zero` / 绝区零 | `RC-ZZZ-A` | `RC-ZZZ-B` | pending ImageGen |

## Human scoring

Review A/B side by side without pixel-similarity scoring. Record 1–5 for:

1. Visual quality and commercial character appeal.
2. Game flavor in the subject, not only the background.
3. Character appeal and packaging.
4. Preservation of pink hair, mature-woman read, and charm.
5. Absence of copied face, hairstyle, outfit, emblem, accessory combination, or silhouette.

Mark any explicit-prompt violation or obvious reference clone as `FAIL`. Do not
automatically declare B the winner when loading, tests, or prompt text pass.
