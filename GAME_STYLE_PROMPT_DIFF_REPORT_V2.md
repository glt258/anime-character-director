# GAME STYLE PROMPT DIFF REPORT v2

日期：2026-09-20
实现版本：`game_style_profile_v2` / `game_style_projection_v2`
用途：验证五向固定角色 prompt 只改变角色渲染 HOW，不改变角色 WHAT、背景、姿势、光照意图或全局质量底线。

## Fixed fixture

五个模式使用同一段角色内容：

```text
adult woman; pink shoulder-length hair; teal eyes; petite build; white and navy short jacket; black shorts; flat ankle boots; no stockings; human; stable open stance
```

背景固定为：

```text
simple neutral commercial character showcase background, light neutral architectural panels, subtle depth, no game-specific landmarks, no fantasy city, no futuristic skyline, no faction symbols, no environmental storytelling, background secondary
```

光照意图固定为：

```text
neutral soft directional studio-like daylight, stable key direction, moderate overall contrast
```

## Five-way diff contract

| Prompt region | Global | Genshin | ZZZ | WuWa | NTE |
|---|---|---|---|---|---|
| Unchanged character | exact fixed fixture | exact fixed fixture | exact fixed fixture | exact fixed fixture | exact fixed fixture |
| Global rendering | `CONTEMPORARY_COMMERCIAL_GACHA_ANIME` | same | same | same | same |
| Game delta | none | firm major contour + crisp/soft interior edge mix; primary shadow blocks followed by soft secondary gradients; high clustered surface detail | soft contour/interior transitions; continuous tonal gradients; moderate localized detail clusters | variable contour and shadow strategies; high surface frequency with visible secondary clusters | variable local contour/shadow strategies; high but locally grouped surface frequency |
| Background | exact fixed fixture | exact fixed fixture | exact fixed fixture | exact fixed fixture | exact fixed fixture |
| Pose / lighting / constraints | exact fixed fixture and shared leg/anatomy constraints | same | same | same | same |

The game delta is emitted as:

```text
## RENDERING SPECIALIZATION
Rendering specialization:
Technical rendering HOW rules only; preserve character WHAT and explicit user choices.
- SLOT [strength]: absolute technical instruction
  Contrastive HOW: relative-to-Global technical instruction
```

The compiler does not place the display game name in this prompt section. The
canonical ID, profile version, projection version, source claim IDs, complete
signature, and applied/adapted/dropped trace remain in `PromptBundle` metadata
and `game_style_debug_trace`.

## Slot and budget evidence

Each packaged profile contains all required signature slots. v2 projects five
core character-subject rules per game, zero supporting rules in the current
evidence boundary, and never exceeds ten total projected rules. Unsupported
slots such as skin, hair, eyes, material specular, post-processing, and color
organization are explicitly represented as `no_reliable_discriminator` and do
not become invented prompt claims.

| Profile | Core | Supporting | Total | Direct subject slots |
|---|---:|---:|---:|---:|
| Global | 0 | 0 | 0 | 0 |
| Genshin Impact | 5 | 0 | 5 | 5 |
| Zenless Zone Zero | 5 | 0 | 5 | 5 |
| Wuthering Waves | 5 | 0 | 5 | 5 |
| Neverness to Everness | 5 | 0 | 5 | 5 |

## Interpretation boundary

This is a prompt-level diff contract, not a claim that text alone proves image
acceptance. The separate `STYLE_DIFFERENCE_VALIDITY_GATE` requires
`character preservation = PASS` and `rendering difference =
CLEAR_CHARACTER_RENDERING_DIFFERENCE`. Background-only, atmosphere-only, pose,
outfit, body, hair-color, or random ornament changes are excluded from the
style score.
