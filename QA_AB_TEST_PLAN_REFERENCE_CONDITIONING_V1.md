# QA / A-B Test Plan — Reference Conditioning v1

## Runtime checks

Run the focused suite:

```powershell
py -3 -m pytest tests/test_style_references.py tests/test_game_style_runtime.py tests/test_game_style_v2.py -q
```

The fixture library uses generated 1×1 PNG bytes only; it is a resolver test
fixture and not game artwork.

## Human acceptance matrix

For each case, generate the same short prompt twice:

| Case | Mode | Style | A | B |
|---|---|---|---|---|
| HA-RC-01 | QUICK | genshin_impact | YAML-only | YAML + local refs |
| HA-RC-02 | QUICK | neverness_to_everness | YAML-only | YAML + local refs |
| HA-RC-03 | QUICK | zenless_zone_zero | YAML-only | YAML + local refs |
| HA-RC-04 | QUICK | wuthering_waves | YAML-only | YAML + local refs |
| HA-RC-05 | AI_DECIDE | genshin_impact | YAML-only | YAML + local refs |

Suggested prompts:

- `画一个粉毛御姐，体现角色魅力，原神立绘风格`
- `画一个粉毛御姐，体现角色魅力，异环立绘风格`
- `画一个魔女，要有乌鸦元素，绝区零角色立绘风格`
- `画一个冷感成熟女性，鸣潮角色立绘风格`

Score each A/B pair on a 1–5 scale for game-style read, overall visual
quality, preservation of explicit constraints, subject originality, and
whether the difference is carried by the character rather than background
alone. Record any hard-constraint violation as a failure regardless of score.

## Fallback and hard-constraint cases

Verify that a missing library, missing images, malformed manifest, unsupported
style, and disabled switch all still reach the YAML-only request without a
crash. Repeat with explicit constraints: no stockings, sneakers, short hair,
small body, and white primary color. The reference branch may alter only
unlocked style preferences.

## Acceptance evidence

Keep the runtime `prompt_bundle.json`, `image_request`, selected reference
IDs/paths, and fallback reason with each pair. Confirm `git ls-files` reports
zero tracked `.png`, `.jpg`, `.jpeg`, or `.webp` files under the local
reference documentation tree.
